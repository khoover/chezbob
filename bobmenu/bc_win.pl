# bc_win.pl
#
# A set of routines that handles the barcode login for Chez Bob.  
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
#
# $Id: bc_win.pl,v 1.15 2001-05-17 23:20:23 mcopenha Exp $
#

require "bc_util.pl";
require "snd_util.pl";
require "bob_db.pl";

my $DLG = "./bobdialog";
my $MIN_BARCODE_LENG = 6;
my $NOT_FOUND = -1;


sub
update_user_barcode
#
# Prompt the user to enter a new barcode.  The following cases are invalid:
# 	- barcode exists under a different userid 
#	- it's a product barcode
#	- it's not a valid barcode (according to 'isa_valid_user_barcode')
# If it's invalid, output an error msg and ask the user to try again.  
#
{
  my ($userid) = @_;

  while (1) {
    my $guess = &get_barcode_win;
    if (!defined $guess) { 
      # User canceled
      return;
    }

    $barcode = &preprocess_barcode($guess);      
    if (&isa_valid_user_barcode($barcode)) {
      my $otherid = &bob_db_get_userid_from_userbarcode($barcode);
      my $product = &bob_db_get_productname_from_barcode($barcode);
      if ($otherid != $NOT_FOUND || defined $product) {
        &barcode_already_in_db_win;
      } else {
        &bob_db_update_user_barcode($userid, $barcode);
        system ("$DLG --title \"$barcode\" --clear --msgbox"
                ." \"Personal barcode successfully updated!\" 6 50");
        return;
      }
    } else {
      &invalid_user_barcode_win;
    }
  }
}


sub
buy_single_item_with_scanner
#
#
#
{
  my ($userid) = @_;
  my $guess = `cat menuout`;

  $barcode = &preprocess_barcode($guess);      
  $prodname = &bob_db_get_productname_from_barcode($barcode);
  if (!defined $prodname) {
    &invalid_product_barcode_win;
    return "";
  }

  my @purchase = ();
  my $phonetic_name = &bob_db_get_phonetic_name_from_barcode($barcode);
  &sayit("$phonetic_name");
  my $amt = &bob_db_get_price_from_barcode($barcode);
  my $txt = sprintf("\nIs your purchase amount \\\$%.2f?", $amt);
  if (&confirm_win($prodname, $txt, 40)) {
    push(@purchase, $prodname);
    &bob_db_update_stock(-1, @purchase);
    &bob_db_update_balance($userid, -$amt, "BUY " . $prodname);
    return $prodname;
  } else {
    return "";
  }  
}


sub
get_barcode_win
{
  my $win_title = "Scan barcode:";
  if (system("$DLG --title \"$win_title\" --clear " .
      " --inputbox \"\" 8 45 2> input.barcode") != 0) {
    return undef;
  }

  return `cat input.barcode`;
}


sub
invalid_product_barcode_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
This is an invalid product barcode.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 9 50 2> /dev/null");
}


sub
invalid_user_barcode_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
Valid user barcodes must contain at least 
%d digits and no characters.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 sprintf($win_text, $MIN_BARCODE_LENG) .  "\" 9 50 2> /dev/null");
}


sub
barcode_already_in_db_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
This is not a valid barcode.  
Please try another one.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 sprintf($win_text, $MIN_BARCODE_LENG) .  "\" 9 50 2> /dev/null");
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
user_barcode_not_found_win
{
  my $win_title = "Unknown User Barcode";
  my $win_text = q{
I could not find this barcode in the database. If you're
an existing user you must log into your regular account 
and choose the 'Barcode' option to change your user
barcode.  If you're a new user you'll need to first
create a new account by entering a valid username.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 11 60 2> /dev/null");
}

1;
