# Generated by Django 4.1.3 on 2022-12-21 13:59

from django.db import migrations


def init_deployments(apps, schema_editor):
    deployment = apps.get_model('t9a', 'Deployments')
    if not deployment.objects.all():
        for d in ['Frontline Clash', 'Dawn Assault', 'Countherthrust', 'Encircle', 'Refused Flank', 'Marching Columns']:
            dep = deployment.objects.create(name=d)
            dep.save()


class Migration(migrations.Migration):
    dependencies = [
        ('t9a', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(init_deployments)
    ]