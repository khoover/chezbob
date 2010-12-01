# msgtobob.pl
#
# Routine for recording a message for Bob in the db. 

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

sub
message_win
{
  my ($username, $userid) = @_;
  my $email = &bob_db_get_email_from_userid($userid);
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
                   "\nDo you want to send your message anonymously?",
                   55, 7, 1)) {
    $username = "anonymous";
    undef $userid;
    undef $email;
  }

  my ($dlgErr, $msgText) = &get_dialog_result("--title \"$win_title\" --clear ".
             "--cr-wrap --inputbox \"" .  $win_text . "\" 18 74");
  if ($dlgErr == 0)
  {
    my $msg = "Message from $username: $msgText";
    &bob_db_insert_msg($userid, $msg);
    if ($email) {
      &report_msg($userid, $msg, $email);
    } else {
      &report_msg($userid, $msg);
    }
  }
}

1;
