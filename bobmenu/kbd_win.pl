# kbd_win.pl
#
# Routines that implement the original Chez Bob text interface.  There's 
# no way we can do away with the text login completely; at the very least
# users need an easy way to add money to their accounts.  If the 
# barcode interface really takes off, we may want to remove/disable the 
# ability to purchase items using the text interface.  The potential
# advantage is that the inventory tracking would be more accurate.
#
# Al Su (alsu@cs.ucsd.edu)
#
# $Id: kbd_win.pl,v 1.12 2001-05-17 23:20:23 mcopenha Exp $
#  

require "bob_db.pl";
require "bc_win.pl";

my $DLG = "./bobdialog";
my $NOT_FOUND = -1;
$CANCEL = -1;

$PRICES{"Candy/Can of Soda"} = 0.45;
$PRICES{"Juice"} = 0.70;
$PRICES{"Snapple"} = 0.80;
$PRICES{"Popcorn/Chips/etc."} = 0.30;


################################ MAIN WINDOW ################################

sub
kbd_action_win
{
  my ($userid, $username) = @_;
  my $last_purchase = "";
  &say_greeting;

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
  
      (/^Candy\/Can of Soda$/ || /^Snapple$/ || /^Juice$/ ||
       /^Popcorn\/Chips\/etc.$/) && do {
        &buy_win($userid,$_);
        last SWITCH;
      };
    
      /^Buy Other$/ && do {
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
invalidUsername_win
{
  my $win_title = "Invalid username";
  my $win_text = q{
Valid usernames must contain at least one
character and cannot have any digits.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 9 45 2> /dev/null");
}


sub
guess_pwd_win
{
  my $win_title = "Enter password";
  my $win_text = "Enter your password:";
  if (system("$DLG --title \"$win_title\" --clear --passwordbox \"" .
	     $win_text .  "\" 8 45 2> input.guess") != 0) {
    return undef;
  }

  return `cat input.guess`;
}


sub
invalidPassword_win
{
  my $win_title = "Wrong password";
  my $win_text = "\nWrong password entered!\n";

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 7 30 2> /dev/null");
}


############################## NEW USER WINDOWS #############################

sub
askStartNew_win
{
  my ($username) = @_;
  my $email = "";
  my $win_title = "New Chez Bob user?";
  my $win_textFormat = q{
I did not find you in our database.  Shall I open
up a new Chez Bob record under the name \"%s\"
for you?};

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --yesno \"" .
	       sprintf($win_textFormat, $username) .
	       "\" 9 58 2> /dev/null") != 0) {
      return $CANCEL;
    }

    $email = &askEmail_win($email);
    if (! defined $email) {
      $email = "";
      next;
    }
    if ($email !~ /^[^\s]+@[^\s]+$/) {
      &invalidEmail_win();
      next;
    }

    &bob_db_add_user($username, $email);
    return 0;
  }
}


sub
askEmail_win
{
  my ($currentvalue) = @_;
  my $win_title = "Email address";
  my $win_text = q{
What is your email address?  (UCSD or SDSC
email addresses preferred.)};

  system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	 $win_text .  "\" 11 51 \"$currentvalue\" 2> input.email");
  my $retval = $? >> 8;
  if ($retval == 0) {
    return `cat input.email`;
  } else {
    return undef;
  }
}


sub
invalidEmail_win
{
  my $win_title = "Invalid email address";
  my $win_text = q{
Valid email addresses take the form
<user>@<full.domain.name>};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 8 50 2> /dev/null");
}

############################## ACTION WINDOWS ###############################

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

Choose one of the following actions (scroll down for more options):};

  my $balanceString = &get_balance_string($balance);
  my $msg = &get_msg;

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
add_win
{
  my ($userid) = @_;

  my $win_title = "Add money";
  my $win_text = q{
Deposit cash in the Bank of Bob lockbox and indicate the
amount deposited below.  (NOTE:  Be sure to include the
decimal point!)

Please do *NOT* deposit all your loose change (especially
pennies!) into the Bank of Bob.  If you have large amounts
of coins, Chez Bob will provide you with coin sleeves,
which once filled with coins, we will then gladly accept!
Send mail to chezbob@cs.ucsd.edu for more information.
Thanks for your consideration!

How much was deposited into the Bank of Bob?};

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
	       $win_text .  "\" 20 65 2> input.deposit") != 0) {
      return $CANCEL;
    }

    my $amt = `cat input.deposit`;
    if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
      if (! &confirm_win("Add amount?",
			 sprintf("\nWas the deposit amount \\\$%.2f?", $amt))) {
	next;
      }

      &bob_db_update_balance($userid, $amt, "ADD");
      return $amt;
    } else {
      &invalidAmount_win();
    }
  }
}


