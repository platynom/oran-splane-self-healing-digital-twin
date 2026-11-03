# External citation verification — November 2026

This audit covers every external source family cited on v8 slides 4–12, 16, 20, 21, 24–27 and 40, plus every externally sourced claim in `03_RECOVERY_LOOP_S-PLANE/STANDARDS_EVIDENCE.md`. Repeated references on one slide are combined only when they support the same claim. Page numbers are PDF pages unless an RFC page or HTML/man-page section is stated. Quotes are kept below about 40 words.

Verdicts mean: **CONFIRMED** = the stored source directly supports the scoped claim; **WRONG_CLAUSE** = the cited source exists but the named clause does not say what the artefact claims; **NOT_SUPPORTED** = the source is related but does not establish the stated claim or exact construction; **NOT_ACCESSIBLE** = the cited text was not legally available in the stored corpus.

## Slides 4–12

| ID | Slide/doc | Claim | Source | Clause | Supporting text (short extract) | Page | Verdict |
|---|---|---|---|---|---|---:|---|
| S04-01 | v8 slide 4 | Open Fronthaul lies between O-DU and O-RU and includes C/U/S planes. | ETSI TS 103 982 V8.0.0 | 6.4.7 | “The Open FH Interface is between O-DU and O-RU functions … [and] includes the CUS (Control User Synchronization) Plane.” | 21 | CONFIRMED |
| S04-02 | v8 slide 4 | The O-RAN CUS specification defines the three fronthaul planes. | ETSI TS 103 859 V12.0.1 | 1 | “specifies the control plane, user plane and synchronization plane protocols used over the fronthaul interface linking the O-DU … with the O-RU” | 19 | CONFIRMED |
| S04-03 | v8 slide 4 | NG-RAN architecture contains gNBs connected to 5GC. | ETSI TS 138 401 V18.1.0 | 6.1.1 | “The NG-RAN consists of a set of gNBs connected to the 5GC through the NG interface.” | 16 | CONFIRMED |
| S05-01 | v8 slide 5 | O-RU hosts Low-PHY/RF and terminates Open Fronthaul. | ETSI TS 103 982 V8.0.0 | 3.1; 6.3.6 | “A logical node hosting Low-PHY layer and RF processing” and “The O-RU terminates the Open Fronthaul interface.” | 9, 19 | CONFIRMED |
| S05-02 | v8 slide 5 | NG-RAN logical architecture is grounded in 3GPP TS 38.401. | ETSI TS 138 401 V18.1.0 | 1; 6.1.1 | “describes the overall architecture of the NG-RAN” | 8 | CONFIRMED |
| S05-03 | v8 slide 5 | The antenna-side cell phase requirement is better than 3 microseconds. | Ruffini, *Sync for 5G* | slide 6 | “cell phase synchronization accuracy measured at BS antenna connectors shall be better than 3 µs” | 7 | CONFIRMED |
| S05-04 | v8 slide 5 | MIMO/carrier-aggregation TAE values are antenna/radiated requirements. | 3GPP TS 38.104 V19.2.0 | 9.6.3.2 | “For MIMO transmission … OTA TAE shall not exceed 65 ns. For intra-band contiguous carrier aggregation … 260 ns.” | 245 | CONFIRMED |
| S06-01 | v8 slide 6 | Definitions of LLS-C1 through LLS-C4. | Armstrong, *O-RAN Fundamentals* | “Timing Configurations” | “Configuration LLS-C1: the O-DU is part of the synchronization chain …” (the same page lists C2, C3 and C4) | 15 | CONFIRMED |
| S06-02 | v8 slide 6 | LLS-C1 exposure is specifically T-FRHAUL-01 because a compromised O-DU/link controls O-RU time. | ETSI TR 104 106 V3.0.0 | T-FRHAUL-01 | “An attacker penetrates O-DU and beyond through O-RU or the Fronthaul interface.” | 33 | WRONG_CLAUSE |
| S06-03 | v8 slide 6 | A switched fronthaul gives devices on the path an injection/interception position. | TIMESAFE | 4; 5.1 | “an attacker compromises a device on the network” and the production fronthaul uses a switch to distribute PTP/SyncE | 2, 11 | CONFIRMED |
| S06-04 | v8 slide 6 | TIMESAFE's production setup used LLS-C3. | TIMESAFE | 5.1 | “distributing PTP and SyncE synchronization to the DU and RU with an O-RAN LLS-C3 configuration.” | 11 | CONFIRMED |
| S06-05 | v8 slide 6 | LLS-C4 removes PTP-path exposure but leaves GNSS jamming/spoofing exposure. | RFC 7384 | 3.2.10 | “Grandmasters receive their time from an external accurate time source, such as … a GPS clock” | RFC p.11 | CONFIRMED |
| S06-06 | v8 slide 6 | GNSS receivers used for RAN timing can be jammed. | BSI 5G RAN Risk Analysis | 5.1.7 | “auxiliary GNSS receivers deployed in a network can be targets of jamming attacks.” | 26 | CONFIRMED |
| S07-01 | v8 slide 7 | O-RAN relative TAE can be 130 ns, expressed as ±65 ns from one DU. | Armstrong, *O-RAN Fundamentals* | timing requirements | “TAE down to 130 ns between clusters of RUs (i.e. ±65 ns from same DU)” | 12 | CONFIRMED |
| S07-02 | v8 slide 7 | Point C network limit is 1,100 ns and point E total is 1,500 ns. | ITU-T G.8271.1 (2022) | 7.3; Appendix V | “max\|TEL\| ≤ 1 100 ns” and “Total time error at reference point E … 1 500 ns” | 11, 38 | CONFIRMED |
| S07-03 | v8 slide 7 | One published attack made the RU crash about two seconds after onset and require manual reboot. | TIMESAFE | 6.1 | “Approximately 2 seconds after the attack begins, the RU crashes” and “the RU required a manual reboot” | 12–13 | CONFIRMED |
| S08-01 | v8 slide 8 | IEEE 1588-2019 defines the cited clock states and timePropertiesDS fields. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S08-02 | v8 slide 8 | G.8275.1 uses clockClass 6 for locked and 7 for holdover within specification. | ITU-T G.8275.1 (2026) | Appendix VII | “locked to GNSS, it outputs clockClass 6” and “in holdover, but within holdover specification (clockClass 7).” | 69 | CONFIRMED |
| S08-03 | v8 slide 8 | O-RAN threat model contains malicious timing-source threats. | ETSI TR 104 106 V3.0.0 | 7.4.1.2 | “A Rogue PTP Instance wanting to be a Grand Master” | 34 | CONFIRMED |
| S09-01 | v8 slide 9 | Six named threat-agent categories. | ETSI TR 104 106 V3.0.0 | 7.2 | “Insiders … Nation States … Cyber criminals … Hacktivists … Cyber terrorists … Script Kiddies” | 28 | CONFIRMED |
| S09-02 | v8 slide 9 | Internal/external and MITM/injector attacker classes. | RFC 7384 | 3.1.1–3.1.2 | “Internal attackers either have access to a trusted segment … or possess … keys” and “A traffic injector is not located in an MITM position.” | RFC p.8 | CONFIRMED |
| S09-03 | v8 slide 9 | T-FRHAUL-02 is unauthorized physical-interface access. | ETSI TR 104 106 V3.0.0 | T-FRHAUL-02 | “Unauthorized access to Open Front Haul Ethernet L1 physical layer interface(s)” | 33 | CONFIRMED |
| S09-04 | v8 slide 9 | TIMESAFE directly establishes all four listed real-world access paths, including supply-chain backdoors. | TIMESAFE | 4 | The paper models a compromised fronthaul device and discusses softwarization/multi-vendor exposure, but does not enumerate the slide's full four-item list. | 9–10 | NOT_SUPPORTED |
| S10-01 | v8 slide 10 | RFC attacker-position mapping: injector vs MITM. | RFC 7384 | 3.1.2 | “MITM attackers are located in a position that allows interception” and “A traffic injector … can attack by generating protocol packets.” | RFC p.8 | CONFIRMED |
| S11-01 | v8 slide 11 | A1/A8 rogue-master provenance. | RFC 7384 | 3.2.4 | “an attacker causes other nodes in the network to believe it is a legitimate master” | RFC p.9 | CONFIRMED |
| S11-02 | v8 slide 11 | A2/C3 spoofing provenance. | RFC 7384 | 3.2.2 | “an injector masquerades as a legitimate node … by generating and transmitting protocol packets” | RFC p.9 | CONFIRMED |
| S11-03 | v8 slide 11 | A3 replay provenance. | RFC 7384 | 3.2.3 | “an attacker records protocol packets and replays them at a later time without any modification.” | RFC p.9 | CONFIRMED |
| S11-04 | v8 slide 11 | A5 time-protocol flooding provenance. | RFC 7384 | 3.2.9 | “sending an excessive number of time protocol packets, thus degrading the victim's performance.” | RFC p.11 | CONFIRMED |
| S11-05 | v8 slide 11 | C1 interception/removal provenance. | RFC 7384 | 3.2.5 | “an MITM attacker intercepts and drops protocol packets” | RFC p.10 | CONFIRMED |
| S11-06 | v8 slide 11 | O-RAN T-SPLANE-01…04 map to DoS, impersonation, rogue PTP and selective removal. | ETSI TR 104 106 V3.0.0 | 7.4.1.2 | “DoS attack against a Master clock”; “Impersonation … fake ANNOUNCE”; “Rogue PTP Instance”; “Selective interception and removal” | 34–35 | CONFIRMED |
| S11-07 | v8 slide 11 | Published O-RAN tests include rogue instance, DoS, interception and unexpected-input tests. | ETSI TS 104 105 V7.0.0 | 11.1.5; 24.2.1 | “Rogue PTP Instance”; “Selective Interception and Removal”; “S-Plane PTP DoS Attack”; “S-Plane PTP Unexpected Input” | 121, 123, 224–225 | CONFIRMED |
| S11-08 | v8 slide 11 | TIMESAFE implements spoofing and replay. | TIMESAFE | 4.1 | “we focus on two specific attacks … Spoofing Attack and Replay Attack.” | 9 | CONFIRMED |
| S11-09 | v8 slide 11 | C3 exact field construction comes from IEEE 1588 §8.2.4. | IEEE Std 1588-2019 | 8.2.4 | — | — | NOT_ACCESSIBLE |
| S11-10 | v8 slide 11 | C2's exact three malformed variants reproduce ETSI test 24.2.1.2. | ETSI TS 104 105 V7.0.0 | 24.2.1.2 | The standard instead says to replay captured legitimate PTP while mutating content for at least 250,000 iterations. | 225 | NOT_SUPPORTED |
| S12-01 | v8 slide 12 | RFC impact classes include false time, accuracy degradation and DoS. | RFC 7384 | Table 1 | Table columns are “False Time”, “Accuracy Degrad.” and “DoS”. | RFC p.12 | CONFIRMED |
| S12-02 | v8 slide 12 | T-SPLANE impact includes cell-wide loss and inaccurate time. | ETSI TR 104 106 V3.0.0 | T-SPLANE-01…04 | “affect all the RUs … potentially bringing down the cell” | 34 | CONFIRMED |
| S12-03 | v8 slide 12 | Published service impact: crash, cell drop and manual restart. | TIMESAFE | 6.1 | “causing the 5G cell to drop” and “the RU required a manual reboot” | 13 | CONFIRMED |
| S12-04 | v8 slide 12 | TDD cell phase synchronization must be better than 3 microseconds. | Ruffini, *Sync for 5G* | slide 6 | “cell phase synchronization accuracy … shall be better than 3 µs” | 7 | CONFIRMED |
| S12-05 | v8 slide 12 | TAE limits of 65 ns, 260 ns and 3 microseconds. | 3GPP TS 38.104 V19.2.0 | 9.6.3.2 | “OTA TAE shall not exceed 65 ns … 260 ns … 3 µs.” | 245 | CONFIRMED |

