# Slide 1

## Text



## Notes

Original Samsung PRISM worklet definition. Everything that follows sits inside this scope. Note objective 5 and expected outcome 4 - both explicitly require comparison against rule-based methods.

# Slide 2

## Text

Open Fronthaul S-Plane
Timing Security
Sub-scope of the AI-Native Self-Healing O-RAN worklet
Team  
Tanmaya Kumar · Raghu Ram K · Munipalle Jaswanth Kumar
Mentors  
Mr. Bikas Singh (NovaThink Tech) · Dr. Navin Kumar (Amrita Vishwa Vidyapeetham)
WORKLET SUB-SCOPE: OPEN FRONTHAUL S-PLANE TIMING SECURITY

## Notes

This deck covers the S-plane timing-security sub-scope: what we built, what we measured, and exactly where hardware is required.

# Slide 3

## Text

WORKLET M1: SYSTEM ARCHITECTURE DESIGN (COMPLETED)
End-to-End O-RAN Architecture and S-Plane Project Boundary
The mapped architecture isolates the Open Fronthaul S-plane timing boundary between O-DU and O-RU.
SMO / Non-RT RIC
policy and lifecycle
Near-RT RIC
xApps and E2 control
O-Cloud
hosts RIC, CU and DU functions
User equipment
UE
O-RU
radio unit
O-DU
distributed unit
O-CU-CP / O-CU-UP
central unit
5G Core
control and user plane
Data network
applications and services
Open Fronthaul C/U/S/M planes
A1
E2
PRTC / grandmaster
reference time
Boundary clock
timing relay
PROJECT FOCUS: OPEN FRONTHAUL S-PLANE
PTP timing evidence observed on brUP and brDN; SyncE was outside this software testbed
Feature extraction
packet plus daemon telemetry
Rule and ML comparison
ARM A versus ARM B
Safe response decision
isolate, holdover or escalate
Validated here: live packet-path execution, extracted timing evidence and classification. Remaining scope: digital-twin orchestration, fault prediction, automated recovery and outcome measurement.

## Notes

Architecture scope: O-RAN reference architecture and this repository's six-daemon S-plane testbed. The corrected archive retains extracted evidence, not PCAP files. O-RAN overview: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf

# Slide 4

## Text

WORKLET M1: PROBLEM STUDY (COMPLETED)
Open Fronthaul Timing Requirements and Security Exposure
130 ns
5G FR2 intraband-contiguous CA relative TAE · Timing Category A
Pairwise; ≈±65 ns/RU only under equal allocation
±1.5 µs
End-application absolute time-error limit at reference point E
Relative to a common recognized time standard · ITU-T G.8271.1
~2 s
Observed RU crash after a timing attack in one published study
TIMESAFE · ACM TOPS · DOI 10.1145/3775060
Timing is distributed over the network itself, as ordinary packets.
Because timing is distributed as network traffic, it is attackable. Loss of a shared time reference can degrade radio coordination, making the S-plane a security surface as well as an engineering constraint.
130 ns and ±1.5 µs re-express upstream 3GPP radio requirements. TIMESAFE observed an RU software crash requiring manual reboot with dynamic PTP-port roles; another configuration degraded over ~580 s. These are study-specific, not standardised limits.

## Notes

Standards scope verified 2026-09-28. 130 ns: ETSI TS 103 859 V7.0.2, table for 5G FR2 intraband-contiguous CA relative TAE, Timing Category A: https://www.etsi.org/deliver/etsi_ts/103800_103899/103859/07.00.02_60/ts_103859v070002p.pdf . ±1.5 µs: ITU-T G.8271.1 reference point E/end application relative to common recognized time standard: https://www.itu.int/rec/T-REC-G.8271.1/ . TIMESAFE: ACM TOPS DOI https://doi.org/10.1145/3775060 .

# Slide 5

## Text

WORKLET M1: DECISION REQUIREMENTS (COMPLETED)
Timing Attack and Benign Fault Classification
BENIGN FAULT
The clock is wrong
e.g. a GNSS outage at the grandmaster
Correct response: ride it out in holdover
Isolating the node here causes an outage you did not need
ATTACK
The clock is wrong
e.g. a rogue master injecting false time
Correct response: isolate it immediately
Waiting in holdover lets the attacker keep steering the clock
Where ambiguity appears: a planned grandmaster or boundary-clock change can resemble a rogue clock, while link loss or congestion can resemble packet removal or delay manipulation.
Decision parameters: allow-listed clock identity, maintenance window, clockClass, priority, stepsRemoved, sequence continuity, observed packet rate, offset, path delay and packet-delay variation.

