#!/bin/bash
# usage: batch.sh REPLIST "SC1 SC2 ..." "ARM1 ARM2"
for rep in $1; do for sc in $2; do for arm in $3; do
  /opt/sptb/recovery/devrun.sh $sc $rep $arm
done; done; done
echo BATCH_DONE
