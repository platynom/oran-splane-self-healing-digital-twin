## Slide 3
--- 
+++ 
@@ -26,14 +26,14 @@
 reference time
 Boundary clock
 timing relay
-PROJECT HIT: OPEN FRONTHAUL S-PLANE
-PTP / SyncE timing evidence captured on brUP and brDN
+PROJECT FOCUS: OPEN FRONTHAUL S-PLANE
+PTP timing evidence observed on brUP and brDN; SyncE was outside this software testbed
 Feature extraction
 packet plus daemon telemetry
 Rule and ML comparison
 ARM A versus ARM B
 Safe response decision
 isolate, holdover or escalate
-Validated here: packet capture, feature extraction and classification. Remaining scope: digital-twin orchestration and automated recovery.
+Validated here: live packet-path execution, extracted timing evidence and classification. Remaining scope: digital-twin orchestration, fault prediction, automated recovery and outcome measurement.
 [NOTES]
-Architecture context follows the O-RAN reference architecture: SMO with Non-RT RIC, Near-RT RIC, O-CU-CP/O-CU-UP, O-DU, O-RU and O-Cloud. Open Fronthaul between O-DU and O-RU carries C/U/S/M planes. Official sources: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf ; https://mediastorage.o-ran.org/ecosystem-resources/O-RAN-2025.04.02.WP.O-RAN_NTN_Deployments-v08.4.pdf ; https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3219 . The highlighted project boundary is based on this repository's six-daemon S-plane testbed.
+Architecture scope: O-RAN reference architecture and this repository's six-daemon S-plane testbed. The corrected archive retains extracted evidence, not PCAP files. O-RAN overview: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf

## Slide 4
--- 
+++ 
@@ -1,16 +1,16 @@
 WORKLET M1: PROBLEM STUDY (COMPLETED)
 Open Fronthaul Timing Requirements and Security Exposure
 130 ns
-Category-A relative alignment target between radio units
-O-RAN Open Fronthaul CUS-plane specification
-1.5 µs
-Application-level time-error limit from O-RU to PRTC
-ITU-T G.8271.1
+5G FR2 intraband-contiguous CA relative TAE · Timing Category A
+Pairwise; ≈±65 ns/RU only under equal allocation
+±1.5 µs
+End-application absolute time-error limit at reference point E
+Relative to a common recognized time standard · ITU-T G.8271.1
 ~2 s
-Observed service failure after a timing attack in one study
-TIMESAFE
+Observed RU crash after a timing attack in one published study
+TIMESAFE · ACM TOPS · DOI 10.1145/3775060
 Timing is distributed over the network itself, as ordinary packets.
 Because timing is distributed as network traffic, it is attackable. Loss of a shared time reference can degrade radio coordination, making the S-plane a security surface as well as an engineering constraint.
-The ~2 s figure is an observed result from one published study, not a standardised limit. We treat it as a design target.
+130 ns and ±1.5 µs re-express upstream 3GPP radio requirements. TIMESAFE observed an RU software crash requiring manual reboot with dynamic PTP-port roles; another configuration degraded over ~580 s. These are study-specific, not standardised limits.
 [NOTES]
-The 130 ns value is category-specific, the ±1.5 µs value is an application-level O-RU-to-PRTC limit, and the roughly 2 s result is an observation from TIMESAFE, not a standardised bound or a fastest-known claim.
+Standards scope verified 2026-09-28. 130 ns: ETSI TS 103 859 V7.0.2, table for 5G FR2 intraband-contiguous CA relative TAE, Timing Category A: https://www.etsi.org/deliver/etsi_ts/103800_103899/103859/07.00.02_60/ts_103859v070002p.pdf . ±1.5 µs: ITU-T G.8271.1 reference point E/end application relative to common recognized time standard: https://www.itu.int/rec/T-REC-G.8271.1/ . TIMESAFE: ACM TOPS DOI https://doi.org/10.1145/3775060 .

