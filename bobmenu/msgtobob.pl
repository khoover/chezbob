# msgtobob.pl
#
# Routine for recording a message for Bob in the db. 
#
# $Id: msgtobob.pl,v 1.6 2001-06-01 18:51:30 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

sub
message_win
{
  my ($username, $userid) = @_;
  my $win_title = "Leave a Message for Bob";
  my $win_text = q{
Leave a message for Bob!  We need your feedback about:

 - what you like and dislike about the Chez Bob service
 - what items are out of stock
 - suggestions for future offerings (specific products and a 
   reasonable price you would pay)
 - almost anything else you want to say!

What is your message?};

  if (&confirm_win("Message to Bob",
                   "\nDo you want to send your message anonymously?", 55)) {
    $username = "anonymous";
    undef $userid;
  }

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
             $win_text . "\" 18 74 2> $TMP/input.msg") == 0) {
    my $msg = "From $username: " . `cat $TMP/input.msg`;
    &bob_db_insert_msg($userid, $msg);
    &report_msg($userid, $msg);
  }
}

1;
