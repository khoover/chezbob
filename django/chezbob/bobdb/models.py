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

    def __str__(self):
        return self.description

    def total_price(self):
        """Total price of a product, including all applicable tax and CRV."""

        tax = crv_tax = 1.00
        if self.taxable: tax = 1 + TAX_RATE
        if self.crv_taxable: crv_tax = 1 + TAX_RATE

        amt = self.price * tax + self.crv * crv_tax

        return round(amt, 2)

    def unit_price(self):
        """Total price (including all taxes) for each individual item."""

        return round(self.total_price() / self.quantity, 4)

    class Admin:
        search_fields = ['description']
        fields = [
            ("Details", {'fields': ('description', 'quantity', 'updated')}),
            ("Pricing", {'fields': (('price', 'taxable'),
                                    ('crv', 'crv_taxable'))}),
        ]
        ordering = ['description']
        list_filter = ['updated']
        list_display = ['description', 'quantity', 'price', 'taxable',
                        'crv', 'crv_taxable', 'updated']

class Product(models.Model):
    class Meta:
        db_table = 'products'

    barcode = models.CharField(maxlength=32, primary_key=True, core=True)
    name = models.CharField(maxlength=256, core=True)
    phonetic_name = models.CharField(maxlength=256)
    price = models.FloatField(max_digits=12, decimal_places=2, core=True)
    stock = models.IntegerField()
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
