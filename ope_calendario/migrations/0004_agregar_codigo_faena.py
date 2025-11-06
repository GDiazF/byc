# Generated manually
from django.db import migrations, models
import re


def generar_codigo_desde_nombre(nombre):
    """Genera un código a partir del nombre de la faena"""
    # Tomar las primeras palabras y crear un acrónimo
    palabras = re.findall(r'\b[A-Za-z]+', nombre.upper())
    if len(palabras) >= 2:
        codigo = ''.join(p[0] for p in palabras[:3])
    elif palabras:
        codigo = palabras[0][:3]
    else:
        codigo = 'FAE'
    return codigo


def asignar_codigos_existentes(apps, schema_editor):
    """Asignar códigos únicos a las faenas existentes"""
    Faena = apps.get_model('ope_calendario', 'Faena')
    codigos_usados = set()
    
    for idx, faena in enumerate(Faena.objects.all().order_by('id'), start=1):
        # Intentar generar código desde el nombre
        codigo_base = generar_codigo_desde_nombre(faena.nombre)
        codigo = codigo_base
        
        # Asegurar unicidad
        contador = 1
        while codigo in codigos_usados:
            codigo = f"{codigo_base}{contador:02d}"
            contador += 1
        
        # Si el código es muy corto o genérico, usar formato FAE-XXX
        if len(codigo) < 3:
            codigo = f"FAE{idx:03d}"
            while codigo in codigos_usados:
                idx += 1
                codigo = f"FAE{idx:03d}"
        
        faena.codigo = codigo
        faena.save()
        codigos_usados.add(codigo)


class Migration(migrations.Migration):

    dependencies = [
        ('ope_calendario', '0003_hacer_fechas_obligatorias'),
    ]

    operations = [
        # Paso 1: Agregar campo codigo como nullable
        migrations.AddField(
            model_name='faena',
            name='codigo',
            field=models.CharField(
                max_length=50, 
                null=True, 
                blank=True,
                verbose_name='Código/Identificador',
                help_text='Código único identificador de la faena'
            ),
        ),
        
        # Paso 2: Asignar códigos a faenas existentes
        migrations.RunPython(asignar_codigos_existentes, migrations.RunPython.noop),
        
        # Paso 3: Hacer el campo único y no nullable
        migrations.AlterField(
            model_name='faena',
            name='codigo',
            field=models.CharField(
                max_length=50,
                unique=True,
                verbose_name='Código/Identificador',
                help_text='Código único identificador de la faena'
            ),
        ),
        
        # Paso 4: Remover unique constraint del nombre (ya no es necesario)
        migrations.AlterField(
            model_name='faena',
            name='nombre',
            field=models.CharField(max_length=150),
        ),
    ]

