#!/usr/bin/perl -w

if (! defined $ARGV[0]) {
  print STDERR "no file given.\n";
  exit 1;
}

(undef,undef,undef,undef,undef,undef,undef,undef,$atime) =
  stat($ARGV[0]);

$now = time;
$diff = $now - $atime;

if (! defined $ARGV[1]) {
  print "diff is $diff\n";
}
else {
  if ($diff < $ARGV[1]) {
    exit 1;
  }
  else {
    exit 0;
  }
}
