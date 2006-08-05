# usrlog.pl
#
# A Routine for displaying the user's past transactions.

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

sub
log_win
{
  my ($userid) = @_;
  my $win_title = "Transactions";
  my $logfile = "$TMP/$userid.output.log";

  &bob_db_log_transactions($userid, $logfile);

  &get_dialog_result("--title \"$win_title\" --clear --textbox " .
         "$logfile 24 75");
}

1;
