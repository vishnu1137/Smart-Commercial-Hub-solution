from django.contrib import admin
from hub.models import *

class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_number','shop_type', 'rent_price','floor', 'is_rented', 'tenant', 'created_at')
    list_filter = ('is_rented', 'shop_type','floor')
    search_fields = ('name','shop_type')
    
class TenantAdmin(admin.ModelAdmin):
    list_display = ("tenant", "name", "rent_amount", "lease_start", "lease_end", "phone", "address")
    search_fields = ("name", "user__username")
    list_filter = ("lease_start", "lease_end")

admin.site.register(Shop)
admin.site.register(Tenant)
admin.site.register(AllocatedShop)
admin.site.register(Complaint)
admin.site.register(Manager)
admin.site.register(Announcement)