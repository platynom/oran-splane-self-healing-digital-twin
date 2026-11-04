# v9.1 verification

Slides: 46. Source input SHA256 confirmed.

Text-run differences (whitespace normalized, per slide, original run order): 0. Notes and embedded media byte differences: 0. Source table-cell text is included in the run traversal; the deck uses native text-box tables rather than table objects.

Before: 331 bounds, text-fit and text-ink overlap findings. After: 0. Native font-size findings: 0. Text-box rectangle overlap findings after excluding intentional backings: 0.

Checks use PowerPoint TextFrame2 BoundHeight/BoundWidth (actual installed-font metrics), plus bounding-box and pairwise text-ink checks. Formatting changes only: no text node, note, media, citation, table-cell value or slide relationship was changed. The source input remains unchanged.

Raster limitation: slide 1 is the supplied booklet image and slide 4 includes a raster architecture figure. Their internal text cannot be made 12 pt as editable text without changing forbidden image content. Image bytes are preserved. Font minimum checks apply to editable slide text; source/reference lines use the permitted 10 pt floor. The preserved raster content is explicitly outside native-font measurement.

Cover/booklet compositions are retained rather than forced into a content-slide header grid. Dense tables keep content-dependent row heights to retain all original wording at readable sizes. These are disclosed layout exceptions to literal universal-grid/uniform-row requirements.

Both decks rendered with PowerPoint to 46 PNGs each. All 46 output slides were inspected individually at full resolution across the repair iterations; the corrected attack table, status panel, markers and bridge labels were rechecked after their final adjustments. No remaining clipping or unintended visual overlap was observed. The requested 23-page before/after contact PDF contains every slide pair. Its first, middle and final pages were rendered and inspected; PDF page counts were independently verified (46-page view PDF, 23-page comparison PDF).

Initial wrapping estimates used installed-font measurements through Pillow; final fit checks used actual PowerPoint font metrics. The published verification is the final result after the last render. The two inherited background-boundary issues on slides 13 and 15 are fixed. Slide 1 remains unchanged, with the mandatory booklet raster preserved; slides 2–46 have layout/formatting changes.

PPTX SHA256: 2fbe5fbf788e00feb6aee60e44713f5aaee6c9068a545419a10b8c2866bc0d91 
View PDF SHA256: d830d7e43efe4fde93d60b57cb3370d9113776dfdb0b7cd635d5233ab3049569 
Before/after PDF SHA256: 83ed320928d0dcb8f78983e9cd40c08ae9f5d4cfc7918b85390581cdc87193d0

## Intentional background/backing/connector shapes excluded from overlap tests

These IDs enumerate non-text slide objects: full-slide backgrounds, source/footer containers, peer-card backings, diagram connectors and raster figures. Intentional text-on-backing containment is excluded. Text-versus-text intersections are not excluded.

