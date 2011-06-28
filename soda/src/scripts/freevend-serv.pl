#!/usr/bin/perl
use warnings;
use strict;
use FindBin qw[$Bin];
use lib "$Bin/../lib";
use ServIO;

sioOpen("FREEVEND-SERV", "1.11");
sioHookExit();

sioWrite('DATA', 'SYS-ACCEPT', '*');

sioWrite('DATA', 'VEND-RESET');
while (1) {
  my $ln = sioRead();
  my ($cmd, @a) = split(/\t/, $ln);
  if ($cmd eq 'VEND-REQUEST') {
	sioWrite('LOG', "vend request for can $a[0] (price $a[1]) - approved");
	sioWrite('DATA', 'VEND-APPROVED');
  } elsif ($cmd eq 'VEND-READY') {
	sioWrite('DATA', 'VEND-SSTART', -1);
  } elsif ($cmd eq 'VEND-SUCCESS') {
	sioWrite('LOG', "vend request ($a[0]) was sucessful");
  } elsif ($cmd eq 'VEND-FAILURE') {
	sioWrite('LOG', "vend request has failed");
  };
};

