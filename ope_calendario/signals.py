"""
Señales Django para capturar cambios automáticamente y registrar en historial de Faenas.
Complementa el registro manual existente en las vistas.
"""
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Faena, AsignacionFaena, HistorialFaena, EstadoManual


@receiver(post_save, sender=Faena)
def registrar_cambio_faena(sender, instance, created, **kwargs):
    """
    Registra en el historial cuando se crea o modifica una Faena.
    Complementa el registro manual en las vistas.
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # Faena creada - solo registrar si no se registró manualmente
        # (las vistas pueden registrar manualmente con más detalles)
        if not hasattr(instance, '_historial_registrado'):
            HistorialFaena.registrar(
                faena=instance,
                accion='FAENA_CREADA',
                descripcion=f"Faena creada: {instance.nombre} (Código: {instance.codigo})",
                usuario=usuario,
                datos_nuevos={
                    'faena_id': instance.id,
                    'codigo': instance.codigo,
                    'nombre': instance.nombre,
                    'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                    'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
                }
            )
    else:
        # Faena modificada - solo registrar si no se registró manualmente
        if not hasattr(instance, '_historial_registrado') and hasattr(instance, '_previous_state'):
            previo = instance._previous_state
            
            # Verificar cambio de estado activo/inactivo
            if previo.get('activo') != instance.activo:
                if instance.activo:
                    HistorialFaena.registrar(
                        faena=instance,
                        accion='FAENA_MODIFICADA',
                        descripcion=f"Faena activada: {instance.nombre}",
                        usuario=usuario,
                        datos_previos={'activo': False},
                        datos_nuevos={'activo': True}
                    )
                else:
                    HistorialFaena.registrar(
                        faena=instance,
                        accion='FAENA_MODIFICADA',
                        descripcion=f"Faena desactivada: {instance.nombre}",
                        usuario=usuario,
                        datos_previos={'activo': True},
                        datos_nuevos={'activo': False}
                    )
            else:
                # Otros cambios
                campos_cambiados = []
                campos_importantes = ['codigo', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'ubicacion']
                for campo in campos_importantes:
                    if previo.get(campo) != getattr(instance, campo, None):
                        campos_cambiados.append(campo)
                
                if campos_cambiados:
                    datos_previos = {campo: previo.get(campo) for campo in campos_cambiados}
                    datos_nuevos = {campo: getattr(instance, campo) for campo in campos_cambiados}
                    
                    HistorialFaena.registrar(
                        faena=instance,
                        accion='FAENA_MODIFICADA',
                        descripcion=f"Faena modificada: {', '.join(campos_cambiados)}",
                        usuario=usuario,
                        datos_previos=datos_previos,
                        datos_nuevos=datos_nuevos
                    )


@receiver(pre_save, sender=Faena)
def guardar_estado_previo_faena(sender, instance, **kwargs):
    """
    Guarda el estado previo de la Faena antes de guardar para comparar cambios.
    """
    if instance.pk:  # Solo si ya existe (no es creación)
        try:
            faena_anterior = Faena.objects.get(pk=instance.pk)
            instance._previous_state = {
                'activo': faena_anterior.activo,
                'codigo': faena_anterior.codigo,
                'nombre': faena_anterior.nombre,
                'descripcion': faena_anterior.descripcion,
                'fecha_inicio': faena_anterior.fecha_inicio.isoformat() if faena_anterior.fecha_inicio else None,
                'fecha_fin': faena_anterior.fecha_fin.isoformat() if faena_anterior.fecha_fin else None,
                'ubicacion': faena_anterior.ubicacion,
            }
        except Faena.DoesNotExist:
            instance._previous_state = {}


@receiver(post_save, sender=AsignacionFaena)
def registrar_asignacion_faena(sender, instance, created, **kwargs):
    """
    Registra cuando se crea o modifica una asignación de personal a faena.
    Solo si no se registró manualmente en las vistas (para evitar duplicados).
    """
    if hasattr(instance, '_historial_registrado'):
        return  # Ya se registró manualmente
    
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        HistorialFaena.registrar(
            faena=instance.faena,
            accion='PERSONAL_ASIGNADO',
            descripcion=f"{instance.personal.nombre} {instance.personal.apepat} asignado con turno {instance.turno.nombre}",
            usuario=usuario,
            personal=instance.personal,
            datos_nuevos={
                'personal_id': instance.personal.personal_id,
                'personal_nombre': f"{instance.personal.nombre} {instance.personal.apepat} {instance.personal.apemat}",
                'turno': instance.turno.nombre,
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None
            }
        )
    else:
        HistorialFaena.registrar(
            faena=instance.faena,
            accion='ASIGNACION_MODIFICADA',
            descripcion=f"Asignación de {instance.personal.nombre} {instance.personal.apepat} modificada",
            usuario=usuario,
            personal=instance.personal,
        )


@receiver(pre_delete, sender=AsignacionFaena)
def registrar_eliminacion_asignacion_faena(sender, instance, **kwargs):
    """
    Registra cuando se elimina una asignación de personal a faena.
    Solo si no se registró manualmente en las vistas (para evitar duplicados).
    """
    if hasattr(instance, '_historial_registrado'):
        return  # Ya se registró manualmente
    
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialFaena.registrar(
        faena=instance.faena,
        accion='PERSONAL_ELIMINADO',
        descripcion=f"{instance.personal.nombre} {instance.personal.apepat} eliminado de la faena",
        usuario=usuario,
        personal=instance.personal,
        datos_previos={
            'personal_id': instance.personal.personal_id,
            'personal_nombre': f"{instance.personal.nombre} {instance.personal.apepat} {instance.personal.apemat}",
            'turno': instance.turno.nombre,
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None
        }
    )


@receiver(post_save, sender=EstadoManual)
def registrar_estado_manual(sender, instance, created, **kwargs):
    """
    Registra cuando se asigna o modifica un estado manual a personal.
    """
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        HistorialFaena.registrar(
            faena=instance.faena if instance.faena else None,
            accion='FAENA_MODIFICADA',  # Usar acción genérica ya que no hay específica para estados manuales
            descripcion=f"Estado manual '{instance.estado.nombre}' asignado a {instance.personal.nombre} {instance.personal.apepat}",
            usuario=usuario,
            personal=instance.personal,
            datos_nuevos={
                'estado_id': instance.estado.id,
                'estado_nombre': instance.estado.nombre,
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
            }
        )


@receiver(pre_delete, sender=EstadoManual)
def registrar_eliminacion_estado_manual(sender, instance, **kwargs):
    """
    Registra cuando se elimina un estado manual de personal.
    """
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialFaena.registrar(
        faena=instance.faena if instance.faena else None,
        accion='FAENA_MODIFICADA',
        descripcion=f"Estado manual '{instance.estado.nombre}' eliminado de {instance.personal.nombre} {instance.personal.apepat}",
        usuario=usuario,
        personal=instance.personal,
        datos_previos={
            'estado_id': instance.estado.id,
            'estado_nombre': instance.estado.nombre,
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
        }
    )

