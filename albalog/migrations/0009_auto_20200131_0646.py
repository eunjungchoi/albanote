# Generated by Django 3.0.2 on 2020-01-31 06:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('albalog', '0008_auto_20200130_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timetable',
            name='day',
            field=models.CharField(choices=[('0', '월'), ('1', '화'), ('2', '수'), ('3', '목'), ('4', '금'), ('5', '토'), ('6', '일')], max_length=10),
        ),
        migrations.CreateModel(
            name='PayRoll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(max_length=4)),
                ('month', models.IntegerField(max_length=2)),
                ('total_monthly_salary', models.IntegerField(max_length=20)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='albalog.Member')),
            ],
        ),
    ]
