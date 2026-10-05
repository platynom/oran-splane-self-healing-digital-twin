#!/bin/bash
# usage: devrun.sh SC REP ARM
pkill -x ptp4l; pkill -x tcpdump; true
rm -rf /opt/sptb/cap/$1__r$2__$3
cd /opt/sptb/recovery && python3 run_one.py "$1" "$2" "$3"
