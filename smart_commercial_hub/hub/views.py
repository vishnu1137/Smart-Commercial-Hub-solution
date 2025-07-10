from datetime import datetime
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist  
from django.contrib.auth.decorators import login_required,user_passes_test
from django.urls import reverse
from hub.models import *
from hub.forms import *
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
import calendar
from django.contrib.admin.views.decorators import staff_member_required
import json
import razorpay
import uuid
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from num2words import num2words
from io import BytesIO
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
import datetime
import io
import pandas as pd
import matplotlib.pyplot as plt
from django.utils.timezone import now
from weasyprint import HTML


def is_manager(user):
    return hasattr(user,'manager')

@login_required
@user_passes_test(is_manager)
def manager_rent_payments(request):
    # Get all rent payments
    payments = RentPaymentTransaction.objects.all().order_by('-created_at')

    # Filters
    tenant_name = request.GET.get('tenant_name')
    payment_status = request.GET.get('payment_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if tenant_name:
        payments = payments.filter(
            Q(tenant__tenant_id__tenant__username__icontains=tenant_name) |
            Q(tenant__tenant_id__tenant__first_name__icontains=tenant_name) |
            Q(tenant__tenant_id__tenant__last_name__icontains=tenant_name)
        )

    if payment_status:
        payments = payments.filter(payment_status__icontains=payment_status)

    if start_date and end_date:
        payments = payments.filter(created_at__date__range=[start_date, end_date])

    context = {
        'payments': payments
    }

    return render(request, 'manager/track_rent_payments.html', context)

def download_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return HttpResponse("Missing start_date or end_date", status=400)

    shops = Shop.objects.filter(created_at__range=[start_date, end_date])
    complaints = Complaint.objects.filter(created_at__range=[start_date, end_date])
    payments = RentPaymentTransaction.objects.filter(created_at__range=[start_date, end_date])

    occupied_count = shops.filter(status='occupied').count()
    vacant_count = shops.filter(status='vacant').count()

    complaint_status = complaints.values('status').annotate(count=models.Count('id'))
    complaint_category = complaints.values('category').annotate(count=models.Count('id'))
    payment_status = payments.values('payment_status').annotate(count=models.Count('id'))

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Shops Sheet
        df_shops = pd.DataFrame({
            'Shop Status': ['Occupied', 'Vacant'],
            'Count': [occupied_count, vacant_count]
        })
        df_shops.to_excel(writer, sheet_name='Shops', index=False)

        # Payments Sheet
        df_payments = pd.DataFrame(list(payment_status))
        if not df_payments.empty:
            df_payments.columns = ['Payment Status', 'Count']
        df_payments.to_excel(writer, sheet_name='Payments', index=False)

        # Complaint Status Sheet
        df_complaints = pd.DataFrame(list(complaint_status))
        if not df_complaints.empty:
            df_complaints.columns = ['Complaint Status', 'Count']
        df_complaints.to_excel(writer, sheet_name='Complaints Status', index=False)

        # Complaint Categories Sheet
        df_categories = pd.DataFrame(list(complaint_category))
        if not df_categories.empty:
            df_categories.columns = ['Complaint Category', 'Count']
        df_categories.to_excel(writer, sheet_name='Complaint Categories', index=False)

    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = f"mall_report_{now().strftime('%d%m%Y')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return HttpResponse("Missing start_date or end_date", status=400)

    # Fetching Data
    shops = Shop.objects.filter(created_at__range=[start_date, end_date])
    complaints = Complaint.objects.filter(created_at__range=[start_date, end_date])
    payments = RentPaymentTransaction.objects.filter(created_at__range=[start_date, end_date])

    occupied_count = shops.filter(status='occupied').count()
    vacant_count = shops.filter(status='vacant').count()

    complaint_status = complaints.values('status').annotate(count=models.Count('id'))
    complaint_category = complaints.values('category').annotate(count=models.Count('id'))
    payment_status = payments.values('payment_status').annotate(count=models.Count('id'))

    # Render HTML to PDF
    html_string = render_to_string('report_pdf_template.html', {
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'complaint_status': complaint_status,
        'complaint_category': complaint_category,
        'payment_status': payment_status,
        'now': now(),
        'start_date': start_date,
        'end_date': end_date
    })

    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    print("entry start")
    email = EmailMessage(
        subject=f"Mall Management Report ({start_date} to {end_date})",
        body="Dear Owner,\n\nPlease find attached the latest mall manager report.\n\nBest regards,\nSmart Commercial Hub System",
        from_email=settings.MANAGER_EMAIL,
        to=[settings.EMAIL_HOST_USER],
    )
    print("sucess")

    email.attach(f"Mall_Report_{now().strftime('%d%m%Y')}.pdf", pdf_file, 'application/pdf')
    email.send(fail_silently=False)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="mall_report_{now().strftime("%d%m%Y")}.pdf"'
    return response

# views.py

def generate_combined_report(request):
    managers = Manager.objects.all()
    context = {
        'managers': managers,
        'show_report': False,  # By default hide report
    }

    if request.GET.get('start_date') and request.GET.get('end_date') and request.GET.get('manager'):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        manager_id = request.GET.get('manager')

        # Fetch shops, complaints, payments
        shops = Shop.objects.filter(created_at__range=[start_date, end_date])
        complaints = Complaint.objects.filter(created_at__range=[start_date, end_date])
        payments = RentPaymentTransaction.objects.filter(created_at__range=[start_date, end_date])

        # Shop Status
        occupied_count = shops.filter(status='occupied').count()
        vacant_count = shops.filter(status='vacant').count()

        # Complaint Status
        complaint_status = complaints.values('status').annotate(count=Count('id'))

        # Complaint Categories
        complaint_category = complaints.values('category').annotate(count=Count('id'))

        # Payment Status
        payment_status = payments.values('payment_status').annotate(count=Count('id'))

        context.update({
            'occupied_count': occupied_count,
            'vacant_count': vacant_count,
            'complaint_status': complaint_status,
            'complaint_category': complaint_category,
            'payment_status': payment_status,
            'start_date': start_date,
            'end_date': end_date,
            'selected_manager_id': manager_id,
            'show_report': True,
        })

    return render(request, 'report_combined.html', context)

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def initiate_payment(request):
    """View to show list of shops for payment and initiate payment flow"""
    
    if not request.user.is_authenticated:
        return redirect('login')
        
    try:
        # Get tenant's allocated shops that need payment
        tenant = request.user.tenant
        allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant, payment_status='pending')
        
        return render(request, 'select_shop_for_payment.html', {'allocated_shops': allocated_shops})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def create_payment(request, allocated_shop_id):
    """View to create a Razorpay Order for rent payment"""
    
    # Get the allocated shop
    allocated_shop = get_object_or_404(AllocatedShop, id=allocated_shop_id)
    
    # Check if the logged-in user is the tenant of this shop
    if request.user != allocated_shop.tenant_id.tenant:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get amount from allocated shop's rent_amount
        amount = int(float(allocated_shop.rent_amount) * 100)  # Convert to paise
        currency = 'INR'
        
        # Generate a unique receipt ID
        receipt_id = f"rent_{allocated_shop_id}_{uuid.uuid4().hex[:8]}"
        
        # Create Razorpay Order
        payment_data = {
            'amount': amount,
            'currency': currency,
            'receipt': receipt_id,
            'payment_capture': '1'  # Auto capture
        }
        
        order = client.order.create(data=payment_data)
        
        # Create a record in RentPaymentTransaction
        transaction = RentPaymentTransaction.objects.create(
            tenant=allocated_shop,  # Using tenant field
            shop=allocated_shop,    # Using shop field
            transaction_id=order['id'],
            amount=float(allocated_shop.rent_amount),
            currency=currency,
            payment_status='Created',
            order_receipt_id=receipt_id
        )
        
        # Prepare payment context for template
        context = {
            'razorpay_order_id': order['id'],
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': amount,
            'currency': currency,
            'callback_url': f'/payment/callback/{transaction.id}/',
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
            'customer_phone': allocated_shop.tenant_id.phone,
            'allocated_shop': allocated_shop
        }
        
        return render(request, 'payment.html', context)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def payment_callback(request, transaction_id):
    """Callback view for payment verification"""
    
    # Get the transaction
    transaction = get_object_or_404(RentPaymentTransaction, id=transaction_id)
    
    if request.method == "POST":
        try:
            # Get payment data
            payment_data = request.POST
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': payment_data.get('razorpay_order_id', ''),
                'razorpay_payment_id': payment_data.get('razorpay_payment_id', ''),
                'razorpay_signature': payment_data.get('razorpay_signature', '')
            }
            
            # Verify the payment signature
            client.utility.verify_payment_signature(params_dict)
            
            # Update transaction details
            transaction.payment_id = payment_data.get('razorpay_payment_id', '')
            transaction.payment_status = 'Success'
            transaction.amount_paid = True
            transaction.save()
            
            # Update AllocatedShop payment status
            allocated_shop = transaction.shop
            allocated_shop.payment_status = 'complete'
            allocated_shop.save()
            
            return redirect('view_receipt', transaction_id=transaction.id)
        except Exception as e:
            # Payment verification failed
            transaction.payment_status = 'Failed'
            transaction.attempts = transaction.attempts + 1
            transaction.save()
            
            return render(request, 'payment_failure.html', {'error': str(e), 'transaction': transaction})
    
    # GET request, redirect to payment page
    return redirect('initiate_payment')

