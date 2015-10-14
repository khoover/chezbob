#!/bin/bash
set -eu

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function error {
  echo $1
  exit -1
}

if [[ $# -ne 1 ]] ; then
  error "Usage: $0 <vm-name>"
fi

logF=deploy.log

function log {
  echo $1 >> $logF
}

function getIP {
  VM=$1
  IPProp=`vboxmanage guestproperty get $VM /VirtualBox/GuestInfo/Net/1/V4/IP`
  if [[ $IPProp =~ ^Value:\ [0-9\.]*$ ]] ; then
    echo $IPProp | sed 's/Value: \([0-9\.]*\)/\1/'
  else
    echo ""
  fi
}

function getIPOrWait {
  VM=$1
  until [[ `getIP $VM` =~ ^[0-9\.][0-9.]*$ ]];
     do
       log "IP Currently: `getIP $VM`"
       sleep 1;
     done
  echo `getIP $VM`
}

VM=$1

log "Restoring blank snapshot of VM $VM"
vboxmanage snapshot $VM restore blank

log "Starting VM $VM"
vboxmanage startvm $VM

log "Waiting to obtain IP of $VM"
IP=`getIPOrWait $VM`
log "VM IP is $IP"

log "Waiting for SSH to come up..."
until [[ 1 == 0 ]]
do
  log "Checking port 22..."
  nc -z $IP 22
  if [[ $? -eq 0 ]] ; then
    break;
  fi
  sleep 1;
done

$DIR/initial_deploy.sh $IP dev $DIR/bob_devel.sql
