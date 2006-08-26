 -- Maintenance script for the Chez Bob database.  Should be run periodically
 -- to clean old records from the Chez Bob database and to update summary
 -- tables.
 --
 -- Written by Michael Vrable <mvrable@cs.ucsd.edu>

 -- Update the last_activity table in the database, which tracks the most
 -- recent time that we have seen any transaction for each user.  This isn't
 -- currently updated automatically, and so must periodically be updated by
 -- scanning the transaction log.
begin;
set transaction isolation level serializable;
create temp table last_activity_tmp (userid int, time timestamp with time zone)
    on commit drop;
insert into last_activity_tmp select userid, time from last_activity;
insert into last_activity_tmp
    select userid, max(xacttime) as time from transactions
        where xacttype <> 'INIT'
          and xacttype <> 'DONATION'
          and xacttype <> 'WRITEOFF'
        group by userid;

delete from last_activity;
insert into last_activity
    select userid, max(time) as time from last_activity_tmp group by userid;
commit;

 -- Search for any accounts where the reported balance does not match the
 -- transaction log.  This query should return zero rows.
select userid, balance, xactbalance from balances_check
    where balance <> xactbalance;

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
insert into transactions select (select * from date_cutoff) as xacttime,
    userid, balance as xactvalue, 'INIT' as xacttype
    from initial_balances;
commit;

 -- Verify no new inconsistencies were introduced.
select userid, balance, xactbalance from balances_check
    where balance <> xactbalance;