## Slide 7
--- 
+++ 
@@ -2,7 +2,6 @@
 Worklet Milestone Completion Status
 DONE
 PARTIAL
-HARDWARE-BLOCKED
 NOT STARTED
 M1
 Problem study + literature survey
@@ -28,14 +27,14 @@
 Healing logic integration
 Decision engine evaluated; closed-loop healing not validated
 PARTIAL
-M6
+M6a
 Testing and evaluation
 168-run campaign + AI-vs-rule comparison
 DONE
-M6
+M6b
 Paper & IP draft
 Publication + patent disclosure
 NOT STARTED
-M4 and M6 closed by the AI-vs-rule comparison completed on the 168-run campaign (slide 20).
+M4 model evaluation and M6 testing are supported by 56 held-out runs from the 168-run campaign (slide 21). M3 and M5 remain partial; prediction, healing execution and outcome metrics remain open.
 [NOTES]
-Every milestone except the paper/IP draft is now closed. M4 and M6 moved to DONE once the comparison ran.
+Independent V5 audit: M3 remains partial because a digital twin was not run; M5 remains partial because response labels were not executed as closed-loop actions. Objective 2 prediction and MTTR/availability outcomes were not measured.

## Slide 8
--- 
+++ 
@@ -10,7 +10,7 @@
 ARM B · MACHINE LEARNING
 Supervised + open-set models
 RandomForest (90 trees, depth 6, balanced classes)
-IsolationForest open-set layer providing abstention
+IsolationForest open-set layer intended to provide abstention (held-out score: 0.000)
 Consumes ptp4l servo telemetry: offset, path delay, PDV
 Session-disjoint split by replicate — never by window
 The rule-based arm is not a deviation from the worklet — it is the comparison baseline the worklet explicitly requires.

## Slide 9
--- 
+++ 
@@ -16,10 +16,10 @@
 RU3
 radio unit
 Capture point
-tcpdump on both bridges — every PTP frame on the wire is recorded, unmodified.
+tcpdump was configured on both bridges. The corrected archive retains extracted deep CSVs and decisions, but not the source PCAPs.
 Real linuxptp daemons execute BMCA and servo logic on isolated network namespaces
 Faults use live packet-path mechanisms, not synthetic packet rows
 No independent clock-error instrument was used; synchronisation impact is inferred from protocol and servo telemetry
 ITU-T G.8275.1 profile settings: domain 24, priority1 128, Sync 16/s, Announce 8/s
 [NOTES]
-Emphasise that protocol execution is real. Do not claim independently measured loss of synchronisation: the campaign uses packet captures and daemon telemetry, not an external timing instrument.
+The corrected campaign archive SHA-256 is 6149b4fb15940cdac694ba8666d97041b4eb62d5523d2631c1edf96d531e4ed9 with 1,096 entries and 168 run directories. It contains scenario-named deep CSVs, context and decisions, but no retained PCAP files.

## Slide 10
--- 
+++ 
@@ -1,6 +1,6 @@
 WORKLET M2: KPI CONFIGURATION (COMPLETED)
 Timing Configuration Derived from Standards
-The campaign read back every configuration value from the running system and traced it to the governing standard.
+Configuration values are consistent with repository scripts and cited standards; the corrected archive does not retain the complete runtime config set.
 Parameter
 Value
 Basis
@@ -24,10 +24,10 @@
 Alternate BMCA, not IEEE default
 Transport
 L2 multicast 01-1B-19-00-00-00
-G.8275.1 forwardable address
+Permitted forwardable address; ptp4l global default
 Timestamping
 software
 Platform limit — see next slide
-Some ITU-T values are cited via vendor application notes because the normative recommendations are paywalled — disclosed in the workbooks.
+Official ITU recommendation pages are cited. Where full normative text is access-restricted, V5 distinguishes primary metadata from corroborating implementation documentation.
 [NOTES]
