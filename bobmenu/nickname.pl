# nickname.pl
#
# Nicknames are used by the speech synthesis program when greeting the user. 
#
# $Id: nickname.pl,v 1.2 2001-05-19 22:37:54 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

sub
get_nickname_win
{
  my $win_title = "Enter nickname:";
  if (system("$DLG --title \"$win_title\" --clear " .
      " --inputbox \"\" 8 45 2> input.nickname") != 0) {
    return undef;
  }

  return `cat input.nickname`;
}


sub
update_nickname
{
  my ($userid) = @_;

  while (1) {
    my $name = &get_nickname_win;
    if (!defined $name) {
      # User canceled
      return;
    }
    if (&isa_valid_nickname($name)) {
      &bob_db_update_nickname($userid, $name);
      system ("$DLG --title \"Nickname\" --clear --msgbox"
              ." \"Nickname successfully updated!\" 6 50");
      return;
    } else {
      &invalid_nickname_win;
    }
  }
}


sub
isa_valid_nickname
#
# Nicknames contain only alphanumeric characters.  Things get really
# screwed up if the user enters an apostrophe; in postgres an apostrophe
# delimits a string
#
{
  my ($name) = @_;
  return ($name =~ /^\w+$/);
}


sub
invalid_nickname_win
{
  my $win_title = "Invalid Nickname";
  my $win_text = q{
Valid nicknames consist of alphanumeric characters and no spaces.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 8 50 2> /dev/null");
}

1;
