# Generated by Django 4.1.3 on 2023-01-09 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0015_alter_gaminggroup_members'),
    ]

    operations = [
        migrations.AddField(
            model_name='games',
            name='save_date',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='lists',
            name='data_save',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='results',
            name='data_save',
            field=models.DateField(auto_now_add=True, null=True),
        ),
    ]
