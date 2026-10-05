from pathlib import Path
from textwrap import dedent

root = Path(__file__).resolve().parent

reports = {
    "P_ACM_2024_SpotLight_Open_RAN_System_for_Dynamic_Spectrum_Access_and_Anomaly_Detection_REPORT.txt": """
Paper: SpotLight: An Open RAN System for Dynamic Spectrum Access and Anomaly Detection
Publication/source: ACM MobiCom / Open RAN system paper, 2024
Pages visually reviewed: 4
Visual assets: _visual_review/P_ACM_2024_SpotLight_Open_RAN_System_for_Dynamic_Spectrum_Access_and_Anomaly_Detection/ALL_PAGES_CONTACT_SHEET.png

Core idea:
SpotLight is a compact Open RAN anomaly detection system focused on dynamic spectrum access and abnormal spectrum/resource behavior. It is useful as a concrete anomaly-detection subsystem reference rather than a full O-RAN architecture survey.

Page-wise visual review:
- Page 1: Repository/front matter and metadata. No technical architecture content.
- Page 2: Abstract, introduction, and motivation. Frames Open RAN disaggregation as a source of new anomaly/security risks.
- Page 3: Main technical page. Shows SpotLight system architecture and anomaly detection behavior against a baseline.
- Page 4: References.

Important visuals:
- System architecture figure.
- Anomaly detection behavior figure comparing SpotLight with TranAD.

Relation to our project:
Use this for the radio/RAN anomaly-detection module in the Digital Twin. It supports a monitored spectrum/resource state twin that detects abnormal RAN behavior before a guarded healing controller acts.

Project mapping:
- Layer: Radio/RAN monitoring, O-DU/O-CU adjacent anomaly detection.
- Twin object: Spectrum/resource state twin.
- AI function: Anomaly detection.
- Self-healing relevance: Detection trigger before traffic steering, resource reallocation, or RIC policy action.

Limitations:
Short paper; does not cover national-scale architecture, 5G Core, SMO, transport, or full O-RAN hierarchy.
""",
    "P_Elsevier_2024_Adversarial_Machine_Learning_Threat_Analysis_and_Remediation_in_ORAN_REPORT.txt": """
Paper: Adversarial Machine Learning Threat Analysis and Remediation in Open Radio Access Network (O-RAN)
Publication/source: Journal of Network and Computer Applications, Elsevier, 2024
Pages visually reviewed: 24
Visual assets: _visual_review/P_Elsevier_2024_Adversarial_Machine_Learning_Threat_Analysis_and_Remediation_in_ORAN/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This is a security survey on adversarial machine learning in O-RAN. It studies attacks against ML pipelines, xApps/rApps, telemetry, and AI-assisted control, then maps remediation approaches.

Page-wise visual review:
- Pages 1-2: Abstract, introduction, O-RAN motivation, and the security problem created by openness and intelligence.
- Pages 3-5: Core visual pages: O-RAN reference architecture, general ML pipeline, ML deployment scenarios, and taxonomy tables.
- Pages 6-9: Threat categories and attack mapping across training, inference, model, and control stages.
- Pages 10-14: Defense/remediation discussion with dense comparison matrices.
- Pages 15-21: Large tables mapping attacks, effects, defenses, and O-RAN components.
- Pages 22-24: References.

Important visuals:
- O-RAN reference architecture.
- General ML pipeline in O-RAN.
- O-RAN ML deployment scenarios.
- Adversarial threat/remediation taxonomy tables.

Relation to our project:
This should drive the security twin and AI governance design. A self-healing O-RAN network can become dangerous if telemetry, training data, models, or xApp actions are poisoned or manipulated.

Project mapping:
- Layer: Near-RT RIC, Non-RT RIC, SMO, AI/ML pipeline.
- Twin object: Security twin and ML pipeline twin.
- AI function: Poisoning/evasion/backdoor detection, model robustness monitoring.
- Self-healing relevance: Quarantine model, roll back xApp, reject suspicious telemetry, require human approval for high-risk automated changes.

Limitations:
Survey-heavy; needs pairing with concrete architecture/control papers like COMIX, xApp distillation, and the xApp/E2 anomaly paper.
""",
    "P_Elsevier_2024_Drift_Handling_Framework_for_Open_Radio_Access_Networks_REPORT.txt": """
Paper: The Drift Handling Framework for Open Radio Access Networks: An Experimental Evaluation
Publication/source: Computer Networks, Elsevier, 2024
Pages visually reviewed: 17
Visual assets: _visual_review/P_Elsevier_2024_Drift_Handling_Framework_for_Open_Radio_Access_Networks/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This paper proposes a drift-handling framework for AI/ML-enabled O-RAN control loops. It addresses the fact that traffic, RF, mobility, and service conditions change over time, causing trained models to become stale.

Page-wise visual review:
- Pages 1-2: Abstract and introduction; establishes O-RAN, RIC loops, and drift problem.
- Page 3: O-RAN architecture figure and drift-type visual.
- Pages 4-5: Proposed drift-handling architecture and initialization process.
- Pages 6-8: Algorithm/workflow sections.
- Pages 9-14: Evaluation with time-series plots, radar/bar charts, and model adaptation results.
- Page 15: Summary architecture/conclusion.
- Pages 16-17: References and author details.

Important visuals:
- O-RAN architecture with components/interfaces.
- Drift types based on data distributions.
- Proposed drift-handling framework.
- Adaptation plots under drift scenarios.

Relation to our project:
This is core for model lifecycle management in the Digital Twin. The self-healing system needs model drift detection, retraining triggers, and guardrails that pause unsafe AI actions when model confidence degrades.

Project mapping:
- Layer: Near-RT RIC, Non-RT RIC, SMO AI/ML workflow.
- Twin object: Model lifecycle twin and distribution/twin synchronization tracker.
- AI function: Drift detection, continual learning, retraining trigger.
- Self-healing relevance: Stop or downgrade AI automation when drift exceeds threshold.

Limitations:
Drift detection does not solve root cause analysis alone. It must be integrated with topology, alarms, security, and policy layers.
""",
    "P_Elsevier_2025_ORAN_xApps_Survey_and_Research_Challenges_REPORT.txt": """
Paper: O-RAN xApps: Survey and Research Challenges
Publication/source: Computer Networks, Elsevier, 2025
Pages visually reviewed: 46
Visual assets: _visual_review/P_Elsevier_2025_ORAN_xApps_Survey_and_Research_Challenges/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This is the main xApp survey in the priority set. It explains O-RAN architecture, Near-RT RIC, Non-RT RIC, xApp workflows, APIs, use cases, AI/ML methods, and research challenges.

Page-wise visual review:
- Pages 1-3: Abstract, introduction, survey structure.
- Pages 4-10: O-RAN overview, Non-RT RIC architecture, Near-RT RIC architecture, components and interfaces.
- Pages 11-17: xApp workflow, Near-RT RIC APIs, and xApp structure.
- Pages 18-24: xApp use cases such as traffic steering, anomaly detection, control, and optimization.
- Pages 25-36: Research challenges: robust AI/ML, real-time constraints, multi-xApp conflicts, scalability, privacy, explainability, and security.
- Pages 37-46: References.

Important visuals:
- Survey structure.
- O-RAN architecture.
- Non-RT RIC architecture.
- Near-RT RIC architecture.
- Near-RT RIC APIs.
- xApp structure.

Relation to our project:
This is the foundation for the RIC/xApp layer of the architecture. It defines where near-real-time self-healing can run, what the timing constraints are, and why xApp governance matters.

Project mapping:
- Layer: Near-RT RIC/xApps.
- Twin object: RIC application twin and control-loop twin.
- AI function: xApp-based anomaly detection, traffic steering, slicing, load balancing, handover optimization.
- Self-healing relevance: xApps can execute near-real-time actions but need conflict management, validation, and rollback.

Limitations:
Survey only; pair with COMIX, xApp distillation, xApp/E2 anomaly detection, and drift-handling papers.
""",
    "P_Elsevier_2026_xApp_Distillation_AI_Based_Conflict_Mitigation_in_B5G_ORAN_REPORT.txt": """
Paper: xApp Distillation: AI-Based Conflict Mitigation in B5G O-RAN
Publication/source: Computer Networks, Elsevier, 2026
Pages visually reviewed: 12
Visual assets: _visual_review/P_Elsevier_2026_xApp_Distillation_AI_Based_Conflict_Mitigation_in_B5G_ORAN/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This paper proposes xApp distillation to mitigate conflicts among independently developed xApps. This is directly relevant to safe self-healing because multiple AI controllers can optimize incompatible objectives.

Page-wise visual review:
- Pages 1-2: Abstract/introduction and motivation for multi-vendor xApp conflict.
- Pages 3-5: O-RAN architecture with xApp deployment, conflict-management background, and multi-headed DQN structure.
- Pages 6-8: Distillation methodology and algorithmic flow.
- Pages 9-10: Evaluation plots.
- Pages 11-12: Conclusion, references, author information.

Important visuals:
- O-RAN architecture with xApp deployment.
- Multi-headed DQN architecture.
- xApp distillation methodology.
- Algorithm blocks and evaluation graphs.

Relation to our project:
This paper should inform the action arbitration layer before automated healing is applied. The Digital Twin can simulate an action, while a distillation/conflict mitigation layer merges or suppresses unsafe policies.

Project mapping:
- Layer: Near-RT RIC/xApp orchestration.
- Twin object: Policy/action twin.
- AI function: Conflict mitigation and safe action selection.
- Self-healing relevance: Avoid AI-induced outages caused by conflicting healing actions.

Limitations:
Focused on xApp conflict only. Needs integration with SMO policy, ZSM governance, drift detection, and security monitoring.
""",
    "P_IEEE_2024_AI_Enabled_Digital_Twin_Network_in_6G_Survey_REPORT.txt": """
Paper: A Comprehensive Survey on Revolutionizing Connectivity Through Artificial Intelligence-Enabled Digital Twin Network in 6G
Publication/source: IEEE Access, 2024
Pages visually reviewed: 32
Visual assets: _visual_review/P_IEEE_2024_AI_Enabled_Digital_Twin_Network_in_6G_Survey/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This is a broad 6G AI-enabled network digital twin survey. It is not O-RAN-specific, but it provides strong background on 6G DTN concepts, AI methods, enabling technologies, and open challenges.

Page-wise visual review:
- Pages 1-3: Title, abstract, introduction, wireless evolution tables.
- Pages 4-6: AI-enabled DTN architecture and survey structure.
- Pages 7-10: Fundamental services and enabling technologies.
- Pages 11-16: Large comparison tables.
- Pages 17-26: AI/DTN services, computation, communication, security, and future network capabilities.
- Pages 27-31: References and extended comparison material.
- Page 32: Author bios.

Important visuals:
- Wireless technology evolution tables.
- AI-enabled DTN in 6G illustration.
- Survey structure.
- Fundamental services of AI-enabled DTN.
- Large comparison tables.

Relation to our project:
Use this for the literature-review introduction and 6G motivation. It supports why AI, digital twins, edge/cloud, slicing, and autonomous management are converging.

Project mapping:
- Layer: Cross-domain RAN, transport, core, edge, services.
- Twin object: End-to-end network digital twin.
- AI function: Prediction, optimization, anomaly detection, resource allocation.
- Self-healing relevance: Strategic basis for AI-driven closed loops.

Limitations:
Broad survey, not O-RAN-specific. Use as background, not as the main architecture reference.
""",
    "P_IEEE_2024_Digital_Twin_Driven_End_to_End_Network_Slicing_Toward_6G_REPORT.txt": """
Paper: Digital-Twin-Driven End-to-End Network Slicing Toward 6G
Publication/source: IEEE Internet Computing, 2024
Pages visually reviewed: 9
Visual assets: _visual_review/P_IEEE_2024_Digital_Twin_Driven_End_to_End_Network_Slicing_Toward_6G/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This paper proposes a digital twin framework for end-to-end network slicing in 6G. It is highly relevant to monetizable SLA assurance.

Page-wise visual review:
- Page 1: Title, abstract, and slicing/twin motivation.
- Page 2: Ecosystem figure for interconnected digital twins.
- Pages 3-4: Core proposed DT framework for E2E network slicing using AI.
- Pages 5-6: What-if simulation and slice planning discussion.
- Page 7: Training loss and latency prediction/regression plots.
- Page 8: Discussion and future directions.
- Page 9: References/closing page.

Important visuals:
- Intelligent interconnected ecosystem of digital twins.
- Proposed DT framework enabling E2E slicing.
- Training loss plot.
- True vs predicted latency regression plot.

Relation to our project:
This supports a slice/SLA twin that maps RAN, transport, core, and service failures to customer/business impact. It is important for monetizable telecom NOC dashboards.

Project mapping:
- Layer: Cross-domain slices across RAN/transport/core/services.
- Twin object: Slice/SLA twin.
- AI function: Latency prediction and what-if simulation.
- Self-healing relevance: Predict SLA breach, reroute/reallocate/scale before violation.

Limitations:
Not O-RAN-specific; pair with O-RAN standards and RIC/xApp papers.
""",
    "P_IEEE_2025_Anomaly_Detection_for_xApp_and_E2_Interface_Threats_in_ORAN_Near_RT_RIC_REPORT.txt": """
Paper: Anomaly Detection for Mitigating xApp and E2 Interface Threats in O-RAN Near-RT RIC
Publication/source: IEEE, 2025
Pages visually reviewed: 13
Visual assets: _visual_review/P_IEEE_2025_Anomaly_Detection_for_xApp_and_E2_Interface_Threats_in_ORAN_Near_RT_RIC/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This paper detects threats involving xApps and the E2 interface in the Near-RT RIC. It is one of the most directly relevant papers for securing AI control in O-RAN.

Page-wise visual review:
- Pages 1-2: Abstract, introduction, and O-RAN/Near-RT RIC background.
- Page 3: O-RAN architecture with anomaly traffic detector framework.
- Pages 4-5: Threat model, E2 communication process, and WG11 attack mapping table.
- Pages 6-7: Detector framework and detection logic/tree.
- Pages 8-9: Methodology and experimental design.
- Pages 10-11: Evaluation anomaly plots.
- Pages 12-13: Discussion, conclusion, references, author bios.

Important visuals:
- O-RAN architecture with anomaly detector.
- E2 communication process between xApp and E2 node.
- Attack mapping table.
- Detection structure/tree.
- Experimental anomaly plots.

Relation to our project:
This should guide the RIC security monitoring subsystem. The twin should model E2 associations, xApp commands, telemetry trust, and abnormal control behavior.

Project mapping:
- Layer: Near-RT RIC, E2 interface, O-CU/O-DU E2 nodes.
- Twin object: E2 control-plane twin and xApp behavior twin.
- AI function: xApp/E2 anomaly detection.
- Self-healing relevance: Quarantine malicious xApp, block E2 control, rollback policy, raise NOC incident.

Limitations:
Focused on RIC/E2, not full transport/core. Needs integration with adversarial ML and policy governance.
""",
    "P_IEEE_2025_COMIX_Generalized_Conflict_Management_in_ORAN_xApps_REPORT.txt": """
Paper: COMIX: Generalized Conflict Management in O-RAN xApps - Architecture, Workflow, and a Power Control Case
Publication/source: IEEE Access, 2025
Pages visually reviewed: 17
Visual assets: _visual_review/P_IEEE_2025_COMIX_Generalized_Conflict_Management_in_ORAN_xApps/ALL_PAGES_CONTACT_SHEET.png

Core idea:
COMIX proposes a generalized architecture and workflow for detecting and managing conflicts between O-RAN xApps.

Page-wise visual review:
- Pages 1-2: Abstract/introduction and conflict category figure.
- Pages 3-5: General O-RAN architecture and generalized conflict detector.
- Pages 6-10: Mathematical notation, workflow, and algorithmic details.
- Pages 11-14: Evaluation and power-control case graphs.
- Pages 15-17: Discussion, conclusion, references, author bios.

Important visuals:
- Conflict categories in O-RAN.
- General O-RAN architecture for COMIX.
- Generalized direct/indirect conflict detector.
- Evaluation graphs for conflict scenarios.

Relation to our project:
This is a core guardrail paper. A self-healing controller must detect contradictory xApp actions before they hit the live network.

Project mapping:
- Layer: Near-RT RIC/xApp orchestration.
- Twin object: Control action twin and conflict-risk twin.
- AI function: Conflict detection/resolution.
- Self-healing relevance: Prevent unsafe or contradictory automated healing.

Limitations:
Needs extension to rApps, dApps, SMO policies, transport/core automation, and operator approval workflows.
""",
    "P_Springer_2025_CERBERUS_Secure_Automated_Multi_Operator_Management_in_B5G_ZSM_REPORT.txt": """
Paper: CERBERUS: Towards Secure and Automated Multi-Operator Management in B5G Through a Dynamic Policy-Based ZSM Framework
Publication/source: Journal of Network and Systems Management, Springer, 2025
Pages visually reviewed: 34
Visual assets: _visual_review/P_Springer_2025_CERBERUS_Secure_Automated_Multi_Operator_Management_in_B5G_ZSM/ALL_PAGES_CONTACT_SHEET.png

Core idea:
CERBERUS is a secure automated multi-operator management framework based on dynamic policy and ZSM concepts. It is valuable for secure closed-loop management and national-scale NOC governance.

Page-wise visual review:
- Pages 1-5: Abstract, introduction, and secure automated management context.
- Page 6: CERBERUS framework architecture overview.
- Pages 7-19: Policy logic, orchestration, and security-management framework.
- Page 20: Step-by-step orchestration workflow in a multi-operator environment.
- Pages 21-22: Use case and KPI table.
- Pages 23-30: Evaluation figures for deployment time and detection time.
- Pages 31-34: Conclusion, references, author information.

Important visuals:
- CERBERUS architecture.
- Multi-operator orchestration workflow.
- KPI table.
- MTTD/deployment timing graphs.

Relation to our project:
Use this for the SMO/NOC/ZSM governance layer. It supports policy-based, auditable, secure automation rather than uncontrolled AI action.

Project mapping:
- Layer: SMO, OSS/NOC, ZSM orchestration.
- Twin object: Policy twin, security twin, multi-domain operations twin.
- AI function: Security event detection and policy-triggered response.
- Self-healing relevance: Dynamic policy-based mitigation at management/orchestration layer.

Limitations:
Less O-RAN-specific; adapt concepts to A1/E2/O1/O2 and telecom operator workflows.
""",
    "P_Springer_2025_Time_Sensitive_Networking_Digital_Twin_for_STRIDE_Based_Security_Testing_REPORT.txt": """
Paper: Time-Sensitive Networking Digital Twin for STRIDE-Based Security Testing
Publication/source: EURASIP Journal on Information Security, Springer, 2025
Pages visually reviewed: 17
Visual assets: _visual_review/P_Springer_2025_Time_Sensitive_Networking_Digital_Twin_for_STRIDE_Based_Security_Testing/ALL_PAGES_CONTACT_SHEET.png

Core idea:
This paper builds a TSN digital twin for security testing using STRIDE. It is useful for O-RAN fronthaul/midhaul timing, deterministic transport, PTP, and security simulation.

Page-wise visual review:
- Pages 1-2: Abstract/introduction and TSN twin motivation.
- Pages 3-4: TSN protocol classification and STRIDE threat mapping tables.
- Pages 5-7: Digital twin architecture, PTP clock hierarchy, and transport timing visuals.
- Pages 8-10: Implementation and attack/experiment setup.
- Pages 11-12: Test workflow diagrams.
- Pages 13-14: Measurement graphs and STRIDE testing results.
- Pages 15-17: Discussion, limitations, references.

Important visuals:
- TSN protocol classification table.
- STRIDE threat mapping table.
- TSN Digital Twin architecture.
- PTP Grandmaster/Boundary/Slave clock figure.
- Experiment graphs.

Relation to our project:
O-RAN fronthaul and transport depend on strict latency, jitter, and timing. This paper supports a timing/security twin that can test PTP/TSN attacks and misconfigurations before they damage RAN behavior.

Project mapping:
- Layer: Open fronthaul, midhaul, transport, timing/synchronization.
- Twin object: TSN/PTP/timing twin.
- AI function: Timing anomaly detection and threat simulation.
- Self-healing relevance: Switch timing source, isolate faulty timing domain, trigger PTP/SyncE remediation.

Limitations:
Not O-RAN-specific, but highly transferable to fronthaul/transport timing security.
""",
}

