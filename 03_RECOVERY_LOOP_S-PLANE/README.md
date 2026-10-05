# 03_RECOVERY_LOOP_S-PLANE — automated recovery for the Open Fronthaul S-plane

Built on 5 Oct 2026. Kept in its own folder so that the presented deck (v7), the current deck (v8), the 168-run campaign evidence and the 29 Sep document set stay untouched.

## What this is

A closed loop that **detects, localises, decides, acts, verifies and rolls back**, running on the same software G.8275.1 testbed as the 168-run campaign.
- **Detector:** the campaign's frozen decision rule, unchanged and hash-checked at start-up.
- **Actions:**
  - isolate the offending ingress port (PTP only);
  - fail over to a standby boundary clock when timing is removed;
  - tolerate benign faults;
  - escalate when intent is unknown.
- **Standards basis:** each action is mapped to a standard in `RECOVERY_LOOP_DESIGN.md` and `STANDARDS_EVIDENCE.md`.

## Read in this order

1. `RESULTS_2026-10-05.md` — what was measured, against the pre-registered criteria
2. `RECOVERY_LOOP_DESIGN.md` — architecture, the two detection channels, the policy table, limits
3. `PREREGISTRATION.md` — hypotheses and pass criteria, frozen before the evaluation runs
4. `STANDARDS_EVIDENCE.md` — quotes and URLs behind every action, with verification level
5. `code/` — the loop and the run harness; `code/FROZEN_RL.json` holds the freeze hashes
6. `testbed_frozen_copy/` — the unchanged campaign harness the loop runs on (hashes in `HASHES.txt`)
7. `results/` — every evaluation run (replicates 13–17) and the development runs (replicate 101), archived

## How to re-run (Linux, root, linuxptp 4.0, iproute2, nftables, tcpdump, tcpreplay, python3-scapy)

```
sudo mkdir -p /opt/sptb && sudo cp -r testbed_frozen_copy/* /opt/sptb/ && sudo cp -r code /opt/sptb/recovery && sudo cp PREREGISTRATION.md /opt/sptb/recovery/
cd /opt/sptb/recovery
sudo python3 freeze.py --verify          # must print nothing
sudo ./devrun.sh A1_rogue_master 13 loop # one run, about 70 s
sudo ./campaign.sh                       # full 140-run evaluation, about 2.8 h
python3 analyse.py /opt/sptb/cap out.json 13,14,15,16,17
```

The harness never touches the host clock. Every daemon runs with `free_running 1` and software timestamping, inside network namespaces.
