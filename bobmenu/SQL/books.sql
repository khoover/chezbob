create table books
(
  barcode varchar   not null,
  isbn    varchar,
  author  varchar  not null,
  title   varchar   not null,

  primary key (barcode),
  unique (barcode)
);
