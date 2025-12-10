"""
Señales Django para capturar cambios automáticamente y registrar en historial.

Este módulo contiene todos los receivers de señales Django que se ejecutan
automáticamente cuando se crean, modifican o eliminan registros de Personal
y sus documentos relacionados (licencias, certificaciones, exámenes, etc.).

Las señales permiten mantener un historial completo de auditoría sin necesidad
de modificar manualmente el código de las vistas.
"""
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Personal, HistorialPersonal, HistorialDocumentoPersonal
from .models import LicenciaPorPersonal, LicenciaMedicaPorPersonal, LicenciaInternaPorPersonal, Certificacion, Examen


@receiver(post_save, sender=Personal)
def registrar_cambio_personal(sender, instance, created, **kwargs):
    """
    Registra en el historial cuando se crea o modifica un Personal.
    
    Esta señal se ejecuta después de guardar un registro de Personal.
    Detecta si es una creación nueva o una modificación, y registra los cambios
    relevantes en HistorialPersonal. También crea notificaciones si la app
    de notificaciones está disponible.
    
    Args:
        sender: El modelo que envió la señal (Personal)
        instance: La instancia del Personal que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible (se establece en las vistas)
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    if created:
        # Caso: Personal creado (nuevo registro)
        HistorialPersonal.registrar(
            personal=instance,
            accion='PERSONAL_CREADO',
            descripcion=f"Personal creado: {instance.nombre} {instance.apepat} (RUT: {instance.rut}-{instance.dvrut})",
            usuario=usuario,
            datos_nuevos={
                'rut': instance.rut,
                'dvrut': instance.dvrut,
                'nombre': instance.nombre,
                'apepat': instance.apepat,
                'apemat': instance.apemat,
                'correo': instance.correo,
                'activo': instance.activo,
            }
        )
        
        # Intentar crear notificación de personal creado (si la app está disponible)
        try:
            from notificaciones.utils import crear_notificacion_por_tipo
            crear_notificacion_por_tipo(
                codigo_tipo='RRHH_PERSONAL_CREADO',
                titulo=f'Personal creado: {instance.nombre} {instance.apepat}',
                mensaje=f'Se ha creado el personal {instance.nombre} {instance.apepat} (RUT: {instance.rut}-{instance.dvrut}).',
                datos_adicionales={
                    'personal_id': instance.personal_id,
                    'rut': f'{instance.rut}-{instance.dvrut}',
                    'nombre_completo': f'{instance.nombre} {instance.apepat} {instance.apemat or ""}'.strip(),
                    'url_accion': f'/rrhh/personal/{instance.personal_id}/'
                }
            )
        except ImportError:
            # La app de notificaciones no está disponible, continuar sin error
            pass
    else:
        # Caso: Personal modificado (registro existente)
        # Verificar cambios importantes comparando con el estado previo
        if hasattr(instance, '_previous_state'):
            previo = instance._previous_state
            cambios = []
            
            # Verificar cambio de estado activo/inactivo (cambio crítico)
            if previo.get('activo') != instance.activo:
                if instance.activo:
                    # Personal fue activado
                    HistorialPersonal.registrar(
                        personal=instance,
                        accion='PERSONAL_ACTIVADO',
                        descripcion=f"Personal activado: {instance.nombre} {instance.apepat}",
                        usuario=usuario,
                        datos_previos={'activo': False},
                        datos_nuevos={'activo': True}
                    )
                    
                    # Intentar crear notificación de personal activado
                    try:
                        from notificaciones.utils import crear_notificacion_por_tipo
                        crear_notificacion_por_tipo(
                            codigo_tipo='RRHH_PERSONAL_ACTIVADO',
                            titulo=f'Personal activado: {instance.nombre} {instance.apepat}',
                            mensaje=f'Se ha activado el personal {instance.nombre} {instance.apepat} (RUT: {instance.rut}-{instance.dvrut}).',
                            datos_adicionales={
                                'personal_id': instance.personal_id,
                                'rut': f'{instance.rut}-{instance.dvrut}',
                                'nombre_completo': f'{instance.nombre} {instance.apepat} {instance.apemat or ""}'.strip(),
                                'url_accion': f'/rrhh/personal/{instance.personal_id}/'
                            }
                        )
                    except ImportError:
                        # La app de notificaciones no está disponible, continuar sin error
                        pass
                else:
                    # Personal fue desactivado
                    HistorialPersonal.registrar(
                        personal=instance,
                        accion='PERSONAL_DESACTIVADO',
                        descripcion=f"Personal desactivado: {instance.nombre} {instance.apepat}",
                        usuario=usuario,
                        datos_previos={'activo': True},
                        datos_nuevos={'activo': False}
                    )
                    
                    # Intentar crear notificación de personal desactivado
                    try:
                        from notificaciones.utils import crear_notificacion_por_tipo
                        crear_notificacion_por_tipo(
                            codigo_tipo='RRHH_PERSONAL_DESACTIVADO',
                            titulo=f'Personal desactivado: {instance.nombre} {instance.apepat}',
                            mensaje=f'Se ha desactivado el personal {instance.nombre} {instance.apepat} (RUT: {instance.rut}-{instance.dvrut}).',
                            datos_adicionales={
                                'personal_id': instance.personal_id,
                                'rut': f'{instance.rut}-{instance.dvrut}',
                                'nombre_completo': f'{instance.nombre} {instance.apepat} {instance.apemat or ""}'.strip(),
                                'url_accion': f'/rrhh/personal/{instance.personal_id}/'
                            }
                        )
                    except ImportError:
                        # La app de notificaciones no está disponible, continuar sin error
                        pass
            else:
                # Caso: Otros cambios (no relacionados con activación/desactivación)
                # Comparar todos los campos importantes para detectar modificaciones
                cambios_detallados = []
                # Diccionario que mapea nombres de campos de BD a nombres legibles
                campos_importantes = {
                    'nombre': 'Nombre',
                    'apepat': 'Apellido Paterno',
                    'apemat': 'Apellido Materno',
                    'correo': 'Correo',
                    'direccion': 'Dirección',
                    'rut': 'RUT',
                    'dvrut': 'Dígito Verificador',
                    'fecha_nacimiento': 'Fecha de Nacimiento',
                    'estcivil_id': 'Estado Civil',
                    'comuna_id': 'Comuna',
                    'sexo_id': 'Sexo',
                    'region_id': 'Región',
                }
                
                datos_previos = {}
                datos_nuevos = {}
                
                # Iterar sobre todos los campos importantes para detectar cambios
                for campo_db, campo_display in campos_importantes.items():
                    valor_previo = previo.get(campo_db)
                    
                    # Obtener valor nuevo según el tipo de campo
                    # Manejar campos ForeignKey de manera especial para obtener nombres legibles
                    if campo_db == 'estcivil_id':
                        valor_nuevo = instance.estcivil_id_id if instance.estcivil_id else None
                        # Comparar también el nombre del estado civil para la descripción
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {previo.get('estcivil_nombre', 'N/A')} → {instance.estcivil_id.estadocivil if instance.estcivil_id else 'N/A'}")
                            datos_previos[campo_db] = previo.get('estcivil_nombre', 'N/A')
                            datos_nuevos[campo_db] = instance.estcivil_id.estadocivil if instance.estcivil_id else 'N/A'
                    elif campo_db == 'fecha_nacimiento':
                        valor_nuevo = instance.fechanac.isoformat() if instance.fechanac else None
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {valor_previo or 'N/A'} → {valor_nuevo or 'N/A'}")
                            datos_previos[campo_db] = valor_previo
                            datos_nuevos[campo_db] = valor_nuevo
                    elif campo_db == 'sexo_id':
                        valor_nuevo = instance.sexo_id_id if instance.sexo_id else None
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {previo.get('sexo_nombre', 'N/A')} → {instance.sexo_id.sexo if instance.sexo_id else 'N/A'}")
                            datos_previos[campo_db] = previo.get('sexo_nombre', 'N/A')
                            datos_nuevos[campo_db] = instance.sexo_id.sexo if instance.sexo_id else 'N/A'
                    elif campo_db == 'region_id':
                        valor_nuevo = instance.region_id_id if instance.region_id else None
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {previo.get('region_nombre', 'N/A')} → {instance.region_id.nombre if instance.region_id else 'N/A'}")
                            datos_previos[campo_db] = previo.get('region_nombre', 'N/A')
                            datos_nuevos[campo_db] = instance.region_id.nombre if instance.region_id else 'N/A'
                    elif campo_db == 'comuna_id':
                        valor_nuevo = instance.comuna_id_id if instance.comuna_id else None
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {previo.get('comuna_nombre', 'N/A')} → {instance.comuna_id.nombre if instance.comuna_id else 'N/A'}")
                            datos_previos[campo_db] = previo.get('comuna_nombre', 'N/A')
                            datos_nuevos[campo_db] = instance.comuna_id.nombre if instance.comuna_id else 'N/A'
                    else:
                        valor_nuevo = getattr(instance, campo_db, None)
                        if valor_previo != valor_nuevo:
                            cambios_detallados.append(f"{campo_display}: {valor_previo or 'N/A'} → {valor_nuevo or 'N/A'}")
                            datos_previos[campo_db] = valor_previo
                            datos_nuevos[campo_db] = valor_nuevo
                
                if cambios_detallados:
                    HistorialPersonal.registrar(
                        personal=instance,
                        accion='PERSONAL_MODIFICADO',
                        descripcion=f"Personal modificado. Cambios: {'; '.join(cambios_detallados)}",
                        usuario=usuario,
                        datos_previos=datos_previos,
                        datos_nuevos=datos_nuevos
                    )


@receiver(pre_save, sender=Personal)
def guardar_estado_previo_personal(sender, instance, **kwargs):
    """
    Guarda el estado previo del Personal antes de guardar para comparar cambios.
    
    Esta señal se ejecuta ANTES de guardar un registro de Personal.
    Guarda el estado anterior en un atributo temporal (_previous_state) que
    será usado por registrar_cambio_personal para detectar qué cambió.
    
    Args:
        sender: El modelo que envió la señal (Personal)
        instance: La instancia del Personal que se va a guardar
        **kwargs: Argumentos adicionales de la señal
    """
    # Solo guardar estado previo si el registro ya existe (tiene PK)
    # Si no tiene PK, es un registro nuevo y no hay estado previo
    if instance.pk:
        try:
            personal_anterior = Personal.objects.get(pk=instance.pk)
            instance._previous_state = {
                'activo': personal_anterior.activo,
                'nombre': personal_anterior.nombre,
                'apepat': personal_anterior.apepat,
                'apemat': personal_anterior.apemat,
                'correo': personal_anterior.correo,
                'direccion': personal_anterior.direccion,
                'rut': personal_anterior.rut,
                'dvrut': personal_anterior.dvrut,
                'estcivil_id': personal_anterior.estcivil_id_id if personal_anterior.estcivil_id else None,
                'estcivil_nombre': personal_anterior.estcivil_id.estadocivil if personal_anterior.estcivil_id else None,
                'fecha_nacimiento': personal_anterior.fechanac.isoformat() if personal_anterior.fechanac else None,
                'comuna_id': personal_anterior.comuna_id_id if personal_anterior.comuna_id else None,
                'comuna_nombre': personal_anterior.comuna_id.nombre if personal_anterior.comuna_id else None,
                'sexo_id': personal_anterior.sexo_id_id if personal_anterior.sexo_id else None,
                'sexo_nombre': personal_anterior.sexo_id.sexo if personal_anterior.sexo_id else None,
                'region_id': personal_anterior.region_id_id if personal_anterior.region_id else None,
                'region_nombre': personal_anterior.region_id.nombre if personal_anterior.region_id else None,
            }
        except Personal.DoesNotExist:
            instance._previous_state = {}


@receiver(pre_delete, sender=Personal)
def registrar_eliminacion_personal(sender, instance, **kwargs):
    """
    Registra en el historial cuando se elimina un Personal.
    
    Esta señal se ejecuta ANTES de eliminar un registro de Personal.
    Guarda información del personal eliminado en el historial para auditoría.
    
    Args:
        sender: El modelo que envió la señal (Personal)
        instance: La instancia del Personal que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    HistorialPersonal.registrar(
        personal=instance,
        accion='PERSONAL_ELIMINADO',
        descripcion=f"Personal eliminado: {instance.nombre} {instance.apepat} (RUT: {instance.rut}-{instance.dvrut})",
        usuario=usuario,
        datos_previos={
            'rut': instance.rut,
            'dvrut': instance.dvrut,
            'nombre': instance.nombre,
            'apepat': instance.apepat,
            'apemat': instance.apemat,
        }
    )


