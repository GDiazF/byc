from django.db import models
from gen_settings.models import Empresa
from rrhh_personal.models import Personal
from django.contrib.auth.models import User
from datetime import datetime
import os
import re
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Q, CheckConstraint

# Create your models here.

# ============================================================================
# FUNCIONES PARA RUTAS DE DOCUMENTOS DE MAQUINARIAS
# ============================================================================

def obtener_ruta_documento_maquinaria(instance, filename):
    """
    Función para determinar la ruta donde se guardarán los documentos de maquinarias.
    La estructura será: Documentacion_Maquinarias/EQUIPO_ID/TIPO_DOCUMENTO/archivo
    """
    extension = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Usar el nombre de la clase para evitar referencias forward
    class_name = instance.__class__.__name__
    
    if class_name == 'DocumentoMaquinaria':
        equipo_id = instance.equipo_id.equipo_id
        tipo_doc = instance.tipo_documento_id.nombre.replace(' ', '_').lower()
        nombre_archivo = f"{tipo_doc}_{timestamp}{extension}"
        return os.path.join('Documentacion_Maquinarias', str(equipo_id), tipo_doc, nombre_archivo)
    elif class_name == 'HistorialDocumentoMaquinaria':
        equipo_id = instance.equipo_id.equipo_id
        tipo_doc = instance.tipo_documento_nombre.replace(' ', '_').lower()
        nombre_archivo = f"{tipo_doc}_{timestamp}_historial{extension}"
        return os.path.join('Documentacion_Maquinarias', str(equipo_id), 'Historial', tipo_doc, nombre_archivo)
    
    return os.path.join('Documentacion_Maquinarias', 'Otros', filename)

def mover_archivo_a_eliminados_maquinaria(archivo_field, equipo_id, nombre_documento):
    """
    Mueve un archivo de maquinaria a la carpeta de eliminados en lugar de eliminarlo.
    Estructura: Documentacion_Eliminada_Maquinarias/EQUIPO_ID/EQUIPO_ID_nombre_documento.pdf
    
    Args:
        archivo_field: Campo FileField del modelo
        equipo_id: ID del equipo (int o string)
        nombre_documento: Nombre descriptivo del documento (ej: "Permiso de Circulación")
    
    Returns:
        str: Ruta relativa del archivo movido, o None si hubo error
    """
    if not archivo_field or not archivo_field.name:
        return None
    
    try:
        from django.conf import settings
        import shutil
        
        # Obtener rutas
        archivo_original_path = archivo_field.path
        if not os.path.exists(archivo_original_path):
            return None
        
        # Crear nombre de archivo limpio (sin caracteres especiales)
        # Formato: EQUIPO_ID_nombre_documento.pdf
        nombre_limpio = nombre_documento.lower().replace(' ', '_').replace('/', '_')
        # Obtener extensión del archivo original
        extension = os.path.splitext(archivo_field.name)[1]
        nombre_archivo_final = f"{equipo_id}_{nombre_limpio}{extension}"
        
        # Ruta destino: Documentacion_Eliminada_Maquinarias/EQUIPO_ID/EQUIPO_ID_nombre_documento.pdf
        carpeta_eliminados = os.path.join(settings.MEDIA_ROOT, 'Documentacion_Eliminada_Maquinarias', str(equipo_id))
        os.makedirs(carpeta_eliminados, exist_ok=True)
        
        ruta_destino = os.path.join(carpeta_eliminados, nombre_archivo_final)
        
        # Si ya existe un archivo con ese nombre, agregar timestamp
        if os.path.exists(ruta_destino):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            nombre_base, ext = os.path.splitext(nombre_archivo_final)
            nombre_archivo_final = f"{nombre_base}_{timestamp}{ext}"
            ruta_destino = os.path.join(carpeta_eliminados, nombre_archivo_final)
        
        # Mover el archivo
        shutil.move(archivo_original_path, ruta_destino)
        
        # Retornar ruta relativa para guardar en historial
        ruta_relativa = os.path.join('Documentacion_Eliminada_Maquinarias', str(equipo_id), nombre_archivo_final)
        return ruta_relativa
        
    except Exception as e:
        # Si falla el movimiento, intentar eliminar normalmente
        print(f"Error al mover archivo a eliminados: {str(e)}")
        try:
            archivo_field.delete(save=False)
        except:
            pass
        return None


class OverwriteStorage(FileSystemStorage):
    """
    Storage class para desarrollo local que sobrescribe archivos existentes
    """
    def get_available_name(self, name, max_length=None):
        # Eliminar archivo existente si existe
        if self.exists(name):
            self.delete(name)
        return name

class TipoEquipo(models.Model):
    tipoEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoEquipo = models.CharField(max_length=100, null=False, blank=False)
    siglaEquipo = models.CharField(max_length=3, null=False, blank=False)

    def __str__(self):
        return self.tipoEquipo

