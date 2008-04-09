#!/usr/bin/perl

use warnings;
use strict;
use IO::Socket::INET;
use Time::HiRes qw[time];
use Sys::Hostname;
use POSIX;
use Sys::Syslog;

use FindBin qw[$Bin];
use lib "$Bin/../lib";
use ServIO;

#
#
# global variables
#
#

# syslog facility - undef to disable syslog
my $logfacility = "LOG_LOCAL2";
# bitvector to select for read
our $rvector = '';
# bitvector to select for write
our $wvector = '';
# hash of fd->object that contain read/write handles
our %obj;
# object must be a blessed hashref that contains methods:
#     $this->selectedForRead();
#     $this->selectedForWrite();
#     $this->onMessage($sender_obj, $message_text, $time)
#     $this->destroy();

# hash of appid->object, maintained buy updatObjName
our %objname;

my $VERSION = "1.30";

# listen socket object
my $listsock; 

our $servname = hostname();
my $lastdate = '';
$|=1;
#
#
# main() and main loop
#
#
exit(0) if ($ARGV[0] && ($ARGV[0] eq '--test'));

sub main {
  openlog("contr[$$]", '', $logfacility) if $logfacility;
  eval {
	my $ctrlport = $ENV{'SODACTRL_PORT'} 
	  || die "Error! SODACTRL_PORT is not set!\n";
	$listsock = ListenSocket->new($ctrlport);
	runMainLoop();
	1;
  } || do {
	doLog(undef, "CONTROLLER failed: internal error $@");
  };
};


sub runMainLoop {

  while (1) {
	if (strftime('%F', localtime()) ne $lastdate) {
	  # update the date field
	  doLog(undef, "--- MARK ---");
	};
	my ($rout, $wout) = ($rvector, $wvector);
	my $timeout = 10;
	my $rv = select($rout, $wout, undef, $timeout);
	if ($rv < 0) {
	  die "Select() failed: $!\n";
	} elsif ($rv == 0) { # timeout
	  next;
	};
	foreach my $fno (keys %obj) {
	  my $o = $obj{$fno}; #cache obj in case of destuction
	  next unless $o;
	  $o->selectedForRead()  if (vec($rout, $fno, 1));
	  $o->selectedForWrite() if (vec($wout, $fno, 1));
	};
  };
};


sub doLog {
  my ($obj, $msg, @arg) = @_;
  $msg = join(" | ", $msg, @arg);
  $msg =~ s/([\x00-\x1F])/sprintf("\\x%.2X", ord($1))/ge;
  my $time = strftime('%H:%M:%S', localtime());
  my $date = strftime('%F', localtime());
  if ($date ne $lastdate) {
	$lastdate = $date;
	doLog(undef, "NEW DAY: $date");
  };
  my $objid = $obj ? "#$$obj{'fileno'}" : "##";
  my $objname = $obj ? $$obj{'appname'} : "contrl";
  my $objpid = $obj ? $$obj{'appPID'} : $$;
  my $idstr = $objname."[$objpid]$objid";

  # message for hidden app
  if ($$obj{'postlog'}) {
	$msg.=$$obj{'postlog'};
  };

  if ($logfacility) {
	my $lv = 'info';
	my $entry = $msg;
	if ($msg =~ m/^(DBG|MSG)/) {
	  $lv = 'debug';
	} elsif ($entry =~ m/^WARN: /) {
	  $lv = 'warning';
	} elsif ($entry =~ m/^ERR: /) {
	  $lv = 'err';
	};
	if (defined($Sys::Syslog::ident)) {
	  # undocumented feature to make nice syslog output
	  $Sys::Syslog::ident=$idstr;
	  syslog($lv, "%s", $entry) if $lv;
	} else {
	  syslog($lv, "%s %s", $idstr, $entry) if $lv;
	};
  };
  print STDERR "$time $idstr: $msg\n"
	unless ($ENV{'CTRL_NOSTDOUT'});
};

