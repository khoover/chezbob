#!/usr/bin/perl -w

###
### libraries and constants
###

use Pg;
use Barcode;

$DLG = "/usr/bin/dialog";

$PRICES{"Candy/Can of Soda"} = 0.45;
$PRICES{"Juice"} = 0.70;
$PRICES{"Snapple"} = 0.80;
$PRICES{"Popcorn/Chips/etc."} = 0.30;

############################# BARCODE UTILS #################################

sub
isa_barcode
{
  my ($str) = @_;
  $cuecat_header = "^\\.C";
  if ($str =~ $cuecat_header) {
    return 1;
  } else {
    return 0;
  }
}

sub
decode_barcode
{
  my ($crap) = @_;
  my $scan = CueCat->decode($crap);
  $barcode = $scan->{'barcode_data'};
#  system("$DLG --msgbox $barcode 5 50");
  return $barcode;
}

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
  my ($username, $userid, $conn) = @_;
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
      $newBarcode = &decode_barcode($guess);      
      my $selectqueryFormat = q{
        select userid
        from users
        where userbarcode = '%s';
      };
      my $result = $conn->exec(sprintf($selectqueryFormat, $newBarcode));
      if ($result->ntuples == 1) {
        if ($result->getvalue(0,0) != $userid) {
          invalidBarcode_win($newBarcode);
          next;
        }
      }
   
      my $updatequeryFormat = q{
        update users
  	set userbarcode = '%s'
        where userid = %d;
      };      
      $result = $conn->exec(sprintf($updatequeryFormat,
  				     $newBarcode,
				     $userid));
      if ($result->resultStatus != PGRES_COMMAND_OK) {
        print STDERR "barcode_win: error updating new barcode\n";
        exit 1;
      }       
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
{
  my ($username,$userid,$conn) = @_;
  my $guess = '0';
  my $win_title = "Scan a barcode";

  @purchase; 
  $leng = 12;

  while (1) {
    my $win_text = q{
Please scan a product's barcode.  When you're done,
scan the barcode at the top of the monitor labeled 'done' \n\n};
    foreach $p (@purchase) {
      $win_text = $win_text . "\n" . $p;
    }
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
               $win_text .
	       "\" $leng 65 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    system("rm -f /tmp/input.barcode");

    if (&isa_barcode($guess)) {
      $prod_barcode = &decode_barcode($guess);      
      my $selectqueryFormat = q{
        select name
        from products
        where barcode = '%s';
      };
      my $result = $conn->exec(sprintf($selectqueryFormat, $prod_barcode));
      if ($result->ntuples != 1) {
        system ("$DLG --title \"$prod_barcode\""
                ." --clear --msgbox"
                ." \"Product not found.  Please try again\" 9 50");
        next;
      } else {
        $prodname = $result->getvalue(0,0);
        if ($prodname eq "done") {
          # record all transactions at once
          return;
        } else {
          # update dialog
          push(@purchase, $prodname);
#          system("echo \"$prodname\" > /dev/speech");
          $leng += 1;
          next;
        }
      }
    } else {
      invalidBarcode_win($guess);
      next;
    }
  } # while(1)
}

################################ MAIN WINDOW ################################

sub
login_win
{
  my ($rev) = @_;

  my $username = "";
  my $win_title = "Bank of Bob 2000 (v.$rev)";
  my $win_text = q{
Welcome to the B.o.B. 2K!


Enter your username (or your desired
username if you are a new user):};

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	       $win_text .
	       "\" 14 45 \"$username\" 2> /tmp/input.main") != 0) {
      print "empty\n";
      return "";
    }

    $username = `cat /tmp/input.main`;
    system("rm -f /tmp/input.*");

    # MAC: check if we're dealing with a regular username or a barcode
    if (&isa_barcode($username)) {
      # Barcode: 
      return $username;
    } elsif ($username !~ /^\w+$/) {
      # Invalid username
      &invalidUsername_win();
      next;
    } else {
      # Valid username
      return $username;
    }
  }
}

