"""Render the GitHub profile's original graphics and public project previews.

Requires Pillow and numpy. Run from any directory with Python 3.10+.
The GIFs are deterministic graphics, not model-generated images.
"""

from __future__ import annotations

import math
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
SOURCES = ROOT / 'output' / 'research'
BACKGROUND = '#071811'
PANEL = '#10291e'
RULE = '#2c503c'
MINT = '#b6f5cf'
GREEN = '#57dc98'
AMBER = '#e9c36d'
MUTED = '#a4c7b3'
REGULAR = ASSETS / 'fonts/manrope-400.ttf'
BOLD = ASSETS / 'fonts/manrope-700.ttf'
ORIGIN = ('Origin: deterministic Pillow rendering of the user-confirmed dark research bench, '
          'using the existing Anyi handwritten wordmark from Easesgr/anyiai-docs. '
          'Three labeled paths represent public research, tools and learning resources. '
          'No measured data, model-generated imagery or third-party stats services.')


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)


def text(draw: ImageDraw.ImageDraw, xy, value: str, size: int, color=MINT, bold=False):
    draw.text(xy, value, font=font(size, bold), fill=color)


def source(name: str, url: str) -> Image.Image:
    path = SOURCES / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=30) as response:
            path.write_bytes(response.read())
    return Image.open(path).convert('RGB')


def png(image: Image.Image, name: str, origin: str = ORIGIN):
    info = PngImagePlugin.PngInfo()
    info.add_text('impeccable:prompt', origin)
    image.save(ASSETS / name, pnginfo=info, optimize=True)


def exif(origin: str) -> Image.Exif:
    metadata = Image.Exif()
    metadata[0x010E] = origin
    return metadata


def provenance(name: str, origin: str):
    (ASSETS / (name + '.json')).write_text(json.dumps({'prompt': origin}, indent=2) + '\n')


def wordmark() -> Image.Image:
    image = Image.open(ASSETS / 'anyi-wordmark.png').convert('RGBA')
    pixels = np.asarray(image).copy()
    amber = (pixels[:, :, 0] > pixels[:, :, 1]) & (pixels[:, :, 3] > 0)
    pixels[:, :, :3] = (182, 245, 207)
    pixels[amber, :3] = (233, 195, 109)
    image = Image.fromarray(pixels)
    return image.crop(image.getbbox())


def polyline_sample(points, fraction: float):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    distance = fraction * sum(lengths)
    for a, b, length in zip(points, points[1:], lengths):
        if distance <= length:
            ratio = distance / length
            return a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio
        distance -= length
    return points[-1]


