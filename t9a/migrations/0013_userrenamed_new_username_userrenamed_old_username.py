# Generated by Django 4.1.3 on 2023-01-04 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0012_userrenamed'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrenamed',
            name='new_username',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='userrenamed',
            name='old_username',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
