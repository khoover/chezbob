# mainmenu.pl
#
# The main menu for Chez Bob which currently contains options for depositing
# money, purchasing products, updating user settings (passwd, nickname, 
# barcode id), viewing transactions, and sending messages to Bob.  Routines
# for each of these functions is contained in separate files.
#
# $Id: mainmenu.pl,v 1.1 2001-05-18 05:41:44 mcopenha Exp $
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


sub
bob_action_win
{
  my ($userid, $username) = @_;
  my $nickname = &bob_db_get_nickname_from_userid($userid);
  &say_greeting($nickname);

  my $action = "";
  do {
    #
    # refresh the balance
    #
    my $balance = &bob_db_get_balance($userid);
    if ($balance == $NOT_FOUND) {
      print "no balance from database...exiting.\n";
      exit 1;
    }

    #
    # get the action
    #
    $action = &action_win($username,$userid,$balance,$last_purchase);

    $_ = $action;
    SWITCH: {
      /^DIGITS$/ && do {
        $last_purchase = &buy_single_item_with_scanner($userid);
        last SWITCH;
      };

      /^Add Money$/ && do {
        &add_win($userid);
        last SWITCH;
      };
  
      /^Candy\/Can of Soda$/ && do {
        $last_purchase = "Candy/Can of Soda";
        &buy_win($userid,$_);
        last SWITCH;
      };
    
      /^Snapple$/ && do {
        $last_purchase = "Snapple";
        &buy_win($userid,$_);
        last SWITCH;
      };
    
      /^Juice$/ && do {
        $last_purchase = "Juice";
        &buy_win($userid,$_);
        last SWITCH;
      };
    
      /^Popcorn\/Chips\/etc.$/ && do {
        $last_purchase = "Popcorn/Chips";
        &buy_win($userid,$_);
        last SWITCH;
      };
    
      /^Buy Other$/ && do {
        $last_purchase = "Other";
        &buy_win($userid);
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
   
      /^Modify Barcode ID$/ && do {
        &update_user_barcode($userid);
        last SWITCH;
      };
  
      /^Modify Nickname$/ && do {
        &update_nickname($userid);
        last SWITCH;
      };

      /^Modify Password$/ && do {
        &pwd_win($userid);
        last SWITCH;
      };
  
      /^No action$/ && do {
        last SWITCH;
      };
   
      (! /^Quit$/) && do {
        &unimplemented_win();
        last SWITCH;
      };
    } # SWITCH
  } while ($action ne "Quit");

  &say_goodbye;
} 


sub
action_win
{
  my ($username,$userid,$balance,$last_purchase) = @_;
  my $win_title = "Main menu";
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
	   "\"Message\" " .
	       "\"Leave a message for Bob                        \" " .
	   "\"Quit\" " .
	       "\"Finished\!                                      \" " .
	   "\"Modify Barcode ID\" " .
	       "\"Set your personal barcode                     \" " .
	   "\"Modify Nickname\" " .
	       "\"Set your nickname\" " .
	   "\"Modify Password\" " .
	       "\"Set, change, or delete your password           \" " .
	   "\"Transactions\" " .
	       "\"List recent transactions                       \" " .
	   " 2> input.action");

  $action = `cat input.action`;

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