## Notes

The overlap is scenario-specific. Decisions use operator allow-lists and maintenance context together with protocol fields, packet-rate evidence and servo telemetry.

# Slide 6

## Text

WORKLET M1: S-PLANE SUB-SCOPE (COMPLETED)
Rationale for the Open Fronthaul S-Plane Scope
The selected sub-scope targets timing events where benign faults and attacks require different recovery actions.
01
Highest consequence
Published attacks show that a timing failure can become a service failure in seconds, leaving little time for a safe decision.
02
Genuine ambiguity
Selected benign faults and attacks can produce overlapping symptoms. The decision combines protocol evidence with provisioned context.
03
Constrained by standards
IEEE 1588-2019 and ITU-T G.8275.1 constrain wire-level legality. Operator intent still requires provisioned context, and some thresholds are measured.
04
Reproducible in software
Real PTP daemons can be run and attacked on a virtual wire — no proprietary RAN stack required.

## Notes

If asked why not the whole RAN: scoping to S-plane is what made rigorous measurement possible in the time available.

# Slide 7

## Text

WORKLET DELIVERY MAP: CURRENT STATUS
Worklet Milestone Completion Status
DONE
PARTIAL
NOT STARTED
M1
Problem study + literature survey
Standards baseline, 11-source citation set
DONE
M1
System architecture design
Data flow: capture → extract → decide
DONE
M2
KPI and fault taxonomy
A1-A8 / B1-B8 catalogue; 144-parameter × 16-fault matrix
DONE
M3
Digital twin + fault injection
Six-node testbed and injection validated; digital twin not in this campaign
PARTIAL
M4
AI model development
RandomForest + IsolationForest; now evaluated on this testbed
DONE
M5
Healing logic integration
Decision engine evaluated; closed-loop healing not validated
PARTIAL
M6a
Testing and evaluation
168-run campaign + AI-vs-rule comparison
DONE
M6b
Paper & IP draft
Publication + patent disclosure
NOT STARTED
M4 model evaluation and M6 testing are supported by 56 held-out runs from the 168-run campaign (slide 21). M3 and M5 remain partial; prediction, healing execution and outcome metrics remain open.

## Notes

Independent V5 audit: M3 remains partial because a digital twin was not run; M5 remains partial because response labels were not executed as closed-loop actions. Objective 2 prediction and MTTR/availability outcomes were not measured.

# Slide 8

## Text

OBJECTIVE 5: AI VS RULE COMPARISON (COMPLETED)
Rule and ML Detection Evaluation Design
Worklet objective 5 requires a direct comparison between AI-based detection and traditional fault management.
ARM A · RULE-BASED
Frozen decision rule
Combines standards legality with provisioned operator context
No model training; a small number of measured thresholds remain
Base rule was SHA-256 frozen before the campaign
v3 is a disclosed post-campaign defect-fix revision
ARM B · MACHINE LEARNING
Supervised + open-set models
RandomForest (90 trees, depth 6, balanced classes)
IsolationForest open-set layer intended to provide abstention (held-out score: 0.000)
Consumes ptp4l servo telemetry: offset, path delay, PDV
Session-disjoint split by replicate — never by window
The rule-based arm is not a deviation from the worklet — it is the comparison baseline the worklet explicitly requires.

## Notes

The comparison is required by worklet objective 5. Distinguish the pre-frozen base rule from v3, which was written after v2 false positives were observed and then re-frozen before V4 scoring.

# Slide 9

## Text

WORKLET M3: FAULT-INJECTION TESTBED (PARTIAL)
Open Fronthaul Timing Testbed with Six Daemons
Six genuine linuxptp 4.0 daemons in isolated Linux network namespaces, across two bridged segments.
GM-A
grandmaster
GM-B
backup GM
brUP
BC
boundary clock
brDN
RU1
radio unit
RU2
radio unit
RU3
radio unit
Capture point
tcpdump was configured on both bridges. The corrected archive retains extracted deep CSVs and decisions, but not the source PCAPs.
Real linuxptp daemons execute BMCA and servo logic on isolated network namespaces
Faults use live packet-path mechanisms, not synthetic packet rows
No independent clock-error instrument was used; synchronisation impact is inferred from protocol and servo telemetry
ITU-T G.8275.1 profile settings: domain 24, priority1 128, Sync 16/s, Announce 8/s

