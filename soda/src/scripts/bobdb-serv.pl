#!/usr/bin/perl
#
# A server listening on the soda machine communications bus that can issue
# queries and updates to the main ChezBob database.  The intent is to provide
# an abstract interface for getting and updating user and product information
# which is independent of the underlying database representation and
# implementation.  A description of the protocol is provided in PROTO_DB.txt.
#
# The general implementation pattern of this server is to dispatch based on the
# incoming message type to a sequence of database accesses.  We currently
# assume a transactional database, and wrap all access up inside an "eval { }"
# block to catch any errors that occur; on error, we rollback the database
# updates.
#
# Author: Michael Vrable <mvrable@cs.ucsd.edu>

use warnings;
use strict;
use POSIX;
use FindBin qw[$Bin];
use lib "$Bin/../lib";
use ServIO;
use DBI;

# Set to true to enable debugging output.
my $DEBUG = 0;

my $dbh = DBI->connect("dbi:Pg:dbname=bob;host=chezbob.ucsd.edu", "bob", "",
                       { AutoCommit => 0, RaiseError => 1 })
    or die "Unable to connect to ChezBob database";

sioOpen("BOBDB-SERV", "2.00");
sioHookExit();

sioWrite('DATA', 'SYS-ACCEPT', '*');

# Convert a price from a decial to an integral number of cents (i.e., 2.50 to
# 250).
sub to_cents {
    my $in = shift;
    return POSIX::floor(100 * $in + 0.5);
}

# Send a response on the message bus, and also echo it to the screen for
# debugging.
sub sendResponse {
    print "  -> ", join(" | ", @_), "\n" if $DEBUG;
    sioWrite('DATA', @_);
}

