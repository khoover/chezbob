# bc_win.pl
#
# A set of routines that handles the barcode login for Chez Bob.  
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
#
# $Id: bc_win.pl,v 1.12 2001-05-16 01:45:43 mcopenha Exp $
#

require "bc_util.pl";
require "snd_util.pl";
require "bob_db.pl";

my $DLG = "/usr/bin/dialog";
my $MIN_BARCODE_LENG = 6;
my $NOT_FOUND = -1;


sub
update_user_barcode
#
# Prompt the user to enter a new barcode. If it's already in the database 
# under a different userid or is not a valid barcode, output an error msg
# and ask the user to try again. 
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
        next;
      }
 
      &bob_db_update_user_barcode($userid, $barcode);
      system ("$DLG --title \"$barcode\" --clear --msgbox"
              ." \"Personal barcode successfully updated!\" 6 50");
      return;
    } else {
      &invalid_user_barcode_win;
    }
  }
}


sub
barcode_action_win
#
# Show the main menu in barcode mode.  Keep a running tally of the products 
# the user's purchased and echo them to the screen.  When user scans the 
# his/her personal barcode again, the entire transaction is recorded 
# (update balance and products tables).  Using this setup we cannot show 
# more than 4 products on the screen at once (using standard vga 80x25).  
# Our solution is to show the text "...more..." when the number of 
# products == 5 or more.  We only show the latest 4 purchases.  If the user 
# scans a product that's not in the database we output some text at the
# bottom of the dialog.
#
{
  my ($userid, $username) = @_;
  my $win_title = "Main Menu";
  my $guess = '0';		# initial barcode input
  my $numbought = 0;		# number of products users has purchased
  my $price = 0.0;		# price of current product
  my $phonetic_name = "";	# phonetic name of current product
  my $unknown_prod = 0;		# flag == 0 if product not found

  my $userbarcode = &bob_db_get_userbarcode_from_userid($userid);
  my $balance = &bob_db_get_balance($userid);
  my $balanceString = &get_balance_string($balance);

  &say_greeting;

  while (1) {
    my $win_textFormat = q{
Welcome, %s!

You currently %s

Please scan each product's barcode.  When you're done,
scan your personal barcode again.  The transaction will 
NOT be recorded until then. \n
		Product			Price
		-------			----- 
};

    my $total = 0.00;
    my $starting_prod = 0;
    if ($numbought >= 5) {
      $starting_prod = $numbought - 3 - 1;
      $win_textFormat .= "\t\t...more...\n"; 
    }
    for ($i = $starting_prod; $i < $numbought; ++$i) {
      $win_textFormat .= "\t\t" . $purchase[$i];
      my $name_leng = length($purchase[$i]);
      if ($name_leng < 8) {
        $win_textFormat .= "\t\t\t"; 
      } elsif ($name_leng < 16) {
        $win_textFormat .= "\t\t"; 
      } else {
        $win_textFormat .= "\t"; 
      }

      $win_textFormat .= sprintf("%.2f", $prices[$i]) . "\n";
      $total += $prices[$i];
    }
    if ($total > 0) {
      $win_textFormat .= "\t\t\t\t\t-----";
      $win_textFormat .= sprintf("\n\t\t\t\tTOTAL:\t\\\$%.2f", $total);
    }
   
    if ($unknown_prod) {
      $win_textFormat .= "\n   I did not recognize the last product you scanned";
    }

    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	   sprintf($win_textFormat, $username, $balanceString) .
	       "\" 24 65 2> /tmp/input.barcode") != 0) {
      return undef;
    }

    $guess = `cat /tmp/input.barcode`;
    $prod_barcode = &preprocess_barcode($guess);      

    if ($prod_barcode eq $userbarcode) {
      # We're done: Record entire transaction at once
      &sayit("your total is " . &format_money($total));
      &bob_db_update_stock(-1, @purchase);
      &bob_db_update_balance($userid, -$total, "BUY (BARCODE)");
      &say_goodbye;
      return $total;
    } else {
      # Update dialog
      $prodname = &bob_db_get_productname_from_barcode($prod_barcode);
      if (!defined $prodname) {
        $unknown_prod = 1;
      } else {
        $unknown_prod = 0;
        $phonetic_name = &bob_db_get_phonetic_name_from_barcode($prod_barcode);
        $price = &bob_db_get_price_from_barcode($prod_barcode);
        push(@purchase, $prodname);
        push(@prices, $price);
        $numbought++;
        &sayit("$phonetic_name");
      }
    }
  } 
}


sub
buy_single_item_with_scanner
{
  my ($userid) = @_;
  my $guess = &get_barcode_win;
  if (!defined $guess) {
    return;
  }

  $barcode = &preprocess_barcode($guess);      
  $prodname = &bob_db_get_productname_from_barcode($barcode);
  if (!defined $prodname) {
    &invalid_product_barcode_win;
    return;
  }

  my $phonetic_name = &bob_db_get_phonetic_name_from_barcode($barcode);
  &sayit("$phonetic_name");
  my $amt = &bob_db_get_price_from_barcode($barcode);
  my $txt = sprintf("\nIs your purchase amount \\\$%.2f?", $amt);
  if (&confirm_win($prodname, $txt, 40)) {
    push(@purchase, $prodname);
    &bob_db_update_stock(-1, @purchase);
    &bob_db_update_balance($userid, -$amt, "BUY " . $prodname);
  } else {
    return;
  }  
}


sub
get_barcode_win
{
  my $win_title = "Scan barcode:";
  if (system("$DLG --title \"$win_title\" --clear " .
      " --inputbox \"\" 8 45 2> /tmp/input.barcode") != 0) {
    return undef;
  }

  return `cat /tmp/input.barcode`;
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
