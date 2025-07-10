from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from hub.models import *

@receiver(post_save, sender=Complaint)
def send_complaint_resolved_email(sender, instance, **kwargs):
    if instance.status == "resolved":
        tenant_email = None
        tenant_name = "Tenant"

        #Check if Complaint is linked to `AllocatedShop`
        if hasattr(instance, "allocated_shop") and instance.allocated_shop:
            tenant = instance.allocated_shop.tenant_id  # Correct way to access Tenant
            if tenant and hasattr(tenant, "user"):
                tenant_email = tenant.user.email
                tenant_name = tenant.user.username  # Adjust if username is stored differently

        if tenant_email:
            subject = "Your Complaint Has Been Resolved"
            message = (
                f"Dear {tenant_name},\n\n"
                f"Your complaint (ID: {instance.id}) has been resolved. "
                "If you have any further issues, feel free to contact us.\n\n"
                "Best Regards,\nManagement Team"
            )

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [tenant_email],
                fail_silently=False,
            )

@receiver(post_delete, sender=AllocatedShop)
def update_shop_status_on_delete(sender, instance, **kwargs):
    """Change shop status to 'vacant' when an allocated shop is deleted."""
    if instance.shop_id:  # Ensure the shop exists
        instance.shop_id.status = "vacant"
        instance.shop_id.save()
