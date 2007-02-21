#!/usr/bin/perl -w
#
# Dump a list of all ChezBob transactions, for analysis purposes.
#
# Michael Vrable <mvrable@cs.ucsd.edu>, November 2005

use strict;
use DBI;

sub encode_string {
    my $in = shift;
    $in =~ s/([^\x20-\x7e]|["\\,])/sprintf("\\%03o", ord($1))/ge;
    return "\"$in\"";
}

# Obscure the user IDs in the database dump for privacy purposes.
my %users = ();
my $user_counter = 0;
sub encode_user {
    my $id = shift;
    $users{$id} = $user_counter++ if !exists($users{$id});
    return $users{$id};
}

my $dbh = DBI->connect("dbi:Pg:dbname=bob", "bob")
    or die "Unable to connect to ChezBob database";

my $sth = $dbh->prepare(
    "SELECT xacttime, xactvalue, xacttype, userid FROM transactions
     ORDER BY xacttime"
);
$sth->execute();

my @row;
while ((@row = $sth->fetchrow_array)) {
    $row[0] = encode_string($row[0]);
    $row[2] = encode_string($row[2]);
    $row[3] = encode_user($row[3]);
    print join(", ", @row), "\n";
}

$dbh->disconnect();