# ============================================================================
# SEÑALES PARA DOCUMENTOS DE PERSONAL
# ============================================================================

@receiver(post_save, sender=LicenciaPorPersonal)
def registrar_licencia_conducir(sender, instance, created, **kwargs):
    """
    Registra cuando se agrega o modifica una licencia de conducir.
    
    Esta señal se ejecuta después de guardar un registro de LicenciaPorPersonal.
    Registra la acción en HistorialDocumentoPersonal para mantener un historial
    completo de todas las licencias de conducir del personal.
    
    Args:
        sender: El modelo que envió la señal (LicenciaPorPersonal)
        instance: La instancia de la licencia que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento con los tipos de licencia
    tipos_str = ", ".join([t.tipoLicencia for t in instance.tipos.all()])
    nombre_doc = f"Licencia de Conducir - Tipos: {tipos_str}"
    
    if created:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_CONDUCIR',
            accion='DOCUMENTO_AGREGADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia de conducir agregada. Emisión: {instance.fechaEmision}, Vencimiento: {instance.fechaVencimiento}",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
            datos_nuevos={
                'tipos': [t.tipoLicencia for t in instance.tipos.all()],
                'fecha_emision': instance.fechaEmision.isoformat() if instance.fechaEmision else None,
                'fecha_vencimiento': instance.fechaVencimiento.isoformat() if instance.fechaVencimiento else None,
            }
        )
    else:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_CONDUCIR',
            accion='DOCUMENTO_MODIFICADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia de conducir modificada",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )


@receiver(pre_delete, sender=LicenciaPorPersonal)
def registrar_eliminacion_licencia_conducir(sender, instance, **kwargs):
    """
    Registra cuando se elimina una licencia de conducir y mueve el archivo a eliminados.
    
    Esta señal se ejecuta ANTES de eliminar un registro de LicenciaPorPersonal.
    Mueve el archivo físico a la carpeta de eliminados (en lugar de borrarlo)
    para mantener un historial de documentos eliminados.
    
    Args:
        sender: El modelo que envió la señal (LicenciaPorPersonal)
        instance: La instancia de la licencia que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    tipos_str = ", ".join([t.tipoLicencia for t in instance.tipos.all()])
    nombre_doc = f"Licencia de Conducir - Tipos: {tipos_str}"
    
    # Mover archivo a carpeta de eliminados antes de eliminar el registro
    # Esto permite mantener un historial de documentos eliminados
    archivo_ruta_historial = None
    if instance.rutaDoc and instance.rutaDoc.name:
        from .models import mover_archivo_a_eliminados
        archivo_ruta_historial = mover_archivo_a_eliminados(
            instance.rutaDoc,
            instance.personal_id.rut,
            nombre_doc
        )
        # Si no se pudo mover, usar la ruta original como fallback
        if not archivo_ruta_historial:
            archivo_ruta_historial = instance.rutaDoc.name
    
    HistorialDocumentoPersonal.registrar(
        personal=instance.personal_id,
        tipo_documento='LICENCIA_CONDUCIR',
        accion='DOCUMENTO_ELIMINADO',
        nombre_documento=nombre_doc,
        descripcion=f"Licencia de conducir eliminada",
        usuario=usuario,
        archivo_ruta=archivo_ruta_historial,
        datos_previos={
            'tipos': [t.tipoLicencia for t in instance.tipos.all()],
            'fecha_emision': instance.fechaEmision.isoformat() if instance.fechaEmision else None,
            'fecha_vencimiento': instance.fechaVencimiento.isoformat() if instance.fechaVencimiento else None,
        }
    )


