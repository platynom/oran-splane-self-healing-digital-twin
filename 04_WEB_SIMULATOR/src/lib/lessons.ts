/**
 * Lesson content. Facts are taken from the project documents named in each `source`:
 *   GUIDE   = 00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/SPlane_Project_Story_Guide.pdf
 *   RESULTS = 03_RECOVERY_LOOP_S-PLANE/RESULTS_2026-10-05.md
 *   DESIGN  = 03_RECOVERY_LOOP_S-PLANE/RECOVERY_LOOP_DESIGN.md
 *   PREREG  = 03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md
 *   STD     = 03_RECOVERY_LOOP_S-PLANE/STANDARDS_EVIDENCE.md
 * Widgets that use illustrative numbers say so on screen.
 */

export type Widget =
  | { type: "planes" }
  | { type: "budget" }
  | { type: "topology-tour" }
  | { type: "sequence" }
  | { type: "offset" }
  | { type: "profile-check" }
  | { type: "bmca" }
  | { type: "steps-removed" }
  | { type: "lookalikes" }
  | { type: "verdict-game" }
  | { type: "verdict-actions" }
  | { type: "replay"; scenarios: string[]; rep?: number; note?: string }
  | { type: "loop-stepper" }
  | { type: "policy" }
  | { type: "limits" };

export interface Step {
  id: string;
  title: string;
  body: string[];
  widget: Widget;
  source: string;
  task?: string; // what the learner must do before "Continue" unlocks (widgets report completion)
}

export interface QuizQ {
  id: string;
  prompt: string;
  options: string[];
  answer: number;
  explanation: string;
  citation: string;
}

export interface Lesson {
  id: string;
  n: number;
  title: string;
  summary: string;
  minutes: number;
  steps: Step[];
  quiz: QuizQ[];
}

