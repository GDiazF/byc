# Generated manually
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ope_calendario', '0002_faena_fecha_fin_faena_fecha_inicio_and_more'),
    ]

    operations = [
        # Paso 1: Eliminar el constraint anterior que permitía nulls
        migrations.RemoveConstraint(
            model_name='faena',
            name='faena_rango_valido',
        ),
        
        # Paso 2: Hacer fecha_inicio NOT NULL
        migrations.AlterField(
            model_name='faena',
            name='fecha_inicio',
            field=models.DateField(default=timezone.now().date(), verbose_name='Fecha de Inicio'),
            preserve_default=False,
        ),
        
        # Paso 3: Hacer fecha_fin NOT NULL
        migrations.AlterField(
            model_name='faena',
            name='fecha_fin',
            field=models.DateField(default=timezone.now().date(), verbose_name='Fecha de Fin'),
            preserve_default=False,
        ),
        
        # Paso 4: Agregar el nuevo constraint sin opciones de NULL
        migrations.AddConstraint(
            model_name='faena',
            constraint=models.CheckConstraint(
                check=models.Q(('fecha_fin__gte', models.F('fecha_inicio'))),
                name='faena_rango_valido'
            ),
        ),
    ]