@login_required
def view_receipt(request, transaction_id):
    """View to display an HTML receipt for a completed transaction"""
    transaction = get_object_or_404(RentPaymentTransaction, id=transaction_id)
    
    # Security check: ensure the logged-in user is the tenant who made this payment
    if request.user != transaction.tenant.tenant_id.tenant:
        return HttpResponse("Unauthorized", status=403)
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'tenant/rent_receipt.html', context)

@login_required
def download_receipt_pdf(request, transaction_id):
    """View to generate and download a PDF receipt"""
    transaction = get_object_or_404(RentPaymentTransaction, id=transaction_id)
    
    # Security check: ensure the logged-in user is the tenant who made this payment
    if request.user != transaction.tenant.tenant_id.tenant:
        return HttpResponse("Unauthorized", status=403)
    
    context = {
        'transaction': transaction,
        'request': request,
    }
    
    # Generate PDF from template
    pdf = render_to_pdf('tenant/rent_receipt_pdf.html', context)
    
    # Generate a filename for the PDF
    filename = f"rent_receipt_{transaction.transaction_id[:8]}_{timezone.now().strftime('%Y%m%d')}.pdf"
    
    # Configure the response to prompt a download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# Update payment history view to include receipt links
@login_required
def payment_history(request):
    """View to show payment history with receipt download options"""
    
    try:
        tenant = request.user.tenant
        # Find all allocated shops for this tenant
        allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)
        
        # Get transactions where tenant field matches any of these allocated shops
        transactions = RentPaymentTransaction.objects.filter(
            tenant__in=allocated_shops
        ).order_by('-created_at')
        
        context = {
            'transactions': transactions
        }
        return render(request, 'tenant/payment_history.html', context)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
