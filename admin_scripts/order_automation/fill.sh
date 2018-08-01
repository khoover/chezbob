#!/bin/bash
set -eu

USERNAME=$(head creds.txt -n 1)
PASSWORD=$(tail creds.txt -n +2)

xdotool selectwindow windowfocus "%1" type "$USERNAME"
xdotool key Tab
xdotool type "$PASSWORD"
xdotool key Tab
xdotool type "92093"
xdotool key Return