## Slides 16, 20, 21 and 24–27

| ID | Slide/doc | Claim | Source | Clause | Supporting text (short extract) | Page | Verdict |
|---|---|---|---|---|---|---:|---|
| S16-01 | v8 slide 16 | IEEE 1588 provides legal PTP fields, data sets and leap handling. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S16-02 | v8 slide 16 | O-RAN CUS defines the O-DU/O-RU fronthaul synchronization boundary. | ETSI TS 103 859 V12.0.1 | 1 | “Synchronization Plane … traffic between the O-RU or O-DU and a synchronization controller” | 23 | CONFIRMED |
| S16-03 | v8 slide 16 | WG11 supplies the cited timing-threat identifiers. | ETSI TR 104 106 V3.0.0 | 7.4.1.2 | “T-SPLANE-01” through “T-SPLANE-04” are listed with threat titles and descriptions. | 34–35 | CONFIRMED |
| S16-04 | v8 slide 16 | G.8275.1 fixes profile domain/rates/transport and alternate BTCA. | ITU-T G.8275.1 (2026) | 6.1; 6.2.5; 6.2.6; 6.3 | “default PTP domain number is 24”; “Sync … 16 packets-per-second”; “Announce … 8”; “uses an Alternate BTCA” | 14, 18, 20 | CONFIRMED |
| S16-05 | v8 slide 16 | G.8273.2 supplies telecom boundary-clock performance limits. | ITU-T G.8273.2 (2023) | 7.3 | The recommendation specifies time-error requirements for T-GM and T-BC classes. | 18–33 | CONFIRMED |
| S16-06 | v8 slide 16 | G.8262 is frequency-synchronization context, not implemented. | ITU-T G.8262 (2024) | 1 | The recommendation specifies timing characteristics of synchronous equipment slave clocks. | 1 | CONFIRMED |
| S20-01 | v8 slide 20 | IEEE 1588 defines the message/data-set KPIs. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S20-02 | v8 slide 20 | `pmc -d` sets the management-message domain; default is zero. | linuxptp 4.0 `pmc.8` | `-d` option | “Specify the domain number in sent messages. The default is 0.” | man page | CONFIRMED |
| S20-03 | v8 slide 20 | O-RU is the Low-PHY/Open-Fronthaul termination point. | ETSI TS 103 982 V8.0.0 | 6.3.6 | “The O-RU terminates the Open Fronthaul interface … as well as Low-PHY functions.” | 19 | CONFIRMED |
| S21-01 | v8 slide 21 | IEEE 1588 provides the cited field-legality basis. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S21-02 | v8 slide 21 | G.8275.1 profile constants include domain 24–43, supported multicast addresses and rates. | ITU-T G.8275.1 (2026) | 6.1; 6.2.5–6.2.6 | “range … {24–43}”; supported addresses include `01-1B-19-00-00-00`; nominal Sync 16/s and Announce 8/s. | 14, 16, 18 | CONFIRMED |
| S24-01 | v8 slide 24 | Exact IEEE message formats, sequence and time-properties clauses. | IEEE Std 1588-2019 | 8.2.4; 9.4 | — | — | NOT_ACCESSIBLE |
| S24-02 | v8 slide 24 | ETSI defines rogue, DoS, selective-removal and unexpected-input test families. | ETSI TS 104 105 V7.0.0 | 11.1.5; 24.2.1 | The four test titles appear in the specified clauses. | 117–125, 224–225 | CONFIRMED |
| S25-01 | v8 slide 25 | Announce/Sync/Follow_Up fields and sequence continuity follow IEEE 1588. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S25-02 | v8 slide 25 | Alternate-BTCA and cadence claims. | ITU-T G.8275.1 (2026) | 6.2.5; 6.3 | “nominal rate: 16 packets-per-second”; “Announce … 8 packets per second”; “uses an Alternate BTCA” | 18, 20 | CONFIRMED |
| S25-03 | v8 slide 25 | DoS/rogue identifiers match WG11 threat labels. | ETSI TR 104 106 V3.0.0 | T-SPLANE-01…03 | The stored threat titles identify DoS, impersonation and rogue PTP instance. | 34 | CONFIRMED |
| S26-01 | v8 slide 26 | Test identifiers 11.1.5.3.1 and 24.2.1.2 exist and concern removal and unexpected input. | ETSI TS 104 105 V7.0.0 | named clauses | “Selective Interception and Removal of PTP Timing Packets”; “S-Plane PTP Unexpected Input” | 123, 225 | CONFIRMED |
| S26-02 | v8 slide 26 | Exact IEEE stepsRemoved/timeProperties/leap semantics. | IEEE Std 1588-2019 | 8.2.4; 9.4 | — | — | NOT_ACCESSIBLE |
| S26-03 | v8 slide 26 | C1 and A8 scenario labels align with T-SPLANE-04/-03. | ETSI TR 104 106 V3.0.0 | T-SPLANE-03/-04 | “A Rogue PTP Instance” and “Selective interception and removal of PTP timing packets” | 34–35 | CONFIRMED |
| S26-04 | v8 slide 26 | Whole-second forged values would necessarily shift O-RU phase by one second in this testbed. | IEEE / project construction | cited generally | `free_running 1` means the campaign did not steer clocks; the asserted service shift was not measured. | — | NOT_SUPPORTED |
| S27-01 | v8 slide 27 | G.8275.1 clock-class ladder and profile behavior. | ITU-T G.8275.1 (2026) | 6.4; Appendix VII | “clockClass 6” locked and “clockClass 7” holdover within specification. | 21, 69 | CONFIRMED |
| S27-02 | v8 slide 27 | Exact IEEE BMCA re-election semantics. | IEEE Std 1588-2019 | cited generally | — | — | NOT_ACCESSIBLE |
| S27-03 | v8 slide 27 | G.8261 is the proper PDV context for B3. | ITU-T G.8261 (2019) | 6.2 | The recommendation defines packet-delay variation and network limits for packet timing. | 9–20 | CONFIRMED |

