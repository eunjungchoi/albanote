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
    type = models.CharField(choices=Types, max_length=10, default='member')
    business = models.ForeignKey(Business, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    hourly_wage = models.IntegerField(blank=True)
    status = models.CharField(choices=Statuses, max_length=10, default='active')
    resignation_date = models.DateField(null=True, blank=True)
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
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    day = models.CharField(choices=DAYS_OF_WEEK, max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()


class Attendance(models.Model):
    Absence_choices = [
        (0, '법정휴일'),
        (1, '약정휴일'),
        (2, '연차'),
        (3, '무단결근'),
    ]
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField(blank=True, null=True)
    date = models.DateField('날짜', null=True, blank=True)
    timetable = models.ForeignKey(TimeTable, null=True, on_delete=models.DO_NOTHING)
    late_come = models.DurationField(blank=True, null=True)
    early_leave = models.DurationField(blank=True, null=True)
    absence = models.BooleanField('부재', default=False)
    reason = models.CharField('사유', choices=Absence_choices, max_length=2, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


@receiver(pre_save, sender=Attendance)
def calculate_duration_and_late_come(sender, instance, **kwargs):
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

        if diff1_minutes and diff2_minutes:
            # 출근
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
    total_monthly_salary = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
