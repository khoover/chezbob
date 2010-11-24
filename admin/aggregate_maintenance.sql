 -- Merge records in the aggregate_purchases table.  New purchases simply cause
 -- new rows to be inserted in the table.  However, for storage efficiency we
 -- will combine records with the same date and barcode.  We could also
 -- decrease the resolution of the records further back in time by rounding the
 -- dates on old records to the nearest month, but we don't yet do this.
 --
 -- This version only merges records created in the past two days, to bound the
 -- work performed.  If run at least once a day, it will ensure that all
 -- records merged.

 -- NOTE: We rely on the fact that under PostgreSQL, now() returns the same
 -- result for the duration of a transaction.
begin;
set transaction isolation level serializable;
create temp table aggregated(date date, barcode text, quantity integer,
                             price numeric(12,2), bulkid integer)
    on commit drop;
insert into aggregated
    select date, barcode, sum(quantity) as quantity, sum(price) as price, bulkid
        from aggregate_purchases
        where date > now() - interval '2 day'
        group by date, barcode, bulkid;
delete from aggregate_purchases where date > now() - interval '2 day';
insert into aggregate_purchases
    select * from aggregated where quantity <> 0 or price <> 0;
commit;

 -- Update the last_*_time columns of the users table, which track the most
 -- recent time that we have seen activity for each user.  This isn't currently
 -- updated automatically, and so must periodically be updated by scanning the
 -- transaction log.

begin;
set transaction isolation level serializable;
create temp table last_activity_tmp (userid int,
                                     last_purchase timestamp with time zone,
                                     last_deposit timestamp with time zone)
    on commit drop;
insert into last_activity_tmp
    select userid, last_purchase_time, last_deposit_time from users;

insert into last_activity_tmp
    select userid, max(xacttime) as last_purchase, null as last_deposit
        from transactions
        where xacttype like 'BUY%'
        group by userid;
insert into last_activity_tmp
    select userid, null as last_purchase, max(xacttime) as last_deposit
        from transactions
        where xacttype like 'ADD%'
        group by userid;

update users set last_deposit_time = s.last
    from (select userid, max(last_deposit) as last
          from last_activity_tmp group by userid) s
    where users.userid = s.userid;
update users set last_purchase_time = s.last
    from (select userid, max(last_purchase) as last
          from last_activity_tmp group by userid) s
    where users.userid = s.userid;

commit;