## Notes

The corrected campaign archive SHA-256 is 6149b4fb15940cdac694ba8666d97041b4eb62d5523d2631c1edf96d531e4ed9 with 1,096 entries and 168 run directories. It contains scenario-named deep CSVs, context and decisions, but no retained PCAP files.

# Slide 10

## Text

WORKLET M2: KPI CONFIGURATION (COMPLETED)
Timing Configuration Derived from Standards
Configuration values are consistent with repository scripts and cited standards; the corrected archive does not retain the complete runtime config set.
Parameter
Value
Basis
Profile
ITU-T G.8275.1 telecom profile
Full timing support from the network
domainNumber
24
G.8275.1 (range 24–43)
priority1
128 (fixed)
G.8275.1 — removed from BMCA comparison
Sync rate
16 / s  (logInterval −4)
G.8275.1
Announce rate
8 / s  (logInterval −3)
G.8275.1
BMCA
dataset_comparison G.8275.x
Alternate BMCA, not IEEE default
Transport
L2 multicast 01-1B-19-00-00-00
Permitted forwardable address; ptp4l global default
Timestamping
software
Platform limit — see next slide
Official ITU recommendation pages are cited. Where full normative text is access-restricted, V5 distinguishes primary metadata from corroborating implementation documentation.

## Notes

G.8275.1 profile source: https://www.itu.int/rec/T-REC-G.8275.1/ . The forwardable destination is permitted, but 01:1B:19:00:00:00 is ptp4l's global default rather than the profile reference address. Complete runtime cfg files are absent from the corrected archive.

# Slide 11

## Text

WORKLET M2: PLATFORM CONSTRAINTS (COMPLETED)
Verified Platform Constraints
Direct queries of the running system confirmed each platform limitation.
!
No PTP hardware clock
ls /dev/ptp* → empty
Software timestamping only: baseline mean |offset| = 1,866 ns in this testbed, above the 130 ns category-specific target
!
No loadable kernel modules
modprobe → not found
No per-node mock PHC; no netem qdisc
!
One shared oscillator
architectural
All namespaces share the host clock, so clocks cannot genuinely drift apart
!
No GNSS receiver
not present
GNSS spoofing and jamming cannot be produced at all

## Notes

Direct retained-servo parsing: baseline 1,056 samples, mean |offset| 1,866.252 ns; C1 534 samples, 1,583.672 ns; C3 336 samples, 1,764.598 ns. This supports a testbed-specific limitation, not a universal software-timestamping range. Linux timestamping documentation: https://docs.kernel.org/networking/timestamping.html

# Slide 12

## Text

WORKLET M1: SYSTEM DATA FLOW (COMPLETED)
Data Flow from Packet Capture to Verdict
01
The wire
Real PTP frames on two bridged segments
›
02
Capture
tcpdump records every frame, unmodified
›
03
Deep extract
56 protocol fields per packet; absent fields left EMPTY, never zero
›
04
Decision rule
Standards legality + provisioned context, ordered clauses
›
05
Verdict
ATTACK · BENIGN · UNKNOWN
Integrity rule carried through the whole pipeline
A value that cannot be measured is written EMPTY — never zero. Zero offset reads as perfect synchronisation, which once made an earlier build report “healthy” while it was blind. Nothing is healthy without proof of observation.

## Notes

The empty-not-zero rule came from a real safety defect we found and fixed. Good story if asked about engineering rigour.

# Slide 13

## Text

WORKLET M5: DECISION ENGINE (PARTIAL — CLASSIFICATION EVALUATED)
Attack Classification Using Protocol and Operator Context
Classification combines protocol consistency, observed timing behaviour and provisioned operator context.
BENIGN faults
Degrade timing in a way that is self-consistent with a declared, standards-compliant state change — 
clockClass 6→7 for a T-GM entering holdover while still within its configured specification, or drift bounded by an explicit holdover mask.
ATTACKS
Produce illegal or unauthorised evidence, such as forged Announce fields, non-monotonic sequence IDs, or a superior grandmaster that is outside the provisioned allow-list.
Worked example — the discriminator that decides it
A grandmaster suddenly changes.
It could be B2 — a planned grandmaster failover, entirely legitimate
It could be A1 — Announce/BMCA spoofing by a rogue master
The decisive test: is the new grandmaster's clock identity on the provisioned allow-list?

