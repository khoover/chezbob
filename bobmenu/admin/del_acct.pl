#!/usr/bin/perl -w

# libs
use Pg;

# vars
$PROG = "del_acct.pl";
$DB = "bob";

#queries
$mainQuery = qq{
select users.userid, balance
  from users, balances
 where users.userid = balances.userid
   and users.username='%s';
};
$delUsersQuery = qq {
delete from users
 where userid=%s;
};
$delBalancesQuery = qq {
delete from balances
 where userid=%s;
};
$delTransactionsQuery = qq {
delete from transactions
 where userid=%s;
};


# db
$conn = Pg::connectdb("dbname=$DB");
if ($conn->status != PGRES_CONNECTION_OK) {
  print STDERR "$PROG: unable to make connection to database...exiting.\n";
  exit 1;
}

foreach $acct (@ARGV) {

  my $result = $conn->exec(sprintf($mainQuery, $acct));

  $num = $result->ntuples;
  if ($num == 0) {
    print STDERR "$acct: no such account...skipping.\n";
    next;
  }
  if ($num != 1) {
    print STDERR "$PROG: $num records found for account \"$acct\"\n";
    exit 2;
  }

  $userid = $result->getvalue(0,0);
  $bal = $result->getvalue(0,1);
  print STDERR "delete account $acct (userid=$userid)? ";
  chop($answer = <STDIN>);
  if ($answer eq "y" || $answer eq "yes") {
    push(@DEL, "$userid:$acct:$bal");
    $conn->exec(sprintf($delUsersQuery, $userid));
    $conn->exec(sprintf($delBalancesQuery, $userid));
    $conn->exec(sprintf($delTransactionsQuery, $userid));
  }
  else {
    print STDERR "NOT deleting account $acct\n";
  }
}

foreach $deleted (@DEL) {
  @cols = split(/:/, $deleted);
  foreach $col (@cols) {
    print "$col\t";
  }
  print "\n";
}
