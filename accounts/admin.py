# accounts/admin.py
from django.contrib import admin
from .models import ResearchField, UserProfile, Role, UserRole

@admin.register(ResearchField)
class ResearchFieldAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'institution')
    search_fields = ('full_name', 'email')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active')
    list_filter = ('role', 'is_active')