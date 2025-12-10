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
    Señal que se ejecuta después de guardar un Equipo.
    
    Registra en el historial cuando se crea o modifica un Equipo, capturando
    información sobre quién hizo el cambio y qué campos fueron modificados.
    Esta señal se dispara automáticamente después de cada save() en el modelo Equipo.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    # Esto permite registrar quién hizo el cambio en el historial
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO 1: Equipo creado (nuevo registro)
        # Paso 2.1: Registrar la creación del equipo en el historial
        # Se guardan todos los datos iniciales del equipo como datos_nuevos
        HistorialEquipo.registrar(
            equipo=instance,  # Equipo que se acaba de crear
            accion='EQUIPO_CREADO',  # Tipo de acción realizada
            descripcion=f"Equipo creado: {instance.nombreEquipo} (Código: {instance.codigoInterno})",  # Descripción legible
            usuario=usuario,  # Usuario que creó el equipo
            datos_nuevos={  # Todos los datos del equipo recién creado
                'equipo_id': instance.equipo_id,
                'nombreEquipo': instance.nombreEquipo,
                'codigoInterno': instance.codigoInterno,
                'patente': instance.patente,
                'activo': instance.activo,
            }
        )
    else:
        # CASO 2: Equipo modificado (registro existente actualizado)
        # Paso 2.2: Verificar qué campos cambiaron comparando con el estado previo
        # El estado previo se guarda en pre_save (ver función guardar_estado_previo_equipo)
        if hasattr(instance, '_previous_state'):
            previo = instance._previous_state  # Estado anterior del equipo
            
            # Paso 2.3: Verificar si cambió el estado activo/inactivo
            # Este es un cambio importante que se registra por separado
            if previo.get('activo') != instance.activo:
                if instance.activo:
                    # Equipo fue activado
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_ACTIVADO',
                        descripcion=f"Equipo activado: {instance.nombreEquipo}",
                        usuario=usuario,
                        datos_previos={'activo': False},  # Estado anterior
                        datos_nuevos={'activo': True}  # Estado nuevo
                    )
                else:
                    # Equipo fue desactivado
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_DESACTIVADO',
                        descripcion=f"Equipo desactivado: {instance.nombreEquipo}",
                        usuario=usuario,
                        datos_previos={'activo': True},  # Estado anterior
                        datos_nuevos={'activo': False}  # Estado nuevo
                    )
            else:
                # Paso 2.4: Verificar cambios en otros campos importantes
                # Se comparan solo los campos considerados importantes para el historial
                campos_cambiados = []
                campos_importantes = ['nombreEquipo', 'codigoInterno', 'patente', 'horometro', 'odometro', 'horometroSuperEstructural']
                
                # Comparar cada campo importante con su valor anterior
                for campo in campos_importantes:
                    if previo.get(campo) != getattr(instance, campo, None):
                        campos_cambiados.append(campo)  # Agregar a la lista si cambió
                
                # Paso 2.5: Registrar los cambios si hubo alguno
                if campos_cambiados:
                    # Crear diccionarios con solo los campos que cambiaron
                    datos_previos = {campo: previo.get(campo) for campo in campos_cambiados}
                    datos_nuevos = {campo: getattr(instance, campo) for campo in campos_cambiados}
                    
                    # Registrar en el historial con los cambios detectados
                    HistorialEquipo.registrar(
                        equipo=instance,
                        accion='EQUIPO_MODIFICADO',
                        descripcion=f"Equipo modificado: {', '.join(campos_cambiados)}",  # Lista de campos modificados
                        usuario=usuario,
                        datos_previos=datos_previos,  # Valores anteriores
                        datos_nuevos=datos_nuevos  # Valores nuevos
                    )


