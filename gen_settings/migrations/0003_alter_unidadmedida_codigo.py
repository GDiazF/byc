# Generated by Django 5.2 on 2025-04-29 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gen_settings', '0002_alter_comuna_options_alter_region_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unidadmedida',
            name='codigo',
            field=models.CharField(max_length=3, unique=True),
        ),
    ]
