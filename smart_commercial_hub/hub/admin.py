from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from hub.models import *

class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_number','shop_type', 'rent_price','floor', 'is_rented', 'tenant', 'created_at')
    list_filter = ('is_rented', 'shop_type','floor')
    search_fields = ('name','shop_type')
    
class TenantAdmin(admin.ModelAdmin):
    list_display = ("tenant", "name", "rent_amount", "lease_start", "lease_end", "phone", "address")
    search_fields = ("name", "user__username")
    list_filter = ("lease_start", "lease_end")

class AllocatedShopAdmin(admin.ModelAdmin):
    def delete_model(self, request, obj):
        """Update shop status before deleting an allocated shop"""
        obj.shop_id.status = "vacant"
        obj.shop_id.save()
        super().delete_model(request, obj)

    def save_model(self, request, obj, form, change):
        """Update shop status and send an email when allocated via admin."""
        shop = obj.shop_id
        tenant = obj.tenant_id

        # Ensure the shop exists before updating
        if shop:
            shop.status = "occupied"  # ✅ Change status to occupied
            shop.save()

        # Send email only for new allocations
        if not change and tenant:
            tenant_email = tenant.tenant.email
            subject = "Shop Allocation Confirmation"
            message = (
                f"Dear {tenant.tenant.username},\n\n"
                f"You have been successfully allocated Shop {shop.shop_no} ({shop.name}).\n"
                f"Location: {shop.location}\n"
                f"Lease Start: {obj.lease_start}\n"
                f"Lease End: {obj.lease_end}\n"
                f"Rent Amount: ₹{obj.rent_amount}\n"
                f"Security Deposit: ₹{obj.security_deposit}\n\n"
                "Please contact the management for further details.\n\n"
                "Best Regards,\nSmart Commercial Hub Management"
            )

            send_mail(subject, message, settings.EMAIL_HOST_USER, [tenant_email], fail_silently=False)

        # Save the allocated shop
        super().save_model(request, obj, form, change)


admin.site.register(Shop)
admin.site.register(Tenant)
admin.site.register(AllocatedShop)
admin.site.register(Complaint)
admin.site.register(Manager)
admin.site.register(Announcement)