sub broadcastMessage {
  my ($sender, $time, $line) = @_;
  if ($line =~ m/^SYS-DEBUG\t([^\t]*)\t([^\t]*)\t(.*)$/) {
	my ($app, $level, $dbg) = ($1, $2, $3);
	$dbg =~ s/\t/ | /g;
	doLog($sender, "DBG[$level]: $dbg");
  } elsif ($line =~ m/^SYS-LOG\t([^\t]*)\t(.*)$/) {
	my ($app, $msg) = ($1, $2);
	$msg =~ s/\t/ | /g;
	if ($msg =~ s/^(WARN|ERR): //) {
	  my $ltype = $1;
	  doLog($sender, "$ltype: $msg");
	} else {
	  doLog($sender, "LOG: $msg");
	};
  } elsif ($line =~ m/^SYS-DONE/) {
	# do not log
  } elsif ($line =~ m/^SYS-(UN)?SET\tCONTROLLER\t_apps%\t/) {
	# do not log
  } else {
	my $l1 = $line;
	$l1 =~ s/\t/ | /g;
	doLog($sender, "MSG: $l1");
  };
  for my $cli (values %obj) {
	next if $cli eq ($sender||''); # do not send to itself
	eval {
	  $cli->onMessage($sender, $line, $time);
	  1;
	} || do {
	  my $err = $@;
	  chomp $err;
	  doLog($cli, "error with message [$line]: [$err]");
	};
  };
};
#
#
#       ListenSocket
#
#
sub ListenSocket::new {
  my ($class, $port) = @_;
  my $addr = "127.0.0.1";
  my $fd = IO::Socket::INET->new(
								 "LocalAddr" => $addr,
								 "LocalPort" => $port,
								 "Proto" => "tcp",
								 "Listen" => 10,
								 "ReuseAddr" => 1,
								 "Blocking" => 0)
	|| die "Cannot open listen socket on $port: $!\n";
  my $this = bless({ 
					type => 'listen',
					fd => $fd,
					port => $port,
					fileno => fileno($fd),
					addr => "$addr:$port",
					rbuffer => '',
					wbuffer=>'',
					pver => '0', pflags=>'',
					appname => 'CONTROLLER',
					appPID => $$,
					appver => $VERSION,
					appclient => "".getpwuid($<),
					vars => { '_apps%' => [] },
				   }, $class);
  vec($rvector, fileno($fd), 1) = 1; # always select for reading
  $obj{fileno($fd)} = $this;
  doLog($this, "Listening on $port");
  return $this;
};

sub ListenSocket::selectedForRead {
  my ($this) = @_;
  my $nfd = $this->{fd}->accept()
	|| die "accept failed: $!\n";
  binmode $nfd;
  $nfd->blocking(1);
  my $peerport = $nfd->peerport();
  my $haddr =  sprintf("%.2X%.2X%.2X%.2X:%.4X", reverse(split(/\./, $nfd->peerhost())), $peerport);
  my ($huid, $hinode) = ('', '');
  my $FH;
  if (open($FH, "< /proc/net/tcp")) {
	while (defined(my $x = <$FH>)) {
	  $x =~ s/^\s+//;
	  my ($sl, $local, $remote, $st, $queue, $tr, $retr, $uid, $timeout, $inode) = split(/ +/, $x);
	  if ($local eq $haddr) {
		$hinode = $inode;
		$huid = getpwuid($uid) || $uid || 'ROOT';
		last;
	  };
	};
  };
  if ((!$huid) && open($FH, "< /proc/net/tcp6")) {
	while (defined(my $x = <$FH>)) {
	  $x =~ s/^\s+//;
	  my ($sl, $local, $remote, $st, $queue, $tr, $retr, $uid, $timeout, $inode) = split(/ +/, $x);
	  if ($local =~ m/$haddr$/) {
		$hinode = $inode;
		$huid = getpwuid($uid) || $uid || 'ROOT';
		last;
	  };
	};
  };
  unless ($huid) {
	doLog($this, "WARN: no UID for faddr (port $peerport), going fuser way");
	sleep(6);
	my $rv = `sudo fuser -u -n tcp $peerport 2>&1`;
	chomp $rv;
	if ($rv =~ m/\d\((\S+)\)\s*$/) {
	  $huid = $1;
	} else {
	  doLog($this, "WARN: fuser gave JUNK: $rv");
	};
  };

  unless($huid) {
	doLog($this, "ERR: could not determine UID for $peerport: $haddr (see /tmp/net-tcp)");
	system("cat /proc/net/tcp /proc/net/tcp6 > /tmp/net-tcp");
	system("netstat -antp  >> /tmp/net-tcp");
        system("lsof -itcp -n >> /tmp/net-tcp");
  };
  TextSocket->new($nfd, $nfd->peerhost().":".$nfd->peerport(), $huid, $hinode);
};

