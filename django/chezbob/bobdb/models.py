import datetime
from django.db import models

# Current tax rate.  This is only used to compute current item prices.  For any
# historical analysis, the per-order tax rate stored with each order is used
# instead.
TAX_RATE = 0.0875

class ProductSource(models.Model):
    class Meta:
        db_table = 'product_source'

    id = models.AutoField(db_column='sourceid', primary_key=True)
    description = models.CharField(db_column='source_description',
                                   max_length=255)

    def __unicode__(self):
        return self.description

class FloorLocations(models.Model):
    class Meta:
        db_table = 'floor_locations'

    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(db_column='name', max_length=255)

    def __unicode__(self):
        return self.name

class BulkItem(models.Model):
    class Meta:
        db_table = 'bulk_items'

    bulkid = models.AutoField(primary_key=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    taxable = models.BooleanField()
    crv = models.DecimalField(max_digits=12, decimal_places=2)
    crv_taxable = models.BooleanField()
    quantity = models.IntegerField()
    updated = models.DateField()
    source = models.ForeignKey(ProductSource, db_column='source')
    reserve = models.IntegerField()
    active = models.BooleanField(default=True)
    floor_location = models.ForeignKey(FloorLocations,
                                       db_column='floor_location')

    def __unicode__(self):
        return self.description

    def cost_taxable(self):
        """Portion of total price which is taxed."""
        amt = 0.0
        if self.taxable: amt += self.price
        if self.crv_taxable: amt += self.crv
        return amt

    def cost_nontaxable(self):
        """Portion of total price which is not taxed."""
        amt = 0.0
        if not self.taxable: amt += self.price
        if not self.crv_taxable: amt += self.crv
        return amt

    def total_price(self):
        """Total price of a product, including all applicable tax and CRV."""
        amt = (1 + TAX_RATE) * self.cost_taxable() + self.cost_nontaxable()
        return round(amt, 2)

    def unit_price(self):
        """Total price (including all taxes) for each individual item."""

        return round(self.total_price() / self.quantity, 4)

class Product(models.Model):
    class Meta:
        db_table = 'products'

    barcode = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=256)
    phonetic_name = models.CharField(max_length=256)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    bulk = models.ForeignKey(BulkItem, db_column='bulkid', blank=True)

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.barcode)

    def get_absolute_url(self):
        return "/products/%s/" % (self.barcode)

    def sales_stats(self):
        """Return a list with historical sales per day."""

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""SELECT date, sum(quantity) FROM aggregate_purchases
                          WHERE barcode = %s GROUP BY date ORDER BY date""",
                       [self.barcode])
        return cursor.fetchall()

class Order(models.Model):
    class Meta:
        db_table = 'orders'
        permissions = [("edit_orders", "Enter Order Information")]

    date = models.DateField()
    description = models.CharField(max_length=256)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4)

    def __unicode__(self):
        return "%s %s" % (self.date, self.description)

class OrderItem(models.Model):
    class Meta:
        db_table = 'order_items'

    # What order is this line item part of?
    order = models.ForeignKey(Order)

    # What was ordered?  This refers to BulkItem rather than Product since a
    # single unit ordered might contain multiple items with different UPC
    # barcodes.
    bulk_type = models.ForeignKey(BulkItem)

    # Number of individual items that come in each unit ordered.  Should match
    # bulk_type.quantity except in unusual cases.
    quantity = models.IntegerField()

    # Number of units ordered.  The total number of individual items received
    # will be number*quantity.
    number = models.IntegerField()

    # Cost for each unit ordered.  To get the total cost, multiply by number.
    # The cost is split into taxable and non-taxable components; we do this
    # instead of using a "taxable" boolean since both could be present (for
    # example, item is not taxable but the CRV on the item is).  In most cases,
    # one of the costs will be zero.
    cost_taxable = models.DecimalField(max_digits=12, decimal_places=2)
    cost_nontaxable = models.DecimalField(max_digits=12, decimal_places=2)

    def __unicode__(self):
        return "%d %s" % (self.number, self.bulk_type)

# This class doesn't actually connect directly with the underlying database
# table, but the class methods provided do perform useful queries.
class Inventory(models.Model):
    class Meta:
        db_table = 'inventory'

    inventoryid = models.AutoField(primary_key=True)
    inventory_time = models.DateField()

    def __unicode__(self):
        return "#%d %s" % (self.inventoryid, self.inventory_time)

    @classmethod
    def all_inventories(cls):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT date FROM inventory2 ORDER BY date")
        return [r[0] for r in cursor.fetchall()]

    @classmethod
    def get_inventory(cls, date):
        """Returns counts for all items with inventory taken on the given day.

        The returned value is a dictionary mapping a bulkid to a tuple (count,
        cases, loose, case_size).  count is the number of the item at the time
        of inventory, and cases is the number of full cases, and loose is the
        number of loose units of the item.  case_size is the number of units in
        a case (at the time the inventory was taken).
        """

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""SELECT bulkid, units, cases, loose_units, case_size
                          FROM inventory2
                          WHERE date = '%s'""", [date])

        inventory = {}
        for (bulkid, units, cases, loose, case_size) in cursor.fetchall():
            inventory[bulkid] = (units, cases, loose, case_size)
        return inventory

    @classmethod
    def set_inventory(cls, date, bulkid, count, cases, loose, case_size):
        """Insert a record with an inventory estimate for a product.

        Create a record of the inventory count for the given product on the
        given day.  If a record already exists, it is overwritten.  If count is
        None, then any existing inventory count for the given day is deleted.
        """

        from django.db import connection, transaction
        cursor = connection.cursor()

        cursor.execute("""DELETE FROM inventory2
                          WHERE date = '%s' AND bulkid = %s""",
                       (date, bulkid))

        if count is not None:
            cursor.execute("""INSERT INTO inventory2(date, bulkid, units, cases, loose_units, case_size)
                              VALUES ('%s', %s, %s, %s, %s, %s)""",
                           (date, bulkid, count, cases, loose, case_size))

        transaction.commit_unless_managed()

    @classmethod
    def get_inventory_summary(cls, date, include_latest=False):
        """Returns a summary of estimated inventory of all items on the given date.\

        The returned value is a dictionary mapping a bulkid to a second
        per-item dictionary with the following keys:
            estimate: estimate for the inventory
            date: date last inventory was taken for this item
            old_count: count at last inventory
            activity: has this product inventory changed
            sales: number of this item sold since last inventory
            purchases: number of this item received since last inventory
        """
        
        inventory_date = date

        #DOCME [nbales] Michael, can you please explain include_latest?
        if not include_latest:
            inventory_date -= datetime.timedelta(days=1)

        #Get most recent handcount and sales and purchase numbers since last handcount
        sql = """SELECT b.bulkid, i.date, i.units,
                    -- correlated subquery, sum total sale unit sales
                    (SELECT sum(a.quantity)
                     FROM aggregate_purchases a
                     WHERE a.bulkid = b.bulkid
                         AND (a.date > i.date OR i.date IS NULL)
                         AND (a.date <= '%s')) as sales,
                    -- correlated subquery, sum total sale unit purchases
                    (SELECT sum(oi.quantity * oi.number)
                     FROM orders o JOIN order_items oi ON o.id = oi.order_id
                     WHERE oi.bulk_type_id = b.bulkid
                         AND (o.date > i.date OR i.date IS NULL)
                         AND (o.date <= '%s')) as purchases
                 FROM bulk_items b
                    LEFT JOIN
                        -- get the most recent hand count or null for each item
                        (SELECT i.bulkid, i.date, i.units
                         FROM inventory2 d
                              JOIN inventory2 i ON d.bulkid = i.bulkid
                         WHERE d.date <= '%s'
                         GROUP BY i.bulkid, i.date, i.units
                         HAVING i.date = max(d.date))
                      AS i ON i.bulkid = b.bulkid;;"""

        from django.db import connection
        cursor = connection.cursor()

        cursor.execute(sql,[date,date,date])

        summary = {}
        for (bulkid, date, units, sales, purchases) in cursor.fetchall():

            if sales is None: sales = 0
            if purchases is None: purchases = 0
            if units is None: units = 0

            summary[bulkid] = {'estimate': units + purchases - sales,
                                 'date': date,
                                 'old_count': units, 
                                 'activity': sales > 0 or purchases > 0,
                                 'sales': sales,
                                 'purchases': purchases
                               }

        return summary

    @classmethod
    def get_sales(cls, date_from, date_to):
        """Returns total sales of each bulk item in the given date range."""

        from django.db import connection
        cursor = connection.cursor()

        cursor.execute("""SELECT bulkid, sum(aggregate_purchases.quantity)
                          FROM aggregate_purchases
                          WHERE date >= '%s' AND date <= '%s'
                                AND bulkid is not NULL
                          GROUP BY bulkid""", [date_from, date_to])
        return dict(cursor.fetchall())