-If challenged on sourcing: we disclose that several standards values come from authoritative secondary sources, and recommend confirming against normative text before publication.
+G.8275.1 profile source: https://www.itu.int/rec/T-REC-G.8275.1/ . The forwardable destination is permitted, but 01:1B:19:00:00:00 is ptp4l's global default rather than the profile reference address. Complete runtime cfg files are absent from the corrected archive.

## Slide 11
--- 
+++ 
@@ -4,7 +4,7 @@
 !
 No PTP hardware clock
 ls /dev/ptp* → empty
-Software timestamping only: microsecond noise floor against a nanosecond target
+Software timestamping only: baseline mean |offset| = 1,866 ns in this testbed, above the 130 ns category-specific target
 !
 No loadable kernel modules
 modprobe → not found
@@ -18,4 +18,4 @@
 not present
 GNSS spoofing and jamming cannot be produced at all
 [NOTES]
-This slide is deliberately placed before the results. It sets the ceiling on what any result here can claim.
+Direct retained-servo parsing: baseline 1,056 samples, mean |offset| 1,866.252 ns; C1 534 samples, 1,583.672 ns; C3 336 samples, 1,764.598 ns. This supports a testbed-specific limitation, not a universal software-timestamping range. Linux timestamping documentation: https://docs.kernel.org/networking/timestamping.html

## Slide 13
--- 
+++ 
@@ -1,8 +1,9 @@
-WORKLET M5: DECISION ENGINE (COMPLETED)
+WORKLET M5: DECISION ENGINE (PARTIAL — CLASSIFICATION EVALUATED)
 Attack Classification Using Protocol and Operator Context
 Classification combines protocol consistency, observed timing behaviour and provisioned operator context.
 BENIGN faults
-Degrade timing in a way that is self-consistent with a declared, standards-compliant state change — clockClass 6→7 on GNSS loss, an ESMC quality downgrade, drift bounded by the holdover mask.
+Degrade timing in a way that is self-consistent with a declared, standards-compliant state change — 
+clockClass 6→7 for a T-GM entering holdover while still within its configured specification, or drift bounded by an explicit holdover mask.
 ATTACKS
 Produce illegal or unauthorised evidence, such as forged Announce fields, non-monotonic sequence IDs, or a superior grandmaster that is outside the provisioned allow-list.
 Worked example — the discriminator that decides it
@@ -11,4 +12,4 @@
 It could be A1 — Announce/BMCA spoofing by a rogue master
 The decisive test: is the new grandmaster's clock identity on the provisioned allow-list?
 [NOTES]
-This is the LOOK-ALIKES logic. Classification is testing self-consistency against the standard, not reacting to fault magnitude.
+ClockClass 6→7 is valid for a T-GM entering holdover only while it remains within its configured specification. Verdict labels were evaluated; response actions were not executed.

## Slide 14
--- 
+++ 
@@ -1,12 +1,12 @@
-WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)
+WORKLET M5: SAFE ABSTENTION LOGIC (PARTIAL — VERDICT LOGIC EVALUATED)
 Safe Abstention for Ambiguous Timing Events
 The decision engine abstains when packet evidence cannot support a reliable attack or benign classification.
 ATTACK
 Protocol-inconsistent evidence present
-ISOLATE
+ISOLATE — recommended response; not executed
 BENIGN
 Only provisioned clocks, no legality violation
-TOLERATE / HOLDOVER
+TOLERATE / HOLDOVER — recommended; not executed
 UNKNOWN
 Packets genuinely cannot distinguish intent
 ESCALATE, DO NOT ACT BLINDLY

## Slide 15
--- 
+++ 
@@ -3,19 +3,19 @@
 SW FULL · SW* DETECTION
 HW PHYSICAL
 ATTACKS
-A1
+A1 · TESTED
 Rogue grandmaster / BMCA spoof
 SW
-A2
+A2 · TESTED
 Sync / Follow_Up spoofing
 SW
