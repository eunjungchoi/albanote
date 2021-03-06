# Generated by Django 3.0.2 on 2020-02-03 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('albalog', '0014_auto_20200203_0823'),
    ]

    operations = [
        migrations.CreateModel(
            name='HolidayPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(blank=True, choices=[(0, '공휴일'), (1, '창립기념일'), (2, '병가'), (3, '경조사'), (4, '기타')], max_length=10, verbose_name='사유')),
                ('paid', models.BooleanField(default=False, verbose_name='유급 여부')),
                ('memo', models.TextField(blank=True, max_length=50, verbose_name='비고')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='albalog.Business')),
            ],
        ),
    ]
