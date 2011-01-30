#!/usr/bin/perl -w
#
# Generate a static HTML page containing the "Wall of Shame" (users who owe
# $5.00 or more).
#
# Michael Vrable <mvrable@cs.ucsd.edu>, April 2007

use strict;
use DBI;
use File::Basename;
use POSIX qw(strftime);

# Extract database connection parameters from the shared database settings
# configuration file.
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

sub format_table_rows {
    my @rows = @_;
    my $i = 1;

    foreach (@rows) {
        my @row = @$_;

        printf qq[<tr class="%s">\n], ($i % 2 ? "odd" : "even");
        foreach (@row) {
            print "  <td>", $_, "</td>\n";
        }
        print "</tr>\n";
        $i++;
    }
}

my $dbh = get_database_connection();

my $sth = $dbh->prepare(
    "SELECT username, balance FROM users
     WHERE balance <= -5.00 ORDER BY balance"
);
$sth->execute();

print <<'END';
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>Chez Bob Wall of Shame</title>
</head>
<body bgcolor="#ffffff">
<table border="0" cellspacing="0" width="100%" bgcolor="#CCCCFF"><tr>
<td align=center><br><b>Chez Bob Wall of <font color=#ff000>Shame</font></b><br>
These are the poor souls who have "purchased" $5 or more from Chez Bob without
paying for it. Tsk, tsk... for shame. 
<br><br></td>
</tr></table>
<br>

<table width="75%" border="1" cellspacing="0">
<tr>
  <th>User Name</th>
  <th>Owes Bob (USD)</th>
</tr>
END

my @rows = ();
my @row;
my $owed = 0.0;
while ((@row = $sth->fetchrow_array)) {
    push @rows, [$row[0], sprintf("%.02f", -$row[1])];
    $owed += -$row[1];
}
format_table_rows @rows;

$sth = $dbh->prepare(
    "SELECT -sum(balance) FROM users WHERE balance < 0"
);
$sth->execute();
@row = $sth->fetchrow_array;
my $total_owed = $row[0];
$sth->finish();

my $updated = strftime "%Y-%m-%d %H:%M:%S %z", localtime;

print <<END;
</table>
<p>Total owed to Chez Bob: \$@{[ sprintf("%.02f", $total_owed) ]}
(@{[ sprintf("%.01f", 100.0 * $owed / $total_owed) ]}\% by users above)</p>
<p>Last updated: $updated</p>
</body>
</html>
END

$dbh->disconnect();