-A3
+A3 · TESTED
 Replay
 SW
 A4
 Delay (time) attack
 SW*
-A5
+A5 · TESTED
 DoS / PTP flooding
 SW
 A6
@@ -24,17 +24,17 @@
 A7
 GNSS jamming
 HW
-A8
+A8 · TESTED
 Rogue boundary clock
 SW*
 BENIGN FAULTS
 B1
 GNSS holdover
 HW
-B2
+B2 · TESTED
 Planned GM changeover
 SW
-B3
+B3 · TESTED
 PDV / congestion
 SW
 B4
@@ -46,12 +46,12 @@
 B6
 Oscillator drift
 HW
-B7
+B7 · TESTED
 Topology reconfiguration
 SW
 B8
 Measurement noise floor
 SW
-Attack classes align where applicable with ETSI TR 104 106. Benign classes are test conditions, not threat identifiers. SW* means software detection logic only; physical impact needs hardware.
+ETSI mapping is partial: A5→T-SPLANE-01, A1→T-SPLANE-02/-03, C1→T-SPLANE-04, A4 delay→T-SPLANE-05. Replay and GNSS classes lack a clean one-to-one mapping. Eight of 16 A/B classes were run. SW* means detection logic only; physical impact needs hardware.
 [NOTES]
-Taxonomy from the latest parameter matrix: 8 fully software classes, 3 software detection-only classes (A4, A8, B5), and 5 hardware-required classes (A6, A7, B1, B4, B6).
+ETSI TR 104 106 V3.0.0 mappings: T-SPLANE-01 DoS, -02 spoofed GM, -03 rogue PTP instance, -04 selective interception/removal, -05 delay manipulation. Source: https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf

## Slide 16
--- 
+++ 
@@ -1,17 +1,17 @@
-WORKLET M3: FAULT INJECTION (COMPLETED)
+WORKLET M3: FAULT INJECTION (PARTIAL — DIGITAL TWIN NOT RUN)
 Fault Injection on the Live Packet Path
 Extra real PTP daemons
 A1 · A8
-A new namespace runs a genuine ptp4l with attacker-chosen identity and a superior priority2, then competes in BMCA for real.
+A new namespace runs genuine ptp4l with an unallow-listed identity and a superior dataset, then competes under the G.8275.1 alternate BMCA.
 Scapy packet injection
 A2 · C2 · C3
-Hand-built frames: forged Sync with manipulated originTimestamp; illegal version/length/control fields; Announce with leap61 set and UTC offset wrong.
+Hand-built frames: forged two-step timing messages; C2 uses versionPTP=3, a reserved message type and a short length; C3 changes leap61/UTC properties. G.8275.1 ignores controlField, so it is not used as sole legality evidence.
 Capture and replay
 A3
 tcpdump captures live frames mid-run; tcpreplay retransmits them — genuinely stale timestamps and reused sequence IDs.
 Link and queue manipulation
 A5 · C1 · B3 · B7
 Flooding; blackholing the boundary clock's downstream port; a tbf bottleneck with competing non-PTP traffic; bouncing an RU link.
-An attack and its benign twin are often the same physical action — what separates them is the provisioned context, not the packets.
+An attack and its benign twin can share a packet-path mechanism; provisioned context separates them. IEEE 1588-2019: timePropertiesDS §8.2.4; leap-second handling §9.4. controlField is deprecated and ignored by G.8275.1.
 [NOTES]
-B2 and B_unplanned_failover are literally the same command - kill the grandmaster. Only the maintenance-window context differs.
+C2 remains malformed because of versionPTP=3, reserved message type and short length. controlField is ignored by G.8275.1 and is not a standalone profile-legality discriminator. For two-step operation, preciseOriginTimestamp is carried in Follow_Up; Sync originTimestamp is not authoritative.

## Slide 17
--- 
+++ 
@@ -8,7 +8,7 @@
 12
 randomised replicates each
 3
