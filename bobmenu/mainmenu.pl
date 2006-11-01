# mainmenu.pl
#
# The main menu for Chez Bob which currently contains options for depositing
# money, purchasing products, updating user settings (passwd, nickname,
# barcode id), viewing transactions, sending messages to Bob, and updating
# user profiles.  Routines for each of these options is contained in separate
# files.

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
      system("ogg123 -q $BOBPATH/negative_balance.ogg >/dev/null &");
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
	   "\" 24 76 7 " .
	   "\"Soda Login\" " .
	       "\"Log in to the soda machine                      \" " .
	   "\"Add Money\" " .
	       "\"Add money to your Chez Bob account             \" " .
	   "\"Extra Items\" " .
	       "\"Buy espresso and other items from Bob             \" " .
	   "\"Buy Other\" " .
	       "\"Manually enter purchase price                    \" " .
	   "\"Message\" " .
	       "\"Leave a message for Bob                        \" " .
	   "\"Transactions\" " .
	       "\"List recent transactions                       \" " .
	   "\"Quit\" " .
	       "\"Finished\!                                      \" " .
	   "\"My Chez Bob\" " .
	       "\"Update your personal settings                     \" " .
	   "\"Barcode ID\" " .
	       "\"Set your personal barcode login                \" " .
	   "\"Nickname\" " .
	       "\"Set your nickname                             \" " .
	   "\"Password\" " .
	       "\"Set your password           \" ");

  if ($retval != 0 || $action eq "Quit") {
    return "Quit";
  }

  if ($action eq "Extra Items") {
      $action = &extras_win();
  }

  return $action;
}


sub
extras_win
#
# Read a list of barcodes from $BOBPATH/extras.txt and provide the user with a
# menu to purchase one of them.
#
{
  my @barcode_list = ();        # Barcodes listed, in order
  my %extras = ();              # Product information, keyed by barcode

  open EXTRAS, "$BOBPATH/extras.txt" or do {
    &noextras_win();
    return "No action";
  };

  while (<EXTRAS>) {
    # We allow comments in extras.txt.  Ignore them.
    chomp;
    s/#.*$//;

    # Valid barcodes should be at least six digits long.  If we find one, try
    # to look it up.
    if (m/(\d{6,})/) {
      my $barcode = $1;
      my $name = &bob_db_get_productname_from_barcode($barcode);
      my $price = &bob_db_get_price_from_barcode($barcode);
      next unless $name && $price;

      # We're currently passing off text to dialog as a command with shell
      # expansion, so strange characters could throw us off.  The name will be
      # enclosed in a single set of double quotes.  Be conservative in which
      # characters we allow through in the product name.
      $name =~ s/[^-A-Za-z0-9()&:.,'+ ]//g;

      push @barcode_list, $barcode;
      $extras{$barcode} = [$name, $price];
    }
  }

  close EXTRAS;
  unless (@barcode_list) {
    &noextras_win();
    return "No action";
  }

  my $win_title = "Extra Items Menu";
  my $win_text = "Choose one of the following items to purchase.";

  my $menu_items = "";
  foreach (0 .. $#barcode_list) {
    my $barcode = $barcode_list[$_];
    my ($name, $price) = @{$extras{$barcode}};
    $menu_items .= sprintf(qq{ %d "%s (\\\$%.2f)"}, $_ + 1, $name, $price);
  }

  my ($retval, $action) =
    &get_dialog_result(qq{--title "$win_title" --clear --cr-wrap --menu } .
                       qq{"$win_text" 20 76 12 $menu_items});

  if ($retval != 0) {
    return "No action";
  }

  if ($action =~ /^(\d+)$/) {
    my $n = $1 - 1;
    if ($n >= 0 && $n <= $#barcode_list) {
      return $barcode_list[$n];
    }
  }

  return "No action";
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
noextras_win
{
  my $win_title = "No Extra Items";
  my $win_text = "No additional items are available for purchase at this time.";

  &get_dialog_result ("--title \"$win_title\" --clear --msgbox \"" .
	  $win_text .  "\" 8 40");
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