sub
buy_win
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
What is the price of the item you are
buying?

(NOTE: Be sure to include the decimal
point!)};

    while (1) {
      if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
		 $win_text .  "\" 13 50 2> input.deposit") != 0) {
	return $CANCEL;
      }

      $amt = `cat input.deposit`;
      if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
	last;
      }

      &invalidAmount_win();
    }
  }

  if (! &confirm_win($confirmMsg,
		     sprintf("\nIs your purchase amount \\\$%.2f?", $amt),40)) {
    return $CANCEL;
  } else {
    &bob_db_update_balance($userid, -$amt, $type);
    return $amt;
  }
}


sub
message_win
{
  my ($username, $userid) = @_;
  my $win_title = "Leave a message for Bob";
  my $win_text = q{
Leave a message for Bob!  We need your feedback about:

 - what you like and dislike about the Chez Bob service
 - what items are out of stock
 - suggestions for future offerings (specific products
   and a reasonable price you would pay)
 - almost anything else you want to say!

What is your message?};

  if (&confirm_win("Anonymous?",
		   "\nDo you want to send your message anonymously?", 50)) {
    $username = "anonymous";
    undef $userid;
  }

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .  
             $win_text .
	     "\" 18 74 \"From $username: \" 2> input.msg") == 0) {
    my $msg = `cat input.msg`;
    &bob_db_insert_msg($userid, $msg);
  }
}


sub
log_win
{
  my ($userid) = @_;
  my $win_title = "Transactions";
  my $logfile = "$userid.output.log";
  
  &bob_db_log_transactions($userid, $logfile);

  system("$DLG --title \"$win_title\" --clear --textbox " .
	 "$logfile 24 75 2> /dev/null");
}


sub
pwd_win
{
  my ($userid) = @_;
  my $win_title = "Enter Password";
  my $win_text = q{
Type your new password.  To remove an existing
password, do not enter any text.};

  my $verify_win_text = q{
Re-type your password:};

  my $passwd = &bob_db_get_pwd($userid);
  if (defined $passwd) {
    $salt = substr($passwd, -2, 2);
    $pwd_exists = 1;
  } else {
    $salt = "cB";
    $pwd_exists = 0;
  }

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --passwordbox \"" .
	     $win_text .  "\" 12 50 2> input.pwd") != 0) {
    return $CANCEL;
  }
  my $p = `cat input.pwd`;

  if ($p eq "") {
    &bob_db_remove_pwd($userid);
    return;
  }

  if (system("$DLG --title \"$win_title\" --clear --passwordbox \"" .
	     $verify_win_text .  "\" 10 40 2> input.pwd_v") != 0) {
    return $CANCEL;
  }
  my $p_v = `cat input.pwd_v`;

  if ($p ne $p_v) {
    my $no_match_msg = q{
There was a mismatch between the two passwords.
No changes were made.};
    system("$DLG --title \"Passwords do not match\" --clear --msgbox \"" .
	   $no_match_msg .  "\" 8 52 2> /dev/null");
    return;
  }

  $c = crypt($p, $salt);
  if ($pwd_exists == 1) {
    &bob_db_update_pwd($userid, $c);
  } else {
    &bob_db_insert_pwd($userid, $c);
  }
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

################################# UTILITIES #################################

sub
isa_valid_username
#
# usernames must consist of at least 1 char and can only contain 
# non-digit (\D) chars.
#
{
  my ($username) = @_;
  return ($username =~ /^\D+$/); 
}
 

sub
checkPwd
{
  my ($p, $guess) = @_;
  return (crypt($guess, $p) eq $p); 
}


sub
confirm_win
{
  my ($win_title,$win_text,$w,$h) = @_;
  $h ||= 7;
  $w ||= 40;

  $retval = system("$DLG --title \"$win_title\" --clear --yesno \"" .
		   $win_text .  "\" $h $w 2> /dev/null");
  return ($retval == 0);
}


sub
get_balance_string
{
  my ($balance) = @_;
  if ($balance < 0.0) {
    return (sprintf("owe Bob \\\$%.2f", -$balance));
  } else {
    return (sprintf("have a credit balance of \\\$%.2f", $balance));
  }
}


sub
get_msg
{
  if (-r "message") {
    chop($msg = `cat message`);
  } else {
    return "";
  }
}


sub
invalidAmount_win
{
  my $win_title = "Invalid amount";
  my $win_text = q{
Valid amounts are positive numbers with up
to two decimal places of precision.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 8 50 2> /dev/null");
}


1;
