#!/usr/bin/perl

use warnings;
use strict;
use X11::Protocol;
use Data::Dumper; $Data::Dumper::Useqq=1;  $Data::Dumper::Terse=1; $Data::Dumper::Sortkeys=1; $Data::Dumper::Indent=1;

my $x = X11::Protocol->new($ENV{'DISPLAY'} || ":0");

#print Dumper($x);
#print Dumper($x->GetInputFocus());
#print Dumper(  $x->ListExtensions());
#print Dumper(  $x->ListHosts());

#print Dumper($x->robust_req('KillClient',  0xa00001));

my $root = $x->root();
dumpTree($x, $root, '');
#print Dumper($g, $x->QueryTree($g));

#xls_lookat($x, $root);



sub xls_lookat {
  my ($x, $win) = @_;
  xls_printprops($x, $win);
  my ($root, $parent, @kids) = $x->QueryTree($win);

  foreach my $chwin (@kids) {
	my $cl = xmu_clientwin($x, $chwin);
	if ($cl) {
	  xls_printprops($x, $cl);
	};
  };
};


sub xls_printprops {
  my ($x, $win) = @_;

  my ($mach) = $x->GetProperty($win, $x->atom('WM_CLIENT_MACHINE'), "STRING", 0, 1024, 0);
  $mach ||= '';

  my ($wcmd) = $x->GetProperty($win, $x->atom('WM_COMMAND'), "STRING", 0, 1024, 0);
  return unless length($wcmd);

  printf "Window: 0x%.X\n", $win;
  print "  command: $wcmd\n";
  print "  machine: $mach\n" if $mach;
  #print "  Instance/Class: $inst/$class\n";
};

sub xmu_clientwin {
  my ($x, $win) = @_;
  return $win;
};

sub dumpTree {
  my ($x, $g, $pref) = @_;
  my ($root, $parent, @kids) = $x->QueryTree($g);
  $root =~ s/^None$/-1/g;
  $parent =~ s/^None$/-1/g;
  my ($wname) = $x->GetProperty($g, $x->atom('WM_NAME'), "AnyPropertyType", 0, 1024, 0);
  my ($wclass) = $x->GetProperty($g, $x->atom('WM_CLASS'), "AnyPropertyType", 0, 1024, 0);
  my ($wcmd) = $x->GetProperty($g, $x->atom('WM_COMMAND'), "STRING", 0, 1024, 0);
  #my ($wleader)  = $x->GetProperty($g, $x->atom('WM_CLIENT_LEADER'), "AnyPropertyType", 0, 1024, 0);
  my ($wstate, $hasstate)  = $x->GetProperty($g, $x->atom('WM_STATE'), "AnyPropertyType", 0, 1024, 0);
  # has state => main client window
  $wclass =~ s/\x00/:/g;
  $wcmd =~ s/\x00/ /g;
  #$wleader = (length($wleader))?unpack("L",$wleader):0;
  #if (($wleader) && ($wleader == $g)) {

  #if ($hasstate) {
	printf "$pref + 0x%.X (rt=%.X pa=%.X) wn[%s] wc[%s] cm[%s] wl[%s]\n",
	  $g, $root, $parent, $wname, $wclass, $wcmd, $hasstate?"+$wstate":'';
  #};

  do { dumpProperties($x, $g); die "\n" } if (($::t++>=200));

  foreach my $k (@kids) {
	dumpTree($x, $k, $pref." ");
  };
};

sub dumpProperties {
  my ($x, $g) = @_;
  foreach my $aid ($x->ListProperties($g)) {
	my $aname = $x->GetAtomName($aid);
	my ($value, $type, $format, $bytes_after) = $x->GetProperty($g, $aid, "AnyPropertyType", 0, 1024, 0);
	my @values = ($value);
	if ($format == 32) {
	  @values =  unpack("L*", $value);
	} elsif ($format == 16) {
	  @values = unpack("S*", $value);
	};
	if ($type == $x->atom('ATOM')) {
	  @values = map { eval{$x->atom_name($_)} || "#$_" } @values;
	} elsif ($type == $x->atom('STRING')) {
	  # nothing
	} else {
	  if ($format > 8) {
		@values = map {sprintf("0x%.8x",$_)} @values;
	  } else {
		@values = map {sprintf("%.2x",ord($_)&0xFF)} split(/./, join("", @values));
	  };
	};

	s/[^\x20-\x7F]/\#/g foreach @values;
	print "  $aname = ".join("/",@values)." [".($x->atom_name($type)||"#$type")."]\n";
  };
};

