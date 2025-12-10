# ============================================================================
# SEÑALES DJANGO PARA HISTORIAL DE FAENAS
# ============================================================================
# Este módulo define señales Django que capturan automáticamente cambios en los modelos
# relacionados con faenas y los registran en el historial.
# Complementa el registro manual existente en las vistas para asegurar que todos
# los cambios queden registrados, incluso si se hacen desde el admin o APIs.

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Faena, AsignacionFaena, HistorialFaena, EstadoManual


@receiver(post_save, sender=Faena)
def registrar_cambio_faena(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar una Faena (creación o modificación).
    Registra automáticamente el cambio en el historial de faenas.
    Complementa el registro manual en las vistas para asegurar que todos los cambios queden registrados.
    
    Parámetros:
        sender: Modelo que envió la señal (Faena)
        instance: Instancia de Faena que fue guardada
        created: bool - True si es una creación nueva, False si es una modificación
        **kwargs: Argumentos adicionales de la señal
    """
    # Paso 1: Obtener el usuario actual si está disponible
    # El usuario se puede pasar desde las vistas usando instance._current_user
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO: Faena creada - solo registrar si no se registró manualmente
        # Las vistas pueden registrar manualmente con más detalles, por lo que se verifica
        # el atributo _historial_registrado para evitar duplicados
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
        # CASO: Faena modificada - solo registrar si no se registró manualmente
        # Se requiere que exista _previous_state (guardado por pre_save) para comparar cambios
        if not hasattr(instance, '_historial_registrado') and hasattr(instance, '_previous_state'):
            previo = instance._previous_state  # Estado anterior guardado por la señal pre_save
            
            # Paso 2.1: Verificar cambio de estado activo/inactivo (prioridad alta)
            # Los cambios de estado activo/inactivo son críticos y se registran por separado
            if previo.get('activo') != instance.activo:
                if instance.activo:
                    # CASO: Faena activada
                    HistorialFaena.registrar(
                        faena=instance,
                        accion='FAENA_MODIFICADA',
                        descripcion=f"Faena activada: {instance.nombre}",
                        usuario=usuario,
                        datos_previos={'activo': False},
                        datos_nuevos={'activo': True}
                    )
                else:
                    # CASO: Faena desactivada
                    HistorialFaena.registrar(
                        faena=instance,
                        accion='FAENA_MODIFICADA',
                        descripcion=f"Faena desactivada: {instance.nombre}",
                        usuario=usuario,
                        datos_previos={'activo': True},
                        datos_nuevos={'activo': False}
                    )
            else:
                # Paso 2.2: Otros cambios en campos importantes
                # Comparar campos importantes para detectar qué cambió
                campos_cambiados = []
                campos_importantes = ['codigo', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'ubicacion']
                
                # Verificar cada campo importante para ver si cambió
                for campo in campos_importantes:
                    valor_previo = previo.get(campo)
                    valor_actual = getattr(instance, campo, None)
                    
                    # Convertir fechas a formato ISO para comparación si es necesario
                    if campo in ['fecha_inicio', 'fecha_fin'] and valor_actual:
                        valor_actual = valor_actual.isoformat() if hasattr(valor_actual, 'isoformat') else valor_actual
                    
                    if valor_previo != valor_actual:
                        campos_cambiados.append(campo)
                
                # Paso 2.3: Si hay campos cambiados, registrar el cambio en el historial
                if campos_cambiados:
                    # Construir diccionarios con solo los campos que cambiaron
                    datos_previos = {campo: previo.get(campo) for campo in campos_cambiados}
                    datos_nuevos = {campo: getattr(instance, campo) for campo in campos_cambiados}
                    
                    # Convertir fechas a formato ISO en datos_nuevos
                    for campo in ['fecha_inicio', 'fecha_fin']:
                        if campo in datos_nuevos and datos_nuevos[campo] and hasattr(datos_nuevos[campo], 'isoformat'):
                            datos_nuevos[campo] = datos_nuevos[campo].isoformat()
                    
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
    Señal que se ejecuta ANTES de guardar una Faena.
    Guarda el estado previo de la faena en instance._previous_state para poder
    comparar cambios después en la señal post_save.
    
    Parámetros:
        sender: Modelo que envió la señal (Faena)
        instance: Instancia de Faena que se va a guardar
        **kwargs: Argumentos adicionales de la señal
    """
    if instance.pk:  # Solo si ya existe en la BD (no es una creación nueva)
        try:
            # Paso 1: Obtener la faena anterior desde la base de datos
            faena_anterior = Faena.objects.get(pk=instance.pk)
            
            # Paso 2: Guardar el estado previo en un atributo temporal de la instancia
            # Este atributo será usado por la señal post_save para comparar cambios
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
            # Si no existe (no debería ocurrir), inicializar con diccionario vacío
            instance._previous_state = {}


@receiver(post_save, sender=AsignacionFaena)
def registrar_asignacion_faena(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar una AsignacionFaena (creación o modificación).
    Registra automáticamente el cambio en el historial de faenas.
    Solo registra si no se registró manualmente en las vistas (para evitar duplicados).
    
    Parámetros:
        sender: Modelo que envió la señal (AsignacionFaena)
        instance: Instancia de AsignacionFaena que fue guardada
        created: bool - True si es una creación nueva, False si es una modificación
        **kwargs: Argumentos adicionales de la señal
    """
    # Paso 1: Verificar si ya se registró manualmente en las vistas
    # Las vistas pueden registrar manualmente con más detalles, por lo que se verifica
    # el atributo _historial_registrado para evitar duplicados
    if hasattr(instance, '_historial_registrado'):
        return  # Ya se registró manualmente, no hacer nada
    
    # Paso 2: Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO: Asignación creada - registrar en el historial
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
        # CASO: Asignación modificada - registrar en el historial
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
    Señal que se ejecuta ANTES de eliminar una AsignacionFaena.
    Registra automáticamente la eliminación en el historial de faenas.
    Solo registra si no se registró manualmente en las vistas (para evitar duplicados).
    
    Nota: Se usa pre_delete en lugar de post_delete para poder acceder a los datos
    de la instancia antes de que se elimine de la base de datos.
    
    Parámetros:
        sender: Modelo que envió la señal (AsignacionFaena)
        instance: Instancia de AsignacionFaena que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Paso 1: Verificar si ya se registró manualmente en las vistas
    if hasattr(instance, '_historial_registrado'):
        return  # Ya se registró manualmente, no hacer nada
    
    # Paso 2: Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Paso 3: Registrar la eliminación en el historial
    # Se guardan los datos previos porque después de eliminar ya no estarán disponibles
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
    Señal que se ejecuta después de guardar un EstadoManual (creación o modificación).
    Registra automáticamente el cambio en el historial de faenas.
    
    Parámetros:
        sender: Modelo que envió la señal (EstadoManual)
        instance: Instancia de EstadoManual que fue guardada
        created: bool - True si es una creación nueva, False si es una modificación
        **kwargs: Argumentos adicionales de la señal
    """
    # Paso 1: Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # CASO: Estado manual creado - registrar en el historial
        HistorialFaena.registrar(
            faena=instance.faena if instance.faena else None,  # Puede ser None si no está asociado a faena
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
    Señal que se ejecuta ANTES de eliminar un EstadoManual.
    Registra automáticamente la eliminación en el historial de faenas.
    
    Nota: Se usa pre_delete en lugar de post_delete para poder acceder a los datos
    de la instancia antes de que se elimine de la base de datos.
    
    Parámetros:
        sender: Modelo que envió la señal (EstadoManual)
        instance: Instancia de EstadoManual que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Paso 1: Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Paso 2: Registrar la eliminación en el historial
    # Se guardan los datos previos porque después de eliminar ya no estarán disponibles
    HistorialFaena.registrar(
        faena=instance.faena if instance.faena else None,  # Puede ser None si no está asociado a faena
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