-rules scored on the same runs
+rules scored on the same captures; v2 and v3 verdicts are identical
 Freeze history disclosed
 The base rule was hashed before the campaign. v3 was created after v2 false positives were observed, then re-frozen before V4 scoring on the same captures.
 Pre-registered expectations

## Slide 18
--- 
+++ 
@@ -5,6 +5,7 @@
 Frozen base
 v3 defect-fix
 95% CI
+(v3, Wilson)
 A1 rogue grandmaster
 ATTACK
 12/12
@@ -75,6 +76,6 @@
 12/12
 12/12
 0.757–1.000
-Green = the three coverage gaps closed this cycle. Red = the one known open failure, B_bc_replacement, explained on slide 22.
+Green = three post-campaign coverage fixes. Red = the dominant open false-positive scenario, B_bc_replacement, explained on slide 23. B3 also contains one UNKNOWN benign run.
 [NOTES]
 Per-scenario is the primary metric. Point at the three green rows - those are the new detectors - and be upfront about the red row.

## Slide 19
--- 
+++ 
@@ -1,8 +1,8 @@
 WORKLET M6: PRIMARY RESULTS (COMPLETED)
 Results Across 168 Live Runs
 0.990
-Macro attack sensitivity
-across 8 attack scenarios
+Macro attack sensitivity · v3
+Base rule on same captures: 0.625
 0.783
 Macro specificity
 across 5 benign scenarios
@@ -10,9 +10,9 @@
 Abstention correctness
 ambiguous failover → UNKNOWN
 0.875
-Attribution accuracy
-correct fault identified
-Three coverage gaps closed this cycle: packet removal, malformed frames and whole-second abuse went from 0/12 to 11/12, 12/12 and 12/12 — with no loss of specificity.
-Specificity is 0.783 — not 1.000 — because of a single known failure. We report it rather than exclude it.
+Attribution accuracy · v3
+84/96 attack runs
+The v3 defect-fix rule closes three observed coverage gaps on the same captures: C1 11/12, C2 12/12 and C3 12/12. This is transparent post-observation evaluation, not independent pre-registered validation.
+Specificity is 0.783 because B_bc_replacement yields 12 false ATTACK calls and B3 has one UNKNOWN. Excluding B_bc_replacement, specificity is 47/48 = 0.979.
 [NOTES]
-Lead with sensitivity, but do not skip past the 0.783. Volunteering the weakness is what makes the rest credible.
+Independent recomputation from all 168 retained run directories: base macro sensitivity 0.625; v3 95/96 attack detections = 0.989583 macro sensitivity; specificity 47/60 = 0.783333; specificity excluding BC replacement 47/48 = 0.979167; attribution 84/96 = 0.875. V3 is post-observation and not an independent pre-registered validation.

## Slide 20
--- 
+++ 
@@ -1,22 +1,22 @@
 WORKLET M6: DETECTION BOUNDARY (COMPLETED)
 Measured Boundary of the Interception Detector
-The evaluation measured adjacent interception levels and reports the approximately 62% boundary as an interpolation.
-Fraction of the observation window blackholed
-75 %
-observed / declared rate  0.366
+The tested bracket is 60–65%. Linear interpolation of the observed/declared ratio gives a 60.54% threshold crossing.
+Configured blackhole fraction of the post-warm-up C1 injection window
+75 % · n=6
+median observed / declared rate  0.366530
 caught
-70 %
-observed / declared rate  0.414
+70 % · n=3
+median observed / declared rate  0.413656
 caught
-65 %
-observed / declared rate  0.458
+65 % · n=2
+observed ratios  0.4581 / 0.4619
 caught
-60 %
-observed / declared rate  0.505
+60 % · n=1
+observed / declared rate  0.504889
 MISSED
 Detection threshold
 0.500
