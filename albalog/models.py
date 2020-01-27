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


class Member(models.Model):
    Types = [
        ('manager', '관리자'),
        ('member', '일반직원')
    ]
    type = models.CharField(choices=Types, max_length=10)
    business = models.ForeignKey(Business, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business.license_name + '_' + self.user.name


class Work(models.Model):
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    hourly_wage = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField(blank=True, null=True)


@receiver(pre_save, sender=Work)
def calculate_hours_worked(sender, instance, **kwargs):
    instance.duration = instance.end_time - instance.start_time
