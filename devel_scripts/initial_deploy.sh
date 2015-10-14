#!/bin/bash
set -eu

function error {
  echo $1
  exit -1
}

if [[ $# -ne 3 ]] ; then
  echo $#
  error "Usage: $0 <ip> <remote-user> <devel-db>"
fi

IP=$1
REMOTE_USER=$2
PATH_TO_DEVEL_DB=$3
LOCAL_USER=`whoami`
LOCAL_USER_SSH_KEY=/home/$LOCAL_USER/.ssh/id_rsa.pub
PATH_TO_REPO="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

cat > /tmp/soda-dev-hosts <<EOL
[soda-dev-machines]
$IP
EOL

ansible-playbook -Kk -i /tmp/soda-dev-hosts -s -vvvv -u $REMOTE_USER $PATH_TO_REPO/ansible/dev.yml --extra-vars "REMOTE_USER=$REMOTE_USER LOCAL_USER=$LOCAL_USER LOCAL_USER_SSH_KEY=$LOCAL_USER_SSH_KEY PATH_TO_REPO=$PATH_TO_REPO DEVEL_DB=$PATH_TO_DEVEL_DB"