#Rent payment

def shop_rent(request):
    allocated_shops = AllocatedShop.objects.filter(tenant_id__tenant=request.user)

    return render(request, "tenant/shop_rent.html", {"allocated_shops": allocated_shops})


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
            allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)  # Fix the query
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
    
    if hasattr(user, 'tenant'):
        tenant = user.tenant
        
        # Get tenant's allocated shops
        allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)
        
        # Extract shop IDs
        shop_ids = [alloc.shop_id.id for alloc in allocated_shops]
        shops = Shop.objects.filter(id__in=shop_ids)
        
        # Create a formset for editing just the shop names
        ShopNameFormSet = modelformset_factory(
            Shop, 
            form=ShopNameOnlyForm,
            extra=0
        )
        
        if request.method == "POST":
            tenant_form = TenantUpdateForm(request.POST, request.FILES, instance=tenant)
            email_form = EmailUpdateForm(request.POST, instance=user)
            shop_formset = ShopNameFormSet(request.POST, queryset=shops)
            
            if tenant_form.is_valid() and email_form.is_valid() and shop_formset.is_valid():
                tenant_form.save()
                email_form.save()
                shop_formset.save()
                messages.success(request, "Profile and shop details updated successfully!")
                return redirect("profile")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            tenant_form = TenantUpdateForm(instance=tenant)
            email_form = EmailUpdateForm(instance=user)
            shop_formset = ShopNameFormSet(queryset=shops)
        
        return render(request, "tenant/edit_profile.html", {
            'tenant_form': tenant_form,
            'email_form': email_form,
            'shop_formset': shop_formset,
        })
    
    elif hasattr(user, 'manager'):
        # Manager handling code remains the same
        manager = user.manager
        
        if request.method == "POST":
            manager_form = ManagerUpdateForm(request.POST, request.FILES, instance=manager)
            email_form = EmailUpdateForm(request.POST, instance=user)
            
            if manager_form.is_valid() and email_form.is_valid():
                manager_form.save()
                email_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("profile")
            else:
                messages.error(request, "Error updating profile. Please check the form.")
        else:
            manager_form = ManagerUpdateForm(instance=manager)
            email_form = EmailUpdateForm(instance=user)
        
        return render(request, "manager/edit_profile.html", {
            'manager_form': manager_form,
            'email_form': email_form,
        })
    
    else:
        messages.warning(request, "You don't have a profile to edit.")
        return redirect("dashboard")
    
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
    # Ensure the user is a tenant
    if not hasattr(request.user, 'tenant'):
        messages.error(request, "Only tenants can submit complaints.")
        return redirect('dashboard')
    
    tenant = request.user.tenant
    
    # Get only allocations for this tenant
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)
    
    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        
        # Limit shop choices to AllocatedShop instances for this tenant
        form.fields['shop'].queryset = allocated_shops
        
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = request.user
            complaint.save()
            messages.success(request, "Complaint submitted successfully!")
            return redirect('view_complaints')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ComplaintForm()
        # Limit shop choices to AllocatedShop instances for this tenant
        form.fields['shop'].queryset = allocated_shops
    
    return render(request, 'tenant/submit_complaint.html', {'form': form})

