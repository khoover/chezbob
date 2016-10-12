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
            print "  <td>";
            if (length $_) {
                print $_;
            }
            print "</td>\n";
        }
        print "</tr>\n";
        $i++;
    }
}

my $dbh = get_database_connection();

my $sth = $dbh->prepare(
    "SELECT username, nickname, balance FROM users
     WHERE
        balance <= -5.00
        AND NOT disabled
        AND last_purchase_time > now() - INTERVAL '2 years'
    ORDER BY balance"
);
$sth->execute();

print <<'END';
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>Chez Bob Wall of Shame</title>
<meta http-equiv="refresh" content="60">
<link href='https://fonts.googleapis.com/css?family=Open+Sans:400,700|Dancing+Script' rel='stylesheet' type='text/css'>
<link rel="stylesheet" href="css/common.css">
<style>
.red {
    color: #cc0000;
}

#shame_table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid black;
}

#shame_table th {
    text-align: left;
    background-color: #dddddd;
}

#shame_table tr {
    margin: 0px;
}

#shame_table td {
    border-top: 1px solid black;
    margin: 0px;
    padding: 3px;
}

#shame_table tr.even {
    background-color: #eeeeee;
}

</style>
</head>
<body>
<h1>Chez Bob</h1>

<div id="content-box">
<h2>Wall of <font class="red">Shame</font></h2>
<p>These are the poor souls who have "purchased" $5 or more from Chez Bob without
paying for it. Tsk, tsk... for shame.</p>

<table id='shame_table'>
<tr>
  <th>Username</th>
  <th>Name</th>
  <th width="150">Owes Bob (USD)</th>
</tr>
END

my @rows = ();
my @row;
my $owed = 0.0;
while ((@row = $sth->fetchrow_array)) {
    push @rows, [$row[0], $row[1], sprintf("%.02f", -$row[2])];
    $owed += -$row[2];
}
format_table_rows @rows;

$sth = $dbh->prepare(
    "SELECT -sum(balance) FROM users WHERE balance < 0 AND NOT disabled"
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
</div>
</body>
</html>
END

$dbh->disconnect();