export const LESSONS: Lesson[] = [
  {
    id: "oran-splane",
    n: 1,
    title: "O-RAN and the S-plane",
    summary: "Why a radio unit needs time from the network, and where that time can be attacked.",
    minutes: 6,
    steps: [
      {
        id: "planes",
        title: "A base station in pieces",
        body: [
          "O-RAN splits the base station into the O-CU, the O-DU and the O-RU, with standard interfaces between them. The link between the O-DU and the O-RU is the Open Fronthaul (split option 7-2x).",
          "Four kinds of traffic share the fronthaul. Select each plane to see what it carries.",
        ],
        widget: { type: "planes" },
        task: "Open all four planes.",
        source: "GUIDE ch. 1, citing ETSI TS 103 982 V8.0.0 cl. 3.1 and 6.3.3–6.3.6",
      },
      {
        id: "budget",
        title: "How tight is the timing budget?",
        body: [
          "Radio units that cooperate (MIMO, carrier aggregation) must transmit at the same instant. Drag the time error and see which published limit it breaks first.",
        ],
        widget: { type: "budget" },
        task: "Move the slider past at least one limit.",
        source: "GUIDE ch. 2: O-RAN timing category A (130 ns relative), ITU-T G.8271.1 (±1.5 µs at point E), 3GPP TS 38.104 cl. 9.6.3.2 (65 ns TAE for MIMO), TS 38.133 (3 µs cell phase)",
      },
      {
        id: "topology",
        title: "The testbed you will replay",
        body: [
          "The project's testbed has the LLS-C3 shape: a grandmaster feeds a boundary clock, which feeds the radio units. There is no O-DU in the timing chain.",
          "Six real linuxptp 4.0 daemons run in Linux network namespaces on one host, wired by two software bridges (brUP for the grandmasters, brDN for the radio units). Select each device.",
        ],
        widget: { type: "topology-tour" },
        task: "Inspect every device.",
        source: "GUIDE ch. 1 and 7; PREREG s2",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Which Open Fronthaul plane carries time and frequency to the O-RU?",
        options: ["C-plane", "U-plane", "S-plane", "M-plane"],
        answer: 2,
        explanation: "The S-plane (synchronization plane) carries PTP time and SyncE frequency. C, U and M carry control, user samples and management.",
        citation: "ETSI TS 103 982 cl. 6.4.7, via GUIDE ch. 1",
      },
      {
        id: "q2",
        prompt: "Can the RIC read S-plane health of the O-RU over the E2 interface?",
        options: [
          "Yes, E2 terminates at the O-RU",
          "No, E2 ends at the O-CU-CP, O-CU-UP and O-DU, so evidence must come from the timing protocol itself",
          "Only for LLS-C1 deployments",
        ],
        answer: 1,
        explanation: "E2 does not reach the O-RU. That is why this project works from PTP packets, ptp4l logs and pmc management queries.",
        citation: "ETSI TS 103 982 cl. 6.3.3–6.3.6, via GUIDE ch. 1",
      },
      {
        id: "q3",
        prompt: "The testbed is GM → boundary clock → radio units with no O-DU in the timing chain. Which LLS configuration is that?",
        options: ["LLS-C1", "LLS-C2", "LLS-C3", "LLS-C4"],
        answer: 2,
        explanation: "LLS-C3: a grandmaster in the network provides time; the O-DU is not in the timing chain. LLS-C4 uses a local GNSS receiver at the O-RU.",
        citation: "O-RAN.WG4.CUS.0 v06.00 via Armstrong (ATIS 2023), secondary source, GUIDE ch. 1",
      },
    ],
  },
  {
    id: "ptp",
    n: 2,
    title: "How PTP works",
    summary: "Four timestamps, one offset, and the telecom profile the testbed runs.",
    minutes: 7,
    steps: [
      {
        id: "sequence",
        title: "Four timestamps",
        body: [
          "The master sends Sync (and Follow_Up with the exact send time t1). The slave notes the arrival t2, sends Delay_Req at t3, and the master returns the arrival time t4 in Delay_Resp.",
          "Step through the exchange.",
        ],
        widget: { type: "sequence" },
        task: "Step through all four messages.",
        source: "IEEE 1588-2019 two-step delay request-response, as explained in GUIDE ch. 3",
      },
      {
        id: "offset",
        title: "Compute the offset yourself",
        body: [
          "Assuming the cable takes the same time in both directions: mean path delay = [(t2 − t1) + (t4 − t3)] / 2 and offset from master = [(t2 − t1) − (t4 − t3)] / 2.",
          "The numbers below are illustrative. Find the slave's offset, then try making the path asymmetric to see the error it creates.",
        ],
        widget: { type: "offset" },
        task: "Enter the correct offset.",
        source: "GUIDE ch. 3; asymmetry consequence from the fault catalogue (A4 / B5: constant time error equal to half the asymmetry)",
      },
      {
        id: "profile",
        title: "The telecom profile G.8275.1",
        body: [
          "A profile fixes the settings for one industry. The testbed ran ITU-T G.8275.1: domain 24, priority1 128, Sync 16/s, Announce 8/s, L2 multicast 01-1B-19-00-00-00, alternate BMCA.",
          "Because the profile fixes these values, many security checks become yes/no legality tests. Find the Announce messages that break the profile.",
        ],
        widget: { type: "profile-check" },
        task: "Classify all four Announce messages.",
        source: "GUIDE ch. 3 (testbed configuration read back from the running system)",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "t1 = 1 000, t2 = 6 400, t3 = 9 000, t4 = 13 600 (ns). What is the offset from master?",
        options: ["+400 ns", "+5 000 ns", "−400 ns", "+800 ns"],
        answer: 0,
        explanation: "(t2−t1) = 5 400, (t4−t3) = 4 600. Offset = (5 400 − 4 600)/2 = +400 ns; mean path delay = (5 400 + 4 600)/2 = 5 000 ns.",
        citation: "IEEE 1588-2019 delay request-response mechanism, GUIDE ch. 3",
      },
      {
        id: "q2",
        prompt: "Why is a constant one-way delay added by an in-path element dangerous for PTP?",
        options: [
          "It raises the message rate",
          "PTP assumes symmetric paths, so the slave absorbs half the asymmetry as a time error it cannot see",
          "It changes the clockIdentity",
        ],
        answer: 1,
        explanation: "With an asymmetric path the computed offset is wrong by half the asymmetry. This is the A4 delay attack and the benign B5 static asymmetry; neither was producible on this testbed (no sch_netem).",
        citation: "Fault catalogue A4 / B5 (ORAN_Fault_Detectability_v2026-10-05.xlsx)",
      },
      {
        id: "q3",
        prompt: "Every ptp4l daemon in the testbed ran with free_running 1. What does that mean for the results?",
        options: [
          "Clocks were steered with hardware timestamps",
          "Offsets were measured but clocks were never steered, so outcomes are who the RUs follow, not nanosecond time error",
          "PTP was disabled",
        ],
        answer: 1,
        explanation: "With free_running 1 the servo stays in state s0. The recovery evaluation therefore scores parent, grandmaster and port state, not time error.",
        citation: "PREREG s2 and s6; RESULTS s6",
      },
    ],
  },
  {
    id: "bmca",
    n: 3,
    title: "BMCA: who becomes the master?",
    summary: "The election every clock runs, and why a perfectly legal rogue can win it.",
    minutes: 7,
    steps: [
      {
        id: "arena",
        title: "Run the election",
        body: [
          "Every clock broadcasts Announce messages and runs the Best Master Clock Algorithm. Fields are compared in order; the smaller value wins and the first difference decides.",
          "Drag clocks into the arena (or use the Add buttons) and change their fields. Then make the rogue win using only values the profile allows.",
        ],
        widget: { type: "bmca" },
        task: "Make the rogue win with legal values.",
        source: "IEEE 1588 default data-set comparison (simplified); GUIDE ch. 3 and ch. 9 (A1 replicate 1: rogue clockClass 6 vs legitimate 248)",
      },
      {
        id: "steps",
        title: "stepsRemoved and the rogue boundary clock",
        body: [
          "A boundary clock re-serves the grandmaster's time and adds one to stepsRemoved. When two paths lead to the same grandmaster, the BMCA prefers the shorter one.",
        ],
        widget: { type: "steps-removed" },
        task: "Compare both paths.",
        source: "RESULTS s4 (A8: 160/160 samples on the real BC in 5/5 control runs)",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "In A1 replicate 1 the rogue advertised priority1 128, priority2 1, clockClass 6. Which field broke the standard?",
        options: ["priority1", "clockClass", "None: every field was legal; only the operator's allow-list exposes it", "priority2"],
        answer: 2,
        explanation: "The rogue wins the election fairly. The clause that fired was 'unauthorised clock advertising itself as grandmaster (not in the provisioned allow-list)'.",
        citation: "GUIDE ch. 9, traceability workbook (ORAN_SPlane_Packets_to_Classification_2026-10-05.xlsx)",
      },
      {
        id: "q2",
        prompt: "In the 5 A8 control runs, did RU1/RU2 re-parent to the rogue boundary clock?",
        options: ["Yes, in 5/5", "No: their parent never changed (160/160 samples on the real BC)", "Only RU3 did"],
        answer: 1,
        explanation: "With the same grandmaster on both paths the BMCA prefers fewer stepsRemoved, so the rogue BC was a candidate, not a takeover. The v8 deck wording overstated this.",
        citation: "RESULTS s4",
      },
      {
        id: "q3",
        prompt: "What value does ITU-T G.8275.1 fix for priority1?",
        options: ["0", "64", "128", "255"],
        answer: 2,
        explanation: "G.8275.1 fixes priority1 at 128; any other value is illegal under the profile and is one of the rule's legality checks.",
        citation: "GUIDE ch. 3 and ch. 10 (rule check 5)",
      },
    ],
  },
  {
    id: "attack-vs-benign",
    n: 4,
    title: "Attack vs benign: same symptom, opposite action",
    summary: "Why 'anomaly' is not enough, and how operator context decides.",
    minutes: 8,
    steps: [
      {
        id: "lookalikes",
        title: "Look-alike pairs",
        body: [
          "A planned grandmaster changeover (B2) and a rogue grandmaster (A1) look the same in the packets: the grandmaster changes. For a benign fault the right move is to ride it out; for an attack it is to isolate the source.",
          "Open each pair to see the decisive test.",
        ],
        widget: { type: "lookalikes" },
        task: "Open at least three pairs.",
        source: "ORAN_SPlane_Attack_vs_Benign_Classification_v2026-10-05.xlsx (LOOK-ALIKES)",
      },
      {
        id: "verdict-game",
        title: "You are the rule",
        body: [
          "Each card is a real run from the 168-run campaign with the operator context the rule received. Choose ATTACK, BENIGN or UNKNOWN; you then see what the frozen v3 rule actually returned.",
        ],
        widget: { type: "verdict-game" },
        task: "Classify every card.",
        source: "Campaign archive splane_campaign_CORRECTED_2026-09-20.tgz (decision_v3.json, context.json)",
      },
      {
        id: "verdict-actions",
        title: "Three answers, three actions",
        body: ["The loop maps each verdict to one response. Select a verdict."],
        widget: { type: "verdict-actions" },
        task: "Open all three verdicts.",
        source: "GUIDE ch. 4; DESIGN policy table",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "The grandmaster identity changes. What decides between B2 (planned changeover) and A1 (rogue)?",
        options: [
          "The size of the offset step",
          "Whether the new grandmaster is on the provisioned allow-list and whether a maintenance window is open",
          "The Announce rate",
        ],
        answer: 1,
        explanation: "For a benign fault the declaration and the observation agree; for an attack they disagree. The decisive test is the allow-list plus the maintenance state.",
        citation: "GUIDE ch. 4; LOOK-ALIKES row 1 (TIMESAFE; Telestream WP; G.8275.1)",
      },
      {
        id: "q2",
        prompt: "GM-A fails with no maintenance window; the allow-listed GM-B takes over. What is the correct verdict?",
        options: ["ATTACK", "BENIGN", "UNKNOWN: packets cannot reveal intent, so escalate to an operator"],
        answer: 2,
        explanation: "The campaign rule returned UNKNOWN in 12/12 runs, and the loop escalated without acting in 5/5.",
        citation: "EVALUATION_V4.json (abstention 12/12); RESULTS s2 (H4)",
      },
      {
        id: "q3",
        prompt: "How did the frozen rule score the planned boundary-clock replacement (B_bc_replacement) in the campaign?",
        options: ["12/12 correct", "0/12: it reads the provisioned replacement as a rogue BC (A8): an open failure", "6/12"],
        answer: 1,
        explanation: "This is the one open benign failure. In the recovery loop the safety guard keeps it harmless: the replacement's port is provisioned in the master role, so nothing is isolated and the loop escalates once.",
        citation: "Packets_to_Classification PER-SCENARIO; DESIGN 'Why the B_bc_replacement false alarm causes no harm'",
      },
    ],
  },
  {
    id: "attacks",
    n: 5,
    title: "The eight attacks, replayed",
    summary: "A1, A2, A3, A5, A8, C1, C2, C3: recorded control runs next to recorded loop runs.",
    minutes: 12,
    steps: [
      {
        id: "takeovers",
        title: "Takeovers: A1 rogue grandmaster and C3 whole-second abuse",
        body: [
          "In both, the radio units followed the attacker for about 38.5 s of 40 when nothing was done. With the loop they were off a legitimate parent for 2.0 s (median, 5/5 restored).",
          "C3's forger uses GM-A's identity directly on the RU segment, so ptp4l's 'selected best master' line cannot show the capture; the corrected pmc -d 24 observer does.",
        ],
        widget: { type: "replay", scenarios: ["A1_rogue_master", "C3_wholesecond"] },
        task: "Play a replay to the end.",
        source: "RESULTS s1 and s4; EVALUATION_RL.json",
      },
      {
        id: "injections",
        title: "Injections that did not capture the RUs: A2, A3, A5, C2",
        body: [
          "These attacks entered through RU3's port. RU1 and RU2 were never pulled off their parent in the control arm, so H1 passes trivially here; what the loop adds is containment: the ingress port was isolated and verified in 5/5 runs each.",
          "Collateral: isolating p-v-ru3 also blocks RU3's own Delay_Req, so RU3's timing is reported separately.",
        ],
        widget: { type: "replay", scenarios: ["A2_sync_spoof", "A3_replay", "A5_dos_flood", "C2_malformed"] },
        task: "Play a replay to the end.",
        source: "RESULTS s1, s2 (H1 note), s6 (collateral on RU3)",
      },
      {
        id: "path",
        title: "Path attacks: A8 rogue boundary clock and C1 interception",
        body: [
          "A8: the rogue BC was a BMCA candidate, not a takeover; the loop isolated its port anyway (5/5, verified).",
          "C1: the BC's downstream port is blackholed and never restored. The frozen rule cannot see an ongoing total blackhole in a sliding window, so the loop's service-continuity channel fails over to the standby BC after 2 s without Announce: 39.0 s unhealthy without action, 2.5 s with the loop.",
        ],
        widget: { type: "replay", scenarios: ["C1_removal", "A8_rogue_bc"] },
        task: "Play a replay to the end.",
        source: "RESULTS s1, s4; DESIGN 'Two detection channels'",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Why does the loop need a second detection channel for C1?",
        options: [
          "C1 frames are malformed",
          "The frozen rule's starvation clause cannot hold during a continuous blackhole in a sliding window, so only 'no Announce for 2 s' detects it",
          "C1 uses a rogue identity",
        ],
        answer: 1,
        explanation: "Clause D1 needs the starved source active over half the window and delivering below half its declared rate; during a total blackhole both cannot hold. The campaign caught C1 only because its captures had a restore tail.",
        citation: "DESIGN 'Two detection channels'; RESULTS s4",
      },
      {
        id: "q2",
        prompt: "In A2, A3, A5, A8 and C2, what did the loop demonstrate?",
        options: ["A large restoration benefit", "Containment (verified isolation); RU1/RU2 had no measurable impact even without action", "Nothing"],
        answer: 1,
        explanation: "Control-arm unhealthy time for RU1/RU2 was 0 s in these scenarios; H1 passes trivially and H2 shows containment.",
        citation: "RESULTS s1 and s2",
      },
      {
        id: "q3",
        prompt: "What was the A1 median time RU1/RU2 spent off a legitimate parent: control vs loop?",
        options: ["38.5 s vs 2.0 s", "39.0 s vs 2.5 s", "16.5 s vs 3.5 s"],
        answer: 0,
        explanation: "A1: 38.5 s of 40 without action (5/5 never recovered) and 2.0 s median with the loop. 39.0 vs 2.5 is C1; 16.5 vs 3.5 is the B3 r17 outage.",
        citation: "RESULTS s1, recomputed from the database on the Dashboard",
      },
    ],
  },
  {
    id: "benign",
    n: 6,
    title: "Benign faults and the ambiguous case",
    summary: "When the right action is no action, and the one run where the loop acted anyway.",
    minutes: 10,
    steps: [
      {
        id: "planned",
        title: "Planned work: B2 changeover and B7 topology change",
        body: [
          "Both happen during an open maintenance window and involve only provisioned clocks. The loop takes no action (0 disruptive actions in 5/5 each).",
        ],
        widget: { type: "replay", scenarios: ["B2_gm_failover", "B7_topology_change", "baseline"] },
        task: "Play a replay to the end.",
        source: "RESULTS s1; EVALUATION_RL.json",
      },
      {
        id: "b3r17",
        title: "B3 congestion, replicate 17: the H3 failure",
        body: [
          "In this run the boundary clock hit 'timed out while polling for tx timestamp' and its downstream port went FAULTY for about 16 s. Without action RU1/RU2 lost timing for 16.5 s. With the loop, the service-continuity channel activated the standby BC at T0 + 5.1 s and RU1/RU2 were unhealthy for 3.5 s.",
          "The action shortened a genuine outage, but the pre-registered criterion was zero disruptive actions on benign runs, so H3 is reported as FAILED.",
        ],
        widget: { type: "replay", scenarios: ["B3_pdv_congestion"], rep: 17, note: "Locked to replicate 17" },
        task: "Play the replay to the end.",
        source: "RESULTS s3",
      },
      {
        id: "guarded",
        title: "B_bc_replacement and B_unplanned_failover",
        body: [
          "B_bc_replacement: the base rule still says ATTACK (A8), but the replacement port is provisioned by the maintenance ticket, so the guard escalates once and nothing is isolated.",
          "B_unplanned_failover: intent is unknowable from packets, so the loop escalates (5/5) and takes no action.",
        ],
        widget: { type: "replay", scenarios: ["B_bc_replacement", "B_unplanned_failover"] },
        task: "Play a replay to the end.",
        source: "DESIGN; RESULTS s2 (H4)",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "The failover in B3 r17 shortened a real 16.5 s outage to 3.5 s. Why is H3 still FAILED?",
        options: [
          "Because the loop was wrong",
          "The pre-registered criterion was zero disruptive actions on benign runs; the outcome is reported, not re-run or re-defined",
          "Because verification failed",
        ],
        answer: 1,
        explanation: "The service-loss trigger acts on consequence, not intent. The pre-registration did not anticipate a benign run turning into a real outage.",
        citation: "RESULTS s3; PREREG s5",
      },
      {
        id: "q2",
        prompt: "What did the loop do in B_unplanned_failover?",
        options: ["Isolated GM-B", "Activated the standby BC", "Nothing disruptive; it escalated in 5/5 runs"],
        answer: 2,
        explanation: "UNKNOWN → ESCALATE. H4 (honest abstention) passed.",
        citation: "RESULTS s2",
      },
      {
        id: "q3",
        prompt: "Why did B_bc_replacement cause no isolation even though the base rule returned ATTACK (A8)?",
        options: [
          "The rule was fixed",
          "The replacement's port is provisioned in the master role and carries only its provisioned identity, so the guard escalates instead of isolating",
          "The loop was in observe mode",
        ],
        answer: 1,
        explanation: "This is a property of the loop's safety guard; the rule itself is not fixed.",
        citation: "DESIGN 'Why the B_bc_replacement false alarm causes no harm here'",
      },
    ],
  },
  {
    id: "loop-limits",
    n: 7,
    title: "The recovery loop and its limits",
    summary: "Detect, localise, decide, act, verify, roll back: and what the evidence does not show.",
    minutes: 8,
    steps: [
      {
        id: "stepper",
        title: "Inside the loop",
        body: ["Walk through the seven stages with the pre-registered parameters."],
        widget: { type: "loop-stepper" },
        task: "Visit all seven stages.",
        source: "DESIGN; PREREG s3",
      },
      {
        id: "policy",
        title: "Policy table and the safety guard",
        body: ["Each signal maps to one action and one standards basis. Choose a signal."],
        widget: { type: "policy" },
        task: "Open every row.",
        source: "DESIGN policy table; STD s1–s3",
      },
      {
        id: "limits",
        title: "What the evidence does not establish",
        body: ["Turn every card. These limits apply to every number in this app."],
        widget: { type: "limits" },
        task: "Turn all cards.",
        source: "PREREG s6; RESULTS s6; GUIDE ch. 7",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "What must verification observe after an action?",
        options: [
          "Offset below 100 ns",
          "Every non-isolated RU with a provisioned master-role parent, an allow-listed GM and portState SLAVE or UNCALIBRATED, within 20 s; otherwise roll back and escalate",
          "No ATTACK verdicts for 60 s",
        ],
        answer: 1,
        explanation: "Verification uses pmc -d 24 on each RU; on failure the action is undone and the operator alerted.",
        citation: "PREREG s3; DESIGN policy table",
      },
      {
        id: "q2",
        prompt: "Is the nftables isolation an implementation of IEEE 1588-2019 Annex P authentication?",
        options: [
          "Yes",
          "No: it is a software stand-in for a switch-port PTP filter/ACL; linuxptp 4.0 has no authentication TLV",
          "Only in loop runs",
        ],
        answer: 1,
        explanation: "Authentication TLV support arrived only in linuxptp 4.3 (V2 evidence). The loop enforces provisioned port roles at the bridge instead.",
        citation: "STD s1 'How the loop applies it'",
      },
      {
        id: "q3",
        prompt: "How many replicates per arm per scenario back each result?",
        options: ["5, so the intervals are wide", "12", "140"],
        answer: 0,
        explanation: "14 scenarios × 2 arms × 5 replicates = 140 runs. H3's 1/25 has a Wilson 95 % interval of [0.007, 0.195].",
        citation: "PREREG s2; RESULTS s2 and s6",
      },
    ],
  },
];

export function lessonById(id: string) {
  return LESSONS.find((l) => l.id === id);
}