## Notes

ClockClass 6→7 is valid for a T-GM entering holdover only while it remains within its configured specification. Verdict labels were evaluated; response actions were not executed.

# Slide 14

## Text

WORKLET M5: SAFE ABSTENTION LOGIC (PARTIAL — VERDICT LOGIC EVALUATED)
Safe Abstention for Ambiguous Timing Events
The decision engine abstains when packet evidence cannot support a reliable attack or benign classification.
ATTACK
Protocol-inconsistent evidence present
ISOLATE — recommended response; not executed
BENIGN
Only provisioned clocks, no legality violation
TOLERATE / HOLDOVER — recommended; not executed
UNKNOWN
Packets genuinely cannot distinguish intent
ESCALATE, DO NOT ACT BLINDLY
An unplanned grandmaster failure with no maintenance window is indistinguishable from an attack that suppressed it. The rule returns UNKNOWN — and did so correctly on 12 of 12 runs.

## Notes

Abstention is scored on its own axis. A BENIGN call here would be a dangerous over-claim; an ATTACK call a false alarm. Both are failures.

# Slide 15

## Text

WORKLET M2: FAULT TAXONOMY (COMPLETED)
Fault Taxonomy and Test Coverage
SW FULL · SW* DETECTION
HW PHYSICAL
ATTACKS
A1 · TESTED
Rogue grandmaster / BMCA spoof
SW
A2 · TESTED
Sync / Follow_Up spoofing
SW
A3 · TESTED
Replay
SW
A4
Delay (time) attack
SW*
A5 · TESTED
DoS / PTP flooding
SW
A6
GNSS spoofing
HW
A7
GNSS jamming
HW
A8 · TESTED
Rogue boundary clock
SW*
BENIGN FAULTS
B1
GNSS holdover
HW
B2 · TESTED
Planned GM changeover
SW
B3 · TESTED
PDV / congestion
SW
B4
SyncE / EEC degradation
HW
B5
Static path asymmetry
SW*
B6
Oscillator drift
HW
B7 · TESTED
Topology reconfiguration
SW
B8
Measurement noise floor
SW
ETSI mapping is partial: A5→T-SPLANE-01, A1→T-SPLANE-02/-03, C1→T-SPLANE-04, A4 delay→T-SPLANE-05. Replay and GNSS classes lack a clean one-to-one mapping. Eight of 16 A/B classes were run. SW* means detection logic only; physical impact needs hardware.

## Notes

ETSI TR 104 106 V3.0.0 mappings: T-SPLANE-01 DoS, -02 spoofed GM, -03 rogue PTP instance, -04 selective interception/removal, -05 delay manipulation. Source: https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf

# Slide 16

## Text

WORKLET M3: FAULT INJECTION (PARTIAL — DIGITAL TWIN NOT RUN)
Fault Injection on the Live Packet Path
Extra real PTP daemons
A1 · A8
A new namespace runs genuine ptp4l with an unallow-listed identity and a superior dataset, then competes under the G.8275.1 alternate BMCA.
Scapy packet injection
A2 · C2 · C3
Hand-built frames: forged two-step timing messages; C2 uses versionPTP=3, a reserved message type and a short length; C3 changes leap61/UTC properties. G.8275.1 ignores controlField, so it is not used as sole legality evidence.
Capture and replay
A3
tcpdump captures live frames mid-run; tcpreplay retransmits them — genuinely stale timestamps and reused sequence IDs.
Link and queue manipulation
A5 · C1 · B3 · B7
Flooding; blackholing the boundary clock's downstream port; a tbf bottleneck with competing non-PTP traffic; bouncing an RU link.
An attack and its benign twin can share a packet-path mechanism; provisioned context separates them. IEEE 1588-2019: timePropertiesDS §8.2.4; leap-second handling §9.4. controlField is deprecated and ignored by G.8275.1.

## Notes

C2 remains malformed because of versionPTP=3, reserved message type and short length. controlField is ignored by G.8275.1 and is not a standalone profile-legality discriminator. For two-step operation, preciseOriginTimestamp is carried in Follow_Up; Sync originTimestamp is not authoritative.

# Slide 17

## Text

