"""
Signals para crear notificaciones automáticamente cuando ocurren eventos.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from .utils import crear_notificacion_por_tipo, crear_notificacion_para_usuario
from .sse_manager import sse_manager
from .utils import contar_notificaciones_no_leidas
from .models import Notificacion


# ============================================================================
# SIGNALS DE RRHH
# ============================================================================

# NOTA: Las señales de Personal (activado/desactivado/creado) están manejadas en rrhh_personal/signals.py
# para evitar duplicación de notificaciones. Esta señal fue deshabilitada.


@receiver(post_save, sender='rrhh_personal.LicenciaMedicaPorPersonal')
def notificar_licencia_medica(sender, instance, created, **kwargs):
    """
    Notifica cuando se crea una licencia médica.
    """
    if created:
        fecha_inicio = instance.fechaEmision.strftime('%d/%m/%Y') if instance.fechaEmision else 'N/A'
        fecha_fin = instance.fecha_fin_licencia.strftime('%d/%m/%Y') if instance.fecha_fin_licencia else 'N/A'
        
        crear_notificacion_por_tipo(
            codigo_tipo='RRHH_LICENCIA_MEDICA_CREADA',
            titulo=f'Licencia médica creada: {instance.personal_id.nombre} {instance.personal_id.apepat}',
            mensaje=(
                f"Se ha creado una licencia médica para {instance.personal_id.nombre} {instance.personal_id.apepat} "
                f"(RUT: {instance.personal_id.rut}-{instance.personal_id.dvrut}). "
                f"Período: {fecha_inicio} a {fecha_fin}."
            ),
            datos_adicionales={
                'personal_id': instance.personal_id.personal_id,
                'licencia_id': instance.licenciaMedicaPorPersonal_id,
                'fecha_inicio': instance.fechaEmision.isoformat() if instance.fechaEmision else None,
                'fecha_fin': instance.fecha_fin_licencia.isoformat() if instance.fecha_fin_licencia else None
            }
        )


@receiver(post_save, sender='rrhh_personal.Ausentismo')
def notificar_ausentismo(sender, instance, created, **kwargs):
    """
    Notifica cuando se crea un ausentismo.
    """
    if created:
        tipo_ausentismo = instance.tipoausen_id.tipo if instance.tipoausen_id else 'N/A'
        fecha_desde = instance.fechaini.strftime('%d/%m/%Y') if instance.fechaini else 'N/A'
        fecha_hasta = instance.fechafin.strftime('%d/%m/%Y') if instance.fechafin else 'N/A'
        
        crear_notificacion_por_tipo(
            codigo_tipo='RRHH_AUSENTISMO_CREADO',
            titulo=f'Ausentismo creado: {instance.personal_id.nombre} {instance.personal_id.apepat}',
            mensaje=(
                f"Se ha creado un ausentismo de tipo '{tipo_ausentismo}' para "
                f"{instance.personal_id.nombre} {instance.personal_id.apepat} "
                f"(RUT: {instance.personal_id.rut}-{instance.personal_id.dvrut}). "
                f"Período: {fecha_desde} a {fecha_hasta}."
            ),
            datos_adicionales={
                'personal_id': instance.personal_id.personal_id,
                'ausentismo_id': instance.ausentismo_id,
                'tipo_ausentismo': tipo_ausentismo,
                'fecha_desde': instance.fechaini.isoformat() if instance.fechaini else None,
                'fecha_hasta': instance.fechafin.isoformat() if instance.fechafin else None
            }
        )


# ============================================================================
# SIGNALS DE MAQUINARIAS
# ============================================================================

@receiver(post_save, sender='maquinarias.Equipo')
def notificar_cambio_estado_equipo(sender, instance, created, **kwargs):
    """
    Notifica cuando se activa o desactiva un equipo.
    """
    if created:
        # Equipo nuevo activado
        crear_notificacion_por_tipo(
            codigo_tipo='MAQUINARIAS_EQUIPO_ACTIVADO',
            titulo=f'Equipo activado: {instance.nombreEquipo}',
            mensaje=(
                f"Se ha activado el equipo {instance.nombreEquipo} "
                f"(Código: {instance.codigoInterno})."
            ),
            datos_adicionales={
                'equipo_id': instance.equipo_id,
                'codigo': instance.codigoInterno
            }
        )
    else:
        # Verificar si cambió el estado activo
        if hasattr(instance, '_previous_activo'):
            if instance._previous_activo and not instance.activo:
                # Se desactivó
                crear_notificacion_por_tipo(
                    codigo_tipo='MAQUINARIAS_EQUIPO_DESACTIVADO',
                    titulo=f'Equipo desactivado: {instance.nombreEquipo}',
                    mensaje=(
                        f"Se ha desactivado el equipo {instance.nombreEquipo} "
                        f"(Código: {instance.codigoInterno})."
                    ),
                    datos_adicionales={
                        'equipo_id': instance.equipo_id,
                        'codigo': instance.codigoInterno
                    }
                )
            elif not instance._previous_activo and instance.activo:
                # Se activó
                crear_notificacion_por_tipo(
                    codigo_tipo='MAQUINARIAS_EQUIPO_ACTIVADO',
                    titulo=f'Equipo activado: {instance.nombreEquipo}',
                    mensaje=(
                        f"Se ha activado el equipo {instance.nombreEquipo} "
                        f"(Código: {instance.codigoInterno})."
                    ),
                    datos_adicionales={
                        'equipo_id': instance.equipo_id,
                        'codigo': instance.codigoInterno
                    }
                )


@receiver(pre_save, sender='maquinarias.Equipo')
def guardar_estado_previo_equipo(sender, instance, **kwargs):
    """
    Guarda el estado previo del equipo para detectar cambios.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._previous_activo = old_instance.activo
        except sender.DoesNotExist:
            instance._previous_activo = None
    else:
        instance._previous_activo = None


