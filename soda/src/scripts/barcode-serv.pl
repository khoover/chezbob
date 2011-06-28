#!/usr/bin/perl
use warnings;
use strict;
use FindBin qw[$Bin];
use lib "$Bin/../lib";
use ServIO;

my $SPORT = "/dev/ttyUSB_PRO*";

sioOpen("BARCODE-SERV", "1.01");
sioHookExit();

sioWrite('DATA', 'SYS-ACCEPT', 'BARCODE-');

sioWrite('DATA', 'BARCODE-RESET');

my $SERFH;
my $serbuff = '';
my $sbtick = 0;

while (1) {
  my $rin = '';
  vec($rin, fileno($SERFH), 1) = 1 if $SERFH;
  vec($rin, fileno($ServIO::FH), 1) = 1;
  (select($rin, undef, undef, 0.5)>=0) || die "select() failed: $!\n";

  if (vec($rin, fileno($ServIO::FH), 1)) {
	while (defined(my $ln = sioRead(0))) {
	  my ($cmd, @a) = split(/\t/, $ln);
	};
  };

  if ($SERFH && vec($rin, fileno($SERFH), 1)) {
	my $rv = sysread($SERFH, $serbuff, 8192, length($serbuff));
	if ($rv <= 0) {
	  sioWrite('WARN', "serial port read failure: ".(($rv==0)? "EOF" : $!));
	  close $SERFH;
	  $SERFH = undef;
	  next;
	};
	while ($serbuff =~ s/^(.*?)\x00([A-Z])([\x20-\x7F]+)\x0D//) {
	  my ($pmj, $type, $code) = ($1, $2, $3);
	  sioWrite('DEBUG', "pre-message junk: ".mkMessage($pmj)) 
		if length($pmj);
	  if ($code eq 'NV') {
		sioWrite('DATA', "BARCODE-BADSCAN", $type);
	  } else{
		sioWrite('DATA', "BARCODE-SCAN", $code, $type);
	  };
	};
	$sbtick = time() + 10;
  };

  if ($sbtick < time()) {
	sioWrite('DEBUG', "non-message junk: ".mkMessage($serbuff)) 
		if length($serbuff);
	$serbuff = '';
	serOpen() unless $SERFH;
	$sbtick = time() + 10;
  };

};



sub serOpen {
  close $SERFH if $SERFH;
  $SERFH = undef;

  my $rport = (glob($SPORT))[-1] || '';
  unless ($rport && (-r $rport)) {
	sioWrite('LOG', "Cannot find $SPORT ($rport) or no access to it");
	return 0;
  };

  system("stty -F '$rport' 9600 raw pass8 -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke");

  unless (open($SERFH, "+< $rport")) {
	$SERFH = undef;
	sioWrite('LOG', "Cannot open $SPORT ($rport): $!");
	return 0;
  };

  return 1;
};

sub mkMessage {
  my ($msg) = @_;
  $msg =~ s/([^\x20-\x7E])/sprintf("%%%.2X", unpack("C", $1))/ge;
  return qq["$msg"];
};