def node(draw, center, radius=6, color=GREEN):
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def hero_base(mobile: bool):
    width, height = (720, 660) if mobile else (1280, 440)
    image = Image.new('RGB', (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    mark = wordmark()
    mark.thumbnail((480, 170) if not mobile else (460, 166), Image.Resampling.LANCZOS)
    image.paste(mark, (54, 54) if not mobile else (46, 44), mark)

    if mobile:
        text(draw, (48, 218), 'Research. Tools.', 42, bold=True)
        text(draw, (48, 270), 'Open knowledge.', 42, bold=True)
        endpoints = [(200, 448), (380, 448), (560, 448)]
        paths = [[(76, 370), (128, 370), (200, 408), (200, 448)],
                 [(76, 370), (258, 370), (380, 408), (380, 448)],
                 [(76, 370), (438, 370), (560, 408), (560, 448)]]
        labels = [('Vision', 144), ('Tools', 335), ('Learn', 513)]
        for label, x in labels:
            text(draw, (x, 480), label, 34, bold=True)
        draw.line((48, 565, 672, 565), fill=RULE, width=1)
        text(draw, (48, 600), 'Easesgr / Anyi', 28, MUTED)
        text(draw, (483, 600), 'Yunnan Univ.', 25, MUTED)
    else:
        text(draw, (58, 238), 'Image restoration.', 32, bold=True)
        text(draw, (58, 282), 'AI tools. Open knowledge.', 32, bold=True)
        endpoints = [(800, 102), (1052, 206), (850, 314)]
        paths = [[(620, 206), (690, 206), (740, 156), (740, 102), endpoints[0]],
                 [(620, 206), endpoints[1]],
                 [(620, 206), (690, 206), (740, 258), (740, 314), endpoints[2]]]
        text(draw, (826, 82), 'VISION', 27, bold=True)
        text(draw, (1078, 186), 'TOOLS', 27, bold=True)
        text(draw, (876, 294), 'LEARN', 27, bold=True)
        draw.line((58, 368, 1222, 368), fill=RULE, width=1)
        text(draw, (58, 390), 'Easesgr / Anyi', 23, MUTED)
        text(draw, (1011, 390), 'Yunnan University', 23, MUTED)

    for index, path in enumerate(paths):
        draw.line(path, fill=RULE, width=3, joint='curve')
        node(draw, endpoints[index], 7, AMBER if index == 2 else GREEN)
    node(draw, paths[0][0], 7, MINT)
    return image, paths


def hero(mobile: bool):
    base, paths = hero_base(mobile)
    frames = []
    for frame in range(72):
        image = base.copy()
        draw = ImageDraw.Draw(image)
        for index, points in enumerate(paths):
            phase = ((frame / 72) + index / 3) % 1
            color = AMBER if index == 2 else MINT
            for step in range(12, -1, -1):
                position = max(0, phase - step * .013)
                x, y = polyline_sample(points, position)
                node(draw, (x, y), 2 if step else 5, GREEN if step else color)
        frames.append(image)
    name = 'hero-mobile' if mobile else 'hero'
    png(frames[38], name + '-static.png')
    # A shared palette keeps thin traces and lettering stable between frames.
    palette = base.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(ASSETS / (name + '.gif'), save_all=True, append_images=indexed[1:],
                    duration=84, loop=0, optimize=True, disposal=1,
                    comment=ORIGIN.encode())


def deraining():
    original = source('mslkad-comparison.png',
        'https://raw.githubusercontent.com/Easesgr/MSLKAD/main/assets/figures/real-world-comparison.png')
    # The top row of the published Fig. 3, first (Input) and fifth (Ours) columns.
    rainy = original.crop((14, 36, 395, 260)).resize((1080, 635), Image.Resampling.LANCZOS)
    restored = original.crop((1611, 36, 1992, 260)).resize((1080, 635), Image.Resampling.LANCZOS)
    origin = ('Origin: Easesgr/MSLKAD assets/figures/real-world-comparison.png, Fig. 3. '
              'Top-row first (Input) and fifth (Ours) panels cropped at identical 381x224 sizes, '
              'resized with LANCZOS and revealed with a divider. No image enhancement or synthetic restoration.')
    frames = []
    for frame in range(72):
        # Pause at both ends, then move through the paired real figure crops.
        phase = frame / 72
        progress = (1 - math.cos(2 * math.pi * phase)) / 2
        x = round(1080 * (.04 + .92 * progress))
        image = Image.new('RGB', (1120, 742), BACKGROUND)
        image.paste(rainy, (20, 20))
        image.paste(restored.crop((x, 0, 1080, 635)), (20 + x, 20))
        draw = ImageDraw.Draw(image)
        draw.line((20 + x, 20, 20 + x, 655), fill=MINT, width=3)
        draw.rectangle((24, 32, 162, 80), fill=BACKGROUND)
        draw.rectangle((860, 32, 1088, 80), fill=BACKGROUND)
        text(draw, (38, 37), 'INPUT', 29, bold=True)
        text(draw, (885, 37), 'MSLKAD', 29, bold=True)
        text(draw, (30, 684), 'Single-image deraining', 26, bold=True)
        text(draw, (835, 684), 'ICIP 2026', 26, AMBER, bold=True)
        frames.append(image)
    # The still shows two equally sized halves with the same divider.
    frames[18].save(ASSETS / 'deraining-static.webp', quality=88, method=6,
                    exif=exif(origin))
    provenance('deraining-static.webp', origin)
    gif_frames = [frame.resize((840, 556), Image.Resampling.LANCZOS) for frame in frames]
    palette = gif_frames[18].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for frame in gif_frames]
    indexed[0].save(ASSETS / 'deraining.gif', save_all=True, append_images=indexed[1:],
                    duration=84, loop=0, optimize=True, disposal=1, comment=origin.encode())


def previews():
    rows = [('dialogue-converter.png', 'dialogue-preview.webp',
             'https://raw.githubusercontent.com/Easesgr/dialogue-converter/main/docs/images/demo.png', 1120),
            ('learning-site.png', 'learning-preview.webp',
             'https://raw.githubusercontent.com/Easesgr/anyiai-docs/main/docs/screenshots/home.png', 1440)]
    for source_name, target_name, url, width in rows:
        image = source(source_name, url)
        image.thumbnail((width, width), Image.Resampling.LANCZOS)
        description = 'Origin: existing public project screenshot, resized without altering its contents. ' + url
        image.save(ASSETS / target_name, quality=86, method=6,
                   exif=exif(description))
        provenance(target_name, description)


if __name__ == '__main__':
    ASSETS.mkdir(exist_ok=True)
    hero(False)
    hero(True)
    deraining()
    previews()
    for path in sorted(ASSETS.glob('*')):
        if path.is_file():
            print(f'{path.name}: {path.stat().st_size:,} bytes')
