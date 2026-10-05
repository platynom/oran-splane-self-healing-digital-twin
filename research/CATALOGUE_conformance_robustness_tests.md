I've completed the research. Here is the catalogue.

---

# Exhaustive Catalogue: IEEE 1588 / PTP Conformance, Interoperability & Robustness Test Cases
### With emphasis on ITU-T G.8275.1 (telecom profile) as used in O-RAN fronthaul S-plane

**Provenance caveat up front:** UNH-IOL's numbered test IDs below are extracted verbatim from the publicly posted *IEEE 1588 Default PTP Profiles Conformance Test Plan v0.0.2* and the *1588 Power Profile Test Plan (NISTIR 8002 pre-publication)*. The UNH-IOL index page lists newer revisions (Default v0.0.7, Power Profile v1, and a **partially-implemented draft ITU-T G.8275.1 test plan, last updated 2019-08-05**) whose PDFs are not publicly downloadable — the G.8275.1 plan has no public test IDs. ITU-T G.8273.2 numbers are from the freely-served 05/2014 text plus the G.8275.1 Amd.3 text; ITU-T G.8275.1's current main body is paywalled, so a few profile values are corroborated from vendor/tool-vendor restatements and are marked as such.

---

## 0. STANDARDISED THRESHOLDS AND QUALIFICATION RULES
*(the highest-value section — these replace invented constants)*

### 0.1 Message rate tolerance — the single most reusable constant

