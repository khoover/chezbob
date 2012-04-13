#!/bin/bash

export XAUTHORITY=~kiosk/.Xauthority
export DISPLAY=:0

for device_id in `xinput list | grep eGalax | tr -s ' ' | sed -e 's/=/\t/g' | cut -f 3`
do
    xinput set-int-prop ${device_id} "Evdev Axis Inversion" 8 1 0
done