@receiver(post_save, sender='maquinarias.OrdenTrabajo')
def notificar_cambio_ot(sender, instance, created, **kwargs):
    """
    Notifica cuando se crea una OT o cambia su estado.
    """
    if created:
        # OT creada
        crear_notificacion_por_tipo(
            codigo_tipo='MAQUINARIAS_OT_CREADA',
            titulo=f'Orden de Trabajo creada: OT-{instance.folio}',
            mensaje=(
                f"Se ha creado la Orden de Trabajo OT-{instance.folio} "
                f"para el equipo {instance.equipo_id.nombreEquipo if instance.equipo_id else 'N/A'}."
            ),
            datos_adicionales={
                'ot_id': instance.ot_id,
                'folio': instance.folio,
                'equipo_id': instance.equipo_id.equipo_id if instance.equipo_id else None
            }
        )
    else:
        # Verificar si cambió el estado
        if hasattr(instance, '_previous_estado_ot_id'):
            estado_anterior = instance._previous_estado_ot_id
            estado_actual = instance.estado_ot_id
            
            if estado_anterior != estado_actual:
                estado_nombre = estado_actual.nombre if estado_actual else 'N/A'
                
                # Si el estado es "Disponible" o similar
                if estado_actual and 'disponible' in estado_actual.nombre.lower():
                    crear_notificacion_por_tipo(
                        codigo_tipo='MAQUINARIAS_EQUIPO_DISPONIBLE',
                        titulo=f'Equipo disponible: {instance.equipo_id.nombreEquipo if instance.equipo_id else "N/A"}',
                        mensaje=(
                            f"El equipo {instance.equipo_id.nombreEquipo if instance.equipo_id else 'N/A'} "
                            f"ha cambiado a estado disponible (OT-{instance.folio})."
                        ),
                        datos_adicionales={
                            'ot_id': instance.ot_id,
                            'folio': instance.folio,
                            'equipo_id': instance.equipo_id.equipo_id if instance.equipo_id else None,
                            'estado': estado_nombre
                        }
                    )
                else:
                    # Cambio de estado general
                    crear_notificacion_por_tipo(
                        codigo_tipo='MAQUINARIAS_OT_ESTADO_CAMBIADO',
                        titulo=f'Estado de OT cambiado: OT-{instance.folio}',
                        mensaje=(
                            f"La Orden de Trabajo OT-{instance.folio} ha cambiado de estado a '{estado_nombre}'."
                        ),
                        datos_adicionales={
                            'ot_id': instance.ot_id,
                            'folio': instance.folio,
                            'estado_anterior_id': estado_anterior.estadoOT_id if estado_anterior else None,
                            'estado_actual_id': estado_actual.estadoOT_id if estado_actual else None,
                            'estado': estado_nombre
                        }
                    )


