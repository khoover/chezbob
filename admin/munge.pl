#!/usr/bin/perl -w

$started = 0;
foreach (<>) {
  chop;

  if (/^----------/) {
    $started = 1;
    next;
  }

  if ($started == 0) {
    next;
  }

  @orderline = split(/  +/);
  $numElts = @orderline;
  if ($numElts != 3) {
    print STDERR "warning: order line doesn't parse: \"$_\"\n";
    next;
  }

  (undef,$qty,$item) = @orderline;
  print "$item $qty\n";
}
