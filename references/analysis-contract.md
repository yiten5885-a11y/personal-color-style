# Analysis contract

## Photo check

A usable primary photo should show the face clearly, without beauty filters, strong colored light, extreme exposure, or large occlusions. Neutral daylight or neutral indoor light is preferable. A gray card, standardized camera, or controlled draping session can improve color measurement, but this Skill does not require or simulate laboratory measurement.

Record limitations before making a styling hypothesis. Common limits include makeup, dyed hair, tinted glasses, warm indoor light, cool phone processing, backlighting, deep shadows, compression, and a face that occupies too little of the image.

Use these confidence levels:

- `高`: several relevant cues are clear under neutral-looking light and point in the same direction;
- `中`: the image is usable but one or more important variables remain uncontrolled;
- `低`: the image is strongly limited or two seasonal directions remain plausible.

A `limited` photo cannot support a high-confidence result in the manifest.

## Reasoning layers

Keep the following layers distinct:

1. **Visible observations**: apparent contrast between hair, skin, lips, and eyes; apparent warmth or coolness under the current light; apparent value and chroma relationships.
2. **Styling hypotheses**: colors, contrast levels, finishes, and combinations likely to create a requested effect.
3. **User-provided facts**: natural hair color, known foundation match, dye history, usual jewelry preference, and the user's own successful or unsuccessful colors.

Do not convert an observation from one photograph into a permanent physical fact. Do not invent invisible details or use generated variants as new diagnostic evidence.

## Four-axis model

Record each axis as a label and a value from 0 to 100:

- `temperature`: 0 is cooler, 100 is warmer;
- `value`: 0 is deeper, 100 is lighter;
- `chroma`: 0 is softer, 100 is brighter;
- `contrast`: 0 is lower contrast, 100 is higher contrast.

The numeric value is a visual placement for the report, not an instrument reading. Keep labels natural and avoid false precision in prose.

## Seasonal direction

The four-season or twelve-season label is a styling framework. Use it to organize recommendations, not as a scientific identity classification.

- When evidence is coherent, name a primary season or subtype and explain three to six concise reasons.
- When evidence is mixed, state a primary candidate plus an alternative and explain what better photo or real draping comparison could resolve it.
- When the photo is inadequate, provide only an exploratory palette and request improved input for a stronger conclusion.

The report must carry the same seasonal direction, confidence, palette logic, and uncertainty through all three cards.

## Recommendation rules

- Create core, exploratory, and caution groups from the current analysis; keep them distinct.
- A caution color means it may need a smaller area, separation from the face, another texture, or a balancing color. It is not a universal ban.
- Include more than one usable style direction inside the selected color range.
- Makeup, hair, eyewear, metals, and outfit formulas must match the same temperature, value, chroma, and contrast logic.
- Treat brand shades, screen colors, printing, hair dye, lenses, fabrics, and cosmetics as approximate. Use descriptive color names plus hex values for layout, not as purchasing guarantees.
