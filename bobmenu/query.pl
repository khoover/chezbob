#!/usr/bin/perl

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
  "   and balances.balance < -8\n" .
  " order by balances.balance;";

$Q{"users_unused"} =
  "select users.username, balances.balance, users.email\n" .
  "  from users, balances, num_transactions\n" .
  " where users.userid=balances.userid\n" .
  "   and users.userid=num_transactions.userid\n" .
  "   and balances.balance < 0\n" .
  "   and 1=num_transactions.count\n" .
  " order by 2, 1;";

$Q{"users"} =
  "select *\n" .
  "  from users\n" .
  " order by userid;";

$Q{"bal_comp"} =
  "select users.username, balances.balance, sum(transactions.xactvalue)\n".
  "  from users, balances, transactions\n" .
  " where users.userid=balances.userid\n" .
  "   and users.userid=transactions.userid\n" .
  " group by users.username, balances.balance\n" .
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

foreach $query (@ARGV) {
  if ($query eq "list" || ! defined($Q{$query})) {
    print "list of available queries:\n";
    print "--------------------------\n";
    foreach $qname (sort(keys(%Q))) {
      print "  $qname\n";
    }
  }

  print `psql bob -c '$Q{$query}\n'`;
}