@receiver(pre_save, sender='maquinarias.OrdenTrabajo')
def guardar_estado_previo_ot(sender, instance, **kwargs):
    """
    Guarda el estado previo de la OT para detectar cambios.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._previous_estado_ot_id = old_instance.estado_ot_id
        except sender.DoesNotExist:
            instance._previous_estado_ot_id = None
    else:
        instance._previous_estado_ot_id = None


@receiver(post_save, sender='ope_calendario.AsignacionEquipoFaena')
def notificar_asignacion_equipo_faena(sender, instance, created, **kwargs):
    """
    Notifica cuando se asigna un equipo a una faena.
    """
    if created:
        crear_notificacion_por_tipo(
            codigo_tipo='MAQUINARIAS_EQUIPO_ASIGNADO_FAENA',
            titulo=f'Equipo asignado a faena: {instance.equipo.nombreEquipo}',
            mensaje=(
                f"El equipo {instance.equipo.nombreEquipo} (Código: {instance.equipo.codigoInterno}) "
                f"ha sido asignado a la faena {instance.faena.nombre} "
                f"desde {instance.fecha_inicio.strftime('%d/%m/%Y')}."
            ),
            datos_adicionales={
                'equipo_id': instance.equipo.equipo_id,
                'faena_id': instance.faena.id,
                'asignacion_id': instance.id,
                'fecha_inicio': instance.fecha_inicio.isoformat()
            }
        )


# ============================================================================
# SIGNALS DE PLANIFICACIÓN
# ============================================================================

@receiver(post_save, sender='ope_calendario.Faena')
def notificar_faena(sender, instance, created, **kwargs):
    """
    Notifica cuando se crea, edita o elimina una faena.
    """
    if created:
        crear_notificacion_por_tipo(
            codigo_tipo='PLANIFICACION_FAENA_CREADA',
            titulo=f'Faena creada: {instance.nombre}',
            mensaje=(
                f"Se ha creado la faena {instance.nombre} "
                f"(Código: {instance.codigo}). "
                f"Período: {instance.fecha_inicio.strftime('%d/%m/%Y')} a "
                f"{instance.fecha_fin.strftime('%d/%m/%Y') if instance.fecha_fin else 'Indefinido'}."
            ),
            datos_adicionales={
                'faena_id': instance.id,
                'codigo': instance.codigo,
                'fecha_inicio': instance.fecha_inicio.isoformat(),
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None
            }
        )
    else:
        # Verificar si cambió algo importante
        if hasattr(instance, '_previous_fecha_inicio'):
            fecha_inicio_anterior = instance._previous_fecha_inicio
            fecha_fin_anterior = instance._previous_fecha_fin
            
            # Si cambió la fecha de inicio o fin, notificar
            if fecha_inicio_anterior != instance.fecha_inicio or fecha_fin_anterior != instance.fecha_fin:
                crear_notificacion_por_tipo(
                    codigo_tipo='PLANIFICACION_FAENA_EDITADA',
                    titulo=f'Faena editada: {instance.nombre}',
                    mensaje=(
                        f"Se han modificado las fechas de la faena {instance.nombre} "
                        f"(Código: {instance.codigo}). "
                        f"Nuevo período: {instance.fecha_inicio.strftime('%d/%m/%Y')} a "
                        f"{instance.fecha_fin.strftime('%d/%m/%Y') if instance.fecha_fin else 'Indefinido'}."
                    ),
                    datos_adicionales={
                        'faena_id': instance.id,
                        'codigo': instance.codigo
                    }
                )


@receiver(pre_save, sender='ope_calendario.Faena')
def guardar_estado_previo_faena(sender, instance, **kwargs):
    """
    Guarda el estado previo de la faena para detectar cambios.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._previous_fecha_inicio = old_instance.fecha_inicio
            instance._previous_fecha_fin = old_instance.fecha_fin
        except sender.DoesNotExist:
            instance._previous_fecha_inicio = None
            instance._previous_fecha_fin = None
    else:
        instance._previous_fecha_inicio = None
        instance._previous_fecha_fin = None