class MarcaEquipo(models.Model):
    marcaEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    marcaEquipo = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.marcaEquipo

class ModeloEquipo(models.Model):
    modeloEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    modeloEquipo = models.CharField(max_length=100, null=False, blank=False)
    tipoEquipo_id = models.ForeignKey(TipoEquipo, on_delete=models.CASCADE, db_column='tipoEquipo_id', null=True, blank=True)
    marcaEquipo_id = models.ForeignKey(MarcaEquipo, on_delete=models.CASCADE, db_column='marcaEquipo_id', null=True, blank=True)

    class Meta:
        verbose_name = 'Modelo de Equipo'
        verbose_name_plural = 'Modelos de Equipo'
        # Un modelo es único para cada combinación de tipo, marca y nombre
        unique_together = [['tipoEquipo_id', 'marcaEquipo_id', 'modeloEquipo']]

    def __str__(self):
        return f"{self.modeloEquipo} ({self.marcaEquipo_id.marcaEquipo})"

class Equipo(models.Model):
    equipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    empresa_id = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column='empresa_id', null=False, blank=False)
    modeloEquipo_id = models.ForeignKey(ModeloEquipo, on_delete=models.CASCADE, db_column='modeloEquipo_id', null=False, blank=False)
    codigoInterno = models.CharField(max_length=100, null=False, blank=False)
    patente = models.CharField(max_length=100, null=True, blank=True)
    horometro = models.IntegerField(null=True, blank=True)
    odometro = models.IntegerField(null=True, blank=True)
    horometroSuperEstructural = models.IntegerField(null=True, blank=True)
    nombreEquipo = models.CharField(max_length=100, null=False, blank=True)  # Se genera automáticamente
    activo = models.BooleanField(default=True, null=False, blank=False)
    
    class Meta:
        # El código interno debe ser único POR TIPO de equipo
        # Ahora el tipo se obtiene del modelo, así que la restricción es por modelo + código
        unique_together = [['modeloEquipo_id', 'codigoInterno']]
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        # Permisos personalizados para acciones específicas dentro del modelo Equipo
        permissions = [
            ('desactivar_equipo', 'Puede desactivar equipos'),
            ('activar_equipo', 'Puede activar equipos'),
            ('exportar_equipos', 'Puede exportar datos de equipos'),
            ('ver_historial_equipo', 'Puede ver historial completo de equipos'),
        ]

    def save(self, *args, **kwargs):
        """
        Genera automáticamente el nombreEquipo basado en:
        - siglaEquipo del TipoEquipo (obtenido del modelo)
        - codigoInterno
        - patente (opcional)
        
        Formato: {siglaEquipo}{codigoInterno} - {patente}
        Ejemplo: GT01 - KJL556
        """
        # Obtener la sigla del tipo de equipo a través del modelo
        sigla = self.modeloEquipo_id.tipoEquipo_id.siglaEquipo if self.modeloEquipo_id and self.modeloEquipo_id.tipoEquipo_id else ''
        
        # Construir el nombre base con sigla y código interno
        nombre_base = f"{sigla}{self.codigoInterno}"
        
        # Agregar patente si existe
        if self.patente and self.patente.strip():
            self.nombreEquipo = f"{nombre_base} - {self.patente.strip()}"
        else:
            self.nombreEquipo = nombre_base
        
        super().save(*args, **kwargs)
    
    @property
    def tipoEquipo(self):
        """Propiedad para acceder al tipo de equipo a través del modelo"""
        return self.modeloEquipo_id.tipoEquipo_id
    
    @property
    def marcaEquipo(self):
        """Propiedad para acceder a la marca a través del modelo"""
        return self.modeloEquipo_id.marcaEquipo_id

    def __str__(self):
        return self.nombreEquipo


class Seccion(models.Model):
    """Secciones/sistemas de un equipo (motor, radiador, sistema hidráulico, etc.)"""
    seccion_id = models.AutoField(primary_key=True, null=False, blank=False)
    nombre = models.CharField(max_length=100, unique=True, null=False, blank=False)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maquinarias_seccion'
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class EstadoOT(models.Model):
    """Estados de una Orden de Trabajo"""
    estadoOT_id = models.AutoField(primary_key=True, null=False, blank=False)
    nombre = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    color = models.CharField(max_length=20, default='secondary', verbose_name='Color (Bootstrap)')
    activo = models.BooleanField(default=True, null=False, blank=False, verbose_name='Activo')
    orden = models.IntegerField(default=0, verbose_name='Orden de Visualización')
    
    class Meta:
        db_table = 'maquinarias_estadoot'
        verbose_name = 'Estado de OT'
        verbose_name_plural = 'Estados de OT'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class TipoReparacion(models.Model):
    """Tipos de reparación para cada sección"""
    tipoReparacion_id = models.AutoField(primary_key=True, null=False, blank=False)
    seccion_id = models.ForeignKey(Seccion, on_delete=models.CASCADE, db_column='seccion_id', related_name='tipos_reparacion', null=False, blank=False)
    nombre = models.CharField(max_length=200, null=False, blank=False)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maquinarias_tiporeparacion'
        verbose_name = 'Tipo de Reparación'
        verbose_name_plural = 'Tipos de Reparación'
        unique_together = [['seccion_id', 'nombre']]
        ordering = ['seccion_id', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.seccion_id.nombre})"


