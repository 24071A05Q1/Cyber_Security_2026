from django.contrib import admin
from .models import CustomUser, StudentProfile, EmployerProfile, AdminProfile
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'email', 'department', 'graduation_year', 'cgpa')
    list_filter = ('department', 'graduation_year')
    search_fields = ('name', 'user__username', 'email', 'skills')
    readonly_fields = ('user',)


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'contact_number', 'industry')
    list_filter = ('industry', 'company_size')
    search_fields = ('company_name', 'user__username', 'contact_number')
    readonly_fields = ('user',)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    list_filter = ('department',)
    search_fields = ('user__username', 'department')
    readonly_fields = ('user',)


admin.site.register(CustomUser, CustomUserAdmin)
