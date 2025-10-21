# Generated manually to populate initial data for TipoLicenciaInterna

from django.db import migrations


def create_initial_tipos_licencia_interna(apps, schema_editor):
    """
    Crear tipos de licencia interna comunes para operación de maquinaria
    y vehículos en faenas mineras/industriales
    """
    TipoLicenciaInterna = apps.get_model('rrhh_personal', 'TipoLicenciaInterna')
    
    tipos = [
        {
            'tipoLicenciaInterna': 'OPERADOR CAMIÓN MINERO',
            'descripcion': 'Licencia para operación de camiones mineros (CAT 797, Komatsu 930E, etc.)'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR CARGADOR FRONTAL',
            'descripcion': 'Licencia para operación de cargadores frontales (CAT 992, 994, etc.)'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR PALA',
            'descripcion': 'Licencia para operación de palas mecánicas e hidráulicas'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR GRÚA HORQUILLA',
            'descripcion': 'Licencia para operación de grúas horquilla (forklifts)'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR GRÚA TELESCÓPICA',
            'descripcion': 'Licencia para operación de grúas telescópicas y plumas'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR RETROEXCAVADORA',
            'descripcion': 'Licencia para operación de retroexcavadoras'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR BULLDOZER',
            'descripcion': 'Licencia para operación de bulldozers y tractores'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR MOTONIVELADORA',
            'descripcion': 'Licencia para operación de motoniveladoras (grader)'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR RODILLO COMPACTADOR',
            'descripcion': 'Licencia para operación de rodillos compactadores'
        },
        {
            'tipoLicenciaInterna': 'CONDUCTOR CLASE A',
            'descripcion': 'Licencia interna clase A - Vehículos livianos'
        },
        {
            'tipoLicenciaInterna': 'CONDUCTOR CLASE B',
            'descripcion': 'Licencia interna clase B - Buses y minibuses'
        },
        {
            'tipoLicenciaInterna': 'CONDUCTOR CLASE C',
            'descripcion': 'Licencia interna clase C - Camiones'
        },
        {
            'tipoLicenciaInterna': 'CONDUCTOR CLASE D',
            'descripcion': 'Licencia interna clase D - Maquinaria especial'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR PERFORADORA',
            'descripcion': 'Licencia para operación de equipos de perforación'
        },
        {
            'tipoLicenciaInterna': 'OPERADOR JUMBOS',
            'descripcion': 'Licencia para operación de jumbos de perforación'
        },
    ]
    
    for tipo_data in tipos:
        TipoLicenciaInterna.objects.get_or_create(
            tipoLicenciaInterna=tipo_data['tipoLicenciaInterna'],
            defaults={'descripcion': tipo_data['descripcion']}
        )


def delete_tipos_licencia_interna(apps, schema_editor):
    """
    Eliminar los tipos de licencia interna creados (rollback)
    """
    TipoLicenciaInterna = apps.get_model('rrhh_personal', 'TipoLicenciaInterna')
    
    tipos_nombres = [
        'OPERADOR CAMIÓN MINERO',
        'OPERADOR CARGADOR FRONTAL',
        'OPERADOR PALA',
        'OPERADOR GRÚA HORQUILLA',
        'OPERADOR GRÚA TELESCÓPICA',
        'OPERADOR RETROEXCAVADORA',
        'OPERADOR BULLDOZER',
        'OPERADOR MOTONIVELADORA',
        'OPERADOR RODILLO COMPACTADOR',
        'CONDUCTOR CLASE A',
        'CONDUCTOR CLASE B',
        'CONDUCTOR CLASE C',
        'CONDUCTOR CLASE D',
        'OPERADOR PERFORADORA',
        'OPERADOR JUMBOS',
    ]
    
    TipoLicenciaInterna.objects.filter(
        tipoLicenciaInterna__in=tipos_nombres
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh_personal', '0013_personal_fecha_vencimiento_carnet'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_tipos_licencia_interna,
            delete_tipos_licencia_interna
        ),
    ]

