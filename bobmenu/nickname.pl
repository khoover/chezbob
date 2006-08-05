# nickname.pl
#
# Nicknames are used by the speech synthesis program when greeting the user. 

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

sub
get_nickname_win
{
  my $win_title = "Nickname";
  my $win_text = q{
Your nickname is used by the 'Speech' option when 
greeting you.  You may enable the Speech option by 
choosing 'My Chez Bob' from the main menu.}; 
  my ($err, $result) = &get_dialog_result("--title \"$win_title\" " .
      "--cr-wrap --clear --inputbox \"$win_text\" 11 55");

  return undef if ($err != 0);
  return $result;
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
      &get_dialog_result ("--title \"Nickname\" --clear --msgbox"
              ." \"Nickname successfully updated!\" 6 38");
      return;
    } else {
      &invalid_nickname_win;
    }
  }
}


sub
isa_valid_nickname
#
# Nicknames contain only letters and and few special characters.
#
{
  my ($name) = @_;
  return ($name =~ /^[A-Za-z,!?\. ]+$/);
}


sub
invalid_nickname_win
{
  my $win_title = "Invalid Nickname";
  my $win_text = q{
Valid nicknames consist of only letters and 
any of the characters from the set \{, ! ? . \}.};

  &get_dialog_result("--title \"$win_title\" --cr-wrap --msgbox \"" .
         $win_text .  "\" 8 54");
}

1;
