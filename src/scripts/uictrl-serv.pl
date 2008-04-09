#!/usr/bin/perl
use warnings;
use strict;
use FindBin qw[$Bin];
use lib "$Bin/../lib";
use Data::Dumper;
use List::Util qw[min max];
use X11::Protocol;

use ServIO;


#xFFNavigate("http://www.google.com/search?q=".rand()); exit;
#xSetFFSize(100); exit;

my $DEF_PREFIX= "http://localhost/lh/";
my $HOME_PAGE = "start";
my $XKBD_BIN = "xkbd"; #"/home/kiosk/xkbd/xkb-run";
my @XKBD_ARGS = qw[-k /home/kiosk/xkbd/en_US.noctrl.kbd ];
my $XKBD_HEIGHT = 250;
my $XKBD_OFFSET = 10;

my $NOKILL = {#"firefox-bin/Firefox-bin"=>1,
			  "fpserv/Fpserv" => 1,
			  "MozKioskBin/MozKioskBin" => 1};

# how to contorl firefox:
#    exec   - call firefox binary
#    direct - send commands directly to ff window
#    kiosk  - translate to MOZ- command for kiosk app
my $moz_type = "kiosk";

my $appid = "UICTRL-SERV";
sioOpen($appid, "1.24");
sioHookExit();

my $lock_queue = {};   # map: pri.time => appid
my $lock_holder = "";  # lock holder
my $lock_prio = 0;     # lock holder's priority
my $lock_seq = 0;      # seq number for conflict resolvance

sioWrite('DATA', 'SYS-ACCEPT', 'UI-');

my $xkb_pid = 0;

doReset();

while (1) {
  my $ln = sioRead();
  my ($cmd, @a) = split(/\t/, $ln);
  eval {
	if ($cmd eq 'UI-RESET') {
	  sioWrite('LOG', "UI reset request");
	  doReset();
	} elsif ($cmd eq 'UI-OPEN') {
	  xFFNavigate($a[0], $a[1]);
	} elsif ($cmd eq 'UI-RELOAD') {
	  xFFNavigate("___reload___", $a[0]);
	} elsif ($cmd eq 'UI-KEYBOARD-SHOW') {
	  if ($xkb_pid) {
		sioWrite('LOG', "Keyboard show request - ignored");
	  } else {
		my $y = $XKBD_HEIGHT + 1 + $XKBD_OFFSET;
		sioWrite('LOG', "Keyboard show request");
		xSetFFSize($y);
		$xkb_pid = fork();
		if ($xkb_pid == 0) {
		  my $yy = 600-$y;
		  exec($XKBD_BIN, "-geometry", "800x$XKBD_HEIGHT+0+$yy", @XKBD_ARGS);
		  die "$!\n";
		};
		# run refresher process
		if (fork() == 0) {
		  exec("sh", "-c", "sleep 1; xrefresh; sleep 5; xrefresh") || die;
		};
	  };
	} elsif ($cmd eq 'UI-KEYBOARD-HIDE') {
	  if ($xkb_pid) {
		kill(1, $xkb_pid);
		$xkb_pid = 0;
	  };
	  xSetFFSize(0);
	} elsif ($cmd eq 'UI-WIN-LIST') {
	  my $wlist = [];
	  eval { # need to write end of list no matter what
		$wlist = xGetWinList();
		1; } || do {
		  sioWrite('WARN', "Could not get window list", $@);
		};
	  foreach my $win (@$wlist) {
		sioWrite('DATA', 'UI-WIN-LIST-ENTRY', $$win{'id'}, $$win{'name'}.($$win{'mach'}?("@".$$win{'mach'}):""),
				 $$win{'inst'}."/".$$win{'class'}, $$win{'pid'}||'', $$win{'cmd'}||'');
	  };
	  sioWrite('DATA', 'UI-WIN-LIST-ENTRY');
	} elsif ($cmd eq 'UI-LOCK-REQUEST') {
	  my $pri = $a[1]||'0';
	  requestLock($a[0], $pri);
	  sioWrite('LOG', "Application $a[0] requests UI lock with priority $pri");
	} elsif ($cmd eq 'UI-LOCK-RELEASE') {
	  requestLock($a[0], undef);
	  requestLock($a[0], $a[1]) if (defined($a[1]));
	};
	1;
  } || do {
	my $err = $@; chomp $err;
	sioWrite('ERROR', "UI Command failed", $cmd, $err);
  };
};


