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
# $Id: snd_util.pl,v 1.6 2001-05-16 01:45:43 mcopenha Exp $
#

require "ctime.pl";


sub
format_money
#
# Given a dollar amount in x.xx format, return a string representation
# that festival can parse correctly (Festival recognizes the '$' sign and 
# says 'dollars', but it's not smart enough to get the change correct).
#
{
  my ($amt) = @_;
  my $str = sprintf("%.2f", $amt);
  my @money = split(/\./, $str);
  my $dollars = int($money[0]);
  my $cents = $money[1];
  if (substr($cents, 0, 1) eq "0") {
    $cents = chop($cents);
  }

  if ($dollars > 0) {
    return "\\\$$dollars and $cents cents";
  } else {
    return "$cents cents";
  }
}


sub
say_greeting
#
# Say an appropriate greeting based on the time
#
{
  my $hour = substr(&ctime(time), 11, 2);
  my $greeting = "good ";
  if ($hour >= 17) {
    $greeting .= "evening";
  } elsif ($hour >= 12) {
    $greeting .= "after noon";
  } else {
    $greeting .= "morning";
  }
  sayit($greeting);
}


sub
say_goodbye
{
  @goodbyes = ( 
    "goodbye",
    "later, dude",
    "have a nice day",
    "now get to work, ok?", 
    "shay bob thanks you",
    "please feed me dollar bills, not pennies",
    "go do some research for crying out loud",
    "by the way, you look very nice today",
    "remember that pee equals n pee, ok?",
    "by the way, tell bill gris wald that he owes me big time",
    "by the way, tell bill gris wald that he owes me big time",
    "your new balance is minus one billion dollars.",
    "could you rub my back? please?",
    "by the way, you are stepping on my toes",
    "don't play with my scanner, ok?"
  );
  sayit(splice(@goodbyes, rand @goodbyes, 1));
}


sub
sayit
{
  my ($str) = @_;
  system("echo $str > /dev/speech");
}

1;