WORKLET M6: CAMPAIGN DESIGN (COMPLETED)
Campaign Design and Reproducibility Controls
The campaign froze the base rule before execution. The team documented v3 as a post-campaign defect-fix revision.
168
live on-wire runs
14
scenarios
12
randomised replicates each
3
rules scored on the same captures; v2 and v3 verdicts are identical
Freeze history disclosed
The base rule was hashed before the campaign. v3 was created after v2 false positives were observed, then re-frozen before V4 scoring on the same captures.
Pre-registered expectations
Each scenario's expected verdict is written down in advance — sensitivity, specificity and abstention scored on separate axes.
Per-replicate randomisation
Parameters are reproducible from random.Random(rep). The C-series designs contain only 4-5 distinct parameter values, so the randomised space remains narrow.
Per-scenario reporting
Per-scenario recall is primary. Pooled figures move with run counts, so they are labelled descriptive only.

## Notes

Do not describe v3 as independent pre-registered validation. The base rule was pre-frozen; v3 is a transparent post-observation defect fix evaluated on the same campaign captures.

# Slide 18

## Text

WORKLET M6: PER-SCENARIO EVALUATION (COMPLETED)
Detection Results by Scenario
Scenario
Expected
Frozen base
v3 defect-fix
95% CI
(v3, Wilson)
A1 rogue grandmaster
ATTACK
12/12
12/12
0.757–1.000
A2 sync spoofing
ATTACK
12/12
12/12
0.757–1.000
A3 replay
ATTACK
12/12
12/12
0.757–1.000
A5 DoS flooding
ATTACK
12/12
12/12
0.757–1.000
A8 rogue boundary clock
ATTACK
12/12
12/12
0.757–1.000
C1 packet removal
ATTACK
0/12
11/12
0.646–0.985
C2 malformed frames
ATTACK
0/12
12/12
0.757–1.000
C3 whole-second abuse
ATTACK
0/12
12/12
0.757–1.000
baseline
BENIGN
12/12
12/12
0.757–1.000
B2 planned GM failover
BENIGN
12/12
12/12
0.757–1.000
B3 congestion
BENIGN
11/12
11/12
0.646–0.985
B7 topology change
BENIGN
12/12
12/12
0.757–1.000
B_bc_replacement
BENIGN
0/12
0/12
0.000–0.242
B_unplanned_failover
UNKNOWN
12/12
12/12
0.757–1.000
Green = three post-campaign coverage fixes. Red = the dominant open false-positive scenario, B_bc_replacement, explained on slide 23. B3 also contains one UNKNOWN benign run.

## Notes

Per-scenario is the primary metric. Point at the three green rows - those are the new detectors - and be upfront about the red row.

# Slide 19

## Text

WORKLET M6: PRIMARY RESULTS (COMPLETED)
Results Across 168 Live Runs
0.990
Macro attack sensitivity · v3
Base rule on same captures: 0.625
0.783
Macro specificity
across 5 benign scenarios
1.000
Abstention correctness
ambiguous failover → UNKNOWN
0.875
Attribution accuracy · v3
84/96 attack runs
The v3 defect-fix rule closes three observed coverage gaps on the same captures: C1 11/12, C2 12/12 and C3 12/12. This is transparent post-observation evaluation, not independent pre-registered validation.
Specificity is 0.783 because B_bc_replacement yields 12 false ATTACK calls and B3 has one UNKNOWN. Excluding B_bc_replacement, specificity is 47/48 = 0.979.

## Notes

Independent recomputation from all 168 retained run directories: base macro sensitivity 0.625; v3 95/96 attack detections = 0.989583 macro sensitivity; specificity 47/60 = 0.783333; specificity excluding BC replacement 47/48 = 0.979167; attribution 84/96 = 0.875. V3 is post-observation and not an independent pre-registered validation.

# Slide 20

## Text

WORKLET M6: DETECTION BOUNDARY (COMPLETED)
Measured Boundary of the Interception Detector
The tested bracket is 60–65%. Linear interpolation of the observed/declared ratio gives a 60.54% threshold crossing.
Configured blackhole fraction of the post-warm-up C1 injection window
75 % · n=6
median observed / declared rate  0.366530
caught
70 % · n=3
median observed / declared rate  0.413656
caught
65 % · n=2
observed ratios  0.4581 / 0.4619
caught
60 % · n=1
observed / declared rate  0.504889
MISSED
Detection threshold
0.500
The detector fires below 0.500. At 60%, ratio 0.504889 is 0.004889 absolute (0.98% relative) above threshold, so it evades.
Observed: 65% caught; 60% missed. The 60.54% crossing is linearly interpolated, not measured. Configured 55% was never drawn; window arithmetic predicts ratio ≈0.568, also missed.

