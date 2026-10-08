# Quality and privacy

## Identity and visual review

Image generation preserves identity only on a best-effort basis. Compare every variant directly with the source portrait. Reject changes to facial structure, age, ethnicity, skin tone, distinctive marks, or body proportions. Reject waxy skin, malformed hands, impossible clothing, unreadable embedded text, and accessories that conflict with the recommendation.

Use the exact source crop for draping previews. A generated face under a recommended color and a deliberately degraded face under a caution color would be circular evidence and must not be used.

## Text and layout

The final text belongs in the deterministic renderer. Verify every visible heading, label, color name, formula, and note against the manifest. At full size and fit-to-screen, check that text remains readable and no content clips, overlaps, or leaves the canvas.

All three files must be separate 1800 x 2400 PNG images. They must share one title system, accent palette, spacing system, seasonal direction, and subject identity.

## Privacy

- Use only portraits the user is authorized to use.
- Keep originals unchanged and write new files.
- Do not put portraits, generated variants, personal names, or report manifests containing personal details in Git, test fixtures, or public repositories.
- Use synthetic fixtures for automated tests.
- Strip inherited metadata from rendered outputs. Do not retain GPS, camera, EXIF, or document-author fields.
- Do not create face databases, identity scores, or persistent biometric profiles.

## Publication

Creating the three images does not authorize posting them. Before a public upload, verify the exact images, account, title, caption, audience, and platform with the user. A local render, ZIP file, Git commit, or public Skill repository does not prove that a personal report was published.

## Completion gate

Before delivery, require all of the following:

1. final manifest validation passes;
2. exactly three PNG files exist and decode at 1800 x 2400;
3. all three files were visually inspected;
4. the same seasonal direction and palette logic appear across the set;
5. all visual variants remain recognizably the same person;
6. draping comparisons use an unchanged portrait crop;
7. visible text matches the manifest;
8. output metadata contains no inherited personal metadata.

If the image-generation step fails, none of these gates may be inferred from the manifest or renderer alone. Preserve the draft for repair, identify the failed step, and keep the report state incomplete until real visual assets are generated and reviewed.