| Rule | Value | Source |
|---|---|---|
| **Message interval tolerance** | A device **shall, with 90% confidence, issue messages with intervals within ±30% of the stated (mean) value** — applies to Announce, Sync and Pdelay_Req | IEEE 1588-2019 **clause 7.7.2.1**, as restated by [Calnex PFV: Message Rate Testing](https://calnexsolutions.atlassian.net/wiki/spaces/KB/pages/10977515/PFV+Message+Rate+Testing) |
| Delay_Req rate conformance | Judged against the **mean** in the Delay_Resp `logMessageInterval` field, not per-interval bounds | IEEE 1588-2019 **clause 9.5.11.2**; [Calnex PFV](https://calnexsolutions.atlassian.net/wiki/spaces/KB/pages/10977515/PFV+Message+Rate+Testing) |
| Unicast/negotiated rate check | Rate is not carried in the packet; derive expected rate from first N Syncs, round to a standard 1588 rate, then apply ±30% | [Calnex PFV](https://calnexsolutions.atlassian.net/wiki/spaces/KB/pages/10977515/PFV+Message+Rate+Testing) |
| **G.8275.1 successive-interval cap** | "Successive Sync and Announce message intervals **must not exceed twice the mean interval**" | ITU-T G.8275.1 Amd.3, via [ITU 08/2019 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items) |
| UNH operationalisation, Announce @ 1/s default profile | 90% CI of mean interval must lie wholly within **7–13 s**; **no outlier > 3.5 s**; `logMessageInterval` field == 1 | [UNH PWR.c.1.1](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| UNH operationalisation, Sync @ 1/s | 90% CI wholly within **0.7–1.3 s**; `logMessageInterval` == 0 | [UNH PWR.c.1.2](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| UNH operationalisation, Pdelay_Req | 90% CI wholly **> 0.7 s** | [UNH PWR.c.1.4](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |

Note the asymmetry worth exploiting: the 7–13 s band is **±30% of 10 s**, and 0.7–1.3 s is **±30% of 1 s**. The UNH bands *are* clause 7.7.2.1 applied. So a detector threshold of ±30% on observed message interval is standards-derived, not invented.

### 0.2 Foreign-master qualification window

| Rule | Value | Source |
|---|---|---|
| Qualification condition | An Announce qualifies for BMCA only if **at least `FOREIGN_MASTER_THRESHOLD` Announce messages have been received from that sending port within `FOREIGN_MASTER_TIME_WINDOW`** | IEEE 1588-2008/2019 §9.3.2.4.x, as modelled in [IEEE 802.1 as-roberts-bmca-rearrangement](https://www.ieee802.org/1/files/public/docs2013/as-roberts-bmca-rearrangement-time-calc-spreadsheet-0713-v01.pdf) |
| `FOREIGN_MASTER_THRESHOLD` | **2** | [linuxptp `foreign.h`](https://github.com/richardcochran/linuxptp/blob/master/foreign.h) (`#define FOREIGN_MASTER_THRESHOLD 2`) |
| `FOREIGN_MASTER_TIME_WINDOW` | **4 announce intervals** (confirmed behaviourally by the UNH test below) | Derived from [UNH PWR.c.2.3](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **Behavioural proof of the window** | Announce sent **once per 4 announceIntervals → must NOT qualify**; **once per 2 announceIntervals → must qualify**; **once per announceInterval → must qualify** | [UNH PWR.c.2.3 Part A](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **foreignMasterDS minimum capacity** | **≥ 5 foreign master records** | [UNH PWR.c.2.3 Part B](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |

This gives a **precise, standards-based rule**: 2 Announce within 4 announceIntervals = qualified; fewer = must be ignored. At G.8275.1's 8 Announce/s, that window is **0.5 s**.

### 0.3 announceReceiptTimeout semantics

| Rule | Value | Source |
|---|---|---|
| Semantics | Timeout = `portDS.announceReceiptTimeout` × `announceInterval`. Expiry raises **`ANNOUNCE_RECEIPT_TIMEOUT_EXPIRES`** (IEEE 1588-2008 §9.2.6.11); clock **immediately updates data sets** and the port leaves SLAVE (→ MASTER, via PRE_MASTER where implemented) | [IEEE 802.1 BMCA rearrangement doc](https://www.ieee802.org/1/files/public/docs2013/as-roberts-bmca-rearrangement-time-calc-spreadsheet-0713-v01.pdf) |
| IEEE 1588 default-profile value | **3** | [UNH PWR.c.1.3 Part B](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) — FAIL if GET returns ≠ 3 |
| Default-profile behavioural bound (announceInterval = 10 s nominal in that test) | DUT **must not** claim master when Announce arrive every **10–25 s**; **must** claim master by **N = 30–35 s** | [UNH PWR.c.1.3 Part A](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **G.8275.1 value** | **3** (→ 3 × 1/8 s = **375 ms** to declare loss of Announce) | [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items); corroborated by [Cisco IR8340 G.8275.1 guide](https://www.cisco.com/c/en/us/td/docs/routers/ir8340/software/configuration/b-ir8340-timing-ios-xe-17/m-8275-1-telecom-profile.pdf) (portDS shows 3) |
| Power Profile behavioural bound | PrefGM: DUT sends Announce when N = **2 or 2.5 s**. Other GMC: when N = **3 or 3.5 s** | [UNH Power PWR.c.1.3](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |

### 0.4 stepsRemoved limits

| Rule | Value | Source |
|---|---|---|
| Discard rule | Announce with **stepsRemoved ≥ 255** must be **discarded** (not used by BMCA) | [UNH PWR.c.2.4 Parts A–D](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf): 255 (0x00FF) → must NOT be selected; 254 (0x00FE) → must be selected; 65,535 (0xFFFF) → must NOT; 10 (0x000A) → must |
| **±1 rule (Erbest self-comparison)** | If received stepsRemoved is **≥ own + 1** → stop announcing (yield). If **≤ own − 1** → continue announcing. Both the ±1 boundary and the ±2 cases are tested | [UNH PWR.c.2.9 Parts A–D](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| ±1 rule between two foreign masters | TS1 stepsRemoved < TS2 → TS1 wins; > → TS2 wins; tested at both ±1 and ±2 | [UNH PWR.c.2.9 Parts E–H](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **G.8275.1 `maxStepsRemoved`** | default **255**, configurable range **{1…255}**. Purpose stated in the Rec: limit reference-chain length "to prevent performance degradation or **rogue frame propagation in ring topologies**" | [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items); [linuxptp G.8275.1 config](https://linuxptp.nwtime.org/documentation/configs/g-8275-1/) (`maxStepsRemoved 255`) |

### 0.5 ITU-T G.8275.1 profile attribute values (the conformance baseline for O-RAN fronthaul)

| Attribute | Value | Range | Source |
|---|---|---|---|
| Profile name / version / ID | "ITU-T PTP profile for phase/time distribution with full timing support from the network" / **2.1** / **00-19-A7-01-02-01** | — | [ITU Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items) |
| `domainNumber` | **24** | **24–43** | [ITU Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items); [Calnex G.8275.1 Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |
| `priority1` | **128**, static, not used by the alternate BMCA | fixed | same |
| `priority2` | T-GM/T-BC **128**, range {0–255}; **T-TSC fixed 255** | — | same |
| `localPriority` (profile-specific, non-transmitted) | **128**, per-port **and** per-clock | **{1–255}** | same |
| `logAnnounceInterval` | **−3** → **8 Announce/s** | fixed nominal | [ITU Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items); [linuxptp](https://linuxptp.nwtime.org/documentation/configs/g-8275-1/) |
| `logSyncInterval` | **−4** → **16 Sync/s** (+ Follow_Up) | fixed nominal | same |
| `logMinDelayReqInterval` | **−4** → **16 Delay_Req/s** | fixed nominal | same |
| `announceReceiptTimeout` | **3** | — | same |
| `delayMechanism` | **01 = Delay_Req/Resp (E2E)**; **peer-delay prohibited** | — | [Calnex Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |
| Transport | **IEEE 802.3 Ethernet multicast only** (1588 Annex F). MACs **01-80-C2-00-00-0E** (non-forwardable) and **01-1B-19-00-00-00** (forwardable). **VLAN tags not allowed. Unicast prohibited.** | — | [Calnex Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |
| One-step / two-step | **Both must be supported and handled without reconfiguration** | — | same |
| Mode | **Two-way only** | — | [WSTS 2014 Jobert](https://wsts.atis.org/wp-content/uploads/2018/11/4-4-Iometrix_Jobert_ITU_G.8275.1.pdf) |
| `clockAccuracy` | **0x21** (PRTC-locked), **0x20–0xFE** (ePRTC-locked), **0xFE** (non-PRTC) | — | [Calnex Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |
| `offsetScaledLogVariance` | **0x4E5D** (PRTC), **0x4B32–0xFFFF** (ePRTC), **0xFFFF** (other) | — | same |
| `maxStepsRemoved` | **255** | {1–255} | [ITU Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items) |
| Messages used | Sync, Follow_Up, Announce, Delay_Req, Delay_Resp. **Signaling & Management: FFS/not used** | — | [WSTS 2014 Jobert](https://wsts.atis.org/wp-content/uploads/2018/11/4-4-Iometrix_Jobert_ITU_G.8275.1.pdf) |

**clockClass table (G.8275.1)** — any value outside this set is a conformance failure:

| clockClass | Meaning | Permitted on |
|---|---|---|
| **6** | Locked to PRTC/ePRTC (e.g. GNSS-traceable) | T-GM |
| **7** | T-GM in holdover, **within** spec, Cat-1 frequency source | T-GM |
| **13 / 14** | (ePRTC/PRTC variants, frequency-traceable states) | T-GM |
| **135** | T-BC in holdover, **within** spec | T-BC |
| **140 / 150 / 160** | T-GM **out of** holdover spec (graded by frequency-source quality) | T-GM |
| **165** | T-BC **out of** holdover spec | T-BC |
| **248** | Clock with **no time reference since startup** / default | T-GM, T-BC |
| **255** | **Slave-only OC (T-TSC)** | T-TSC |

Sources: [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items), [Calnex G.8275.1 Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946).

**Alternate BMCA deltas vs. IEEE 1588 default** (all testable):
1. `priority1` is **not used** (fixed 128) — comparison begins effectively at clockClass.
2. Per-port Boolean **`masterOnly` / `notSlave`**: if TRUE, the port **shall never enter SLAVE**.
3. **`localPriority`** is appended to each foreign-master/parent dataset received on port *r* and used as a tie-breaker in determining **Erbest** and **Ebest**.
4. **Multiple active grandmasters** are permitted simultaneously.
5. `maxStepsRemoved` gates chain length.
Source: [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items).

**G.8275.2 comparison** (partial timing support — for contrast): domain **44–63** (default 44); Sync & Delay 1–128/s; Announce **1–8/s**; **unicast negotiation mandatory**; IPv4/UDP mandatory; clockClasses {6,7,140,150,160,248} GM / {135,165,248} BC / {255} slave-only. [Calnex G.8275.2 Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10486539).

### 0.6 PTSF (Packet Timing Signal Fail) states

| State | Trigger | Source |
|---|---|---|
| **PTSF-lossSync** | Sync receipt timeout exceeded | G.8275.2 §6.7.11; [linuxptp PTSF patch thread](https://sourceforge.net/p/linuxptp/mailman/linuxptp-devel/thread/Y06UPaVa2Swq+DFJ@hoboy.vegasvil.org/) |
| **PTSF-lossDelayResp** | Delay_Resp timeout exceeded | same |
| **PTSF-lossAnnounce** | Announce receipt timeout (announceReceiptTimeout × announceInterval) | G.8275.1/.2; ITU-T SG15 contribution [C-1835 "Timeout parameter of PTSF-lossSync"](https://www.itu.int/md/T17-SG15-C-1835/en) (China Mobile/Unicom/Huawei/SKT, 2020-01-14) |
| **PTSF-unusable** | Set via management (`PORT_PTSF_UNUSABLE_NP` TLV) | [linuxptp thread](https://sourceforge.net/p/linuxptp/mailman/linuxptp-devel/thread/Y06UPaVa2Swq+DFJ@hoboy.vegasvil.org/) |
| **Required behaviour** | While a signal-fail condition exists, the port **ignores Announce messages from that source** until it clears | same |

---

## GROUP 1 — ATTRIBUTE / FIELD VALUE CONFORMANCE

### 1a. UNH-IOL Default PTP Profiles Conformance Test Plan — Group 1
Source for all: [UNH-IOL 1588-Default-Test-Plan_v0.0.2.pdf](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) · index: [UNH-IOL 1588 test plans](https://www.iol.unh.edu/testing/switching/1588/test-plans)

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **PWR.c.1.1** | logAnnounceInterval | Default init value + settability via mgmt (managementId 0x2009) | 90% CI of mean Announce interval wholly in **7–13 s**, no outlier >3.5 s, `logMessageInterval`(offset 33) **= 1**; after SET to 0.3, mean in **1.7–2.3 s** |
| **PWR.c.1.2** | logSyncInterval | Default + settability (0x200B) | 90% CI wholly in **0.7–1.3 s**, `logMessageInterval` **= 0**; after SET, **1.7–2.3 s** |
| **PWR.c.1.3** | announceReceiptTimeout | Timeout value and behaviour (0x200A) | GET returns **3**; DUT stays slave for N=10–25 s, claims master at N=30–35 s; SET to 4 accepted |
| **PWR.c.1.4** | logMinPdelayReqInterval | Default + settability (0x6001) | 90% CI wholly **> 0.7 s**; value **0**; after SET to 0.3, mean **> 1.7 s** |
| **PWR.c.1.5** | priority1 and priority2 | Defaults + settability (0x2005 / 0x2006) | `grandmasterPriority1` **= 128** and `grandmasterPriority2` **= 128** in every Announce; SET to 130 reflected |
| **PWR.c.1.6** | slaveOnly | Default + settability (0x2008) | Defaults **FALSE**; SET to TRUE accepted |
| **PWR.c.1.7** | domainNumber | Domain in every message type + **domain isolation** + settability (0x2007) | Part A/B: all emitted PTP messages carry `domainNumber` **= 0**. **Part C: DUT responds to Pdelay_Req with domain 0 and MUST NOT respond to domain 2.** Part D: SET to 100 reflected |
| **PWR.c.1.8** | primaryDomain | TC primary domain (0x4002) | Defaults **0**; SET to 100 accepted |

### 1b. UNH-IOL Power Profile — attribute, transport, timescale, TLV and misc groups
Source for all: [UNH-IOL Power-Profile-Test-Plan (NISTIR 8002 pre-pub)](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIRPrePublication.pdf) → correct URL: [Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) · [NIST record](https://www.nist.gov/publications/1588-power-profile-test-plan)

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **PWR.c.1.1** | logAnnounceInterval | 1/s Announce | 90% CI wholly **0.7–1.3 s**; `logMessageInterval` **= 0** |
| **PWR.c.1.2** | logSyncInterval | 1/s Sync | 90% CI wholly **0.7–1.3 s**; field **= 0** |
| **PWR.c.1.3** | announceReceiptTimeout | Timeout, split by GM role | PrefGM: Announce emitted at N = **2 / 2.5 s**; other GMC: at N = **3 / 3.5 s** |
| **PWR.c.1.4** | logMinPdelayReqInterval | Pdelay_Req rate | 90% CI wholly **> 0.7 s** |
| **PWR.c.1.5** | priority1 and priority2 | Defaults | both **= 128** in every Announce |
| **PWR.c.1.6** | domainNumber | Domain value + isolation | All messages domain **0**; responds only to domain 0 |
| **PWR.c.5.1** | IEEE 802.3 Transport Mapping for Announce, Sync, Follow_Up | Correct Ethernet framing | Correct frame structure |
| **PWR.c.5.2** | IEEE 802.3 Transport Mapping for Forwarded Messages | TC forwarding preserves mapping | Mapping preserved |
| **PWR.c.5.3** | IEEE 802.3 Transport Mapping for Peer Delay Messages | Pdelay framing | Correct framing |
| **PWR.c.5.4** | Multiple Priorities | Priority tagging | Correct priority values |
| **PWR.c.5.5** | IEEE Std 802.1Q Tags | VLAN tag add/remove behaviour | Tags added/removed as required |
| **PWR.c.5.6** | **transportSpecific Field Checking Upon Receipt** | Rejection of wrong `transportSpecific` | Only correctly-tagged messages accepted — **a field-value negative test** |
| **PWR.c.6.1** | PTP Timescale | `ptpTimescale` flag | Timescale correctly indicated in Announce |
| **PWR.c.6.2** | Current UTC Offset | `currentUtcOffset` | Correct and current |
| **PWR.c.6.3** | Grandmaster Clock Class | clockClass for GM | Appropriate for GM capability |
| **PWR.c.6.4** | **Grandmaster Degradation of Clock Class** | clockClass change on reference loss | Degrades appropriately |
| **PWR.c.6.5** | Slave-Only Clock Class | clockClass 255 | Set to slave-only value |
| **PWR.c.6.6** | Clock Accuracy | `clockAccuracy` enum | Within spec |
| **PWR.c.6.7** | Holdover Drift for Grandmasters | Holdover drift | Within limits |
| **PWR.c.6.8** | GrandmasterID | GM identity stability | Stable and correctly propagated |
| **PWR.c.6.9** | Re-synchronization Behavior | Recovery after reference loss | Re-syncs within specified time |
| **PWR.c.7.1** | Order of TLVs | TLV ordering in Announce | Correct order |
| **PWR.c.7.2** | Profile-Specific TLV Default Field Values | TLV defaults | Correct defaults |
| **PWR.c.7.3** | organizationId / organizationSubType Recognition | Org-specific TLV parsing | Recognised and processed |
| **PWR.c.7.4** | **Announce Messages without TLVs** | Handling of missing expected TLV | Correctly processed (**negative/robustness**) |
| **PWR.c.7.5** | ALTERNATE_TIME_OFFSET_INDICATOR TLV with Discontinuity | Leap/DST discontinuity | Alternate time correct across discontinuity |
| **PWR.c.7.6** | Sequence of Announce Messages Before Discontinuity | Pre-discontinuity sequencing | Properly sequenced |
| **PWR.c.7.7** | ALTERNATE_TIME_OFFSET_INDICATOR TLV is not UTC | Non-UTC alt time | Distinguished from UTC |
| **PWR.c.7.8** | BCs Forwarding ALTERNATE_TIME_OFFSET_INDICATOR | BC TLV forwarding | Forwarded correctly |
| **PWR.c.9.1** | Clock Identity | Uniqueness/stability of clockIdentity | Stable, uniquely identifies device |
| **PWR.c.9.2** | Peer Delay One-Step and Two-Step Ingress Ports | Ingress mode handling | Both modes handled |
| **PWR.c.9.3** | Sync One-Step and Two-Step Ingress Ports | Sync ingress both modes | Both handled |
| **PWR.c.9.4** | One-Step or Two-Step Mode Egress Ports | Egress mode | Correct mode |
| **PWR.c.9.5** | One-Step or Two-Step Flags | `twoStepFlag` correctness | Flags correct in all message types |

### 1c. Tool-implemented field verification (vendor, but usable as a checklist)

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| PFV-1 | Protocol Field Verifier — profile field checks | Every header/body field against the selected profile's permitted values | Field-by-field PASS/FAIL against profile table | [Calnex PFV datasheet](https://calnexsol.com/datasheet/protocol-field-verifier-pfv/) |
| PFV-2 | PFV message rate — Announce (multicast) | Interval vs. `logMessageInterval` carried in the packet | within **±30%** | [Calnex PFV](https://calnexsolutions.atlassian.net/wiki/spaces/KB/pages/10977515/PFV+Message+Rate+Testing) |
| PFV-3 | PFV message rate — Sync (multicast & unicast) | Interval vs. declared/derived rate | within **±30%** | same |
| PFV-4 | PFV message rate — Delay_Req | Mean vs. Delay_Resp `logMessageInterval` | mean-based compliance | same |

---

## GROUP 2 — BMCA BEHAVIOUR

### 2a. UNH-IOL Default profile, Group 2
Source: [UNH-IOL Default Test Plan v0.0.2](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf)

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **PWR.c.2.1** | Disqualified Announce Messages, by clockIdentity | **Self-loop rejection**: Announce whose `sourcePortIdentity.clockIdentity` == DUT's own must be discarded even though it advertises a *better* priority1 | GM must become `0x102233fffe445566` (the one not using DUT's clockIdentity), **never** `…445567` |
| **PWR.c.2.2** | Disqualified Announce Messages, by Most Recent | Only the most recent Announce from a given clock is used | GM never becomes the spoof during the 10 worse-priority messages; becomes it only after the final better-priority message |
| **PWR.c.2.3** | Disqualified Announce Messages, by Foreign Master Window | **Foreign-master qualification window** (see §0.2) | 1-per-4-intervals → not selected; 1-per-2 and 1-per-1 → selected. Part B: **5 simultaneous foreign masters**, correct winner (`…445568`) proves ≥5-record foreignMasterDS |
| **PWR.c.2.4** | Disqualified Announce Messages, by stepsRemoved | stepsRemoved ≥255 discard rule, incl. 0xFFFF | 255/65535 → not selected; 254/10 → selected. Parts C/D repeat with mgmt read-back (0x2001/0x2002) |
| **PWR.c.2.5** | Disqualified Announce Messages, by alternateMasterFlag | Announce with `alternateMasterFlag`=TRUE must be discarded even if better | GM = the FALSE-flag source, never the TRUE-flag one |
| **PWR.c.2.6** | Data Set Comparison on a Single Port | Ordered comparison over **priority1, clockClass, clockAccuracy, offsetScaledLogVariance, priority2, clockIdentity** — run 5×, one attribute per run | Correct GM each time; Part C also checks parentDS via mgmt 0x2002 |
| **PWR.c.2.7** | Data Set Comparison on Multiple Ports | Same comparison across **4 foreign masters on 2 ports** | Best (`…445569`) wins; run 5× varying each attribute |
| **PWR.c.2.8** | State Decision Algorithm | SDA outputs **P1 / M1 / P2** | A(P1): clockClass 1–127, better sources present → DUT **PASSIVE**, emits only Pdelay/signaling/mgmt. B(M1): worse sources → DUT **MASTER** and is GM. C(P2): clockClass >127, 4 sources on 2 ports → **PASSIVE** |
| **PWR.c.2.9** | Steps Removed | **±1 stepsRemoved rule** (see §0.4) — 8 parts | A/C: TS stepsRemoved ≤ DUT−1 → DUT keeps announcing. B/D: ≥ DUT+1 → DUT stops. E–H: correct choice between TS1/TS2 at ±1 and ±2 |
| **PWR.c.2.10** | Source Port Identity | `sourcePortIdentity` handling in BMCA | (section truncated in the public draft) |

### 2b. UNH-IOL Power Profile, Group 3
Source: [UNH-IOL Power Profile Test Plan](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf)

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **PWR.c.3.1** | Disqualified Announce Messages, by clockIdentity | Duplicate/self clockIdentity rejection | Only one Announce per unique clockIdentity accepted |
| **PWR.c.3.2** | Disqualified Announce Messages, by Most Recent | Most-recent rule | Most recent accepted |
| **PWR.c.3.3** | Disqualified Announce Messages, by Foreign Master Window | Qualification window | Outside window rejected, inside accepted |
| **PWR.c.3.4** | Disqualified Announce Messages, by stepsRemoved | stepsRemoved in BMCA | Lower stepsRemoved preferred |
| **PWR.c.3.5** | Disqualified Announce Messages, by alternateMasterFlag | alternateMasterFlag | Flag influences selection correctly |
| **PWR.c.3.6** | Data Set Comparison on a Single Port | Comparison algorithm | Correct for all dataset fields |
| **PWR.c.3.7** | Data Set Comparison on Multiple Ports | Multi-port comparison | Correct port selection |
| **PWR.c.3.8** | State Decision Algorithm | SDA | Correct master/slave/passive transitions |
| **PWR.c.3.9** | Steps Removed | stepsRemoved computed in own Announce | Correct value emitted |
| **PWR.c.3.10** | Source Port Identity | sourcePortIdentity propagation | Correct |
| **PWR.c.3.11** | Default Slave-only | slaveOnly default | TRUE for slave-only devices |

### 2c. G.8275.1-specific alternate-BMCA cases (derivable; no public numbered IDs)
The UNH-IOL **ITU-T G.8275.1 test plan exists but is marked "Draft (Partially Implemented)"** and is not publicly posted ([index](https://www.iol.unh.edu/testing/switching/1588/test-plans)). The following are the profile deltas that a G.8275.1 BMCA test must cover, each traceable to [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items):

| Derived ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| G8275.1-BMCA-1 | priority1 is ignored | Two Announce differing **only** in priority1 | Selection **must not** change; priority1 must be 128 on the wire |
| G8275.1-BMCA-2 | localPriority tie-break (port) | Two equal Announce on two ports with different portDS.localPriority | Lower localPriority port wins Ebest |
| G8275.1-BMCA-3 | localPriority tie-break (clock) | defaultDS.localPriority effect | Applied at Ebest determination |
| G8275.1-BMCA-4 | masterOnly / notSlave | Port with `masterOnly`=TRUE receiving a superior Announce | Port **never** enters SLAVE |
| G8275.1-BMCA-5 | maxStepsRemoved enforcement | Announce with stepsRemoved > configured maxStepsRemoved | Discarded (loop/rogue-frame containment) |
| G8275.1-BMCA-6 | Multiple active T-GMs | Two GMs advertising simultaneously | Both permitted to remain active; each port resolves independently |
| G8275.1-BMCA-7 | clockClass ordering | 6 vs 7 vs 135 vs 140/150/160 vs 165 vs 248 vs 255 | Lower clockClass wins; 255 never becomes GM |

---

## GROUP 3 — STATE MACHINE AND PORT STATE TRANSITIONS

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| **PWR.c.2.8 A** | State Decision Algorithm output **P1** | Transition to PASSIVE when a better clock exists on the same path | Port in **BMC_PASSIVE**; DUT emits **only** Pdelay_Req/Resp/Resp_Follow_Up, signaling and required mgmt responses — **any other message type is a FAIL** | [UNH Default](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **PWR.c.2.8 B** | SDA output **M1** | Transition to MASTER when DUT is best | Port in **BMC_MASTER**, DUT is GM | same |
| **PWR.c.2.8 C** | SDA output **P2** | PASSIVE with clockClass >127 and 4 competing sources across 2 ports | **BMC_PASSIVE**; GM must not be TS1 | same |
| **PWR.c.1.3 A** | announceReceiptTimeout → SLAVE-to-MASTER transition | `ANNOUNCE_RECEIPT_TIMEOUT_EXPIRES` handling | No premature transition at N ≤ 25 s; transition by N = 30–35 s | same |
| **Group 3** | **State Configuration Options** (whole group, p.52) | Statically-configured port states / profile state options | (section not in the public draft body) | same |
| **Group 4** | **Management Mechanism** (p.53) | Management message GET/SET conformance | (section not in the public draft body) | same |
| **Group 6** | **Miscellaneous** (p.58) | — | — | same |
| **PWR.c.2.7 B/C/D** (Power) | Restriction on Peer Delay → **FAULTY state** | Behaviour on **multiple Pdelay_Resp** to a single Pdelay_Req | Device **enters FAULTY**, **discards** Sync/Follow_Up (BC/OC) and **stops forwarding** Sync/Follow_Up (TC) | [UNH Power](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **PWR.c.2.7 A** (Power) | Zero Pdelay_Resp | Behaviour on **no** response | DUT **continues** transmitting Pdelay_Req (must not wedge) | same |
| **PWR.c.6.9** (Power) | Re-synchronization Behavior | UNCALIBRATED → SLAVE re-entry after reference loss | Re-synchronises within specified time | same |
| **PTSF-1** | PTSF-lossSync | Sync timeout → signal-fail assertion | Port asserts PTSF-lossSync and **ignores Announce from that source until cleared** | [linuxptp PTSF thread](https://sourceforge.net/p/linuxptp/mailman/linuxptp-devel/thread/Y06UPaVa2Swq+DFJ@hoboy.vegasvil.org/) (G.8275.2 §6.7.11) |
| **PTSF-2** | PTSF-lossAnnounce | Announce timeout → signal-fail | as above | [ITU-T SG15 C-1835](https://www.itu.int/md/T17-SG15-C-1835/en) |
| **PTSF-3** | PTSF-lossDelayResp | Delay_Resp timeout → signal-fail | as above | [linuxptp thread](https://sourceforge.net/p/linuxptp/mailman/linuxptp-devel/thread/Y06UPaVa2Swq+DFJ@hoboy.vegasvil.org/) |
| **PTSF-4** | PTSF-unusable via management | `PORT_PTSF_UNUSABLE_NP` TLV | Port marked unusable, Announce ignored | same |
| **BMCA-RT-1** | BMCA re-arrangement time | Worst-case network re-convergence given foreign-master window + announceReceiptTimeout + PRE_MASTER | 10-node/9-BC chain: **110 s @ 1 Announce/s**, **55 s @ 2/s** (target 60 s); 20-node @ 2/s: **157.5 s (fails)** → conclusion "**Announce rate must be at least 2 pps**" | [IEEE 802.1 as-roberts-bmca-rearrangement-0713](https://www.ieee802.org/1/files/public/docs2013/as-roberts-bmca-rearrangement-time-calc-spreadsheet-0713-v01.pdf) |
| **STAB-1** | Steady-state port-state stability (O-RAN interop) | No SLAVE↔UNCALIBRATED toggling, **zero BMCA flaps**, exactly **one GM per domain** | Stable SLAVE; multiple visible GM candidates = FAIL | [nxgconnect O-DU↔O-RU troubleshooting](https://www.nxgconnect.com/post/o-du-o-ru-interoperability-troubleshooting-o-ran-wg4-c-u-s-m-planes) |
| **STAB-2** | Time-to-settle after BMCA change | Convergence after GM change | **≤ 5 min per ITU-T G.8275.1 guidance** | same |
| **Avnu-1** | 802.1AS recovered-clock lock time | Lock time and hold quality | Slave shall sync **within 6 s to ±80 ns** of directly-connected master and **maintain over a 5-minute window** | [Avnu 802.1AS Recovered Clock Quality Testing r1.0](https://avnu.org/wp-content/uploads/2014/05/Avnu-Testability-802.1AS-Recovered-Clock-Quality-Measurement-1.0_Approved-for-Public-Release.pdf) |

---

## GROUP 4 — MESSAGE RATE AND TIMING

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| **PWR.c.1.1** (Default) | logAnnounceInterval | Announce rate + declared field | 90% CI ⊂ **7–13 s**, no outlier >3.5 s, field = 1; ≥60 (or 600) intervals observed | [UNH Default](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **PWR.c.1.2** (Default) | logSyncInterval | Sync rate | 90% CI ⊂ **0.7–1.3 s**, field = 0 | same |
| **PWR.c.1.4** (Default) | logMinPdelayReqInterval | Pdelay_Req rate | 90% CI **> 0.7 s** | same |
| **PWR.c.1.1/1.2/1.4** (Power) | same, Power profile (1/s Announce) | Power-profile rates | CI ⊂ **0.7–1.3 s** (Announce & Sync); Pdelay_Req **> 0.7 s** | [UNH Power](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **RATE-30** | ±30% interval conformance | Generic 1588 rate tolerance | 90% confidence, intervals within **±30%** of stated value | IEEE 1588-2019 §7.7.2.1 via [Calnex](https://calnexsolutions.atlassian.net/wiki/spaces/KB/pages/10977515/PFV+Message+Rate+Testing) |
| **RATE-G8275.1-A** | G.8275.1 Announce rate | 8/s nominal, `logAnnounceInterval` = −3 | Rate 8/s; **no successive interval > 2× mean** | [ITU Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items) |
| **RATE-G8275.1-S** | G.8275.1 Sync rate | 16/s, `logSyncInterval` = −4 | Rate 16/s; no successive interval > 2× mean | same |
| **RATE-G8275.1-D** | G.8275.1 Delay_Req rate | 16/s, `logMinDelayReqInterval` = −4 | Rate 16/s (mean-based) | same |
| **PWR.c.1.1/1.2/1.4 Part B** | Rate **re-negotiation** via management | SET new interval then verify on the wire **and** via GET | New rate observed in `logMessageInterval` **and** in measured intervals within one test window | [UNH Default](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |

---

## GROUP 5 — DELAY MECHANISM

### 5a. Delay-Request/Response (E2E) — the mechanism used by G.8275.1

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| **PWR.c.7.1** | Mean Path Delay for Delay_Req (Parts A–D: GMC/slave-only × one-step/two-step) | meanPathDelay computation via E2E | Correct computed mean path delay | [UNH Default Group 7](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **PWR.c.2.1** (Power) | Peer Delay Mechanism is the only mechanism | **Negative**: E2E must be absent in Power Profile | Part A: **no Delay_Req received**; Part B: **no Delay_Resp received**; C/D: peer delay works in master and slave states | [UNH Power](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **G8275.1-DM-1** | Peer-delay prohibition (derived) | G.8275.1 forbids peer delay | DUT must not emit Pdelay_Req and must not respond to Pdelay_Req | [Calnex G.8275.1 Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |

### 5b. Peer Delay (P2P) — UNH Default Group 8

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **PWR.c.8.1** | Independent Ports for Boundary Clocks (one/two-step) | Per-port independent pdelay state | Measurements independent per port |
| **PWR.c.8.2** | Independent Ports for Transparent Clocks (4 parts) | Per-port independence on TC | Independent per port |
| **PWR.c.8.3** | Peer Delay Mechanism | Basic pdelay exchange | Correct exchange |
| **PWR.c.8.4** | Peer Delay Turnaround Timestamps, One-Step Clock | `correctionField` sanity | correctionField **> 0 and < (t4 − t1)** |
| **PWR.c.8.5** | Peer Delay Turnaround Timestamps, Two-Step Clock | Turnaround time sanity | Turnaround **> 0 and < (t4 − t1)** |
| **PWR.c.8.6** | Pdelay_Req Message Field Values (OC/BC, syntonized TC, non-syntonized TC) | Field values in Pdelay_Req | `correctionField` = 0, `originTimestamp` = 0, correct domainNumber |
| **PWR.c.8.7** | Pdelay_Resp Message Field Values, One-Step Clock | Field values | All fields correct |
| **PWR.c.8.8** | Peer Delay Message Field Values, Two-Step Clock | Pdelay_Resp + Pdelay_Resp_Follow_Up fields | All fields correct |
| **PWR.c.8.9** | Mean Path Delay (BC/OC/TC × one/two-step) | meanPathDelay accuracy | Average observed meanPathDelay **within 100 ns** of actual (Power Profile PWR.c.2.8 states this numeric limit) |
| **PWR.c.8.10** | **Restriction on Peer Delay Mechanism** | Zero / multiple Pdelay_Resp handling | See Group 3 FAULTY-state rows |

Source for 5b: [UNH Default Group 8](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf); Power-profile equivalents **PWR.c.2.1–2.10** at [UNH Power](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf).

---

## GROUP 6 — NEGATIVE / ROBUSTNESS / MALFORMED INPUT

### 6a. Standardised threat taxonomy — RFC 7384 (IETF, normative for time-protocol security requirements)
Source: [RFC 7384 — Security Requirements of Time Protocols in Packet Switched Networks](https://www.rfc-editor.org/rfc/rfc7384)

| ID | Title | What it verifies (as a test) | Pass criterion |
|---|---|---|---|
| **RFC7384-3.1.1** | Internal vs. external attacker | Classification axis: does attacker hold keys / have network access | — (model) |
| **RFC7384-3.1.2** | MITM vs. packet injector | Classification axis: can attacker intercept, or only inject | — (model) |
| **RFC7384-3.2.1** | **Packet manipulation** | MITM alters timing packets in flight | DUT detects/rejects altered packets; no unbounded time step |
| **RFC7384-3.2.2** | **Spoofing** | Attacker impersonates a legitimate node/master | DUT does not accept spoofed identity as GM |
| **RFC7384-3.2.3** | **Replay attack** | Recorded packets replayed unmodified | DUT rejects on sequenceId/timestamp regression |
| **RFC7384-3.2.4** | **Rogue master attack** | Attacker manipulates master election with malicious control packets | Correct GM retained (this is the BMCA-hardening case) |
| **RFC7384-3.2.5** | **Packet interception and removal** | MITM drops protocol packets | DUT asserts PTSF / announceReceiptTimeout within spec, does not free-run silently |
| **RFC7384-3.2.6** | **Packet delay manipulation** | MITM adds maliciously computed asymmetric delay | Detected or bounded; note this is **not** detectable by integrity checks |
| **RFC7384-3.2.7** | **L2/L3 DoS** | ARP/IP spoofing, MAC flooding | Sync maintained or clean failure |
| **RFC7384-3.2.8** | **Cryptographic performance attack** | Fake authenticated packets to exhaust crypto engine | No sync loss from CPU exhaustion |
| **RFC7384-3.2.9** | **DoS against the time protocol** | Excessive protocol packets (e.g. Announce/Sync flood) | Rate-limiting; no state corruption |
| **RFC7384-3.2.10** | **Grandmaster time-source attack** | GNSS jamming / GNSS spoofing at the GM | clockClass degrades correctly (6 → 7 → 140/150/160); downstream reacts |
| **RFC7384-3.2.11** | **Protocol vulnerability exploitation** | Implementation bugs / misconfiguration | No crash, no privilege issue |
| **RFC7384-3.2.12** | **Network reconnaissance** | Topology/node discovery via PTP | Information exposure bounded |

RFC 7384 §3.3 Table 1 maps each threat to **impact** (false time / accuracy degradation / DoS) × **attacker class** — use this as the coverage matrix.

### 6b. Enumerated PTP attack strategies (peer-reviewed, field-level detail)
Source: [Precision time protocol attack strategies and their resistance to existing security extensions, *Cybersecurity* (Springer) 2021](https://link.springer.com/article/10.1186/s42400-021-00080-y)

| ID | Attack | Message / field manipulated | Effect | Threshold noted |
|---|---|---|---|---|
| **ATK-1** | Packet content manipulation | `originTimestamp`, `preciseOriginTimestamp`, `correctionField`, `versionPTP`, `domainNumber` | Sync error or forced free-run | Clients "disregard clock offset calculations beyond a certain threshold" |
| **ATK-2** | Packet removal | Sync / Follow_Up / Delay_Req selectively dropped | Degradation or free-run | Selective removal must be subtle to evade detection |
| **ATK-3** | Packet delay manipulation | Sync or Delay_Req delayed asymmetrically | Offset error from path asymmetry | **Large instantaneous delays are detectable; incremental delay is not** |
| **ATK-4** | Time-source degradation | GNSS jam/spoof, firmware tamper at GM/BC | Whole subtree wrong | endpoint attack |
| **ATK-5** | Master spoofing | Announce/Sync/Follow_Up with spoofed identity | Subtree follows false GM | — |
| **ATK-6** | Slave spoofing | Delay_Req with victim's identity + matching sequenceId | Asymmetric delay, degraded sync | **Fails if response sequenceId does not match** → sequenceId checking is a defence and a test |
| **ATK-7** | Replay | Sync/Follow_Up or Delay_Resp replayed | Clock swings synced/unsynced or free-runs | Errors **> 1 s** trigger clock reset in their experiments |
| **ATK-8** | **BMCA attack** | `priority1`, `clockClass`, `clockAccuracy`, `offsetScaledLogVariance`, `priority2`, `clockIdentity` | Subtree elects compromised reference | Attacker must advertise "best" attributes |
| **ATK-9** | DoS | L2/L3 flooding, crypto-exhaustion | Free-run | High CPU from crypto verification |

Related: [Feasible Time Delay Attacks Against PTP (TUM-ESI)](https://tum-esi.github.io/publications-list/PDF/2022_feasible_time_delay_attack_against_ptp.pdf); [Cyber Attacks on PTP Networks — A Case Study, *Electronics* 9(9):1398](https://www.mdpi.com/2079-9292/9/9/1398); [Breaking Precision Time: OS Vulnerability Exploits Against IEEE 1588, arXiv:2510.06421](https://arxiv.org/html/2510.06421v1) — the latter adds **kernel-level** primitives (constant offset injection via `clock_gettime`, progressive skew via `clock_adjtime(ADJ_FREQUENCY)`, randomised disturbance) and cites **CVE-2025-21814** (uninitialised function pointer in PTP sysfs ioctl → NULL deref), **CVE-2018-11508** (`adjtimex()` info leak), **CVE-2022-2318**.

### 6c. Commercial fuzz-test suites (coverage definition)
Sources: [Black Duck Defensics IEEE1588 PTP **Server**](https://www.blackduck.com/fuzz-testing/defensics/protocols/ptp-server.html) · [IEEE1588 PTP **Client**](https://www.blackduck.com/fuzz-testing/defensics/protocols/ptp-client.html)

| ID | Title | Scope | Notes |
|---|---|---|---|
| **DEF-SRV** | PTP Server test suite | Fuzzes **Announce, Sync, Follow-Up, Delay-Resp, Pdelay-Req, Management, Signaling** (PTPv2) + PTPv1 Sync/Follow-Up/Delay-Resp/Management | Specs: IEEE 1588-2002, IEEE 1588-2008, **ITU-T G.8265.1**. Transports: UDP/IPv4, UDP/IPv6 (multicast **and** unicast), **Ethernet multicast**. "Fully automated black-box negative testing." Case count not published |
| **DEF-CLI** | PTP Client test suite | Fuzzes **Delay-Req, Pdelay-Resp, Pdelay-Resp-Follow-Up, Management, Signaling** (v1 and v2) | Same specs/transports |

Note for a G.8275.1/O-RAN programme: neither suite advertises a **G.8275.1** profile model — the Ethernet-multicast transport applies, but G.8275.1-specific field constraints (domain 24–43, forbidden VLAN tags, forbidden peer-delay, forbidden unicast) would need custom anomalies.

### 6d. Fuzzing / robustness taxonomy to instantiate against PTP fields
Source: [A Survey on the Development of Network Protocol Fuzzing Techniques, *Electronics* 12(13):2904](https://www.mdpi.com/2079-9292/12/13/2904); see also [Fuzzers for Stateful Systems: Survey and Research Directions, ACM CSUR](https://dl.acm.org/doi/10.1145/3648468) and [Network protocol fuzz testing: a survey and taxonomy, *MTAP*](https://link.springer.com/article/10.1007/s11042-015-2763-6)

| Axis | Categories | PTP instantiation (test cases to build) |
|---|---|---|
| Generation strategy | Mutation-based (bit flip, arithmetic, block add/delete/replace, dictionary) vs. generation-based (from spec/template) | Mutate a valid G.8275.1 Announce vs. generate from the Annex A table |
| Anomaly classes | long strings, format specifiers, large integers, negative numbers, boundary values | `messageLength` ≠ actual; `stepsRemoved` = 0xFFFF; `correctionField` = 0x7FFF…; `logMessageInterval` = 0x7F/0x80; `currentUtcOffset` extreme; `domainNumber` 0/23/44/255; `versionPTP` = 0/1/3/15; `sdoId`/`transportSpecific` wrong; `clockIdentity` = all-zero / all-FF / broadcast |
| Visibility | black / grey / white box | Black-box on a sealed O-RU; grey-box on ptp4l with coverage |
| Statefulness | state inference (passive/active), response-code state tracking, memory snapshots, message-sequence dependencies, state-transition guidance | Deliver Delay_Resp with no Delay_Req; Follow_Up with no Sync; Sync with `twoStepFlag`=0 followed by a Follow_Up; Announce from a port already in MASTER; Pdelay_Resp ×2 (→ expected **FAULTY**, see PWR.c.8.10 / Power PWR.c.2.7); management SET during UNCALIBRATED |
| Evaluation | code/branch coverage, path depth, vulnerability rate, state-space coverage, crash detection, **differential testing** | Differential: same anomaly against ptp4l vs. vendor O-RU; divergence = finding |

### 6e. Profile-specific negative cases with **standards-defined** expected rejection
These are the highest-confidence negative tests because the standard states the rejection, not a heuristic.

| ID | Input | Expected behaviour | Source |
|---|---|---|---|
| **NEG-1** | Announce with `sourcePortIdentity.clockIdentity` = DUT's own, advertising better quality | **Discarded** | [UNH PWR.c.2.1](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **NEG-2** | Announce with `alternateMasterFlag` = TRUE, better quality | **Discarded** | [UNH PWR.c.2.5](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **NEG-3** | Announce with `stepsRemoved` = 255 or 65535 | **Discarded** | [UNH PWR.c.2.4](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **NEG-4** | Announce arriving **slower than 2 per 4 announceIntervals** | **Never qualifies** as foreign master | [UNH PWR.c.2.3](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **NEG-5** | Any PTP message in a **different domain** | **Ignored, no response** | [UNH PWR.c.1.7 Part C](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **NEG-6** | Wrong `transportSpecific` field | **Rejected on receipt** | [UNH Power PWR.c.5.6](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **NEG-7** | **Multiple** Pdelay_Resp to one Pdelay_Req | Port → **FAULTY**; Sync/Follow_Up discarded (BC/OC) or not forwarded (TC) | [UNH PWR.c.8.10 / Power PWR.c.2.7](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **NEG-8** | **Zero** Pdelay_Resp | Keep transmitting Pdelay_Req (no wedge) | same |
| **NEG-9** | Announce **without** expected profile TLV | Processed correctly, no crash | [UNH Power PWR.c.7.4](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **NEG-10** | **VLAN-tagged** PTP frame under G.8275.1 | Rejected — VLAN tags **not allowed** in the profile | [Calnex G.8275.1 Annex A](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/10420946) |
| **NEG-11** | **Unicast** PTP under G.8275.1 | Rejected — multicast only, unicast prohibited | same |
| **NEG-12** | Pdelay_Req under G.8275.1 | No response — peer delay must not be used | same |
| **NEG-13** | Announce with `stepsRemoved` > configured `maxStepsRemoved` | Discarded (explicitly for **rogue frame propagation in ring topologies**) | [ITU G.8275.1 Amd.3](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8275.1-201908-S!Amd3!PDF-E&type=items) |
| **NEG-14** | Superior Announce on a port with `masterOnly`/`notSlave` = TRUE | Port never enters SLAVE | same |
| **NEG-15** | Announce advertising `priority1` ≠ 128 under G.8275.1 | Field value non-conformant; and **priority1 must not affect selection** | same |
| **NEG-16** | Successive Sync or Announce interval **> 2× the mean** | Non-conformant transmission | same |

---

## GROUP 7 — PERFORMANCE / ACCURACY LIMITS

### 7a. ITU-T G.8273.2 — T-BC and T-TSC timing characteristics
Source: [ITU-T Rec. G.8273.2/Y.1368.2 (05/2014) full text](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8273.2-201405-S%21%21PDF-E&type=items); Class C/D update: [Calnex, G.8273.2 specification for Class C and D clocks](https://calnexsol.com/blog/g-8273-2-specification-for-class-c-and-d-clocks/); [Amendment 2 (01/2019) ToC](https://www.itu.int/dms_pubrec/itu-t/rec/g/T-REC-G.8273.2-201901-S!Amd2!TOC-HTM-E.htm)

| ID | Title | Verifies | Pass criterion |
|---|---|---|---|
| **G8273.2-7.1** | **Noise generation** — max\|TE\| | Absolute time error of T-BC output | **Class A: 100 ns; Class B: 70 ns** (Table 7-1). T-TSC identical (Table C.1) |
| **G8273.2-7.1-cTE** | Noise generation — constant TE | Steady offset | **Class A: ±50 ns; Class B: ±20 ns** (Table 7-2 / C.2). Class C: ±10 ns, Class D: (see max\|TE_L\| below) |
| **G8273.2-7.1-dTE-const** | Noise generation — dTE MTIE, **constant temperature (±1 K)** | Dynamic TE wander | **MTIE ≤ 40 ns** for m < τ ≤ **1,000 s** (Table 7-3); τ_min set by packet rate (1/16 s at 16 pps) or 1 s for 1PPS |
| **G8273.2-7.1-dTE-var** | Noise generation — dTE MTIE, **variable temperature** | Wander over temperature | **MTIE ≤ 40 ns** for m < τ ≤ **10,000 s** (Table 7-4); T-TSC Tables C.3/C.4 |
| **G8273.2-IV.1 / V.1** | dTE **TDEV** (informative) | Wander stability | **TDEV ≤ 4 ns**, m < τ ≤ 1,000 s, constant temperature (Appendix IV for T-BC, Appendix V for T-TSC) |
| **G8273.2-ClassD** | Class D max\|TE_L\| | Low-pass-filtered TE | **5 ns** ("headline 5 ns specification") |
| **G8273.2-7.2** | **Noise tolerance** | Input noise the clock must survive **simultaneously** | dTE per **G.8271.1 clause 7.3** at PTP input; wander per **G.8262 clause 9.1** at SyncE input; wander per **G.813 clause 8.1** at SDH input — **with no alarms, no reference switching, no entry into holdover** |
| **G8273.2-7.3.1** | **Noise transfer, PTP → PTP/1PPS** | Transfer function | Bandwidth **max 0.1 Hz / min 0.05 Hz**; **gain peaking ≤ 0.1 dB** |
| **G8273.2-7.3.2** | **Noise transfer, physical-layer frequency → PTP/1PPS** | SyncE-to-PTP transfer | Band-pass: lower corner **0.05–0.1 Hz**, upper corner **1–10 Hz**; **max phase gain 0.2 dB** |
| **G8273.2-B.1** | **SyncE/SDH transient — first output phase-error transient** | Rearrangement transient before PRC-traceability re-established | Mask: 0 ≤ S < 0.016 → **40 + 7,500S** ns; 0.016 ≤ S < 0.5 → **160 + 50(S−0.016)**; 0.5 ≤ S < 2.2 → **214.2 + 50(S−0.5)**; 2.2 ≤ S < 25 → **40 + 259.2·e^(−2π(0.05)(S−2.2))** |
| **G8273.2-B.2** | SyncE/SDH transient — **second** output phase-error transient | After PRC-traceability re-established (10 s window) | 0 ≤ S < 0.016 → **40 + 7,500S**; 0.016 ≤ S < 0.141 → **160**; 0.141 ≤ S < 25 → **40 + 60·e^(−2π(0.05)(S−0.141))** |
| **G8273.2-7.4.2** | **Holdover** | Local-oscillator and physical-layer-assisted holdover | **"For further study"** in the 2014 text (T-BC 7.4.2, T-TSC C.2.4.2) — Class B holdover masks exist in later amendments/tooling |
| **Filter bandwidths** | — | Measurement filters | G.8273.2 BC filter **0.05–0.1 Hz**; enhanced EEC (Class C/D) **1–3 Hz**; ordinary EEC (Class A/B) **1–10 Hz** |

Mask assumptions (Appendix II), useful when reproducing results: first T-BC in chain, **perfect PTP input**, **0.05 Hz** filter, **2,000 ms holdover message delay (T_HM)**, **30 ns** phase jump on SyncE/SDH rejection, **60 ns** on reacquisition, **16 packet/s** Sync rate.

**Practical test-instrument realisation** (names map 1:1 to the clauses above) — [SiTime/Calnex IEEE 1588 test instructions](https://www.sitime.com/api/gated/IEEE-1588-Calnex-Test-Instructions.pdf), [Calnex G.8273.2 BC Conformance Test](https://www.calnexsol.com/en/solutions-en/education/techlib/timing-and-sync-lab/1284-g-8273-2-bc-conformance-test), [Calnex G.8273.2 T-TSC Conformance Test](https://calnexsol-jp.com/solutions-jp/education/techlib/timing-and-sync-lab/1048-g-8273-2-t-tsc-conformance-test):

| # | Test | Applies to |
|---|---|---|
| 1 | Noise generation **with** SyncE | BC, TSC |
| 2 | Noise generation **without** SyncE (free-run) | BC, TSC |
| 3 | Noise tolerance with SyncE (**1.1 µs limit**) | BC, TSC |
| 4 | Noise transfer PTP → PTP/1PPS **with** SyncE | BC |
| 5 | Noise transfer PTP → PTP/1PPS **without** SyncE | BC |
| 6 | Noise transfer SyncE → PTP/1PPS | BC, TSC |
| 7 | SyncE transient → PTP | BC, TSC |
| 8 | SyncE transient → 1PPS | BC, TSC |
| 9 | Holdover with SyncE (**Class B holdover mask**) | BC, TSC |

Noise-generation runs collect **1,000 s** of data against the TDEV mask.

### 7b. ITU-T G.8260 / G.8271.1 — metrics and network limits

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| **G8260** | Definitions and terminology for sync in packet networks | Normative definitions of **TE, cTE, dTE, dTE_L, dTE_H, MTIE, TDEV, FPP (floor packet percentile), FPC, minTDEV, clusterTDEV, PDV** and their measurement methods | Metrics computed per G.8260 definitions | [ITU-T G.8260 (11/2022)](https://www.itu.int/epublications/ru/publication/itu-t-g-8260-2022-11-definitions-and-terminology-for-synchronization-in-packet-networks/en); [Amd.1 (01/2024)](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.8260-202401-I!Amd1!PDF-E&type=items) |
| **G8271.1-C** | Network limit at **reference point C** | End-of-network time error, FTS | **max\|TE\| ≤ 1,100 ns** | [ITU-T G.8271.1 (11/2022)](https://www.itu.int/rec/T-REC-G.8271.1-202211-I); [Calnex G.8271.1 one-page summary](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/9470164/ITU-T+G.8271.1+(Network+Limits+-+FTS)+One-Page+Summary) |
| **G8271.1-E** | Total limit at **reference point E** (end application) | End-to-end budget | **1,500 ns (±1.5 µs)** | same (Appendix V budget) |
| **G8271.1-7.3.1/7.3.2** | Point-C limits, standard vs. **enhanced SyncE + Class C clocks** | Two limit sets depending on network class | per clause | same |

### 7c. O-RAN WG4 S-plane conformance tests
Primary source: **O-RAN.WG4.CONF.0** (Fronthaul Conformance Test Specification), section **3.3 S-Plane**. Current version per [Calnex O-RAN Sync Standards Updates](https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/1790935082): **O-RAN.WG4.CONF.0 v16.00, June 2026**; companion **O-RAN.WG4.IOT.0 v16.00**. The section numbering below is stable across v04→v08 and was extracted from [O-RAN.WG4.CONF.0-v04.00](https://pdfcoffee.com/o-ran-wg4-conf-0-v04-00-00-pdf-free.html) and [v08.00 (R003)](https://www.scribd.com/document/684467241/O-RAN-WG4-CONF-0-R003-v08-00).

| Test ID | Title | Status | Verifies | Pass criterion |
|---|---|---|---|---|
| **3.3.1** | S-Plane Test Environment | — | Test bed definition for S-plane | — |
| **3.3.2** | **Functional test of O-RU using ITU-T G.8275.1 profile (LLS-C1/C2/C3)** | **Mandatory** | O-RU can synchronise to a wrap-around tester delivering PTP **and** SyncE with the G.8275.1 profile across the three sync topologies | Per **Table 3.3.2.2** of the CONF spec; command-output log reports PASS |
| **3.3.3** | **Performance test of O-RU using ITU-T G.8275.1 Profile (LLS-C1/C2/C3)** | **Mandatory** | O-RU time-error performance under **ideal and normal operating conditions**, optionally with SyncE | Per **section 3.3.3 D** of the CONF spec |
| **3.3.4** | Performance test of O-RU using LLS-C4 | **For Future Study** | O-RU with local GNSS | — |
| **3.3.5** | **Functional test of O-DU synchronized from ITU-T G.8275.1 profile PRTC/T-GM** | **Mandatory** | O-DU as PTP client of a network T-GM | — |
| **3.3.6** | **Functional test of O-DU synchronized from embedded or local non-PTP PRTC** | **Mandatory** | O-DU with local/embedded PRTC | — |
| **3.3.7** | **Performance test of O-DU synchronized from either local or remote PRTC** | **Conditional Mandatory** | O-DU time-error performance | — |
| **3.3.8** | **Performance test of O-DU synchronized from embedded GNSS receiver** | **Conditional Mandatory** | O-DU + GNSS performance; per WSTS, uses **G.8273.2 Appendix IX noise patterns** | — |

Downstream instantiation (NTIA 5G Challenge Stage 2 RU test plan, which cites O-RAN.WG4.CONF.0-v05.00) — [test plan PDF](https://its.ntia.gov/media/rz5d044m/5gchallenge2023_stage2_ru_testplan_v13.pdf):

| Test ID | Title | Pass criterion |
|---|---|---|
| **RU-TC-WG4.CONF.3.3.2** | Functional test of RU using ITU-T G.8275.1 profile (LLS-C1/C2/C3) | Per Table 3.3.2.2 in O-RAN.WG4.CONF.0-v05.00; log PASS |
| **RU-TC-WG4.CONF.3.3.3** | Performance test of RU using ITU-T G.8275.1 Profile (LLS-C1) | Per section 3.3.3 D; log PASS |

**O-RAN sync configurations** (from [O-RAN.WG4.CUS.0](https://www.techplayon.com/o-ran-fronthaul-transport-synchronization-configurations/), [WSTS 2022 Armstrong](https://wsts.atis.org/wp-content/uploads/2022/05/12-Greg-Armstrong.ORAN-Fundamentals.pdf)):

| Config | Definition | O-RU inputs required |
|---|---|---|
| **LLS-C1** | O-DU in the sync chain; direct point-to-point O-DU↔O-RU | PLFS (SyncE) **and** PTP |
| **LLS-C2** | O-DU in the sync chain; one or more Ethernet switches in the fronthaul | PLFS **and** PTP |
| **LLS-C3** | O-DU **not** in the sync chain; PRTC/T-GM distributes through the network | PLFS **and** PTP |
| **LLS-C4** | Local GNSS at the O-RU; no transport-network involvement | neither |

**O-RAN / 3GPP time-error budgets** (from [WSTS 2021 Frost](https://wsts.atis.org/wp-content/uploads/2021/03/Sync-in-Fronthaul-WSTS21-Frost.pdf), [WSTS 2022 Frost](https://wsts.atis.org/wp-content/uploads/2022/05/08-Tim-Frost.Challenges-in-Synchronization-Testing-for-ORAN-.pdf), [WSTS 2022 Armstrong](https://wsts.atis.org/wp-content/uploads/2022/05/12-Greg-Armstrong.ORAN-Fundamentals.pdf)):

| Item | Limit |
|---|---|
| **Category A** (intra-band CA, FR2) TAE | **130 ns** |
| **Category B** (intra-band CA, FR1) TAE | **260 ns** |
| **Category C** (TDD radios) TAE | **3 µs** |
| TAE between RU clusters from the same DU | **130 ns (±65 ns)** |
| **O-RU time error to PRTC** | **±1.5 µs** (hard limit) |
| **Relative TE between O-DU and O-RU** | **3 µs (±1.5 µs)** |
| O-DU time error | no hard limit; ~3–5 µs reasonable |
| Reference point C (LLS-C2) | **max\|TE_L\| < 1.1 µs** per G.8271.1/G.8271.2 |
| Network time error (C2) | 95–140 ns |
| Relative time error (C2) | 60–190 ns |
| **O-DU frequency class** | Class A **±15 ppb**; Class B **±5 ppb** |
| **O-RU RF output** | **50 ppb**; O-RU 1PPS output **36 ppb** |
| Max one-way fronthaul latency | 100 µs |

### 7d. Other performance tests

| ID | Title | Verifies | Pass criterion | Source |
|---|---|---|---|---|
| **PWR.c.5.1** | Frequency Accuracy (one-step / two-step GM) | GM oscillator accuracy | per plan | [UNH Default Group 5](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588-Default-Test-Plan_v0.0.2.pdf) |
| **PWR.c.5.2** | Frequency Adjustment Range (P2P one/two-step, E2E) | Servo pull range | per plan | same |
| **PWR.c.2.8** (Power) | Mean Path Delay | Path-delay accuracy | **Average observed meanPathDelay within 100 ns of actual** | [UNH Power](https://www.iol.unh.edu/sites/default/files/testsuites/1588/Power-Profile-Test-Plan_NISTIR8002PrePublication.pdf) |
| **PWR.c.8.1–8.6** (Power) | LocalTimeInaccuracy / TimeInaccuracy for GM, TC; Grandmaster+NetworkTimeInaccuracy | Power-profile inaccuracy reporting and accumulation | Values correct, propagated and accumulated | same |
| **LTNCY.1.1** | Port **Egress** Latency Behavior on a 1-Step TC | Egress timestamp point vs. MDI | **Informative** — reports max/min/mean/σ of egress timestamp error | [UNH 1588 Port Latency Test Plan v1.0.0](https://www.iol.unh.edu/sites/default/files/testsuites/1588/1588_Port-Latency_TestPlan_v1.0.0.pdf) |
| **LTNCY.1.2** | Port **Ingress** Latency Behavior on a 1-Step TC | Ingress timestamp point vs. MDI | Informative; same statistics | same |
| **LTNCY.2.1** | Port Egress Latency on a Single Active Link | Egress latency | **Conditional Mandatory**; ≥ **1,000 samples**, reports max/min/mean/σ | same |
| **LTNCY.2.2** | Port Ingress Latency on a Single Active Link | Ingress latency | Conditional Mandatory; ≥ 1,000 samples | same |
| **Avnu-RCQ** | 802.1AS recovered clock quality | Lock time + hold quality, via **1PPS**, **ingress reporting** or **reverse-Sync** methods | Sync **within 6 s to ±80 ns**, maintained over a **5-minute** window | [Avnu r1.0](https://avnu.org/wp-content/uploads/2014/05/Avnu-Testability-802.1AS-Recovered-Clock-Quality-Measurement-1.0_Approved-for-Public-Release.pdf) |
| **G8262** | ITU G.8262 EEC test plan | SyncE clock conformance | per G.8262 | [UNH-IOL test plans index](https://www.iol.unh.edu/testing/switching/1588/test-plans) |
| **TC-SIL** | IEEE 1588 TC Silicon Validation | TC residence-time/correctionField silicon validation | per plan (1 week) | same |
| **GM-FAILOVER** | GM Failover Testing | Primary/backup GM switchover behaviour and transient | Custom performance test | same |

---

## Additional catalogued test plans (index, for completeness)
[UNH-IOL IEEE 1588 Test Plans](https://www.iol.unh.edu/testing/switching/1588/test-plans)

| Plan | Version | Status | Duration |
|---|---|---|---|
| IEEE 1588 Default PTP Profiles Conformance Test Plan | **0.0.7** (public draft v0.0.2 mined above) | Draft, active | 2 weeks |
| IEEE 802.1AS gPTP Conformance Test Suite | v1.0.1 | Fully documented | 1 week — **Avnu members only** |
| 1588 Port Latency Test Plan | v1.0.0 | Draft, active | 2 weeks |
| ITU G.8262 Test Plan | — | Fully documented | 2 weeks |
| **ITU-T G.8275.1** | — | **Draft, partially implemented** (2019-08-05) | 2 weeks |
| IEEE 1588 TC Silicon Validation | — | Draft, active | 1 week |
| 1588 Power Profile Conformance Test Plan (C37.238-2018, IEC/IEEE 61850-9-3) | v1 | Draft, active | 3 weeks |
| **IEEE 1588 Interoperability Test Suite** | **0.6** | Draft, active | **5 days** |
| GM Failover Testing | — | Draft, active | custom |

---

## Summary and gaps

**Count:** ~175 discrete test cases/criteria across the seven groups (Group 1: 42; Group 2: 28; Group 3: 17; Group 4: 10; Group 5: 13; Group 6: 47; Group 7: 38), well past the 50 target.

**Highest-value standards-based constants recovered** (each replaces an invented threshold):
- **±30% message-interval tolerance at 90% confidence** — IEEE 1588-2019 §7.7.2.1
- **Foreign-master qualification: 2 Announce within 4 announceIntervals** (= 0.5 s at G.8275.1's 8/s); **foreignMasterDS ≥ 5 records**
- **announceReceiptTimeout = 3** in both the default profile and G.8275.1 → **375 ms** loss-of-Announce detection at 8 Announce/s
- **stepsRemoved ≥ 255 ⇒ discard**; **±1 rule** for self/peer comparison; `maxStepsRemoved` default 255, explicitly for rogue-frame containment in rings
- **G.8275.1: successive Sync/Announce interval must not exceed 2× the mean**
- **G.8273.2**: max\|TE\| 100/70 ns (A/B), cTE ±50/±20 ns, dTE MTIE 40 ns (τ ≤ 1,000 s const-temp / 10,000 s var-temp), TDEV 4 ns, transfer BW 0.05–0.1 Hz with ≤0.1 dB peaking, Class D max\|TE_L\| 5 ns
- **G.8271.1**: 1,100 ns at point C, 1,500 ns at point E
- **O-RAN**: O-RU ±1.5 µs; Cat A/B/C TAE 130 ns / 260 ns / 3 µs; O-DU Class A ±15 ppb, Class B ±5 ppb
- **Avnu**: lock within 6 s to ±80 ns, held for 5 minutes

**Gaps I could not close:**
1. **UNH-IOL Default plan Groups 3 (State Configuration Options), 4 (Management Mechanism) and 6 (Miscellaneous)** appear in the ToC of v0.0.2 but their bodies are not in the public PDF; v0.0.7 returns 404.
2. **UNH-IOL's ITU-T G.8275.1 test plan** is not published — there are no public numbered G.8275.1 test IDs anywhere. The G.8275.1-specific rows I give are derived from the Recommendation's own normative statements, clearly marked as derived.
3. **O-RAN.WG4.CONF.0 section 3.3's pass-criteria tables** (Table 3.3.2.2, section 3.3.3 D) — the O-RAN spec body is behind a registration wall and every mirror I reached (scribd, pdfcoffee, zgc-xnet) served only front matter or was blocked by the egress proxy. Section numbers, titles and mandatory/conditional status are confirmed; the numeric contents of those two tables are not.
4. **ITU-T G.8275.1 main body (2022)** is paywalled; Amendment 3 (08/2019) served the profile table and clockClass list, which is what I used.
5. Defensics does **not** publish test-case counts or anomaly-class breakdowns for its PTP suites, and advertises G.8265.1 rather than G.8275.1 profile modelling.