# Generated by Django 4.1.3 on 2023-01-13 15:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('t9a', '0017_alter_games_save_date_alter_lists_data_save_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ListsUnits',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RenameField(
            model_name='results',
            old_name='data_save',
            new_name='save_date',
        ),
        migrations.RemoveField(
            model_name='lists',
            name='data_save',
        ),
        migrations.AddField(
            model_name='lists',
            name='save_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='Units',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0)),
                ('special', models.IntegerField(default=0)),
                ('unit', models.CharField(max_length=256)),
                ('save_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('army', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='t9a.army')),
                ('list', models.ManyToManyField(through='t9a.ListsUnits', to='t9a.lists')),
            ],
        ),
        migrations.AddField(
            model_name='listsunits',
            name='list',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='t9a.lists'),
        ),
        migrations.AddField(
            model_name='listsunits',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='listsunits',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='t9a.units'),
        ),
    ]