@receiver(post_save, sender=LicenciaMedicaPorPersonal)
def registrar_licencia_medica(sender, instance, created, **kwargs):
    """
    Registra cuando se agrega o modifica una licencia médica.
    
    Esta señal se ejecuta después de guardar un registro de LicenciaMedicaPorPersonal.
    Las licencias médicas no tienen archivo asociado, solo son registros de fechas.
    
    Args:
        sender: El modelo que envió la señal (LicenciaMedicaPorPersonal)
        instance: La instancia de la licencia médica que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Licencia Médica - {instance.tipoLicenciaMedica_id.tipoLicenciaMedica if instance.tipoLicenciaMedica_id else 'N/A'}"
    
    # Nota: Las licencias médicas no tienen archivo asociado (rutaDoc), solo son registros
    if created:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_MEDICA',
            accion='DOCUMENTO_AGREGADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia médica agregada",
            usuario=usuario,
            archivo_ruta=None,  # Las licencias médicas no tienen archivo
        )
    else:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_MEDICA',
            accion='DOCUMENTO_MODIFICADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia médica modificada",
            usuario=usuario,
            archivo_ruta=None,  # Las licencias médicas no tienen archivo
        )


@receiver(pre_delete, sender=LicenciaMedicaPorPersonal)
def registrar_eliminacion_licencia_medica(sender, instance, **kwargs):
    """
    Registra cuando se elimina una licencia médica.
    
    Esta señal se ejecuta ANTES de eliminar un registro de LicenciaMedicaPorPersonal.
    Las licencias médicas no tienen archivo asociado, solo se registra la eliminación.
    
    Args:
        sender: El modelo que envió la señal (LicenciaMedicaPorPersonal)
        instance: La instancia de la licencia médica que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Licencia Médica - {instance.tipoLicenciaMedica_id.tipoLicenciaMedica if instance.tipoLicenciaMedica_id else 'N/A'}"
    
    # Nota: Las licencias médicas no tienen archivo asociado (rutaDoc), solo son registros
    HistorialDocumentoPersonal.registrar(
        personal=instance.personal_id,
        tipo_documento='LICENCIA_MEDICA',
        accion='DOCUMENTO_ELIMINADO',
        nombre_documento=nombre_doc,
        descripcion=f"Licencia médica eliminada",
        usuario=usuario,
        archivo_ruta=None,  # Las licencias médicas no tienen archivo
    )


