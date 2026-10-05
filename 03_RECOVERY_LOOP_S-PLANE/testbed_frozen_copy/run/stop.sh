#!/bin/bash
SC="${1:-baseline}"; OUT=/opt/sptb/cap/$SC
for n in gma gmb bc ru1 ru2 ru3; do [ -f $OUT/$n.pid ] && kill $(cat $OUT/$n.pid) 2>/dev/null; done
sleep 1; for p in tcpu tcpd; do [ -f $OUT/$p.pid ] && kill $(cat $OUT/$p.pid) 2>/dev/null; done
sleep 1; pkill -f "ptp4l -f /opt/sptb" 2>/dev/null; echo "stopped $SC"
