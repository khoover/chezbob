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
# $Id: dlg.pl,v 1.23 2001-08-21 00:01:34 bob Exp $
#

$DLG = "$BOBPATH/dialog-0.9a/dialog";
$CANCEL = -1;
$TMP = "$BOBPATH";		# locn of temp files for dialog output


sub
confirm_win
{
  my ($win_title,$win_text,$w,$h) = @_;
  $h ||= 7;
  $w ||= 40;

  my($retval, $res) = &get_dialog_result("--title \"$win_title\" --clear " .
         "--cr-wrap --yesno \"" .  $win_text .  "\" $h $w");
  return ($retval == 0);
}


sub
get_barcode_win
{
  my ($msg, $w, $h) = @_;
  $h ||= 7;
  $w ||= 40;

  my $win_title = "Scan Barcode";
  my ($err, $result) = &get_dialog_result("--title \"$win_title\" --clear " .
                             "--cr-wrap --inputbox \"$msg\" $h $w");
  return undef if ($err != 0);
  return $result;
}


sub
remove_tmp_files
{
  system("rm -f $TMP/input.*");
  system("rm -f $TMP/*.output.log");
}

sub
get_dialog_result
{
    my $cmd = shift;
    local *CHILDIN;
    local *CHILDOUT;
    local *CHILDERR;
    my $pid;
    my $stderrLine = "";
    my $stdoutLine = "";
    my $line;
    use FileHandle;
    use IPC::Open3;
    use POSIX;

    $pid = open3(*CHILDIN, *CHILDOUT, *CHILDERR, "$DLG $cmd") ||return (-2, "");
    return(-3, "") if ($pid == 0 || $pid == -1);
    return(-4, "") if (!defined(CHILDIN) || !defined(CHILDOUT) || !defined(CHILDERR));
    close(CHILDIN);
    return (-1, "") if(-1 == waitpid($pid, 0));
    return (($? >> 8), "") if ($? != 0);

    while ($line = <CHILDERR>)
    {
        $stderrLine .= $line;
    }
    while ($line = <CHILDOUT>)
    {
        $stdoutLine .= $line;
    }
    close(CHILDERR);
    close(CHILDOUT);
    chomp $stderrLine;
    chomp $stdoutLine;

    return (0, $stderrLine);
    #return (0, $stderrLine, $stdoutLine);
}

1;