sub ListenSocket::onMessage {
  # do nothing
};

sub ListenSocket::destroy {
  my ($this) = @_;
  vec($rvector, $$this{'fileno'}, 1) = 0; 
  delete $obj{$$this{'fileno'}};
  updateObjName();
};

sub ListenSocket::setVar {
  my ($this, $caller, $name, $key, @val) = @_;
  return if ($name =~ m/^(_apps%)$/);
  return TextSocket::setVar($this, $caller, $name, $key, @val);
};

sub ListenSocket::unsetVar {
  my ($this, $caller, $name, @keys) = @_;
  return if ($name =~ m/^(_apps%)$/);
  return TextSocket::unsetVar($this, $caller, $name, @keys);
};


sub ListenSocket::getVar {
  my ($this, $caller, $name, $key) = @_;
  if ($name eq '_apps%') {
	if ($key =~ m/^_(\d+)$/) {
	  my $targ = $obj{$1};
	  return $targ ? [ $$targ{'appname'}, $$targ{'type'}, $$targ{'addr'}, 0+(keys %{$$targ{'vars'}}) ] : [];
	} elsif ($key eq '') {
	  return [ map { "_$_" } sort {$a <=> $b} keys %obj ];
	} else {
	  return [];
	};
  };
  return TextSocket::getVar($this, $caller, $name, $key);
};

#
#
#       TextTcpSocket
#
#

sub TextSocket::new {
  my ($class, $fd, $addr, $uid, $inode) = @_;
  my $this = bless({ 
					type     => 'noinit',
					fd       => $fd,
					fileno   => fileno($fd),
					addr     => $addr,
					rbuffer  => '',
					wbuffer  => '',
					pver     => 0, # protocol version
					pflags   => '', # protocol flags
					appname  => '',
					appPID   => '',
					appver   => '',
					appclient=> '',
					errcode  => '-1',
					errmsg   => 'no SYS-DONE',
					accept_re => qr/^$/,
					vars    => { _init=>[], _accept=>[] },
					uid     => $uid,
					inode   => $inode,
				   }, $class);
  vec($rvector, fileno($fd), 1) = 1; # always select for reading
  $obj{fileno($fd)} = $this;
  #doLog($this, "connected from $addr");
  return $this;
};

sub TextSocket::selectedForRead {
  my ($this) = @_;
  my $rv = $this->{fd}->sysread($$this{'rbuffer'}, 4096, length($$this{'rbuffer'}));
  if ((!defined($rv)) || ($rv <= 0)) {
	$this->doClose($rv ? "read failed: $!" : "connection closed");
	return;
  };
  while ($$this{'rbuffer'} =~ s/^([^\n]*?)\r?\n//s) {
	my $line = $1;
	my $etime = time();
	eval {
	  $this->onLineRead($line);
	  1;
	} || do {
	  my $err = $@;
	  chomp $err;
	  doLog($this, "error while processing [$line]: [$err]");
	};
	$etime = time() - $etime;
	if ($etime > 1) {
	  doLog($this, "took $etime  to proces msg [$line]\n");
	};
  };
};

