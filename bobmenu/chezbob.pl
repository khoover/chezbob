#!/usr/bin/perl -w

# chezbob.pl
# 
# Main routine for Chez Bob.  There are currently three ways to log into 
# the system:
# 1. Buy with cash barcode: The user scans this barcode if they plan to
#    pay for their item with cash.  The user is then prompted to scan the 
#    barcode of the product they are purchasing, and the system updates 
#    the stock of that particular product.
# 2. Personal Barcode: The user scans his/her id card, or personal barcode.
# 3. Username: The user types in their standard username.
#
# $Id: chezbob.pl,v 1.10 2001-05-24 01:40:34 mcopenha Exp $
#

# Make sure Perl can find all of our files by appending INC with the 
# path to the 'chezbob' executable.
open(FILE, "which $0 |") || die "can't do which $0: $!\n";
my $fullpath = <FILE>;
close(FILE) || die "can't close\n";
$BOBPATH = substr($fullpath, 0, rindex($fullpath, '/'));
push(@INC, $BOBPATH);

$CASH_BARCODE = "888888";

require "login.pl";	# login_win
require "bob_db.pl";	# database routines
require "buyitem.pl";   # buy routines
require "dlg.pl";


$REVISION = q{$Revision: 1.10 $};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
} else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";
&bob_db_connect;
&speech_startup;

do {
  $logintxt = &login_win($REVISION);
} while ($logintxt eq "");

my $barcode = &preprocess_barcode($logintxt); 
if ($barcode eq $CASH_BARCODE) {
  &buy_with_cash();
} elsif (&isa_valid_user_barcode($barcode)) {
  my $username = &bob_db_get_username_from_userbarcode($barcode);
  if (defined $username) {
    &process_login($username, 0);
  } else {
    &user_barcode_not_found_win;
  }
} elsif (&isa_valid_username($logintxt)) {
  &process_login($logintxt, 1);
} else {
  &invalidUsername_win();
} 

&remove_tmp_files;
&speech_shutdown;
