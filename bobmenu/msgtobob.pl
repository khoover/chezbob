# msgtobob.pl
#
# Routine for recording a message for Bob in the db. 
#
# $Id: msgtobob.pl,v 1.3 2001-05-22 01:23:05 chpham Exp $
#

require "bob_db.pl";
require "dlg.pl";

sub
message_win
{
  my ($username, $userid) = @_;
  my $win_title = "Leave a message for Bob";
  my $win_text = q{
Leave a message for Bob!  We need your feedback about:

 - what you like and dislike about the Chez Bob service
 - what items are out of stock
 - suggestions for future offerings (specific products
   and a reasonable price you would pay)
 - almost anything else you want to say!

What is your message?};

  if (&confirm_win("Message to Bob",
                   "\nDo you want to send your message anonymously?", 55)) {
    $username = "anonymous";
    undef $userid;
  }

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
             $win_text .
             "\" 18 74 \"From $username: \" 2> /tmp/input.msg") == 0) {
    my $msg = `cat /tmp/input.msg`;
    &bob_db_insert_msg($userid, $msg);
	&report_msg($userid, $msg);
  }
}

1;
