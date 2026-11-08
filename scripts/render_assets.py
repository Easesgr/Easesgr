"""Render the profile's animated identity using geometry and the original logo.

Requires requirements-assets.txt. No model calls or project-image downloads.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
MINT = (173, 249, 212)
CYAN = (79, 204, 210)
VIOLET = (148, 127, 228)
ORIGIN = ('Origin: original deterministic orbital light trails, star field and scan-light '
          'animation around the existing Anyi handwritten wordmark. Revised at the user request '
          'for a visually striking personal profile with minimal project detail. No project '
          'screenshots, fabricated data or model-generated imagery.')


def wordmark() -> Image.Image:
    image = Image.open(ASSETS / 'anyi-wordmark.png').convert('RGBA')
    pixels = np.asarray(image).copy()
    gold = (pixels[:, :, 0] > pixels[:, :, 1]) & (pixels[:, :, 3] > 0)
    pixels[:, :, :3] = MINT
    pixels[gold, :3] = (244, 207, 118)
    image = Image.fromarray(pixels)
    return image.crop(image.getbbox())


def orbit(width: int, height: int, tilt: float, spread: float):
    angles = np.linspace(0, math.tau, 240)
    x = width * spread * np.cos(angles)
    y = height * .17 * np.sin(angles)
    cosine, sine = math.cos(tilt), math.sin(tilt)
    return [(width / 2 + a * cosine - b * sine, height * .44 + a * sine + b * cosine)
            for a, b in zip(x, y)]


def background(width: int, height: int):
    yy, xx = np.mgrid[:height, :width]
    glow = np.exp(-(((xx - width * .49) / (width * .36)) ** 2 +
                    ((yy - height * .47) / (height * .55)) ** 2) * 1.8)
    pixels = np.empty((height, width, 3), dtype=np.uint8)
    for channel, (base, light) in enumerate([(5, 8), (12, 20), (15, 16)]):
        pixels[:, :, channel] = base + glow * light
    return Image.fromarray(pixels)


def hero(mobile: bool):
    width, height = (720, 540) if mobile else (1280, 420)
    base = background(width, height)
    mark = wordmark()
    mark.thumbnail((460, 160) if mobile else (570, 180), Image.Resampling.LANCZOS)
    mark_position = ((width - mark.width) // 2, round(height * .43 - mark.height / 2))
    mask = Image.new('L', (width, height))
    mask.paste(mark.getchannel('A'), mark_position)
    soft_logo = Image.new('RGB', (width, height), MINT)
    logo_halo = mask.filter(ImageFilter.GaussianBlur(16)).point(lambda value: value // 4)
    base.paste(soft_logo, (0, 0), logo_halo)

    rng = np.random.default_rng(2411 if mobile else 1706)
    stars = [(rng.uniform(.035, .965) * width, rng.uniform(.07, .9) * height,
              rng.uniform(.7, 1.6), rng.uniform(0, math.tau)) for _ in range(58)]
    paths = [orbit(width, height, tilt, .38 if mobile else .355)
             for tilt in ((-.28, .32) if mobile else (-.16, .16))]
    regular = ImageFont.truetype(str(ASSETS / 'fonts/manrope-400.ttf'), 24 if mobile else 25)
    role = 'Vision  /  Agents  /  Open Source' if mobile else 'Computer Vision  /  AI Agents  /  Open Source'
    label = Image.new('RGBA', (width, height))
    draw = ImageDraw.Draw(label)
    box = draw.textbbox((0, 0), role, font=regular)
    draw.text(((width - box[2]) / 2, height * .80), role, font=regular, fill=(178, 205, 201, 255))

    frames = []
    for index in range(84):
        phase = index / 84
        image = base.copy()
        ink = ImageDraw.Draw(image)
        for x, y, radius, offset in stars:
            brightness = .45 + .25 * math.sin(phase * math.tau + offset)
            color = tuple(round(value * brightness) for value in MINT)
            ink.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        luminous = Image.new('RGBA', (width, height))
        pen = ImageDraw.Draw(luminous)
        for route, (points, tint) in enumerate(zip(paths, (CYAN, VIOLET))):
            ink.line(points, fill=tuple(value // 6 for value in tint), width=1)
            for strand in range(2):
                head = int(((phase * (1 if route == 0 else -1) + strand * .5 + route * .2) % 1) * len(points))
                for tail in range(54, -1, -1):
                    point = points[(head - tail) % len(points)]
                    opacity = int(220 * (1 - tail / 55) ** 2)
                    pen.ellipse((point[0] - 1.4, point[1] - 1.4, point[0] + 1.4, point[1] + 1.4),
                                fill=(*tint, opacity))
                x, y = points[head]
                pen.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(*MINT, 255))
        image = Image.alpha_composite(image.convert('RGBA'), luminous.filter(ImageFilter.GaussianBlur(5)))
        image = Image.alpha_composite(image, luminous)
        image.paste(mark, mark_position, mark)

        # One soft highlight crosses the existing letter strokes per loop.
        sweep_x = width * ((phase + .18) % 1)
        xx = np.arange(width)
        strip = (np.exp(-((xx - sweep_x) / (width * .04)) ** 2) * 90).astype(np.uint8)
        sweep = np.tile(strip, (height, 1))
        alpha = Image.fromarray((sweep.astype(np.uint16) * np.asarray(mask) // 255).astype(np.uint8))
        highlight = Image.new('RGBA', (width, height), (237, 255, 247, 0))
        highlight.putalpha(alpha)
        image = Image.alpha_composite(image, highlight)
        image = Image.alpha_composite(image, label)
        frames.append(image.convert('RGB'))

    name = 'orbit-mobile' if mobile else 'orbit'
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('impeccable:prompt', ORIGIN)
    frames[22].save(ASSETS / (name + '-static.png'), pnginfo=metadata, optimize=True)
    palette_source = Image.new('RGB', (width, height * 3))
    for row, sample in enumerate((0, 22, 50)):
        palette_source.paste(frames[sample], (0, row * height))
    palette = palette_source.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(ASSETS / (name + '.gif'), save_all=True, append_images=indexed[1:],
                    duration=80, loop=0, optimize=True, disposal=1, comment=ORIGIN.encode())


if __name__ == '__main__':
    hero(False)
    hero(True)
    for name in ('orbit.gif', 'orbit-mobile.gif', 'orbit-static.png', 'orbit-mobile-static.png'):
        print(f'{name}: {(ASSETS / name).stat().st_size:,} bytes')
