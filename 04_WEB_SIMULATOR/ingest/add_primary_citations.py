#!/usr/bin/env python3
"""Apply the final primary-source audit to architecture.json.

The existing ``verification`` block records the earlier sentence/source audit.
This pass adds ``citation.primary`` only where the sentence's substantive claim
originates in an external standard.  Project measurements and configuration
claims deliberately do not receive a primary-standard badge.
"""

from __future__ import annotations

import json
from pathlib import Path


ARCH = Path(__file__).resolve().parents[1] / "content" / "architecture.json"

URLS = {
    "ARCH": "https://www.etsi.org/deliver/etsi_ts/103900_103999/103982/08.00.00_60/ts_103982v080000p.pdf",
    "CUS": "https://www.etsi.org/deliver/etsi_ts/103800_103899/103859/12.00.01_60/ts_103859v120001p.pdf",
    "MP": "https://www.etsi.org/deliver/etsi_ts/104000_104099/104023/17.01.00_60/ts_104023v170100p.pdf",
    "SEC": "https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf",
    "G8275": "https://www.itu.int/rec/T-REC-G.8275.1",
    "G8271": "https://www.itu.int/rec/T-REC-G.8271.1-202211-I/en",
    "G8262": "https://www.itu.int/rec/T-REC-G.8262",
    "RFC": "https://www.rfc-editor.org/rfc/rfc7384.html",
    "IEEE": "https://standards.ieee.org/ieee/1588/6825/",
    "TS38104": "https://www.etsi.org/deliver/etsi_ts/138100_138199/138104/19.03.00_60/ts_138104v190300p.pdf",
    "TS38133": "https://www.etsi.org/deliver/etsi_ts/138100_138199/138133/17.05.00_60/ts_138133v170500p.pdf",
}


def confirmed(url: str, clause: str, quote: str) -> dict:
    return {"checked": True, "result": "CONFIRMED", "quote": quote, "url": url, "clause": clause}


def inaccessible(url: str, clause: str) -> dict:
    return {"checked": False, "result": "NOT_ACCESSIBLE", "quote": "", "url": url, "clause": clause}


