# Generated by Django 5.0.6 on 2025-04-29 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gen_settings', '0004_alter_empresa_telefono'),
    ]

    operations = [
        migrations.AlterField(
            model_name='empresa',
            name='telefono',
            field=models.CharField(max_length=12),
        ),
    ]