@receiver(post_save, sender=LicenciaInternaPorPersonal)
def registrar_licencia_interna(sender, instance, created, **kwargs):
    """
    Registra cuando se agrega o modifica una licencia interna.
    
    Esta señal se ejecuta después de guardar un registro de LicenciaInternaPorPersonal.
    Registra la acción en HistorialDocumentoPersonal para mantener un historial
    completo de todas las licencias internas del personal.
    
    Args:
        sender: El modelo que envió la señal (LicenciaInternaPorPersonal)
        instance: La instancia de la licencia interna que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Licencia Interna - {instance.tipoLicenciaInterna_id.tipoLicenciaInterna if instance.tipoLicenciaInterna_id else 'N/A'}"
    
    if created:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_INTERNA',
            accion='DOCUMENTO_AGREGADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia interna agregada",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )
    else:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='LICENCIA_INTERNA',
            accion='DOCUMENTO_MODIFICADO',
            nombre_documento=nombre_doc,
            descripcion=f"Licencia interna modificada",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )


@receiver(pre_delete, sender=LicenciaInternaPorPersonal)
def registrar_eliminacion_licencia_interna(sender, instance, **kwargs):
    """
    Registra cuando se elimina una licencia interna y mueve el archivo a eliminados.
    
    Esta señal se ejecuta ANTES de eliminar un registro de LicenciaInternaPorPersonal.
    Mueve el archivo físico a la carpeta de eliminados (en lugar de borrarlo)
    para mantener un historial de documentos eliminados.
    
    Args:
        sender: El modelo que envió la señal (LicenciaInternaPorPersonal)
        instance: La instancia de la licencia interna que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Licencia Interna - {instance.tipoLicenciaInterna_id.tipoLicenciaInterna if instance.tipoLicenciaInterna_id else 'N/A'}"
    
    # Mover archivo a carpeta de eliminados antes de eliminar el registro
    # Esto permite mantener un historial de documentos eliminados
    archivo_ruta_historial = None
    if instance.rutaDoc and instance.rutaDoc.name:
        from .models import mover_archivo_a_eliminados
        archivo_ruta_historial = mover_archivo_a_eliminados(
            instance.rutaDoc,
            instance.personal_id.rut,
            nombre_doc
        )
        # Si no se pudo mover, usar la ruta original como fallback
        if not archivo_ruta_historial:
            archivo_ruta_historial = instance.rutaDoc.name
    
    HistorialDocumentoPersonal.registrar(
        personal=instance.personal_id,
        tipo_documento='LICENCIA_INTERNA',
        accion='DOCUMENTO_ELIMINADO',
        nombre_documento=nombre_doc,
        descripcion=f"Licencia interna eliminada",
        usuario=usuario,
        archivo_ruta=archivo_ruta_historial,
    )


