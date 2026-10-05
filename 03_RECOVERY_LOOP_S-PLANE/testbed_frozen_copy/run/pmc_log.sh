#!/bin/bash
# Poll linuxptp management datasets per node for the duration of a run.
# Unlocks L3 portDS and L5 counters (sync_mismatch / followup_mismatch / *_timeout),
# which are the native replay and DoS detectors, plus the inputs A4 needs.
SC="$1"; DUR="$2"; OUT=/opt/sptb/cap/$SC; mkdir -p $OUT
NODES="gma gmb bc ru1 ru2 ru3"
DS="TIME_STATUS_NP CURRENT_DATA_SET PARENT_DATA_SET TIME_PROPERTIES_DATA_SET PORT_DATA_SET PORT_STATS_NP PORT_SERVICE_STATS_NP"
end=$(( $(date +%s) + DUR ))
: > $OUT/pmc.jsonl
while [ $(date +%s) -lt $end ]; do
  ts=$(date -u +%s.%N)
  for n in $NODES; do
    for d in $DS; do
      v=$(ip netns exec $n pmc -u -b 0 -s /var/run/p.$n "GET $d" 2>/dev/null | tr '\n' '|')
      [ -n "$v" ] && printf '{"t":%s,"node":"%s","ds":"%s","raw":"%s"}\n' \
        "$ts" "$n" "$d" "$(echo "$v" | sed 's/"/\\"/g')" >> $OUT/pmc.jsonl
    done
  done
  sleep 1
done
echo "pmc log: $(wc -l < $OUT/pmc.jsonl) records -> $OUT/pmc.jsonl"
