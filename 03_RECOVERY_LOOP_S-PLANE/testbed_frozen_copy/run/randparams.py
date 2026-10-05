#!/usr/bin/env python3
"""Per-replicate randomised attack/benign parameters, seeded reproducibly by rep number.

WHY. The prior campaign had ZERO randomisation: 5 attack designs repeated 9 times
identically, so the 45 runs were not 45 independent samples. The honest effective n was
~5 and the reported Wilson CIs were optimistic (the deliverable disclosed this). This file
makes each replicate a genuinely different instance of the same attack CLASS, so that a
correct verdict across reps is evidence of generalisation, not of repetition.

Every value is drawn from random.Random(rep) so a rep is fully reproducible from its number
alone. The randomisation is DELIBERATELY WITHIN the class definition - e.g. a rogue master
always uses an off-allow-list identity and a superior priority, but WHICH identity and HOW
superior vary. It never changes ground truth.
"""
import sys, json, random

def params(rep: int) -> dict:
    r = random.Random(rep)
    # a random locally-administered off-allow-list identity (02....fffe.RRRRRR), never the
    # provisioned 0a/0b/0c/0d/0e/01
    def off_id():
        while True:
            suf = r.randint(0x20, 0xfe)
            if suf not in (0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x01):
                return f"020000fffe0000{suf:02x}", f"02:00:00:00:00:{suf:02x}"
    rogue_id, rogue_mac = off_id()
    inj_id, _ = off_id()
    bc_id, bc_up_mac = off_id(); _, bc_dn_mac = off_id()
    return {
        "rep": rep,
        # A1 rogue master: identity, and a SUPERIOR priority2 (lower = better; legit best is 100)
        "rogue_id": rogue_id, "rogue_mac": rogue_mac,
        "rogue_priority2": r.choice([1, 5, 10, 20, 50, 90]),
        "rogue_clockclass": r.choice([6, 6, 6, 7, 13]),   # all "attractive"; mostly locked-eligible
        # A2 sync spoof: forged source id + a random implausible future-seconds value
        "inject_id": inj_id,
        "inject_seconds": r.choice([0x7FFFFFFF, 0x70000000, 0x60000000, 0x50000000]),
        "inject_burst": r.choice([4, 6, 8, 10]),
        "inject_gap_ms": r.choice([40, 60, 80, 100]),
        # A5 flood: rate and burst
        "flood_burst": r.choice([100, 150, 200, 300]),
        "flood_gap_ms": r.choice([30, 50, 70]),
        "flood_src": off_id()[1],
        # A3 replay: loop count and captured-slice size
        "replay_loops": r.choice([4, 6, 8, 10]),
        "replay_count": r.choice([300, 400, 500]),
        # A8 rogue BC: two identities + priority2
        "rbc_id_up": bc_id, "rbc_up_mac": bc_up_mac, "rbc_dn_mac": bc_dn_mac,
        "rbc_priority2": r.choice([105, 110, 115, 118]),
        # B3 congestion: jitter magnitude (still benign - no protocol anomaly)
        "pdv_delay_ms": r.choice([3, 5, 8]), "pdv_jitter_ms": r.choice([2, 3, 4]),
        # timing jitter: when in the run the fault is introduced (seconds after start)
        "onset_jitter_s": r.choice([-3, -2, 0, 2, 3]),
        # C1 removal: fraction of the post-warmup window the BC->RU path is blackholed
        "c1_down_pct": r.choice([55, 60, 65, 70, 75]),
        # C2 malformed: injected inter-frame gap (ms) -> varies count
        "c2_gap_ms": r.choice([80, 100, 125, 150]),
        # C3 whole-second: injected Announce gap (ms)
        "c3_gap_ms": r.choice([100, 125, 150, 200]),
    }

if __name__ == "__main__":
    print(json.dumps(params(int(sys.argv[1])), indent=2))