## Slide 40 and recovery-loop standards note

| ID | Slide/doc | Claim | Source | Clause | Supporting text (short extract) | Page | Verdict |
|---|---|---|---|---|---|---:|---|
| S40-01 | v8 slide 40 | Multiple industry-specific PTP profiles exist. | IEEE SA public PTP profile index | profile list | The page lists telecom, power, broadcast, AES67, 802.1AS, automotive and enterprise profiles. | HTML | CONFIRMED |
| S40-02 | v8 slide 40 | RFC 7384 is not O-RAN-specific and focuses on PTP/NTP. | RFC 7384 | 1 | “This document focuses on the two most common time protocols, the Network Time Protocol (NTP) and the Precision Time Protocol (PTP).” | RFC p.3 | CONFIRMED |
| S40-03 | v8 slide 40 | G.8275.1 constants shown on the slide apply to this profile. | ITU-T G.8275.1 (2026) | 6.1–6.3 | Domain, rates, multicast addressing, priority1 and Alternate BTCA are explicitly specified by the profile. | 14–22 | CONFIRMED |
| D01 | `STANDARDS_EVIDENCE.md` §1 | Slaves authenticate and authorize masters. | RFC 7384 | 5.1.1 | “MUST allow slaves to verify that the authenticated master is authorized to be a master.” | RFC p.15 | CONFIRMED |
| D02 | same | Secure mode discards unsecured-clock packets. | RFC 7384 | 5.10.1 | “every protocol packet received from an unsecured clock MUST be discarded.” | RFC p.28 | CONFIRMED |
| D03 | same | Time protocol security should mitigate DoS. | RFC 7384 | 5.4 | “The security mechanism SHOULD include measures to mitigate DoS attacks against the time protocol.” | RFC p.20 | CONFIRMED |
| D04 | same | Acceptable-master table and master-only-port operational practice. | Arnold & Frost, WSTS 2016 | cited generally | — | — | NOT_ACCESSIBLE |
| D05 | same | The cited G.8275.1 attribute is named `notSlave`. | Secondary Rodrigues slides | cited generally | Current G.8275.1 uses `timeTransmitterOnly` / `notTimeTransmitter`; the cited secondary text is not stored. | — | WRONG_CLAUSE |
| D06 | same | NVIDIA documentation says acceptable-master tables prevent a rogue grandmaster. | NVIDIA Cumulus docs | cited generally | — | — | NOT_ACCESSIBLE |
| D07 | `STANDARDS_EVIDENCE.md` §2 | Protection from accuracy-degrading MITM attacks is required. | RFC 7384 | 5.9 | “MUST include means to protect the protocol from MITM attacks that degrade the clock accuracy.” | RFC p.27 | CONFIRMED |
| D08 | same | Redundant masters or paths are common mitigation practice. | RFC 7384 | 5.9 | “common practices … use redundant masters … or redundant paths between the master and slave” | RFC p.27 | CONFIRMED |
| D09 | same | Prong C includes redundancy. | TIMESAFE | 10 | “Network redundancy, as suggested in Prong C, enhances protection and resilience … through redundant paths and clocks.” | 22 | CONFIRMED |
| D10 | same | The four-prong list is quoted from an O'Donoghue workshop source. | O'Donoghue, 2016 | cited generally | — | — | NOT_ACCESSIBLE |
| D11 | `STANDARDS_EVIDENCE.md` §3 | Ambiguity should raise an alarm and enter holdover. | Arnold & Frost, WSTS 2016 | cited generally | — | — | NOT_ACCESSIBLE |
| D12 | same | G.8275.1 class 6/7/135/165 meanings. | ITU-T G.8275.1 (2026) | 6.4; Appendix VII | “clockClass 6”; “clockClass 7”; class 135 is within holdover specification and 165 is out of specification. | 21, 69, 72 | CONFIRMED |
| D13 | same | Point-E budget allocates 250 ns to rearrangement/short holdover. | ITU-T G.8271.1 (2022) | Appendix V, Table V.1 | “Rearrangements and short-term holdover in the end application … 250 ns” | 38 | CONFIRMED |
| D14 | `STANDARDS_EVIDENCE.md` §4 | Monitoring is Prong D and can detect attacks. | TIMESAFE | 7; 10 | “we propose a monitoring system (Prong D)” | 15 | CONFIRMED |
| D15 | same | `pmc` must be sent in the configured domain. | linuxptp 4.0 `pmc.8` | `-d` | “Specify the domain number in sent messages. The default is 0.” | man page | CONFIRMED |
| D16 | `STANDARDS_EVIDENCE.md` §6 | ETSI 11.1.5.2.2 and 11.1.5.3.1 were not verified. | ETSI TS 104 105 V7.0.0 | named clauses | Both clauses and their procedures are present in the stored PDF, so the old `NV` status is obsolete. | 121–124 | CONFIRMED |
| D17 | same | ETSI TS 104 104 clause 5.2.5.3 was not verified. | ETSI TS 104 104 V9.1.0 | 5.2.5.3 | The cited source was not downloaded in the permitted source set. | — | NOT_ACCESSIBLE |

