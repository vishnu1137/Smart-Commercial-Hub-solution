from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


#shop 

def generate_shop_no():
    last_shop = Shop.objects.order_by('-id').first()
    next_number = last_shop.id + 1 if last_shop else 1
    return f"Shop-{next_number}"

class Shop(models.Model):

    STATUS_CHOICES = [
        ('occupied','Occupied'),
        ('vacant','Vacant'),
    ]

    SHOP_TYPES = [
        ('retail', 'Retail'),
        ('restaurant', 'Restaurant'),
        ('service', 'Service'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]


    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=115)
    shop_no = models.CharField(max_length=10,unique=True,default=generate_shop_no)
    size = models.IntegerField(null=True,blank=True)
    location = models.CharField(max_length=115)
    shop_type = models.CharField(max_length=50,choices=SHOP_TYPES)
    status = models.CharField(max_length=15,choices=STATUS_CHOICES,default='vacant')
    image = models.ImageField(upload_to='shop_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.shop_no})"

#tenant
class Tenant(models.Model):
    id = models.AutoField(primary_key=True)
    tenant = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=12)
    address = models.CharField(max_length=255)
    id_proof = models.FileField(upload_to='id_proof/',null=True,blank=True)
    image = models.ImageField(upload_to='tenant_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tenant.username



PAYMENT_STATUS = [
        ('complete','Complete'),
        ('pending','Pending'),
    ]

STATUS_CHOICES = [
        ('active', 'Active'),
        ('terminated', 'Terminated'),
    ]

#allocatedshop
class AllocatedShop(models.Model):
    id = models.AutoField(primary_key=True)
    shop_id = models.ForeignKey(Shop,on_delete=models.CASCADE,related_name='shops')
    tenant_id = models.ForeignKey(Tenant,on_delete=models.CASCADE,related_name='tenants')
    lease_start = models.DateField()
    lease_end = models.DateField()
    rent_amount = models.DecimalField(max_digits=7,decimal_places=2)
    security_deposit = models.DecimalField(max_digits=7,decimal_places=2)
    payment_status = models.CharField(max_length=15,choices=PAYMENT_STATUS)
    status = models.CharField(max_length=10,choices=STATUS_CHOICES)
    agreement_document = models.FileField(upload_to='agreement/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant_id.tenant} - {self.shop_id.name}"

FLOOR_CHOICES = [
    ('all','All'),
    ('floor 1','Floor 1'),
    ('floor 2','Floor 2'),
    ('floor 3','Floor 3'),

]

ROLE_CHOICES = [
        ('general_manager', 'General Manager'),
        ('property_manager', 'Property Manager'),
        ('finance_manager', 'Finance Manager'),
    ]

STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

#manager

class Manager(models.Model):
    id= models.AutoField(primary_key=True)
    manager = models.OneToOneField(User,on_delete=models.CASCADE)
    phone = models.CharField(max_length=12)
    description = models.TextField()
    role = models.CharField(max_length=25,choices=ROLE_CHOICES)
    floor= models.CharField(max_length=10,choices=FLOOR_CHOICES)
    salary = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES)
    image = models.ImageField(upload_to='manager_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.manager.username

STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
#announcement

class Announcement(models.Model):

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    message = models.CharField(max_length=255)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('billing', 'Billing Issue'),
        ('security', 'Security Concern'),
        ('other', 'Other'),
    ]

STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

#complaint

class Complaint(models.Model):
    id = models.AutoField(primary_key=True)
    shop = models.ForeignKey(AllocatedShop,on_delete=models.CASCADE,related_name='allocat_shops')
    category = models.CharField(max_length=25,choices=CATEGORY_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='resolved_images/', null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.shop.tenant_id.tenant.username} - {self.category} ({self.status})"