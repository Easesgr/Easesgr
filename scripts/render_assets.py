"""Render transparent, theme-aware SVG artwork for the GitHub profile.

Native SVG/CSS animation and the original handwritten logo. No scripts,
external assets, network requests or model calls are used by the artwork.
"""

from __future__ import annotations

import base64
import io
import math
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
THEMES = {
    'light': {'ink': (20, 92, 65), 'caption': (73, 100, 94), 'line_alpha': 100},
    'dark': {'ink': (155, 232, 195), 'caption': (181, 207, 202), 'line_alpha': 150},
}
COLORS = [(53, 118, 235), (22, 166, 146), (154, 111, 221), (226, 155, 60)]
ORIGIN = ('Origin: original transparent vector color-flow animation surrounding the regenerated '
          'Anyi-only handwritten wordmark, with bird and a heart over i. Designed for GitHub default white pages. The embedded '
          'artwork inherits the host color scheme and provides narrow-screen and static '
          'alternatives. No screenshots, project demos, scripts or external services.')


def wordmark(ink: tuple[int, int, int]) -> Image.Image:
    image = Image.open(ASSETS / 'anyi-wordmark.png').convert('RGBA')
    pixels = np.asarray(image).copy()
    gold = (pixels[:, :, 0] > pixels[:, :, 1]) & (pixels[:, :, 3] > 0)
    pixels[:, :, :3] = ink
    pixels[gold, :3] = (214, 160, 48)
    return Image.fromarray(pixels).crop(image.getbbox())


def label_layers(width: int, height: int, entries, size: int, light: str, dark: str, bold=False):
    layers = []
    for theme, color in [('light', light), ('dark', dark)]:
        image = Image.new('RGBA', (width * 2, height * 2))
        pen = ImageDraw.Draw(image)
        font_name = 'manrope-700.ttf' if bold else 'manrope-400.ttf'
        font = ImageFont.truetype(str(ASSETS / 'fonts' / font_name), size * 2)
        for text, x, y, anchor in entries:
            pen.text((x * 2, y * 2), text, font=font, fill=color, anchor=anchor)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        layers.append((theme, base64.b64encode(buffer.getvalue()).decode()))
    return layers


def flowing_points(width: int, height: int, strand: int, upper: bool):
    points = []
    for x in np.linspace(-width * .03, width * 1.03, 140):
        progress = x / width
        offset = strand * height * .016
        y = (height * (-.09 + .14 * math.sin(progress * math.pi + .3) ** 2) + offset if upper
             else height * (1.08 - .15 * math.sin(progress * math.pi + .5) ** 2) - offset)
        points.append((x, y))
    return points


