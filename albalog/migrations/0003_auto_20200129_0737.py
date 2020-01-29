# Generated by Django 2.1.1 on 2020-01-29 07:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('albalog', '0002_business_member_work'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='work',
            name='hourly_wage',
        ),
        migrations.AddField(
            model_name='member',
            name='hourly_wage',
            field=models.IntegerField(blank=True, default=9000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='work',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='work',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
