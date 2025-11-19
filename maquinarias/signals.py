"""
Señales Django para capturar cambios automáticamente y registrar en historial de Equipos.
"""
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Equipo, HistorialEquipo, EstadoManualEquipo, DocumentoMaquinaria, HistorialDocumentoMaquinaria
from ope_calendario.models import AsignacionEquipoFaena


@receiver(post_save, sender=Equipo)
def registrar_cambio_equipo(sender, instance, created, **kwargs):
    """
    Registra en el historial cuando se crea o modifica un Equipo.
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # Equipo creado
        HistorialEquipo.registrar(
            equipo=instance,
            accion='EQUIPO_CREADO',
            descripcion=f"Equipo creado: {instance.nombreEquipo} (Código: {instance.codigoInterno})",
            usuario=usuario,
            datos_nuevos={
                'equipo_id': instance.equipo_id,
                'nombreEquipo': instance.nombreEquipo,
                'codigoInterno': instance.codigoInterno,
                'patente': instance.patente,
                'activo': instance.activo,
            }
        )
    else:
        # Equipo modificado - verificar cambios importantes
        if hasattr(instance, '_previous_state'):
            previo = instance._previous_state
            
            # Verificar cambio de estado activo/inactivo
            if previo.get('activo') != instance.activo:
                if instance.activo:
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_ACTIVADO',
                        descripcion=f"Equipo activado: {instance.nombreEquipo}",
                        usuario=usuario,
                        datos_previos={'activo': False},
                        datos_nuevos={'activo': True}
                    )
                else:
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_DESACTIVADO',
                        descripcion=f"Equipo desactivado: {instance.nombreEquipo}",
                        usuario=usuario,
                        datos_previos={'activo': True},
                        datos_nuevos={'activo': False}
                    )
            else:
                # Otros cambios
                campos_cambiados = []
                campos_importantes = ['nombreEquipo', 'codigoInterno', 'patente', 'horometro', 'odometro', 'horometroSuperEstructural']
                for campo in campos_importantes:
                    if previo.get(campo) != getattr(instance, campo, None):
                        campos_cambiados.append(campo)
                
                if campos_cambiados:
                    datos_previos = {campo: previo.get(campo) for campo in campos_cambiados}
                    datos_nuevos = {campo: getattr(instance, campo) for campo in campos_cambiados}
                    
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_MODIFICADO',
                        descripcion=f"Equipo modificado: {', '.join(campos_cambiados)}",
                        usuario=usuario,
                        datos_previos=datos_previos,
                        datos_nuevos=datos_nuevos
                    )


@receiver(pre_save, sender=Equipo)
def guardar_estado_previo_equipo(sender, instance, **kwargs):
    """
    Guarda el estado previo del Equipo antes de guardar para comparar cambios.
    """
    if instance.pk:  # Solo si ya existe (no es creación)
        try:
            equipo_anterior = Equipo.objects.get(pk=instance.pk)
            instance._previous_state = {
                'activo': equipo_anterior.activo,
                'nombreEquipo': equipo_anterior.nombreEquipo,
                'codigoInterno': equipo_anterior.codigoInterno,
                'patente': equipo_anterior.patente,
                'horometro': equipo_anterior.horometro,
                'odometro': equipo_anterior.odometro,
                'horometroSuperEstructural': equipo_anterior.horometroSuperEstructural,
            }
        except Equipo.DoesNotExist:
            instance._previous_state = {}


@receiver(pre_delete, sender=Equipo)
def registrar_eliminacion_equipo(sender, instance, **kwargs):
    """
    Registra en el historial cuando se elimina un Equipo.
    """
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialEquipo.registrar(
        equipo=instance,
        accion='EQUIPO_ELIMINADO',
        descripcion=f"Equipo eliminado: {instance.nombreEquipo} (Código: {instance.codigoInterno})",
        usuario=usuario,
        datos_previos={
            'equipo_id': instance.equipo_id,
            'nombreEquipo': instance.nombreEquipo,
            'codigoInterno': instance.codigoInterno,
            'patente': instance.patente,
        }
    )


# Señales para estados manuales de equipos
@receiver(post_save, sender=EstadoManualEquipo)
def registrar_estado_manual_equipo(sender, instance, created, **kwargs):
    """Registra cuando se asigna o modifica un estado manual a un equipo."""
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        HistorialEquipo.registrar(
            equipo=instance.equipo,
            accion='ESTADO_MANUAL_ASIGNADO',
            descripcion=f"Estado manual '{instance.estado.nombre}' asignado al equipo desde {instance.fecha_inicio} hasta {instance.fecha_fin}",
            usuario=usuario,
            datos_nuevos={
                'estado_id': instance.estado.id,
                'estado_nombre': instance.estado.nombre,
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
            }
        )
    else:
        HistorialEquipo.registrar(
            equipo=instance.equipo,
            accion='ESTADO_MANUAL_MODIFICADO',
            descripcion=f"Estado manual modificado",
            usuario=usuario,
        )


@receiver(pre_delete, sender=EstadoManualEquipo)
def registrar_eliminacion_estado_manual_equipo(sender, instance, **kwargs):
    """Registra cuando se elimina un estado manual de un equipo."""
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialEquipo.registrar(
        equipo=instance.equipo,
        accion='ESTADO_MANUAL_ELIMINADO',
        descripcion=f"Estado manual '{instance.estado.nombre}' eliminado del equipo",
        usuario=usuario,
        datos_previos={
            'estado_id': instance.estado.id,
            'estado_nombre': instance.estado.nombre,
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
        }
    )


# Señales para asignaciones de equipos a faenas
@receiver(post_save, sender=AsignacionEquipoFaena)
def registrar_asignacion_equipo_faena(sender, instance, created, **kwargs):
    """Registra cuando se asigna o modifica un equipo a una faena."""
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        HistorialEquipo.registrar(
            equipo=instance.equipo,
            accion='ASIGNACION_FAENA_CREADA',
            descripcion=f"Equipo asignado a faena '{instance.faena.nombre}' desde {instance.fecha_inicio} hasta {instance.fecha_fin or 'sin fecha fin'}",
            usuario=usuario,
            datos_nuevos={
                'faena_id': instance.faena.id,
                'faena_nombre': instance.faena.nombre,
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
            }
        )
    else:
        HistorialEquipo.registrar(
            equipo=instance.equipo,
            accion='ASIGNACION_FAENA_MODIFICADA',
            descripcion=f"Asignación a faena '{instance.faena.nombre}' modificada",
            usuario=usuario,
        )


@receiver(pre_delete, sender=AsignacionEquipoFaena)
def registrar_eliminacion_asignacion_equipo_faena(sender, instance, **kwargs):
    """Registra cuando se elimina una asignación de equipo a faena."""
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialEquipo.registrar(
        equipo=instance.equipo,
        accion='ASIGNACION_FAENA_ELIMINADA',
        descripcion=f"Asignación a faena '{instance.faena.nombre}' eliminada",
        usuario=usuario,
        datos_previos={
            'faena_id': instance.faena.id,
            'faena_nombre': instance.faena.nombre,
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
        }
    )

