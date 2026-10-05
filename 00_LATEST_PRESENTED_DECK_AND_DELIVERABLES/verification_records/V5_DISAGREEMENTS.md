# V5 disagreement record

**Compared:** independent V5 recomputation against `V4_DECK_FACT_CHECK_2026-09-28.md`  
**Order of operations:** the independent recomputation and `V5_VERIFICATION_LOG.md` were completed before the prior audit was opened.

## Agreement

The prior audit is substantially right on the campaign scorecard, held-out comparison, model-feature counts, C1 replicate distribution, and the major presentation defects. In particular, both audits reproduce: base sensitivity 0.625; v3 sensitivity 0.9896; overall specificity 0.7833; v3 attribution 84/96 = 0.875; ARM A 51/56; ARM B 24/56; always-BENIGN 20/56; McNemar p = 0.21875; and all four fusion results.

## Numbers or numerical scopes the prior audit got wrong

1. **C1 threshold crossing:** its body correctly gives approximately 60.5%, but it never reports the independently recomputed value **60.542884%**. Any continued use of **~62% or 62.5%** is rejected. V5 uses **60.54%**, labelled as a linear interpolation inside an untested 60–65% bracket.
2. **C1 65% representative value:** the prior audit reports two raw values, 0.4581 and 0.4619. The deck should not select only 0.458. The recomputed per-level median is **0.459859** (n=2). V5 uses the median and retains n.
3. **C1 70% and 75% display precision:** the prior audit gives ranges. Recomputed medians are **0.413656** (70%, n=3) and **0.366530** (75%, n=6). V5 uses these exact summaries.
4. **Servo magnitude:** the prior audit validates only line counts per run. Direct parsing gives mean absolute offsets of **1,866.252 ns over 1,056 baseline samples**, **1,583.672 ns over 534 C1 samples**, and **1,764.598 ns over 336 C3 samples**. V5 uses these to support only a testbed-specific software-timestamping limitation.
5. **130 ns scope:** the prior audit treats 130 ns as broadly correct and adds a derived ±65 ns implication. The authoritative ETSI/O-RAN table scopes 130 ns specifically to **5G FR2 intraband-contiguous carrier aggregation relative TAE, Timing Category A**. V5 does not present it as a universal O-RAN limit and does not promote the derived ±65 ns value as a normative requirement.
6. **±1.5 µs scope:** the prior audit calls this an “O-RU to PRTC” application-level limit. G.8271.1 frames it as maximum absolute time error at **reference point E / the end application relative to a common recognized time standard**. V5 removes the path-like “O-RU to PRTC” wording.
7. **Wrong-fact count:** the prior audit’s headline says **eight** factually wrong statements, but its Tier 1 contains eight numbered groups with multiple independent errors and later sections identify further factual overstatements. V5 therefore reports claim-level verdicts instead of preserving “eight” as a defensible total.

## Evidence-scope disagreements

1. The prior audit says nothing is unsupported and describes live readback of runtime configurations. The supplied corrected evidence archive has **1,096 entries and 168 run directories**, but it contains no retained per-run PCAP files and no `cfg/*.cfg` set. Configuration claims may be consistent with repository scripts, but full runtime readback is **not independently reproducible from the corrected archive alone**.
2. The prior audit says captures support the deck’s evidence language. In the corrected archive, the retained artifacts are scenario-named deep CSVs, context, decisions and telemetry; the original PCAPs are absent. V5 distinguishes “capture configured” from “PCAP retained.”
3. The exact workbook named by the request, `docs/comparison_notes_and_results.xlsx`, does not exist under the repository. Its contents and correction status are therefore **UNVERIFIABLE**. A different workbook is not silently substituted.

## Corrections accepted from the prior audit

- Specificity excluding B_bc_replacement is **47/48 = 0.979**, not 1.000; B3 replicate 4 is UNKNOWN.
- Slide 7 notes and M3/M5 completion labels contradict the milestone table.
- AI-vs-rule evaluation is on **56 held-out runs**, not “on 168 runs.”
- ROC-AUC **0.604** is a **1,923-window** statistic, not a run-level statistic.
- ARM B is not distinguishable from always-BENIGN at this sample size (**24/56 vs 20/56; exact McNemar p=0.21875**).
- The C1 x-axis must describe the **post-warm-up injection window**.
- The slide-24 duplicate-data statement must say **three captures, each copied 12 times**, not one capture copied 12 times.
- TIMESAFE should cite the published ACM TOPS article and DOI.
- GNSS-spoofing language must be scoped to the evidence available to this ptp4l-only testbed.
- G.8275.1 `controlField` is ignored and is not a standalone legality discriminator.

## Declined or narrowed prior-audit corrections

1. **“≈±65 ns per RU” was not accepted as a normative limit.** V5 includes it only because the requested correction calls for the per-RU implication, and labels it explicitly as a derived value that applies only under equal allocation.
2. **“Software timestamping is typically 10–100 µs” was not generalized into the deck.** The measured testbed baseline is about 1.866 µs mean absolute offset; broad platform ranges depend on hardware, load and timestamp path. V5 reports the local measurement and limitation.
3. **A4 replay → T-SPLANE-04 was not preserved.** ETSI T-SPLANE-04 is selective interception/removal; delay manipulation is T-SPLANE-05. Replay has no clean one-to-one mapping in the cited set.
4. **A4 delay → T-SPLANE-04 was rejected.** Delay manipulation maps to **T-SPLANE-05**, not -04.
5. **“Nothing is unsupported by data we hold” was rejected.** Retained PCAP and runtime-config claims exceed the corrected archive supplied for reproducibility.

## Remaining irreducible limitations

- No independent rerun of the network experiment was performed; this audit recomputed from retained artifacts.
- No raw PCAPs are present in the corrected archive, so packet-level extraction cannot be repeated end-to-end.
- Full runtime configuration cannot be reconstructed from the corrected archive because the actual config set is absent.
- The requested comparison workbook is missing and could not be corrected without inventing a substitute.
- The 60.54% crossing is an interpolation, not a measured boundary; the decisive 60% level has n=1.
