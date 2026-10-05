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
PROJECT HIT: OPEN FRONTHAUL S-PLANE
PTP / SyncE timing evidence captured on brUP and brDN
Feature extraction
packet plus daemon telemetry
Rule and ML comparison
ARM A versus ARM B
Safe response decision
isolate, holdover or escalate
Validated here: packet capture, feature extraction and classification. Remaining scope: digital-twin orchestration and automated recovery.

## Notes

Architecture context follows the O-RAN reference architecture: SMO with Non-RT RIC, Near-RT RIC, O-CU-CP/O-CU-UP, O-DU, O-RU and O-Cloud. Open Fronthaul between O-DU and O-RU carries C/U/S/M planes. Official sources: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf ; https://mediastorage.o-ran.org/ecosystem-resources/O-RAN-2025.04.02.WP.O-RAN_NTN_Deployments-v08.4.pdf ; https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3219 . The highlighted project boundary is based on this repository's six-daemon S-plane testbed.

# Slide 4

## Text

WORKLET M1: PROBLEM STUDY (COMPLETED)
Open Fronthaul Timing Requirements and Security Exposure
130 ns
Category-A relative alignment target between radio units
O-RAN Open Fronthaul CUS-plane specification
1.5 µs
Application-level time-error limit from O-RU to PRTC
ITU-T G.8271.1
~2 s
Observed service failure after a timing attack in one study
TIMESAFE
Timing is distributed over the network itself, as ordinary packets.
Because timing is distributed as network traffic, it is attackable. Loss of a shared time reference can degrade radio coordination, making the S-plane a security surface as well as an engineering constraint.
The ~2 s figure is an observed result from one published study, not a standardised limit. We treat it as a design target.

## Notes

The 130 ns value is category-specific, the ±1.5 µs value is an application-level O-RU-to-PRTC limit, and the roughly 2 s result is an observation from TIMESAFE, not a standardised bound or a fastest-known claim.

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
HARDWARE-BLOCKED
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
M6
Testing and evaluation
168-run campaign + AI-vs-rule comparison
DONE
M6
Paper & IP draft
Publication + patent disclosure
NOT STARTED
M4 and M6 closed by the AI-vs-rule comparison completed on the 168-run campaign (slide 20).

## Notes

Every milestone except the paper/IP draft is now closed. M4 and M6 moved to DONE once the comparison ran.

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
IsolationForest open-set layer providing abstention
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
tcpdump on both bridges — every PTP frame on the wire is recorded, unmodified.
Real linuxptp daemons execute BMCA and servo logic on isolated network namespaces
Faults use live packet-path mechanisms, not synthetic packet rows
No independent clock-error instrument was used; synchronisation impact is inferred from protocol and servo telemetry
ITU-T G.8275.1 profile settings: domain 24, priority1 128, Sync 16/s, Announce 8/s

## Notes

Emphasise that protocol execution is real. Do not claim independently measured loss of synchronisation: the campaign uses packet captures and daemon telemetry, not an external timing instrument.

# Slide 10

## Text

WORKLET M2: KPI CONFIGURATION (COMPLETED)
Timing Configuration Derived from Standards
The campaign read back every configuration value from the running system and traced it to the governing standard.
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
G.8275.1 forwardable address
Timestamping
software
Platform limit — see next slide
Some ITU-T values are cited via vendor application notes because the normative recommendations are paywalled — disclosed in the workbooks.

## Notes

If challenged on sourcing: we disclose that several standards values come from authoritative secondary sources, and recommend confirming against normative text before publication.

# Slide 11

## Text

WORKLET M2: PLATFORM CONSTRAINTS (COMPLETED)
Verified Platform Constraints
Direct queries of the running system confirmed each platform limitation.
!
No PTP hardware clock
ls /dev/ptp* → empty
Software timestamping only: microsecond noise floor against a nanosecond target
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

This slide is deliberately placed before the results. It sets the ceiling on what any result here can claim.

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

WORKLET M5: DECISION ENGINE (COMPLETED)
Attack Classification Using Protocol and Operator Context
Classification combines protocol consistency, observed timing behaviour and provisioned operator context.
BENIGN faults
Degrade timing in a way that is self-consistent with a declared, standards-compliant state change — clockClass 6→7 on GNSS loss, an ESMC quality downgrade, drift bounded by the holdover mask.
ATTACKS
Produce illegal or unauthorised evidence, such as forged Announce fields, non-monotonic sequence IDs, or a superior grandmaster that is outside the provisioned allow-list.
Worked example — the discriminator that decides it
A grandmaster suddenly changes.
It could be B2 — a planned grandmaster failover, entirely legitimate
It could be A1 — Announce/BMCA spoofing by a rogue master
The decisive test: is the new grandmaster's clock identity on the provisioned allow-list?

## Notes

This is the LOOK-ALIKES logic. Classification is testing self-consistency against the standard, not reacting to fault magnitude.

# Slide 14

