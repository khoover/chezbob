create table users
(
  userid int            not null               ,
  username varchar      not null               ,
  email varchar         not null               ,
  nickname varchar      ,
  userbarcode varchar	not null	       ,	

  primary key (userid),
  unique (username),
  unique (userbarcode),
  constraint valid_email check (email ~~ '%@%')
);
