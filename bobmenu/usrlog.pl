# usrlog.pl
#
# A Routine for displaying the user's past transactions.
# 
# $Id: usrlog.pl,v 1.4 2001-06-08 17:55:16 cse210 Exp $
#

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

sub
log_win
{
  my ($userid) = @_;
  my $win_title = "Transactions";
  my $logfile = "$TMP/$userid.output.log";

  &bob_db_log_transactions($userid, $logfile);

  system("$DLG --title \"$win_title\" --clear --textbox " .
         "$logfile 24 75 2> /dev/null");
}

1;
