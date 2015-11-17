-- This script exists as a workaround, since bob2k14 doesn't properly update the
-- aggregate_purchases table. Until we update that node.js monstrosity, this
-- script can run daily and roll recent transactions into the table.
BEGIN;

INSERT INTO aggregate_purchases
    SELECT
        date(min(xacttime)),
        transactions.barcode AS barcode,
        sum(*) AS quantity,
        CAST (-1*sum(xactvalue) AS numeric(12,2)) AS price,
        min(bulkid) AS bulkid
    FROM transactions INNER JOIN products
    ON products.barcode = transactions.barcode
    WHERE
        transactions.barcode IS NOT NULL
        AND source = 'bob2k14.2'
        AND xacttime > current_date - interval '1 days'
        AND xacttime < current_date
    GROUP BY transactions.barcode;

COMMIT;
