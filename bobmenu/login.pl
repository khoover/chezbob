# login_win.pl
#
# Routines for processing login names, both text and barcode

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

  my $pwd = &bob_db_get_pwd($userid);
  if ($pwd =~ /^closed/) {
    &expiredAccount_win;
    return;
  }
  if ($checkpass) {
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
  my $errCode;
  my $back_title = "Chez Bob 2001 (changeset $rev)";
  my $win_title = "Bank of Bob 2001";
  my $win_text = q{
Welcome to the B.o.B. 2001!

Enter your username or scan your personal barcode.
(If you are a new user enter a new username)
Or, scan an item to find its price:};

  ($errCode, $username) = &get_dialog_result("--backtitle \"$back_title\" --title \"$win_title\" --clear --cr-wrap --inputbox \"" . $win_text .  "\" 14 55 \"$username\"");

  return "" if ($errCode != 0);
  return $username;
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

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 9 45");
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

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
	 sprintf($win_text, $MIN_BARCODE_LENG) .  "\" 8 45");
}


sub
user_barcode_not_found_win
{
  my $win_title = "Unknown Barcode";
  my $win_text = q{
I could not find this barcode in the database. If you're
an existing user you must log into your regular account 
and choose the 'Barcode ID' option to change your user
barcode.  If you're a new user you'll need to first
create a new account by entering a valid username.
If this is a product, it isn't yet in the database.};

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
	 $win_text .  "\" 12 62");
}

# Display a window giving the name of an item and its price if a user scans an
# item barcode from the login screen.
sub
pricecheck_win
{
  my $barcode = shift;

  my $name = &bob_db_get_productname_from_barcode($barcode);
  my $price = &bob_db_get_price_from_barcode($barcode);

  # We shouldn't have been called unless the item is in the database, so this
  # should always be true...
  if (defined($name) && defined($price)) {
    my $win_title = "Item Price Check";
    my $win_text = sprintf("Item: %s\nPrice: \$%.02f", $name, $price);
    $win_text = &shell_escape($win_text);
    &get_dialog_result("--title \"$win_title\" --cr-wrap " .
                       "--msgbox \"$win_text\" 8 50");

  }
}

1;
