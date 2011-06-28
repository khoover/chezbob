package ServIO;

@EXPORT=qw[ sioOpen sioRead sioWrite sioClose sioOnMessage sioHookExit sioConf ];


#
#   IMPLEMENTATION
#

@ISA=qw[Exporter];
require Exporter;
use warnings;
use strict;
use IO::Socket::INET;
use Time::HiRes;
use Cwd;
use FindBin qw[$Bin];
#use Carp qw[cluck]; $SIG{'__WARN__'} = sub { cluck(@_); }; $::NO_SERVIO_WARN=1;

# global variables

# filehandle
our $FH = 0;

# read buffer
our $rbuff = '';

# handlers (map regExp->handler)
our %handlers;

# handler order (most recent first)
our @regexps;

# config array (undef if not loaded yet)
our $CONF;
#config files (filename => cfile)
our %CONF_FILES;

# time config filaes were last stat'ed
our $confcheck;

our $needclose;

# appname from init
our $appname = '';

sub sioOpen {
  my ($appname_a, $appversion, $clientid) = @_;
  $appversion || die "AppVersion not specified in sioOpen\n";
  $FH && die "sioOpen called twice!\n";
  $clientid ||= cwd();


  $appname = $appname_a;

  my $pver = "106";
  $pver = "101" if ($appname_a =~ s/^\+//);
  $pver = "103" if ($appname =~ s/\*$//);

  my $ctrlport = $ENV{'SODACTRL_PORT'};
  unless ($ctrlport) {
	eval { $ctrlport = sioConf("SODACTRL_PORT"); };
  };
  $ctrlport || die "Error! SODACTRL_PORT is not set!\n";
  my $ctrlip = ($ENV{'SODACTRL_IP'}||'127.0.0.1');
  $FH = IO::Socket::INET->new
	( PeerAddr => $ctrlip,
	  PeerPort => $ctrlport,
	  Proto => 'tcp',
	  Blocking => 1,
	)
  || die "Cannot connect to $ctrlip:$ctrlport: $!\n";
  binmode $FH;

  sioWrite('DATA', "SYS-INIT", $pver, $appname, $appversion, $$, $clientid);
  my $rv = sioRead(10);

  die "Server initial reponse timed out\n" unless $rv;
  if ($rv =~ m/^SYS-NOTWELCOME\t([^\t]*)\t([^\t]+)/) {
	chomp $rv;
	die "Server rejected us ($1): $2\n";
  } elsif ($rv !~ m/^SYS-WELCOME\t/) {
	chomp $rv;
	$rv =~ s/[\x00-\x1F]/\#/g;
	die "Server initial response is junk: $rv\n";
  };

  sioOnMessage("SYS-CPING", sub {
				 my ($msginfo, $message, @args) = @_;
				 sioWrite('DATA', "SYS-CPONG",  @args);
			   });

  return 1;
};

sub sioHookExit {
  $SIG{'__DIE__'} = sub {
	no warnings 'uninitialized';
	return if $^S; # fix perl bug
	my @trace;
	my $err = join("", @_); chomp $err;
	sioWrite('ERROR', "Perl Fatal Error", $err);
	my $dumpl = 10;
	my $prev = "";
	for my $level (0..$dumpl) {
	  my ($package, $filename, $line, $sub, $hasargs,
		  $wantarray, $evaltext, $is_require, $hints, $bitmask) = caller($level);       
	  last unless $filename;
	  $filename =~ s|^.*/([^/]+)$|$1|;
	  sioWrite('WARN', "StackTrace", $level, "$sub, $prev") if $level;
	  $prev = "$filename:$line"; # filename info is delayed by 1 frame
	};
	sioWrite('WARN', "StackTrace", '-', "$prev") if $prev;
	print STDERR $err."\n";
	sioClose("-1", "Perl error: $err");
	exit(18);
  };

  unless ($::NO_SERVIO_WARN) {
	$SIG{'__WARN__'} = sub {
	  no warnings 'uninitialized';
	  my $msg = $_[0]; chomp $msg;
	  print STDERR $_[0];
	  sioWrite('WARN', $msg);
	};
  };

  $needclose = 1;

};

END {
  if ($needclose) {
	sioClose(0, "");
  };
};


sub sioWrite {
  my ($type, $cmd, @args) = @_;

  #$FH || die "sioWrite called before sioOpen\n";

  my $data = "";
  if ($type eq "DATA") {
	# do nothing else
  } elsif ($type eq "LOG") {
	$data = "SYS-LOG\t$appname\t";
  } elsif ($type eq "ERROR") {
	$data = "SYS-LOG\t$appname\tERR: ";
  } elsif ($type eq "WARN") {
	$data = "SYS-LOG\t$appname\tWARN: ";
  } elsif ($type eq "DEBUG") {
	$data = "SYS-DEBUG\t$appname\t50\t";
  } elsif ($type =~ m/^1?[1-9]?[0-9]$/) {
	$data = "SYS-DEBUG\t$appname\t$type\t";
  } else {
	die "Invalid TYPE to sioWrite: $type\n";
  };

  # clean up CMD - we do not remove tabs as it could be pre-joined
  $cmd =~ s/[^\t\x20-\xFF]/\#/g;
  # clean up args - we do remove all tabs there to prevent false aliasing
  {
	no warnings 'uninitialized';
	s/[^\x20-\xFF]/\#/g for @args;
	$data .= join("\t", $cmd, @args)."\n";
  };

  unless ($FH) {
 	warn "sioOpen not called: message lost: $data\n";
	return;
  };

  if ($ENV{'SIO_DEBUG'}) {
	print ">>> ".$data;
  };

  while (length($data)) {
	my $rv = syswrite($FH, $data);
	unless (defined($rv)) {
	  die "sioWrite: syswrite failed ($!)\n";
	};
	substr($data, 0, $rv) = '' if $rv;
  };
};


sub sioOnMessage {
  my ($mask, $proc) = @_;

  my $re = ( (ref($mask)||'') eq 'Regexp' ) 
	? $mask : qr/^\Q$mask\E(\z|\t)/;

  if ($handlers{$re}) {
	delete $handlers{$re};
	@regexps = grep { $_ ne $re } @regexps;
  };

  if (defined($proc)) {
	push(@regexps,  $re);
	$handlers{$re} = $proc;
  };
};

# rv: empty string = timeout
#     undef = extraFH selected
#     data = data recieved
sub sioRead {
  my ($timeout, $extraFH) = @_;
  # undef'ed/negative timeout = 3 years/infinity
  $timeout = 1e8 if ((!defined($timeout)) || ($timeout<0));

  my $etime = Time::HiRes::time() + $timeout;
  while ((!$timeout) || ($etime > Time::HiRes::time())) {

	while ($rbuff =~ s/^([^\r\n]*)\r?\n//) {
	  my $line = $1; # already chomped
	  # match loop
	  if (_sioLineRecvd($line)) {
		return $line;
	  };
	};

	my $rin = '';
	vec($rin, fileno($FH), 1)=1;
	vec($rin, fileno($extraFH), 1)=1 if $extraFH;

	my $tleft = $etime - Time::HiRes::time();
	my $nfnd = select($rin, undef, undef, ($tleft<0)?0:$tleft);
	die "sioRead: select() failed: $!\n" unless defined($nfnd);
	unless ($nfnd) {
	  last unless $timeout;
	  next;
	};
	if (vec($rin, fileno($FH), 1)) {
	  my $blk = '';
	  my $rv = sysread($FH, $blk, 1024);
	  die "sioRead: sysread() failed: $!\n" unless defined($rv);
	  die "sioRead: READ-DONE, server has closed the connection\n" unless $rv;
	  $rbuff .= $blk;
	};
	if ($extraFH && vec($rin, fileno($extraFH), 1)) {
	  return undef;
	};

  };
  # true timeout
  return '';
};

# RV: true = return to user; false = hide
sub _sioLineRecvd {
  my ($line) = @_;
  return 0 unless length($line); # skip long ones
  foreach my $re (@regexps) {
	if ($line =~ $re) {
	  &{$handlers{$re}}
		({ text => $line },
		split(/\t/, $line));
	  return 0;
	};
  };
  return 1; # pass to user - no match
};


sub sioClose {
  my ($excode, $comment) = @_;
  $excode ||= 0;
  $comment = '' unless defined($comment);
  eval { # don't care if sioWrite failed...
	  sioWrite('DATA', 'SYS-DONE', $appname, $excode, $comment);
  };
  $needclose = 0;
  $FH = undef;
  $rbuff = '';
};


sub sioConf {
	my ($valname) = @_;

	if (!$CONF) {
		loadConfig();
	} elsif ($confcheck != time()) { # check for stale files
		my @dx = ();
		foreach my $f (keys %CONF_FILES) {
			my $st = (stat($f))[10] || warn "[$$] Cannot stat $f: $!\n";
			my $st1 = $CONF_FILES{$f} || warn;
			push(@dx, $f." ($st/$st1)") if ($st != $st1 );
		};
		if (@dx) {
			warn "Config files changed: ".join(", ", @dx).". Reloading!\n";
			loadConfig();
		};
	};
	return (defined($valname) ? $$CONF{$valname} : $CONF);
};

sub loadConfig {
	my ($confname, $append) = @_;
	unless ($append) {
		$CONF = {};
		%CONF_FILES = ();
		$confcheck = time();
	};
	unless ($confname) {
		$confname = "$Bin/sodacom.conf";
		$confname = "$Bin/../conf/sodacom.conf" unless (-f $confname);	
	};
	if ($CONF_FILES{$confname}) {
		warn "[$$] WARNING: config file $confname was alredy scanned\n";
		return;
	};
	
	my $CFILE;
	open($CFILE, "< $confname")|| die "Cannot open config $confname: $!\n";
	while (defined(my $l=<$CFILE>)) {
		chomp $l;
		if ($l =~ m/^\#/ or $l =~ m/^\s*$/) {
			# comments
		} elsif ($l =~ m/^\s*([a-z0-9_-]+)\s*=\s*(.*?)\s*$/i) {
			$$CONF{$1} = $2;
		} elsif ($l =~ m/^([a-z0-9_-]+)\s*\[([^\]\[=]+)\]\s*=\s*(.*?)\s*$/i) {
			my ($n, $k, $v) = ($1, $2, $3);
			if ($k eq '+') {
				my $i = 0;
				while (1) {
					$i++; $k = sprintf("%.3d", $i);
					last unless exists($$CONF{$n}{$k});
				};
			};
			$$CONF{$n}{$k} = $v;
		} elsif ($l =~ m/^\s*include\s*(.*?)\s*$/i) {
			my $fname = $1;
			my $subc = ($fname =~ m|^/|) ? $fname :
				($confname =~ m|^(.*)/[^/]+$|) ? "$1/$fname" : 
				$fname;
			eval {
				loadConfig($subc, 1);
				1;
			} || do {
				warn "[$$] WARNING: $@"
			};
		} else {
			warn "[$$] WARNING: Unknown config line: $l\n";
		};
	};
	close($CFILE);
	$CONF_FILES{$confname} = 
		(stat($confname))[10] || die "Cannot stat $confname: $!\n"; # ctime
};


=pod

=head1 DESCRIPTION

ServIO  - intervace to soda machine controller

=head1 EXAMPLE

     sioOpen("+SERVIO-TESTER", "1.00");
     sioHookExit(); # hook warn, die, signals

     sioWrite('DATA', "SYS-ACCEPT", "MYAPP-");

     sioOnMessage("MYAPP-FOO", &foo_handler);
     sub foo_handler {
        my ($msginfo, $message, @args) = {};
	 };

     sioWrite('DATA', "MYAPP-RESET", "arg1", "arg2");
	 sioWrite('LOG', "this goes to syslog");
     sioWrite(50, "debug level 50");

	 while (1) {
	   $msg = sioRead(10); # 10 seconds timeout
	   next unless ($msg); # undef = timeout occurs
     };


=head2 sioOpen

     Argument: appname
         open in exclusive mode unless + is first character
     Argument: appversion


=head2 sioConf

	 Argument: option name
     Output: value if single, 
             hashref if multiple
             undef if not found

=cut
1;
