# usrbarcode.pl
#
# Routines for updating a user's personal barcode ID.  The user can login
# to the system using this personal barcode.
#
# $Id: usrbarcode.pl,v 1.1 2001-05-18 05:41:44 mcopenha Exp $
#

require "bc_util.pl";
require "bob_db.pl";
require "dlg.pl";


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
                ." \"Personal barcode successfully updated!\" 6 45");
        return;
      }
    } else {
      &invalid_user_barcode_win;
    }
  }
}


sub
barcode_already_in_db_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
This is not a valid barcode.  
Please try another one.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text . "\" 9 50 2> /dev/null");
}

1;
