import datetime
from django.db import models

TAX_RATE = 0.0775

class ProductSource(models.Model):
    class Meta:
        db_table = 'product_source'

    id = models.AutoField(db_column='sourceid', primary_key=True)
    description = models.CharField(db_column='source_description',
                                   maxlength=255)

    def __str__(self):
        return self.description

class BulkItem(models.Model):
    class Meta:
        db_table = 'bulk_items'

    bulkid = models.AutoField(primary_key=True)
    description = models.TextField()
    price = models.FloatField(max_digits=12, decimal_places=2)
    taxable = models.BooleanField()
    crv = models.FloatField(max_digits=12, decimal_places=2)
    crv_taxable = models.BooleanField()
    quantity = models.IntegerField()
    updated = models.DateField()
    source = models.ForeignKey(ProductSource, db_column='source')
    reserve = models.IntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
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

    class Admin:
        search_fields = ['description']
        fields = [
            ("Details", {'fields': ('description', 'quantity', 'updated',
                                    'source', 'reserve', 'active')}),
            ("Pricing", {'fields': (('price', 'taxable'),
                                    ('crv', 'crv_taxable'))}),
        ]
        ordering = ['description']
        list_filter = ['updated', 'active', 'source']
        list_display = ['description', 'quantity', 'price', 'taxable',
                        'crv', 'crv_taxable', 'updated', 'active', 'source']

class Product(models.Model):
    class Meta:
        db_table = 'products'

    barcode = models.CharField(maxlength=32, primary_key=True, core=True)
    name = models.CharField(maxlength=256, core=True)
    phonetic_name = models.CharField(maxlength=256)
    price = models.FloatField(max_digits=12, decimal_places=2, core=True)
    bulk = models.ForeignKey(BulkItem, db_column='bulkid', blank=True,
                             edit_inline=models.TABULAR)

    def __str__(self):
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

    class Admin:
        ordering = ['name']
        search_fields = ['barcode', 'name']
        list_display = ['barcode', 'name', 'price']

class Order(models.Model):
    class Meta:
        db_table = 'orders'
        permissions = [("edit_orders", "Enter Order Information")]

    date = models.DateField()
    description = models.CharField(maxlength=256)
    amount = models.FloatField(max_digits=12, decimal_places=2)

    def __str__(self):
        return "%s %s" % (self.date, self.description)

    class Admin:
        ordering = ['date', 'description']
        search_fields = ['date', 'description']
        list_display = ['date', 'amount', 'description']

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
    cost_taxable = models.FloatField(max_digits=12, decimal_places=2)
    cost_nontaxable = models.FloatField(max_digits=12, decimal_places=2)

    def __str__(self):
        return "%d %s" % (self.number, self.bulk_type)

    class Admin:
        list_display = ['bulk_type', 'number', 'order']

