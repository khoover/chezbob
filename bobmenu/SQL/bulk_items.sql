create table bulk_items
(
  bulk_barcode varchar not null,
  bulk_name varchar not null,
  item_barcode varchar not null,
  item_quantity int not null,

  unique(item_barcode)
);
