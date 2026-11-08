# Asset sources

- `anyi-wordmark.png`: original handwritten Anyi logo from [anyiai-docs](https://github.com/Easesgr/anyiai-docs/blob/bcd2201988682aed1459ee1c7e91d356b6e60c97/src/.vuepress/public/logo.svg), keeping the letterforms, bird and heart.
- `flow.svg`, `flow-mobile.svg` and their static SVG alternatives: original deterministic color-flow animation on a fully transparent canvas, designed for GitHub’s default white page and rendered by `scripts/render_assets.py`. They are decorative personal-profile graphics; no experimental data or project screenshots.
- `tech-stack-*.svg`: six technology icons from [Skill Icons](https://github.com/tandpfun/skill-icons), with its included license. The two versions adapt to GitHub light/dark themes.
- `fonts/`: Manrope, under the included SIL Open Font License.

Regenerate the banner with:

```sh
python3 -m pip install -r requirements-assets.txt
python3 scripts/render_assets.py
```

The README selects the static header when reduced motion is requested, and a separate composition below 600 CSS pixels. Embedded SVG source metadata documents the rendering recipe. The SVG inherits the host page’s color scheme internally, so the default white page uses the original dark green letterforms without relying on combined GitHub picture conditions.