class Inventory(models.Model):
    class Meta:
        db_table = 'inventory'

    inventoryid = models.AutoField(primary_key=True)
    inventory_time = models.DateField()

    def __str__(self):
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
        exact).  count is the number of the item at the time of inventory, and
        exact is a boolean indicating whether this is an estimate or an exact
        value.
        """

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""SELECT bulkid, units, exact FROM inventory2
                          WHERE date = '%s'""", [date])

        inventory = {}
        for (bulkid, units, exact) in cursor.fetchall():
            inventory[bulkid] = (units, exact)
        return inventory

    @classmethod
    def set_inventory(cls, date, bulkid, count, exact=True):
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
            cursor.execute("""INSERT INTO inventory2(date, bulkid, units, exact)
                              VALUES ('%s', %s, %s, %s)""",
                           (date, bulkid, count, exact))

        transaction.commit_unless_managed()

    @classmethod
    def last_inventory(cls, date):
        """Find the most recent inventory on or before the given date.

        This will return, for each product, the date inventory for that product
        was last taken (on or before the specified date), and the count from
        that inventory.  The returned value is a dictionary mapping bulkids to
        (date, units, exact) tuples.
        """

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""SELECT bulkid, date, units, exact FROM
                          (SELECT bulkid, max(date) AS date FROM inventory2
                              WHERE date <= '%s' GROUP BY bulkid) as d
                          NATURAL JOIN inventory2""", [date])

        inventory = {}
        for (bulkid, date, units, exact) in cursor.fetchall():
            inventory[bulkid] = (date, units, exact)
        return inventory

    @classmethod
    def estimate_change(cls, bulkid, start_date=None, end_date=None):
        """Return the expected change in inventory for an item.

        This looks up, in the given date range, all sales (in the
        aggregate_purchases table) and bulk purchases (in the orders and
        order_items tables) of the given item.
        """

        from django.db import connection
        cursor = connection.cursor()

        # Construct an appropriate query for selecting only rows in the given
        # date range.  If a date is specified as None, then do not restrict
        # that endpoint.
        where_values = []
        if start_date is not None:
            where_query = "date >= '%s'"
            where_values.append(start_date)
        else:
            where_query = "true"

        if end_date is not None:
            where_query += " and date <= '%s'"
            where_values.append(end_date)

        # Look up sales in aggregate_purchases
        cursor.execute("""SELECT sum(quantity)
                          FROM aggregate_purchases JOIN products USING (barcode)
                          WHERE bulkid = %s AND """ + where_query,
                       [bulkid] + where_values)
        sales = cursor.fetchone()[0]
        if sales is None: sales = 0

        # Look up bulk purchases
        cursor.execute("""SELECT sum(quantity * number)
                          FROM orders JOIN order_items
                              ON orders.id = order_items.order_id
                          WHERE bulk_type_id = %s AND """ + where_query,
                       [bulkid] + where_values)
        purchases = cursor.fetchone()[0]
        if purchases is None: purchases = 0

        return (sales, purchases)

    @classmethod
    def get_inventory_estimate(cls, date):
        """Returns inventory estimates for all items on the given date.

        The returned value is a dictionary mapping a bulkid to a second
        per-item dictionary with the following keys:
            estimate: estimate for the inventory
            date: date last inventory was taken for this item
            old_count: count at last inventory
            exact: whether the last inventory was exact
            sales: number of this item sold since last inventory
            purchases: number of this item received since last inventory
        """

        counts = Inventory.get_inventory(date)
        previous = Inventory.last_inventory(date - datetime.timedelta(days=1))

        estimates = {}
        for i in BulkItem.objects.all():
            bulkid = i.bulkid
            d = {}

            if bulkid in previous:
                (d['date'], d['old_count'], d['exact']) = previous[bulkid]
                start_date = d['date'] + datetime.timedelta(days=1)
            else:
                d['old_count'] = 0
                start_date = None

            (sales, purchases) = Inventory.estimate_change(bulkid,
                                                           start_date, date)
            (d['sales'], d['purchases']) = (sales, purchases)
            d['estimate'] = d['old_count'] + purchases - sales
            estimates[bulkid] = d

        return estimates

    @classmethod
    def get_sales(cls, date_from, date_to):
        """Returns total sales of each bulk item in the given date range."""

        from django.db import connection
        cursor = connection.cursor()

        cursor.execute("""SELECT bulkid, sum(aggregate_purchases.quantity)
                          FROM aggregate_purchases JOIN products USING (barcode)
                          WHERE date >= '%s' AND date <= '%s'
                                AND bulkid is not NULL
                          GROUP BY bulkid""", [date_from, date_to])
        return dict(cursor.fetchall())

    class Admin:
        list_display = ['inventoryid', 'inventory_time']

#class InventoryItem(models.Model):
#    class Meta:
#        db_table = 'inventory_item'
#
#    inventoryid = models.ForeignKey(Inventory, db_column='inventoryid')
#    bulkid = models.ForeignKey(BulkItem, db_column='bulkid')
#    units = models.IntegerField()
#    exact = models.BooleanField()
