from django import forms
from django.forms import modelformset_factory
from hub.models import *

class TenantUpdateForm(forms.ModelForm):
   class Meta:
    
       model = Tenant
       fields = ['phone','address']

class ShopnameUpdateForm(forms.ModelForm):
   class Meta:
    
       model = Shop
       fields = ['name']

class EmailUpdateForm(forms.ModelForm):
   class Meta:
    
       model = User
       fields = ['email']


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'description','shop','priority']

class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'resolution_notes']


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5, "cols": 40}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']  # Allow updating basic user details

class AllocateShopForm(forms.ModelForm):
    lease_start = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    lease_end = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = AllocatedShop
        fields = ["tenant_id", "lease_start", "lease_end", "rent_amount", "security_deposit", "payment_status", "agreement_document"]
        widgets = {
            "payment_status": forms.Select(choices=[("pending", "Pending"), ("complete", "Complete")]),
        }

class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["status", "resolution_notes","image"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "resolution_notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

class ManagerUpdateForm(forms.ModelForm):
    class Meta:
        model = Manager
        fields = ['phone', 'image']

        

ShopFormSet = modelformset_factory(Shop, form=ShopnameUpdateForm, extra=0)