sub doReset {
  xCleanDisplay();
  xSetFFSize(0);
  xFFNavigate();
  $lock_queue = {}; $lock_holder = ""; $lock_prio = "";
  $lock_seq = 1;
  requestLock($appid, undef);
  if ($xkb_pid) {
	kill(1, $xkb_pid);
	$xkb_pid = 0;
  };
  # UI-READY is sent by the PHP script when it loads
  #sioWrite('DATA', 'UI-READY');
};


sub requestLock {
  my ($rappid, $prio) = @_;
  # remove old values...
  foreach my $tkill (grep { $$lock_queue{$_} eq $rappid } keys %$lock_queue) {
	sioWrite('DEBUG', "Removing $rappid from queue - prio $tkill");
	sioWrite('DATA', 'SYS-UNSET', $appid, "lock_queue%", $tkill);
	delete $$lock_queue{$tkill};
  };
  # make priority unique..
  if (defined($prio)) {
	$lock_seq++;
	$prio = int($prio) + (($prio<0)?-1:0) + 1/$lock_seq; # earlier values have higher priorities
	$$lock_queue{$prio} = $rappid;
	sioWrite('DATA', 'SYS-SET', $appid, "lock_queue%", $prio, $rappid);
  };
  my $maxnext = max(keys %$lock_queue);
  my $old = $lock_holder || "(nobody)";
  # release the lock first, if needed
  if ($rappid eq $lock_holder) {
	$lock_holder = ""; $lock_prio = 0;
  };
  if (!$maxnext) {
	sioWrite('LOG', "Application $old has released its UI lock, and no one took it")
	  unless $lock_holder || ($old eq '(nobody)');
  } elsif (!$lock_holder) {
	# lock can be granted right away, perhaps transferred
	$lock_prio = $maxnext;
	$lock_holder = $$lock_queue{$maxnext};
	sioWrite('DATA', 'SYS-UNSET', $appid, "lock_queue%", $lock_prio);
	sioWrite('DATA', 'UI-LOCK-GRANTED', $lock_holder);
	sioWrite('LOG', "Application $lock_holder now has the UI lock (which used to belong to $old)");
  } elsif ($maxnext > $lock_prio) {
	# lock is being held. Request the transfer
	sioWrite('DATA', 'UI-LOCK-PAUSE', $lock_holder);
	sioWrite('LOG', "Application $lock_holder is asked to release UI lock (to give it to ".$$lock_queue{$maxnext}.")");
  }; # else: new app has lower priority than existing..

  # update the var
  sioWrite('DATA', 'SYS-SET', $appid, 'lock_holder', undef, $lock_holder, $lock_prio);
};

my $x11_cache;

# try to connect to server
# die if connection failed, return protocol handle otherwise
sub getX11 {
  # undef handle if server went away
  if ($x11_cache) {
	eval {
	  $x11_cache->QueryPointer($x11_cache->root());
	  1;
	} || do {
	  $x11_cache = undef;
	};
  };
  # connect if needed
  unless ($x11_cache) {
	my $x = X11::Protocol->new($ENV{'DISPLAY'} || ":0");
	$x || die "Cannot connect to X-server!\n";
	$x->QueryPointer($x->root());
	$x11_cache = $x;
  };
  return $x11_cache;
};


