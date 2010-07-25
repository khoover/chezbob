 -- Check the Chez Bob database for consistency in various ways.  Each of these
 -- queries should return an empty result set; if not, something has become
 -- mixed up and should be fixed.

select 'Account balances match transaction data' as check;
select s.userid, balances.balance, s.xactbalance
    from (select transactions.userid,
                 sum(transactions.xactvalue)::numeric(12,2) AS xactbalance
          from transactions group by transactions.userid) s
    join balances using (userid)
    where balance <> xactbalance;

select 'Anonymous account has zero balance' as check;
select username, balance from users natural join balances
    where username = 'anonymous' and balance <> 0.00;

select 'Closed accounts have zero balance' as check;
select userid, balance from balances natural join pwd
    where p like 'closed%' and balance <> 0.00;

select 'Double-entry accounting transactions balance' as check;
select transaction_id, sum(amount) from finance_splits
    group by transaction_id having sum(amount) <> 0.00;

select 'Cashout totals are correct' as check;
select id, cashout_id, total, expected from
    (select 100*bill100 + 50*bill50 + 20*bill20 + 10*bill10 + 5*bill5 + bill1
            + coin100 + 0.50*coin50 + 0.25*coin25 + 0.10*coin10 + 0.05*coin5
            + 0.01*coin1 + other as expected, *
        from django.cashout_cashcount) s
    where expected <> total;

select 'Inventory records are self-consistent' as check;
select * from
    (select date, bulkid, units as units_listed,
                  round(coalesce(cases, 0) * case_size
                         + coalesce(loose_units, 0)) as units_expected
        from inventory2 where cases is not null or loose_units is not null) s
where units_listed <> units_expected;
