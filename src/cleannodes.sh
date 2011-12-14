#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var 'export SUDO_ASKPASS=/bin/true && sudo -A sh -c "killall -9 python; rm concoord_log*; rm *-descriptor"'
done