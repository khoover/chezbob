create table messages
(
  msgid int             not null               ,
  msgtime datetime      not null               ,
  userid int                                   ,
  message varchar       not null               ,

  primary key (msgid)
);