sub TextSocket::selectedForWrite {
  my ($this) = @_;

  return unless defined($$this{'fileno'});

  my $rv = $this->{fd}->syswrite($$this{'wbuffer'});
  if (!defined($rv) || ($rv < 0)) {
	$this->doClose($rv ? "write failed: $!" : "connection closed during write");
	return;
  } elsif ($rv == 0) {
	doLog($this, "write busy: $! (rv=$rv, bflen=".length($$this{'buffer'}).")");
  };
  substr($$this{'wbuffer'}, 0, $rv) = ''; # remove written stuff
  if ($$this{'wbuffer'} eq '') {
	vec($wvector, $$this{'fileno'}, 1) = 0; # done writing
  };
};

sub TextSocket::setVar {
  my ($this, $caller, $name, $key, @val) = @_;
  my $old = join("\t", @{$this->getVar($caller, $name, $key)});
  if ($name =~ m/^(_init||%)$/) {
	return 0;
  } elsif ($name =~ m/\%$/) {
	if (length($key)) {
	  $this->{'vars'}->{$name}->{$key} = [ @val ];
	} else {
	  return 0;
	};
  } else {
	if (defined($key) && length($key)) {
	  	doLog($caller, "WARN: attempt to give key to simple variable", $$this{'appname'}.".".$name, $key);
	  };
	$this->{'vars'}->{$name} = [ @val ];
  };
  if ($name eq '_accept') {
	my $are = join("|",   # TODO: add binary unescape here
				   map { s/ \| /\t/g; 
						 $_ = ($_ eq '*') ? '.' :
						   (m/^\^/) ? qr/$_/ : quotemeta($_) } @{[@val]}) || qr/^$/;
	$$this{'accept_re'} = qr/^($are)/;
	$are =~ s/\t/<tab>/g;
	doLog($this, "DBG[50]: Accept-mask changed", $are) unless ($$this{'postlog'} || $$this{'accept_nolog'});
  };
  if ($old ne join("\t", @val)) {
	#doLog($caller, "Property set: $$this{'appname'}.$name=".join(" | ",@val));
	broadcastMessage($caller, time(), join("\t", "SYS-SET", $$this{'appname'}, $name, $key, @val));
  };
  return 1;
};

sub TextSocket::unsetVar {
  my ($this, $caller, $name, @keys) = @_;
  if ($name =~ m/^(_init||%)$/) {
	return 0;
  } elsif (!@keys) {
	if ($this->{'vars'}->{$name}) {
	  delete $this->{'vars'}->{$name};
	  #doLog($caller, "Variable removed: $$this{'appname'}.$name");
	} else {
	  return 1;
	};
  } elsif ($name eq '_accept') {
	# accept cannot be unset, only set to empty value
	return $this->setVar($this, $caller, $name, '');
  } elsif ($name =~ m/\%$/) {
	my @ok_keys = ();
	foreach my $k (@keys) {
	  push(@ok_keys, $k) if $this->{'vars'}->{$name}->{$k};
	  delete $this->{'vars'}->{$name}->{$k};
	};
	return 1 unless (@ok_keys); # do not notify if nothing was removed
	@keys = @ok_keys;
	#doLog($caller, "Variable values removed: $$this{'appname'}.$name", @keys);
  } else {
	return 0; # cannot unset subitems from simple var
  };
  broadcastMessage($caller, time(), join("\t", "SYS-UNSET", "CONTROLLER", $$this{'appname'}, $name, @keys));
  return 1;
};


sub TextSocket::getVar {
  my ($this, $caller, $name, $key) = @_;
  if ($name eq '_init') {
	return [$$this{'pver'}.":".$$this{'pflags'}, $$this{'appname'}, $$this{'appver'}, $$this{'appPID'},
			  $$this{'appclient'}];
  } elsif ($name eq '') {
	return [ sort keys %{$this->{'vars'}} ];
  } elsif ($name =~ m/\%$/) {
	my $vk = $this->{'vars'}->{$name} || {};
	return length($key) ? ($vk->{$key}||[]) : [sort keys %$vk];
  } else {
	if (defined($key) && length($key)) {
	  	doLog($caller, "WARN: attempt to give key to simple variable on get", $$this{'appname'}.".".$name, $key);
		#use Data::Dumper; print Dumper($this->{'vars'});
	  };
	return $this->{'vars'}->{$name} || [];
  };
};


