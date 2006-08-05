# mainmenu.pl
#
# The main menu for Chez Bob which currently contains options for depositing
# money, purchasing products, updating user settings (passwd, nickname, 
# barcode id), viewing transactions, sending messages to Bob, updating 
# user profiles, and checking out books (limited).  Routines for each of 
# these options is contained in separate files.
#
# $Id: mainmenu.pl,v 1.19 2002/08/01 21:59:50 alsu Exp $
#  

require "$BOBPATH/passwd.pl";
require "$BOBPATH/bob_db.pl";
require "$BOBPATH/msgtobob.pl";
require "$BOBPATH/buyitem.pl";
require "$BOBPATH/deposit.pl";
require "$BOBPATH/speech.pl";
require "$BOBPATH/usrlog.pl";
require "$BOBPATH/nickname.pl";
require "$BOBPATH/usrbarcode.pl";
require "$BOBPATH/dlg.pl";
require "$BOBPATH/profile.pl";
require "$BOBPATH/library.pl";

my $MIN_BALANCE = -1.00;
my $MIN_BALANCE_ANNOUNCE = -2.00;

sub
bob_action_win
#
# This is where most of the work gets done.  Call 'action_win' to display
# the main menu and get the user's last action.  Make sure to refresh the
# screen with the user's balance and the last product they purchased.
#
{
  my ($userid, $username) = @_;
  my $nickname = &bob_db_get_nickname_from_userid($userid);
  my $userbarcode = &bob_db_get_userbarcode_from_userid($userid);
  my $last_purchase = "";
  my $action = "";

  &get_user_profile($userid);
  
  my $balance = &bob_db_get_balance($userid);
  if ($balance <= $MIN_BALANCE) {
    if ($balance <= $MIN_BALANCE_ANNOUNCE) {
      system("play $BOBPATH/negative_balance.wav >/dev/null &");
    }
    &balanceNag_win($balance);
  } elsif ($PROFILE{"Speech"}) { 
    &say_greeting($nickname); 
  }

MAINLOOP:
  while ($action ne "Quit") {

    $balance = &bob_db_get_balance($userid);
    if ($balance == $NOT_FOUND) {
      &report_fatal("mainmenu: no balance from database.\n");
    }

    $action = &action_win($username, $userid, $balance, $last_purchase);
    my $curr_purchase = "";

    # First check if we're dealing with a barcode
    if (&isa_numeric_barcode($action)) {
      my $prodbarcode = &preprocess_barcode($action);
      if ($prodbarcode eq $userbarcode) { last MAINLOOP; }
      $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
    } else {
      # Otherwise, check for any of the visible menu options

      $_ = $action;
      SWITCH: {

      /^Soda Login$/ && do {
        if (&soda_rlogin($username, $balance) == 0) {
          $action = "Quit";
        }
        last SWITCH;
      };

      /^Add Money$/ && do {
        &add_win($userid);
        last SWITCH;
      };

      (/^Candy\/Can of Soda$/ || /^Snapple$/ || /^Juice$/ ||
       /^Popcorn\/Chips\/etc.$/) && do {
        $curr_purchase = &buy_win($userid, $_);
        last SWITCH;
      };
    
      /^Espresso, Single$/ && do {
	  $prodbarcode = &preprocess_barcode("034707031043");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Espresso, Double$/ && do {
	  $prodbarcode = &preprocess_barcode("075678356124");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Cappuccino, Single$/ && do {
	  $prodbarcode = &preprocess_barcode("075140005154");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Cappuccino, Double$/ && do {
	  $prodbarcode = &preprocess_barcode("077711012318");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Latte, Single$/ && do {
	  $prodbarcode = &preprocess_barcode("093624835028");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Latte, Double$/ && do {
	  $prodbarcode = &preprocess_barcode("042491500010");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Mocha, Single$/ && do {
	  $prodbarcode = &preprocess_barcode("074182260170");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Mocha, Double$/ && do {
	  $prodbarcode = &preprocess_barcode("074711331081");
	  $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
	  last SWITCH;
      };
      
      /^Buy Other$/ && do {
        $curr_purchase = &buy_win($userid, $_);
        last SWITCH;
      };
  
      /^Message$/ && do {
        &message_win($username, $userid);
        last SWITCH;
      };
    
      /^Transactions$/ && do {
        &log_win($userid);
        last SWITCH;
      };
     
      /^My Chez Bob$/ && do {
        &profile_win($userid);
        last SWITCH;
      };
  
      /^Barcode ID$/ && do {
        &update_user_barcode($userid);
        $userbarcode = &bob_db_get_userbarcode_from_userid($userid);
        last SWITCH;
      };
    
      /^Nickname$/ && do {
        &update_nickname($userid);
        last SWITCH;
      };
  
      /^Password$/ && do {
        &pwd_win($userid);
        last SWITCH;
      };
    
      /^Checkout a Book$/ && do {
        &checkout_book($userid, $username);
        last SWITCH;
      };
  
      /^No action$/ && do {
        last SWITCH;
      };
     
      (! /^Quit$/) && do {
        &unimplemented_win;
        last SWITCH;
      };
    
      }  # SWITCH
    }  # ELSE
  
    if ($curr_purchase ne "") {
      # User did *not* cancel purchase
      $last_purchase = $curr_purchase;
      if ($PROFILE{"Auto Logout"}) { last MAINLOOP; }
    }

  }  # WHILE

  if ($PROFILE{"Speech"}) { &say_goodbye; }
} 


sub
action_win
#
# Print the text for Bob's main menu.  Return the menu selection the user
# chooses.  If the user scans an item with the scanner, the dialog program
# will return only numeric input.   
#
{
  my ($username,$userid,$balance,$last_purchase) = @_;
  my $win_title = "Main Menu";
  my $win_textFormat = q{
Welcome, %s!
USER INFORMATION:
  You currently %s
  %s
  Last Item Purchased: %s

Choose one of the following actions (scroll down for more options) 
or scan an item using the barcode scanner.};

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }
  if (-r "message") {
    chop($msg = `cat message`);
  } 

  my ($retval, $action) =
    &get_dialog_result("--title \"$win_title\" --clear --cr-wrap " .
                       "--default-item \"Add Money\" --menu \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $last_purchase) .
	   "\" 24 76 9 " .
	   "\"Soda Login\" " .
	       "\"Log in to the soda machine (in progress)        \" " .
	   "\"Add Money\" " .
	       "\"Add money to your Chez Bob account             \" " .
	   "\"Candy/Can of Soda\" " .
	       "\"Buy candy or a can of soda from Bob     (\\\$0.45)\" " .
	   "\"Juice\" " .
	       "\"Buy apple/orange/Kern's juice from Bob  (\\\$0.70)\" " .
	   "\"Snapple\" " .
	       "\"Buy a Snapple drink from Bob            (\\\$0.80)\" " .
	   "\"Popcorn/Chips/etc.\" " .
	       "\"Buy popcorn, chips, etc. from Bob       (\\\$0.30)\" " .
	   "\"Espresso\" " .
	       "\"Buy espresso from Bob                          \" " .
	   "\"Buy Other\" " .
	       "\"Buy something else from Bob                    \" " .
	   "\"Quit\" " .
	       "\"Finished\!                                      \" " .
	   "\"My Chez Bob\" " .
	       "\"Update your personal settings                     \" " .
	   "\"Message\" " .
	       "\"Leave a message for Bob                        \" " .
	   "\"Nickname\" " .
	       "\"Set your nickname                             \" " .
	   "\"Barcode ID\" " .
	       "\"Set your personal barcode login                \" " .
	   "\"Password\" " .
	       "\"Set your password           \" " .
	   "\"Transactions\" " .
	       "\"List recent transactions                       \" " .
	   "\"Checkout a Book\" " .
	       "\"Checkout a book from the lounge library        \" ");

  if ($retval != 0 || $action eq "Quit") {
    return "Quit";
  }

  if ($action eq "Espresso") {
      $action = &espresso_win($userid, $_);
  }

  return $action;
}


sub
espresso_win
#
# Print the espresso items and return the barcode for the selected item.
#
{
  my ($username,$userid,$balance,$last_purchase) = @_;
  my $win_title = "Espresso Menu";
  my $win_textFormat = q{
Choose one of the following espresso items (scroll down for more options).};

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }
  if (-r "message") {
    chop($msg = `cat message`);
  } 

  my ($retval, $action) =
    &get_dialog_result("--title \"$win_title\" --clear --cr-wrap --menu \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $last_purchase) .
	   "\" 24 76 8 " .
	   "\"Espresso, Single\" " .
	       "\"Espresso, Single                        (\\\$0.50)\" " .
	   "\"Espresso, Double\" " .
	       "\"Espresso, Double                        (\\\$1.00)\" " .
	   "\"Cappuccino, Single\" " .
	       "\"Cappuccino, Single                       (\\\$1.50)\" " .
	   "\"Cappuccino, Double\" " .
	       "\"Cappuccino, Double                       (\\\$2.00)\" " .
	   "\"Latte, Single\" " .
	       "\"Latte, Single                           (\\\$1.50)\" " .
	   "\"Latte, Double\" " .
	       "\"Latte, Double                           (\\\$2.00)\" " .
	   "\"Mocha, Single\" " .
	       "\"Mocha, Single                           (\\\$2.00)\" " .
	   "\"Mocha, Double\" " .
	       "\"Mocha, Double                           (\\\$2.50)\" ");

  if ($retval != 0 || $action eq "Quit") {
    return "Quit";
  }
  
  return $action;
}

sub
balanceNag_win
{
  my $balance = shift;
  my $win_title = "Negative Balance";
  my $win_text = sprintf <<ENDMSG, $balance;
Your account has a balance of %.2f.
Please help us out by depositing money into
your account.
ENDMSG

  &get_dialog_result("--title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 10 60");
}

sub
unimplemented_win
{
  my $win_title = "Unimplemented function";
  my $win_text = q{
This functionality has not yet been
implemented.};

  &get_dialog_result ("--title \"$win_title\" --clear --msgbox \"" .
	  $win_text .  "\" 8 40");
}

sub
soda_rlogin
{
  my ($username, $balance) = @_;

  $balance = sprintf("%.0f", $balance * 100) + 0.0;
  &get_dialog_result ("--title \"Transferring Login...\" --infobox " .
                      "\"Transferring login information to soda machine.\" " .
                      "5 40");

  system "$BOBPATH/soda_rlogin.pl $username $balance";

  if ($? == 0) {
    &get_dialog_result ("--title \"Login Succeeded\" --infobox " .
                        "\"Login transferred; automatically logging out...\" " .
                        "5 40");
    sleep 2;
    return 0;
  } else {
    &get_dialog_result ("--title \"Login Failed\" --msgbox " .
                        "\"Remote soda machine login failed.\" 5 40");
    return 1;
  }
}

1;
