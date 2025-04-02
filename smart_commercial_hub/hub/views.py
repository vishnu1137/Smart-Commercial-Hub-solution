from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist  
from django.contrib.auth.decorators import login_required,user_passes_test
from django.urls import reverse
from hub.models import *
from hub.forms import *

#Authentication 

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            
            if user.is_superuser:  # Admin
                return redirect(reverse("admin:index"))  
            elif hasattr(user, "tenant"):  # Tenant
                return redirect(reverse("tenant_dashboard"))
            elif hasattr(user, "manager"):  # Manager
                return redirect(reverse("manager_dashboard"))
            else:  
                messages.error(request, "Unknown user role.")
                return redirect("login")

        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")

    return render(request, "login.html")

def user_logout(request):
    logout(request)
    return redirect("user_login")

#tenant

@login_required
def tenant_dashboard(request):
    try:
        # Get tenant details linked to the logged-in user
        tenant = Tenant.objects.get(tenant=request.user)

        # Get the allocated shop for this tenant
        allocated_shop = AllocatedShop.objects.filter(tenant_id=tenant).first()
    except Tenant.DoesNotExist:
        tenant = None
        allocated_shop = None

    # Fetch announcements (latest first)
    announcements = Announcement.objects.all().order_by('-published_at')

    return render(
        request,
        "tenant/dashboard.html",  # Your template file
        {
            "tenant": tenant,
            "allocated_shop": allocated_shop,
            "announcements": announcements,
        },
    )

@login_required
def profile_view(request):
    user = request.user
    tenant = None
    manager = None
    allocated_shops = None

    try:
        if hasattr(user, 'tenant'):  # Check if user is a Tenant
            tenant = user.tenant
            allocated_shops = AllocatedShop.objects.filter(tenant=tenant)  # Fix the query
            template_name = "tenant/profile.html"  # ✅ Tenant Profile Page

        elif hasattr(user, 'manager'):  # Check if user is a Manager
            manager = user.manager
            template_name = "manager/profile.html"  # ✅ Manager Profile Page

        else:
            return redirect("dashboard")  # Redirect unknown users to the dashboard

    except ObjectDoesNotExist:
        return redirect("dashboard")

    return render(request, template_name, {
        "tenant": tenant,
        "allocated_shops": allocated_shops if tenant else None,
        "manager": manager
    })

@login_required
def edit_profile(request):
    user = request.user
    tenant = None
    manager = None
    allocated_shops = None
    shop_formset = None  # ✅ Initialize shop_formset to avoid referencing before assignment

    try:
        if hasattr(user, 'tenant'):
            tenant = user.tenant
            allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant.id)  # ✅ Corrected field name

            tenant_form = TenantUpdateForm(instance=tenant)
            email_form = EmailUpdateForm(instance=user)
            shop_formset = ShopFormSet(queryset=Shop.objects.filter(id__in=[shop.shop_id.id for shop in allocated_shops]))

            template_name = "tenant/edit_profile.html"  # ✅ Tenant Edit Profile Page

            if request.method == "POST":
                tenant_form = TenantUpdateForm(request.POST, instance=tenant)
                email_form = EmailUpdateForm(request.POST, instance=user)
                shop_formset = ShopFormSet(request.POST, queryset=Shop.objects.filter(id__in=[shop.shop_id.id for shop in allocated_shops]))

                if tenant_form.is_valid() and email_form.is_valid() and shop_formset.is_valid():
                    tenant_form.save()
                    email_form.save()
                    shop_formset.save()
                    return redirect("profile")

        elif hasattr(user, 'manager'):
            manager = user.manager
            manager_form = ManagerUpdateForm(instance=manager)
            email_form = EmailUpdateForm(instance=user)

            template_name = "manager/edit_profile.html"  # ✅ Manager Edit Profile Page

            if request.method == "POST":
                manager_form = ManagerUpdateForm(request.POST, instance=manager)
                email_form = EmailUpdateForm(request.POST, instance=user)

                if manager_form.is_valid() and email_form.is_valid():
                    manager_form.save()
                    email_form.save()
                    return redirect("profile")

        else:
            return redirect("dashboard")  

    except ObjectDoesNotExist:  
        return redirect("dashboard")  

    return render(request, template_name, {
        'tenant_form': tenant_form if tenant else None,
        'shop_formset': shop_formset if tenant else None,
        'manager_form': manager_form if manager else None,
        'email_form': email_form
    })

