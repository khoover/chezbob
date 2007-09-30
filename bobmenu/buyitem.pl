# buyitem.pl
#
# Routines for purchasing products with both keyboard input (buy_win) and 
# barcode input (buy_single_item_with_scanner).

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";
require "$BOBPATH/speech.pl";
require "$BOBPATH/profile.pl";
require "$BOBPATH/bc_util.pl";

my $MAX_PURCHASE = 100;		# dollars


sub
buy_win
# Routine for handling "Buy Other" purchases.  This also used to handle food
# categories (candy/can of soda/chips/etc.), but no longer does so since those
# categories are removed and users must use the barcode scanner.
#
# The privacy option is not consulted, since we'd like a purchase of an item
# with a barcode to be distinguished from a BUY OTHER even for users with
# privacy turned on.
#
{
  my ($userid, $type) = @_;

  my $amt;
  my $confirmMsg;
  undef $amt;

  $confirmMsg = "Purchase amount?";

  my $win_title = "Buy Stuff from Chez Bob";
  my $win_text = q{
What is the price of the item you are buying?
(NOTE: Be sure to include the decimal point!)};

  while (1) {
    (my $err, $amt) = &get_dialog_result("--title \"$win_title\" --clear ".
                      "--cr-wrap --inputbox \"" .  $win_text .  "\" 10 50");
    return "" if ($err != 0);

    if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
      if ($amt > $MAX_PURCHASE) {
        &exceed_max_purchase_win;
      } else {
        # amt entered is OK
        last;
      }
    } else {
      &invalid_purchase_win;
    }
  }  # while
  &sayit(&format_money($amt)) if ($PROFILE{"Speech"});

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
buy_single_item_with_scanner
#
# Look up 'prodbarcode' from the products table and update the transaction
# table and the user's balance.  On failure (product does not exist or user
# cancels) return empty string; on success (user buys product) return the name
# of the product purchased.
#
{
  my ($userid, $prodbarcode) = @_;
  my $buy_time = time;
  my $dup_purchase = 0;
  my $ent;

  # Check for the magic 'shell access' barcode
  if ($prodbarcode eq '898972437' || $prodbarcode eq '31415926535')
  {
    # Alan Su  -- 1001
    # Mike C.  -- 1174
    # John Bellardo -- 1181
    # Marvin McNett -- 1191
    # Vic Gidofalvi -- 1261
    # Wenjing Rao -- 1349
    # Mike McCracken -- 1347
    # Kirill Levchenko -- 1436
    # Michael Vrable -- 1743
    # Justin Ma -- 1721
    if ($userid != 1001 && $userid != 1174 &&
        $userid != 1181 && $userid != 1191 &&
        $userid != 1261 && $userid != 1349 &&
        $userid != 1347 && $userid != 1436 &&
        $userid != 1743 && $userid != 1721)
    {
      return "";
    }

    if ($main::drop_to_shell == 0)
    {
        $main::drop_to_shell = $userid;
        if ($PROFILE{"Speech"}) { &sayit("Thank you for taking such good care of chay bob"); }
    }
    else
    {
        $main::drop_to_shell = 0;
        if ($PROFILE{"Speech"}) { &sayit("i regret your decision not to take care of me"); }
    }
    return "";
  }

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

  foreach $ent ( @main::this_purchase_list ) {
    $dup_purchase = 1 if ($buy_time - $ent->{Time} <= 30 &&
                                          $ent->{Prod} eq $prodname);
  }
  if ($dup_purchase || !$PROFILE{"No Confirmation"}) {
    if ($dup_purchase) {
      $txt = sprintf("\nReally purchase another $prodname for \\\$%.2f?", $amt);
    }
    if (! &confirm_win($prodname, $txt, 40)) {
      #&report("ChezBob: Questionable Duplicate Purchase", "Questionable duplicate purchase declined by $userid: $prodname\n") if ($dup_purchase);
      return "";
    }
    #&report("ChezBob: Valid Duplicate Purchase", "Duplicate purchase accepted by $userid: $prodname\n") if ($dup_purchase);
  }
  $main::this_purchase_list[$#main::this_purchase_list + 1] = { Prod => $prodname, Time => $buy_time };

  my $type = $PROFILE{"Privacy"} ? "BUY" : "BUY $prodname";
  &bob_db_update_balance($userid, -$amt, $type, $barcode, $PROFILE{"Privacy"});

  return $prodname;
}


sub
buy_with_cash
#
# Call get_barcode_win to get item barcode, look it up and purchase it.  On
# failure (product does not exist or user cancels) return empty string; on
# success (user buys product) return the name of the product purchased.
#
{
  my $msg = q{
You are paying with cash.  Please deposit the 
appropriate amount in the Bank of Bob and 
scan the product's barcode now.};
  my $barcode = &get_barcode_win($msg, 50, 11); 
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
  &sayit("$phonetic_name") if ($PROFILE{"Speech"});

  return $prodname;
}


sub
invalid_product_barcode_win
{
  my $win_title = "Invalid Product";
  my $win_text = q{This is an invalid product barcode.
If you think this item should be valid, send a message to chezbob@cs.ucsd.edu
to let us know to fix it.};

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
	 $win_text .  "\" 9 50");
}


sub
exceed_max_purchase_win
{
  my $win_title = "Invalid amount";
  my $win_text = "\nThe maximum purchase amount is \\\$$MAX_PURCHASE";

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 7 40");
}


sub
invalid_purchase_win
{
  my $win_title = "Invalid amount";
  my $win_text = q{
Valid amounts are positive numbers with up
to two decimal places of precision.};

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 8 50");
}


1;
