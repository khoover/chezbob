# deposit.pl
#
# Routines for adding money to a chez bob account
#
# $Id: deposit.pl,v 1.1 2001-05-18 05:41:44 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

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
      &invalid_deposit_win();
    }
  }
}


sub
invalid_deposit_win
{
  my $win_title = "Invalid amount";
  my $win_text = q{
Valid deposits are positive numbers with up
to two decimal places of precision.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 8 50 2> /dev/null");
}

1;
