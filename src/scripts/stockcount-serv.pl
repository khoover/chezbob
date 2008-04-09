#!/usr/bin/perl
use warnings;
use strict;
use FindBin qw[$Bin];
use lib "$Bin/../lib";
use ServIO;

use PHP::Serialization qw(serialize unserialize);
use Data::Dumper; $Data::Dumper::Useqq=1;  $Data::Dumper::Terse=1; $Data::Dumper::Sortkeys=1; $Data::Dumper::Indent=1;

my $DATAFILE = "/var/soda/stockcount.psr";

# correct empty initial data (make sure no trailing EOL present):
#   a:1:{s:2:"r1";a:1:{s:4:"name";s:5:"empty";}}

sioOpen("STOCKCNT-SERV", "1.15");
sioHookExit();
sioWrite('DATA', 'SYS-ACCEPT', '*');

my $psr_enc;
{
  my $FH;
  local $/;
  open($FH, "< $DATAFILE")||die "Cannot open $DATAFILE: $!\n";
  $psr_enc = <$FH>;
  close $FH;
};
my $PSR = unserialize($psr_enc) || die "Cannot parse data in $DATAFILE - invalid format?\n";
#print Dumper($PSR);

fillSodaNames();

writeData();

my $sodatype = undef;

while (1) {
  my $ln = sioRead();
  my $rel = 0;
  my ($cmd, @a) = split(/\t/, $ln);
  if ($cmd eq 'VEND-REQUEST') {
	$sodatype = sprintf("r%.2d", $a[0]);
  } elsif ($cmd eq 'VEND-SUCCESS') {
	if ($sodatype) {
	  $$PSR{$sodatype}{'instock'}=1;
	  $$PSR{$sodatype}{'sold'}++;
	  $$PSR{$sodatype}{'lsale'}=time();
	  writeData();
	  $sodatype = undef;
	  $rel = 1;
	};
  } elsif ($cmd eq 'VEND-DENIED') {
	$sodatype = undef;
  } elsif (($cmd eq 'VEND-FAILURE') || ($cmd eq 'VEND-FAILED') || ($cmd eq 'VEND-READY')) {
	if ($sodatype) {
	  $$PSR{$sodatype}{'instock'}=0;
	  $$PSR{$sodatype}{'nosold'}++;
	  $$PSR{$sodatype}{'lsale'}=time();
	  writeData();
	  $sodatype = undef;
	  $rel = 1;
	};
  };
  if ($rel) {
	sioWrite('DATA', 'UI-RELOAD');
  };
};




sub writeData {
  my $FH;
  local $/;
  unlink("$DATAFILE.old");
  rename("$DATAFILE", "$DATAFILE.old");
  open($FH, "> $DATAFILE")||die "Cannot open $DATAFILE: $!\n";
  print $FH serialize($PSR);
  close $FH;
};

sub fillSodaNames {
  delete $$PSR{'1'};
  $$PSR{'r01'}{'name'} = "Coca Cola";
  $$PSR{'r02'}{'name'} = "Pepsi Cola";
  $$PSR{'r03'}{'name'} = "Diet Coke";
  $$PSR{'r04'}{'name'} = "Diet Pepsi";
  $$PSR{'r05'}{'name'} = "Mountain Dew";
  $$PSR{'r06'}{'name'} = "Dr. Pepper";
  $$PSR{'r07'}{'name'} = "Diet Dr. Pepper";
  $$PSR{'r08'}{'name'} = "Sunkist Orange";
  $$PSR{'r09'}{'name'} = "BRISK Ice Tea";
  $$PSR{'r10'}{'name'} = "Mystery drink";
  foreach my $v (values %$PSR) {
	$$v{'instock'} = 1 unless defined $$v{'instock'};
	$$v{'nosold'} = 0 unless defined $$v{'nosold'};
	$$v{'sold'} = 0 unless defined $$v{'sold'};
  };
  #if ($$PSR{'r08'}{'sold'} > 100000) { $$PSR{'r08'}{'sold'} -= 100000; };
  delete $$PSR{'r1'};
};


