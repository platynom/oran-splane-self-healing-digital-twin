#!/usr/bin/env bash
# Frozen V3 order; execute only inside the disposable WSL testbed as root.
set -euo pipefail
ROOT="outputs/empirical_software_network_pilot_v1/v3_runs"
RUNNER="01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_empirical_software_pilot.sh"
run() { PILOT_DURATION_SECONDS=8 bash "$RUNNER" --execute "$ROOT/$3" "$1" "$2"; }
run w3b1 baseline_control 20260913_v3_b1
run w3n1 netem_delay_jitter_loss 20260913_v3_n1
run w3c1 authorized_source_change_no_action_control 20260913_v3_c1
run w3s1 authorized_source_change_intervention 20260913_v3_s1
run w3b2 baseline_control 20260913_v3_b2
run w3n2 netem_delay_jitter_loss 20260913_v3_n2
run w3c2 authorized_source_change_no_action_control 20260913_v3_c2
run w3s2 authorized_source_change_intervention 20260913_v3_s2
run w3b3 baseline_control 20260913_v3_b3
run w3n3 netem_delay_jitter_loss 20260913_v3_n3
run w3c3 authorized_source_change_no_action_control 20260913_v3_c3
run w3s3 authorized_source_change_intervention 20260913_v3_s3
run w3b4 baseline_control 20260913_v3_b4
run w3n4 netem_delay_jitter_loss 20260913_v3_n4
run w3c4 authorized_source_change_no_action_control 20260913_v3_c4
run w3s4 authorized_source_change_intervention 20260913_v3_s4
run w3b5 baseline_control 20260913_v3_b5
run w3n5 netem_delay_jitter_loss 20260913_v3_n5
run w3c5 authorized_source_change_no_action_control 20260913_v3_c5
run w3s5 authorized_source_change_intervention 20260913_v3_s5