-The detector fires when a source delivers below half the rate it itself declares. At a 60 % blackhole the ratio is 0.505 — a 1 % margin above the threshold, so the attack evades.
-Observed: 65% blackhole was caught and 60% was missed. The ~62% evasion boundary is an interpolation, not a directly tested point. Short or bursty interception may average out.
+The detector fires below 0.500. At 60%, ratio 0.504889 is 0.004889 absolute (0.98% relative) above threshold, so it evades.
+Observed: 65% caught; 60% missed. The 60.54% crossing is linearly interpolated, not measured. Configured 55% was never drawn; window arithmetic predicts ratio ≈0.568, also missed.
 [NOTES]
-This is why C1 is 11/12 and not 12/12. Presenting the boundary is more useful than a clean number.
+C1 medians recomputed from retained deep CSVs: 60%=0.504889 (n=1), 65%=0.459859 (n=2), 70%=0.413656 (n=3), 75%=0.366530 (n=6). Linear crossing at ratio 0.500 is 60.542884%. The configured fraction applies to the 36-second post-warm-up injection window, not the whole 44-second capture.

## Slide 21
--- 
+++ 
@@ -22,9 +22,10 @@
 0.000
 0.000
 ARM B is not distinguishable from always-BENIGN
-ARM B outputs BENIGN on 47/56 and has ROC-AUC 0.604. It scores 24/56 versus 20/56 for always-BENIGN (paired exact McNemar p = 0.219). Both score 4/4 on B_bc_replacement, so that result is not unique.
+ARM B outputs BENIGN on 47/56 and has window-level ROC-AUC 0.604 across 1,923 known-scenario windows.
+ It scores 24/56 versus 20/56 for always-BENIGN (paired exact McNemar p = 0.219). Both score 4/4 on B_bc_replacement, so that result is not unique.
 No measured combination beats the rule arm
 OR-combination 0.893, rule-first-then-ML 0.839, consensus 0.429 — all below ARM A's 0.911. No unmeasured combination is recommended.
 Scope condition: ARM B ran on 6 of 28 designed features — GNSS, SyncE and oscillator telemetry do not exist in ptp4l logs. This is not a general verdict on ML.
 [NOTES]
-The always-BENIGN control scores attack 0/32, benign 20/20, abstention 0/4, and exact accuracy 20/56. ARM B improves by only four runs and is not statistically distinguishable at this sample size (paired exact McNemar p = 0.21875). Its B_bc_replacement result is shared by the constant predictor and is not a unique learned capability.
+Held-out runs: ARM A 51/56, ARM B 24/56, always-BENIGN 20/56. ARM B versus baseline discordant pairs are 5 and 1; exact two-sided McNemar p=0.21875. ROC-AUC 0.603792 is computed over 1,923 known-scenario windows, not 56 runs. Both ARM B and always-BENIGN score 4/4 on B_bc_replacement.

## Slide 22
--- 
+++ 
@@ -1,11 +1,11 @@
 OBJECTIVE 5: RESULT INTERPRETATION (COMPLETED)
 Telemetry Constraints Behind ARM B Performance
-Its input is suppressed by the attacks it must detect
-C1 blackholes the timing path and C3 disrupts BMCA. Servo samples fall from 88 per baseline run to 44 and 28. The ML arm loses evidence; the rule arm can still use packet-rate deficit plus legality and context evidence.
-Only 6 of 28 features were observable
-GNSS, SyncE, oscillator and all protocol-legality features are absent from ptp4l servo logs. The model could key only on offset, path-delay and PDV magnitude.
+Telemetry starvation compounds broader feature poverty
+Servo samples average 88.0 per baseline run, 44.5 for C1 and 28.0 for C3. Starvation hurts those cases, but ARM B sensitivity is also low where telemetry remains; feature poverty and class overlap are primary constraints.
+Only 6 of 28 configured features were populated and used
+GNSS, SyncE, oscillator and protocol-legality features are absent from ptp4l servo logs. Six features were used, but holdover_rate had zero importance; five features carried model signal.
 Feature importances indicate testbed-servo artefact risk
 Top importances are offset_abs_max 0.268, path_delay_mean 0.262, and offset_std 0.208. With one testbed, domain shift cannot be separated from intrinsic class overlap.
 This is an argument for the rule-based layer, not against machine learning in general.
 [NOTES]