for name, body in reports.items():
    (root / name).write_text(dedent(body).strip() + "\n", encoding="utf-8")

combined = """
Priority Literature Visual Review Report
Date: 2026-06-05
Folder reviewed: literature-survey/papers/priority

Method used:
- Every priority PDF was rendered page-wise into images using PyMuPDF.
- One all-pages contact sheet per PDF was generated under _visual_review/<paper>/ALL_PAGES_CONTACT_SHEET.png.
- Additional page-group visual sheets and page_text.txt files were generated for deeper checking.
- Reports were written after visual inspection of the rendered sheets plus page-wise text/caption extraction.

Priority reading order:
1. P_Elsevier_2025_ORAN_xApps_Survey_and_Research_Challenges.pdf
2. P_IEEE_2025_Anomaly_Detection_for_xApp_and_E2_Interface_Threats_in_ORAN_Near_RT_RIC.pdf
3. P_IEEE_2025_COMIX_Generalized_Conflict_Management_in_ORAN_xApps.pdf
4. P_Elsevier_2026_xApp_Distillation_AI_Based_Conflict_Mitigation_in_B5G_ORAN.pdf
5. P_Elsevier_2024_Drift_Handling_Framework_for_Open_Radio_Access_Networks.pdf
6. P_Elsevier_2024_Adversarial_Machine_Learning_Threat_Analysis_and_Remediation_in_ORAN.pdf
7. P_IEEE_2024_Digital_Twin_Driven_End_to_End_Network_Slicing_Toward_6G.pdf
8. P_Springer_2025_Time_Sensitive_Networking_Digital_Twin_for_STRIDE_Based_Security_Testing.pdf
9. P_Springer_2025_CERBERUS_Secure_Automated_Multi_Operator_Management_in_B5G_ZSM.pdf
10. P_IEEE_2024_AI_Enabled_Digital_Twin_Network_in_6G_Survey.pdf
11. P_ACM_2024_SpotLight_Open_RAN_System_for_Dynamic_Spectrum_Access_and_Anomaly_Detection.pdf

Cross-paper conclusions:
- Near-RT RIC/xApps are the most important near-real-time automation point for RAN self-healing.
- Non-RT RIC/SMO should own slower policy, model lifecycle, training, enrichment, governance, and orchestration.
- Digital Twin should validate proposed actions before live actuation.
- AI anomaly detection is not sufficient alone; it needs model drift handling, adversarial ML defense, conflict management, and policy rollback.
- Monetizable value comes from SLA/slice assurance, predictive maintenance, secure automation, and NOC-grade RCA dashboards.

Recommended project modules:
1. O-RAN topology and RIC application twin.
2. E2/xApp anomaly detector.
3. xApp conflict manager.
4. xApp policy distillation/arbitration layer.
5. Model drift monitor and retraining trigger.
6. Adversarial ML/security twin.
7. Slice/SLA digital twin.
8. TSN/PTP/fronthaul timing security twin.
9. ZSM/SMO policy orchestration layer.
10. NOC dashboard linking failures to service impact.

Generated artifacts:
- One *_REPORT.txt file per priority PDF.
- Visual artifacts under _visual_review.
"""
(root / "PRIORITY_REVIEW_REPORT.txt").write_text(dedent(combined).strip() + "\n", encoding="utf-8")

print(f"Wrote {len(reports)} per-PDF reports plus PRIORITY_REVIEW_REPORT.txt")
