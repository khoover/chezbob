# bc_win.pl
#
# A set of routines that handles the barcode login for Chez Bob.  
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
#
# $Id: bc_win.pl,v 1.6 2001-05-14 22:06:51 mcopenha Exp $
#

my $DLG = "/usr/bin/dialog";
my $MIN_BARCODE_LENG = 6;


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
    my $guess = &get_user_barcode_win;
    if ($guess eq "") { 
      # User canceled
      return;
    }

    $barcode = &preprocess_barcode($guess);      
    if (&isa_valid_user_barcode($barcode)) {
      my $id = &bob_db_get_userid_from_barcode($barcode);
      if ($id != -1) {
        if ($id != $userid) {
          &invalid_user_barcode_win;
          next;
        }
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
# the user's purchased and echoes them to the screen.  When user scans the 
# 'Done' barcode the entire transaction is recorded (update balance and 
# products tables). 
#
{
  my ($userid, $username) = @_;
  my $guess = '0';
  my $win_title = "Main Menu";
  my $dialog_leng = 24;
  my $balance = &bob_db_get_balance($userid);
  my $numbought = 0;

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }

  my $msg = "";
  if (-r "/tmp/message") {
    chop($msg = `cat /tmp/message`);
  }

  &say_greeting;

  while (1) {
    my $win_textFormat = q{
Welcome, %s!

USER INFORMATION:
  You currently %s
  %s
  %s

Please scan each product's barcode.  When you're done,
scan the barcode at the top of the monitor labeled 'done'. 
The transaction will not be recorded until then. \n
		Product			Price
		-------			-----
};

    my $total = 0.00;
    for ($i = 0; $i < $numbought; ++$i) {
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
      $win_textFormat .= sprintf("\n\t\t\t\tTOTAL:\t\\\$%.2f\n", $total);
    }

    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $msg) .
	       "\" $dialog_leng 65 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    $prod_barcode = &preprocess_barcode($guess);      
    $prodname = &bob_db_get_productname_from_barcode($prod_barcode);
    if (!defined $prodname) {
      next;
    } 

    $phonetic_name = &bob_db_get_phonetic_name_from_barcode($prod_barcode);
    $price = &bob_db_get_price_from_barcode($prod_barcode);

    if ($prodname eq "Done") {
      # Record entire transaction at once
      &sayit("your total is " . &format_money($total));
      &bob_db_update_stock(-1, @purchase);
      &bob_db_update_balance($userid, -$total, "BARCODE PURCHASE");
      &say_goodbye;
      return;
    } else {
      # Update dialog
      push(@purchase, $prodname);
      push(@prices, $price);
      $numbought++;
      &sayit("$phonetic_name");
      $dialog_leng += 1;
      next;
    }

  } # while(1)
}


sub
get_user_barcode_win
{
  my $win_title = "Scan your barcode:";
  if (system("$DLG --title \"$win_title\" --clear " .
      " --inputbox \"\" 8 45 2> /tmp/input.barcode") != 0) {
    return "";
  }

  return `cat /tmp/input.barcode`;
}


sub
invalid_user_barcode_win
{
  my $win_title = "Invalid User Barcode";
  my $win_text = q{
Valid user barcodes must contain at least %d digits
and no characters.};

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