def centerpiece(theme: str, mobile: bool, width: int, height: int):
    settings = THEMES[theme]
    mark = wordmark(settings['ink'])
    mark.thumbnail((370, 180) if mobile else (500, 215), Image.Resampling.LANCZOS)
    image = Image.new('RGBA', (width, height))
    image.alpha_composite(mark, ((width - mark.width) // 2, round(height * .45 - mark.height / 2)))
    subtitle = 'Vision  /  Agents  /  Open Source' if mobile else 'Computer Vision  /  AI Agents  /  Open Source'
    font = ImageFont.truetype(str(ASSETS / 'fonts/manrope-400.ttf'), 23 if mobile else 24)
    pen = ImageDraw.Draw(image)
    box = pen.textbbox((0, 0), subtitle, font=font)
    pen.text(((width - box[2]) / 2, height * .77), subtitle, font=font, fill=(*settings['caption'], 255))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return image, base64.b64encode(buffer.getvalue()).decode()


def render(mobile: bool):
    width, height = (720, 370) if mobile else (1280, 400)
    name = 'signature-mobile' if mobile else 'signature'
    raster_images = {theme: centerpiece(theme, mobile, width, height) for theme in THEMES}
    previews = {theme: Image.new('RGBA', (width * 2, height * 2)) for theme in THEMES}
    layers = []
    for upper in (True, False):
        paths = []
        for strand in range(7):
            color = COLORS[(strand // 2 + (0 if upper else 1)) % len(COLORS)]
            points = flowing_points(width, height, strand, upper)
            path = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in points)
            ink = '#%02x%02x%02x' % color
            paths.append(f'<path class="track" d="{path}" stroke="{ink}"/>')
            for theme, preview in previews.items():
                ImageDraw.Draw(preview).line([(x * 2, y * 2) for x, y in points],
                    fill=(*color, THEMES[theme]['line_alpha']), width=4)
            if strand in (1, 5):
                delay = -(strand * .31 + (0 if upper else 1.3))
                direction = 'normal' if upper else 'reverse'
                paths.append(f'<path class="pulse" d="{path}" pathLength="100" stroke="{ink}" '
                    f'stroke-width="3.2" stroke-dasharray="12 88" opacity=".95" '
                    f'style="animation-delay:{delay}s;animation-direction:{direction}"/>')
        offset = 0 if upper else -2.88
        layers.append(f'<g class="ribbon" style="animation-delay:{offset}s">' + ''.join(paths) + '</g>')
    styles = ('.track{opacity:.392}.dark-ink{display:none}'
              '@media(prefers-color-scheme:dark){.track{opacity:.588}.light-ink{display:none}.dark-ink{display:inline}}')
    motion = ('.pulse{animation:travel 5.76s linear infinite}.ribbon{animation:sway 5.76s ease-in-out infinite}'
              '@keyframes travel{to{stroke-dashoffset:-100}}'
              '@keyframes sway{0%,100%{transform:translateY(-4px)}50%{transform:translateY(4px)}}'
              '@media(prefers-reduced-motion:reduce){.pulse,.ribbon{animation:none}}')
    images = ''.join(f'<image class="{theme}-ink" width="{width}" height="{height}" '
                     f'xlink:href="data:image/png;base64,{raster}"/>' for theme, (_, raster) in raster_images.items())
    for animated in (True, False):
        filename = name + ('' if animated else '-static') + '.svg'
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
               '<title id="title">Anyi — Vision, Agents, Open Source</title>'
               '<desc id="desc">Original handwritten signature and flowing colored lines on a transparent canvas.</desc>'
               f'<metadata>{ORIGIN}</metadata><style>{styles}{motion if animated else ""}</style>'
               '<g fill="none" stroke-width="2" stroke-linecap="round">' + ''.join(layers) + '</g>' + images + '</svg>')
        (ASSETS / filename).write_text(svg + '\n')
        print(f'{filename}: {(ASSETS / filename).stat().st_size:,} bytes')
    # Local proofs make the actual canvas alpha independently inspectable.
    proof_root = ROOT / 'output' / 'flow-proofs'
    proof_root.mkdir(parents=True, exist_ok=True)
    for theme, preview in previews.items():
        proof = Image.alpha_composite(preview.resize((width, height), Image.Resampling.LANCZOS), raster_images[theme][0])
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('impeccable:prompt', ORIGIN)
        proof.save(proof_root / f'{name}-{theme}.png', pnginfo=metadata)


def action_buttons():
    icons = {
        'learn': '<path d="M4 5.5c3-1 5-.5 8 1 3-1.5 5-2 8-1v14c-3-1-5-.5-8 1-3-1.5-5-2-8-1zM12 6.5v14"/>',
        'projects': '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-14-2 16"/>',
        'email': '<rect x="2" y="4" width="20" height="16" rx="3"/><path d="m3 6 9 7 9-7"/>',
    }
    for name, label in [('learn', 'Learn'), ('projects', 'Projects'), ('email', 'Email')]:
        title = f'{label} — Anyi'
        labels = label_layers(160, 54, [(label, 55, 27, 'lm')], 18, '#245c45', '#b8e5cc', bold=True)
        text_images = ''.join(f'<image class="text-{theme}" width="160" height="54" href="data:image/png;base64,{raster}"/>'
                              for theme, raster in labels)
        theme_styles = (
            '.surface{fill:#f6faf8;stroke:#c5dacf}.symbol{stroke:#245c45}.text-dark{display:none}.accent{stroke:#54a381}'
            '@media(prefers-color-scheme:dark){.surface{fill:#17271f;stroke:#385644}.text-light{display:none}.text-dark{display:inline}.symbol{stroke:#b8e5cc}}')
        motion_styles = (
            '.accent{animation:edge 6s linear infinite}@keyframes edge{to{stroke-dashoffset:-240}}'
            '@media(prefers-reduced-motion:reduce){.accent{animation:none}}')
        for animated in (True, False):
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="160" height="54" viewBox="0 0 160 54" role="img">'
                f'<title>{title}</title><metadata>Original action graphic for the GitHub profile; self-contained vector icon and subtle moving edge.</metadata>'
                f'<style>{theme_styles}{motion_styles if animated else ""}</style>'
                '<rect class="surface" x=".75" y=".75" width="158.5" height="51" rx="12" stroke-width="1.5"/>'
                f'<g class="symbol" transform="translate(20 15)" fill="none" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round">{icons[name]}</g>'
                + text_images +
                '<path class="accent" d="M20 51H140" fill="none" stroke-width="1.8" stroke-dasharray="20 100"/>'
                '</svg>')
            filename = f'action-{name}' + ('' if animated else '-static') + '.svg'
            (ASSETS / filename).write_text(svg + '\n')


def technology_band(mobile: bool):
    # Preserve upstream logo paths, remove the old square backgrounds, and
    # arrange them on one shared line with understated animated accents.
    ns = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', ns)
    source = ET.parse(ASSETS / 'tech-stack-light.svg').getroot()
    originals = [child for child in source if child.tag == f'{{{ns}}}svg']
    assert len(originals) == 6
    width, height = (360, 150) if mobile else (600, 100)
    root = ET.Element(f'{{{ns}}}svg', {'width': str(width), 'height': str(height),
        'viewBox': f'0 0 {width} {height}', 'role': 'img', 'aria-labelledby': 'title'})
    ET.SubElement(root, f'{{{ns}}}title', {'id': 'title'}).text = 'Python, PyTorch, OpenCV, TypeScript, Vue and Linux'
    ET.SubElement(root, f'{{{ns}}}metadata').text = 'Source: tandpfun/skill-icons under MIT. Original paths arranged on transparent canvas with labels and animated underlines.'
    theme_styles = (
        '.text-dark{display:none}.base{stroke:#dbe8df}.accent{stroke:#58a786}'
        '@media(prefers-color-scheme:dark){.text-light{display:none}.text-dark{display:inline}.base{stroke:#334b3b}}')
    motion_styles = (
        '.accent{animation:pass 6s linear infinite}@keyframes pass{to{stroke-dashoffset:-64}}'
        '@media(prefers-reduced-motion:reduce){.accent{animation:none}}')
    style = ET.SubElement(root, f'{{{ns}}}style')
    names = ['Python', 'PyTorch', 'OpenCV', 'TypeScript', 'Vue', 'Linux']
    columns = 3 if mobile else 6
    cell_width = width / columns
    for index, (original, name) in enumerate(zip(originals, names)):
        x = index % columns * cell_width
        y = index // columns * 75
        icon = copy.deepcopy(original)
        for child in list(icon):
            if child.tag == f'{{{ns}}}rect' and child.get('fill') == '#F4F2ED':
                icon.remove(child)
        # Upstream assets may reuse gradient ids; prefix each icon independently.
        for element in icon.iter():
            if 'id' in element.attrib:
                element.set('id', f'icon{index}-' + element.get('id'))
            for key, value in list(element.attrib.items()):
                if 'url(#' in value:
                    element.set(key, value.replace('url(#', f'url(#icon{index}-'))
        icon.set('x', str(x + (cell_width - 42) / 2))
        icon.set('y', str(y + 3))
        icon.set('width', '42')
        icon.set('height', '42')
        root.append(icon)
        for kind in ['base', 'accent']:
            attrs = {'class': kind, 'd': f'M{x + cell_width / 2 - 24} {y + 69}h48', 'fill': 'none', 'stroke-width': '1.5'}
            if kind == 'accent':
                attrs.update({'stroke-dasharray': '12 52', 'style': f'animation-delay:-{index * .7}s'})
            ET.SubElement(root, f'{{{ns}}}path', attrs)
    labels = label_layers(width, height, [(name, index % columns * cell_width + cell_width / 2,
        index // columns * 75 + 56, 'mm') for index, name in enumerate(names)], 14, '#5b7068', '#b7cdc0')
    for theme, raster in labels:
        ET.SubElement(root, f'{{{ns}}}image', {'class': 'text-' + theme, 'width': str(width),
            'height': str(height), 'href': 'data:image/png;base64,' + raster})
    for animated in (True, False):
        style.text = theme_styles + (motion_styles if animated else '')
        filename = 'technologies' + ('-mobile' if mobile else '') + ('' if animated else '-static') + '.svg'
        (ASSETS / filename).write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True))


def project_links(mobile: bool):
    """Borderless repository links, with a narrower composition for phones."""
    width, height = (136, 52) if mobile else (228, 52)
    label_x, label_size = (30, 14) if mobile else (42, 17)
    icon_x, icon_size = (8, 16) if mobile else (12, 20)
    projects = [
        ('mslkad', 'MSLKAD', 'MSLKAD', '#3576eb',
         '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 9h10M7 13h7M7 17h4"/>'),
        ('cdmir', 'CDMIR', 'CDMIR', '#9a6fdd',
         '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m3 17 5-5 4 4 4-6 5 7M15 6v2"/>'),
        ('converter', 'Converter', 'Dialogue Converter', '#16a692',
         '<path d="M4 8h16m-4-4 4 4-4 4M20 16H4m4-4-4 4 4 4"/>'),
        ('docs', 'Docs', 'AnyiAI Docs', '#e29b3c',
         '<path d="M3 4.5c3-1 6-.5 9 1 3-1.5 6-2 9-1v15c-3-1-6-.5-9 1-3-1.5-6-2-9-1zM12 5.5v15"/>'),
    ]
    for slug, label, title, accent, icon in projects:
        labels = label_layers(width, height, [(label, label_x, 24, 'lm')], label_size,
                              '#245c45', '#b8e5cc', bold=True)
        text_images = ''.join(
            f'<image class="text-{theme}" width="{width}" height="{height}" '
            f'href="data:image/png;base64,{raster}"/>' for theme, raster in labels)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">'
            f'<title>{title}</title>'
            '<metadata>Original borderless project link graphic for Anyi. Embedded Manrope lettering, '
            'vector icon and directional arrow on a transparent canvas. Static and theme-aware.</metadata>'
            '<style>.symbol{stroke:#245c45}.rule{stroke:#dbe8df}.text-dark{display:none}'
            '@media(prefers-color-scheme:dark){.symbol{stroke:#b8e5cc}.rule{stroke:#334b3b}'
            '.text-light{display:none}.text-dark{display:inline}}</style>'
            f'<g class="symbol" transform="translate({icon_x} {24 - icon_size / 2}) scale({icon_size / 24})" '
            f'fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icon}</g>'
            + text_images +
            f'<path class="symbol" d="M{width - 22} 29l8-8m-8 0h8v8" '
            'fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path class="rule" d="M8 47H{width - 8}" fill="none" stroke-width="1"/>'
            f'<path d="M8 47H36" stroke="{accent}" fill="none" stroke-width="2" stroke-linecap="round"/>'
            '</svg>')
        filename = f'project-{slug}' + ('-mobile' if mobile else '') + '.svg'
        (ASSETS / filename).write_text(svg + '\n')


if __name__ == '__main__':
    render(False)
    render(True)
    action_buttons()
    technology_band(False)
    technology_band(True)
    project_links(False)
    project_links(True)
