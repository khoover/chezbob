#!/usr/bin/perl -w

# bobmenu.pl
# 
# Main routine for Chez Bob.  
#
# Al Su (alsu@cs.ucsd.edu)
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
# 
# $Id: bobmenu.pl,v 1.33 2001-05-17 23:23:38 mcopenha Exp $
#

require "bc_win.pl";	# barcode login windows
require "kbd_win.pl";	# keyboard login windows
require "bc_util.pl";	# barcode utils
require "snd_util.pl";	# speech utils
require "bob_db.pl";	# database routines

my $DLG = "./bobdialog";
my $NOT_FOUND = -1;
$CANCEL = -1;


$REVISION = q{$Revision: 1.33 $};
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
    &kbd_login($username);
  } else {
    &user_barcode_not_found_win;
  }
} elsif (&isa_valid_username($logintxt)) {
  &kbd_login($logintxt);
} else {
  &invalidUsername_win();
} 

# Make sure any temp input files are gone. We can run into permission
# problems if multiple people are trying to run Bob on the same system.
system("rm -f input.*");
system("rm -f *.output.log");
system("rm -f menuout");


sub
login_win
{
  my ($rev) = @_;

  my $username = "";
  my $win_title = "Bank of Bob 2001 (v.$rev)";
  my $win_text = q{
Welcome to the B.o.B. 2K!


Enter your username or scan your personal barcode. 
(If you are a new user enter a new username):
};

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
         $win_text .  "\" 14 55 \"$username\" 2> input.main") != 0) {
    return "";
  }

  return `cat input.main`;
}


sub
kbd_login
{
  my ($username) = @_;
  my $userid = &bob_db_get_userid_from_username($username);

  if ($userid == $NOT_FOUND) {
    # New user!

    if (&askStartNew_win($username) == $CANCEL) {
      return;
    }

    # Get the new userid
    $userid = &bob_db_get_userid_from_username($username);
    &bob_db_init_balance($userid);
  }

  $pwd = &bob_db_get_pwd($userid);
  if (defined $pwd && &checkPwd($pwd, &guess_pwd_win()) == 0) {
    &invalidPassword_win();
  } else {
    &kbd_action_win($userid, $username);
  }
}
