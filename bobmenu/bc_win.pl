# bc_win.pl
#
# A set of routines that handles the barcode login for Chez Bob.  
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
#
# $Id: bc_win.pl,v 1.3 2001-05-13 21:55:08 mcopenha Exp $
#

$DLG = "/usr/bin/dialog";


sub
invalidBarcode_win
{
  my ($txt) = @_;
  my $win_title = $txt;
  my $win_text = q{
Invalid barcode.  Please try again.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 9 50 2> /dev/null");
}


sub
barcode_win
#
# Prompt the user to enter a new barcode. If it's already in the database 
# (under a different userid) or is not a valid barcode, output an error msg
# and ask the user to try again. 
#
{
  my ($userid) = @_;
  my $guess = '0';
  my $newBarcode = '0';
  my $win_title = "New barcode";
  my $win_text = "Scan your barcode:";

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
               $win_text .
	       "\" 8 45 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    system("rm -f /tmp/input.barcode");

    if (&isa_barcode($guess)) {
      $newBarcode = &preprocess_barcode($guess);      

      my $id = &bob_db_get_userid_from_barcode($newBarcode);
      if ($id != -1) {
        if ($id != $userid) {
          invalidBarcode_win($newBarcode);
          next;
        }
      }
 
      &bob_db_update_user_barcode($userid, $newBarcode);
      system ("$DLG --title \"$newBarcode\""
              ." --clear --msgbox"
              ." \"Barcode updated successfully!\" 9 50");
      return $newBarcode;
    } else {
      invalidBarcode_win($guess);
      next;
    }
  }
}


sub
barcode_action_win
#
# Nasty proc that shows the main menu in barcode mode.  Keeps a running 
# tally of the products you've purchased and echoes them to the screen.
# When user hits OK or scans the 'Done' barcode the entire transaction
# is recorded (update balance and products tables). 
#
{
  my ($userid) = @_;
  my $guess = '0';
  my $win_title = "Main Menu";

  my $leng = 24;	# initial dialog length 
  my $balance = &bob_db_get_balance($userid);
  my $numbought = 0;

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }

  my $username = bob_db_get_username_from_userid($userid);

  my $msg = "";
  if (-r "/tmp/message") {
    chop($msg = `cat /tmp/message`);
  }

  &sayit("Welcome $username");
  if ($balance < -5.0) {
    &sayit("It is time you deposited some money");
  }

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
      my $leng = length($purchase[$i]);
      if ($leng < 8) {
        $win_textFormat .= "\t\t\t"; 
      } elsif ($leng < 16) {
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
	       "\" $leng 65 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    system("rm -f /tmp/input.barcode");

    if (&isa_barcode($guess)) {
      $prod_barcode = &preprocess_barcode($guess);      

      $prodname = &bob_db_get_productname_from_barcode($prod_barcode);
      if (!defined $prodname) {
        next;
      } 

      $phonetic_name = &bob_db_get_phonetic_name_from_barcode($prod_barcode);
      $price = &bob_db_get_price_from_barcode($prod_barcode);

      if ($prodname eq "Done") {
        # Record all transactions at once
        &saytotal($total);
        &bob_db_update_stock(-1, @purchase);
        &bob_db_update_balance($userid, -$total, "BUY");
        &sayit("goodbye, $username!");
        return;
      } else {
        # Update dialog
        push(@purchase, $prodname);
        push(@prices, $price);
        $numbought++;
        &sayit("$phonetic_name");
        $leng += 1;
        next;
      }

    } else {
      # do nothing
      next;
    }
  } # while(1)
}


sub
barcode_not_found
{
  my $win_title = "Invalid barcode";
  my $win_text = q{
I could not find this barcode in the database. If you're 
an existing user you can change your barcode login from 
the main menu.  If you're a new user you'll need to first 
create a new account by entering a valid text login id.}; 

  system("$DLG --title \"$win_title\" --msgbox \"" .  $win_text .
	 "\" 10 65 2> /dev/null");
}

