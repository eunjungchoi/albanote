from django.contrib import admin

# Register your models here.
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from albalog.models import User, Business, Member, TimeTable, Attendance, HolidayPolicy, PayRoll


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
    list_display = ('id', 'business_name', 'user', 'member_name', 'type', 'hourly_wage', 'weekly_holiday', 'start_date', 'annual_leave')

    def business_name(self, obj):
        return obj.business.license_name

    def member_name(self, obj):
        return obj.user.name


class AttendanceAdmin(ModelAdmin):
    list_display = ('id', 'member', 'start_time', 'end_time', 'duration', 'date', 'absence', 'reason')


class TimeTableAdmin(ModelAdmin):
    list_display = ('id', 'member_name', 'day', 'start_time', 'end_time')

    def member_name(self, obj):
        return obj.member.business.license_name + '_' + obj.member.user.name


class HolidayPolicyAdmin(ModelAdmin):
    list_display = ('id', 'business_name', 'type_name', 'paid', 'memo')

    def business_name(self, obj):
        return obj.business.license_name

    def type_name(self, obj):
        return obj.type

class PayrollAdmin(ModelAdmin):
    list_display = ('id', 'member_name', 'year', 'month', 'working_hours', 'working_days', 'base_salary', 'weekly_holiday_allowance', 'gross_pay', 'net_pay', 'sum_of_deductions')

    def member_name(self, obj):
        return obj.member.business.license_name + '_' + obj.member.user.name


admin.site.register(User, CustomeUserAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(TimeTable, TimeTableAdmin)
admin.site.register(HolidayPolicy, HolidayPolicyAdmin)
admin.site.register(PayRoll, PayrollAdmin)
