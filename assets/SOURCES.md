# Asset sources

- `anyi-wordmark.png`: regenerated **Anyi-only** version of the [original handwritten brand](https://github.com/Easesgr/anyiai-docs/blob/bcd2201988682aed1459ee1c7e91d356b6e60c97/src/.vuepress/public/logo.svg). The separate final “Ai” is removed. The original first four letters and bird remain, with the existing gold heart placed above the i. Transparent canvas and source metadata are preserved.
- `signature.svg`, `signature-mobile.svg` and their static variants: original color-flow animation surrounding the new Anyi wordmark. All images are embedded and the artwork adapts to the host light/dark theme.
- `action-*.svg`: original vector link buttons and slow moving edge accents; the artwork names the link action.
- `technologies*.svg`: logos from [Skill Icons](https://github.com/tandpfun/skill-icons), with its included MIT license, rearranged on transparent backgrounds with labels and animated underlines. `tech-stack-light.svg` is retained as the upstream source for regeneration.
- `project-*.svg`: original transparent repository-link graphics with embedded Manrope labels, vector icons, directional arrows and colored rules. Desktop and mobile compositions preserve the four individual repository links. These graphics are static.
- `fonts/`: Manrope, under the included SIL Open Font License.

Regenerate the profile graphics:

```sh
python3 -m pip install -r requirements-assets.txt
python3 scripts/render_assets.py
```

SVG artwork includes source metadata and has no scripts or remote dependencies. The README selects static alternatives for every animated image under reduced motion, plus narrower header/technology layouts below 600 CSS pixels. Project links remain native HTML links.
