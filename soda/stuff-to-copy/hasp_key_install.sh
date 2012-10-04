#!/bin/bash
#cp aksusbd /usr/local/bin/aksusbd
cd hasp_key
tar -xzf HDD_Linux_USB_dinst.tar.gz
tar -xzf HDD_Linux_USB_daemon.tar.gz
cp HDD_Linux_USB_daemon/aksusbd HDD_Linux_USB_dinst/
cd HDD_Linux_USB_dinst
./dinst .
cd ..
rm -rf HDD_Linux_USB_daemon
rm -rf HDD_Linux_USB_dinst
