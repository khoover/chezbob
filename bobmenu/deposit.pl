# deposit.pl
#
# Routines for adding money to a chez bob account
#
# $Id: deposit.pl,v 1.8 2001-06-25 21:41:37 bellardo Exp $
#

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

my $MAX_DEPOSIT = 100;


sub
add_win
#
# Prompt the user for the amount of money they're adding to their account.
# Update balance table in the database.  Return amt deposited on success,
# $CANCEL otherwise.
#
{
  my ($userid) = @_;

  my $dlgErr;
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
    ($dlgErr, $amt) = &get_dialog_result("--title \"$win_title\" --clear " .
                         "--cr-wrap --inputbox \"" .  $win_text .  "\" 20 65");
    return $CANCEL if ($dlgErr != 0);

    if ($amt =~ /^\d+$/ || $amt =~ /^\d*\.\d{0,2}$/) {
      if ($amt > $MAX_DEPOSIT) {
        &exceed_max_deposit_win;
        next;
      }

      if (! &confirm_win("Add Amount?",
                         sprintf("\nWas the deposit amount \\\$%.2f?", $amt))) {
        next;
      }

      &bob_db_update_balance($userid, $amt, "ADD");
      return $amt;
    } else {
      &invalid_deposit_win;
    }
  }
}


sub
exceed_max_deposit_win
{
  my $win_title = "Invalid Amount";
  my $win_text = "\nThe maximum deposit is \\\$$MAX_DEPOSIT";

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 7 35");
}


sub
invalid_deposit_win
{
  my $win_title = "Invalid Amount";
  my $win_text = q{
Valid deposits are positive numbers with up
to two decimal places of precision.};

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 8 50");
}


1;
