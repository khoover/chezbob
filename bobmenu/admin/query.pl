#!/usr/bin/perl

sub parseARGV {
  @params = @_;
  $flags = "";
  while (@params != ()) {
    ($param, @params) = @params;
    if ($param eq "--") {
      $num = @params;
      return ($flags, @params);
    }
    if ($param !~ /^-.*$/) {
      return ($flags, $param, @params);
    }

    #
    # invalid flags with args
    #
    if ($param eq "-a" ||
        $param eq "-c" ||
        $param eq "-d" ||
        $param eq "-f" ||
        $param eq "-h" ||
        $param eq "-p" ||
        $param eq "-T") {
      print STDERR "warning: flag \"$param\" not supported\n";
      ($dummyarg, @params) = @params;
      print STDERR "         (discarding flag argument \"$dummyarg\")\n";
      next;
    }
    #
    # invalid flgas without args
    #
    if ($param eq "-l" ||
        $param eq "-s" ||
        $param eq "-S" ||
        $param eq "-u") {
      print STDERR "warning: flag \"$param\" not supported\n";
      next;
    }


    #
    # valid flags with args
    #
    if ($param eq "-F" ||
        $param eq "-o" ||
        $param eq "-T") {
      ($arg, @params) = @params;
      $flags .= " $param \"$arg\"";
      next;
    }
    #
    # valid flags without args
    #
    if ($param eq "-A" ||
        $param eq "-e" ||
        $param eq "-E" ||
        $param eq "-H" ||
        $param eq "-n" ||
        $param eq "-q" ||
        $param eq "-t" ||
        $param eq "-x") {
      $flags .= " $param";
      next;
    }

    #
    # unknown flag
    #
    print STDERR "unknown command-line parameter \"$param\", exiting.\n";
    exit 1;
  }
  return ($flags, @params);
}

$DB = "bob";

$Q{"negative_balance"} = $Q{"neg_bal"} =
  "select sum(balance)\n" .
  "  from balances\n" .
  " where balance < 0;";

$Q{"user_xacts"} = $Q{"user_transactions"} =
  "select username, count(*), balance\n" .
  "  from users, transactions, balances\n" .
  " where users.userid=transactions.userid\n" .
  "   and users.userid=balances.userid\n" .
  " group by username, balance\n" .
  " order by 2, 3;";

$Q{"users_overlimit"} =
  "select users.username, balances.balance, users.email\n" .
  "  from users, balances\n" .
  " where users.userid=balances.userid\n" .
  "   and balances.balance <= -5\n" .
  " order by balances.balance;";

$Q{"users_unused"} =
  "select users.username, balances.balance, users.email\n" .
  "  from users, balances, num_transactions\n" .
  " where users.userid=balances.userid\n" .
  "   and users.userid=num_transactions.userid\n" .
  "   and 1=num_transactions.count\n" .
  " order by 2, 1;";

$Q{"users"} =
  "select *\n" .
  "  from users\n" .
  " order by userid;";

$Q{"bal_comp"} =
  "select users.username, balances.balance,\n" .
  "       sum(transactions.xactvalue) as xact_sum\n" .
  "  from users, balances, transactions\n" .
  " where users.userid=balances.userid\n" .
  "   and users.userid=transactions.userid\n" .
  " group by users.username, balances.balance\n" .
  " order by balances.balance;";

$Q{"bal_comp_diff"} =
  "select users.username, balances.balance,\n" .
  "       sum(transactions.xactvalue) as xact_sum\n" .
  "  from users, balances, transactions\n" .
  " where users.userid=balances.userid\n" .
  "   and users.userid=transactions.userid\n" .
  " group by users.username, balances.balance\n" .
  "having sum(transactions.xactvalue)-balances.balance >= 0.00001\n" .
  " order by balances.balance;";

$Q{"transactions"} = $Q{"xacts"} =
  "select xacttime, username, xactvalue, xacttype\n" .
  "  from transactions, users\n" .
  " where users.userid = transactions.userid\n" .
  " order by xacttime, username;";

$Q{"total_balance"} = $Q{"total_bal"} =
  "select sum(balance) from balances;";

$Q{"total_negative_balance"} = $Q{"total_neg_bal"} =
  "select sum(balance) from balances where balance<0;";

$Q{"messages"} = $Q{"msgs"} =
  "select *\n" .
  "  from messages\n" .
  " order by msgid;";

($psqlFlags, @queries) = &parseARGV(@ARGV);

print "flags = [$psqlFlags]\n";
foreach (@queries) {
  print "query: \"$_\"\n";
}

foreach $query (@queries) {
  if ($query eq "list" || ! defined($Q{$query})) {
    print "list of available queries:\n";
    print "--------------------------\n";
    foreach $qname (sort(keys(%Q))) {
      print "  $qname\n";
    }
  }

  print `psql bob $psqlFlags -c '$Q{$query}\n'`;
}