# kill all apps but firefox
sub xCleanDisplay {
  my $x = getX11();

  my (undef, undef, @kids) = $x->QueryTree($x->root());
  my @list;
  foreach my $win (@kids) {

	my ($wcmd) = $x->GetProperty($win, $x->atom('WM_COMMAND'), "STRING", 0, 1024, 0);
	next unless length($wcmd);
	$wcmd = join(" ", split(/\x00/, $wcmd));
	my ($classinst_r) = $x->GetProperty($win, $x->atom('WM_CLASS'), "STRING", 0, 1024, 0);
	my ($inst, $class) = split(/\x00/, $classinst_r);
	$class||='';
	$inst ||= '';
	my $classinst = "$inst/$class";

	if ($$NOKILL{$classinst}) {
	  # spare apps
	  next;
	};

	my (@rv) = $x->robust_req('KillClient',  $win);
	sioWrite("LOG", "xCleanDisplay - killing window", sprintf("0x%.X", $win), $classinst, $wcmd, 
			 ref($rv[0])?"ok":join("/", "ERR", @rv));
  };
  $xkb_pid = 0;
};

# internal - get FF win id
sub getFirefoxWin {
  my ($x) = @_;
  my (undef, undef, @kids) = $x->QueryTree($x->root());
  foreach my $win (@kids) {

	#if (!$x->GetProperty($win, $x->atom('WM_STATE'), "STRING", 0, 1024, 0);

	# TODO: if we had WM, we would have to do recursive scan...

	my ($mver) = $x->GetProperty($win, $x->atom('_MOZILLA_VERSION'), "STRING", 0, 1024, 0);
	if ($mver) {
	  return $win;
	};
  };
  return undef;
};

# return arrayref to window list
sub xGetWinList {
  my $x = getX11();
  my (undef, undef, @kids) = $x->QueryTree($x->root());
  my @list;
  foreach my $win (@kids) {
	  my ($mach) = $x->GetProperty($win, $x->atom('WM_CLIENT_MACHINE'), "STRING", 0, 1024, 0);
	  $mach ||= '';

	  my ($name) = $x->GetProperty($win, $x->atom('WM_NAME'), "STRING", 0, 1024, 0);
	  $name ||= '';

	  my ($wcmd) = $x->GetProperty($win, $x->atom('WM_COMMAND'), "STRING", 0, 1024, 0);
	  next unless length($wcmd);
	  $wcmd = join(" ", split(/\x00/, $wcmd));

	  my ($classinst) = $x->GetProperty($win, $x->atom('WM_CLASS'), "STRING", 0, 1024, 0);
	  my ($inst, $class) = split(/\x00/, $classinst);

	  my $wrec = { id   => sprintf("0x%.X", $win),
				  name => $name,
				  mach => $mach,
				  cmd  => $wcmd,
				  inst => $inst||'',
				  class=> $class||'' };
	  push(@list, $wrec);
  };
  return \@list;
};

# resize firefox window to free Y pixels at the bottom
sub xSetFFSize {
  my ($ymarg) = @_;
  my $x = getX11();
  my $w = $x->{'screens'}->[0]->{'width_in_pixels'} || die;
  my $h = $x->{'screens'}->[0]->{'height_in_pixels'} || die;
  sioWrite('DEBUG', "screen size: $w x $h");

  # we cannot use getFirefoxWin, as it returns only the icon, so we have to search for window
  # that occupies a certain point
  #my $win = getFirefoxWin($x) || die "No firefox window\n";
  my $maxwin;
  my $maxarea = 0;
  my (undef, undef, @kids) = $x->QueryTree($x->root());
  foreach my $win (@kids) {
	#my ($classinst) = $x->GetProperty($win, $x->atom('WM_CLASS'), "STRING", 0, 1024, 0);
	my ($name) = $x->GetProperty($win, $x->atom('WM_NAME'), "STRING", 0, 1024, 0);
	my $at = {$x->GetWindowAttributes($win)};
	next unless $$at{'map_state'} eq 'Viewable';
	#print Dumper($at); die;
	my $geom = {$x->GetGeometry($win)};
	my $area = $$geom{'width'} * $$geom{'height'};
	if ($area > $maxarea) {
	  $maxwin = $win;
	  $maxarea = $area;
	};
	sioWrite('DEBUG', 
			 sprintf('window %.X: %-40s %10s %8d %dx%d+%d+%d', $win, $name, 
					 $$at{'map_state'}, $area,
					 $$geom{'x'}, $$geom{'y'}, $$geom{'width'}, $$geom{'height'}
				   )
			);
  };
  die "No visible windows\n" unless $maxwin;
  my $new_h = ($h - $ymarg);
  $x->ConfigureWindow($maxwin, 'height'=> $new_h);
  my $geom = {$x->GetGeometry($maxwin)};
  sioWrite('DEBUG',
		   sprintf('resize window %.X to height %d (actual %d)', $maxwin, $new_h, $$geom{'height'}));
};


