create table users
(
  userid int            not null               ,
  username varchar      not null               ,
  email varchar         not null               ,
  userbarcode varchar	not null	       ,	

  primary key (userid),
  unique (username),
  constraint valid_email check (email ~~ '%@%')
);