@receiver(pre_save, sender=Equipo)
def guardar_estado_previo_equipo(sender, instance, **kwargs):
    """
    Señal que se ejecuta ANTES de guardar un Equipo.
    
    Guarda el estado previo del Equipo antes de guardar para poder comparar cambios después.
    Esta información se usa en la señal post_save para determinar qué campos cambiaron.
    Esta señal se dispara automáticamente antes de cada save() en el modelo Equipo.
    """
    # Paso 1: Verificar que el equipo ya existe en la base de datos
    # Solo guardamos el estado previo si es una edición, no si es una creación nueva
    if instance.pk:  # pk existe solo si el objeto ya está guardado en la BD
        try:
            # Paso 2: Obtener el estado actual del equipo desde la base de datos
            # Esto nos da los valores ANTES de que se apliquen los cambios del save()
            equipo_anterior = Equipo.objects.get(pk=instance.pk)
            
            # Paso 3: Guardar el estado previo en un atributo temporal de la instancia
            # Este atributo se usará en post_save para comparar con los nuevos valores
            instance._previous_state = {
                'activo': equipo_anterior.activo,  # Estado de activación
                'nombreEquipo': equipo_anterior.nombreEquipo,  # Nombre del equipo
                'codigoInterno': equipo_anterior.codigoInterno,  # Código interno
                'patente': equipo_anterior.patente,  # Patente del equipo
                'horometro': equipo_anterior.horometro,  # Horas de uso
                'odometro': equipo_anterior.odometro,  # Kilómetros recorridos
                'horometroSuperEstructural': equipo_anterior.horometroSuperEstructural,  # Horas de superestructura
            }
        except Equipo.DoesNotExist:
            # Si por alguna razón no existe el equipo anterior, inicializar como diccionario vacío
            instance._previous_state = {}


@receiver(pre_delete, sender=Equipo)
def registrar_eliminacion_equipo(sender, instance, **kwargs):
    """
    Señal que se ejecuta ANTES de eliminar un Equipo.
    
    Registra en el historial cuando se elimina un Equipo, capturando información
    sobre quién lo eliminó y los datos del equipo eliminado.
    Esta señal se dispara automáticamente antes de cada delete() en el modelo Equipo.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Paso 2: Registrar la eliminación en el historial
    # Se guardan los datos del equipo antes de que se elimine de la base de datos
    HistorialEquipo.registrar(
        equipo=instance,  # Equipo que se está eliminando
        accion='EQUIPO_ELIMINADO',  # Tipo de acción realizada
        descripcion=f"Equipo eliminado: {instance.nombreEquipo} (Código: {instance.codigoInterno})",  # Descripción legible
        usuario=usuario,  # Usuario que eliminó el equipo
        datos_previos={  # Datos del equipo antes de eliminarlo (para referencia histórica)
            'equipo_id': instance.equipo_id,
            'nombreEquipo': instance.nombreEquipo,
            'codigoInterno': instance.codigoInterno,
            'patente': instance.patente,
        }
    )


# Señales para estados manuales de equipos
@receiver(post_save, sender=EstadoManualEquipo)
def registrar_estado_manual_equipo(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar un EstadoManualEquipo.
    
    Registra en el historial cuando se asigna o modifica un estado manual a un equipo.
    Los estados manuales permiten asignar estados temporales a equipos independientemente
    de las órdenes de trabajo o asignaciones a faenas.
    
    Esta señal se dispara automáticamente después de cada save() en el modelo EstadoManualEquipo.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO 1: Estado manual creado (nuevo registro)
        # Paso 2.1: Registrar la asignación del estado manual en el historial
        HistorialEquipo.registrar(
            equipo=instance.equipo,  # Equipo al que se asignó el estado
            accion='ESTADO_MANUAL_ASIGNADO',  # Tipo de acción realizada
            descripcion=f"Estado manual '{instance.estado.nombre}' asignado al equipo desde {instance.fecha_inicio} hasta {instance.fecha_fin}",  # Descripción legible
            usuario=usuario,  # Usuario que asignó el estado
            datos_nuevos={  # Datos del estado manual asignado
                'estado_id': instance.estado.id,  # ID del estado
                'estado_nombre': instance.estado.nombre,  # Nombre del estado
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,  # Fecha de inicio (formato ISO)
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,  # Fecha de fin (formato ISO)
            }
        )
    else:
        # CASO 2: Estado manual modificado (registro existente actualizado)
        # Paso 2.2: Registrar la modificación del estado manual en el historial
        HistorialEquipo.registrar(
            equipo=instance.equipo,  # Equipo cuyo estado manual fue modificado
            accion='ESTADO_MANUAL_MODIFICADO',  # Tipo de acción realizada
            descripcion=f"Estado manual modificado",  # Descripción legible
            usuario=usuario,  # Usuario que modificó el estado
        )


@receiver(pre_delete, sender=EstadoManualEquipo)
def registrar_eliminacion_estado_manual_equipo(sender, instance, **kwargs):
    """
    Señal que se ejecuta ANTES de eliminar un EstadoManualEquipo.
    
    Registra en el historial cuando se elimina un estado manual de un equipo.
    Se guardan los datos del estado antes de que se elimine de la base de datos
    para mantener un registro histórico completo.
    
    Esta señal se dispara automáticamente antes de cada delete() en el modelo EstadoManualEquipo.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Paso 2: Registrar la eliminación en el historial
    # Se guardan los datos del estado antes de que se elimine de la base de datos
    HistorialEquipo.registrar(
        equipo=instance.equipo,  # Equipo del que se eliminó el estado
        accion='ESTADO_MANUAL_ELIMINADO',  # Tipo de acción realizada
        descripcion=f"Estado manual '{instance.estado.nombre}' eliminado del equipo",  # Descripción legible
        usuario=usuario,  # Usuario que eliminó el estado
        datos_previos={  # Datos del estado antes de eliminarlo (para referencia histórica)
            'estado_id': instance.estado.id,  # ID del estado
            'estado_nombre': instance.estado.nombre,  # Nombre del estado
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,  # Fecha de inicio (formato ISO)
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,  # Fecha de fin (formato ISO)
        }
    )


