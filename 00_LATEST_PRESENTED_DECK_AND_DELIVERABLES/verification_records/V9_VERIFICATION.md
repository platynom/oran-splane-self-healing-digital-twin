# v9 verification record

Date: 2026-11-04  
Deck: `ORAN_SPlane_PRISM_Review_v9.pptx`

## Baseline and outputs

| File | SHA-256 | Size |
|---|---|---:|
| Frozen 42-slide v8 baseline | `AFD35BA8ECCCA1A2AAD07591CBF26AA0BD560C9984F5924186310A58C27F53BA` | 744,293 bytes |
| v9 PPTX | `7CA64474294949DA930FB00F4B701E4056115CD035D720EC62FE7B00BD90059B` | 762,462 bytes |
| v9 view PDF | `CDF7E3E71B126BF8C4806D8A7D513435F5770AAFA3B02B62F78BAB9963B62BD9` | 1,225,053 bytes |

The main-folder v8 file was not edited. It already had 46 slides before the v9 task, so the committed 42-slide baseline from commit `600b5ec` was used.

## Automated content verification

Command: `verification_records/verify_v9.py`

| Check | Result |
|---|---:|
| v9 slide count | 46 |
| Unchanged-slide ordered text and notes mismatches | **0** |
| Missing required errata wording | **0** |
| Forbidden obsolete wording in slides or notes | **0** |
| Question-map/navigation mismatches | **0** |
| Evidence-number/source mismatches | **0** |
| PDF present and non-empty | PASS |
| Per-slide PNG count | 46 |

The number/source check covers the experimental values added or changed in v9. Slide-navigation numbers and bibliography identifiers are validated structurally rather than treated as experimental claims.

## Package and geometry checks

- Package integrity: **PASS**, 46 slides, 0 findings.
- Geometry validator: 0 findings.
- Two inherited boundary warnings remain on unchanged slides 13 and 15. The same ordered text and notes match frozen v8 exactly; no v9 content caused them.
- PDF page count: **46**.
- PDF page size: **960 × 540 pt** (16:9).

## Render and visual inspection

LibreOffice is not installed on this Windows host: no `soffice` executable or LibreOffice registry installation was found. The required LibreOffice backend could therefore not be used without adding software to the machine.

Fallback used: installed Microsoft 365 PowerPoint exported the PDF and all 46 slide PNGs at 1600 × 900. This is also the target application for the PPTX.

Changed/new slides inspected individually at full PNG size: **3, 6, 9, 11, 24 notes, 26, 29 notes, 34, 35, 36, 37, 42, 43, 45 and 46**. Visible slides were checked for cut-off text, overlap, unintended wrapping and font readability. The first render exposed crowding on slides 11, 42 and 43; the deck was corrected and re-rendered. The final render has no visible overflow or overlap on the changed/new slides.

## Errata and stale-wording result

- Slide 6 `T-FRHAUL-01` misattribution removed.
- Slide 9 TIMESAFE/ETSI access-path attribution corrected.
- Slides 11 and 26 C2 wording corrected; obsolete C2 mapping removed from notes.
- Slide 26 C3 physical-shift overclaim removed.
- `notSlave` absent from slides and notes; G.8275.1 naming uses `timeTransmitterOnly` and `notTimeTransmitter`.
- “closed-loop healing not validated”, “Automated corrective action: none” and “No MTTR, recovery-time…” are absent from the complete PPTX text and notes.

## Reproducibility

- Builder: `verification_records/build_v9.py`
- Renderer fallback: `verification_records/render_v9_powerpoint.ps1`
- Verifier: `verification_records/verify_v9.py`
- Slide lineage: `verification_records/V9_SLIDE_SOURCE_MAP.md`
- Change list: `verification_records/V9_CHANGELOG.md`