def tenant_profile(request):
    tenant = request.user.tenant  # Get tenant details
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)  # Fetch allocated shops

    context = {
        'tenant': tenant,
        'allocated_shops': allocated_shops,
    }
    return render(request, 'tenant/profile.html', context)


@login_required
def update_tenant(request):
    tenant = request.user.tenant  # Get the tenant instance
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)  # Get all allocated shops
    shop_ids = [shop.shop_id.id for shop in allocated_shops]  # Extract shop IDs

    if request.method == "POST":
        tenant_form = TenantUpdateForm(request.POST, instance=tenant)
        email_form = EmailUpdateForm(request.POST, instance=request.user)
        shop_formset = ShopFormSet(request.POST, queryset=Shop.objects.filter(id__in=shop_ids))  # Get all tenant shops

        if tenant_form.is_valid() and email_form.is_valid() and shop_formset.is_valid():
            tenant_form.save()
            email_form.save()
            shop_formset.save()  # Save all updated shops
            return redirect('tenant_profile')  # Redirect to profile page after update
    else:
        tenant_form = TenantUpdateForm(instance=tenant)
        email_form = EmailUpdateForm(instance=request.user)
        shop_formset = ShopFormSet(queryset=Shop.objects.filter(id__in=shop_ids))

    context = {
        'tenant_form': tenant_form,
        'email_form': email_form,
        'shop_formset': shop_formset,
    }
    
    return render(request, 'tenant/update_tenant.html', context)


def my_shop(request):
    allocated_shops = AllocatedShop.objects.filter(tenant_id__tenant=request.user)

    return render(request, "tenant/my_shop.html", {"allocated_shops": allocated_shops})

def lease_details(request):
    leases = AllocatedShop.objects.filter(tenant_id__tenant=request.user)
    return render(request, "tenant/lease_details.html", {"leases": leases})

