#!/usr/bin/perl -w

# bobmenu.pl
# 
# Main routine for Chez Bob.  
#
# Al Su (alsu@cs.ucsd.edu)
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
# 
# $Id: chezbob.pl,v 1.1 2001-05-18 05:41:44 mcopenha Exp $
#

require "login.pl";	# login_win
require "bob_db.pl";	# database routines


$REVISION = q{$Revision: 1.1 $};
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

# Check if we're dealing with a user barcode or regular username
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
system("rm -f input.*");
system("rm -f *.output.log");
system("rm -f menuout");


