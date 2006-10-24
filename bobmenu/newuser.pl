# newuser.pl
#
# Routines for processing a new user: create db entry, ask for email 

require "$BOBPATH/bob_db.pl";
require "$BOBPATH/dlg.pl";

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
    my ($dlgErr, $button) = &get_dialog_result("--title \"$win_title\" --clear".
           " --yesno \"" .  sprintf($win_textFormat, $username) .
               "\" 9 50");
    return $CANCEL if ($dlgErr != 0);

    $email = &askEmail_win($email);
    if (! defined $email) {
      $email = "";
      next;
    }
    if ($email !~ /^[^\s]+@[^\s]+$/) {
      &invalidEmail_win;
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

  my ($dlgErr, $email) = &get_dialog_result("--title \"$win_title\" --clear " .
         "--inputbox \"" .  $win_text .  "\" 11 51 \"$currentvalue\"");
  if ($dlgErr == 0) {
    return $email;
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

  &get_dialog_result("--title \"$win_title\" --msgbox \"" .
         $win_text .  "\" 8 50");
}

sub
notify_new_user
{
  my $username = shift;
  my $userid = &bob_db_get_userid_from_username($username);
  return if $userid < 0;
  my $email = &bob_db_get_email_from_userid($userid);
  my $date = `date -R`; chomp $date;

  my $msg = <<"END";
Date: $date
From: Chez Bob <chezbob\@cs.ucsd.edu>
To: $email
Subject: Your New Chez Bob Account
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Disposition: inline

Thank you for creating an account with Chez Bob, the UCSD graduate
student food co-op.  We hope you'll find Chez Bob useful.  You can find
more information about Chez Bob at http://chezbob.ucsd.edu/.  Feel free
to send us questions, comments, and suggestions at chezbob\@cs.ucsd.edu.

If you did not create an account with Chez Bob, and believe that someone
else may have opened an account in your name, please let us know
immediately so that we may close the account.  Send a message to
chezbob\@cs.ucsd.edu (or simply reply to this message).  Please include
the following information with your message:
    Account name: $username
    E-mail address: $email

--Chez Bob
END

  open MAIL, "|-", "sendmail", "--", $email;
  print MAIL $msg;
  close MAIL;
}

1;
