# ============================================================================
# FUNCIONES HELPER PARA CREAR Y GESTIONAR NOTIFICACIONES
# ============================================================================
# Este módulo contiene funciones utilitarias para crear y gestionar notificaciones
# en el sistema, incluyendo funciones para crear notificaciones por tipo, por usuario,
# y para obtener/contar notificaciones no leídas.
# ============================================================================

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
    
    Busca qué roles tienen habilitado el tipo de notificación y crea notificaciones
    para todos los usuarios activos con esos roles. Si se especifican usuarios
    específicos, solo se notifica a esos usuarios.
    
    Args:
        codigo_tipo (str): Código del tipo de notificación (ej: 'RRHH_PERSONAL_ACTIVADO')
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación
        datos_adicionales (dict, optional): Diccionario con datos adicionales en formato JSON
        prioridad (str, optional): Prioridad de la notificación. Si no se especifica,
                                   usa la prioridad por defecto del tipo de notificación
        usuarios_especificos (list, optional): Lista de usuarios específicos a notificar.
                                               Si se especifica, solo se notifica a estos usuarios
                                               y se ignora la configuración por roles
                                               
    Returns:
        list: Lista de objetos Notificacion creados. Lista vacía si el tipo no existe
              o está inactivo, o si no se encontraron usuarios destinatarios.
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
        usuario (User|int): Usuario destinatario (objeto User o ID de usuario)
        codigo_tipo (str): Código del tipo de notificación
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación
        datos_adicionales (dict, optional): Diccionario con datos adicionales en formato JSON
        prioridad (str, optional): Prioridad de la notificación. Si no se especifica,
                                   usa la prioridad por defecto del tipo de notificación
                                   
    Returns:
        Notificacion|None: Objeto Notificacion creado, o None si el tipo no existe,
                          está inactivo, o el usuario no existe.
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
        usuario (User|int): Usuario (objeto User o ID de usuario)
        limit (int, optional): Límite máximo de resultados a retornar
        
    Returns:
        QuerySet: QuerySet de notificaciones no leídas y no archivadas,
                 ordenadas por fecha de creación descendente. QuerySet vacío
                 si el usuario no existe.
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
        usuario (User|int): Usuario (objeto User o ID de usuario)
        
    Returns:
        int: Número de notificaciones no leídas y no archivadas del usuario.
             Retorna 0 si el usuario no existe.
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

