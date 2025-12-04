"""
Management command para poblar los tipos de notificaciones iniciales.
"""

from django.core.management.base import BaseCommand
from notificaciones.models import TipoNotificacion


class Command(BaseCommand):
    help = 'Pobla la base de datos con los tipos de notificaciones iniciales'

    def handle(self, *args, **options):
        tipos_notificaciones = [
            # RRHH
            {
                'codigo': 'RRHH_PERSONAL_ACTIVADO',
                'nombre': 'Personal Activado',
                'descripcion': 'Se genera cuando se activa un personal',
                'categoria': 'RRHH',
                'prioridad': 'MEDIA',
                'template_titulo': 'Personal activado: {nombre}',
                'template_mensaje': 'Se ha activado el personal {nombre} {apellido} (RUT: {rut}).'
            },
            {
                'codigo': 'RRHH_PERSONAL_DESACTIVADO',
                'nombre': 'Personal Desactivado',
                'descripcion': 'Se genera cuando se desactiva un personal',
                'categoria': 'RRHH',
                'prioridad': 'MEDIA',
                'template_titulo': 'Personal desactivado: {nombre}',
                'template_mensaje': 'Se ha desactivado el personal {nombre} {apellido} (RUT: {rut}).'
            },
            {
                'codigo': 'RRHH_LICENCIA_MEDICA_CREADA',
                'nombre': 'Licencia Médica Creada',
                'descripcion': 'Se genera cuando se crea una licencia médica',
                'categoria': 'RRHH',
                'prioridad': 'ALTA',
                'template_titulo': 'Licencia médica creada: {nombre}',
                'template_mensaje': 'Se ha creado una licencia médica para {nombre} {apellido}. Período: {fecha_inicio} a {fecha_fin}.'
            },
            {
                'codigo': 'RRHH_AUSENTISMO_CREADO',
                'nombre': 'Ausentismo Creado',
                'descripcion': 'Se genera cuando se crea un ausentismo',
                'categoria': 'RRHH',
                'prioridad': 'ALTA',
                'template_titulo': 'Ausentismo creado: {nombre}',
                'template_mensaje': 'Se ha creado un ausentismo de tipo "{tipo}" para {nombre} {apellido}. Período: {fecha_desde} a {fecha_hasta}.'
            },
            {
                'codigo': 'RRHH_DOCUMENTO_VENCIMIENTO_45D',
                'nombre': 'Documento Vence en 45 Días',
                'descripcion': 'Se genera cuando un documento vence en 45 días',
                'categoria': 'RRHH',
                'prioridad': 'BAJA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" de {nombre} vence en 45 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'RRHH_DOCUMENTO_VENCIMIENTO_30D',
                'nombre': 'Documento Vence en 30 Días',
                'descripcion': 'Se genera cuando un documento vence en 30 días',
                'categoria': 'RRHH',
                'prioridad': 'MEDIA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" de {nombre} vence en 30 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'RRHH_DOCUMENTO_VENCIMIENTO_15D',
                'nombre': 'Documento Vence en 15 Días',
                'descripcion': 'Se genera cuando un documento vence en 15 días',
                'categoria': 'RRHH',
                'prioridad': 'ALTA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" de {nombre} vence en 15 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'RRHH_DOCUMENTO_VENCIMIENTO_5D',
                'nombre': 'Documento Vence en 5 Días',
                'descripcion': 'Se genera cuando un documento vence en 5 días',
                'categoria': 'RRHH',
                'prioridad': 'ALTA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" de {nombre} vence en 5 días ({fecha_vencimiento}).'
            },
            
            # MAQUINARIAS
            {
                'codigo': 'MAQUINARIAS_EQUIPO_ACTIVADO',
                'nombre': 'Equipo Activado',
                'descripcion': 'Se genera cuando se activa un equipo',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Equipo activado: {nombre}',
                'template_mensaje': 'Se ha activado el equipo {nombre} (Código: {codigo}).'
            },
            {
                'codigo': 'MAQUINARIAS_EQUIPO_DESACTIVADO',
                'nombre': 'Equipo Desactivado',
                'descripcion': 'Se genera cuando se desactiva un equipo',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Equipo desactivado: {nombre}',
                'template_mensaje': 'Se ha desactivado el equipo {nombre} (Código: {codigo}).'
            },
            {
                'codigo': 'MAQUINARIAS_OT_CREADA',
                'nombre': 'Orden de Trabajo Creada',
                'descripcion': 'Se genera cuando se crea una orden de trabajo',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Orden de Trabajo creada: OT-{folio}',
                'template_mensaje': 'Se ha creado la Orden de Trabajo OT-{folio} para el equipo {equipo}.'
            },
            {
                'codigo': 'MAQUINARIAS_OT_ESTADO_CAMBIADO',
                'nombre': 'Estado de OT Cambiado',
                'descripcion': 'Se genera cuando cambia el estado de una OT',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Estado de OT cambiado: OT-{folio}',
                'template_mensaje': 'La Orden de Trabajo OT-{folio} ha cambiado de estado a "{estado}".'
            },
            {
                'codigo': 'MAQUINARIAS_EQUIPO_DISPONIBLE',
                'nombre': 'Equipo Disponible',
                'descripcion': 'Se genera cuando un equipo cambia a estado disponible',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Equipo disponible: {nombre}',
                'template_mensaje': 'El equipo {nombre} ha cambiado a estado disponible (OT-{folio}).'
            },
            {
                'codigo': 'MAQUINARIAS_EQUIPO_ASIGNADO_FAENA',
                'nombre': 'Equipo Asignado a Faena',
                'descripcion': 'Se genera cuando se asigna un equipo a una faena',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Equipo asignado a faena: {nombre}',
                'template_mensaje': 'El equipo {nombre} (Código: {codigo}) ha sido asignado a la faena {faena} desde {fecha_inicio}.'
            },
            {
                'codigo': 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_45D',
                'nombre': 'Documento de Equipo Vence en 45 Días',
                'descripcion': 'Se genera cuando un documento de equipo vence en 45 días',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'BAJA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" del equipo {equipo} vence en 45 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_30D',
                'nombre': 'Documento de Equipo Vence en 30 Días',
                'descripcion': 'Se genera cuando un documento de equipo vence en 30 días',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'MEDIA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" del equipo {equipo} vence en 30 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_15D',
                'nombre': 'Documento de Equipo Vence en 15 Días',
                'descripcion': 'Se genera cuando un documento de equipo vence en 15 días',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'ALTA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" del equipo {equipo} vence en 15 días ({fecha_vencimiento}).'
            },
            {
                'codigo': 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_5D',
                'nombre': 'Documento de Equipo Vence en 5 Días',
                'descripcion': 'Se genera cuando un documento de equipo vence en 5 días',
                'categoria': 'MAQUINARIAS',
                'prioridad': 'ALTA',
                'template_titulo': 'Vencimiento próximo: {tipo_documento}',
                'template_mensaje': 'El documento "{tipo_documento}" del equipo {equipo} vence en 5 días ({fecha_vencimiento}).'
            },
            
            # PLANIFICACIÓN
            {
                'codigo': 'PLANIFICACION_FAENA_CREADA',
                'nombre': 'Faena Creada',
                'descripcion': 'Se genera cuando se crea una faena',
                'categoria': 'PLANIFICACION',
                'prioridad': 'MEDIA',
                'template_titulo': 'Faena creada: {nombre}',
                'template_mensaje': 'Se ha creado la faena {nombre} (Código: {codigo}). Período: {fecha_inicio} a {fecha_fin}.'
            },
            {
                'codigo': 'PLANIFICACION_FAENA_EDITADA',
                'nombre': 'Faena Editada',
                'descripcion': 'Se genera cuando se edita una faena',
                'categoria': 'PLANIFICACION',
                'prioridad': 'BAJA',
                'template_titulo': 'Faena editada: {nombre}',
                'template_mensaje': 'Se han modificado las fechas de la faena {nombre} (Código: {codigo}). Nuevo período: {fecha_inicio} a {fecha_fin}.'
            },
            {
                'codigo': 'PLANIFICACION_PERSONAL_ASIGNADO_FAENA',
                'nombre': 'Personal Asignado a Faena',
                'descripcion': 'Se genera cuando se asigna personal a una faena',
                'categoria': 'PLANIFICACION',
                'prioridad': 'MEDIA',
                'template_titulo': 'Personal asignado a faena: {nombre}',
                'template_mensaje': '{nombre} {apellido} (RUT: {rut}) ha sido asignado a la faena {faena} con turno {turno} desde {fecha_inicio}.'
            },
            {
                'codigo': 'PLANIFICACION_EQUIPO_ASIGNADO_FAENA',
                'nombre': 'Equipo Asignado a Faena',
                'descripcion': 'Se genera cuando se asigna un equipo a una faena',
                'categoria': 'PLANIFICACION',
                'prioridad': 'MEDIA',
                'template_titulo': 'Equipo asignado a faena: {nombre}',
                'template_mensaje': 'El equipo {nombre} (Código: {codigo}) ha sido asignado a la faena {faena} desde {fecha_inicio}.'
            },
            
            # GENERAL
            {
                'codigo': 'GENERAL_CAMBIO_PASSWORD',
                'nombre': 'Cambio de Contraseña',
                'descripcion': 'Se genera cuando un usuario cambia su contraseña',
                'categoria': 'GENERAL',
                'prioridad': 'MEDIA',
                'template_titulo': 'Contraseña cambiada',
                'template_mensaje': 'Tu contraseña ha sido cambiada el {fecha}. Si no fuiste tú, contacta al administrador.'
            },
            {
                'codigo': 'GENERAL_LOGIN_FALLIDO',
                'nombre': 'Intento de Login Fallido',
                'descripcion': 'Se genera cuando hay un intento de login fallido',
                'categoria': 'GENERAL',
                'prioridad': 'ALTA',
                'template_titulo': 'Intento de login fallido',
                'template_mensaje': 'Se detectó un intento de login fallido para la cuenta {usuario} el {fecha}.'
            },
        ]
        
        creados = 0
        actualizados = 0
        
        for tipo_data in tipos_notificaciones:
            tipo, created = TipoNotificacion.objects.update_or_create(
                codigo=tipo_data['codigo'],
                defaults={
                    'nombre': tipo_data['nombre'],
                    'descripcion': tipo_data['descripcion'],
                    'categoria': tipo_data['categoria'],
                    'prioridad': tipo_data['prioridad'],
                    'template_titulo': tipo_data.get('template_titulo', ''),
                    'template_mensaje': tipo_data.get('template_mensaje', ''),
                    'activo': True
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {tipo.codigo}')
                )
            else:
                actualizados += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Actualizado: {tipo.codigo}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado: {creados} creados, {actualizados} actualizados'
            )
        )

