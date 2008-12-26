#!/usr/bin/perl -w
#
# Script for sending out form e-mails to a number of users.  It has the
# following features:
#   - capable of text substitutions for customizing each e-mail
#   - can re-flow e-mail contents to handle varying-length substitutions

use strict;
use IPC::Open2;
use POSIX ":sys_wait_h";

$SIG{PIPE} = sub { die "SIGPIPE" };

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

    open MAIL, "|-", "sendmail", "--", @recipients;
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
    mail($msg, 'mvrable@localhost', $email);
}