## Text

WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)
Safe Abstention for Ambiguous Timing Events
The decision engine abstains when packet evidence cannot support a reliable attack or benign classification.
ATTACK
Protocol-inconsistent evidence present
ISOLATE
BENIGN
Only provisioned clocks, no legality violation
TOLERATE / HOLDOVER
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
A1
Rogue grandmaster / BMCA spoof
SW
A2
Sync / Follow_Up spoofing
SW
A3
Replay
SW
A4
Delay (time) attack
SW*
A5
DoS / PTP flooding
SW
A6
GNSS spoofing
HW
A7
GNSS jamming
HW
A8
Rogue boundary clock
SW*
BENIGN FAULTS
B1
GNSS holdover
HW
B2
Planned GM changeover
SW
B3
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
B7
Topology reconfiguration
SW
B8
Measurement noise floor
SW
Attack classes align where applicable with ETSI TR 104 106. Benign classes are test conditions, not threat identifiers. SW* means software detection logic only; physical impact needs hardware.

## Notes

Taxonomy from the latest parameter matrix: 8 fully software classes, 3 software detection-only classes (A4, A8, B5), and 5 hardware-required classes (A6, A7, B1, B4, B6).

# Slide 16

## Text

WORKLET M3: FAULT INJECTION (COMPLETED)
Fault Injection on the Live Packet Path
Extra real PTP daemons
A1 · A8
A new namespace runs a genuine ptp4l with attacker-chosen identity and a superior priority2, then competes in BMCA for real.
Scapy packet injection
A2 · C2 · C3
Hand-built frames: forged Sync with manipulated originTimestamp; illegal version/length/control fields; Announce with leap61 set and UTC offset wrong.
Capture and replay
A3
tcpdump captures live frames mid-run; tcpreplay retransmits them — genuinely stale timestamps and reused sequence IDs.
Link and queue manipulation
A5 · C1 · B3 · B7
Flooding; blackholing the boundary clock's downstream port; a tbf bottleneck with competing non-PTP traffic; bouncing an RU link.
An attack and its benign twin are often the same physical action — what separates them is the provisioned context, not the packets.

## Notes

B2 and B_unplanned_failover are literally the same command - kill the grandmaster. Only the maintenance-window context differs.

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
rules scored on the same runs
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
Green = the three coverage gaps closed this cycle. Red = the one known open failure, B_bc_replacement, explained on slide 22.

## Notes

Per-scenario is the primary metric. Point at the three green rows - those are the new detectors - and be upfront about the red row.

# Slide 19

## Text

WORKLET M6: PRIMARY RESULTS (COMPLETED)
Results Across 168 Live Runs
0.990
Macro attack sensitivity
across 8 attack scenarios
0.783
Macro specificity
across 5 benign scenarios
1.000
Abstention correctness
ambiguous failover → UNKNOWN
0.875
Attribution accuracy
correct fault identified
Three coverage gaps closed this cycle: packet removal, malformed frames and whole-second abuse went from 0/12 to 11/12, 12/12 and 12/12 — with no loss of specificity.
Specificity is 0.783 — not 1.000 — because of a single known failure. We report it rather than exclude it.

## Notes

Lead with sensitivity, but do not skip past the 0.783. Volunteering the weakness is what makes the rest credible.

# Slide 20

## Text

WORKLET M6: DETECTION BOUNDARY (COMPLETED)
Measured Boundary of the Interception Detector
The evaluation measured adjacent interception levels and reports the approximately 62% boundary as an interpolation.
Fraction of the observation window blackholed
75 %
observed / declared rate  0.366
caught
70 %
observed / declared rate  0.414
caught
65 %
observed / declared rate  0.458
caught
60 %
observed / declared rate  0.505
MISSED
Detection threshold
0.500
The detector fires when a source delivers below half the rate it itself declares. At a 60 % blackhole the ratio is 0.505 — a 1 % margin above the threshold, so the attack evades.
Observed: 65% blackhole was caught and 60% was missed. The ~62% evasion boundary is an interpolation, not a directly tested point. Short or bursty interception may average out.

## Notes

This is why C1 is 11/12 and not 12/12. Presenting the boundary is more useful than a clean number.

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
ARM B outputs BENIGN on 47/56 and has ROC-AUC 0.604. It scores 24/56 versus 20/56 for always-BENIGN (paired exact McNemar p = 0.219). Both score 4/4 on B_bc_replacement, so that result is not unique.
No measured combination beats the rule arm
OR-combination 0.893, rule-first-then-ML 0.839, consensus 0.429 — all below ARM A's 0.911. No unmeasured combination is recommended.
Scope condition: ARM B ran on 6 of 28 designed features — GNSS, SyncE and oscillator telemetry do not exist in ptp4l logs. This is not a general verdict on ML.

## Notes