# open given URL in firefox, or home if no url given
# quick mozilla/ff navigation protocol:
# (1) find FF window which has _MOZILLA_VERSION atom set. this is main window.
# (2) set its property _MOZILLA_COMMAND to correct command
# (3) watch property _MOZILLA_RESPONSE
# (4) when it appears, read and delete - it will contain http-like status ne. 2xx is ok
#
sub xFFNavigate {
  my ($ourl, $frame) = @_;
  my $url = ($ourl || $HOME_PAGE);

  if ($url eq '___reload___') {
	if ($frame) {
	  my $f = qq["$frame"];
	  sioWrite('DATA', 'MOZ-JAVASCRIPT', "frames[$f].location=frames[$f].location");
	} else {
	  sioWrite('DATA', 'MOZ-JAVASCRIPT', "window.location=window.location");
	};
	return 0;
  };

  $url = $DEF_PREFIX.$url unless
	$url =~ m%^([~]|[/]|[a-z]+://)%;
  $url =~ s|^[~]/|file://$ENV{'HOME'}/|;
  $url =~ s/[\x00-\x20]//g;
  sioWrite('DEBUG', "Opening URL", $ourl||"{null}", $url, $frame);
  unless ($frame) {
	sioWrite('DATA', 'SYS-SET', $appid, "location", "", $ourl, $url);
  };

  if ($moz_type eq "kiosk") {
	if (length($frame||'')) {
	  sioWrite('DATA', "MOZ-OPEN-FRAME", $frame, $url);
	} else {
	  sioWrite('DATA', "MOZ-OPEN", $url);
	};
  } elsif ($moz_type eq "direct") {
	my $x = getX11();
	my $win = getFirefoxWin($x);
	die "Could not find ff window\n" unless ($win);

	#warn sprintf("win=0x%X\n", $win);

	# remove old results, if any
	my ($rv) = $x->GetProperty($win, $x->atom('_MOZILLA_RESPONSE'), "STRING", 0, 1024, 1);
	$x->sync();
	if ($rv) {
	  sioWrite('DEBUG', "Found old firefox result", $rv);
	};

	# set the command
	$x->ChangeProperty($win, $x->atom("_MOZILLA_COMMAND"), $x->atom("STRING"), 8, "Replace",
							"openURL($url)"); 
	$x->sync();

	# wait for response (busy-wait for now)
	for (1..100) {
	  # read and remove
	  ($rv) = $x->GetProperty($win, $x->atom('_MOZILLA_RESPONSE'), "STRING", 0, 1024, 1);
	  $x->sync();
	  last if $rv;
	  Time::HiRes::sleep(0.1);
	};

	if (!$rv) {
	  sioWrite('WARN', "Firefox timed out - op failed");
	} else {
	  sioWrite('DEBUG', "FF navigation complete", $rv);
	};

  } elsif ($moz_type eq "exec") {
	#sioWrite('DEBUG', "Cannot find firefox window - using slow method");
	if (fork()==0) {
	  exec("firefox", "-remote", "openURL($url)");
	  die "cannot exec: $!";
	};
	wait();
  } else {
	die "bad moz-type: $moz_type\n";
  };
};
