 -- Maintenance script for the Chez Bob database.  Should be run periodically
 -- to clean old records from the Chez Bob database and to update summary
 -- tables.
 --
 -- Written by Michael Vrable <mvrable@cs.ucsd.edu>

 -- Search for any accounts where the reported balance does not match the
 -- transaction log.  This query should return zero rows.
select userid, balance, xactbalance from balances_check
    where balance <> coalesce(xactbalance, 0.00);

 -- Delete old transactions from the transaction log, inserting appropriate
 -- initial balance transactions where needed.
begin;
set transaction isolation level serializable;
create temp table date_cutoff (time timestamp with time zone)
    on commit drop;
insert into date_cutoff
    select date_trunc('day', now() - interval '3 months') as time;
select * from date_cutoff;

create temp table initial_balances (userid int, balance numeric(12, 2))
    on commit drop;
insert into initial_balances select userid, sum(xactvalue) as balance
    from transactions where xacttime <= (select * from date_cutoff)
    group by userid;

delete from transactions where xacttime <= (select * from date_cutoff);
insert into transactions(xacttime, userid, xactvalue, xacttype)
    select (select * from date_cutoff) as xacttime,
        userid, balance as xactvalue, 'INIT' as xacttype
    from initial_balances
    where balance <> 0;
commit;

 -- Verify no new inconsistencies were introduced.
select userid, balance, xactbalance from balances_check
    where balance <> coalesce(xactbalance, 0.00);
