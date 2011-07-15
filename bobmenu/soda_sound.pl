#!/usr/bin/perl -w
#
# Transfer a login from the Chez Bob machine to the soda machine.  This
# executable will attempt to contact the soda machine to perform a remote
# login.  The exit code is 0 for a successful transfer, and non-zero on error.
# Required command-line arguments: <login-name> <available-balance>
#
# Author: Michael Vrable <mvrable@cs.ucsd.edu>
# Date: March 2, 2006
# Ripped off for playing sounds by John McCullough on 3/23/2011
# give it a sound name, and if the sound server aggrees
# (purchased|negative_balance) then it will play it.

use strict;

my ($sound_name) = ($ARGV[0]);

if (!$sound_name) {
    exit 1;
}

system("ssh -oBatchMode=yes -l bob soda.ucsd.edu '/home/kiosk/sodafw/bin/ctool -send \"SOUND-PLAY|$sound_name\"' </dev/null");

exit 0
