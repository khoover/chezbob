#!/usr/bin/perl -w
#
# Script for sending out form e-mails to a number of users.  It has the
# following features:
#   - capable of text substitutions for customizing each e-mail
#   - can re-flow e-mail contents to handle varying-length substitutions
#
# Two inputs are needed for sending out a set of mailings: a message template
# and a list of field substitutions (generally a database dump).  See the files
# in letters/*.txt for some sample templates.  The format is:
#   - Some number of leading comment lines of the form
#       # <Field>: <Value>
#     that define metadata about the template.  One of these must look like
#       # Fields: USERNAME EMAIL BALANCE
#     and specifies the variables in the message that will be substituted with
#     each mailing.
#   - Some number of e-mail headers.  It is good to define at least From and
#     Subject, but pretty much anything can be used.
#   - A blank line, followed by the e-mail body.  If any set of lines are
#     prefixed with "| ", those lines make up a paragraph which can reflowed if
#     needed (if any lines become overly long).  The "| " prefix will be
#     stripped out prior to sending the e-mail.
# In the e-mail headers or body, variables to substitute are surrounded by
# percent signs, such as %BALANCE% or %USERNAME%.
#
# To actually send a set of e-mails, create a file with one line per e-mail to
# send, whose contents gives the substitutions to make for each variable.  The
# variables should be given in the order specified in the Fields: metadata
# line.  Values should be separated by " | " (any amount of surrounding
# whitespace is fine); this format is meant to match the output of PostgreSQL
# when listing database results, so that data can be simply copied and pasted.
# As an example, the metadata might look something like:
#       user1   | user1@cs.ucsd.edu | -2.50
#       userfoo | foo@cs.ucsd.edu   | -3.14
# (where the fields in order are USERNAME, EMAIL, and BALANCE).
#
# As a convention, the templates have a "# Query:" line at the start which
# gives the database query used to get the list of users, but this is not used
# automatically for anything yet.
#
# Given a template file (say template.txt) and list of substitutions (say
# subst.data), send the e-mails by running
#       ./mail.pl template.txt <subst.data
# (That is, substitutions are read on STDIN and the template file is passed as
# the first command-line argument).  Mail is sent using the sendmail
# executable, so the local machine must be configured to deliver mail.
#
# Author: Michael Vrable <mvrable@cs.ucsd.edu>

use strict;
use IPC::Open2;
use POSIX ":sys_wait_h";

$SIG{PIPE} = sub { die "SIGPIPE" };

# E-mail addresses which should receive a copy (Bcc) of all e-mails sent.
my @EXTRA_ADDRESSES = ('mvrable@cs.ucsd.edu', 'kmowery@cs.ucsd.edu');

# Lines in the template that are prefixed with $REFLOW will be processed by fmt
# to rewrap lines, and then the $REFLOW prefix will be stripped off.  This
# allows for lines to be selected rewrapped or not.
my $REFLOW = "| ";

# Standard mail headers to include in e-mail messages that are sent, and the
# order of headers.
my %std_headers = (
    'From' => 'Chez Bob <chezbob@cs.ucsd.edu>',
    'MIME-Version' => "1.0",
    'Content-Type' => "text/plain; charset=us-ascii",
    'Content-Disposition' => "inline",
);
my @header_order = ('Date', 'From', 'To', 'Subject', 'Reply-To',
                    'MIME-Version', 'Content-Type', 'Content-Disposition');

# Clean up children which have become zombies.  Does not actually wait if
# children are still running; as such, if a child has not quite exited, but is
# about to, this won't clean it up.  On the other hand, if used in a loop it
# will prevent zombie children from building up too greatly.
sub reap_zombies {
    my $pid;
    do {
        $pid = waitpid(-1, WNOHANG);
    } while ($pid > 0);
}