The always-BENIGN control scores attack 0/32, benign 20/20, abstention 0/4, and exact accuracy 20/56. ARM B improves by only four runs and is not statistically distinguishable at this sample size (paired exact McNemar p = 0.21875). Its B_bc_replacement result is shared by the constant predictor and is not a unique learned capability.

# Slide 22

## Text

OBJECTIVE 5: RESULT INTERPRETATION (COMPLETED)
Telemetry Constraints Behind ARM B Performance
Its input is suppressed by the attacks it must detect
C1 blackholes the timing path and C3 disrupts BMCA. Servo samples fall from 88 per baseline run to 44 and 28. The ML arm loses evidence; the rule arm can still use packet-rate deficit plus legality and context evidence.
Only 6 of 28 features were observable
GNSS, SyncE, oscillator and all protocol-legality features are absent from ptp4l servo logs. The model could key only on offset, path-delay and PDV magnitude.
Feature importances indicate testbed-servo artefact risk
Top importances are offset_abs_max 0.268, path_delay_mean 0.262, and offset_std 0.208. With one testbed, domain shift cannot be separated from intrinsic class overlap.
This is an argument for the rule-based layer, not against machine learning in general.

## Notes

The sparsity asymmetry is the most interesting architectural finding: attacks that starve telemetry blind a telemetry-based detector but not a packet-based one.

# Slide 23

## Text

WORKLET M6: LIMITATIONS DOCUMENTED (COMPLETED)
Documented Study Limitations
Planned boundary-clock swap is flagged as an attack
0/12
The provisioned context holds a single expected BC identity. This one scenario is the entire reason specificity is 0.783 rather than 1.000. Fix requires an allow-list change and a re-freeze.
A coherent GNSS spoof is undetectable
physical limit
A spoof that perfectly mimics a healthy clock is in-distribution from a single reference. No software feature engineering removes this — it needs an independently trustworthy anchor.
Held-out evidence is small and partially missing
4/scenario
Only four held-out replicates exist per scenario, and 48/168 runs lack pmc.jsonl. Intervals are wide and ARM B sees only 6 of 28 designed features.
Replicate metadata is inconsistent
36 C runs
Thirty-six C-series contexts record rep=901; the split uses the replicate encoded in the directory name. Correct this before any fresh validation claim.

## Notes

Volunteering these is deliberate. A reviewer who finds an undisclosed hole trusts nothing else in the deck.

# Slide 24

## Text

WORKLET M6: PIPELINE AUDIT (COMPLETED)
Pipeline Audit and Corrective Reruns
The audit identified four defects. Two defects had produced invalid data before the corrective reruns.
36 “replicates” were one capture copied 12 times
A script created non-executable returned exit 126, silenced by output redirection; a stale capture then satisfied the validity guard.
FIXED · re-run
A benign scenario never injected anything
The kernel lacks sch_netem and the failure was swallowed by || true. It was a baseline wearing a congestion label.
FIXED · rebuilt
A detector false-positived on upstream captures
No minimum-sample guard: a clock emitting 3 frames at start-up read as “rate starved”, destroying an honest abstention.
FIXED · v3
The evaluator overstated results
Pooled metrics moved with run count; additive-only was “proven” by comparing two scalars.
REPLACED
All fabricated-data runs were re-executed. Evaluator defects were corrected, and the post-observation v3 decision revision is explicitly disclosed.

## Notes

Including this is a deliberate choice. Finding and disclosing our own defects is stronger evidence of rigour than a clean set of numbers would be.

# Slide 25

## Text

WORKLET M3, M5 AND M6: REMAINING WORK
Remaining Software and Hardware Validation
Software — can start immediately
Boundary-clock allow-list to close the B_bc_replacement false positive, then re-freeze and re-run
Test additional interception levels around the interpolated ~62% boundary
Extend the randomised design space for the three new scenarios
Re-run ARM B with richer management-plane telemetry for a fairer comparison
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

Hardware priorities: GNSS receiver for A6/A7/B1, a second oscillator for B6, SyncE hardware for B4, and a hardware-timestamping NIC to improve A4/B5 physical-impact measurement.

# Slide 26

## Text

Validated Findings and Remaining Scope
1
Real protocol execution, scoped evidence
Six linuxptp daemons and live packet-path injection; no independent clock-error instrument
2
168 live runs; base rule pre-frozen
v3 was created after v2 false positives and its revision history is disclosed
3
0.990 macro attack sensitivity
Three coverage gaps closed; benign specificity remains 0.783
4
Worklet objective 5 answered with evidence
On this fixed split, ARM A beats ARM B; ARM B is not distinguishable from always-BENIGN
5
Limits measured, not hidden
~62% is interpolated; BC replacement remains open; 5 HW plus 3 detection-only classes
Thank you
Tanmaya Kumar · Raghu Ram K · Munipalle Jaswanth Kumar
WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE

## Notes

Close on the evidence boundary. ARM B is not statistically distinguishable from always-BENIGN at n=56, and its B_bc_replacement performance is not a unique capability.
