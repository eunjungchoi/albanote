from django.contrib import admin

# Register your models here.
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from albalog.models import User, Business, Member, Work


class CustomeUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'sex')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'username', 'name', 'phone', 'sex')


class BusinessAdmin(ModelAdmin):
    list_display = ('id', 'license_name', 'license_number', 'address')


class MemberAdmin(ModelAdmin):
    list_display = ('id', 'business_name', 'user', 'member_name', 'type', 'hourly_wage')

    def business_name(self, obj):
        return obj.business.license_name

    def member_name(self, obj):
        return obj.user.name


class WorkAdmin(ModelAdmin):
    list_display = ('id', 'member', 'start_time', 'end_time', 'duration')

admin.site.register(User, CustomeUserAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Work, WorkAdmin)
