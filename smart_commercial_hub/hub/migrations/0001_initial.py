# Generated by Django 5.1.7 on 2025-03-10 18:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AllocatedShop',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('lease_start', models.DateField()),
                ('lease_end', models.DateField()),
                ('rent_amount', models.DecimalField(decimal_places=2, max_digits=7)),
                ('security_deposit', models.DecimalField(decimal_places=2, max_digits=7)),
                ('payment_status', models.CharField(choices=[('complete', 'Complete'), ('pending', 'Pending')], max_length=15)),
                ('status', models.CharField(choices=[('active', 'Active'), ('terminated', 'Terminated')], max_length=10)),
                ('agreement_document', models.FileField(blank=True, null=True, upload_to='agreement/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=115)),
                ('shop_no', models.CharField(max_length=10, unique=True)),
                ('size', models.IntegerField(blank=True, null=True)),
                ('location', models.CharField(max_length=115)),
                ('shop_type', models.CharField(choices=[('retail', 'Retail'), ('restaurant', 'Restaurant'), ('service', 'Service'), ('entertainment', 'Entertainment'), ('other', 'Other')], max_length=50)),
                ('status', models.CharField(choices=[('occupied', 'Occupied'), ('vacant', 'Vacant')], default='vacant', max_length=15)),
                ('image', models.ImageField(blank=True, null=True, upload_to='shop_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('message', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('maintenance', 'Maintenance'), ('billing', 'Billing Issue'), ('security', 'Security Concern'), ('other', 'Other')], max_length=25)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')], default='pending', max_length=15)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='resolved_images/')),
                ('resolution_notes', models.TextField(blank=True, null=True)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_complaints', to=settings.AUTH_USER_MODEL)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allocat_shops', to='hub.allocatedshop')),
            ],
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('phone', models.CharField(max_length=12)),
                ('description', models.TextField()),
                ('role', models.CharField(choices=[('general_manager', 'General Manager'), ('property_manager', 'Property Manager'), ('finance_manager', 'Finance Manager')], max_length=25)),
                ('floor', models.CharField(choices=[('all', 'All'), ('floor 1', 'Floor 1'), ('floor 2', 'Floor 2'), ('floor 3', 'Floor 3')], max_length=10)),
                ('salary', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended')], max_length=20)),
                ('image', models.ImageField(blank=True, null=True, upload_to='manager_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('manager', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='allocatedshop',
            name='shop_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shops', to='hub.shop'),
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('phone', models.CharField(max_length=12)),
                ('address', models.CharField(max_length=255)),
                ('id_proof', models.FileField(blank=True, null=True, upload_to='id_proof/')),
                ('image', models.ImageField(blank=True, null=True, upload_to='tenant_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='allocatedshop',
            name='tenant_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenants', to='hub.tenant'),
        ),
    ]