sub
invalidUsername_win
{
  my $win_title = "Invalid username";
  my $win_text = q{
Valid usernames must contain at least one
character and consist of letters and numbers
only.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 9 50 2> /dev/null");
}

sub
guess_pwd_win
{
  my $win_title = "Enter password";
  my $win_text = "Enter your password:";

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	     $win_text .
	     "\" 8 45 2> /tmp/input.guess") != 0) {
    return "";
  }

  $guess = `cat /tmp/input.guess`;
  return $guess;
}

sub
invalidPassword_win
{
  my $win_title = "Wrong password";
  my $win_text = "\nWrong password entered!\n";

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 7 30 2> /dev/null");
}

################################ MAIN WINDOW ################################



############################## NEW USER WINDOWS #############################
sub
askStartNew_win
{
  my ($username,$conn) = @_;
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
      return -1;
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

    my $insertqueryFormat = q{
insert
into users
values(
  nextval('userid_seq'),
  '%s',
  '%s');
  };

    my $result = $conn->exec(sprintf($insertqueryFormat,
				     $username,
				     $email));
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "askStartNew_win: error inserting record...exiting\n";
      exit 1;
    }

    # success!
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
	 $win_text .
	 "\" 11 51 \"$currentvalue\" 2> /tmp/input.email");
  my $retval = $?>>8;
  if ($retval == 0) {
    return `cat /tmp/input.email`;
  }
  else {
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
	 $win_text .
	 "\" 8 50 2> /dev/null");
}

############################## NEW USER WINDOWS #############################



########################### BALANCE INIT WINDOWS ############################
sub
initBalance_win
{
  my ($userid,$conn) = @_;
  my $win_title = "Initial balance";
  my $win_text = q{
Now, we will transfer balance information from
your Chez Bob index card to the database.

Do you currently *OWE* Bob money?};

  my $retval;

  while (1) {
#     $retval = system("$DLG --title \"$win_title\" --clear --yesno \"" .
# 		     $win_text .
# 		     "\" 9 58 2> /dev/null");

#     if ($retval != 0 && $retval != 256) {
#       return -1;
#     }

#     if ($retval == 0) {
#       $amt = - &askHowMuch_win("do you owe Bob");
#       if ($amt > 0) {
# 	next;
#       }
#     }
#     else {
#       $amt = &askHowMuch_win("does Bob owe you");
#       if ($amt < 0) {
# 	next;
#       }
#     }

    my $insertqueryFormat = q{
insert
into balances
values(
  %d,
  %.2f);
insert
into transactions
values(
  'now',
  %d,
  %.2f,
  'INIT');
    };

    my $result = $conn->exec(sprintf($insertqueryFormat,
				     $userid, 0.0,
				     $userid, 0.0));
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "initBalance: error inserting record...exiting\n";
      exit 1;
    }

    # success!
    return 0;
  }
}

sub
askHowMuch_win
{
  my ($qstring) = @_;
  my $win_title = "How much?";
  my $win_textFormat = "\nHow much %s?";

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	       sprintf($win_textFormat, $qstring) .
	       "\" 10 51 2> /tmp/input.howmuch") != 0) {
      return -1;
    }

    my $amt = `cat /tmp/input.howmuch`;
    if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
      return $amt;
    }

    &invalidAmount_win();
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
	 $win_text .
	 "\" 8 50 2> /dev/null");
}
########################### BALANCE INIT WINDOWS ############################



############################## ACTION WINDOWS ###############################
sub
action_win
{
  my ($username,$userid,$balance,$conn) = @_;
  my $win_title = "Main menu";
  my $win_textFormat = q{
Welcome, %s!

USER INFORMATION:
  You currently %s
  %s
  %s

Choose one of the following actions (scroll down for more options):};
  my $msg = "";

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  }
  else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }

  if (-r "/tmp/message") {
    chop($msg = `cat /tmp/message`);
  }

  $retval =
    system("$DLG --title \"$win_title\" --clear --menu \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $msg) .
	   "\" 23 76 8 " .
	   "\"Add\" " .
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
	   "\"Modify Barcode\" " .
	       "\"Set, change, or delete your personal barcode    \" " .
	   "\"Modify Password\" " .
	       "\"Set, change, or delete your password           \" " .
	   "\"Transactions\" " .
	       "\"List recent transactions                       \" " .
	   " 2> /tmp/input.action");

  $action = `cat /tmp/input.action`;
  system("rm -f /tmp/input.*");

  if ($retval != 0 || $action eq "Quit") {
    #
    # confirm
    #
#     if (&confirm_win("Really quit?",
# 		     "\n       Quit the system?")) {
#       return "Quit";
#     }
#     else {
#       return "No action";
#     }
    return "Quit";
  }

  return $action;
}

