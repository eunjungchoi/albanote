# Generated by Django 3.0.2 on 2020-02-07 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('albalog', '0028_auto_20200207_1309'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='member',
            constraint=models.UniqueConstraint(fields=('business', 'user'), name='unique_business_user'),
        ),
    ]