sub TextSocket::onLineRead {
  my ($this, $line, $ftype) = @_;
  #doLog($this, "got message: $line");
  #$this->doSend("got: $line!\n");
  $ftype ||= $$this{'type'};
  if ($line =~ m/^\s*$/) {
	doLog($this, "WARN: Empty line on input");
	return;
  } elsif ($ftype !~ m/^(noinit|client)$/) {
	doLog($this, "WARN: junk in bad state '$$this{'type'}': $line");
	return;
  } elsif ($ftype ne 'client') {
	if ($line =~ m/^SYS-INIT\t/) {
	  # connection setup line
	  my (undef, $pver_c, $appname, $appver, $appPID, $appcli) = split(/\t/, $line);
	  $appcli ||= '';

	  my %OLDVER = ( 100=>'0:a', 101 => '0:', 103=>'0:s', 106=>'0:u', 110=>'3:m' );
	  $pver_c = ($OLDVER{$pver_c} || $pver_c);
	  if (($pver_c !~ m/^(\d+):([a-z]+)$/) || (!$appPID) || (!$appver) || (!$appname)) {
		doLog($this, "Invalid SYS-INIT: [$line]");
		$$this{'type'} = 'bad';
		$this->doSend(join("\t", "SYS-NOTWELCOME", "bad-init", "Invalid welcome string"));
		return;
	  };
	  my $uid = $$this{'uid'};
	  $$this{'pver'} = $1;
	  $$this{'pflags'} = $2;
	  $$this{'appname'} = $appname;
	  $$this{'appver'} = $appver;
	  $$this{'appPID'} = $appPID;
	  $$this{'appclient'} = $appcli."[$uid]";
	  $$this{'accept_re'} = ( qr/./ );
	  if (($$this{'pflags'} =~ m/u/) && ($objname{$appname})) {
		my $oo = $objname{$appname};
		my $msg = "Second start attempt: v$$oo{'appver'} at pid $$oo{'appPID'} is already running";
		doLog($this, $msg);
		$this->doSend(join("\t", "SYS-NOTWELCOME", "not-unique", $msg, $$oo{'appPID'}));
		$$this{'type'} = 'bad';
		return;
	  };

	  if ((my $uok = sioConf("USER_OK"))) {
		if ((!$uid) || ($uok !~ m/:\Q$uid\E:/)) { 
		  my $oo = $objname{$appname};
		  my $msg = "User ".($uid||"(unknown)")." is not authorized to run '$appname' for '$appcli' pid $appPID";
		  doLog($this, "ERR: $msg");
		  $this->doSend(join("\t", "SYS-NOTWELCOME", "unauthorized", $msg));
		  $$this{'type'} = 'bad';
		  return;
		};
	  };

	  $$this{'type'} = 'client';
	  updateObjName();

	  my $nolog = ($$this{'pflags'} =~ m/s/);
	  if ($nolog) {
		my $pl = "v$$this{'appver'} ";
		$pl .= "for $$this{'appclient'}" if $$this{'appclient'};
		$pl =~ s/ $//;
		$$this{'postlog'} = " [$pl]";
	  } else {
		doLog($this, "Connected from ".$$this{'addr'}.", proto $$this{'pver'}:$$this{'pflags'}, ".
			  "appver ".$$this{'appver'}.", ".
			  "for ".$$this{'appclient'}
			 );
	  };

	  $this->doSend("SYS-WELCOME\t$servname");

	  my $iprop = sioConf("IPROP");
	  my $ctrl = $objname{'CONTROLLER'};
	  if (ref($iprop)) {
		foreach my $k (sort keys %$iprop) {
		  if ($k =~ m/^\Q$appname.\E(.*)$/) {
			my $pn = $1;
			my @v = split(/\s*\|\s*/, $$iprop{$k});
			$this->setVar($ctrl, $pn, '', @v);
		  };
		};
	  };

	  my $apps_key = "_".$$this{'fileno'};
	  broadcastMessage($ctrl, time(), join("\t", "SYS-SET", "CONTROLLER", "_apps%", 
										   $apps_key, @{$ctrl->getVar($this, "_apps%", $apps_key)}));

	  unless ($$this{'pflags'} =~ m/a/) {
		$$this{'accept_nolog'}=1;
		$this->setVar($this, "_accept", "");
		$$this{'accept_nolog'}=0;
	  };

	  return;
	} else {
	  doLog($this, "Junk on input: $line");
	  return;
	};
  };

  if ($line =~ m/^SYS-/) {
	my ($cmd, @a) = split(/\t/, $line);
	if ($cmd eq 'SYS-ACCEPT') {
	  my @accept = @a;
	  if (@accept && ($accept[0] eq '+')) {
		shift(@accept);
		unshift(@accept, @{$$this->{'vars'}->{'_accept'}});
	  };
	  $this->setVar($this, "_accept", "", @accept);
	  return;
	} elsif (($cmd eq 'SYS-DONE') && (@a >= 2)) {
	  $$this{'pver'} = 'done';
	  $$this{'errcode'} = $a[1]||0;
	  $$this{'errmsg'} = $a[2]||'';
	} elsif (($cmd eq 'SYS-LOG') || ($cmd eq 'SYS-DEBUG') || ($cmd eq 'SYS-INIT')) {
	  # do nothing, broadcast will take care
	} elsif ($cmd eq 'SYS-SET') {
	  my ($app, $name, $key, @val) = @a;
	  my $targ = ($app =~ m/^_(\d+)$/) ? $obj{$1} : $objname{$app};
	  unless ($targ) {
		doLog($this, "WARN: Cannot SYS-SET: target app not found", @a);
		return;
	  };
	  unless ($targ->setVar($this, $name, $key, @val)) {
		doLog($this, "WARN: SYS-SET failed", "$app.$name", $key, @val);
	  };
	  return;
	} elsif ($cmd eq 'SYS-UNSET') {
	  my ($app, $name, @keys) = @a;
	  my $targ = ($app =~ m/^_(\d+)$/) ? $obj{$1} : $objname{$app};
	  unless ($targ) {
		doLog($this, "WARN: Cannot SYS-UNSET: target app not found", @a);
		return;
	  };
	  unless ($targ->unsetVar($this, $name, @keys)) {
		doLog($this, "WARN: SYS-UNSET failed", "$app.$name", @keys);
	  };
	  #doLog($this, "Property cleared: $app.$name", @val);
	  return;
	} elsif ($cmd eq 'SYS-GET') {
	  my ($app, $name, @keys) = @a;
	  push(@keys, '') unless (@keys);
	  my @vals;
	  $name ||= '';
	  my $targ = ($app =~ m/^_(\d+)$/) ? $obj{$1} : $objname{$app};
	  unless ($targ) {
		doLog($this, "WARN: Cannot SYS-GET: target app not found", @a);
	  };
	  foreach my $k (@keys) {
		my $v = $targ ? $targ->getVar($this, $name, $k) : [];
		$this->doSend("SYS-VALUE", $app, $name, $k, @$v);
	  };
	  return;
	} elsif (($cmd eq 'SYS-ONCLOSE')) {
	  my ($id, @cmd) = @a;
	  if (@cmd) {
		$this->setVar($this, '_onclose%', $id, @cmd);
	  } else {
		$this->unsetVar($this, '_onclose%', $id);
	  };
	  return;
	} elsif (($cmd eq 'SYS-DO-PING') && (@a == 2)) {
	  my $target = undef;
	  my $tname = $a[1];
	  if ($tname eq 'CONTROLLER') {
		doLog($this, "Pinged controller ".$a[0]);
		$this->doSend("SYS-CPONG\t".$a[0]."\t#".$$this{'fileno'}."\t".$tname);
		return;
	  };

	  if ($tname =~ m/^\#(\d+)$/) {
		# client number
		$target = $obj{$1};
	  } else {
		# search for appname
		foreach my $fd (sort {$a<=>$b} keys %obj) {
		  next unless $obj{$fd}->{'type'} eq 'client';
		  if ($obj{$fd}->{'appname'} eq $tname) {
			$target = $obj{$fd};
			last;
		  };
		};
	  };
	  unless ($target) {
		doLog($this, "WARN: Cannot ping $tname - not found");
		return;
	  };
	  doLog($this, "Sent ping to $tname (#".$$target{'fileno'}.") ". $a[0]);
	  $target->doSend("SYS-CPING\t".$a[0]."\t#".$$this{'fileno'}."\t".$tname);
	  return;
	} elsif ($cmd eq 'SYS-CPONG') {
	  my $target = undef;
	  if ($a[1] =~ m/^\#(\d+)$/) {
		# client number
		$target = $obj{$1};
	  };
	  if ($target) {
		$target->doSend($line);
		doLog($this, "Ping response recieved", $a[0]);
	  } else {
		doLog($this, "Unknown PONG response: $line");
	  };
	} elsif ($cmd eq 'SYS-APP-LIST') {
	  my $cnt = 0;
	  # send ilines
	  foreach my $fd (sort {$a<=>$b} keys %obj) {
		my $o = $obj{$fd};
		#next unless $$o{'isclient'}; 
		#my @iline = split(/\t/, $$o{'init_line'});
		#shift(@iline);
		$this->doSend('SYS-APP-ENTRY', $$o{'fileno'}, $$o{'addr'}, 0+(keys %{$$o{'vars'}}), '', 
					  $$o{'pver'}.":".$$o{'pflags'}, $$o{'appname'}, $$o{'appver'}, $$o{'appPID'}, 
					  $$o{'appclient'});
		$cnt++;
	  };
	  $this->doSend("SYS-APP-ENTRY");
	  doLog($this, "Applist sent: $cnt entries");
	  return;
	} else {
	  doLog($this, "Unknown SYS-command: $line");
	};
  };
  broadcastMessage($this, time(), $line);
};