## Errata for frozen artefacts

The deck itself remains unchanged.

1. **Slide 6 / LLS-C1:** `T-FRHAUL-01` is the wrong clause for “a compromised O-DU or link controls O-RU time.” That threat concerns penetration beyond the O-DU through the O-RU/fronthaul, not timing-source control. The exposure statement is reasonable threat analysis, but that identifier must be removed or replaced with a supported timing-threat citation.
2. **Slide 9 / access paths:** TIMESAFE does not directly enumerate all four bullets shown. Treat supply-chain backdoors and the full access-path list as threat-model synthesis, not as a quotation from TIMESAFE §4.
3. **Slide 11 / C2:** ETSI 24.2.1.2 supports an unexpected-input/fuzzing category but not the exact `versionPTP 3 / reserved type / short length` construction. Label those values as this project's implementation choices.
4. **Slides 11, 16, 20, 21, 24–27:** IEEE 1588-2019 clause-level claims could not be independently checked without licensed access. They remain `NOT_ACCESSIBLE`, not disproved.
5. **Slide 26 / C3:** a one-second service shift was not measured because the campaign used `free_running 1`. The measured result is re-parenting/protocol state; the service consequence is only a reference/engineering implication.
6. **`STANDARDS_EVIDENCE.md`:** its “paywalled ITU” and several `NV` statements are superseded for G.8275.1/G.8273.2 and ETSI TS 104 105 by the freely stored copies in this branch. Its `notSlave` wording also reflects an older/secondary terminology path and should not be used as a current clause citation.
