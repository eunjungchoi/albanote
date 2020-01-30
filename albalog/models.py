from datetime import datetime
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
        ('member', '일반직원')
    ]
    Statuses = [
        ('active', '재직중'),
        ('inactive', '퇴사')
    ]
    type = models.CharField(choices=Types, max_length=10, default='member')
    business = models.ForeignKey(Business, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    hourly_wage = models.IntegerField(blank=True)
    status = models.CharField(choices=Statuses, max_length=10, default='active')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business.license_name + '_' + self.user.name


class TimeTable(models.Model):
    DAYS_OF_WEEK = (
        ('1', '월'),
        ('2', '화'),
        ('3', '수'),
        ('4', '목'),
        ('5', '금'),
        ('6', '토'),
        ('7', '일'),
    )
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    day = models.CharField(choices=DAYS_OF_WEEK, max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()


class Work(models.Model):
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


@receiver(pre_save, sender=Work)
def calculate_hours_worked(sender, instance, **kwargs):
    start = datetime.strptime(instance.start_time, '%Y-%m-%dT%H:%M')
    end = datetime.strptime(instance.end_time, '%Y-%m-%dT%H:%M')
    instance.duration = end - start
