#!/usr/bin/perl -w

$DLG = "/usr/bin/dialog";

($len) = @ARGV;

$title = "B.o.B. 2k down";
$msg = q{
Bank of Bob 2000 currently unavailable.  We should be
back %s.

Sorry for the inconvenience!

-bob
};

system("$DLG --title \"$title\" --msgbox \"" .
       sprintf($msg, defined $len && $len ne "--" ? "in $len" : "soon") .
       "\" 12 60 2> /dev/null");
