# passwd.pl
#
# Routines for updating and checking user passwords
# 
# $Id: passwd.pl,v 1.6 2001-06-25 21:41:37 bellardo Exp $
#

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

sub
guess_pwd_win
{
  my $win_title = "Enter password";
  my $win_text = "Enter your password:";
  my ($err, $pass) = &get_dialog_result("--title \"$win_title\" --clear " .
                  "--passwordbox \"" .  $win_text .  "\" 8 45");

  return undef if ($err != 0);
  return $pass;
}


sub
invalidPassword_win
{
  my $win_title = "Wrong password";
  my $win_text = "\nWrong password entered!\n";
  &get_dialog_result("--title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 7 30");
}


sub
pwd_win
{
  my ($userid) = @_;
  my $win_title = "Enter Password";
  my $win_text = q{
Type your new password.  To remove an existing
password do not enter any text.};

  my $verify_win_text = q{
Re-type your password:};

  my $passwd = &bob_db_get_pwd($userid);
  if (defined $passwd) {
    $salt = substr($passwd, -2, 2);
    $pwd_exists = 1;
  } else {
    $salt = "cB";
    $pwd_exists = 0;
  }

  my ($err, $p) = &get_dialog_result("--title \"$win_title\" --clear " .
             "--cr-wrap --passwordbox \"" .  $win_text .  "\" 10 50");
  return $CANCEL if ($err != 0);

  if ($p eq "") {
    &bob_db_remove_pwd($userid);
    return;
  }

  ($err, my $p_v) = &get_dialog_result("--title \"$win_title\" --clear " .
             "--passwordbox \"" .  $verify_win_text .  "\" 9 50");
  return $CANCEL if ($err != 0);

  if ($p ne $p_v) {
    my $no_match_msg = q{
There was a mismatch between the two 
passwords.  No changes were made.};
    &get_dialog_result("--title \"Passwords Do Not Match\" --cr-wrap " .
           "--clear --msgbox \"" .  $no_match_msg .  "\" 8 42");
    return;
  }

  $c = crypt($p, $salt);
  if ($pwd_exists == 1) {
    &bob_db_update_pwd($userid, $c);
  } else {
    &bob_db_insert_pwd($userid, $c);
  }
}


sub
checkPwd
{
  my ($p, $guess) = @_;
  return (crypt($guess, $p) eq $p);
}

1;
