from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils.html import format_html
from .models import DonorProfile, AdminProfile, PatientProfile

# Unregister default User and Group admins
admin.site.unregister(User)
admin.site.unregister(Group)

# Register your models here.

@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    """
    Django admin configuration for DonorProfile model.
    """
    list_display = ['full_name', 'user', 'blood_group', 'age', 'contact_number', 'created_at']
    list_filter = ['blood_group', 'gender', 'created_at']
    search_fields = ['full_name', 'user__username', 'contact_number']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'age', 'gender', 'contact_number', 'address')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'weight', 'height', 'medical_conditions')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    """
    Django admin configuration for AdminProfile model.
    """
    list_display = ['full_name', 'employee_id', 'user', 'get_admin_type', 'is_active', 'created_at']
    list_filter = ['is_super_admin', 'is_secondary_admin', 'is_active', 'created_at']
    search_fields = ['full_name', 'employee_id', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'employee_id', 'department', 'phone_number')
        }),
        ('Admin Type', {
            'fields': ('is_super_admin', 'is_secondary_admin'),
            'description': 'Admin type is automatically set based on user groups'
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_admin_type(self, obj):
        if obj.is_super_admin:
            return format_html('<span style="color: red; font-weight: bold;">Super Admin</span>')
        elif obj.is_secondary_admin:
            return format_html('<span style="color: blue;">Secondary Admin</span>')
        return "Regular User"
    get_admin_type.short_description = "Admin Type"

    # Permissions - only superusers can manage admin profiles
    def has_add_permission(self, request):
        """Only superusers can add admin profiles"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Only superusers can modify admin profiles"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete admin profiles"""
        return request.user.is_superuser

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """
    Django admin configuration for PatientProfile model.
    """
    list_display = ['full_name', 'user', 'blood_group', 'age', 'contact_number', 'created_at']
    list_filter = ['blood_group', 'gender', 'created_at']
    search_fields = ['full_name', 'user__username', 'contact_number']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'age', 'gender', 'contact_number', 'address')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'emergency_contact', 'medical_history')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_admin_type', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'groups', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_admin_type(self, obj):
        if hasattr(obj, 'admin_profile'):
            if obj.admin_profile.is_super_admin:
                return format_html('<span style="color: red; font-weight: bold;">Super Admin</span>')
            elif obj.admin_profile.is_secondary_admin:
                return format_html('<span style="color: blue;">Secondary Admin</span>')
        if obj.groups.filter(name='Super Admin').exists():
            return format_html('<span style="color: red; font-weight: bold;">Super Admin</span>')
        elif obj.groups.filter(name='Secondary Admin').exists():
            return format_html('<span style="color: blue;">Secondary Admin</span>')
        return "Regular User"
    get_admin_type.short_description = "Admin Type"

# Custom Group Admin
class CustomGroupAdmin(GroupAdmin):
    pass

# Register custom admins
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)

# Customize admin site header and title
admin.site.site_header = "Blood Bank Management System"
admin.site.site_title = "Blood Bank Admin"
admin.site.index_title = "Blood Bank Administration"
