# dlg.pl
#
# This file was intended to encapsulate the calls to the dialog program
# but that's too much of a pain.  Contains the location of the custom 
# dialog program we're using.
#
# $Id: dlg.pl,v 1.3 2001-05-19 23:51:19 mcopenha Exp $
#

$DLG = "./dialog-0.9a/dialog";
$CANCEL = -1;

sub
confirm_win
{
  my ($win_title,$win_text,$w,$h) = @_;
  $h ||= 7;
  $w ||= 40;

  $retval = system("$DLG --title \"$win_title\" --clear --cr-wrap --yesno \"" .
		   $win_text .  "\" $h $w 2> /dev/null");
  return ($retval == 0);
}


1;
