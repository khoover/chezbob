from django.db import models

TAX_RATE = 0.0775

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
    active = models.BooleanField()

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
                                    'active')}),
            ("Pricing", {'fields': (('price', 'taxable'),
                                    ('crv', 'crv_taxable'))}),
        ]
        ordering = ['description']
        list_filter = ['updated', 'active']
        list_display = ['description', 'quantity', 'price', 'taxable',
                        'crv', 'crv_taxable', 'updated', 'active']

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
