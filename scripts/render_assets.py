"""Render transparent, theme-aware SVG artwork for the GitHub profile.

Native SVG/CSS animation and the original handwritten logo. No scripts,
external assets, network requests or model calls are used by the artwork.
"""

from __future__ import annotations

import base64
import io
import math
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
ORIGIN = ('Origin: original transparent vector color-flow animation surrounding the preserved '
          'Anyi handwritten wordmark. Designed for GitHub default white pages. The embedded '
          'artwork inherits the host color scheme and provides narrow-screen and static '
          'alternatives. No screenshots, project demos, scripts or external services.')


def wordmark(ink: tuple[int, int, int]) -> Image.Image:
    image = Image.open(ASSETS / 'anyi-wordmark.png').convert('RGBA')
    pixels = np.asarray(image).copy()
    gold = (pixels[:, :, 0] > pixels[:, :, 1]) & (pixels[:, :, 3] > 0)
    pixels[:, :, :3] = ink
    pixels[gold, :3] = (214, 160, 48)
    return Image.fromarray(pixels).crop(image.getbbox())


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
    mark.thumbnail((455, 158) if mobile else (560, 186), Image.Resampling.LANCZOS)
    image = Image.new('RGBA', (width, height))
    image.alpha_composite(mark, ((width - mark.width) // 2, round(height * .45 - mark.height / 2)))
    subtitle = 'Vision  /  Agents  /  Open Source' if mobile else 'Computer Vision  /  AI Agents  /  Open Source'
    font = ImageFont.truetype(str(ASSETS / 'fonts/manrope-400.ttf'), 23 if mobile else 24)
    pen = ImageDraw.Draw(image)
    box = pen.textbbox((0, 0), subtitle, font=font)
    pen.text(((width - box[2]) / 2, height * .73), subtitle, font=font, fill=(*settings['caption'], 255))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return image, base64.b64encode(buffer.getvalue()).decode()


def render(mobile: bool):
    width, height = (720, 390) if mobile else (1280, 360)
    name = 'flow-mobile' if mobile else 'flow'
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


if __name__ == '__main__':
    render(False)
    render(True)