@login_required
def view_complaints(request):
    # Ensure the user is a tenant
    if not hasattr(request.user, 'tenant'):
        messages.error(request, "Only tenants can view their complaints.")
        return redirect('dashboard')
        
    tenant = request.user.tenant
    
    # Get shop allocations for this tenant
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant)
    
    # Get complaints related to these allocated shops
    complaints = Complaint.objects.filter(shop__in=allocated_shops)
    
    return render(request, "tenant/view_complaints.html", {
        "complaints": complaints,
        "tenant_shops": allocated_shops
    })

#MANAGER

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

def occupied_shops(request):
    allocated_shops = AllocatedShop.objects.select_related('shop_id', 'tenant_id__tenant')\
                                           .filter(shop_id__status='occupied')
    return render(request, "manager/occupied_shop.html", {"allocated_shops": allocated_shops})

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
            print(f"Sending email to: {tenant_email}")
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
    allocated_shops = AllocatedShop.objects.filter(tenant_id=tenant_id)  

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

def admin_dashboard(request):
    total_tenants = Tenant.objects.count()
    total_shops = Shop.objects.count()
    total_complaints = Complaint.objects.count()

    context = {
        'total_tenants': total_tenants,
        'total_shops': total_shops,
        'total_complaints': total_complaints,
    }
    return render(request, 'dashboard.html', context)

#payment

def rent_list(request):
    # Assuming request.user is a tenant
    #rents = RentRecord.objects.filter(allocated_shop__tenant__user=request.user).order_by('-month')
    return render(request, 'tenant/rent_list.html')

@staff_member_required
def admin_reports(request):
    """Dashboard for all available report types"""
    return render(request, 'admin/reports_dashboard.html')