def announcements(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    return render(request, "tenant/announcements.html", {"announcements": announcements})


@login_required
def submit_complaint(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = request.user  
            complaint.save()
            return redirect('view_complaints')  
    else:
        form = ComplaintForm()
    return render(request, 'tenant/submit_complaint.html', {'form': form})

@login_required
def view_complaints(request):
    try:
        tenant_shops = AllocatedShop.objects.filter(tenant_id__tenant=request.user)
        complaints = Complaint.objects.filter(shop__in=tenant_shops)  # Fetch complaints related to tenant shops
    except Complaint.DoesNotExist:
        complaints = None

    return render(request, "tenant/view_complaints.html", {"complaints": complaints,"tenant_shops":tenant_shops})


#MANAGER

def is_manager(user):
    return hasattr(user,'manager')

@login_required
@user_passes_test(is_manager)

def manager_dashboard(request):
    total_shops = Shop.objects.count()
    total_tenants = Tenant.objects.count()
    pending_complaints = Complaint.objects.filter(status="pending").count()
    pending_payments = AllocatedShop.objects.filter(payment_status="pending").count()
    
    announcements = Announcement.objects.order_by("-created_at")[:5]
    recent_complaints = Complaint.objects.order_by("-created_at")[:5]

    context = {
        "total_shops": total_shops,
        "total_tenants": total_tenants,
        "pending_complaints": pending_complaints,
        "pending_payments": pending_payments,
        "announcements": announcements,
        "recent_complaints": recent_complaints,
    }
    
    return render(request, "manager/manager_dashboard.html", context)

@login_required
def manager_profile(request):
    user = request.user
    tenant = None
    manager = None
    allocated_shops = None
    managed_shops = None

    try:
        if hasattr(user, 'tenant'):
            tenant = user.tenant
            allocated_shops = tenant.allocatedshop_set.all()  # Shops assigned to the tenant
        elif hasattr(user, 'manager'):
            manager = user.manager
            managed_shops = Shop.objects.filter(manager=manager)  # Shops managed by the manager
    except ObjectDoesNotExist:
        pass  # If no tenant or manager exists, do nothing

    return render(request, 'profile.html', {
        'tenant': tenant,
        'manager': manager,
        'allocated_shops': allocated_shops,
        'managed_shops': managed_shops
    })

@login_required
def edit_manager_profile(request):
    user = request.user
    tenant = getattr(user, 'tenant', None)
    manager = getattr(user, 'manager', None)

    if request.method == "POST":
        email_form = EmailUpdateForm(request.POST, instance=user)

        if tenant:
            tenant_form = TenantUpdateForm(request.POST, request.FILES, instance=tenant)
            if email_form.is_valid() and tenant_form.is_valid():
                email_form.save()
                tenant_form.save()
                return redirect('profile')

        elif manager:
            manager_form = ManagerUpdateForm(request.POST, request.FILES, instance=manager)
            if email_form.is_valid() and manager_form.is_valid():
                email_form.save()
                manager_form.save()
                return redirect('profile')

    else:
        email_form = EmailUpdateForm(instance=user)
        tenant_form = TenantUpdateForm(instance=tenant) if tenant else None
        manager_form = ManagerUpdateForm(instance=manager) if manager else None

    return render(request, 'edit_profile.html', {
        'email_form': email_form,
        'tenant_form': tenant_form,
        'manager_form': manager_form
    })

def occupied_shops(request):
    shops = Shop.objects.filter(status='occupied')
    return render(request, "manager/occupied_shop.html", {"shops": shops})

def vacant_shops(request):
    shops = Shop.objects.filter(status='vacant')
    return render(request, "manager/vacant_shop.html", {"shops": shops})


def manage_tenants(request):
    tenants = Tenant.objects.all()
    return render(request, "manager/manage_tenants.html", {"tenants": tenants})

def allocate_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)

    if request.method == "POST":
        form = AllocateShopForm(request.POST)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.shop_id = shop
            allocation.save()

            # Update shop status to 'Occupied'
            shop.status = "occupied"
            shop.save()

            # Get the tenant's email
            tenant_email = allocation.tenant_id.tenant.email
            subject = "Shop Allocation Confirmation"
            message = (
                f"Dear {allocation.tenant_id.tenant.username},\n\n"
                f"You have been successfully allocated Shop {shop.shop_no} ({shop.name}).\n"
                f"Location: {shop.location}\n"
                f"Lease Start: {allocation.lease_start}\n"
                f"Lease End: {allocation.lease_end}\n"
                f"Rent Amount: ₹{allocation.rent_amount}\n"
                f"Security Deposit: ₹{allocation.security_deposit}\n\n"
                "Please contact the management for further details.\n\n"
                "Best Regards,\nSmart Commercial Hub Management"
            )

            # Send email to the tenant
            send_mail(subject, message, settings.EMAIL_HOST_USER, [tenant_email], fail_silently=False)

            messages.success(request, "Shop allocated successfully and email sent to the tenant.")
            return redirect("vacant_shops")

    else:
        form = AllocateShopForm()

    return render(request, "manager/allocate_shop.html", {"form": form, "shop": shop})

def shop_details(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    return render(request, 'manager/shop_details.html', {'shop': shop})

def tenant_details(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant_id)  # ✅ Fix here

    return render(request, "manager/tenant_details.html", {
        "tenant": tenant,
        "allocated_shops": allocated_shops,
    })

@login_required
def post_announcement(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.posted_by = request.user
            announcement.save()
            messages.success(request, "Announcement posted successfully!")
            return redirect("manage_announcements")
    else:
        form = AnnouncementForm()

    return render(request, "manager/post_announcement.html", {"form": form})

@login_required
def manage_announcements(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    return render(request, "manager/manage_announcements.html", {"announcements": announcements})

@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, "Announcement deleted successfully!")
    return redirect("manage_announcements")

# View all complaints
def manage_complaints(request):
    complaints = Complaint.objects.all().order_by("-created_at")
    return render(request, "manager/manage_complaints.html", {"complaints": complaints})

# Update complaint status
def update_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    tenant_email = complaint.shop.tenant_id.tenant.email  # ✅ Get tenant's email

    if request.method == "POST":
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            
            if complaint.status == "resolved":  # ✅ If the complaint is resolved
                complaint.resolved_at = now()
                complaint.save()

                # ✅ Send email to the tenant
                send_mail(
                    "Your Complaint Has Been Resolved",
                    f"Dear {complaint.shop.tenant_id.tenant.username},\n\n"
                    f"Your complaint (ID: {complaint.id}) has been resolved by the manager.\n"
                    f"If you have any further issues, feel free to reach out.\n\n"
                    f"Best regards,\nCommercial Hub Team",
                    settings.EMAIL_HOST_USER,
                    [tenant_email],  
                    fail_silently=False,
                )
                
                messages.success(request, "Complaint resolved and email sent to the tenant.")
            else:
                complaint.save()
                messages.success(request, "Complaint updated successfully.")

            return redirect("manage_complaints")
    else:
        form = ComplaintUpdateForm(instance=complaint)

    return render(request, "manager/update_complaint.html", {"form": form, "complaint": complaint})
