#!/usr/bin/env python3
"""Verify that every CONFIRMED audit row has a searchable stored-source anchor."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
STD = ROOT / "01_CURRENT_SPlane_SelfHealing" / "literature-survey" / "papers" / "Standards"
AUDIT = ROOT / "CITATION_VERIFICATION_2026-11.md"

RFC = "RFC7384.txt"
TR106 = "ETSI_TR_104106_V3.0.0.pdf"
TS105 = "ETSI_TS_104105_V7.0.0.pdf"
ARCH = "ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf"
NGRAN = "ETSI_TS_138401_NG-RAN_Architecture_R18.pdf"
CUS = "ETSI_TS_103859_O-RAN_CUS_v12.0.1.pdf"
RAN104 = "ETSI_TS_138104_Rel19_v19.2.0.pdf"
ARM = "Armstrong_ORAN_Fundamentals_WSTS_2023.pdf"
RUFF = "Ruffini_Sync_for_5G_ATIS_2018.pdf"
TIME = "TIMESAFE_arXiv_2412.13049v3.pdf"
BSI = "BSI_5G_RAN_Risk_Analysis.pdf"
G82711 = "ITU_T_G.8271.1_2022.pdf"
G82751 = "ITU_T_G.8275.1_2026.pdf"
G82732 = "ITU_T_G.8273.2_2023.pdf"
G8262 = "ITU_T_G.8262_2024.pdf"
G8261 = "ITU_T_G.8261_2019.pdf"
PROFILES = "IEEE_1588_PTP_Profiles.html"
PMC = "linuxptp_v4.0_pmc.8"


# Short exact anchors are intentionally used: PDF extraction can join visual line breaks,
# while these strings remain specific enough to prove that the cited passage is present.
CHECKS: dict[str, tuple[str, str]] = {
    "S04-01": (ARCH, "The Open FH (Fronthaul) Interface is between O-DU and O-RU functions"),
    "S04-02": (CUS, "specifies the control plane, user plane and synchronization plane protocols"),
    "S04-03": (NGRAN, "The NG-RAN consists of a set of gNBs connected to the 5GC"),
    "S05-01": (ARCH, "A logical node hosting Low-PHY layer and RF processing"),
    "S05-02": (NGRAN, "describes the overall architecture of the NG-RAN"),
    "S05-03": (RUFF, "shall be better than 3 µs"),
    "S05-04": (RAN104, "OTA TAE shall not exceed 65 ns"),
    "S06-01": (ARM, "Configuration LLS-C1: the O-DU is part of the synchronization chain"),
    "S06-03": (TIME, "an attacker compromises a device on the network"),
    "S06-04": (TIME, "with an O-RAN LLS-C3 configuration"),
    "S06-05": (RFC, "Grandmasters receive their time from an external accurate time source"),
    "S06-06": (BSI, "auxiliary GNSS receivers deployed in a network can be targets of jamming attacks"),
    "S07-01": (ARM, "TAE down to 130 ns between clusters of RUs"),
    "S07-02": (G82711, "max|TEL| ≤ 1 100 ns"),
    "S07-03": (TIME, "Approximately 2 seconds after the attack begins, the RU crashes"),
    "S08-02": (G82751, "it outputs clockClass 6"),
    "S08-03": (TR106, "A Rogue PTP Instance wanting to be a Grand Master"),
    "S09-01": (TR106, "Cyber-terrorists"),
    "S09-02": (RFC, "Internal attackers either have access to a trusted segment"),
    "S09-03": (TR106, "Unauthorized access to Open Front Haul Ethernet L1 physical layer interface"),
    "S10-01": (RFC, "A traffic injector is not located in an MITM position"),
    "S11-01": (RFC, "an attacker causes other nodes in the network to believe it is a legitimate master"),
    "S11-02": (RFC, "an injector masquerades as a legitimate node"),
    "S11-03": (RFC, "records protocol packets and replays them at a later time"),
    "S11-04": (RFC, "sending an excessive number of time protocol packets"),
    "S11-05": (RFC, "intercepts and drops protocol packets"),
    "S11-06": (TR106, "Selective interception and removal of PTP timing packets"),
    "S11-07": (TS105, "S-Plane PTP Unexpected Input"),
    "S11-08": (TIME, "Spoofing AttackandReplay Attack"),
    "S12-01": (RFC, "Accuracy|    |"),
    "S12-02": (TR106, "potentially bringing down the cell"),
    "S12-03": (TIME, "the RU required a manual reboot"),
    "S12-04": (RUFF, "shall be better than 3 µs"),
    "S12-05": (RAN104, "OTA TAE shall not exceed 260 ns"),
    "S16-02": (CUS, "S-Plane: Synchronization Plane"),
    "S16-03": (TR106, "Threat ID T-SPLANE-04"),
    "S16-04": (G82751, "default PTP domain number is 24"),
    "S16-05": (G82732, "telecom boundary clock (T-BC) and telecom time"),
    "S16-06": (G8262, "Timing characteristics of synchronous equipment clocks"),
    "S20-02": (PMC, "Specify the domain number in sent messages"),
    "S20-03": (ARCH, "The O-RU terminates the Open Fronthaul interface"),
    "S21-02": (G82751, "range of applicable PTP domain numbers is {24 – 43}"),
    "S24-02": (TS105, "Rogue PTP Instance"),
    "S25-02": (G82751, "Announce messages – nominal rate: 8 packets per second"),
    "S25-03": (TR106, "DoS attack against a Master clock"),
    "S26-01": (TS105, "Selective Interception and Removal of PTP Timing Packets"),
    "S26-03": (TR106, "A Rogue PTP Instance wanting to be a Grand Master"),
    "S27-01": (G82751, "in holdover, but within holdover specification"),
    "S27-03": (G8261, "performance is impacted by packet delay variation"),
    "S40-01": (PROFILES, "Power Profile"),
    "S40-02": (RFC, "Precision Time Protocol (PTP) and the Network Time Protocol (NTP)"),
    "S40-03": (G82751, "This Alternate BTCA differs from the default BTCA"),
    "D01": (RFC, "authorized to be a master"),
    "D02": (RFC, "every protocol packet received from an unsecured clock MUST be discarded"),
    "D03": (RFC, "SHOULD include measures to mitigate DoS attacks against the time protocol"),
    "D07": (RFC, "protect the protocol from MITM attacks that degrade the clock accuracy"),
    "D08": (RFC, "use redundant masters"),
    "D09": (TIME, "Network redundancy, as suggested in Prong C"),
    "D12": (G82751, "clockClass 135"),
    "D13": (G82711, "Rearrangements and short-term holdover in the end application"),
    "D14": (TIME, "we propose a monitoring system (Prong D)"),
    "D15": (PMC, "Specify the domain number in sent messages"),
    "D16": (TS105, "11.1.5.2.2 Rogue PTP Instance"),
}


def normalize(value: str) -> str:
    value = value.replace("\u00ad", "").replace("’", "'").replace("‘", "'")
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", value).strip().casefold()


def read_source(path: Path) -> str:
    if path.suffix.casefold() == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    audit_text = AUDIT.read_text(encoding="utf-8")
    confirmed = set(
        re.findall(r"^\|\s*([A-Z0-9-]+)\s*\|.*\|\s*CONFIRMED\s*\|$", audit_text, flags=re.MULTILINE)
    )
    failures: list[str] = []
    if confirmed != set(CHECKS):
        failures.append(
            f"audit/check-map mismatch: missing={sorted(confirmed - set(CHECKS))}, "
            f"extra={sorted(set(CHECKS) - confirmed)}"
        )

    cache: dict[str, str] = {}
    for citation_id in sorted(confirmed & set(CHECKS)):
        filename, anchor = CHECKS[citation_id]
        path = STD / filename
        if not path.is_file():
            failures.append(f"{citation_id}: missing source {path.relative_to(ROOT)}")
            continue
        if filename not in cache:
            cache[filename] = normalize(read_source(path))
        if normalize(anchor) not in cache[filename]:
            failures.append(f"{citation_id}: anchor not found in {filename}: {anchor!r}")

    print(f"CONFIRMED citations checked: {len(confirmed)}")
    print(f"Stored source files searched: {len(cache)}")
    print(f"Mismatches: {len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