class PautaMantenimientoPreventivo(models.Model):
    """Pauta de mantenimiento preventivo para un modelo de equipo"""
    pauta_id = models.AutoField(primary_key=True, null=False, blank=False)
    modeloEquipo_id = models.ForeignKey(ModeloEquipo, on_delete=models.CASCADE, db_column='modeloEquipo_id', related_name='pautas_mantenimiento', null=False, blank=False)
    nombre = models.CharField(max_length=200, null=False, blank=False)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True, null=False, blank=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maquinarias_pautamantenimientopreventivo'
        verbose_name = 'Pauta de Mantenimiento Preventivo'
        verbose_name_plural = 'Pautas de Mantenimiento Preventivo'
        ordering = ['modeloEquipo_id', 'nombre']
        # Permisos personalizados para acciones específicas dentro del modelo PautaMantenimientoPreventivo
        permissions = [
            ('desactivar_pauta', 'Puede desactivar pautas de mantenimiento'),
            ('activar_pauta', 'Puede activar pautas de mantenimiento'),
            ('exportar_pautas', 'Puede exportar datos de pautas de mantenimiento'),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.modeloEquipo_id}"


class ItemPauta(models.Model):
    """
    Relación entre una pauta, una sección y sus tipos de reparación.
    
    NOTA: Los estados de las secciones NO se guardan aquí, sino en ItemSeccionOT
    (específico de cada OT). Cada OT tiene sus propios estados independientes.
    """
    itemPauta_id = models.AutoField(primary_key=True, null=False, blank=False)
    pauta_id = models.ForeignKey(PautaMantenimientoPreventivo, on_delete=models.CASCADE, db_column='pauta_id', related_name='items', null=False, blank=False)
    seccion_id = models.ForeignKey(Seccion, on_delete=models.CASCADE, db_column='seccion_id', related_name='items_pauta', null=False, blank=False)
    tipos_reparacion = models.ManyToManyField(TipoReparacion, related_name='items_pauta')
    # NOTA: estado_seccion_id fue eliminado - los estados se guardan en ItemSeccionOT (por OT)
    
    class Meta:
        db_table = 'maquinarias_itempauta'
        verbose_name = 'Item de Pauta'
        verbose_name_plural = 'Items de Pauta'
        unique_together = [['pauta_id', 'seccion_id']]
    
    def __str__(self):
        return f"{self.pauta_id.nombre} - {self.seccion_id.nombre}"


# ============================================================================
# MODELOS PARA DOCUMENTACIÓN DE MAQUINARIAS
# ============================================================================

