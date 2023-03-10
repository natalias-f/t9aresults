# Generated by Django 4.1.3 on 2023-01-09 09:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0016_games_save_date_lists_data_save_results_data_save'),
    ]

    operations = [
        migrations.AlterField(
            model_name='games',
            name='save_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='lists',
            name='data_save',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='results',
            name='data_save',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
