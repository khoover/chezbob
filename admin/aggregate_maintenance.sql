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
