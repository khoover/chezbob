# dlg.pl
#
# This file was intended to encapsulate the calls to the dialog program
# but that's too much of a pain.  Contains the location of the dialog 
# executable.  It's important to note that we're using a custom version
# of the dialog program; chez bob won't work correctly with the barcode
# scanner if you use a stock version of the dialog program.  Specifically,
# we made the following changes to dialog version dialog-0.9a-20010429
# (http://dickey.his.com/dialog/dialog.html):
#
# 1. Modified dialog's 'menu' window so that any keyboard input is 
#    redirected to a file called '/tmp/menuout' that's stored in the current
#    directory.  We made this change so that a user could use the 
#    barcode scanner while the main menu was showing.  Modified file
#    menubox.c.
#
# 2. Made changes so that the passwordbox echoes asteriks to the screen
#    instead of echoing nothing.  Changed files dialog.c, inputstr.c,
#    and textbox.c.  Changes were taken from a broken patch file.
#
# Look for comments in the dialog code that begin with 'MAC'
#
# $Id: dlg.pl,v 1.18 2001-06-10 01:58:59 cse210 Exp $
#

$DLG = "$BOBPATH/dialog-0.9a/dialog";
$CANCEL = -1;
$TMP = "$BOBPATH";		# locn of temp files for dialog output
$MENUOUT = "/tmp/menuout"; 	# tmp file created by dialog's menu


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


sub
get_barcode_win
{
  my ($msg, $w, $h) = @_;
  $h ||= 7;
  $w ||= 40;

  my $win_title = "Scan Barcode";
  if (system("$DLG --title \"$win_title\" --clear --cr-wrap " .
      " --inputbox \"$msg\" $h $w 2> $TMP/input.barcode") != 0) {
    return undef;
  }

  return `cat $TMP/input.barcode`;
}


sub
remove_tmp_files
{
  system("rm -f $TMP/input.*");
  system("rm -f $TMP/*.output.log");
  system("rm -f $MENUOUT");
}

1;
