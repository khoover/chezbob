 -- Check the Chez Bob database for consistency in various ways.  Each of these
 -- queries should return an empty result set; if not, something has become
 -- mixed up and should be fixed.

select 'Account balances match transaction data' as check;
select userid, balance, xactbalance from balances_check
    where balance <> xactbalance;

select 'Anonymous account has zero balance' as check;
select username, balance from users natural join balances
    where username = 'anonymous' and balance <> 0.00;

select 'Closed accounts have zero balance' as check;
select userid, balance from balances natural join pwd
    where p like 'closed%' and balance <> 0.00;

select 'Double-entry accounting transactions balance' as check;
select transaction_id, sum(amount) from django.finance_splits
    group by transaction_id having sum(amount) <> 0.00;