class TipoDocumentoMaquinaria(models.Model):
    """Tipos de documentos que puede tener una maquinaria (revisión técnica, seguro, permiso de circulación, etc.)"""
    tipoDocumento_id = models.AutoField(primary_key=True, null=False, blank=False)
    nombre = models.CharField(max_length=100, unique=True, null=False, blank=False, verbose_name='Nombre del Documento')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    requiere_fecha_vencimiento = models.BooleanField(
        default=False, 
        null=False, 
        blank=False,
        verbose_name='Requiere Fecha de Vencimiento',
        help_text='Si está marcado, este tipo de documento requerirá una fecha de vencimiento al subirlo'
    )
    activo = models.BooleanField(default=True, null=False, blank=False, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maquinarias_tipodocumento'
        verbose_name = 'Tipo de Documento de Maquinaria'
        verbose_name_plural = 'Tipos de Documentos de Maquinaria'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class DocumentoMaquinaria(models.Model):
    """Documentos actuales de una maquinaria"""
    documento_id = models.AutoField(primary_key=True, null=False, blank=False)
    equipo_id = models.ForeignKey(
        Equipo, 
        on_delete=models.CASCADE, 
        db_column='equipo_id', 
        null=False, 
        blank=False,
        related_name='documentos'
    )
    tipo_documento_id = models.ForeignKey(
        TipoDocumentoMaquinaria,
        on_delete=models.CASCADE,
        db_column='tipo_documento_id',
        null=False,
        blank=False,
        related_name='documentos',
        verbose_name='Tipo de Documento'
    )
    archivo = models.FileField(
        upload_to=obtener_ruta_documento_maquinaria,
        storage=OverwriteStorage(),
        null=False,
        blank=False,
        verbose_name='Archivo'
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha en que vence el documento (si aplica)'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        db_table = 'maquinarias_documento'
        verbose_name = 'Documento de Maquinaria'
        verbose_name_plural = 'Documentos de Maquinaria'
        # Un equipo solo puede tener un documento activo de cada tipo
        unique_together = [['equipo_id', 'tipo_documento_id']]
        ordering = ['tipo_documento_id__nombre']
        # Permisos personalizados para acciones específicas dentro del modelo DocumentoMaquinaria
        permissions = [
            ('subir_documento', 'Puede subir documentos de maquinarias'),
            ('eliminar_documento', 'Puede eliminar documentos de maquinarias'),
            ('ver_historial_documentos', 'Puede ver historial de documentos'),
        ]
    
    @property
    def esta_vencido(self):
        """Determina si el documento está vencido"""
        from datetime import date
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < date.today()
    
    @property
    def esta_por_vencer(self):
        """Determina si el documento está por vencer (menos de 30 días)"""
        from datetime import date, timedelta
        if not self.fecha_vencimiento:
            return False
        dias_restantes = (self.fecha_vencimiento - date.today()).days
        return 0 <= dias_restantes <= 30
    
    def __str__(self):
        return f"{self.tipo_documento_id.nombre} - {self.equipo_id.nombreEquipo}"


class HistorialDocumentoMaquinaria(models.Model):
    """Historial de documentos reemplazados de una maquinaria"""
    historial_id = models.AutoField(primary_key=True, null=False, blank=False)
    equipo_id = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        db_column='equipo_id',
        null=False,
        blank=False,
        related_name='historial_documentos'
    )
    tipo_documento_id = models.ForeignKey(
        TipoDocumentoMaquinaria,
        on_delete=models.SET_NULL,
        db_column='tipo_documento_id',
        null=True,
        blank=True,
        related_name='historial',
        verbose_name='Tipo de Documento'
    )
    tipo_documento_nombre = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        verbose_name='Tipo de Documento (Nombre)',
        help_text='Nombre del tipo de documento al momento de archivarlo'
    )
    archivo = models.FileField(
        upload_to=obtener_ruta_documento_maquinaria,
        null=False,
        blank=False,
        verbose_name='Archivo'
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento'
    )
    fecha_subida_original = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Subida Original',
        help_text='Fecha en que se subió originalmente este documento'
    )
    fecha_reemplazo = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Reemplazo',
        help_text='Fecha en que este documento fue reemplazado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        db_table = 'maquinarias_historialdocumento'
        verbose_name = 'Historial de Documento de Maquinaria'
        verbose_name_plural = 'Historial de Documentos de Maquinaria'
        ordering = ['-fecha_reemplazo']
    
    def __str__(self):
        return f"{self.tipo_documento_nombre} - {self.equipo_id.nombreEquipo} (Historial)"


# ============================================================================
# MODELOS PARA ORDEN DE TRABAJO (OT)
# ============================================================================

class TipoMantenimiento(models.Model):
    """Tipos de mantenimiento (Preventivo, Correctivo, etc.)"""
    tipoMantenimiento_id = models.AutoField(primary_key=True, null=False, blank=False)
    nombre = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, null=False, blank=False, verbose_name='Activo')
    
    class Meta:
        db_table = 'maquinarias_tipomantenimiento'
        verbose_name = 'Tipo de Mantenimiento'
        verbose_name_plural = 'Tipos de Mantenimiento'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class EstadoEquipo(models.Model):
    """Estados de un equipo durante una OT"""
    estadoEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    nombre = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    color = models.CharField(max_length=20, default='secondary', verbose_name='Color (Bootstrap)')
    activo = models.BooleanField(default=True, null=False, blank=False, verbose_name='Activo')
    orden = models.IntegerField(default=0, verbose_name='Orden de Visualización')
    
    class Meta:
        db_table = 'maquinarias_estadoequipo'
        verbose_name = 'Estado de Equipo'
        verbose_name_plural = 'Estados de Equipo'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


# ============================================================================
# MODELOS PARA ESTADOS DINÁMICOS DEL CALENDARIO DE MAQUINARIAS
# ============================================================================