@receiver(post_save, sender=Certificacion)
def registrar_certificacion(sender, instance, created, **kwargs):
    """
    Registra cuando se agrega o modifica una certificación.
    
    Esta señal se ejecuta después de guardar un registro de Certificacion.
    Registra la acción en HistorialDocumentoPersonal para mantener un historial
    completo de todas las certificaciones del personal.
    
    Args:
        sender: El modelo que envió la señal (Certificacion)
        instance: La instancia de la certificación que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Certificación - {instance.tipoCertificacion_id.tipoCertificacion if instance.tipoCertificacion_id else 'N/A'}"
    
    if created:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='CERTIFICACION',
            accion='DOCUMENTO_AGREGADO',
            nombre_documento=nombre_doc,
            descripcion=f"Certificación agregada",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )
    else:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='CERTIFICACION',
            accion='DOCUMENTO_MODIFICADO',
            nombre_documento=nombre_doc,
            descripcion=f"Certificación modificada",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )


@receiver(pre_delete, sender=Certificacion)
def registrar_eliminacion_certificacion(sender, instance, **kwargs):
    """
    Registra cuando se elimina una certificación y mueve el archivo a eliminados.
    
    Esta señal se ejecuta ANTES de eliminar un registro de Certificacion.
    Mueve el archivo físico a la carpeta de eliminados (en lugar de borrarlo)
    para mantener un historial de documentos eliminados.
    
    Args:
        sender: El modelo que envió la señal (Certificacion)
        instance: La instancia de la certificación que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Certificación - {instance.tipoCertificacion_id.tipoCertificacion if instance.tipoCertificacion_id else 'N/A'}"
    
    # Mover archivo a carpeta de eliminados antes de eliminar el registro
    # Esto permite mantener un historial de documentos eliminados
    archivo_ruta_historial = None
    if instance.rutaDoc and instance.rutaDoc.name:
        from .models import mover_archivo_a_eliminados
        archivo_ruta_historial = mover_archivo_a_eliminados(
            instance.rutaDoc,
            instance.personal_id.rut,
            nombre_doc
        )
        # Si no se pudo mover, usar la ruta original como fallback
        if not archivo_ruta_historial:
            archivo_ruta_historial = instance.rutaDoc.name
    
    HistorialDocumentoPersonal.registrar(
        personal=instance.personal_id,
        tipo_documento='CERTIFICACION',
        accion='DOCUMENTO_ELIMINADO',
        nombre_documento=nombre_doc,
        descripcion=f"Certificación eliminada",
        usuario=usuario,
        archivo_ruta=archivo_ruta_historial,
    )


