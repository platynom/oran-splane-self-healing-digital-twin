# S14 Broader Software Experiment and Recovery Report

## 1. Executive Summary

This report evaluates the S14 prospective broader software validation batch comprising 25 independent trials across 5 frozen experimental conditions. All 25 runs completed with verified cryptographic manifest integrity, zero post-seal decision appending, and zero non-zero process exits.

## 2. Frozen Input Verification

| Component | Expected / Recorded SHA-256 | Verification |
|---|---|---|
| V1 Engine | `1c1d7edfbcc38b6e0c950984eff72b58592160c71ad8e797ff719d4aee0b8d0e` | PASS |
| V3 Nonoverlap Engine | `ee328876367e6547878f85eed60405624f55bd21a03348f4d9527fd302250172` | PASS |
| Live Detector | `897ed8833e5c5615acf2d725add0da0282a65ce9067a0793c1b9117077bcec84` | PASS |
| Writer Drain/Seal v2 | `da37664ae2d8adbbd3a3a90d266c5eee64736bca64a52e5b5b746ccb2111f0a7` | PASS |
| Trial Runner v2 | `ec41100827495c39ba6c609c5f21416d4421c43e5a1969abb8933766626e22d7` | PASS |
| Batch Runner | `8194c43115fdc6723795cfe033e99589a7ba27dd318a6209d68caa9eb7c38a71` | PASS |

## 3. Classification Performance Across Broader Conditions

| Condition | Configured Setting | Target Arm | Runs ($n$) | Triggers ($k$) | Trigger Rate | Wilson 95% CI | Policy Classification |
|---|---|---|---|---|---|---|---|
| `baseline_clean` | none | `no_action` | 5 | 0 | 0/5 (0.0%) | [0.0, 0.4345] | BENIGN_WITHIN_POLICY |
| `benign_delay_jitter` | delay 100us 20us distribution normal | `no_action` | 5 | 0 | 0/5 (0.0%) | [0.0, 0.4345] | BENIGN_WITHIN_POLICY |
| `jitter_fault_action` | delay 100us 200us distribution normal | `action` | 5 | 5 | 5/5 (100.0%) | [0.5655, 1.0] | HARMFUL_UNDER_POLICY |
| `jitter_fault_no_action` | delay 100us 200us distribution normal | `no_action` | 5 | 5 | 5/5 (100.0%) | [0.5655, 1.0] | HARMFUL_UNDER_POLICY |
| `authorized_source_failover` | none (clean master A termination) | `no_action` | 5 | 0 | 0/5 (0.0%) | [0.0, 0.4345] | BENIGN_WITHIN_POLICY (no false jitter trigger) |

### Key Classification Findings:
- **Specificity:** Across 15 non-jitter control trials (`baseline_clean`, `benign_delay_jitter`, `authorized_source_failover`), exactly 15/15 trials remained free of false anomaly triggers (Specificity: 100.0%, Wilson 95% CI: [0.7961, 1.0]). False alarms: 0.
- **Sensitivity:** Across 10 jitter fault trials (`jitter_fault_action`, `jitter_fault_no_action`), the detector triggered in 10/10 trials (Sensitivity: 100.0%, Wilson 95% CI: [0.7225, 1.0]).

## 4. Closed-Loop Recovery Outcomes Against Matched Controls

| Arm | Configured Impairment | Commanded Action | Runs ($n$) | Standby Port Takeover ($k$) | Success Rate | Wilson 95% CI |
|---|---|---|---|---|---|---|
| `jitter_fault_action` | Delay 100 us, Jitter 200 us | `ip link set <seg1> down` | 5 | 5 | 100.0% | [0.5655, 1.0] |
| `jitter_fault_no_action` | Delay 100 us, Jitter 200 us | Action withheld | 5 | 0 | 0.0% | [0.0, 0.4345] |

### Recovery Outcome Separation:
- In 100% of eligible action trials, receiver logs demonstrate the primary port faulted followed by clean standby takeover on Segment 2.
- In 0% of matched no-action control trials did the receiver move to the clean segment, proving that failover is strictly caused by the detector's commanded action and not by impairment exposure or elapsed time.

## 5. Input Integrity and Writer Drain/Seal Verification

- **Manifest Rehash:** All manifested files across all 25 runs were recomputed from disk and verified against `source_manifest.sha256` with 0 mismatches.
- **Post-Seal Appending Defect Resolution:** All `decision_log.jsonl` files exactly match their sealed manifest hashes. The graceful FIFO drain on EOF resolved the post-seal append defect.
- **Writer Exit Codes:** All direct child processes in all 25 runs exited with code `0` recorded in `writer_exit_status.tsv`.

## 6. Software Boundaries and Non-Claims

1. All experiments ran in isolated Linux network namespaces with `free_running 1`. Clock adjustment was disabled; no physical oscillator phase or frequency synchronization is claimed.
2. The self-healing action commands the receiver to drop the impaired timing segment; it does not repair the physical network or undo the impairment.
3. Observations establish software-level protocol agility and packet dispersion discrimination only.
