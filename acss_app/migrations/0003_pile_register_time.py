# Generated by Django 4.0.4 on 2022-06-10 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acss_app', '0002_pile_pile_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='pile',
            name='register_time',
            field=models.DateField(default='2022-01-01'),
            preserve_default=False,
        ),
    ]
