# newuser.pl
#
# Routines for processing a new user: create db entry, ask for email 
# 
# $Id: newuser.pl,v 1.2 2001-05-21 21:20:08 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

sub
askStartNew_win
{
  my ($username) = @_;
  my $email = "";
  my $win_title = "New Chez Bob user?";
  my $win_textFormat = q{
I did not find you in our database.  Shall I open
up a new Chez Bob record under the name \"%s\"
for you?};

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --yesno \"" .
               sprintf($win_textFormat, $username) .
               "\" 9 50 2> /dev/null") != 0) {
      return $CANCEL;
    }

    $email = &askEmail_win($email);
    if (! defined $email) {
      $email = "";
      next;
    }
    if ($email !~ /^[^\s]+@[^\s]+$/) {
      &invalidEmail_win();
      next;
    }

    &bob_db_add_user($username, $email);
    return 0;
  }
}


sub
askEmail_win
{
  my ($currentvalue) = @_;
  my $win_title = "Email address";
  my $win_text = q{
What is your email address?  (UCSD or SDSC
email addresses preferred.)};

  system("$DLG --title \"$win_title\" --clear --inputbox \"" .
         $win_text .  "\" 11 51 \"$currentvalue\" 2> /tmp/input.email");
  my $retval = $? >> 8;
  if ($retval == 0) {
    return `cat /tmp/input.email`;
  } else {
    return undef;
  }
}


sub
invalidEmail_win
{
  my $win_title = "Invalid email address";
  my $win_text = q{
Valid email addresses take the form
<user>@<full.domain.name>};

  system("$DLG --title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 8 50 2> /dev/null");
}

1;