@staff_member_required
def shop_occupancy_report(request):
    """Generate a report on shop occupancy status"""
    total_shops = Shop.objects.count()
    occupied_shops = Shop.objects.filter(status='occupied').count()
    vacant_shops = Shop.objects.filter(status='vacant').count()
    
    # Get occupancy by shop type
    shop_types_data = Shop.objects.values('shop_type').annotate(
        total=Count('id'),
        occupied=Count('id', filter=Q(status='occupied')),
        vacant=Count('id', filter=Q(status='vacant'))
    )
    
    # Calculate occupancy rate
    occupancy_rate = (occupied_shops / total_shops * 100) if total_shops > 0 else 0
    
    context = {
        'total_shops': total_shops,
        'occupied_shops': occupied_shops,
        'vacant_shops': vacant_shops,
        'occupancy_rate': round(occupancy_rate, 2),
        'shop_types_data': shop_types_data
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/shop_occupancy_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"shop_occupancy_report_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/shop_occupancy.html', context)

@staff_member_required
def rental_income_report(request):
    """Generate a report on rental income"""
    # Get current month and year
    today = timezone.now()
    current_month = today.month
    current_year = today.year
    
    # Extract month and year from request or use current
    month = int(request.GET.get('month', current_month))
    year = int(request.GET.get('year', current_year))
    
    # Start and end dates for the selected month
    start_date = datetime(year, month, 1).date()
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day).date()
    
    # Get rent transactions for the period
    transactions = RentPaymentTransaction.objects.filter(
        payment_status='Success',
        created_at__gte=start_date,
        created_at__lte=end_date + timedelta(days=1)  # Add a day to include the entire end date
    )
    
    # Calculate total income
    total_income = transactions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get income by shop type
    income_by_shop_type = []
    for shop_type in dict(Shop.SHOP_TYPES).keys():
        amount = transactions.filter(
            shop__shop_id__shop_type=shop_type
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income_by_shop_type.append({
            'shop_type': dict(Shop.SHOP_TYPES)[shop_type],
            'amount': amount
        })
    
    # Highest and lowest paying shops
    best_shops = transactions.values(
        'shop__shop_id__name', 'shop__shop_id__shop_no'
    ).annotate(
        total_paid=Sum('amount')
    ).order_by('-total_paid')[:5]
    
    context = {
        'month': calendar.month_name[month],
        'year': year,
        'total_income': total_income,
        'transaction_count': transactions.count(),
        'income_by_shop_type': income_by_shop_type,
        'best_shops': best_shops,
        'all_months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'current_month': month,
        'current_year': year,
        'years': range(current_year-2, current_year+1)
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/rental_income_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"rental_income_report_{month}_{year}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/rental_income.html', context)

@staff_member_required
def lease_expiry_report(request):
    """Generate a report on upcoming lease expirations"""
    today = timezone.now().date()
    
    # Get leases expiring in the next 30, 60, and 90 days
    expiring_30_days = AllocatedShop.objects.filter(
        lease_end__gte=today,
        lease_end__lte=today + timedelta(days=30),
        status='active'
    ).order_by('lease_end')
    
    expiring_60_days = AllocatedShop.objects.filter(
        lease_end__gt=today + timedelta(days=30),
        lease_end__lte=today + timedelta(days=60),
        status='active'
    ).order_by('lease_end')
    
    expiring_90_days = AllocatedShop.objects.filter(
        lease_end__gt=today + timedelta(days=60),
        lease_end__lte=today + timedelta(days=90),
        status='active'
    ).order_by('lease_end')
    
    # Get expired leases that are still active
    expired_leases = AllocatedShop.objects.filter(
        lease_end__lt=today,
        status='active'
    ).order_by('lease_end')
    
    context = {
        'today': today,
        'expiring_30_days': expiring_30_days,
        'expiring_60_days': expiring_60_days,
        'expiring_90_days': expiring_90_days,
        'expired_leases': expired_leases,
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/lease_expiry_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"lease_expiry_report_{today.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/lease_expiry.html', context)

@staff_member_required
def complaint_analysis_report(request):
    """Generate a report analyzing complaints"""
    # Get date range from request or use last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=int(request.GET.get('days', 30)))
    
    # Get complaints for the period
    complaints = Complaint.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Total complaints by status
    complaints_by_status = complaints.values('status').annotate(count=Count('id'))
    
    # Complaints by category
    complaints_by_category = complaints.values('category').annotate(count=Count('id'))
    
    # Average resolution time for resolved complaints
    avg_resolution_time = complaints.filter(
        status='resolved',
        resolved_at__isnull=False
    ).annotate(
        resolution_time=F('resolved_at') - F('created_at')
    ).aggregate(avg_time=Avg('resolution_time'))
    
    avg_days = None
    if avg_resolution_time['avg_time']:
        avg_days = avg_resolution_time['avg_time'].total_seconds() / (3600 * 24)  # Convert to days
    
    # Shops with most complaints
    shops_with_most_complaints = complaints.values(
        'shop__shop_id__name', 'shop__shop_id__shop_no'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_complaints': complaints.count(),
        'complaints_by_status': complaints_by_status,
        'complaints_by_category': complaints_by_category,
        'avg_resolution_time_days': round(avg_days, 1) if avg_days else None,
        'shops_with_most_complaints': shops_with_most_complaints,
        'days_options': [30, 60, 90, 180]
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/complaint_analysis_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"complaint_analysis_report_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/complaint_analysis.html', context)

@staff_member_required
def tenant_report(request):
    """Generate a report on tenant information and status"""
    # Get all tenants
    tenants = Tenant.objects.all()
    
    # Calculate tenure for each tenant
    tenant_data = []
    for tenant in tenants:
        allocations = AllocatedShop.objects.filter(tenant_id=tenant)
        shops = [a.shop_id.name for a in allocations]
        
        # Find earliest lease start date to calculate tenure
        earliest_lease = allocations.order_by('lease_start').first()
        tenure_days = None
        if earliest_lease:
            tenure_days = (timezone.now().date() - earliest_lease.lease_start).days
        
        # Calculate total rent paid
        total_paid = RentPaymentTransaction.objects.filter(
            tenant__tenant_id=tenant,
            payment_status='Success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        tenant_data.append({
            'tenant': tenant,
            'shops': shops,
            'shop_count': len(shops),
            'tenure_days': tenure_days,
            'tenure_years': round(tenure_days / 365, 1) if tenure_days else None,
            'total_paid': total_paid
        })
    
    # Sort by tenure (longest first)
    tenant_data.sort(key=lambda x: x['tenure_days'] or 0, reverse=True)
    
    context = {
        'tenant_data': tenant_data,
        'total_tenants': tenants.count()
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/tenant_report_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"tenant_report_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/tenant_report.html', context)

@staff_member_required
def comprehensive_mall_report(request):
    """Generate a comprehensive report with all key metrics"""
    today = timezone.now().date()
    
    # Shop metrics
    total_shops = Shop.objects.count()
    occupied_shops = Shop.objects.filter(status='occupied').count()
    vacant_shops = Shop.objects.filter(status='vacant').count()
    occupancy_rate = (occupied_shops / total_shops * 100) if total_shops > 0 else 0
    
    # Shop breakdown by type
    shop_type_distribution = Shop.objects.values('shop_type').annotate(count=Count('id'))
    
    # Tenant metrics
    total_tenants = Tenant.objects.count()
    
    # Revenue metrics - current month
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    current_month_revenue = RentPaymentTransaction.objects.filter(
        payment_status='Success',
        created_at__date__gte=first_day_of_month,
        created_at__date__lte=last_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Revenue metrics - year to date
    first_day_of_year = today.replace(month=1, day=1)
    ytd_revenue = RentPaymentTransaction.objects.filter(
        payment_status='Success',
        created_at__date__gte=first_day_of_year,
        created_at__date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending payments
    pending_payments = AllocatedShop.objects.filter(payment_status='pending').count()
    pending_amount = AllocatedShop.objects.filter(
        payment_status='pending'
    ).aggregate(total=Sum('rent_amount'))['total'] or 0
    
    # Complaints
    active_complaints = Complaint.objects.filter(
        status__in=['pending', 'in_progress']
    ).count()
    
    # Upcoming lease expirations
    upcoming_expirations = AllocatedShop.objects.filter(
        lease_end__gte=today,
        lease_end__lte=today + timedelta(days=30),
        status='active'
    ).count()
    
    context = {
        'report_date': today,
        'total_shops': total_shops,
        'occupied_shops': occupied_shops,
        'vacant_shops': vacant_shops,
        'occupancy_rate': round(occupancy_rate, 2),
        'shop_type_distribution': shop_type_distribution,
        'total_tenants': total_tenants,
        'current_month': today.strftime('%B %Y'),
        'current_month_revenue': current_month_revenue,
        'ytd_revenue': ytd_revenue,
        'pending_payments': pending_payments,
        'pending_amount': pending_amount,
        'active_complaints': active_complaints,
        'upcoming_expirations': upcoming_expirations
    }
    
    if 'download_pdf' in request.GET:
        # Generate PDF
        template_name = 'admin/reports/comprehensive_report_pdf.html'
        context['is_pdf'] = True
        pdf = render_to_pdf(template_name, context)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"mall_comprehensive_report_{today.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return render(request, 'admin/reports/comprehensive_report.html', context)