@receiver(post_save, sender='ope_calendario.AsignacionFaena')
def notificar_asignacion_personal_faena(sender, instance, created, **kwargs):
    """
    Notifica cuando se asigna personal a una faena.
    """
    if created:
        crear_notificacion_por_tipo(
            codigo_tipo='PLANIFICACION_PERSONAL_ASIGNADO_FAENA',
            titulo=f'Personal asignado a faena: {instance.personal.nombre} {instance.personal.apepat}',
            mensaje=(
                f"{instance.personal.nombre} {instance.personal.apepat} "
                f"(RUT: {instance.personal.rut}-{instance.personal.dvrut}) "
                f"ha sido asignado a la faena {instance.faena.nombre} "
                f"con turno {instance.turno.nombre} desde {instance.fecha_inicio.strftime('%d/%m/%Y')}."
            ),
            datos_adicionales={
                'personal_id': instance.personal.personal_id,
                'faena_id': instance.faena.id,
                'asignacion_id': instance.id,
                'turno_id': instance.turno.id,
                'fecha_inicio': instance.fecha_inicio.isoformat()
            }
        )


# ============================================================================
# SIGNALS GENERALES
# ============================================================================

# Nota: Las notificaciones de cambio de contraseña y login fallido
# se manejan directamente en las vistas personalizadas:
# - Cambio de contraseña: main_home/views.py -> cambiar_contraseña_view()
# - Login fallido: main_login/views.py -> CustomLoginView
# Esto es más eficiente que usar signals que se disparan en cada login


# ============================================================================
# SIGNAL PARA ENVIAR EVENTOS SSE CUANDO SE CREA UNA NOTIFICACIÓN
# ============================================================================

@receiver(post_save, sender=Notificacion)
def enviar_evento_sse_notificacion(sender, instance, created, **kwargs):
    """
    Envía un evento SSE cuando se crea una nueva notificación.
    Esto permite que el cliente reciba la notificación en tiempo real.
    """
    if created:
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Asegurar que el tipo_notificacion esté cargado
            try:
                # Recargar desde la base de datos para asegurar que tenemos todos los datos
                instance.refresh_from_db()
            except Exception as e:
                logger.warning(f'No se pudo refrescar notificación {instance.id}: {str(e)}')
            
            # Preparar datos de la notificación para el evento
            from django.utils.timezone import localtime
            notificacion_data = {
                'id': instance.id,
                'titulo': instance.titulo,
                'mensaje': instance.mensaje,
                'tipo': instance.tipo_notificacion.nombre if instance.tipo_notificacion else 'Sin tipo',
                'codigo_tipo': instance.tipo_notificacion.codigo if instance.tipo_notificacion else '',
                'categoria': instance.tipo_notificacion.categoria if instance.tipo_notificacion else 'GENERAL',
                'prioridad': instance.prioridad,
                'leida': instance.leida,
                'archivada': instance.archivada,
                'fecha_creacion': localtime(instance.fecha_creacion).strftime('%d/%m/%Y %H:%M'),
                'datos_adicionales': instance.datos_adicionales
            }
            
            # Obtener el nuevo contador de notificaciones no leídas
            nuevo_contador = contar_notificaciones_no_leidas(instance.usuario)
            
            logger.info(f'Enviando evento SSE para notificación {instance.id} al usuario {instance.usuario.id} (contador: {nuevo_contador})')
            
            # Enviar evento SSE al usuario
            sse_manager.send_to_user(
                user_id=instance.usuario.id,
                event_type='notification',
                data={
                    'notificacion': notificacion_data,
                    'count': nuevo_contador
                }
            )
            
            logger.info(f'Evento SSE enviado correctamente para notificación {instance.id}')
        except Exception as e:
            # Loggear el error pero no fallar la creación de la notificación
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al enviar evento SSE para notificación {instance.id}: {str(e)}', exc_info=True)

