-- Some useful queries on the Chez Bob database.

-- Determine how much was consumed in some time period, as a way to judge how
-- much to re-order.
select sum(a.quantity) as quantity, round(sum(a.quantity::numeric / b.quantity), 2) as units, description from aggregate_purchases a natural join products join bulk_items b using (bulkid) where date >= now() - interval '10 days' group by bulkid, description order by units;

-- Products which aren't listed in bulk_items.
select sum(a.quantity) as quantity, name from aggregate_purchases a natural join products p left join bulk_items b using (bulkid) where date >= now() - interval '10 days' and b.price is null group by barcode, p.name order by quantity;