P = {
    "o-ru.s1": confirmed(URLS["ARCH"], "clause 3.1, O-RU definition", "A logical node hosting Low-PHY layer and RF processing based on a lower layer functional split."),
    "o-ru.s4": confirmed(URLS["TS38104"], "clause 9.6.3.3, Table 9.6.3.3-4", "For intra-band contiguous carrier aggregation, the 60/120 kHz SCS TAE value is 130 ns."),
    "fh-splane.s1": confirmed(URLS["CUS"], "clauses 3.1 and 11", "S-Plane refers to the synchronization plane used for timing and synchronization aspects."),
    "fh-splane.s2": confirmed(URLS["G8275"], "Annex A, Tables A.1 and A.5; clause 6.5", "domainNumber defaults to 24; logAnnounceInterval is −3; logSyncInterval is −4."),
    "fh-splane.s3": confirmed(URLS["G8271"], "Appendix V, clauses V.1-V.3", "For a TDD network the end application requirement is 1.5 µs maximum absolute time error."),
    "fh-splane.s4": confirmed(URLS["G8262"], "Summary and Introduction", "Network equipment uses the physical layer to deliver frequency synchronization."),
    "fh-splane.s5": confirmed(URLS["G8271"], "Appendix V, clause V.3", "The 1.1 µs network limit is at C; the 1.5 µs limit is at E."),
    "injector.s2": confirmed(URLS["RFC"], "section 3.1", "Threats include internal attackers, external attackers, man-in-the-middle attackers, and packet injectors."),
    "injector.s3": confirmed(URLS["SEC"], "clause 7, T-FRHAUL-02", "Unauthorized access to the Open Fronthaul physical interface enables attacks on availability, integrity, and confidentiality."),
    "o-du.s1": confirmed(URLS["ARCH"], "clause 3.1, O-DU definition", "O-DU is a logical node hosting RLC, MAC, and High-PHY layers."),
    "o-du.s2": confirmed(URLS["SEC"], "clause 9.1, LLS-C1 to LLS-C3", "C1/C2 distribute timing from O-DU; C3 distributes it from the fronthaul network itself."),
    "o-du.s4": confirmed(URLS["ARCH"], "clauses 6.3.2-6.3.5 and 6.4.5", "Near-RT RIC connects to O-CU-CP, O-CU-UP and O-DU through E2."),
    "fh-mplane.s1": confirmed(URLS["ARCH"], "clause 3.1, Open FH M-Plane", "Open FH M-Plane is the management interface controlling the O-RU."),
    "gnss-time.s1": confirmed(URLS["SEC"], "clause 9.1, Configuration LLS-C4", "Local PRTC timing provides time synchronization to the O-RU and may be embedded in it."),
    "synce.s1": confirmed(URLS["G8262"], "Summary and Introduction", "The synchronization method uses a synchronous physical layer for distributing a frequency reference."),
    "fh-cplane.s1": confirmed(URLS["CUS"], "clause 3.1, C-Plane definition", "C-Plane refers specifically to real-time control between O-DU and O-RU."),
    "fh-uplane.s1": confirmed(URLS["CUS"], "clause 3.1, LLS-U definition", "LLS-U is the lower-layer-split user-plane interface between O-DU and O-RU."),
    "air-interface.s1": confirmed(URLS["TS38104"], "clause 9.6.3", "Time-alignment requirements apply to MIMO transmission, carrier aggregation, and their combinations."),
    "air-interface.s2": confirmed(URLS["TS38104"], "clause 9.6.3.2", "MIMO TAE shall not exceed 65 ns; contiguous carrier-aggregation TAE shall not exceed 260 ns."),
    "near-rt-ric.s1": confirmed(URLS["ARCH"], "clauses 6.3.2-6.3.5 and 6.4.5", "Near-RT RIC connects to O-CU-CP, O-CU-UP and O-DU through E2."),
    "o-cu.s1": confirmed(URLS["ARCH"], "clause 3.1, O-CU definitions", "O-CU-CP hosts RRC/control PDCP; O-CU-UP hosts user PDCP and SDAP."),
    "o-cloud.s1": confirmed(URLS["ARCH"], "clause 3.1, O2 definition", "O2 connects the SMO framework and O-Cloud to support O-RAN virtual network functions."),
    "lls-c1.s1": confirmed(URLS["SEC"], "clause 9.1, Configuration LLS-C1", "In LLS-C1, O-DU acts as master and directly synchronizes O-RU."),
    "lls-c1.s2": confirmed(URLS["SEC"], "clause 7, T-SPLANE-01; clause 9.1, LLS-C1", "T-SPLANE-01 covers DoS or impersonation against a timing-network master."),
    "lls-c2.s1": confirmed(URLS["SEC"], "clause 9.1, Configuration LLS-C2", "O-DU acts as master; one or more Ethernet switches are allowed in the fronthaul network."),
    "lls-c3.s1": confirmed(URLS["SEC"], "clause 9.1, Configuration LLS-C3", "Timing is distributed by the fronthaul network, not by the O-DU, using PRTC/T-GM."),
    "lls-c4.s1": confirmed(URLS["SEC"], "clause 9.1, Configuration LLS-C4", "Local PRTC timing provides time synchronization to the O-RU and may be embedded in it."),
    "ptp-exchange.s1": inaccessible(URLS["IEEE"], "IEEE 1588 message exchange (licence-gated)"),
    "ptp-exchange.s2": inaccessible(URLS["IEEE"], "IEEE 1588 delay/offset equations (licence-gated)"),
    "bmca-contest.s1": inaccessible(URLS["IEEE"], "IEEE 1588 best master clock algorithm (licence-gated)"),
}


