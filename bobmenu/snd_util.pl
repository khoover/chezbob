# snd_util.pl
#
# A small set of routines to encapsulate the speech synthesis software.  
# We're currently using the Festival Speech Synthesis System from the 
# University of Edinburgh.  Check out the following pages for information
# on obtaining and running festival:
#
# http://www.cstr.ed.ac.uk/projects/festival.html 
# http://www.speech.cs.cmu.edu/festival/
#
# We also use the SpeechIO package from http://www.speechio.org/ to create
# a nice /dev/speech device.  This sets up festival as a background process
# and allows us to simply pipe text to /dev/speech.  Works a lot faster than
# firing up festival each time we want to say something; also doesn't 
# introduce 'device not available' errors.
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
# Created: 5/10/01
#
# $Id: snd_util.pl,v 1.2 2001-05-13 21:55:08 mcopenha Exp $
#

sub
saytotal
{
  my ($total) = @_;

  my $str = sprintf("%.2f", $total);
  my @money = split(/\./, $str);
  my $dollars = int($money[0]);
  my $cents = $money[1];
  if (substr($cents, 0, 1) eq "0") {
    $cents = chop($cents);
  }

  if ($dollars > 0) {
    &sayit("your total is \\\$$dollars and $cents cents");
  } else {
    &sayit("your total is $cents cents");
  }
}


sub
sayit
{
  my ($str) = @_;
  system("echo $str > /dev/speech");
}

