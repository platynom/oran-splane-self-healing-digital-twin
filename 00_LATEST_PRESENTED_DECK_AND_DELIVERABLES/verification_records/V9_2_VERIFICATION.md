# v9.2 verification

Layout-only follow-up to deck-v9-2026-11 at 0f794439af090ab812e69b6a3b90f7bb3c8c2d69. All 46 slides were rendered with installed Microsoft PowerPoint to PNG and a 46-page view PDF.

## Identity and geometry

- Byte-level UTF-8 text-run differences against v9.1, in original per-slide run order: **0**. No whitespace normalization was used.
- Non-geometry slide XML differences after excluding position/extent transforms: **0**. Fonts, styles, wording, citations and table values are unchanged.
- Non-slide package parts changed: **0**; this includes notes, embedded media and relationships.
- Geometry findings: **0**. Checks cover slide bounds, actual PowerPoint TextFrame2 BoundHeight/BoundWidth text fit, text-box and text-ink intersections, and thin horizontal rules crossing text.
- Native font minimum findings: **0**, using the same body/source floors and intentional non-text backing exclusions as V9_1_VERIFICATION.md.
- 35 unchanged slide renders are pixel-identical to v9.1. The 11 changed slide renders correspond exactly to the changed slide XML parts.

## Whitespace and visual review

All 46 slide renders were visually reviewed in overview sheets; all 11 changed slides were additionally inspected at full resolution. The main source-bar-to-bottom-box region was checked for empty vertical bands exceeding 54 pt (10% of the 540 pt slide height). No remaining flagged bands were found. Cover/booklet, raster architecture and closing/reference compositions (1, 2, 4, 45, 46) were assessed visually rather than forced into a source/footer template. Exterior slide margins and intentionally separate diagram columns are not content-band gaps.

Slide 9 has four 34 pt right-column cards with equal 6 pt gaps; their text tops align with the first four left-column rows. The bullets follow below. Slide 12 has five 58 pt table rows and the service strip immediately above LIMIT. Slide 35 has equal 48 pt PASS/FAIL boxes and 16 pt gaps between the results table, PASS/FAIL row, WHY H3 FAILED box and LIMITS box.

The inherited raster limitation remains: the supplied booklet and embedded architecture image retain their original bytes; internal raster lettering is outside native font measurement. No clipping or unintended overlap was observed in the final changed renders.

## Preserved inputs and output hashes

- Original v9 PPTX, unchanged: `7ca64474294949da930fb00f4b701e4056115cd035d720ec62fe7b00bd90059b`
- Source v9.1 PPTX, unchanged: `2fbe5fbf788e00feb6aee60e44713f5aaee6c9068a545419a10b8c2866bc0d91`
- v9.2 PPTX: `0f96e76e7757a90902613603b064f0d340756f27978fac037b401f72e6fbcae8`
- v9.2 view PDF: `ef73f19505915e2bf8823bedad8bb006bc94ab329a56665a90f9f22b1158f63f`

Machine-readable evidence: v9_2_checks.json and v9_2_changes.json. Local reproducibility scripts: layout_v9_2.py, verify_v9_2.py, render_v9_powerpoint.ps1 and measure_v9_1.ps1. No application, native-demo or Docker configuration was changed in this task.
