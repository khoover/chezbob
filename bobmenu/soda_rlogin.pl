#!/usr/bin/perl -w
#
# Transfer a login from the Chez Bob machine to the soda machine.  This
# executable will attempt to contact the soda machine to perform a remote
# login.  The exit code is 0 for a successful transfer, and non-zero on error.
# Required command-line arguments: <login-name> <available-balance>
#
# Author: Michael Vrable <mvrable@cs.ucsd.edu>
# Date: March 2, 2006

use strict;

#sleep 1;
#exit 1;

# We connect to the soda machine and send a LOGIN message to the message bus.
# We should receive in response either LOGIN-SUCCEEDED or LOGIN-FAILED.  We
# assume failure after a several second timeout.
$SIG{ALRM} = sub { exit 1 };
alarm 5;

my ($name, $balance) = ($ARGV[0], $ARGV[1]);
if (!$name || !$balance) {
    exit 1;
}

open SSH, "ssh -oBatchMode=yes -l bob soda.ucsd.edu '/home/kiosk/sodafw/bin/ctool -send \"LOGIN|$name|$balance\" -monitor LOGIN-' </dev/null |";

while ($_ = <SSH>) {
    if ($_ =~ m/^LOGIN-SUCCEEDED/) {
        exit 0;
    }

    if ($_ =~ m/^LOGIN-FAILED/) {
        exit 1;
    }
}

exit 1;
