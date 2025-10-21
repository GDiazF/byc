# Generated manually to change from ManyToManyField to ForeignKey for LicenciaInternaPorPersonal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh_personal', '0014_add_tipos_licencia_interna'),
    ]

    operations = [
        # Primero eliminar el campo ManyToMany 'tipos'
        migrations.RemoveField(
            model_name='licenciainternaporpersonal',
            name='tipos',
        ),
        # Luego agregar el campo ForeignKey 'tipoLicenciaInterna_id'
        migrations.AddField(
            model_name='licenciainternaporpersonal',
            name='tipoLicenciaInterna_id',
            field=models.ForeignKey(
                db_column='tipoLicenciaInterna_id',
                on_delete=django.db.models.deletion.CASCADE,
                to='rrhh_personal.tipolicenciainterna',
                verbose_name='Tipo de Licencia Interna',
                # Usar el primer tipo como default temporal
                default=1
            ),
            preserve_default=False,
        ),
    ]

