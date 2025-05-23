# Generated by Django 5.1.7 on 2025-05-10 06:47

import rrhh_personal.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh_personal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='personal',
            name='certificado_afp',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Certificado de Afiliación AFP'),
        ),
        migrations.AddField(
            model_name='personal',
            name='certificado_antecedentes',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Certificado de Antecedentes'),
        ),
        migrations.AddField(
            model_name='personal',
            name='certificado_estudios',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Certificado de Estudios'),
        ),
        migrations.AddField(
            model_name='personal',
            name='certificado_residencia',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Certificado de Residencia'),
        ),
        migrations.AddField(
            model_name='personal',
            name='certificado_salud',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Certificado de Afiliación de Salud'),
        ),
        migrations.AddField(
            model_name='personal',
            name='comprobante_banco',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Comprobante de Cuenta Bancaria'),
        ),
        migrations.AddField(
            model_name='personal',
            name='curriculum',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Curriculum Vitae'),
        ),
        migrations.AddField(
            model_name='personal',
            name='foto_carnet',
            field=models.ImageField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Foto tipo Carnet'),
        ),
        migrations.AddField(
            model_name='personal',
            name='fotocopia_carnet',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Fotocopia de Carnet'),
        ),
        migrations.AddField(
            model_name='personal',
            name='fotocopia_finiquito',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Fotocopia de Último Finiquito'),
        ),
        migrations.AddField(
            model_name='personal',
            name='hoja_vida_conductor',
            field=models.FileField(blank=True, null=True, upload_to=rrhh_personal.models.obtener_ruta_documento_personal, verbose_name='Hoja de Vida del Conductor'),
        ),
    ]
