#!/usr/bin/perl -w

do 'bc_win.pl';
do 'kbd_win.pl';
do 'bob_db.pl';

$DLG = "/usr/bin/dialog";

###
### main program
###

$REVISION = q{$Revision: 1.22 $};
if ($REVISION =~ /\$Revisio[n]: ([\d\.]*)\s*\$$/) {
  $REVISION = $1;
} else {
  $REVISION = "0.0";
}

print "rev is $REVISION\n";

&bob_db_connect;

while (1) {
  my $logintxt = &login_win($REVISION);

  # Check if we're dealing with a regular username or a barcode
  if (&isa_barcode($logintxt)) {
    &barcode_login($logintxt);
  } elsif (isa_valid_username($logintxt)) {
    &kbd_login($logintxt);
  } else {
    &invalidUsername_win();
    next;
  } 
} 


sub
barcode_login
{
  my ($logintext) = @_;

  # Do some preprocessing first: decode and retrieve corresponding username
  $barcode = decode_barcode($logintext); 
  my $userid = &bob_db_get_userid_from_barcode($barcode);
  if ($userid == -1) {
    # does not exist
    &barcode_not_found;
  } else {
    &barcode_action_win($userid);
  }
}


sub
login_win
{
  my ($rev) = @_;

  my $username = "";
  my $win_title = "Bank of Bob 2001 (v.$rev)";
  my $win_text = q{
Welcome to the B.o.B. 2K!


Enter your username or scan your personal barcode. 
(If you are a new user enter a new username):
};

  system("$DLG --title \"$win_title\" --clear --inputbox \"" .
         $win_text .  "\" 14 55 \"$username\" 2> /tmp/input.main");

  $txt = `cat /tmp/input.main`;
  system("rm -f /tmp/input.*");

  return $txt;
}


sub
kbd_login
{
  my ($username) = @_;
  $userid = &bob_db_get_userid_from_username($username);

  if ($userid == -1) {
    #
    # new user!
    #

    if (askStartNew_win($username) == -1) {
      # canceled or refused
      exit 1;
    }

    $userid = &bob_db_get_userid_from_username($username);
    if (&initBalance_win($userid) < 0) {
      exit 1;
    }
  }

  $p = &bob_db_get_pwd($userid);
  if (defined $p && &checkPwd($p,&guess_pwd_win()) == 0) {
    &invalidPassword_win();
    exit 1;
  }

  my $action = "";
  do {
    #
    # refresh the balance
    #
    $balance = &bob_db_get_balance($userid);
    if (! defined $balance) {
      print "MAIN: no balance from database...exiting.\n";
      exit 1;
    }

    #
    # get the action
    #
    $action = &action_win($username,$userid,$balance);

    $_ = $action;
   SWITCH: {
     /^Add$/ && do {
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
  
     /^Modify Barcode$/ && do {
       &barcode_win($userid);
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
} 
