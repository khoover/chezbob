# mainmenu.pl
#
# The main menu for Chez Bob which currently contains options for depositing
# money, purchasing products, updating user settings (passwd, nickname, 
# barcode id), viewing transactions, sending messages to Bob, updating 
# user profiles, and checking out books (limited).  Routines for each of 
# these options is contained in separate files.
#
# $Id: mainmenu.pl,v 1.15 2001-06-01 21:00:37 mcopenha Exp $
#  

require "passwd.pl";
require "bob_db.pl";
require "msgtobob.pl";
require "buyitem.pl";
require "deposit.pl";
require "speech.pl";
require "usrlog.pl";
require "nickname.pl";
require "usrbarcode.pl";
require "dlg.pl";
require "profile.pl";
require "library.pl";

my $MIN_BALANCE = -10.00;

sub
bob_action_win
{
  my ($userid, $username) = @_;
  my $nickname = &bob_db_get_nickname_from_userid($userid);
  my $userbarcode = &bob_db_get_userbarcode_from_userid($userid);
  my $last_purchase = "";
  my $action = "";

  &get_user_profile($userid);
  
  my $balance = &bob_db_get_balance($userid);
  if ($balance <= $MIN_BALANCE) {
    &say_greeting(".  This is a reminder to please deposit some money.");
  } elsif ($PROFILE{"Speech"}) { 
    &say_greeting($nickname); 
  }

MAINLOOP:
  while ($action ne "Quit") {
    #
    # refresh the balance
    #
    $balance = &bob_db_get_balance($userid);
    if ($balance == $NOT_FOUND) {
      &report_fatal("mainmenu: no balance from database.\n");
    }

    $action = &action_win($username,$userid,$balance,$last_purchase);
    my $curr_purchase = "";

    $_ = $action;
    SWITCH: {

    /^DIGITS$/ && do {
      # grab the output of the dialog program in $MENUOUT.  If 
      # it's equal to the user's barcode, we're done.

      if (! -r $MENUOUT) {
        &report_fatal("bob_action_win: $MENUOUT from dialog not found\n");
      }
      my $prodbarcode = `cat $MENUOUT`;
      if ($prodbarcode eq $userbarcode) { last MAINLOOP; }
      $curr_purchase = &buy_single_item_with_scanner($userid, $prodbarcode);
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
# will return the special value DIGITS.  
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

  my $retval =
    system("$DLG --title \"$win_title\" --clear --cr-wrap --menu \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $last_purchase) .
	   "\" 24 76 8 " .
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
	   "\"Buy Other\" " .
	       "\"Buy something else from Bob                    \" " .
	   "\"My Chez Bob\" " .
	       "\"Update your personal settings                     \" " .
	   "\"Quit\" " .
	       "\"Finished\!                                      \" " .
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
	       "\"Checkout a book from the lounge library        \" " .
	   " 2> $TMP/input.action");

  $action = `cat $TMP/input.action`;

  if ($retval != 0 || $action eq "Quit") {
    return "Quit";
  }

  return $action;
}


sub
unimplemented_win
{
  my $win_title = "Unimplemented function";
  my $win_text = q{
This functionality has not yet been
implemented.};

  system ("$DLG --title \"$win_title\" --clear --msgbox \"" .
	  $win_text .  "\" 8 40");
}

1;
