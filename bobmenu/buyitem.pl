# buyitem.pl
#
# Routines for purchasing products with both keyboard input (buy_win) and 
# barcode input (buy_single_item_with_scanner).
#
# $Id: buyitem.pl,v 1.8 2001-05-23 00:06:17 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";
require "speech.pl";
require "profile.pl";
require "bc_util.pl";

$PRICES{"Candy/Can of Soda"} = 0.45;
$PRICES{"Juice"} = 0.70;
$PRICES{"Snapple"} = 0.80;
$PRICES{"Popcorn/Chips/etc."} = 0.30;


sub
buy_win
#
# Legacy routine for purchasing an item from one of the food categories
# in the PRICES array.  If 'type' is not found in PRICES then ask the 
# user to input the price of their purchase.  Return the name of the 
# product category on success; return blank string otherwise (user 
# canceled).
#
{
  my ($userid, $type) = @_;

  my $amt;
  my $confirmMsg;
  undef $amt;

  if (defined $type) {
    if (defined $PRICES{$type}) {
      $amt = $PRICES{$type};
      $confirmMsg = "Buy ${type}?";
    }
  } else {
    $type = "BUY";
  }

  if (! defined $amt) {
    $confirmMsg = "Purchase amount?";

    my $win_title = "Buy stuff from Chez Bob";
    my $win_text = q{
What is the price of the item you are buying?
(NOTE: Be sure to include the decimal point!)};

    while (1) {
      if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
                 $win_text .  "\" 10 50 2> $TMP/input.deposit") != 0) {
        return "";
      }

      $amt = `cat $TMP/input.deposit`;
      if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
        last;
      }

      &invalid_purchase_win();
    }
  }

  if (! $PROFILE{"No Confirmation"}) {
    if (! &confirm_win($confirmMsg,
                     sprintf("\nIs your purchase amount \\\$%.2f?", $amt),40)) {
      return "";
    }
  }

  &bob_db_update_balance($userid, -$amt, $type);
  return $type;
}


sub
invalid_purchase_win
{
  my $win_title = "Invalid amount";
  my $win_text = q{
Valid amounts are positive numbers with up
to two decimal places of precision.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 8 50 2> /dev/null");
}


sub
buy_single_item_with_scanner
#
# Look up 'prodbarcode' from the products table and update the product's 
# stock (-1) and the user's balance.  On failure (product does not
# exist or user cancels) return empty string; on success (user buys product)
# return the name of the product purchased.  
#
{
  my ($userid, $prodbarcode) = @_;

  $barcode = &preprocess_barcode($prodbarcode);      
  $prodname = &bob_db_get_productname_from_barcode($barcode);
  if (!defined $prodname) {
    &invalid_product_barcode_win;
    return "";
  }

  my $phonetic_name = &bob_db_get_phonetic_name_from_barcode($barcode);
  if ($PROFILE{"Speech"}) { &sayit("$phonetic_name"); }
  my $amt = &bob_db_get_price_from_barcode($barcode);
  my $txt = sprintf("\nIs your purchase amount \\\$%.2f?", $amt);

  if (! $PROFILE{"No Confirmation"}) {
    if (! &confirm_win($prodname, $txt, 40)) {
      return "";
    }
  }

  &bob_db_update_stock(-1, $prodname);
  &bob_db_update_balance($userid, -$amt, "BUY " . $prodname);

  return $prodname;
}


sub
buy_with_cash
#
# Call get_barcode_win to get item barcode, look it up and update 
# the product's stock (-1).  On failure (product does not
# exist or user cancels) return empty string; on success (user buys product)
# return the name of the product purchased.  
#
{
  my $barcode = &get_barcode_win(); 
  if (!defined $barcode) {
    # user canceled
    return "";
  }

  $barcode = &preprocess_barcode($barcode);      
  $prodname = &bob_db_get_productname_from_barcode($barcode);
  if (!defined $prodname) {
    &invalid_product_barcode_win;
    return "";
  }

  my $phonetic_name = &bob_db_get_phonetic_name_from_barcode($barcode);
  &sayit("$phonetic_name");
  my $amt = &bob_db_get_price_from_barcode($barcode);

# MAC: take out confirmation
#  my $txt = sprintf("\nIs your purchase amount \\\$%.2f?", $amt);
#  if (! &confirm_win($prodname, $txt, 40)) {
#      return "";
#  }

  &bob_db_update_stock(-1, $prodname);

  return $prodname;
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

1;
