#!/usr/bin/perl -w

# bobmenu.pl
# 
# Main routine for Chez Bob.  First checks the kind of login (text or barcode)
# and calls the corresponding handler routine (kbd_login or barcode_login).
#
# Al Su (alsu@cs.ucsd.edu)
# 
# $Id: bobmenu.pl,v 1.24 2001-05-13 21:55:08 mcopenha Exp $
#

do 'bc_win.pl';
do 'bc_util.pl';
do 'snd_util.pl';
do 'kbd_win.pl';
do 'bob_db.pl';

$DLG = "/usr/bin/dialog";


$REVISION = q{$Revision: 1.24 $};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
} else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";

&bob_db_connect;

while (1) {
  my $logintxt = &login_win($REVISION);

  # Check if we're dealing with a regular username or a barcode
  if (&isa_barcode($logintxt)) {
    &barcode_login($logintxt);
  } elsif (isa_valid_username($logintxt)) {
    &kbd_login($logintxt);
  } else {
    &invalidUsername_win();
    next;
  } 
} 


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

  $txt = `cat /tmp/input.main`;
  system("rm -f /tmp/input.main");

  return $txt;
}


sub
barcode_login
{
  my ($logintext) = @_;

  $barcode = &preprocess_barcode($logintext); 
  my $userid = &bob_db_get_userid_from_barcode($barcode);
  if ($userid == -1) {
    &barcode_not_found;
  } else {
    &barcode_action_win($userid);
  }
}


sub
kbd_login
{
  my ($username) = @_;
  my $userid = &bob_db_get_userid_from_username($username);

  if ($userid == -1) {
    # New user!

    if (askStartNew_win($username) == -1) {
      # Canceled or refused
      return;
    }

    if (&initBalance_win($userid) < 0) {
      return;
    }
  }

  $pwd = &bob_db_get_pwd($userid);
  if (defined $pwd && &checkPwd($pwd, &guess_pwd_win()) == 0) {
    &invalidPassword_win();
    return;
  } else {
    &kbd_action_win($userid, $username);
  }
}