# The main message formatting routine.  Given a message (string) and a series
# of replacements to make, return the message with substitution and formatting
# complete.
sub build_message {
    my ($msg, %replace) = @_;

    # First, make a pass through the message replacing all strings of the form
    # %KEY% with the value in $replace{KEY}.  Any token in the original message
    # that does not have a designated replacement text is replaced with
    # %!!KEY!!% to make it obvious that replacement text was left out.
    $msg =~ s/%([A-Z_]+)%/exists $replace{$1} ? $replace{$1} : "%!!$1!!%"/ge;

    # Re-flow the message.  All lines that begin with $REFLOW are reflowed;
    # other lines are left alone.  We fork to avoid deadlocks if we block when
    # performing I/O--a child process writes all data to the fmt subprocess,
    # and the main process then performs all the reading.
    my ($child_out, $child_in);
    open2($child_out, $child_in, "fmt", "--prefix=$REFLOW");
    my $pid = fork();
    die "fork(): $!" if !defined $pid;

    if ($pid == 0) {
        print $child_in $msg;
        exit 0;
    }

    close $child_in;
    $msg = join '', <$child_out>;
    close $child_out;

    reap_zombies();

    # Finally, strip out the reflow prefixes from lines.  These were only used
    # to mark which lines should have been reflowed.
    $msg =~ s/^\Q$REFLOW\E//gmo;

    return $msg;
}

# Extract e-mail headers from the sample message.  These will be merged in with
# other generated headers when sending the final message.
sub fixup_headers {
    my ($msg, %new_headers) = @_;

    # Generate the set of default headers for the outgoing message.  Some of
    # these may be overridden by headers from the message itself.
    my %headers = %std_headers;
    my $date = `date -R`;       # -R: RFC2822 format
    chomp $date;
    $headers{Date} = $date;

    # Strip off any header-like lines from the front of the provided message
    # and use them to replace any default headers we constructed.
    my @lines = split /\n/, $msg;
    while (@lines) {
        my $line = shift @lines;
        last if $line eq "";    # A blank line ends the headers
        if ($line =~ m/^(\S+): (.*)$/) {
            $headers{$1} = $2;
        } else {
            die "Found invalid line in header: $line";
        }
    }

    # Finally, header values provided as arguments take precedence over all
    # other values.
    %headers = (%headers, %new_headers);

    # Reconstruct the full message with all headers.  Headers we know about
    # will be output first, in a standard order, followed by all unknown
    # headers, alphabetically.
    $msg = "";
    foreach (@header_order) {
        $msg .= "$_: " . (exists $headers{$_} ? $headers{$_} : "") . "\n";
        delete $headers{$_};
    }
    foreach (sort keys %headers) {
        $msg .= "$_: " . (exists $headers{$_} ? $headers{$_} : "") . "\n";
    }
    $msg .= "\n";

    $msg .= join("\n", @lines) . "\n";  # Reconstruct message body
    return $msg;
}

sub mail {
    my ($msg, @recipients) = @_;

    open MAIL, "|-", "/usr/sbin/sendmail", "--", @recipients;
    print MAIL $msg;
    close MAIL;
}

open TEMPLATE, $ARGV[0] or die "Cannot open template $ARGV[0]: $!";
my $template = "";
my %meta = ();
while (($_ = <TEMPLATE>)) {
    if ($template eq "" && m/^# ([-\w]+): (.*)$/) {
        $meta{$1} = $2;
    } else {
        $template .= $_;
    }
}
close TEMPLATE;

my @fields = split /\s+/, $meta{Fields};

while (<STDIN>) {
    s/^\s+//;
    s/\s+$//;
    my %items = ();
    my @values = split /\s*\|\s*/, $_;
    foreach (@fields) {
        $items{$_} = shift @values;
    }

    foreach (sort keys %items) {
        print "$_: $items{$_}\n";
    }
    print "\n";

    my $email = $items{EMAIL};
    my $msg = build_message($template, %items);
    $msg = fixup_headers($msg, To => $email);
    mail($msg, $email, @EXTRA_ADDRESSES);
}
