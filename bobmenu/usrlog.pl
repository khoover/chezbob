# usrlog.pl
#
# A Routine for displaying the user's past transactions.
# 
# $Id: usrlog.pl,v 1.2 2001-05-21 21:21:19 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

sub
log_win
{
  my ($userid) = @_;
  my $win_title = "Transactions";
  my $logfile = "/tmp/$userid.output.log";

  &bob_db_log_transactions($userid, $logfile);

  system("$DLG --title \"$win_title\" --clear --textbox " .
         "$logfile 24 75 2> /dev/null");
}

1;
