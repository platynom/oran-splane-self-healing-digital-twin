#!/bin/bash
# Pre-registered evaluation campaign: replicates 13-17, 14 scenarios, 2 arms (see PREREGISTRATION.md).
# Verifies the freeze before every run; any mismatch aborts.
SCS="baseline A1_rogue_master A2_sync_spoof A3_replay A5_dos_flood A8_rogue_bc C1_removal C2_malformed C3_wholesecond B2_gm_failover B3_pdv_congestion B7_topology_change B_bc_replacement B_unplanned_failover"
cd /opt/sptb/recovery
for rep in 13 14 15 16 17; do
  if [ $((rep % 2)) -eq 1 ]; then ARMS="control loop"; else ARMS="loop control"; fi
  for sc in $SCS; do for arm in $ARMS; do
    python3 freeze.py --verify || { echo "FREEZE MISMATCH - ABORT"; exit 3; }
    echo "$(date -u +%FT%TZ) start $sc r$rep $arm"
    ./devrun.sh $sc $rep $arm
  done; done
done
echo CAMPAIGN_DONE
