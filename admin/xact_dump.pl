#!/usr/bin/perl -w
#
# Dump a list of all ChezBob transactions, for analysis purposes.
#
# Michael Vrable <mvrable@cs.ucsd.edu>, November 2005

use strict;
use DBI;
use File::Basename;

# Extract database connection parameters from the shared database settings
# configuration file.  TODO: This code is duplicated in several places; we may
# consider creating a Chez Bob database module.
sub get_database_connection {
    # Expect db.conf in the parent of the directory where this script resides.
    my $db_config_path = dirname(`which $0`) . "/..";

    die "Can't find DB config file at $db_config_path/db.conf"
        unless -r "$db_config_path/db.conf";

    open CONF, "$db_config_path/db.conf"
        or die "Can't open DB config file: $!";

    my %params = ();
    my @required_params = qw(DATABASE_HOST DATABASE_NAME DATABASE_USER);
    while (($_ = <CONF>)) {
        next if m/^\s*(#.*)?$/;
        if (m/^(\w+)\s*=\s*\"(.*)\"$/) {
            $params{$1} = $2;
        } else {
            die "Bad line in database config file: $_";
        }
    }
    close CONF;

    foreach (@required_params) {
        die "Parameter $_ not in db.conf" if not exists $params{$_};
    }

    my $name = "dbi:Pg:dbname=$params{DATABASE_NAME};"
                . "host=$params{DATABASE_HOST}";
    my $dbh = DBI->connect($name, $params{DATABASE_USER})
        or die "Unable to connect to ChezBob database";

    return $dbh;
}
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

my $dbh = get_database_connection();

my $sth = $dbh->prepare(
    "SELECT xacttime, xactvalue, xacttype, source FROM transactions
     ORDER BY xacttime"
);
$sth->execute();

my @row;
while ((@row = $sth->fetchrow_array)) {
    $row[2] =~ s/^TRANSFER.*/TRANSFER/;
    $row[0] = encode_string($row[0]);
    $row[2] = encode_string($row[2]);
    pop @row unless $row[3];
    print join(", ", @row), "\n";
}

$dbh->disconnect();