## Notes

C1 medians recomputed from retained deep CSVs: 60%=0.504889 (n=1), 65%=0.459859 (n=2), 70%=0.413656 (n=3), 75%=0.366530 (n=6). Linear crossing at ratio 0.500 is 60.542884%. The configured fraction applies to the 36-second post-warm-up injection window, not the whole 44-second capture.

# Slide 21

## Text

OBJECTIVE 5: AI VS RULE COMPARISON (COMPLETED)
Rule, ML and Always-BENIGN Performance on 56 Held-Out Runs
The session-disjoint evaluation trained on replicates 1 to 8 and tested on replicates 9 to 12.
Metric
ARM A — rule
ARM B — ML
Always-BENIGN
Exact accuracy
51/56  (0.911)
24/56  (0.429)
20/56  (0.357)
Attack sensitivity
0.969
0.156
0.000
Benign specificity
0.800
0.950
1.000
Correct abstention
1.000
0.000
0.000
ARM B is not distinguishable from always-BENIGN
ARM B outputs BENIGN on 47/56 and has window-level ROC-AUC 0.604 across 1,923 known-scenario windows.
 It scores 24/56 versus 20/56 for always-BENIGN (paired exact McNemar p = 0.219). Both score 4/4 on B_bc_replacement, so that result is not unique.
No measured combination beats the rule arm
OR-combination 0.893, rule-first-then-ML 0.839, consensus 0.429 — all below ARM A's 0.911. No unmeasured combination is recommended.
Scope condition: ARM B ran on 6 of 28 designed features — GNSS, SyncE and oscillator telemetry do not exist in ptp4l logs. This is not a general verdict on ML.

## Notes

Held-out runs: ARM A 51/56, ARM B 24/56, always-BENIGN 20/56. ARM B versus baseline discordant pairs are 5 and 1; exact two-sided McNemar p=0.21875. ROC-AUC 0.603792 is computed over 1,923 known-scenario windows, not 56 runs. Both ARM B and always-BENIGN score 4/4 on B_bc_replacement.

# Slide 22

## Text

OBJECTIVE 5: RESULT INTERPRETATION (COMPLETED)
Telemetry Constraints Behind ARM B Performance
Telemetry starvation compounds broader feature poverty
Servo samples average 88.0 per baseline run, 44.5 for C1 and 28.0 for C3. Starvation hurts those cases, but ARM B sensitivity is also low where telemetry remains; feature poverty and class overlap are primary constraints.
Only 6 of 28 configured features were populated and used
GNSS, SyncE, oscillator and protocol-legality features are absent from ptp4l servo logs. Six features were used, but holdover_rate had zero importance; five features carried model signal.
Feature importances indicate testbed-servo artefact risk
Top importances are offset_abs_max 0.268, path_delay_mean 0.262, and offset_std 0.208. With one testbed, domain shift cannot be separated from intrinsic class overlap.
This is an argument for the rule-based layer, not against machine learning in general.

## Notes

ARM B used six populated features from 28 configured features; holdover_rate importance is 0. Feature importances: 0.267588, 0.261517, 0.208277, 0.138827, 0.123790 and 0. Servo-sample averages: baseline 88.0/run, C1 44.5/run, C3 28.0/run.

# Slide 23

## Text

WORKLET M6: LIMITATIONS DOCUMENTED (COMPLETED)
Documented Study Limitations
Planned boundary-clock swap is flagged as an attack
0/12
The provisioned context holds a single expected BC identity. 
This scenario causes 12 false ATTACK calls and dominates the 0.783 specificity. B3 contributes one UNKNOWN; excluding BC replacement, specificity is 47/48 = 0.979. Fix requires an allow-list change and a re-freeze.
GNSS spoofing is not established by this testbed
testbed limit
Downstream ptp4l telemetry alone cannot establish coherent-spoof detection. Trusted receiver/RF observables, spatial checks or an independent time anchor are outside this setup.
Held-out evidence is small and partially missing
4/scenario
Only four held-out replicates exist per scenario, and 48/168 runs lack pmc.jsonl. Intervals are wide and ARM B sees only 6 of 28 designed features.
Replicate metadata is inconsistent
36 C runs
Thirty-six C-series contexts record rep=901; the split uses the replicate encoded in the directory name. Correct this before any fresh validation claim.

