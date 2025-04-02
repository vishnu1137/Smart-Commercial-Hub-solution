from django.urls import path
from django.contrib.auth import views as auth_views
from hub.views import *

urlpatterns = [

    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),

    path("login/", user_login, name="user_login"),
    path("logout/", user_logout, name="user_logout"),
    path('details/<int:shop_id>/', shop_details, name="shop_details"),
    #path("update/", update_tenant, name="update_tenant"),
    path("dashboard/", tenant_dashboard, name="tenant_dashboard"),
    #path('profile/', tenant_profile, name='tenant_profile'),

    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    path('submit-complaint/', submit_complaint, name='submit_complaint'),
    path('view-complaints/', view_complaints, name='view_complaints'),
    path('my_shop/', my_shop, name='my_shop'),
    path('lease_details/', lease_details, name='lease_details'),
    path('announcements/', announcements, name='announcements'),
    #manager
    path('manager-dashboard/', manager_dashboard, name='manager_dashboard'),
    path("manage-tenants/", manage_tenants, name="manage_tenants"),
    path('allocate-shop/<int:shop_id>/', allocate_shop, name='allocate_shop'),
    path('shop-details/<int:shop_id>/', shop_details, name='shop_details'),
    path('tenant-details/<int:tenant_id>/', tenant_details, name="tenant_details"),
    #path('manager/profile/', manager_profile, name='manager_profile'),
    #path('manager/profile/edit/', edit_manager_profile, name='edit_manager_profile'),
    path('occupied-shops/', occupied_shops, name='occupied_shops'),
    path('vacant-shops/', vacant_shops, name='vacant_shops'),
    path("manage-tenants/", manage_tenants, name="manage_tenants"),
    path("tenant-details/<int:tenant_id>/", tenant_details, name="tenant_details"),
    path("post-announcement/", post_announcement, name="post_announcement"),
    path("manage-announcements/", manage_announcements, name="manage_announcements"),
    path("delete-announcement/<int:announcement_id>/", delete_announcement, name="delete_announcement"),
    path('announcement-side/', submit_complaint, name='submit_complaint'),
    path("manage-complaints/", manage_complaints, name="manage_complaints"),
    path("update-complaint/<int:complaint_id>/", update_complaint, name="update_complaint"),

    
]