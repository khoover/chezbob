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
# $Id: chezbob.pl,v 1.4 2001-05-21 21:20:08 mcopenha Exp $
#

# Make sure Perl can find all of our files by appending INC with the 
# path to the 'chezbob' executable.
open(TMP, "which $0 |") || die "can't do which $0: $!\n";
my $fullpath = <TMP>;
close(TMP) || die "can't close\n";
$BOBPATH = substr($fullpath, 0, rindex($fullpath, '/'));
push(@INC, $BOBPATH);

require "login.pl";	# login_win
require "bob_db.pl";	# database routines


$REVISION = q{$Revision: 1.4 $};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
} else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";
&bob_db_connect;

do {
  $logintxt = &login_win($REVISION);
} while ($logintxt eq "");

my $barcode = &preprocess_barcode($logintxt); 
if (&isa_valid_user_barcode($barcode)) {
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

# Remove any temp input files 
system("rm -f /tmp/input.*");
system("rm -f /tmp/*.output.log");
system("rm -f /tmp/menuout");


