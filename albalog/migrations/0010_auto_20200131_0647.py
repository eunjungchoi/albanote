# Generated by Django 3.0.2 on 2020-01-31 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('albalog', '0009_auto_20200131_0646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payroll',
            name='month',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='payroll',
            name='total_monthly_salary',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='payroll',
            name='year',
            field=models.IntegerField(),
        ),
    ]
