# Generated by Django 4.1.3 on 2022-12-31 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0006_results_first_alter_results_result_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lists',
            options={'ordering': ['army', 'owner', 'name']},
        ),
        migrations.AlterField(
            model_name='results',
            name='first',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]