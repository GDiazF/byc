# ============================================================================
# MODELOS PARA EL SISTEMA DE NOTIFICACIONES
# ============================================================================
# Este módulo define los modelos necesarios para gestionar notificaciones:
# - TipoNotificacion: Catálogo de tipos de notificaciones disponibles
# - Notificacion: Notificaciones individuales para usuarios
# - ConfiguracionNotificacionRol: Configuración de qué notificaciones recibe cada rol
# ============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from gen_permissions.models import Rol


class TipoNotificacion(models.Model):
    """
    Catálogo de tipos de notificaciones disponibles en el sistema.
    
    Cada tipo de notificación tiene un código único que se usa para identificarlo
    y crear notificaciones del mismo tipo. Los tipos definen la categoría, prioridad
    por defecto y templates opcionales para título y mensaje.
    
    Ejemplos de códigos:
    - RRHH_PERSONAL_ACTIVADO
    - RRHH_LICENCIA_MEDICA_CREADA
    - MAQUINARIAS_EQUIPO_ACTIVADO
    - PLANIFICACION_FAENA_CREADA
    """
    
    CATEGORIA_CHOICES = [
        ('RRHH', 'Recursos Humanos'),
        ('MAQUINARIAS', 'Maquinarias'),
        ('PLANIFICACION', 'Planificación'),
        ('GENERAL', 'General'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA', 'Baja'),
    ]
    
    codigo = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Código',
        help_text='Código único del tipo de notificación (ej: RRHH_PERSONAL_ACTIVADO)'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre descriptivo del tipo de notificación'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de cuándo se genera esta notificación'
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoría',
        help_text='Categoría a la que pertenece esta notificación'
    )
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='MEDIA',
        verbose_name='Prioridad',
        help_text='Prioridad por defecto de las notificaciones de este tipo'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si este tipo de notificación está activo y puede generar notificaciones'
    )
    template_titulo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Template de Título',
        help_text='Template para el título (puede usar variables como {nombre}, {fecha})'
    )
    template_mensaje = models.TextField(
        blank=True,
        verbose_name='Template de Mensaje',
        help_text='Template para el mensaje (puede usar variables como {nombre}, {fecha})'
    )
    
    class Meta:
        verbose_name = "Tipo de Notificación"
        verbose_name_plural = "Tipos de Notificaciones"
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.categoria} - {self.nombre}"


class ConfiguracionNotificacionRol(models.Model):
    """
    Configuración de qué tipos de notificaciones puede recibir cada rol.
    
    Cuando se crea una notificación de un tipo específico, se busca qué roles
    tienen habilitado ese tipo y se crean notificaciones para todos los usuarios
    activos con esos roles. Esto permite controlar quién recibe qué tipo de
    notificaciones según su rol en el sistema.
    """
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='configuraciones_notificaciones',
        verbose_name='Rol',
        help_text='Rol al que se aplica esta configuración'
    )
    tipo_notificacion = models.ForeignKey(
        TipoNotificacion,
        on_delete=models.CASCADE,
        related_name='configuraciones_roles',
        verbose_name='Tipo de Notificación',
        help_text='Tipo de notificación que puede recibir este rol'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si este rol puede recibir notificaciones de este tipo'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Modificación'
    )
    
    class Meta:
        verbose_name = "Configuración de Notificación por Rol"
        verbose_name_plural = "Configuraciones de Notificaciones por Rol"
        unique_together = ['rol', 'tipo_notificacion']
        ordering = ['rol', 'tipo_notificacion']
    
    def __str__(self):
        return f"{self.rol.nombre} - {self.tipo_notificacion.nombre}"


class Notificacion(models.Model):
    """
    Notificaciones individuales para usuarios específicos.
    
    Cada notificación está asociada a un usuario y un tipo de notificación.
    Contiene el título, mensaje, metadatos adicionales y estado de lectura/archivado.
    Las notificaciones se ordenan por fecha de creación descendente y tienen
    índices optimizados para consultas frecuentes.
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario',
        help_text='Usuario destinatario de la notificación'
    )
    tipo_notificacion = models.ForeignKey(
        TipoNotificacion,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Tipo de Notificación',
        help_text='Tipo de notificación'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título de la notificación'
    )
    mensaje = models.TextField(
        verbose_name='Mensaje',
        help_text='Mensaje completo de la notificación'
    )
    datos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos Adicionales',
        help_text='Datos adicionales en formato JSON (IDs relacionados, URLs, etc.)'
    )
    leida = models.BooleanField(
        default=False,
        verbose_name='Leída',
        help_text='Indica si el usuario ha leído esta notificación'
    )
    fecha_leida = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Lectura',
        help_text='Fecha y hora en que el usuario leyó la notificación'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación',
        db_index=True
    )
    prioridad = models.CharField(
        max_length=10,
        choices=TipoNotificacion.PRIORIDAD_CHOICES,
        default='MEDIA',
        verbose_name='Prioridad',
        help_text='Prioridad de la notificación'
    )
    archivada = models.BooleanField(
        default=False,
        verbose_name='Archivada',
        help_text='Indica si la notificación ha sido archivada por el usuario'
    )
    fecha_archivada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Archivado'
    )
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'leida', '-fecha_creacion']),
            models.Index(fields=['usuario', 'archivada', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
    
    def marcar_como_leida(self):
        """
        Marca la notificación como leída.
        
        Actualiza el estado de lectura y guarda la fecha de lectura.
        Solo marca como leída si no estaba ya leída.
        """
        if not self.leida:
            self.leida = True
            self.fecha_leida = timezone.now()
            self.save(update_fields=['leida', 'fecha_leida'])
    
    def archivar(self):
        """
        Archiva la notificación.
        
        Marca la notificación como archivada y guarda la fecha de archivado.
        Solo archiva si no estaba ya archivada.
        """
        if not self.archivada:
            self.archivada = True
            self.fecha_archivada = timezone.now()
            self.save(update_fields=['archivada', 'fecha_archivada'])
    
    def desarchivar(self):
        """
        Desarchiva la notificación.
        
        Remueve el estado de archivado y limpia la fecha de archivado.
        Solo desarchiva si estaba archivada.
        """
        if self.archivada:
            self.archivada = False
            self.fecha_archivada = None
            self.save(update_fields=['archivada', 'fecha_archivada'])