@receiver(post_save, sender=Examen)
def registrar_examen(sender, instance, created, **kwargs):
    """
    Registra cuando se agrega o modifica un examen.
    
    Esta señal se ejecuta después de guardar un registro de Examen.
    Registra la acción en HistorialDocumentoPersonal para mantener un historial
    completo de todos los exámenes del personal.
    
    Args:
        sender: El modelo que envió la señal (Examen)
        instance: La instancia del examen que se guardó
        created: Boolean que indica si es un registro nuevo (True) o una modificación (False)
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Examen - {instance.tipoEx_id.tipoExamen if instance.tipoEx_id else 'N/A'}"
    
    if created:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='EXAMEN',
            accion='DOCUMENTO_AGREGADO',
            nombre_documento=nombre_doc,
            descripcion=f"Examen agregado",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )
    else:
        HistorialDocumentoPersonal.registrar(
            personal=instance.personal_id,
            tipo_documento='EXAMEN',
            accion='DOCUMENTO_MODIFICADO',
            nombre_documento=nombre_doc,
            descripcion=f"Examen modificado",
            usuario=usuario,
            archivo_ruta=instance.rutaDoc.name if instance.rutaDoc else None,
        )


@receiver(pre_delete, sender=Examen)
def registrar_eliminacion_examen(sender, instance, **kwargs):
    """
    Registra cuando se elimina un examen y mueve el archivo a eliminados.
    
    Esta señal se ejecuta ANTES de eliminar un registro de Examen.
    Mueve el archivo físico a la carpeta de eliminados (en lugar de borrarlo)
    para mantener un historial de documentos eliminados.
    
    Args:
        sender: El modelo que envió la señal (Examen)
        instance: La instancia del examen que se va a eliminar
        **kwargs: Argumentos adicionales de la señal
    """
    # Obtener el usuario actual si está disponible
    usuario = None
    if hasattr(instance, '_current_user'):
        usuario = instance._current_user
    
    # Construir nombre descriptivo del documento
    nombre_doc = f"Examen - {instance.tipoEx_id.tipoExamen if instance.tipoEx_id else 'N/A'}"
    
    # Mover archivo a carpeta de eliminados antes de eliminar el registro
    # Esto permite mantener un historial de documentos eliminados
    archivo_ruta_historial = None
    if instance.rutaDoc and instance.rutaDoc.name:
        from .models import mover_archivo_a_eliminados
        archivo_ruta_historial = mover_archivo_a_eliminados(
            instance.rutaDoc,
            instance.personal_id.rut,
            nombre_doc
        )
        # Si no se pudo mover, usar la ruta original como fallback
        if not archivo_ruta_historial:
            archivo_ruta_historial = instance.rutaDoc.name
    
    HistorialDocumentoPersonal.registrar(
        personal=instance.personal_id,
        tipo_documento='EXAMEN',
        accion='DOCUMENTO_ELIMINADO',
        nombre_documento=nombre_doc,
        descripcion=f"Examen eliminado",
        usuario=usuario,
        archivo_ruta=archivo_ruta_historial,
    )

