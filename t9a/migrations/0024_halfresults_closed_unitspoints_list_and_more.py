# Generated by Django 4.1.3 on 2023-01-19 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0023_rename_special_points_unitspoints_points_special_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='halfresults',
            name='closed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='unitspoints',
            name='list',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='t9a.lists'),
        ),
        migrations.AddField(
            model_name='unitspoints',
            name='result',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='t9a.results'),
        ),
    ]
