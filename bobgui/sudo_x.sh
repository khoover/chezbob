#!/bin/sh
# Author: jcm
# This puts your xauthority key into bob so that bob can run the app via
# sudo.
sudo -H -u bob xauth add :0 . `xauth list | cut -d\  -f5`