- Slide 1: 1, 2, 3
- Slide 2: 1, 2, 3, 6, 12
- Slide 3: 1, 2, 3, 6, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 41
- Slide 4: 1, 2, 3, 6, 8
- Slide 5: 1, 2, 3, 6, 8, 11, 13, 15, 18, 20, 22, 25, 27, 29, 31, 34, 36, 38, 40, 42, 45, 47, 49, 51, 54
- Slide 6: 1, 2, 3, 6, 11, 15, 19, 23, 27, 28
- Slide 7: 1, 2, 3, 6, 8, 9, 14, 15, 20, 21, 26, 29
- Slide 8: 1, 2, 3, 6, 8, 9, 15, 16, 22, 25, 26, 30, 31, 35, 36, 40, 41, 45
- Slide 9: 1, 2, 3, 6, 21, 23, 26, 29, 32, 37
- Slide 10: 1, 2, 3, 6, 8, 11, 14, 16, 19, 21, 24, 27, 30, 33, 36, 42, 46, 50, 54, 56
- Slide 11: 1, 2, 3, 6, 13, 19, 25, 31, 37, 43, 49, 55, 61, 62
- Slide 12: 1, 2, 3, 6, 13, 19, 25, 31, 37, 43, 44, 46
- Slide 13: 1, 2, 3, 6, 11, 15, 19, 23, 27, 31, 32
- Slide 14: 1, 2, 3, 6, 8, 12, 16, 20, 24, 36
- Slide 15: 1, 2, 3, 6, 8, 12, 13, 17, 18, 22, 23, 27, 30, 33
- Slide 16: 1, 2, 3, 6, 11, 15, 19, 23, 27, 31, 32
- Slide 17: 1, 2, 3, 6, 9, 10, 13, 16, 18, 21, 23, 26, 29, 32, 33, 34, 35, 36, 37, 38, 39, 42, 45, 48
- Slide 18: 1, 2, 3, 6, 11, 15, 19, 23, 27, 31, 35, 39, 43, 44, 58, 61
- Slide 19: 1, 2, 3, 6, 8, 9, 14, 15, 20, 21, 26, 27, 32, 33, 37, 41
- Slide 20: 1, 2, 3, 6, 8, 13, 15, 20, 22, 27, 29, 34, 37
- Slide 21: 1, 2, 3, 6, 12, 17, 22, 27, 32, 37, 42, 47, 48
- Slide 22: 1, 2, 3, 6, 8, 11, 14, 17, 20, 23, 25, 28, 31, 34, 37, 40, 43, 51, 54
- Slide 23: 1, 2, 3, 6, 12, 17, 22, 27, 32, 37, 38
- Slide 24: 1, 2, 3, 6, 8, 9, 11, 14, 15, 17, 20, 21, 23, 26, 27, 29, 32
- Slide 25: 1, 2, 3, 6, 13, 19, 23, 29, 33, 39, 43, 49, 53, 54
- Slide 26: 1, 2, 3, 6, 13, 19, 23, 29, 33, 39, 43, 49, 53, 54
- Slide 27: 1, 2, 3, 6, 13, 19, 23, 29, 33, 39, 43, 49, 53, 59, 63, 64
- Slide 28: 1, 2, 3, 6, 8, 9, 13, 18, 20, 24, 26, 30, 32, 36, 38, 42, 44, 48, 50, 54, 56, 60, 62, 66, 68, 72, 74, 78, 80, 84, 86, 90, 92, 96, 98, 102, 104, 108, 110, 114
- Slide 29: 1, 2, 3, 6, 8, 9, 13, 14, 19, 22, 24, 27, 29, 32, 35, 37
- Slide 30: 1, 2, 3, 6, 8, 11, 14, 17, 20, 21, 24, 25, 28, 29, 32, 33, 36, 37, 40
- Slide 31: 1, 2, 3, 6, 9, 10, 14, 16, 17, 21, 23, 24, 28, 30, 31, 35, 37
- Slide 32: 1, 2, 3, 6, 13, 14, 40, 47, 54, 82, 94
- Slide 33: 1, 2, 3, 6, 8, 9, 13, 14, 18, 19, 23, 24, 28, 31, 34, 37
- Slide 34: 1, 2, 3, 6, 8, 11, 14, 17, 20, 23, 26, 31, 35, 39, 43, 44, 47, 50
- Slide 35: 1, 2, 3, 6, 12, 17, 22, 27, 32, 33, 35, 37, 40
- Slide 36: 1, 2, 3, 6, 12, 17, 22, 27, 32, 37, 42, 47, 48, 51
- Slide 37: 1, 2, 3, 6, 12, 17, 22, 27, 32, 37, 42, 47, 52, 53
- Slide 38: 1, 2, 3, 6, 8, 12, 16, 24, 25, 30, 35, 40, 45, 46, 49, 52
- Slide 39: 1, 2, 3, 6, 9, 10, 11, 15, 16, 17, 21, 22, 23, 27, 29
- Slide 40: 1, 2, 3, 6, 13, 18, 23, 28, 29, 34, 35, 38, 41, 44
- Slide 41: 1, 2, 3, 6, 12, 14, 18, 20, 24, 26, 30, 32, 36, 38, 42, 43
- Slide 42: 1, 2, 3, 6, 8, 10, 12, 14, 18, 20, 24, 26, 30, 32, 36, 38, 42, 44, 48, 50, 54, 56, 60, 62, 76
- Slide 43: 1, 2, 3, 6, 8, 10, 11, 14, 15, 18, 19, 22, 23, 26, 27, 30, 32, 33, 36, 37, 40, 41, 44, 45, 48
- Slide 44: 1, 2, 3, 6, 19, 20, 23, 26, 29
- Slide 45: 1, 2, 3, 6, 10, 14, 18, 22, 26, 30, 34, 38
- Slide 46: 1, 2, 3, 6