sub
add_win
{
  my ($userid,$conn) = @_;

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
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	       $win_text .
	       "\" 20 65 2> /tmp/input.deposit") != 0) {
      return;
    }

    my $amt = `cat /tmp/input.deposit`;
    if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
      my $updatequeryFormat = q{
update balances
set balance = balance+%.2f
where userid = %d;

insert
into transactions
values(
  'now',
  %d,
  %.2f,
  'ADD');
      };

      if (! &confirm_win("Add amount?",
			 sprintf("\nWas the deposit amount \\\$%.2f?",
				 $amt))) {
	next;
      }

      my $result = $conn->exec(sprintf($updatequeryFormat,
				       $amt, $userid,
				       $userid, $amt));
      if ($result->resultStatus != PGRES_COMMAND_OK) {
	print STDERR "add_win: error update record...exiting\n";
	exit 1;
      }

      return;
    }

    &invalidAmount_win();
  }
}

sub
buy_win
{
  my ($userid,$conn,$type) = @_;
  my $amt;
  my $confirmMsg;

  my $updatequeryFormat = q{
update balances
set balance = balance-%.2f
where userid = %d;

insert
into transactions
values(
  'now',
  %d,
  -%.2f,
  '%s');
  };

  undef $amt;

  if (defined $type) {
    if (defined $PRICES{$type}) {
      $amt = $PRICES{$type};
      $confirmMsg = "Buy ${type}?";
    }
  }
  else {
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
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 13 50 2> /tmp/input.deposit") != 0) {
	return;
      }

      $amt = `cat /tmp/input.deposit`;
      if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
	last;
      }

      &invalidAmount_win();
    }
  }

  if (! &confirm_win($confirmMsg,
		     sprintf("\nIs your purchase amount \\\$%.2f?",
			     $amt),40)) {
    return;
  }

  my $result = $conn->exec(sprintf($updatequeryFormat,
				   $amt, $userid,
				   $userid, $amt, uc($type)));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "add_win: error update record...exiting\n";
    exit 1;
  }
}

sub
message_win
{
  my ($username,$userid,$conn) = @_;
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
		   "\nDo you want to send your message anonymously?",
		   50)) {
    $username = "anonymous";
    undef $userid;
  }

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	     $win_text .
	     "\" 18 74 \"From $username: \" 2> /tmp/input.msg") == 0) {
    my $msg = `cat /tmp/input.msg`;
    my $insertqueryFormat = q{
insert
into messages
values(
  nextval('msgid_seq'),
  'now',
  %s,
  '%s');
    };

    my $result = $conn->exec(sprintf($insertqueryFormat,
				     defined $userid ? $userid : "null",
				     $msg));
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "message_win: error inserting record...exiting\n";
      exit 1;
    }
  }
}


sub
log_win
{
  my ($username,$userid,$conn) = @_;
  my $win_title = "Transactions";
  my $logfile = "/tmp/$userid.output.log";
  my $logqueryFormat = q{
select xacttime,xactvalue,xacttype
from transactions
where userid = %d
order by xacttime;
  };

  if (! open(LOG_OUT, ">$logfile")) {
    print STDERR "log_win: unable to write to output file.\n";
    return;
  }

  my $result = $conn->exec(sprintf($logqueryFormat, $userid));
  for ($i = 0 ; $i < $result->ntuples ; $i++) {
    $time = $result->getvalue($i,0);
    $val = $result->getvalue($i,1);
    $type = $result->getvalue($i,2);

    if ($i == 0) {
      $win_title .= " since $time";
    }

    print LOG_OUT sprintf("%s: %.2f (%s)\n", $time, $val, $type);
  }

  close(LOG_OUT);

  system("$DLG --title \"$win_title\" --clear --textbox " .
	 "$logfile 24 75 2> /dev/null");

}


