from django.db import models

class BulkItem(models.Model):
    class Meta:
        db_table = 'bulk_items'

    bulkid = models.AutoField(primary_key=True)
    description = models.TextField()
    price = models.FloatField(max_digits=12, decimal_places=2)
    taxable = models.BooleanField()
    quantity = models.IntegerField()
    updated = models.DateField()

    def __str__(self):
        return self.description

    class Admin:
        search_fields = ['description']
        fields = [
            ("Details", {'fields': ('description', 'quantity', 'updated')}),
            ("Pricing", {'fields': ('price', 'taxable')}),
        ]
        ordering = ['description']
        list_filter = ['updated']
        list_display = ['description', 'quantity', 'price', 'taxable',
                        'updated']

class Product(models.Model):
    class Meta:
        db_table = 'products'

    barcode = models.CharField(maxlength=32, primary_key=True, core=True)
    name = models.CharField(maxlength=256, core=True)
    phonetic_name = models.CharField(maxlength=256)
    price = models.FloatField(max_digits=12, decimal_places=2, core=True)
    stock = models.IntegerField()
    bulkid = models.ForeignKey(BulkItem, db_column='bulkid', blank=True,
                               edit_inline=models.TABULAR)

    def __str__(self):
        return "%s [%s]" % (self.name, self.barcode)

    class Admin:
        ordering = ['name']
        search_fields = ['barcode', 'name']
        list_display = ['barcode', 'name', 'price']
