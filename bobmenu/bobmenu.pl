#!/usr/bin/perl -w

# bobmenu.pl
# 
# Main routine for Chez Bob.  First checks the kind of login (text or barcode)
# and calls the corresponding handler routine (kbd_login or barcode_login).
#
# Al Su (alsu@cs.ucsd.edu)
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
# 
# $Id: bobmenu.pl,v 1.28 2001-05-15 00:18:05 mcopenha Exp $
#

require "bc_win.pl";	# barcode login windows
require "kbd_win.pl";	# keyboard login windows
require "bc_util.pl";	# barcode utils
require "snd_util.pl";	# speech utils
require "bob_db.pl";	# database routines

my $DLG = "/usr/bin/dialog";
$CANCEL = -1;


$REVISION = q{$Revision: 1.28 $};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
} else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";

&bob_db_connect;

# First assume the input is a barcode and try a lookup.  If the lookup 
# fails assume the input is a regular username.
my $logintxt = &login_win($REVISION);
my $barcode = &preprocess_barcode($logintxt); 
my $userid = &bob_db_get_userid_from_barcode($barcode);
if ($userid == $NOT_FOUND) {
  if (isa_valid_username($logintxt)) {
    &kbd_login($logintxt);
  } else {
    &invalidUsername_win();
  }
} else {
  &barcode_login($userid);
}

# Make sure any temp input files are gone. We can run into permission
# problems if multiple people are trying to run Bob on the same system.
system("rm -f /tmp/input.*");


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

  system("$DLG --title \"$win_title\" --clear --inputbox \"" .
         $win_text .  "\" 14 55 \"$username\" 2> /tmp/input.main");

  return `cat /tmp/input.main`;
}


sub
barcode_login
{
  my ($userid) = @_;
  my $username = &bob_db_get_username_from_userid($userid);
  &barcode_action_win($userid, $username);
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