-The sparsity asymmetry is the most interesting architectural finding: attacks that starve telemetry blind a telemetry-based detector but not a packet-based one.
+ARM B used six populated features from 28 configured features; holdover_rate importance is 0. Feature importances: 0.267588, 0.261517, 0.208277, 0.138827, 0.123790 and 0. Servo-sample averages: baseline 88.0/run, C1 44.5/run, C3 28.0/run.

## Slide 23
--- 
+++ 
@@ -2,10 +2,11 @@
 Documented Study Limitations
 Planned boundary-clock swap is flagged as an attack
 0/12
-The provisioned context holds a single expected BC identity. This one scenario is the entire reason specificity is 0.783 rather than 1.000. Fix requires an allow-list change and a re-freeze.
-A coherent GNSS spoof is undetectable
-physical limit
-A spoof that perfectly mimics a healthy clock is in-distribution from a single reference. No software feature engineering removes this — it needs an independently trustworthy anchor.
+The provisioned context holds a single expected BC identity. 
+This scenario causes 12 false ATTACK calls and dominates the 0.783 specificity. B3 contributes one UNKNOWN; excluding BC replacement, specificity is 47/48 = 0.979. Fix requires an allow-list change and a re-freeze.
+GNSS spoofing is not established by this testbed
+testbed limit
+Downstream ptp4l telemetry alone cannot establish coherent-spoof detection. Trusted receiver/RF observables, spatial checks or an independent time anchor are outside this setup.
 Held-out evidence is small and partially missing
 4/scenario
 Only four held-out replicates exist per scenario, and 48/168 runs lack pmc.jsonl. Intervals are wide and ARM B sees only 6 of 28 designed features.
@@ -13,4 +14,4 @@
 36 C runs
 Thirty-six C-series contexts record rep=901; the split uses the replicate encoded in the directory name. Correct this before any fresh validation claim.
 [NOTES]
-Volunteering these is deliberate. A reviewer who finds an undisclosed hole trusts nothing else in the deck.
+The corrected conclusion is testbed-scoped: downstream ptp4l telemetry cannot establish detection of a coherent GNSS spoof. Additional trusted receiver/RF evidence can support detection. NIST GNSS resilience resources: https://www.nist.gov/pnt . Specificity excluding BC replacement is 47/48, not 1.000.

## Slide 24
--- 
+++ 
@@ -1,8 +1,8 @@
 WORKLET M6: PIPELINE AUDIT (COMPLETED)
 Pipeline Audit and Corrective Reruns
 The audit identified four defects. Two defects had produced invalid data before the corrective reruns.
-36 “replicates” were one capture copied 12 times
-A script created non-executable returned exit 126, silenced by output redirection; a stale capture then satisfied the validity guard.
+36 “replicates” were three captures copied 12 times
+A script was created without the execute bit; exit 126 was silenced by redirection, and a stale capture satisfied the validity guard.
 FIXED · re-run
 A benign scenario never injected anything
 The kernel lacks sch_netem and the failure was swallowed by || true. It was a baseline wearing a congestion label.
@@ -11,8 +11,8 @@
 No minimum-sample guard: a clock emitting 3 frames at start-up read as “rate starved”, destroying an honest abstention.
 FIXED · v3
 The evaluator overstated results
-Pooled metrics moved with run count; additive-only was “proven” by comparing two scalars.
+Pooled metrics moved with run count; an additive-only effect had been asserted from two scalars with no per-run test. V2 and v3 were subsequently compared on all 168 captures.
 REPLACED
 All fabricated-data runs were re-executed. Evaluator defects were corrected, and the post-observation v3 decision revision is explicitly disclosed.
 [NOTES]
