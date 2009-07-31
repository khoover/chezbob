from chezbob.bobdb.models import BulkItem, Product, Order
from django.contrib import admin

class ProductInline(admin.TabularInline):
    model = Product

class BulkItemAdmin(admin.ModelAdmin):
    search_fields = ['description']
    fieldsets = [
        ("Details", {'fields': ('description', 'quantity', 'updated',
                                'source', 'reserve', 'active',
                                'floor_location')}),
        ("Pricing", {'fields': (('price', 'taxable'),
                                ('crv', 'crv_taxable'))}),
    ]
    ordering = ['description']
    list_filter = ['updated', 'active', 'source', 'floor_location']
    list_display = ['description', 'quantity', 'price', 'taxable',
                    'crv', 'crv_taxable', 'updated', 'active', 'source',
                    'floor_location']
    inlines = [ProductInline]
admin.site.register(BulkItem, BulkItemAdmin)

class ProductAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['barcode', 'name']
    list_display = ['barcode', 'name', 'price']
admin.site.register(Product, ProductAdmin)

class OrderAdmin(admin.ModelAdmin):
    ordering = ['date', 'description']
    search_fields = ['date', 'description']
    list_display = ['date', 'amount', 'tax_rate', 'description']
admin.site.register(Order, OrderAdmin)