# Look up the userid for a given username or user barcode.  Returns undef if
# the user does not exist in the database.
sub get_userid {
    my $username = shift;

    # Lookup first by username.  Usernames are considered case-insensitively.
    my $sth = $dbh->prepare(
        "SELECT userid FROM users
         WHERE lower(username) = lower(?)");
    $sth->execute($username);
    my @row = $sth->fetchrow_array;
    if (@row) {
        return $row[0] + 0;
    }

    # If no match, next try looking up by user barcode.
    $sth = $dbh->prepare("SELECT userid FROM userbarcodes WHERE barcode = ?");
    $sth->execute($username);
    my @row = $sth->fetchrow_array;
    if (@row) {
        return $row[0] + 0;
    }

    # Apparently, no matches in the database...
    return undef;
}

# Look up a user preference setting in the database.
# TODO: Update for schema change
sub get_userpref {
    my ($userid, $pref) = @_;

    my $sth = $dbh->prepare("SELECT setting FROM profiles
                             WHERE userid = ? AND property = ?");
    $sth->execute($userid, $pref);
    my @row = $sth->fetchrow_array;
    if (@row) {
        return $row[0] + 0;
    } else {
        return 0;               # Default value is 0
    }
}

# Look up product information given a barcode.  Returns a list containing
# (barcode, name, price, stock).  Since stock isn't currently tracked, we
# always return stock=0.
sub get_product {
    my $barcode = shift;

    my $sth = $dbh->prepare(
        "SELECT barcode, name, price, 0 as stock
         FROM products WHERE barcode = ?");
    $sth->execute($barcode);
    my @row = $sth->fetchrow_array;
    $row[2] = to_cents($row[2]) if @row;
    return @row;
}

# Get a user's transaction history: returns the most recent 5 transactions made
# by the user.
sub get_userhistory {
    my $userid = shift;
    my @transactions = ();

    my $sth = $dbh->prepare(
        "SELECT xacttime, xacttype, xactvalue FROM transactions
         WHERE userid = ? ORDER BY xacttime DESC LIMIT 5");
    $sth->execute($userid);

    my @row;
    while (@row = $sth->fetchrow_array) {
        my ($time, $desc, $value) = @row;
        $value = to_cents($value);
        unshift @transactions, "$time;$value;$desc";
    }

    return @transactions;
}

# Record a purchase: insert a transaction entry, update the user's balance, and
# update aggregate purchase statistics, as appropriate.
sub make_purchase {
    my ($userid, $price, $desc, $barcode) = @_;

    $price = $price / 100;
    $desc = uc($desc);

    my $privacy = get_userpref($userid, 'Privacy');
    if ($privacy) {
        $desc = "BUY";
    } else {
        $desc = "BUY $desc";
    }

    my $sth = $dbh->prepare(
        "INSERT INTO transactions
            (xacttime, userid, xactvalue, xacttype, barcode, source)
         VALUES (now(), ?, ?, ?, ?, 'soda')");
    $sth->execute($userid, -$price, $desc, $privacy ? undef : $barcode);

    $sth = $dbh->prepare(
        "UPDATE users SET balance = balance - ? WHERE userid = ?");
    $sth->execute($price, $userid);
}

while (1) {
    my $ln = sioRead();
    my ($cmd, @a) = split(/\t/, $ln);

    # Ignore commands not sent to us.  SYS-ACCEPT was not working for me
    # earlier...
    next if $cmd !~ /^BOBDB-/;

    print "$cmd: @a\n" if $DEBUG;

    # Ensure that we are starting a fresh transaction right before taking any
    # other action.  Otherwise, if we have a transaction that was started some
    # time ago (after the previous action finished), commands like NOW() will
    # return stale timestamps.
    eval { $dbh->rollback };

    # Queries for user information.
    if ($cmd eq 'BOBDB-QUERYUSER') {
        eval {
            my ($tag, $username) = @a;
            my $userid = get_userid($username);
            if (!defined $userid) {
                sendResponse('BOBDB-FAIL', $tag, "NO-USER");
                sioWrite('LOG', "query-user: $username does not exist");
            } else {
                my $sth = $dbh->prepare(
                    "SELECT username, balance, pwd, disabled
                     FROM users
                     WHERE userid = ?");
                $sth->execute($userid);
                my @row = $sth->fetchrow_array;
                if (@row) {
                    $username = $row[0];
                    my $balance = to_cents($row[1]);
                    my $password = $row[2] or "";
                    if ($row[3]) {
                        sendResponse('BOBDB-FAIL', $tag, "NO-USER");
                        sioWrite('LOG',
                                 "query-user: $username account is closed");
                    } else {
                        sendResponse('BOBDB-USERINFO', $tag,
                                     $username, $balance, $password);
                    }
                } else {
                    sendResponse('BOBDB-FAIL', $tag, "NO-USER");
                    sioWrite('LOG', "query-user: $username does not exist");
                }
            }
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    if ($cmd eq 'BOBDB-QUERYWALLOFSHAME') {
        eval {
            my $sth = $dbh->prepare("SELECT username, balance FROM users
                WHERE balance <= -5.00 ORDER BY balance");
            $sth->execute();

            my $array_ref = $sth->fetchall_arrayref();

            my @results;

            push @results, @$_ foreach @$array_ref;

            sendResponse('BOBDB-WALLOFSHAME', @results);
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    if ($cmd eq 'BOBDB-QUERYUSERPREF') {
        eval {
            my ($tag, $username, $pref) = @a;
            my $userid = get_userid($username);
            if (!defined $userid) {
                sendResponse('BOBDB-FAIL', $tag, 'NO-USER');
                sioWrite('LOG', "querypref: user $username not found");
            } else {
                my $pref_value = get_userpref($userid, $pref);
                sendResponse('BOBDB-USERPREF', $tag, $pref, $pref_value);
            }
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    if ($cmd eq 'BOBDB-QUERYTRANSACTIONLOG') {
        eval {
            my ($tag, $username) = @a;
            my $userid = get_userid($username);
            if (!defined $userid) {
                sendResponse('BOBDB-FAIL', $tag, 'NO-USER');
            } else {
                my @log = get_userhistory($userid);
                sendResponse('BOBDB-TRANSACTIONLOG', $tag, @log);
            }
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    # Queries for product information given a barcode.
    if ($cmd eq 'BOBDB-QUERYPRODUCT') {
        eval {
            my ($tag, $product) = @a;
            my @product_data = get_product($product);
            if (@product_data) {
                sendResponse('BOBDB-PRODUCTINFO', $tag, @product_data);
            } else {
                sendResponse('BOBDB-FAIL', $tag, 'NO-PRODUCT');
                sioWrite('LOG', "query-product: $product does not exist");
            }
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    # Log a purchase of an item by a user, give the product barcode.
    if ($cmd eq 'BOBDB-PURCHASE') {
        eval {
            my ($tag, $username, $barcode_in, $forced_price) = @a;
            my $userid = get_userid($username);
            my ($barcode, $name, $price, $stock) = get_product($barcode_in);
            if (defined $forced_price) {
                $price = $forced_price + 0;
            }
            if (!defined $userid) {
                sendResponse('BOBDB-FAIL', $tag, 'NO-USER');
                sioWrite('LOG', "purchase: user $username not found");
            } elsif (!defined $barcode) {
                sendResponse('BOBDB-FAIL', $tag, 'NO-PRODUCT');
                sioWrite('LOG', "purchase: product $barcode_in not found");
            } else {
                make_purchase($userid, $price, $name, $barcode);
                sendResponse('BOBDB-SUCCESS', $tag);
                if (get_userpref($userid, 'Privacy')) {
                    sioWrite('LOG', "purchase: $username: $price <hidden>");
                } else {
                    sioWrite('LOG', "purchase: $username: $price $barcode ($name)");
                }
            }
            $dbh->commit;
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    # Record the deposit of money by a user.
    if ($cmd eq 'BOBDB-DEPOSIT') {
        eval {
            my ($tag, $username, $amt) = @a;
            $amt += 0.0;
            my $userid = get_userid($username);
            if (defined $userid) {
                my $sth = $dbh->prepare(
                    "INSERT INTO transactions
                        (xacttime, userid, xactvalue, xacttype, source)
                     VALUES (now(), ?, ?, 'ADD', 'soda')");
                $sth->execute($userid, $amt/100.0);
                $sth = $dbh->prepare(
                    "UPDATE users SET balance = balance + ?
                     WHERE userid = ?");
                $sth->execute($amt/100.0, $userid);
                sendResponse('BOBDB-SUCCESS', $tag);
                sioWrite('LOG', "deposit: $username: $amt");
            } else {
                sendResponse('BOBDB-FAIL', $tag, "NO-USER");
                sioWrite('LOG', "deposit: user $username not found");
            }
            $dbh->commit;
        };
        if ($@) {
            sendResponse('BOBDB-FATAL');
            sioWrite('ERROR', $@);
            eval { $dbh->rollback };
            exit 1;
        }
    }

    # For testing purposes, to make a clean shutdown easy.
    if ($cmd eq 'BOBDB-QUIT') {
        last;
    }
};

$dbh->disconnect();
