# Standards and literature behind each element of the recovery loop

**Verification levels**

| Level | Meaning |
|---|---|
| **V1** | Quote checked directly against the source in this session (5 Oct 2026) |
| **V2** | Quote returned by a separate research pass with its URL; not re-read a second time |
| **NV** | Not verifiable from a free source; stated as a limitation |

Paywalled texts (IEEE 1588-2019, ITU-T G.8275.1/G.8273.2) were **not** read directly.

## 1. Isolate the source of an unauthorised master or forged traffic

| Claim | Quote | Source | Level |
|---|---|---|---|
| Slaves must accept only authorised masters | "The authentication mechanism MUST allow slaves to verify that the authenticated master is authorized to be a master." | IETF RFC 7384 §5.1.1 — https://www.rfc-editor.org/rfc/rfc7384.html | V1 |
| Packets from unsecured clocks are discarded in secure mode | "The security mechanism MUST support a secure mode, where only secured clocks are permitted to take part in the time protocol. In this mode every protocol packet received from an unsecured clock MUST be discarded." | RFC 7384 §5.10.1 | V1 |
| DoS mitigation | "The security mechanism SHOULD include measures to mitigate DoS attacks against the time protocol." | RFC 7384 §5.4 | V1 |
| Operational practice: acceptable master table, master-only ports | "Acceptable Master Table"; "BCs would not set port to slave state with rogue master input"; "Master_only ports" | D. Arnold, T. Frost, *Security Threats and Mitigation in PTP Networks*, WSTS 2016 — https://sandbox.wsts.atis.org/wp-content/uploads/2018/11/2-06_-Security_Threats_and_Mitigations.pdf | V1 |
| G.8275.1 per-port role restriction | "Per-port Boolean attribute notSlave. notSlave is TRUE -> the port is never placed in the SLAVE state" | Rodrigues, *IEEE 1588 profiles at ITU-T*, NIST WSTS — https://tf.nist.gov/seminars/WSTS/PDFs/3-4-IDT_Rodrigues-IEEE%201588-profiles%20at%20ITU-T%20.pdf | V2 |
| Vendor practice | "The acceptable master table option is a security feature that prevents a rogue player from pretending to be the Grandmaster to take over the PTP network." | NVIDIA Cumulus Linux 4.4 PTP docs | V2 |

**How the loop applies it.** linuxptp 4.0 has no acceptable-master table, and its Authentication TLV support arrived only in linuxptp 4.3 (V2: `sad.c` absent at v4.0/v4.2, present at v4.3). So the loop enforces the provisioned port roles at the segment bridge instead. Once the frozen rule has returned ATTACK on 2 of the last 3 evaluations, an nftables bridge rule drops PTP (ethertype 0x88F7) entering on the offending port. This is the software stand-in for a switch-port PTP filter or ACL. It is **not** an implementation of IEEE 1588-2019 Annex P authentication.

## 2. Fail over to a redundant boundary clock when timing is removed

| Claim | Quote | Source | Level |
|---|---|---|---|
| Protection against interception/delay is required | "The security mechanism MUST include means to protect the protocol from MITM attacks that degrade the clock accuracy." | RFC 7384 §5.9 | V1 |
| Redundancy is the common practice | discussion of §5.9: common practices use redundant masters or redundant paths between master and slave; a source that disagrees is ignored | RFC 7384 §5.9 (summarised by the fetch tool; the exact sentence is in the V2 report: "Common practices for protection against MITM attacks use redundant masters (e.g., [NTPv4]) or redundant paths between the master and slave (e.g., [DelayAtt])") | V1 (requirement) / V2 (sentence) |
| IEEE 1588 security "Prong C" is architecture guidance including redundancy | "Prong C focuses on redundancy (e.g., multiple grandmasters, alternate paths) to mitigate attacks and enhance system resilience." | Groen et al., TIMESAFE, arXiv 2412.13049 §2.3 | V2 |
| The four prongs | "PTP Integrated Security Mechanisms (Prong A) • External Transport Security Mechanisms (Prong B) • Architecture Guidance (Prong C) • Monitoring and Management Guidance (Prong D)" | K. O'Donoghue, IEEE/NIST workshop 2016 — https://www.nist.gov/document/08odonoghueemergingsecurityoverviewpdf (pre-dates 1588-2019; Annex P text itself not read) | V2 |

