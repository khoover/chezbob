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