## Notes

The corrected conclusion is testbed-scoped: downstream ptp4l telemetry cannot establish detection of a coherent GNSS spoof. Additional trusted receiver/RF evidence can support detection. NIST GNSS resilience resources: https://www.nist.gov/pnt . Specificity excluding BC replacement is 47/48, not 1.000.

# Slide 24

## Text

WORKLET M6: PIPELINE AUDIT (COMPLETED)
Pipeline Audit and Corrective Reruns
The audit identified four defects. Two defects had produced invalid data before the corrective reruns.
36 “replicates” were three captures copied 12 times
A script was created without the execute bit; exit 126 was silenced by redirection, and a stale capture satisfied the validity guard.
FIXED · re-run
A benign scenario never injected anything
The kernel lacks sch_netem and the failure was swallowed by || true. It was a baseline wearing a congestion label.
FIXED · rebuilt
A detector false-positived on upstream captures
No minimum-sample guard: a clock emitting 3 frames at start-up read as “rate starved”, destroying an honest abstention.
FIXED · v3
The evaluator overstated results
Pooled metrics moved with run count; an additive-only effect had been asserted from two scalars with no per-run test. V2 and v3 were subsequently compared on all 168 captures.
REPLACED
All fabricated-data runs were re-executed. Evaluator defects were corrected, and the post-observation v3 decision revision is explicitly disclosed.

## Notes

The 36 invalid runs were three scenario captures copied across 12 replicate directories. V2 and v3 verdicts were compared per run and are identical on all 168 retained captures.

# Slide 25

## Text

WORKLET M3, M5 AND M6: REMAINING WORK
Remaining Software and Hardware Validation
Software — can start immediately
Boundary-clock allow-list to close the B_bc_replacement false positive, then re-freeze and re-run
Test additional interception levels around the interpolated 60.54% crossing
Extend the randomised design space for the three new scenarios
Re-run ARM B with richer management-plane telemetry for a fairer comparison
Fault prediction before disruption — not attempted
Execute and measure corrective action — verdict labels are not actions taken
Exercise the digital twin — not run in this campaign
Measure MTTR, recovery time, availability and downtime — no figure yet
M6 deliverable: paper and IP disclosure draft
Hardware — Tier 3, requires equipment
GNSS receiver
unlocks A6 spoof, A7 jam, B1 holdover
Second physical machine
unlocks B6 oscillator drift — two crystals
Hardware-timestamping NIC
improves A4/B5 physical-impact credibility and timestamp precision
SyncE-capable PHY
unlocks B4 EEC degradation
5 of 16 classes require hardware. Three more support software detection logic but need hardware for credible physical-impact measurement.

## Notes

The 60.54% value is interpolated and needs denser direct testing. Worklet objectives still open: prediction before disruption, digital-twin validation, executed corrective action, and measured MTTR/downtime/availability.

# Slide 26

## Text

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

## Notes

This slide closes the silent worklet gaps identified by the independent V5 audit. Prediction, executed corrective action, digital-twin validation, and MTTR/recovery/availability/downtime measurement remain future work.

# Slide 27

## Text

Validated Findings and Remaining Scope
1
Real protocol execution, scoped evidence
Six linuxptp daemons and live packet-path injection; no independent clock-error instrument
2
168 live runs; base rule pre-frozen
v3 was created after v2 false positives and its revision history is disclosed
3
0.990 macro attack sensitivity · post-observation v3
Pre-frozen base: 0.625; specificity: 0.783 (0.979 excluding BC replacement)
4
Worklet objective 5 answered with evidence
On this fixed split, ARM A beats ARM B; ARM B is not distinguishable from always-BENIGN
5
Limits measured, not hidden
60.54% is interpolated; BC replacement remains open; source PCAPs are not retained in the corrected archive
Thank you
Tanmaya Kumar · Raghu Ram K · Munipalle Jaswanth Kumar
STATUS: S-PLANE DETECTION AND CLASSIFICATION EVALUATED · PREDICTION, DIGITAL TWIN AND HEALING NOT YET RUN

## Notes

Close on the evidence boundary. ARM B is not statistically distinguishable from always-BENIGN at n=56, and its B_bc_replacement performance is not a unique capability.
