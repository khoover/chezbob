# usrbarcode.pl
#
# Routines for updating a user's personal barcode ID.  The user can login
# to the system using this personal barcode.
#
# $Id: usrbarcode.pl,v 1.4 2001-06-01 18:51:30 mcopenha Exp $
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
  my $getmsg = q{
You can use your personal barcode to log into AND out of 
Chez Bob.  Please scan a barcode of your choice.  Here are 
some possibilities:

    - The back of your ID card,
    - Your Ralph's or Von's Club keychain,
    - The barcode from the back of a book or magazine,
    - A tattooed barcode on your arm.

There are also some websites for creating your own.  Check 
out http://thor-gw.phys.ualberta.ca/barcode/.  By the way,
you can't use a barcode from a Chez Bob product.};

  my $okmsg = q{
Personal barcode successfully updated!
You may now log in next time by scanning
your personal barcode.};


  while (1) {
    
    my $guess = &get_barcode_win($getmsg, 65, 20);
    if (!defined $guess) { 
      # User canceled
      return;
    }

    my $barcode = &preprocess_barcode($guess);      
    if (&isa_valid_user_barcode($barcode)) {
      my $otherid = &bob_db_get_userid_from_userbarcode($barcode);
      my $product = &bob_db_get_productname_from_barcode($barcode);
      if ($otherid != $NOT_FOUND || defined $product) {
        &barcode_already_in_db_win;
      } else {
        &bob_db_update_user_barcode($userid, $barcode);
        system ("$DLG --title \"$barcode\" --clear --cr-wrap --msgbox"
                ." \"$okmsg\" 9 45");
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

  system("$DLG --title \"$win_title\" --cr-wrap --msgbox \"" .
	 $win_text . "\" 8 40 2> /dev/null");
}

1;
