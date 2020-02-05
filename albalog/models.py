from datetime import datetime, date
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from django.db.models.signals import pre_save
from django.dispatch import receiver


class User(AbstractUser):
    Types = [
        ('male', '남'),
        ('female', '여')
    ]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    sex = models.CharField(choices=Types, max_length=10)


class Business(models.Model):
    license_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=20)
    address = models.CharField(max_length=200)

    def __str__(self):
        return self.license_name


class Member(models.Model):
    Types = [
        ('manager', '관리자'),
        ('member', '일반직원'),
    ]
    Statuses = [
        ('active', '재직중'),
        ('inactive', '퇴사'),
    ]
    Days = (
        ('0', '월'),
        ('1', '화'),
        ('2', '수'),
        ('3', '목'),
        ('4', '금'),
        ('5', '토'),
        ('6', '일')
    )
    type = models.CharField('권한', choices=Types, max_length=10, default='member')
    business = models.ForeignKey(Business, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    hourly_wage = models.IntegerField('시급', null=True, blank=True)
    status = models.CharField('상태', choices=Statuses, max_length=10, default='active')
    annual_leave = models.IntegerField('연차', blank=True, default=0)
    weekly_holiday = models.CharField('주휴일', choices=Days, max_length=1,  blank=True, default=6)
    start_date = models.DateField('입사일', blank=True)
    resignation_date = models.DateField('퇴사일', null=True, blank=True)
    national_pension = models.BooleanField(default=False)
    health_insurance = models.BooleanField(default=False)
    employment_insurance = models.BooleanField(default=False)
    industrial_accident_comp_insurance = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business.license_name + '_' + self.user.name


class TimeTable(models.Model):
    DAYS_OF_WEEK = (
        ('0', '월'),
        ('1', '화'),
        ('2', '수'),
        ('3', '목'),
        ('4', '금'),
        ('5', '토'),
        ('6', '일')
    )
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    day = models.CharField(choices=DAYS_OF_WEEK, max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.member.business.license_name + '_' + self.day + '_' + self.member.user.name


class HolidayPolicy(models.Model):
    Choices = [
        (0, '공휴일'),
        (1, '창립기념일'),
        (2, '병가'),
        (3, '경조사'),
        (4, '기타')
    ]
    business = models.ForeignKey(Business, on_delete=models.DO_NOTHING)
    type = models.CharField('종류', choices=Choices, max_length=10)
    paid = models.BooleanField('유급 여부', default=False)
    memo = models.TextField('비고', max_length=50, null=True, blank=True)


class Attendance(models.Model):
    Absence_choices = [
        (0, '법정휴일'),
        (1, '약정휴일'),
        (2, '연차'),
        (3, '무단결근'),
    ]
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    start_time = models.DateTimeField('출근일시', null=True, blank=True)
    end_time = models.DateTimeField('퇴근일시', null=True, blank=True)
    duration = models.DurationField('근무시간', blank=True, null=True)
    date = models.DateField('날짜', null=True, blank=True)
    timetable = models.ForeignKey(TimeTable, null=True, on_delete=models.DO_NOTHING)
    late_come = models.DurationField('지각', blank=True, null=True)
    early_leave = models.DurationField('조퇴', blank=True, null=True)
    absence = models.BooleanField('부재', default=False)
    reason = models.CharField('사유', choices=Absence_choices, max_length=2, null=True, blank=True)
    reason_detail = models.ForeignKey(HolidayPolicy, null=True, blank=True, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


@receiver(pre_save, sender=Attendance)
def calculate_duration_and_detect_timetable(sender, instance, **kwargs):
    from datetime import date
    if instance.absence:
        date = datetime.strptime(instance.date, '%Y-%m-%d')
        timetable = TimeTable.objects.get(member=instance.member, day=date.weekday())
        instance.timetable = timetable

        if instance.reason == 2:
            instance.member.annual_leave -= 1
            instance.member.save()
        return

    work_start = datetime.strptime(instance.start_time, '%Y-%m-%dT%H:%M')
    work_end = datetime.strptime(instance.end_time, '%Y-%m-%dT%H:%M')
    instance.duration = work_end - work_start

    day = work_start.weekday()
    timetables = TimeTable.objects.filter(member=instance.member, day=day)

    for timetable in timetables:
        # 출근 기준: 해당 근무내역의 시작시간이 시간표의 종료시간보다 작아야 한다 AND 근무내역 종료시간이 시간표의 시작시간보다 커야 한다.
        diff1 = datetime.combine(date.today(), timetable.end_time) - datetime.combine(date.today(), work_start.time())
        diff1_minutes = diff1.total_seconds() / 60

        diff2 = datetime.combine(date.today(), work_end.time()) - datetime.combine(date.today(), timetable.start_time)
        diff2_minutes = diff2.total_seconds() / 60

        if diff1_minutes > 0 and diff2_minutes > 0:
            instance.timetable = timetable

            # 지각: 근무내역 시작시간이 시간표 시작시간 보다 크면 (=늦으면)
            late_come = datetime.combine(date.today(), work_start.time()) - datetime.combine(date.today(), timetable.start_time)
            late_come_to_minutes = late_come.total_seconds() / 60
            if late_come_to_minutes > 0:
                instance.late_come = late_come

            # 조퇴: 근무내역 종료시간이 시간표 종료시간보다 작으면 (=이르면)
            leave_early = datetime.combine(date.today(), timetable.end_time) - datetime.combine(date.today(), work_end.time())
            leave_early_to_minutes = leave_early.total_seconds() / 60
            if leave_early_to_minutes > 0:
                instance.early_leave = leave_early

            break


class PayRoll(models.Model):
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    year = models.IntegerField()
    month = models.IntegerField()
    working_hours = models.IntegerField('월 근로시간')
    working_days = models.IntegerField('월 근로일수')
    base_salary = models.IntegerField('기본급')
    weekly_holiday_allowance = models.IntegerField('주휴수당', null=True, blank=True)
    gross_pay = models.IntegerField('지급액계')
    national_pension = models.IntegerField('국민연금', null=True, blank=True)
    health_insurance = models.IntegerField('건강보험', null=True, blank=True)
    long_term_care_insurance = models.IntegerField('장기요양보험', null=True, blank=True)
    employment_insurance = models.IntegerField('고용보험', null=True, blank=True)
    income_tax = models.IntegerField('소득세', null=True, blank=True)
    local_income_tax = models.IntegerField('지방소득세', null=True, blank=True)
    sum_of_deductions = models.IntegerField('공제액계')
    net_pay = models.IntegerField('차인지급액')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
