---
name: personal-color-style
description: Create a three-image personal color and styling guide from an authorized portrait, with photo-quality limits, identity-consistent visual variants, structured palettes, outfit applications, and makeup, hair, and accessory guidance. Use for 个人色彩, 四季色彩, seasonal color, 配色诊断, or color-led image styling reports. Do not use for medical skin assessment or laboratory color measurement.
---

# Personal Color Style

Turn an authorized portrait into three separate 3:4 report images: a color and style overview, color draping with outfit applications, and makeup, hair, and accessory guidance. Deliver the images unless the user explicitly asks only for analysis or a reusable prompt.

## Inputs

Require one readable portrait that the user is authorized to use. Ask for a better photo when the face is too small, heavily filtered, strongly color-cast, deeply shadowed, or partly hidden. When the photo is usable but limited, continue only with an explicit low-confidence or candidate-direction result.

Use user-provided preferences for presentation, clothing expression, makeup coverage, output language, and style. Do not infer gender identity or force the source document's feminine styling. Adapt the modules to the person's stated preferences.

Read [references/analysis-contract.md](references/analysis-contract.md) before analyzing a portrait. Read [references/report-contract.md](references/report-contract.md) before writing the manifest or generating visual assets. Read [references/quality-and-privacy.md](references/quality-and-privacy.md) before final delivery or any requested publication.

## Workflow

1. Inspect the portrait. Confirm that it can support a head-and-shoulders crop and record visible lighting, filter, makeup, hair-color, and image-quality limits.
2. Separate three kinds of statements: visible observations, styling hypotheses, and user-provided facts. Assign confidence to the overall seasonal direction and keep weak dimensions explicitly uncertain.
3. Choose a season or subtype only when the photo supports it. If two directions remain plausible, present a primary candidate and an alternative instead of forcing a unique answer.
4. Build a manifest that satisfies [references/report-contract.md](references/report-contract.md). Generate every palette, formula, makeup color, hair color, and accessory recommendation from this case; do not begin from a fixed warm, muted, brown, pink, or Korean-style template.
5. Create visual assets without embedded text. Use the portrait as the identity reference for every generated outfit or makeup image. Keep the face, skin tone, age cues, facial proportions, hair direction, and camera character stable unless that page explicitly changes makeup or hair color.
   If image generation or editing is unavailable, stop at a draft manifest and report the unavailable provider or tool. Do not substitute synthetic fixtures, copied examples, text-only cards, or unchanged duplicates and call the personal report complete.
6. For the draping comparison, reuse the exact same portrait crop. Let `scripts/render_report.py` change only the surrounding drape color. Do not darken, yellow, smooth, relight, or reshape the face to manufacture proof.
7. Inspect each generated asset before layout. Replace identity drift, altered skin tone, changed age, malformed clothing or accessories, text artifacts, and an outfit or makeup treatment that contradicts its label.
8. Validate the completed manifest in final mode, then render the three cards:

```bash
python3 scripts/validate_manifest.py report.json --mode final
python3 scripts/render_report.py report.json --output-dir output/personal-color-series
```

9. Open all three full-size PNG files. Check identity consistency, exact 3:4 dimensions, readable Chinese, palette-to-copy consistency, image-to-label consistency, and absence of clipped or overlapping content.
10. Deliver all three images as separate files. Keep the source portrait and intermediate generated assets out of Git and public repositories. Treat generation and publication as different actions.

## Output contract

The standard result is exactly three 1800 x 2400 PNG files:

- `01-color-style-overview.png`
- `02-draping-and-outfits.png`
- `03-makeup-hair-details.png`

The renderer uses deterministic typography and emits no inherited image metadata. It refuses an existing output directory and fails when required content, assets, or readable CJK fonts are unavailable.

Use draft validation only while preparing content. A draft render with synthetic or missing visual assets is development evidence, not a completed user report.

## Boundaries

- Describe this as a photograph-based styling reference. Do not claim scientific, medical, biometric, dermatological, or laboratory-grade diagnosis.
- Do not infer health, ethnicity, personality, income, social value, or objective attractiveness from appearance.
- Do not treat lighter skin as inherently better. Discuss harmony, contrast, clarity, or the requested aesthetic effect.
- Do not promise that generated makeup, dye, contact-lens, or clothing colors will look identical in real products or real lighting.
- Do not reuse a generated face as evidence that a recommendation is accurate.
- Do not publish the portrait, report, or personal fields without explicit authorization for that publication target.

## Completion evidence

Report these states separately:

- manifest validation passed;
- three images rendered and decoded at 1800 x 2400;
- all three images visually reviewed;
- identity preservation assessed visually as best effort;
- image generation availability or the exact blocking failure;
- user testing result;
- public publication state, only when separately authorized and verified.