**How the loop applies it.**
- A cold-standby boundary clock (`bcs`) is provisioned and cabled in every run.
- **Trigger:** no Announce arrives on the segment from any provisioned master port for longer than 2 s. The announceReceiptTimeout in this profile is 3 × 125 ms (the configured `announceReceiptTimeout 3` at `logAnnounceInterval -3`).
- **Action:** the loop starts the standby boundary clock daemon.
- **Why intent does not matter here:** this action is correct whether the loss comes from interception (C1) or from a failed BC.

## 3. Tolerate benign faults; raise an alarm when intent is unknown

| Claim | Quote | Source | Level |
|---|---|---|---|
| Ambiguity → alarm + holdover | "If still confused, raise alarm and go into holdover"; "Raise alarm and go into holdover!" | Arnold & Frost, WSTS 2016 | V1 |
| clockClass 6 = T-GM locked to PRTC; 7 = T-GM in holdover within spec; 135 = T-BC in holdover within spec; 140/150/160 = T-GM in holdover out of spec; 165 = T-BC in holdover out of spec; 248 = without time reference since start-up | Calnex *ITU-T G.8275.1 one-page summary* (table reproduced from G.8275.1) | V2 (table reformatted by the fetch tool) |
| Holdover in the end application is budgeted (250 ns of the 1.5 µs at point E) | G.8271.1 Appendix V example budget, via Calnex | V2 |

**How the loop applies it.**
- **BENIGN:** no action is taken.
- **UNKNOWN:** the loop logs an escalation (the alarm) and takes no automatic action.
- **Holdover is not entered by the loop.** linuxptp 4.0 offers no command to force holdover, and with `free_running 1` the clocks are never steered anyway. This is a stated limitation, not an implemented feature.

## 4. Monitoring as the trigger (Prong D) and the correct management query

| Claim | Quote | Source | Level |
|---|---|---|---|
| Monitoring PTP helps detect attacks | "Prong D emphasizes monitoring and management. Monitoring PTP performance can help detect potential security attacks" | TIMESAFE §2.3 | V2 |
| pmc must name the domain | `-d`: "Specify the domain number in sent messages. The default is 0." | linuxptp v4.0 pmc.8 | V2; behaviour **V1**: on this testbed `pmc` without `-d 24` returns only "sending: GET …" and no data, and with `-d 24` it returns PARENT_DATA_SET / PORT_DATA_SET |

This confirms the probable cause of the 168-run campaign's empty pmc logs, which `pmc_log.sh` called without `-d 24`. The loop's verification step and the outcome observer use `-d 24`.

## 5. Threat definitions reused unchanged from the deck

These all appear on the v8 slides and are referenced there:
- RFC 7384 §3.1 / §3.2
- ETSI TR 104 106 V3.0.0 T-SPLANE-01..04 and T-FRHAUL-01/02
- ETSI TS 104 105 V7.0.0 test IDs 11.1.5.x / 24.2.1.x
- TIMESAFE §4 and §6.1

## 6. Not verified (open items)

- ETSI TS 104 105 pass criteria for 11.1.5.2.2 and 11.1.5.3.1 (pp. 121–124): **NV**. They need reading from the PDF by hand.
- ETSI TS 104 104 V9.1.0 clause 5.2.5.3 S-plane security controls: **NV**. The table of contents was confirmed, the text was not.
- The G.8275.1 clause number for notSlave/masterOnly, and G.8273.2 holdover limits: **NV**.