class EstadoCalendarioEquipo(models.Model):
    """
    Estado configurable para el calendario de maquinarias. Ejemplos: 'Disponible',
    'En Mantenimiento', 'En Reparación', 'Fuera de Servicio', etc.
    Similar al modelo Estado de operaciones pero para equipos.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    nombre_corto = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Nombre corto para mostrar en el calendario (ej: 'DISP' para 'Disponible')",
        verbose_name='Nombre Corto'
    )
    color = models.CharField(
        max_length=7,
        default='#000000',
        help_text="Color HEX para el texto del estado (ej: #0EA5E9)",
        verbose_name='Color Texto'
    )
    background_color = models.CharField(
        max_length=7,
        default='#FFFFFF',
        help_text="Color HEX para el fondo del estado (ej: #0EA5E9)",
        verbose_name='Color Fondo'
    )
    prioridad = models.PositiveIntegerField(
        default=10,
        help_text="Mayor número => mayor prioridad si hay conflicto",
        verbose_name='Prioridad'
    )
    es_bloqueante = models.BooleanField(
        default=False,
        help_text="Si es True, este estado siempre sobreescribe cualquier otro que coincida",
        verbose_name='Es Bloqueante'
    )
    es_predeterminado = models.BooleanField(
        default=False,
        help_text="Si es True, este será el estado por defecto cuando no haya OT (Disponible)",
        verbose_name='Es Predeterminado'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        db_table = 'maquinarias_estadocalendarioequipo'
        ordering = ["-activo", "-prioridad", "nombre"]
        verbose_name = "Estado Calendario Equipo"
        verbose_name_plural = "Estados Calendario Equipo"
        constraints = [
            CheckConstraint(
                check=Q(es_predeterminado=False) | Q(es_predeterminado=True),
                name='solo_un_estado_predeterminado_equipo'
            )
        ]

    def clean(self):
        """Validar que solo haya un estado predeterminado"""
        if self.es_predeterminado:
            # Verificar si ya existe otro estado predeterminado
            otros_predeterminados = EstadoCalendarioEquipo.objects.filter(
                es_predeterminado=True,
                activo=True
            ).exclude(pk=self.pk)
            
            if otros_predeterminados.exists():
                raise ValidationError(
                    'Ya existe otro estado marcado como predeterminado. '
                    'Solo puede haber un estado predeterminado a la vez.'
                )

    def save(self, *args, **kwargs):
        """Asegurar que solo haya un estado predeterminado"""
        if self.es_predeterminado:
            # Desmarcar otros estados predeterminados
            EstadoCalendarioEquipo.objects.filter(
                es_predeterminado=True
            ).exclude(pk=self.pk).update(es_predeterminado=False)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class EstadoFuenteEquipo(models.Model):
    """
    Mapea un EstadoCalendarioEquipo a una FUENTE EXTERNA de datos (OrdenTrabajo),
    para poder consultar si el equipo está en ese estado por rangos de fechas.
    
    La fuente principal será OrdenTrabajo.estado_equipo_id, donde cada estado
    de EstadoEquipo se mapea a un EstadoCalendarioEquipo.
    """
    estado_calendario = models.OneToOneField(
        EstadoCalendarioEquipo, 
        on_delete=models.CASCADE, 
        related_name="fuente",
        verbose_name='Estado Calendario'
    )
    estado_equipo = models.ForeignKey(
        EstadoEquipo,
        on_delete=models.CASCADE,
        related_name='fuentes_calendario',
        help_text="Estado de Equipo que se mapea a este estado del calendario",
        verbose_name='Estado Equipo'
    )
    # Filtro extra opcional como JSON para casos especiales (ej: tipo_mantenimiento='Preventivo')
    filtro_extra = models.JSONField(blank=True, null=True, verbose_name='Filtro Extra')

    class Meta:
        db_table = 'maquinarias_estadofuenteequipo'
        verbose_name = "Fuente de Estado Equipo"
        verbose_name_plural = "Fuentes de Estados Equipo"
        unique_together = [['estado_calendario', 'estado_equipo']]

    def __str__(self):
        return f"Fuente({self.estado_calendario.nombre}) → {self.estado_equipo.nombre}"


class EstadoManualEquipo(models.Model):
    """
    Permite asignar manualmente un estado a un equipo en un rango de fechas,
    independientemente de las OT.
    """
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='estados_manuales',
        verbose_name='Equipo'
    )
    estado = models.ForeignKey(
        EstadoCalendarioEquipo,
        on_delete=models.CASCADE,
        related_name='asignaciones_manuales',
        verbose_name='Estado'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha Fin')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')

    class Meta:
        db_table = 'maquinarias_estadomanualequipo'
        verbose_name = "Estado Manual Equipo"
        verbose_name_plural = "Estados Manuales Equipo"
        ordering = ['-fecha_creacion']

    def clean(self):
        """Validar que fecha_fin sea mayor o igual a fecha_inicio"""
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser mayor o igual a la fecha de inicio.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.equipo.nombreEquipo} - {self.estado.nombre} ({self.fecha_inicio} a {self.fecha_fin})"


# ============================================================================
# FUNCIONES PARA CALCULAR ESTADOS DEL CALENDARIO DE MAQUINARIAS
# ============================================================================

def obtener_estado_final_equipo_fecha(equipo, fecha):
    """
    Calcula el estado final de un equipo en una fecha específica,
    considerando todas las fuentes y prioridades.
    
    Orden de prioridad:
    1. Estados manuales (más alta prioridad)
    2. Estados de OT (basados en estado_equipo_id mapeado a EstadoCalendarioEquipo)
    3. Estado predeterminado "Disponible" si no hay OT
    
    Retorna una lista de estados cuando hay conflictos de prioridad.
    """
    from django.db.models import Q
    
    # 1. Buscar estados manuales activos
    estados_manuales = EstadoManualEquipo.objects.filter(
        equipo=equipo,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    ).select_related('estado').order_by('-estado__prioridad')
    
    if estados_manuales.exists():
        # Si hay estados bloqueantes, retornar el de mayor prioridad
        bloqueantes = [em for em in estados_manuales if em.estado.es_bloqueante]
        if bloqueantes:
            return [bloqueantes[0].estado]
        # Si no hay bloqueantes, retornar el de mayor prioridad
        return [estados_manuales.first().estado]
    
    # 2. Buscar estados de OT (basados en estado_equipo_id)
    estados_ot = []
    
    # Buscar OT activas que incluyan esta fecha
    ordenes_trabajo = OrdenTrabajo.objects.filter(
        equipo_id=equipo
    ).filter(
        Q(fecha_inicio__lte=fecha) & (
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha)
        )
    ).select_related('estado_equipo_id')
    
    for ot in ordenes_trabajo:
        if ot.estado_equipo_id:
            # Buscar el EstadoCalendarioEquipo mapeado a este EstadoEquipo
            fuente = EstadoFuenteEquipo.objects.filter(
                estado_equipo=ot.estado_equipo_id
            ).select_related('estado_calendario').first()
            
            if fuente and fuente.estado_calendario.activo:
                estados_ot.append(fuente.estado_calendario)
            else:
                # Si no hay mapeo, buscar un EstadoCalendarioEquipo con el mismo nombre
                # (fallback para compatibilidad)
                estado_calendario_directo = EstadoCalendarioEquipo.objects.filter(
                    nombre__iexact=ot.estado_equipo_id.nombre,
                    activo=True
                ).first()
                
                if estado_calendario_directo:
                    estados_ot.append(estado_calendario_directo)
    
    # 3. Resolver conflictos de prioridad
    todos_estados = []
    
    # Agregar estados de OT
    for estado in estados_ot:
        todos_estados.append({
            'estado': estado,
            'tipo': 'ot',
            'prioridad': estado.prioridad
        })
    
    if not todos_estados:
        # Si no hay OT, retornar estado predeterminado (Disponible)
        try:
            estado_predeterminado = EstadoCalendarioEquipo.objects.filter(
                activo=True,
                es_predeterminado=True
            ).first()
            
            if estado_predeterminado:
                return [estado_predeterminado]
            
            return []
        except:
            return []
    
    # Ordenar por prioridad (mayor número = mayor prioridad)
    todos_estados.sort(key=lambda x: x['prioridad'], reverse=True)
    
    # Si hay estados bloqueantes, solo retornar el de mayor prioridad
    bloqueantes = [x for x in todos_estados if x['estado'].es_bloqueante]
    if bloqueantes:
        return [bloqueantes[0]['estado']]
    
    # Obtener la prioridad más alta
    prioridad_maxima = todos_estados[0]['prioridad']
    
    # Retornar todos los estados que tengan la prioridad más alta
    estados_misma_prioridad = [
        x['estado'] for x in todos_estados 
        if x['prioridad'] == prioridad_maxima
    ]
    
    return estados_misma_prioridad


class OrdenTrabajo(models.Model):
    """Orden de Trabajo para mantenimiento de equipos"""
    
    ot_id = models.AutoField(primary_key=True, null=False, blank=False)
    folio = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name='Folio')
    equipo_id = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        db_column='equipo_id',
        null=False,
        blank=False,
        related_name='ordenes_trabajo',
        verbose_name='Equipo'
    )
    empresa_id = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        db_column='empresa_id',
        null=False,
        blank=False,
        related_name='ordenes_trabajo',
        verbose_name='Empresa'
    )
    
    # Campos automáticos del equipo (no editables, se copian al crear)
    horometro = models.IntegerField(null=True, blank=True, verbose_name='Horómetro')
    odometro = models.IntegerField(null=True, blank=True, verbose_name='Odómetro')
    horometro_superestructura = models.IntegerField(null=True, blank=True, verbose_name='Horómetro Superestructura')
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin')
    
    # Tipo de mantenimiento (ForeignKey)
    tipo_mantenimiento_id = models.ForeignKey(
        TipoMantenimiento,
        on_delete=models.CASCADE,
        db_column='tipo_mantenimiento_id',
        null=True,
        blank=True,
        related_name='ordenes_trabajo',
        verbose_name='Tipo de Mantenimiento'
    )
    
    # Si es preventivo, puede corresponder a una pauta
    corresponde_pauta = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        verbose_name='Corresponde a Pauta de Mantenimiento'
    )
    pauta_id = models.ForeignKey(
        PautaMantenimientoPreventivo,
        on_delete=models.SET_NULL,
        db_column='pauta_id',
        null=True,
        blank=True,
        related_name='ordenes_trabajo',
        verbose_name='Pauta de Mantenimiento'
    )
    
    # Estados (ForeignKeys)
    estado_ot_id = models.ForeignKey(
        EstadoOT,
        on_delete=models.CASCADE,
        db_column='estado_ot_id',
        null=True,
        blank=True,
        related_name='ordenes_trabajo',
        verbose_name='Estado de la OT'
    )
    estado_equipo_id = models.ForeignKey(
        EstadoEquipo,
        on_delete=models.CASCADE,
        db_column='estado_equipo_id',
        null=True,
        blank=True,
        related_name='ordenes_trabajo',
        verbose_name='Estado del Equipo'
    )
    
    # Personal asignado (muchos a muchos)
    personal_asignado = models.ManyToManyField(
        Personal,
        related_name='ordenes_trabajo',
        blank=True,
        verbose_name='Personal Asignado'
    )
    
    # Observaciones generales (bitácora principal)
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        db_table = 'maquinarias_ordentrabajo'
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Ordenes de Trabajo'
        ordering = ['-fecha_creacion']
        # Permisos personalizados para acciones específicas dentro del modelo OrdenTrabajo
        permissions = [
            ('cambiar_estado_ot', 'Puede cambiar el estado de órdenes de trabajo'),
            ('asignar_personal_ot', 'Puede asignar personal a órdenes de trabajo'),
            ('agregar_observacion_ot', 'Puede agregar observaciones a órdenes de trabajo'),
            ('generar_pdf_ot', 'Puede generar PDF de órdenes de trabajo'),
            ('ver_historial_ot', 'Puede ver historial completo de órdenes de trabajo'),
            ('exportar_ots', 'Puede exportar datos de órdenes de trabajo'),
        ]
    
    def __str__(self):
        # Si el folio ya tiene el prefijo OT-, mostrarlo tal cual, sino agregarlo
        folio_display = self.folio if self.folio.startswith('OT-') else f"OT-{self.folio}"
        return f"{folio_display} - {self.equipo_id.nombreEquipo}"
    
    def save(self, *args, **kwargs):
        """Genera el folio automáticamente si no existe"""
        if not self.folio:
            # Buscar el número más alto de los folios existentes con formato OT-{número}
            ultimo_numero = 0
            folios_existentes = OrdenTrabajo.objects.exclude(
                pk=self.pk if self.pk else None
            ).values_list('folio', flat=True)
            
            for folio in folios_existentes:
                # Intentar extraer el número del folio (formato OT-{número})
                match = re.match(r'^OT-(\d+)$', folio)
                if match:
                    numero = int(match.group(1))
                    if numero > ultimo_numero:
                        ultimo_numero = numero
                # También considerar folios que sean solo números (para compatibilidad)
                elif folio.isdigit():
                    numero = int(folio)
                    if numero > ultimo_numero:
                        ultimo_numero = numero
            
            # Si no se encontró ningún número válido, usar el conteo total de OTs como respaldo
            if ultimo_numero == 0:
                ultimo_numero = OrdenTrabajo.objects.exclude(
                    pk=self.pk if self.pk else None
                ).count()
            
            # Generar el siguiente número con formato OT-{número}
            siguiente_numero = ultimo_numero + 1
            self.folio = f"OT-{siguiente_numero}"
        super().save(*args, **kwargs)


class ItemSeccionOT(models.Model):
    """Items de secciones y tipos de reparación para una OT (cuando NO es pauta)"""
    
    itemSeccionOT_id = models.AutoField(primary_key=True, null=False, blank=False)
    ot_id = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        db_column='ot_id',
        null=False,
        blank=False,
        related_name='items_secciones',
        verbose_name='Orden de Trabajo'
    )
    seccion_id = models.ForeignKey(
        Seccion,
        on_delete=models.CASCADE,
        db_column='seccion_id',
        null=False,
        blank=False,
        related_name='items_ot',
        verbose_name='Sección'
    )
    tipos_reparacion = models.ManyToManyField(
        TipoReparacion,
        related_name='items_ot',
        verbose_name='Tipos de Reparación'
    )
    estado_seccion_id = models.ForeignKey(
        EstadoOT,
        on_delete=models.CASCADE,
        db_column='estado_seccion_id',
        null=True,
        blank=True,
        related_name='items_secciones_ot',
        verbose_name='Estado de la Sección'
    )
    
    class Meta:
        db_table = 'maquinarias_itemseccionot'
        verbose_name = 'Item Sección OT'
        verbose_name_plural = 'Items Secciones OT'
        unique_together = [['ot_id', 'seccion_id']]
        ordering = ['seccion_id__nombre']
    
    def __str__(self):
        return f"{self.ot_id.folio} - {self.seccion_id.nombre}"


class HistorialObservacionesOT(models.Model):
    """Historial de observaciones (bitácora) de una OT"""
    historial_id = models.AutoField(primary_key=True, null=False, blank=False)
    ot_id = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        db_column='ot_id',
        null=False,
        blank=False,
        related_name='historial_observaciones',
        verbose_name='Orden de Trabajo'
    )
    observacion = models.TextField(null=False, blank=False, verbose_name='Observación')
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observaciones_ot',
        verbose_name='Usuario'
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    
    class Meta:
        db_table = 'maquinarias_historialobservacionesot'
        verbose_name = 'Historial de Observación OT'
        verbose_name_plural = 'Historial de Observaciones OT'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.ot_id.folio} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


class HistorialOT(models.Model):
    """
    Registra todos los cambios y acciones realizadas en una OT.
    Permite auditoría completa de modificaciones y cambios de estado.
    """
    ACCION_CHOICES = [
        ('OT_CREADA', 'OT Creada'),
        ('OT_MODIFICADA', 'OT Modificada'),
        ('ESTADO_OT_CAMBIADO', 'Estado OT Cambiado'),
        ('ESTADO_EQUIPO_CAMBIADO', 'Estado Equipo Cambiado'),
        ('ESTADO_SECCION_CAMBIADO', 'Estado Sección Cambiado'),
        ('FECHA_INICIO_CAMBIADA', 'Fecha Inicio Cambiada'),
        ('FECHA_FIN_CAMBIADA', 'Fecha Fin Cambiada'),
        ('PERSONAL_ASIGNADO', 'Personal Asignado'),
        ('PERSONAL_ELIMINADO', 'Personal Eliminado'),
        ('OBSERVACION_AGREGADA', 'Observación Agregada'),
    ]
    
    ot = models.ForeignKey(
        OrdenTrabajo, 
        on_delete=models.CASCADE, 
        related_name="historial",
        db_index=True,
        verbose_name='Orden de Trabajo'
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha y Hora')
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que realizó la acción",
        verbose_name='Usuario'
    )
    accion = models.CharField(
        max_length=50,
        choices=ACCION_CHOICES,
        help_text="Tipo de acción realizada",
        verbose_name='Acción'
    )
    descripcion = models.TextField(
        help_text="Descripción detallada del cambio",
        verbose_name='Descripción'
    )
    datos_previos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado anterior antes del cambio (JSON)",
        verbose_name='Datos Previos'
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado nuevo después del cambio (JSON)",
        verbose_name='Datos Nuevos'
    )
    
    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "Historial de OT"
        verbose_name_plural = "Historial de OTs"
        db_table = 'maquinarias_historialot'
        indexes = [
            models.Index(fields=["ot", "-fecha_hora"]),
            models.Index(fields=["usuario", "-fecha_hora"]),
        ]
    
    def __str__(self):
        return f"{self.ot.folio} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, ot, accion, descripcion, usuario=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial.
        """
        return cls.objects.create(
            ot=ot,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )


