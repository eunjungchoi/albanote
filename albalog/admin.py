from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin

from albalog.models import User


class CustomeUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'sex')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'username', 'name', 'phone', 'sex')


admin.site.register(User, CustomeUserAdmin)
