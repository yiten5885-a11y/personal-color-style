# Three-card report contract

Use the JSON manifest consumed by `scripts/validate_manifest.py` and `scripts/render_report.py`. Paths must be relative to the manifest file, stay inside its directory, and point to decodable local images.

## Shared report fields

- `schema_version`: integer `1`.
- `report.title` and `report.subtitle`: short titles.
- `report.photo_quality`: `good` or `limited`.
- `report.limitations`: zero to four concise items.
- `analysis.season_label`, `season_english`, `confidence`, `alternative`, and `summary`.
- `analysis.evidence`: three to six concise reasons.
- `analysis.axes`: `temperature`, `value`, `chroma`, and `contrast`; each contains `label` and an integer `value` from 0 to 100.
- `analysis.keywords`: five to eight case-specific style words.
- `analysis.style_direction`: `primary`, `explore`, and `caution`.
- `assets.portrait`: the approved primary portrait.

## Card 1 color and style overview

Show the portrait as the main visual, seasonal direction and confidence, four-axis chart, evidence chain, keywords, style direction, three palette groups, and a concise summary.

`palette.core`, `palette.extend`, and `palette.caution` each contain five to eight objects with `name` and six-digit `hex`. Do not repeat the same color name or hex across groups.

## Card 2 draping and outfits

Show three draping groups using the exact same portrait crop, followed by three or four outfit applications. The renderer colors the drape from the first colors in each palette group.

Required fields:

- `draping.core_note`, `extend_note`, and `caution_note`;
- `draping.looks`: three or four objects with `title`, `scene`, `description`, and `image`;
- `draping.formulas`: six to ten concise outfit color formulas;
- `draping.items`: four to eight practical item or material suggestions;
- `draping.avoid`: four to six caution notes;
- `draping.summary`.

The outfit images must depict the same authorized person. They may change clothing and styling while preserving identity and realistic body proportions.

## Card 3 makeup hair and details

Required fields:

- `beauty.makeup`: exactly `base`, `brow`, `eye`, `blush`, and `lip`; each contains `direction` and two to four color objects;
- `beauty.looks`: three or four objects with `title`, `scene`, `description`, and `image`;
- `beauty.hair`: exactly `safe`, `brightening`, `explore`, and `caution`; each contains two to four color objects;
- `beauty.accessories`: four to eight concise material, metal, eyewear, or accessory suggestions;
- `beauty.avoid`: six to ten caution notes;
- `beauty.summary`.

Generated makeup examples must use the same person and remain recognizable. Hair suggestions are design previews; they do not promise an exact salon result.

## Asset generation

Generate pictures without titles, labels, arrows, watermarks, brand marks, or other embedded text. Use one visual concept per file and let the renderer add the final Chinese typography.

For each generated variation, keep camera angle, crop, facial proportions, age cues, and skin tone consistent with the source. When comparing colors, do not change facial exposure, white balance, texture, expression, or contour.

## Draft and final modes

`--mode draft` validates structure and allows missing asset files so content can be prepared before generation. `--mode final` requires the portrait and every look image to exist and decode. Only a final manifest may be used for delivery.