# Señales para asignaciones de equipos a faenas
@receiver(post_save, sender=AsignacionEquipoFaena)
def registrar_asignacion_equipo_faena(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar una AsignacionEquipoFaena.
    
    Registra en el historial cuando se asigna o modifica un equipo a una faena.
    Las asignaciones a faenas indican que un equipo está siendo utilizado en un proyecto específico
    durante un período de tiempo determinado.
    
    Esta señal se dispara automáticamente después de cada save() en el modelo AsignacionEquipoFaena.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO 1: Asignación a faena creada (nuevo registro)
        # Paso 2.1: Registrar la asignación del equipo a la faena en el historial
        HistorialEquipo.registrar(
            equipo=instance.equipo,  # Equipo asignado a la faena
            accion='ASIGNACION_FAENA_CREADA',  # Tipo de acción realizada
            descripcion=f"Equipo asignado a faena '{instance.faena.nombre}' desde {instance.fecha_inicio} hasta {instance.fecha_fin or 'sin fecha fin'}",  # Descripción legible
            usuario=usuario,  # Usuario que realizó la asignación
            datos_nuevos={  # Datos de la asignación creada
                'faena_id': instance.faena.id,  # ID de la faena
                'faena_nombre': instance.faena.nombre,  # Nombre de la faena
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,  # Fecha de inicio (formato ISO)
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,  # Fecha de fin (formato ISO)
            }
        )
    else:
        # CASO 2: Asignación a faena modificada (registro existente actualizado)
        # Paso 2.2: Registrar la modificación de la asignación en el historial
        HistorialEquipo.registrar(
            equipo=instance.equipo,  # Equipo cuya asignación fue modificada
            accion='ASIGNACION_FAENA_MODIFICADA',  # Tipo de acción realizada
            descripcion=f"Asignación a faena '{instance.faena.nombre}' modificada",  # Descripción legible
            usuario=usuario,  # Usuario que modificó la asignación
        )


@receiver(pre_delete, sender=AsignacionEquipoFaena)
def registrar_eliminacion_asignacion_equipo_faena(sender, instance, **kwargs):
    """
    Señal que se ejecuta ANTES de eliminar una AsignacionEquipoFaena.
    
    Registra en el historial cuando se elimina una asignación de equipo a faena.
    Se guardan los datos de la asignación antes de que se elimine de la base de datos
    para mantener un registro histórico completo de cuándo y dónde estuvo asignado el equipo.
    
    Esta señal se dispara automáticamente antes de cada delete() en el modelo AsignacionEquipoFaena.
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se pasa desde la vista usando el atributo temporal _current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Paso 2: Registrar la eliminación en el historial
    # Se guardan los datos de la asignación antes de que se elimine de la base de datos
    HistorialEquipo.registrar(
        equipo=instance.equipo,  # Equipo cuya asignación fue eliminada
        accion='ASIGNACION_FAENA_ELIMINADA',  # Tipo de acción realizada
        descripcion=f"Asignación a faena '{instance.faena.nombre}' eliminada",  # Descripción legible
        usuario=usuario,  # Usuario que eliminó la asignación
        datos_previos={  # Datos de la asignación antes de eliminarla (para referencia histórica)
            'faena_id': instance.faena.id,  # ID de la faena
            'faena_nombre': instance.faena.nombre,  # Nombre de la faena
            'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,  # Fecha de inicio (formato ISO)
            'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,  # Fecha de fin (formato ISO)
        }
    )