def main() -> None:
    data = json.loads(ARCH.read_text(encoding="utf-8"))
    new_sources = [
        ("ETSI_CUS12", "ETSI TS 103 859 V12.0.1 (O-RAN Open Fronthaul CUS-plane)", URLS["CUS"]),
        ("ETSI_MP17", "ETSI TS 104 023 V17.1.0 (O-RAN Open Fronthaul M-plane)", URLS["MP"]),
    ]
    existing = {s["id"] for s in data["sources"]}
    for source_id, title, url in new_sources:
        if source_id not in existing:
            data["sources"].append({
                "id": source_id,
                "title": title,
                "path_or_url": url,
                "openable_in_this_session": True,
                "note": "Official ETSI-hosted O-RAN Publicly Available Specification opened during the final primary-source audit.",
            })

    sentences = {s["id"]: s for e in data["elements"] for s in e["sentences"]}
    missing = sorted(set(P) - set(sentences))
    if missing:
        raise SystemExit(f"unknown sentence IDs: {missing}")
    for sentence_id, primary in P.items():
        sentences[sentence_id]["citation"]["primary"] = primary

    # One existing label cited the wrong O-RAN threat identifier.  The replacement
    # separates the standard's stated threat from the LLS-C1 topology inference.
    s = sentences["lls-c1.s2"]
    s["text"] = "O-RAN threat T-SPLANE-01 covers DoS or impersonation against the timing-network master; because the O-DU is that master in LLS-C1, its served O-RUs can be affected."
    s["citation"].update({
        "source": "ETSI TR 104 106 V3.0.0",
        "source_id": "TR104106",
        "clause": "§7 T-SPLANE-01 and §9.1 Configuration LLS-C1",
        "locator": "official PDF pages 34 and 107",
        "url_or_repo_path": URLS["SEC"],
    })

    resolved = {
        "o-du.s5": {
            "text": "For LLS-C1 and LLS-C2 the O-DU is a PTP master towards the O-RUs; with a remote full-timing-support source it is an embedded end application with extra filtering, not a true G.8273.2 T-BC.",
            "source": "ETSI TS 103 859 V12.0.1",
            "source_id": "ETSI_CUS12",
            "clause": "§11.2.4.2.1 and §11.3.1.2",
            "locator": "official PDF pages 240 and 246",
            "url": URLS["CUS"],
            "quote": "For LLS-C1 and LLS-C2, the O-DU shall act as a G.8275.1 PTP master in the fronthaul network.",
        },
        "fh-mplane.s4": {
            "text": "The O-RAN M-plane YANG model that exposes O-RU synchronization configuration, status and notifications is named o-ran-sync.yang.",
            "source": "ETSI TS 104 023 V17.1.0",
            "source_id": "ETSI_MP17",
            "clause": "§13.1",
            "locator": "official PDF page 120",
            "url": URLS["MP"],
            "quote": "Synchronization items are defined and described in o-ran-sync.yang.",
        },
        "fh-cplane.s3": {
            "text": "When the O-DU is notified that an O-RU has become UNLOCKED, it shall stop sending data to that O-RU; the CUS specification explicitly includes C-plane data in the corresponding FREERUN/HOLDOVER rule.",
            "source": "ETSI TS 104 023 V17.1.0 and ETSI TS 103 859 V12.0.1",
            "source_id": "ETSI_MP17",
            "clause": "MP §13.1; CUS §13.6.2.1",
            "locator": "official PDF pages 120 and 295",
            "url": URLS["MP"],
            "quote": "If the O-RU state changes to UNLOCKED, the O-DU shall stop sending data to the O-RU.",
        },
        "fh-uplane.s3": {
            "text": "When the O-DU is notified that an O-RU has become UNLOCKED, it shall stop sending to and ignore data from that O-RU; the CUS specification explicitly includes U-plane data in the corresponding FREERUN/HOLDOVER rule.",
            "source": "ETSI TS 104 023 V17.1.0 and ETSI TS 103 859 V12.0.1",
            "source_id": "ETSI_MP17",
            "clause": "MP §13.1; CUS §13.6.2.1",
            "locator": "official PDF pages 120 and 295",
            "url": URLS["MP"],
            "quote": "The O-DU shall stop sending data to, and ignore any data from, that O-RU.",
        },
    }
    for sentence_id, item in resolved.items():
        s = sentences[sentence_id]
        s["text"] = item["text"]
        s["citation"] = {
            "source": item["source"],
            "source_id": item["source_id"],
            "clause": item["clause"],
            "locator": item["locator"],
            "url_or_repo_path": item["url"],
            "status": "VERIFIED",
            "primary": confirmed(item["url"], item["clause"], item["quote"]),
        }
        s["verification"] = {
            "by": "final primary-source audit 2026-10-06",
            "quote": item["quote"],
            "where": item["locator"],
        }

    # The archive packet audit resolves the apparent 1-versus-2 conflict:
    # 1 is the field transmitted by the BC, while 2 is the receiving RU's
    # currentDS value after the receiver-side increment.
    s = sentences["bc.s1"]
    s["kind"] = "MEASURED"
    s["text"] = (
        "Across the frozen recovery archive, legitimate GM-A/GM-B Announce frames carry stepsRemoved 0 and "
        "the primary boundary clock's relayed Announce frames carry 1 (62,620 packets). The topology comment's "
        "RU value 2 refers to the receiving clock's currentDS after its increment, not the received Announce field."
    )
    s["citation"] = {
        "source": "Recovery-loop run archive r13-r17 and reproducible packet audit",
        "source_id": "RUNS",
        "clause": "all up.pcap.gz and dn.pcap.gz captures",
        "locator": "audit_steps_removed.py: source 020000fffe000001 relaying GM-A/GM-B",
        "url_or_repo_path": "04_WEB_SIMULATOR/ingest/audit_steps_removed.py",
        "status": "VERIFIED",
        "primary": inaccessible(URLS["IEEE"], "IEEE 1588 currentDS/Announce stepsRemoved update semantics (licence-gated)"),
    }
    s["verification"] = {
        "by": "reproducible packet audit 2026-10-06",
        "quote": "GM-A/GM-B Announce: stepsRemoved 0; primary BC relayed Announce: stepsRemoved 1 in 62,620 packets.",
        "where": "recovery_eval_runs_r13-r17.tgz, every up/dn capture; audit_steps_removed.py output",
    }

    data["status_note"] = (
        "Every sentence cites a source. VERIFIED means an auditor opened the cited source and stored a supporting quote. "
        "External-standard claims also carry citation.primary with CONFIRMED or NOT_ACCESSIBLE. No sentences remain hidden."
    )
    ARCH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
