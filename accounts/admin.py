from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CourseClass, ClassMembership

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'full_name', 'matric_number', 'role', 'is_staff']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email')}),
        ('Role', {'fields': ('role',)}),
        ('Student info', {'fields': ('matric_number', 'department', 'year')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CourseClass)
admin.site.register(ClassMembership)