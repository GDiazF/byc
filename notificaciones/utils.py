"""
Funciones helper para crear y gestionar notificaciones.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from .models import TipoNotificacion, Notificacion, ConfiguracionNotificacionRol
from gen_permissions.models import UserProfile


def crear_notificacion_por_tipo(
    codigo_tipo,
    titulo,
    mensaje,
    datos_adicionales=None,
    prioridad=None,
    usuarios_especificos=None
):
    """
    Crea notificaciones para usuarios basándose en el tipo de notificación y roles.
    
    Args:
        codigo_tipo: Código del tipo de notificación (ej: 'RRHH_PERSONAL_ACTIVADO')
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        datos_adicionales: Diccionario con datos adicionales (opcional)
        prioridad: Prioridad de la notificación (opcional, usa la del tipo si no se especifica)
        usuarios_especificos: Lista de usuarios específicos a notificar (opcional)
                              Si se especifica, solo se notifica a estos usuarios
    
    Returns:
        Lista de notificaciones creadas
    """
    try:
        tipo_notificacion = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
    except TipoNotificacion.DoesNotExist:
        # Si el tipo no existe o está inactivo, no crear notificaciones
        return []
    
    # Determinar prioridad
    if prioridad is None:
        prioridad = tipo_notificacion.prioridad
    
    # Determinar usuarios destinatarios
    usuarios_destinatarios = set()
    
    if usuarios_especificos:
        # Si se especifican usuarios, solo notificar a esos
        usuarios_destinatarios = set(usuarios_especificos)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Usando usuarios específicos: {len(usuarios_destinatarios)} usuarios")
    else:
        # Buscar usuarios con roles que tienen este tipo de notificación habilitado
        configuraciones = ConfiguracionNotificacionRol.objects.filter(
            tipo_notificacion=tipo_notificacion,
            activo=True
        ).select_related('rol')
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Buscando configuraciones para tipo {codigo_tipo}: {configuraciones.count()} configuraciones encontradas")
        
        for config in configuraciones:
            # Obtener todos los usuarios con este rol
            usuarios_con_rol = UserProfile.objects.filter(
                rol=config.rol,
                user__is_active=True
            ).select_related('user')
            
            logger.info(f"Rol {config.rol.nombre}: {usuarios_con_rol.count()} usuarios activos")
            
            for user_profile in usuarios_con_rol:
                usuarios_destinatarios.add(user_profile.user)
        
        logger.info(f"Total de usuarios destinatarios encontrados: {len(usuarios_destinatarios)}")
        if len(usuarios_destinatarios) == 0:
            logger.warning(f"⚠ No se encontraron usuarios con roles configurados para el tipo de notificación {codigo_tipo}")
    
    # Crear notificaciones para cada usuario
    notificaciones_creadas = []
    datos_adicionales = datos_adicionales or {}
    
    for usuario in usuarios_destinatarios:
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales,
            prioridad=prioridad
        )
        notificaciones_creadas.append(notificacion)
    
    return notificaciones_creadas


def crear_notificacion_para_usuario(
    usuario,
    codigo_tipo,
    titulo,
    mensaje,
    datos_adicionales=None,
    prioridad=None
):
    """
    Crea una notificación para un usuario específico.
    
    Args:
        usuario: Usuario destinatario (User o ID)
        codigo_tipo: Código del tipo de notificación
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        datos_adicionales: Diccionario con datos adicionales (opcional)
        prioridad: Prioridad de la notificación (opcional)
    
    Returns:
        Notificación creada o None si el tipo no existe
    """
    try:
        tipo_notificacion = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
    except TipoNotificacion.DoesNotExist:
        return None
    
    if isinstance(usuario, int):
        try:
            usuario = User.objects.get(pk=usuario)
        except User.DoesNotExist:
            return None
    
    if prioridad is None:
        prioridad = tipo_notificacion.prioridad
    
    notificacion = Notificacion.objects.create(
        usuario=usuario,
        tipo_notificacion=tipo_notificacion,
        titulo=titulo,
        mensaje=mensaje,
        datos_adicionales=datos_adicionales or {},
        prioridad=prioridad
    )
    
    return notificacion


def obtener_notificaciones_no_leidas(usuario, limit=None):
    """
    Obtiene las notificaciones no leídas de un usuario.
    
    Args:
        usuario: Usuario (User o ID)
        limit: Límite de resultados (opcional)
    
    Returns:
        QuerySet de notificaciones no leídas
    """
    if isinstance(usuario, int):
        try:
            usuario = User.objects.get(pk=usuario)
        except User.DoesNotExist:
            return Notificacion.objects.none()
    
    queryset = Notificacion.objects.filter(
        usuario=usuario,
        leida=False,
        archivada=False
    ).select_related('tipo_notificacion').order_by('-fecha_creacion')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset


def contar_notificaciones_no_leidas(usuario):
    """
    Cuenta las notificaciones no leídas de un usuario.
    
    Args:
        usuario: Usuario (User o ID)
    
    Returns:
        Número de notificaciones no leídas
    """
    if isinstance(usuario, int):
        try:
            usuario = User.objects.get(pk=usuario)
        except User.DoesNotExist:
            return 0
    
    return Notificacion.objects.filter(
        usuario=usuario,
        leida=False,
        archivada=False
    ).count()

