#!/usr/bin/perl -w

# $Header: /home/mvrable/scratch/bobsource/CVS2/bob/bobmenu/admin/cleandb.pl,v 1.2 2001-06-15 15:04:16 bob Exp $

###
### libs
###
use Pg;

$conn = Pg::connectdb("dbname=bob");
if ($conn->status == PGRES_CONNECTION_BAD) {
  print STDERR "MAIN: error connecting to database...exiting.\n";
  exit 1;
}



$periodQ = q{
select 'now'::datetime-'3 months'::timespan;
};

$result = $conn->exec($periodQ);
if ($result->ntuples != 1) {
  print STDERR "MAIN: error finding period mark...exiting.\n";
  exit 1;
}
$mark = $result->getvalue(0,0);






$useridQ = q{
select userid
from users;
};

$result = $conn->exec($useridQ);
for ($i = 0 ; $i < $result->ntuples ; $i++) {
  $uid = $result->getvalue($i,0);

  my $beginResult = $conn->exec("begin");
  if ($beginResult->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "$uid: unable to begin transaction\n";
    next;
  }

  my $balanceQF = q{
select balance
from balances
where userid = %d;
  };

  my $result = $conn->exec(sprintf($balanceQF,$uid));
  if ($result->ntuples != 1) {
    print STDERR "$uid: no balance?\n";
    $conn->exec("rollback");
    next;
  }

  $bal = sprintf("%.2f",$result->getvalue(0,0));




  my $xactQF = q{
select sum(xactvalue)
from transactions
where userid = %d;
  };

  $result = $conn->exec(sprintf($xactQF,$uid));
  if ($result->ntuples != 1) {
    print "$uid: no transactions, skipping\n";
    $conn->exec("rollback");
    next;
  }

  $xact = sprintf("%.2f",$result->getvalue(0,0));


  #
  # sanity check!
  #
  if ($bal != $xact) {
    print STDERR "$uid: mismatch, bal=$bal xact=$xact\n";
    $conn->exec("rollback");
    next;
  }







  my $periodBalQF = q{
select sum(xactvalue)
from transactions
where userid = %d
and xacttime < '%s';
  };

  my $periodBalResult = $conn->exec(sprintf($periodBalQF,
					     $uid,$mark));
  if ($periodBalResult->ntuples != 1) {
    print STDERR "$uid: unable to get period balance\n";
    $conn->exec("rollback");
    next;
  }
  $periodBal = $periodBalResult->getvalue(0,0);



#  print "updating $uid ($bal)\n";
  ###
  ### make the update!
  ###
  my $delBalQF = q{
delete from balances
where userid = %d;
  };

  my $delBalResult = $conn->exec(sprintf($delBalQF,$uid));
  if ($delBalResult->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "$uid: unable to delete balance\n";
    $conn->exec("rollback");
    next;
  }

  my $delXactQF = q{
delete from transactions
where userid = %d
and xacttime < '%s';
  };

  my $delXactResult = $conn->exec(sprintf($delXactQF,$uid,$mark));
  if ($delXactResult->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "$uid: unable to delete transactions\n";
    $conn->exec("rollback");
    next;
  }




  my $insQF = q{
insert
into balances
values(
  %d,
  %.2f);
  };

  if ($periodBal ne "") {
    $insQF .= q{
insert
into transactions
values(
  '%s',
  %d,
  %.2f,
  'INIT');
    };
  }

  my $insResult = $conn->exec(sprintf($insQF,
				      $uid,$bal,
				      $mark,$uid,$periodBal));
  if ($insResult->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "$uid: unable to insert rows\n";
    $conn->exec("rollback");
    next;
  }


  my $endResult = $conn->exec("commit");
  if ($endResult->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "$uid: unable to end transaction\n";
    $conn->exec("rollback");
    next;
  }

  print "$uid: $bal\n";
}
