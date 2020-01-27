from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    Types = [
        ('male', '남'),
        ('female', '여')
    ]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    sex = models.CharField(choices=Types, max_length=10)