sub
pwd_win
{
  my ($username,$userid,$conn) = @_;
  my $win_title = "Enter Password";
  my $win_text = q{
Type your new password.  To remove an existing
password, enter "none" as your password.

NOTE: YOUR PASSWORD WILL BE ECHOED TO THE
SCREEN...MAKE SURE NO ONE IS LOOKING!
  };

  my $verify_win_text = q{
Re-type your password:
  };

  my $pwdquery = qq{
select p
from pwd
  where userid = $userid;
  };

  my $result = $conn->exec($pwdquery);
  $n = $result->ntuples;
  if ($n == 1) {
    $p = $result->getvalue(0,0);
    $s = substr($p,-2,2);
    $pwd_exists = 1;
  }
  else {
    $s = "cB";
    $pwd_exists = 0;
  }
#  print "salt is $s\n";

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	     $win_text .
	     "\" 15 52 2> /tmp/input.pwd") != 0) {
    return;
  }
  my $p = `cat /tmp/input.pwd`;

  if ($p eq "") {
    my $removequery = qq{
delete
from pwd
where userid = $userid;
    };

    $conn->exec($removequery);
    return;
  }

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	     $verify_win_text .
	     "\" 10 40 2> /tmp/input.pwd_v") != 0) {
    return;
  }
  my $p_v = `cat /tmp/input.pwd_v`;

  if ($p ne $p_v) {
    my $no_match_msg = q{
There was a mismatch between the two passwords.
No changes were made.
    };
    system("$DLG --title \"Passwords do not match\" --clear --msgbox \"" .
	   $no_match_msg .
	   "\" 8 52 2> /dev/null");
    return;
  }

  $c = crypt($p,$s);
  if ($pwd_exists == 1) {
    my $updatequery = qq{
update
pwd
set p = '$c'
where userid = $userid;
    };

    $result = $conn->exec($updatequery);
    if ($result->resultStatus == PGRES_COMMAND_OK) {
      return;
    }
  }
  else {
    my $insertquery = qq{
insert
into pwd
values(
  $userid,
  '$c');
    };

    $result = $conn->exec($insertquery);
    if ($result->resultStatus == PGRES_COMMAND_OK) {
      return;
    }
  }

  #
  # db error
  #
  my $db_error_msg = q{
There was an error updating the database.
No changes were made.
  };
  system("$DLG --title \"Database error\" --clear --msgbox \"" .
	 $db_error_msg .
	 "\" 8 52 2> /dev/null");
}


sub
unimplemented_win
{
  my $win_title = "Unimplemented function";
  my $win_text = q{
This functionality has not yet been
implemented.};

  system ("$DLG --title \"$win_title\" --clear --msgbox \"" .
	  $win_text .
	  "\" 8 40");
}
############################## ACTION WINDOWS ###############################



################################# UTILITIES #################################

sub
checkUser
{
  my ($username,$conn) = @_;

  my $queryFormat = q{
select userid
from users
where username ~* '^%s$';
  };

  if ($conn->status != PGRES_CONNECTION_OK) {
    print STDERR "checkUser: not connected...exiting.\n";
    exit 1;
  }
  $result = $conn->exec(sprintf($queryFormat,$username));

  if ($result->ntuples != 1) {
    return -1;
  }

  return ($result->getvalue(0,0));
}

sub
getPwd
{
  my ($userid,$conn) = @_;
  my $query = qq{
select p
from pwd
where userid = $userid;
  };

  if ($conn->status != PGRES_CONNECTION_OK) {
    print STDERR "getPwd: not connected...exiting.\n";
    exit 1;
  }
  $result = $conn->exec($query);

  if ($result->ntuples != 1) {
    return undef;
  }
  else {
    return $result->getvalue(0,0);
  }
}

sub
checkPwd
{
  my ($p,$guess) = @_;
  if (crypt($guess,$p) eq $p) {
    return 1;
  }

  return 0;
}


sub
getBalance
{
  my ($userid,$conn) = @_;

  my $queryFormat = q{
select balance
from balances
where userid = %d;
  };
  if ($conn->status != PGRES_CONNECTION_OK) {
    print STDERR "checkUser: not connected...exiting.\n";
    exit 1;
  }
  $result = $conn->exec(sprintf($queryFormat,$userid));

  if ($result->ntuples != 1) {
    return;
  }

  return ($result->getvalue(0,0));
}

sub
confirm_win
{
  my ($win_title,$win_text,$w,$h) = @_;
  $h ||= 7;
  $w ||= 35;

#  my $win_title = "Really quit?";
#  my $win_text = q{
#       Quit the system?};

  $retval = system("$DLG --title \"$win_title\" --clear --yesno \"" .
		   $win_text .
		   "\" $h $w 2> /dev/null");

  if ($retval == 0) {
    return 1;
  }
  else {
    return 0;
  }
}


################################# MAIN  #################################

sub
regular_login
{
  my ($username) = @_;
  $userid = &checkUser($username,$conn);

  if ($userid == -1) {
    #
    # new user!
    #

  # transaction causes problems...
  #  $conn->exec("begin");

    if (askStartNew_win($username,$conn) == -1) {
      # canceled or refused
      exit 1;
    }

    $userid = &checkUser($username,$conn);
    if (&initBalance_win($userid,$conn) < 0) {
#      $conn->exec("rollback");
      exit 1;
    }

  #  $conn->exec("commit");
  }

  $p = &getPwd($userid,$conn);
  if (defined $p && &checkPwd($p,&guess_pwd_win()) == 0) {
    &invalidPassword_win();
    exit 1;
  }

  # Output some annonying message if balance is really in the red
  $balance = &getBalance($userid,$conn);
  if ($balance < 10.00) {
  #  system("$FEST \"It's about time to add money to your account!\"&");
  }

  my $action = "";
  do {
    #
    # refresh the balance
    #
    $balance = &getBalance($userid,$conn);
    if (! defined $balance) {
      print "MAIN: no balance from database...exiting.\n";
      exit 1;
    }

    #
    # get the action
    #
    $action = &action_win($username,$userid,$balance,$conn);

    $_ = $action;
   SWITCH: {
     /^Add$/ && do {
       &add_win($userid,$conn);
       last SWITCH;
     };
  
     (/^Candy\/Can of Soda$/ || /^Snapple$/ || /^Juice$/ ||
      /^Popcorn\/Chips\/etc.$/) && do {
       &buy_win($userid,$conn,$_);
       last SWITCH;
     };
  
     /^Buy Other$/ && do {
       &buy_win($userid,$conn);
       last SWITCH;
     };
  
     /^Message$/ && do {
       &message_win($username,$userid,$conn);
       last SWITCH;
     };
  
     /^Transactions$/ && do {
       &log_win($username,$userid,$conn);
       last SWITCH;
     };
  
     /^Modify Barcode$/ && do {
       &barcode_win($username,$userid,$conn);
       last SWITCH;
     };
  
     /^Modify Password$/ && do {
       &pwd_win($username,$userid,$conn);
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
} 


sub
barcode_login
{
  my ($logintext) = @_;

  # Do some preprocessing first: decode and retrieve corresponding username
  $barcode = decode_barcode($logintext); 
  my $selectqueryFormat = q{
    select username 
    from users 
    where userbarcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples != 1) {
    # does not exist
    my $win_title = "Invalid barcode";
    my $win_text = q{
I could not find this barcode in the database. If you're 
an existing user you can change your barcode login from 
the main menu.  If you're a new user you'll need to first 
create a new account by entering a valid text login id.}; 
    system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 10 65 2> /dev/null");
    exit 1;
  } else {
    $username = $result->getvalue(0,0);
    $userid = &checkUser($username,$conn);
    &barcode_action_win($username,$userid,$conn);
  }
}


###
### main program
###

$REVISION = q{
$Revision: 1.13 $
};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
}
else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";

do {
  $logintext = &login_win($REVISION);
} while ($logintext eq "");

# set up db
$conn = Pg::connectdb("dbname=bob");
if ($conn->status == PGRES_CONNECTION_BAD) {
  print STDERR "MAIN: error connecting to database...exiting.\n";
  print STDERR $conn->errorMessage;
  exit 1;
}

$username = "";

if (&isa_barcode($logintext)) {
  &barcode_login($logintext);
} else {
  &regular_login($logintext);
}

