#!/usr/bin/perl -w

# socialhour.pl
# 
# Alternate interface to Chez Bob to be run during social hours, to accept
# donations via the Bank of Bob.  This shares a fair bit of code with the
# normal Chez Bob code, but the interface is a bit simpler.
#
# Copied from bobmenu.pl.  Really, I should somehow merge these to avoid the
# code duplication, but at least there isn't too much code duplication...
#
# Written by Michael Vrable <mvrable@cs.ucsd.edu>.

# Find the full path to this executable file (bobmenu) and store it in
# global variable BOBPATH.  You *must* prefix any require paths with this
# variable so that Perl can find the files.

open(FILE, "which $0 |") || die "can't do which $0: $!\n";
my $fullpath = <FILE>;
close(FILE) || die "can't close\n";
$BOBPATH = substr($fullpath, 0, rindex($fullpath, '/'));

my $MAX_PURCHASE = 100;

require "$BOBPATH/login.pl";	# login_win
require "$BOBPATH/bob_db.pl";	# database routines
require "$BOBPATH/buyitem.pl";  # buy routines
require "$BOBPATH/dlg.pl";      # locn of dialog exe

# Attempt to determine the Mercurial revision number of the current code.  We
# expect at least 12 hex digits.
my $hg_id = `cd $BOBPATH; hg id`;
if ($hg_id =~ /^([[:xdigit:]]{12}\S*)/) {
  $REVISION = $1;
} else {
  $REVISION = "unknown";
}

print "rev is $REVISION\n";
&bob_db_connect;
&bob_db_set_source('socialhour');
&speech_startup;

sub
social_login_win
{
  my ($rev) = @_;
  my $username = "";
  my $errCode;
  my $back_title = "Chez Bob 2001 (changeset $rev)";
  my $win_title = "Social Hour Donations";
  my $win_text = q{
Welcome to the B.o.B. 2001!

You can use your Bank of Bob account to donate to
Social Hour.  Enter your username to continue.};

  ($errCode, $username) = &get_dialog_result("--backtitle \"$back_title\" --title \"$win_title\" --clear --cr-wrap --inputbox \"" . $win_text .  "\" 14 55 \"$username\"");

  return "" if ($errCode != 0);
  return $username;
}

sub
social_process_login
{
  my ($username, $checkpass) = @_;
  my $userid = &bob_db_get_userid_from_username($username);

  if ($userid == $NOT_FOUND) {
    # Don't support creating new users from here yet.
    # Error message?
    return;
  }

  my $pwd = &bob_db_get_pwd($userid);
  if ($pwd && $pwd =~ /^closed/) {
    &expiredAccount_win;
    return;
  }
  if ($checkpass) {
    if (defined $pwd && &checkPwd($pwd, &guess_pwd_win) == 0) {
      &invalidPassword_win;
      return;
    } 
  }

  &social_action_win($userid, $username);
}

sub
social_action_win
{
  my ($userid, $username) = @_;
  my $nickname = &bob_db_get_nickname_from_userid($userid);
  my $userbarcode = &bob_db_get_userbarcode_from_userid($userid);
  my $last_purchase = "";
  my $action = "";

  &get_user_profile($userid);
  
  my $balance = &bob_db_get_balance($userid);

MAINLOOP:
  while ($action ne "Quit") {

    $balance = &bob_db_get_balance($userid);
    if ($balance == $NOT_FOUND) {
      &report_fatal("mainmenu: no balance from database.\n");
    }

    $action = &social_show_action_win($username, $userid, $balance, $last_purchase);
    my $curr_purchase = "";

    # Otherwise, check for any of the visible menu options
    $_ = $action;
    SWITCH: {
      /^Add Money$/ && do {
        &add_win($userid);
        last SWITCH;
      };

      /^Donate$/ && do {
        &social_donate($userid, 0.25);
        last SWITCH;
      };
  
      /^Donate Other$/ && do {
        &social_donate($userid);
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
  
      /^Password$/ && do {
        &pwd_win($userid);
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
    }

  }  # WHILE
} 

sub
social_show_action_win
{
  my ($username,$userid,$balance,$last_purchase) = @_;
  my $win_title = "Main Menu";
  my $win_textFormat = q{
Welcome, %s!
USER INFORMATION:
  You currently %s
  %s
  Last Item Purchased: %s

Choose one of the following actions};

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }

  my ($retval, $action) =
    &get_dialog_result("--title \"$win_title\" --clear --cr-wrap " .
                       "--menu \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $last_purchase) .
	   "\" 23 76 7 " .
	   "\"Donate\" " .
	       "\"Donate \\\$0.25 to Social Hour                 \" " .
	   "\"Donate Other\" " .
	       "\"Donate other amount to Social Hour             \" " .
	   "\"Add Money\" " .
	       "\"Add money to your Chez Bob account             \" " .
	   "\"Message\" " .
	       "\"Leave a message for Bob                        \" " .
	   "\"Transactions\" " .
	       "\"List recent transactions                       \" " .
	   "\"My Chez Bob\" " .
	       "\"Update your personal settings                     \" " .
	   "\"Password\" " .
	       "\"Set your password           \" " .
	   "\"Quit\" " .
	       "\"Finished\!                                      \" ");

  if ($retval != 0 || $action eq "Quit") {
    return "Quit";
  }

  return $action;
}

sub
social_donate
{
  my ($userid, $amt) = @_;

  my $confirmMsg;

  if (!defined $amt) {
    $confirmMsg = "Donation amount?";

    my $win_title = "Donate to Social Hour";
    my $win_text = q{
  How much would you like to donate to Social Hour?
  (This amount will be deducted from your BoB account.)};

    while (1) {
      (my $err, $amt) = &get_dialog_result("--title \"$win_title\" --clear ".
                        "--cr-wrap --inputbox \"" .  $win_text .  "\" 10 65");
      return if ($err != 0);

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
  }

  if (! &confirm_win($confirmMsg,
                   sprintf("\nIs your donation amount \\\$%.2f?", $amt),40)) {
    return;
  }

  my $buy = "SOCIAL HOUR";
  &bob_db_update_balance($userid, -$amt, $buy);
}

do {
  $logintxt = &social_login_win($REVISION);
} while ($logintxt eq "");

# We'll still allow barcode logins, even though we probably won't have a
# barcode scanner available at Social Hour.
my $barcode = &preprocess_barcode($logintxt); 
if (&isa_valid_user_barcode($barcode)) {
  my $username = &bob_db_get_username_from_userbarcode($barcode);
  if (defined $username) {
    &social_process_login($username, 0);
  } else {
    if (defined &bob_db_get_productname_from_barcode($barcode)) {
      &pricecheck_win($barcode);
    } else {
      &user_barcode_not_found_win;
    }
  }
} elsif (&isa_valid_username($logintxt)) {
  &social_process_login($logintxt, 1);
} else {
  &invalidUsername_win;
} 

&remove_tmp_files;
&speech_shutdown;

&bob_db_disconnect;
