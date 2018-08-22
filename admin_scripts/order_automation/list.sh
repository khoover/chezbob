#!/bin/bash
set -eu

total=$(grep -cve '^$' order_estimate.txt)

i=1
xdotool selectwindow windowfocus "%1"
while read -r line
do
  if [[ -z $line ]]; then
    continue
  fi
  qty=$(echo "$line" | cut -d' ' -f1)
  name=$(echo "$line" | cut -c6-)
  itemNo=$(echo "$line" | cut -c6- | grep -Po '(?<=\(#)(\d+)')
  echo "  ($i/$total)  $qty of $itemNo - $name"
  xdotool type "$itemNo"
  xdotool key Tab
  xdotool type "$qty"
  xdotool key Tab
  xdotool key Tab
  if (( i % 20 == 0 )); then
    read -u 3
    xdotool selectwindow windowfocus "%1"
  fi
  let "i++"
done < order_estimate.txt 3>&1