class HistorialEquipo(models.Model):
    """
    Registra todos los cambios y acciones realizadas en los Equipos.
    Permite auditoría completa de modificaciones, activaciones/desactivaciones, cambios de estado, asignaciones.
    """
    ACCION_CHOICES = [
        ('EQUIPO_CREADO', 'Equipo Creado'),
        ('EQUIPO_MODIFICADO', 'Equipo Modificado'),
        ('EQUIPO_ACTIVADO', 'Equipo Activado'),
        ('EQUIPO_DESACTIVADO', 'Equipo Desactivado'),
        ('EQUIPO_ELIMINADO', 'Equipo Eliminado'),
        ('ESTADO_MANUAL_ASIGNADO', 'Estado Manual Asignado'),
        ('ESTADO_MANUAL_MODIFICADO', 'Estado Manual Modificado'),
        ('ESTADO_MANUAL_ELIMINADO', 'Estado Manual Eliminado'),
        ('ASIGNACION_FAENA_CREADA', 'Asignación a Faena Creada'),
        ('ASIGNACION_FAENA_MODIFICADA', 'Asignación a Faena Modificada'),
        ('ASIGNACION_FAENA_ELIMINADA', 'Asignación a Faena Eliminada'),
    ]
    
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name="historial",
        db_index=True,
        verbose_name='Equipo'
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha y Hora')
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que realizó la acción",
        verbose_name='Usuario'
    )
    accion = models.CharField(
        max_length=50,
        choices=ACCION_CHOICES,
        help_text="Tipo de acción realizada",
        verbose_name='Acción'
    )
    descripcion = models.TextField(
        help_text="Descripción detallada del cambio",
        verbose_name='Descripción'
    )
    datos_previos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado anterior antes del cambio (JSON)",
        verbose_name='Datos Previos'
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado nuevo después del cambio (JSON)",
        verbose_name='Datos Nuevos'
    )
    
    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "Historial de Equipo"
        verbose_name_plural = "Historial de Equipos"
        db_table = 'maquinarias_historialequipo'
        indexes = [
            models.Index(fields=["equipo", "-fecha_hora"]),
            models.Index(fields=["usuario", "-fecha_hora"]),
        ]
    
    def __str__(self):
        return f"{self.equipo.nombreEquipo} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, equipo, accion, descripcion, usuario=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial.
        """
        return cls.objects.create(
            equipo=equipo,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )