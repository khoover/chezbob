create table transactions
(
  xacttime datetime     not null               ,
  userid int            not null               ,
  xactvalue float       not null               ,
  xacttype varchar      not null	       
);

create view num_transactions as
  select userid, count(*) from transactions group by userid;