-Including this is a deliberate choice. Finding and disclosing our own defects is stronger evidence of rigour than a clean set of numbers would be.
+The 36 invalid runs were three scenario captures copied across 12 replicate directories. V2 and v3 verdicts were compared per run and are identical on all 168 retained captures.

## Slide 25
--- 
+++ 
@@ -2,9 +2,13 @@
 Remaining Software and Hardware Validation
 Software — can start immediately
 Boundary-clock allow-list to close the B_bc_replacement false positive, then re-freeze and re-run
-Test additional interception levels around the interpolated ~62% boundary
+Test additional interception levels around the interpolated 60.54% crossing
 Extend the randomised design space for the three new scenarios
 Re-run ARM B with richer management-plane telemetry for a fairer comparison
+Fault prediction before disruption — not attempted
+Execute and measure corrective action — verdict labels are not actions taken
+Exercise the digital twin — not run in this campaign
+Measure MTTR, recovery time, availability and downtime — no figure yet
 M6 deliverable: paper and IP disclosure draft
 Hardware — Tier 3, requires equipment
 GNSS receiver
@@ -17,4 +21,4 @@
 unlocks B4 EEC degradation
 5 of 16 classes require hardware. Three more support software detection logic but need hardware for credible physical-impact measurement.
 [NOTES]
-Hardware priorities: GNSS receiver for A6/A7/B1, a second oscillator for B6, SyncE hardware for B4, and a hardware-timestamping NIC to improve A4/B5 physical-impact measurement.
+The 60.54% value is interpolated and needs denser direct testing. Worklet objectives still open: prediction before disruption, digital-twin validation, executed corrective action, and measured MTTR/downtime/availability.

## V4 slide 26 -> V5 slide 27
--- 
+++ 
@@ -6,16 +6,16 @@
 168 live runs; base rule pre-frozen
 v3 was created after v2 false positives and its revision history is disclosed
 3
-0.990 macro attack sensitivity
-Three coverage gaps closed; benign specificity remains 0.783
+0.990 macro attack sensitivity · post-observation v3
+Pre-frozen base: 0.625; specificity: 0.783 (0.979 excluding BC replacement)
 4
 Worklet objective 5 answered with evidence
 On this fixed split, ARM A beats ARM B; ARM B is not distinguishable from always-BENIGN
 5
 Limits measured, not hidden
-~62% is interpolated; BC replacement remains open; 5 HW plus 3 detection-only classes
+60.54% is interpolated; BC replacement remains open; source PCAPs are not retained in the corrected archive
 Thank you
 Tanmaya Kumar · Raghu Ram K · Munipalle Jaswanth Kumar
-WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE
+STATUS: S-PLANE DETECTION AND CLASSIFICATION EVALUATED · PREDICTION, DIGITAL TWIN AND HEALING NOT YET RUN
 [NOTES]
 Close on the evidence boundary. ARM B is not statistically distinguishable from always-BENIGN at n=56, and its B_bc_replacement performance is not a unique capability.

## New V5 slide 26
WORKLET SCOPE DISCLOSURE
Objectives Not Yet Addressed
1
Fault prediction
Prediction before service disruption was not attempted.
2
Corrective action
No corrective action was executed or measured. ISOLATE, HOLDOVER and ESCALATE elsewhere are verdict outputs—not actions taken.
3
Digital twin
The digital twin was not exercised in this campaign.
4
Outcome metrics
No MTTR, recovery-time, availability or downtime figure was measured here.
Next gate · execute the missing objectives and measure recovery outcomes before claiming self-healing
[NOTES]
This slide closes the silent worklet gaps identified by the independent V5 audit. Prediction, executed corrective action, digital-twin validation, and MTTR/recovery/availability/downtime measurement remain future work.
