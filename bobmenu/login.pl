# login_win.pl
#
# Routines for processing login names, both text and barcode
#
# $Id: login.pl,v 1.12 2001-06-08 17:55:16 cse210 Exp $
#

$MIN_BARCODE_LENG = 6;

require "$BOBPATH/bc_util.pl";
require "$BOBPATH/dlg.pl";
require "$BOBPATH/newuser.pl";
require "$BOBPATH/passwd.pl";
require "$BOBPATH/mainmenu.pl";


sub
process_login
#
# See if we're dealing with a new user.  Check for a password if 
# 'checkpass' is true (barcode login doesn't require password). 
#
{
  my ($username, $checkpass) = @_;
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

  if ($checkpass) {
    my $pwd = &bob_db_get_pwd($userid);
    if (defined $pwd && &checkPwd($pwd, &guess_pwd_win) == 0) {
      &invalidPassword_win;
      return;
    } 
  }

  &bob_action_win($userid, $username);
}


sub
login_win
{
  my ($rev) = @_;
  my $username = "";
  my $win_title = "Bank of Bob 2001 (v.$rev)";
  my $win_text = q{
Welcome to the B.o.B. 2001!


Enter your username or scan your personal barcode.
(If you are a new user enter a new username):};

  if (system("$DLG --backtitle \"Chez Bob 2001\" --title \"$win_title\" --clear --cr-wrap --inputbox \"" . $win_text .  "\" 14 55 \"$username\" 2> $TMP/input.main") != 0) {
    return "";
  }

  return `cat $TMP/input.main`;
}


sub
isa_valid_username
#
# usernames can only have letters 
#
{
  my ($username) = @_;
#  return ($username =~ /^\D+$/);
  return ($username =~ /^[a-zA-Z]+$/);
}


sub
invalidUsername_win
{
  my $win_title = "Invalid Username";
  my $win_text = q{
Valid usernames must contain at least 
one letter and cannot have any digits.};

  system("$DLG --title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 9 45 2> /dev/null");
}


sub
isa_valid_user_barcode
#
# It's important to put some restrictions on the type of user barcode;
# otherwise, some people might take advantage of the system by using 1 or
# two digits numbers as their barcode, which would obviate the need to 
# use the barcode scanner.  Our current restriction is somewhat arbitrary:
# the barcode must be of length >= $MIN_BARCODE_LENG and must consist of
# only numbers.  If you alter this proc, be sure to modify the msg in 
# 'invalid_user_barcode_win' as well.  
#
{
  my ($str) = @_;
  my $leng = length($str);
  return (&isa_numeric_barcode($str) && $leng >= $MIN_BARCODE_LENG);
}


sub
invalid_user_barcode_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
Valid user barcodes must contain at 
least %d digits and no letters.};

  system("$DLG --title \"$win_title\" --cr-wrap --msgbox \"" .
	 sprintf($win_text, $MIN_BARCODE_LENG) .  "\" 8 45 2> /dev/null");
}


sub
user_barcode_not_found_win
{
  my $win_title = "Unknown User Barcode";
  my $win_text = q{
I could not find this barcode in the database. If you're
an existing user you must log into your regular account 
and choose the 'Barcode ID' option to change your user
barcode.  If you're a new user you'll need to first
create a new account by entering a valid username.};

  system("$DLG --title \"$win_title\" --cr-wrap --msgbox \"" .
	 $win_text .  "\" 11 62 2> /dev/null");
}

1;