sub updateObjName {
  %objname = ( );
  foreach my $v (sort { $$a{'fileno'} <=> $$b{'fileno'} } values %obj) {
	if ($$v{'type'} =~ m/^(client|listen)$/) {
	  $objname{$$v{'appname'}} = $v;
	};
  };
};

sub TextSocket::onMessage {
  my ($this, $sender, $text, $time) = @_;
  return unless ($$this{'type'} eq 'client');
  return unless ($text =~ $$this{'accept_re'});
  if ($$this{'pver'} & 2) {
	$this->doSend( (int($time*1000)/1000.0)."\t".
				   "_".$$sender{"fileno"}."\t".
				   $text);
  } else {
	$this->doSend($text);
  };
};

sub TextSocket::destroy {
  my ($this) = @_;
  vec($rvector, $$this{'fileno'}, 1) = 0;
  vec($wvector, $$this{'fileno'}, 1) = 0;
  delete $obj{$$this{'fileno'}};
  broadcastMessage($objname{'CONTROLLER'}, 
				   time(), join("\t", "SYS-UNSET", 'CONTROLLER', "_apps%", "_".$$this{'fileno'}));
  $$this{'fileno'} = undef;
  updateObjName();
};

sub TextSocket::doClose {
  my ($this, $reason) = @_;
  unless ($$this{'postlog'} && ($$this{'errmsg'} eq '') && ($$this{'errcode'} eq '0')) {
	doLog $this, "closing: $reason | errMsg=$$this{'errmsg'} | errCode=$$this{'errcode'}";
  };
  my $onc = $this->{'vars'}->{'_onclose%'};
  $this->{fd}->close();
  $this->destroy();
  if ($onc) {
	#use Data::Dumper; print Dumper($this->{'vars'}); 
	foreach my $k (sort { $a <=> $b } keys %$onc) {
	  broadcastMessage($this, time(), join("\t", @{$$onc{$k}}));
	};
  };
};

sub TextSocket::doSend {
  my ($this, @data) = @_;
  no warnings 'uninitialized';
  $$this{'wbuffer'} .= join("\t", @data) . "\n";
  vec($wvector, $$this{'fileno'}, 1) = 1; # select for reading
};


# last - run main
# do it here so that all globals will be initialized
main(@ARGV);
