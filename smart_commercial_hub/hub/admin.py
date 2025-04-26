from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from hub.models import *
from django.utils.html import format_html
from hub.views import shop_occupancy_report, rental_income_report, lease_expiry_report, complaint_analysis_report, tenant_report, comprehensive_mall_report

class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_no', 'shop_type', 'location', 'status', 'created_at')
    list_filter = ('status', 'shop_type', 'location')
    search_fields = ('name', 'shop_no')

class TenantAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'phone', 'address', 'created_at')
    search_fields = ('tenant__username', 'phone', 'address')

class AllocatedShopAdmin(admin.ModelAdmin):
    list_display = ('shop_id', 'tenant_id', 'lease_start', 'lease_end', 'rent_amount', 'payment_status')
    list_filter = ('payment_status', 'status', 'lease_start', 'lease_end')
    search_fields = ('shop_id__name', 'tenant_id__tenant__username')
    
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
                
                from django.core.mail import send_mail
                from django.conf import settings
                send_mail(subject, message, settings.EMAIL_HOST_USER, [tenant_email], fail_silently=False)
        
        # Save the allocated shop
        super().save_model(request, obj, form, change)

class MallAdminSite(admin.AdminSite):
    site_header = "Mall Management Administration"
    site_title = "Mall Management Portal"
    index_title = "Welcome to Mall Management Portal"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/', self.admin_view(self.reports_dashboard), name='reports_dashboard'),
        ]
        return custom_urls + urls
    
    def reports_dashboard(self, request):
        context = {
            'title': 'Mall Reports Dashboard',
            'report_types': [
                {'name': 'Shop Occupancy Report', 'url': '/admin/reports/shop-occupancy/', 'icon': 'fas fa-store'},
                {'name': 'Rental Income Report', 'url': '/admin/reports/rental-income/', 'icon': 'fas fa-dollar-sign'},
                {'name': 'Lease Expiry Report', 'url': '/admin/reports/lease-expiry/', 'icon': 'fas fa-calendar-times'},
                {'name': 'Complaint Analysis Report', 'url': '/admin/reports/complaint-analysis/', 'icon': 'fas fa-exclamation-circle'},
                {'name': 'Tenant Report', 'url': '/admin/reports/tenant-report/', 'icon': 'fas fa-users'},
                {'name': 'Comprehensive Mall Report', 'url': '/admin/reports/comprehensive-report/', 'icon': 'fas fa-chart-line'},
            ]
        }
        return render(request, 'admin/reports_dashboard.html', context)

# Create custom admin site
mall_admin_site = MallAdminSite(name='mall_admin')

# Register models with custom admin classes
mall_admin_site.register(Shop, ShopAdmin)
mall_admin_site.register(Tenant, TenantAdmin)
mall_admin_site.register(AllocatedShop, AllocatedShopAdmin)
mall_admin_site.register(Complaint)
mall_admin_site.register(Manager)
mall_admin_site.register(Announcement)
mall_admin_site.register(RentPaymentTransaction)

# Register with default admin site as well
admin.site.register(Shop, ShopAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(AllocatedShop, AllocatedShopAdmin)
admin.site.register(Complaint)
admin.site.register(Manager)
admin.site.register(Announcement)
admin.site.register(RentPaymentTransaction)