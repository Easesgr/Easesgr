# Asset sources

- `anyi-wordmark.png`: original handwritten Anyi logo from [anyiai-docs](https://github.com/Easesgr/anyiai-docs/blob/bcd2201988682aed1459ee1c7e91d356b6e60c97/src/.vuepress/public/logo.svg), keeping the letterforms, bird and heart.
- `orbit*.gif` and `orbit*-static.png`: original deterministic orbital light trails, stars and a soft highlight on the preserved wordmark, rendered by `scripts/render_assets.py`. They are decorative personal-profile graphics; no experimental data or project screenshots.
- `tech-stack-*.svg`: six technology icons from [Skill Icons](https://github.com/tandpfun/skill-icons), with its included license. The two versions adapt to GitHub light/dark themes.
- `fonts/`: Manrope, under the included SIL Open Font License.

Regenerate the banner with:

```sh
python3 -m pip install -r requirements-assets.txt
python3 scripts/render_assets.py
```

The README selects the static header when reduced motion is requested, and a separate composition below 600 CSS pixels. GIF comments and PNG metadata document the original rendering recipe.
