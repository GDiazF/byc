from django.db import models
from gen_settings.models import Empresa
from rrhh_personal.models import Personal
from django.contrib.auth.models import User
from datetime import datetime
import os
import re
# from django.core.files.storage import FileSystemStorage  # Solo para desarrollo local
from django.core.exceptions import ValidationError
from rrhh_personal.storage import MediaS3Storage  # Para producción con S3
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
    
    Esta función se usa como upload_to en los campos FileField para organizar automáticamente
    los archivos en una estructura de carpetas lógica. Los documentos se organizan por equipo
    y tipo de documento para facilitar su gestión y acceso.
    
    La estructura será: Documentacion_Maquinarias/EQUIPO_ID/TIPO_DOCUMENTO/archivo
    
    Parámetros:
        instance: Instancia del modelo que contiene el campo FileField
        filename: Nombre original del archivo subido
    
    Retorna:
        str: Ruta relativa (desde MEDIA_ROOT) donde se guardará el archivo
    """
    # Paso 1: Extraer la extensión del archivo original
    # Esto preserva el tipo de archivo (ej: .pdf, .jpg)
    extension = os.path.splitext(filename)[1]
    
    # Paso 2: Generar timestamp para hacer único el nombre del archivo
    # Esto evita sobrescritura accidental si se suben archivos con el mismo nombre
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Formato: YYYYMMDDHHMMSS
    
    # Paso 3: Obtener el nombre de la clase de la instancia
    # Se usa el nombre de la clase en lugar de isinstance() para evitar referencias forward
    # (cuando el modelo aún no está completamente definido)
    class_name = instance.__class__.__name__
    
    # Paso 4: Determinar la ruta según el tipo de modelo
    if class_name == 'DocumentoMaquinaria':
        # CASO 1: Documento actual (no histórico)
        # Estructura: Documentacion_Maquinarias/EQUIPO_ID/TIPO_DOCUMENTO/archivo
        equipo_id = instance.equipo_id.equipo_id  # ID del equipo
        tipo_doc = instance.tipo_documento_id.nombre.replace(' ', '_').lower()  # Nombre del tipo normalizado
        nombre_archivo = f"{tipo_doc}_{timestamp}{extension}"  # Nombre único con timestamp
        return os.path.join('Documentacion_Maquinarias', str(equipo_id), tipo_doc, nombre_archivo)
    
    elif class_name == 'HistorialDocumentoMaquinaria':
        # CASO 2: Documento histórico (reemplazado o eliminado)
        # Estructura: Documentacion_Maquinarias/EQUIPO_ID/Historial/TIPO_DOCUMENTO/archivo
        equipo_id = instance.equipo_id.equipo_id  # ID del equipo
        tipo_doc = instance.tipo_documento_nombre.replace(' ', '_').lower()  # Nombre del tipo (puede ser string)
        nombre_archivo = f"{tipo_doc}_{timestamp}_historial{extension}"  # Nombre con sufijo _historial
        return os.path.join('Documentacion_Maquinarias', str(equipo_id), 'Historial', tipo_doc, nombre_archivo)
    
    # CASO 3: Cualquier otro tipo (fallback)
    # Si no coincide con ninguno de los casos anteriores, guardar en carpeta "Otros"
    return os.path.join('Documentacion_Maquinarias', 'Otros', filename)

def mover_archivo_a_eliminados_maquinaria(archivo_field, equipo_id, nombre_documento):
    """
    Copia un archivo de maquinaria a la carpeta de eliminados en lugar de eliminarlo físicamente.
    
    Esta función preserva los archivos eliminados en una carpeta especial para poder recuperarlos
    si es necesario. Los archivos se organizan por equipo para facilitar su gestión.
    Funciona tanto con S3 como con sistema de archivos local.
    
    Estructura de carpetas: Documentacion_Eliminada_Maquinarias/EQUIPO_ID/EQUIPO_ID_nombre_documento.pdf
    
    Args:
        archivo_field: Campo FileField del modelo que contiene el archivo a mover
        equipo_id: ID del equipo (int o string) para organizar en carpetas
        nombre_documento: Nombre descriptivo del documento (ej: "Permiso de Circulación")
    
    Returns:
        str: Ruta relativa del archivo copiado (desde MEDIA_ROOT o S3), o None si hubo error
    """
    # Paso 1: Validar que el archivo existe y tiene un nombre
    # Si no hay archivo o nombre, no hay nada que mover
    if not archivo_field or not archivo_field.name:
        return None
    
    try:
        from django.core.files.storage import default_storage
        from django.conf import settings
        import logging
        logger = logging.getLogger(__name__)
        
        # Paso 2: Verificar que el archivo existe en el storage (S3 o local)
        # El archivo_field.name ya incluye el prefijo 'media/' si se guardó con MediaS3Storage
        archivo_ruta_original = archivo_field.name
        logger.info(f"Intentando copiar archivo a eliminados. Ruta original: {archivo_ruta_original}")
        
        if not default_storage.exists(archivo_ruta_original):
            logger.warning(f"El archivo no existe en el storage: {archivo_ruta_original}")
            return None
        
        # Paso 3: Crear nombre de archivo limpio y seguro
        # Se normaliza el nombre del documento eliminando caracteres especiales que podrían causar problemas
        # Formato final: EQUIPO_ID_nombre_documento.pdf
        nombre_limpio = nombre_documento.lower().replace(' ', '_').replace('/', '_')  # Normalizar nombre
        extension = os.path.splitext(archivo_ruta_original)[1]  # Obtener extensión del archivo original (.pdf)
        nombre_archivo_final = f"{equipo_id}_{nombre_limpio}{extension}"  # Nombre completo del archivo
        
        # Paso 4: Construir ruta relativa de destino
        # IMPORTANTE: Como MediaS3Storage tiene location='media', todas las rutas se prefijan con 'media/'
        # La estructura final será: media/Documentacion_Eliminada_Maquinarias/EQUIPO_ID/nombre_archivo
        ruta_relativa_destino = os.path.join('Documentacion_Eliminada_Maquinarias', str(equipo_id), nombre_archivo_final)
        logger.info(f"Ruta de destino para archivo eliminado: {ruta_relativa_destino}")
        
        # Paso 5: Manejar caso de archivo duplicado
        # Si ya existe un archivo con ese nombre, agregar timestamp para evitar sobrescritura
        if default_storage.exists(ruta_relativa_destino):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Timestamp en formato YYYYMMDDHHMMSS
            nombre_base, ext = os.path.splitext(nombre_archivo_final)  # Separar nombre y extensión
            nombre_archivo_final = f"{nombre_base}_{timestamp}{ext}"  # Agregar timestamp al nombre
            ruta_relativa_destino = os.path.join('Documentacion_Eliminada_Maquinarias', str(equipo_id), nombre_archivo_final)  # Actualizar ruta destino
            logger.info(f"Archivo duplicado detectado, usando nombre con timestamp: {ruta_relativa_destino}")
        
        # Paso 6: Copiar el archivo desde la ubicación original a la carpeta de eliminados
        # Usar el storage para que funcione tanto con S3 como con sistema de archivos local
        # MediaS3Storage automáticamente agregará el prefijo 'media/' a la ruta
        logger.info(f"Copiando archivo desde {archivo_ruta_original} a {ruta_relativa_destino}")
        with default_storage.open(archivo_ruta_original, 'rb') as source_file:
            ruta_guardada = default_storage.save(ruta_relativa_destino, source_file)
            logger.info(f"Archivo copiado exitosamente a: {ruta_guardada}")
        
        # Paso 7: Retornar ruta relativa para guardar en el historial
        # Esta ruta se usa para referencia en la base de datos
        # La ruta retornada será relativa (sin el prefijo 'media/') para que sea consistente
        return ruta_relativa_destino
        
    except Exception as e:
        # Manejo de errores: si falla la copia, registrar el error pero continuar
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al copiar archivo a eliminados: {str(e)}", exc_info=True)
        return None  # Retornar None para indicar que hubo un error


# ============================================================================
# CONFIGURACIÓN PARA DESARROLLO LOCAL (COMENTADO PARA AWS)
# ============================================================================
# class OverwriteStorage(FileSystemStorage):
#     """
#     Clase de almacenamiento personalizada para desarrollo local que sobrescribe archivos existentes.
#     
#     Esta clase extiende FileSystemStorage de Django y modifica el comportamiento para que,
#     cuando se intenta guardar un archivo con un nombre que ya existe, se elimine el archivo
#     anterior antes de guardar el nuevo. Esto es útil en desarrollo para evitar acumulación
#     de archivos duplicados.
#     
#     IMPORTANTE: Esta clase solo debe usarse en desarrollo, no en producción.
#     """
#     def get_available_name(self, name, max_length=None):
#         """
#         Obtiene un nombre disponible para el archivo, eliminando el existente si hay uno.
#         
#         Este método se ejecuta automáticamente cuando Django intenta guardar un archivo.
#         Si ya existe un archivo con ese nombre, lo elimina antes de retornar el nombre.
#         
#         Parámetros:
#             name: Nombre del archivo a guardar
#             max_length: Longitud máxima del nombre (no usado en esta implementación)
#         
#         Retorna:
#             str: Nombre del archivo (el mismo que se recibió, después de eliminar el existente)
#         """
#         # Paso 1: Verificar si ya existe un archivo con ese nombre
#         if self.exists(name):
#             # Paso 2: Si existe, eliminarlo para permitir sobrescribir
#             self.delete(name)
#         
#         # Paso 3: Retornar el nombre original (ahora disponible)
#         return name

# ============================================================================
# CONFIGURACIÓN PARA PRODUCCIÓN EN NUBE (AWS S3)
# ============================================================================
class OverwriteStorage(MediaS3Storage):
    """
    Clase de almacenamiento personalizada para producción que usa S3 y sobrescribe archivos existentes.
    
    Esta clase extiende MediaS3Storage y permite sobrescribir archivos con el mismo nombre.
    S3 naturalmente sobrescribe archivos con la misma clave, así que solo retornamos el nombre.
    """
    def get_available_name(self, name, max_length=None):
        """
        Retorna el nombre del archivo (S3 sobrescribirá automáticamente si existe).
        
        Parámetros:
            name: Nombre del archivo a guardar
            max_length: Longitud máxima del nombre (no usado)
        
        Retorna:
            str: Nombre del archivo (S3 sobrescribirá si existe)
        """
        # S3 naturalmente sobrescribe archivos con la misma clave
        return name

class TipoEquipo(models.Model):
    """
    Modelo que representa los tipos de equipos (categorías).
    
    Ejemplos: Grúa Torre, Excavadora, Camión, Cargador Frontal, etc.
    Cada tipo tiene una sigla que se usa para generar nombres de equipos (ej: GT, EX, CM).
    """
    # Campo de clave primaria autoincremental
    tipoEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    
    # Nombre completo del tipo de equipo (ej: "Grúa Torre", "Excavadora")
    tipoEquipo = models.CharField(max_length=100, null=False, blank=False)
    
    # Sigla del tipo de equipo (ej: "GT", "EX", "CM")
    # Se usa para generar nombres de equipos automáticamente
    siglaEquipo = models.CharField(max_length=3, null=False, blank=False)

    def __str__(self):
        """Representación en string del objeto (usado en admin y shell de Django)"""
        return self.tipoEquipo

class MarcaEquipo(models.Model):
    """
    Modelo que representa las marcas de equipos.
    
    Ejemplos: Caterpillar, Komatsu, Liebherr, Volvo, etc.
    Cada marca puede tener múltiples modelos asociados.
    """
    # Campo de clave primaria autoincremental
    marcaEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    
    # Nombre de la marca (ej: "Caterpillar", "Komatsu", "Liebherr")
    marcaEquipo = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        """Representación en string del objeto (usado en admin y shell de Django)"""
        return self.marcaEquipo

class ModeloEquipo(models.Model):
    """
    Modelo que representa los modelos específicos de equipos.
    
    Cada modelo pertenece a un tipo y una marca específicos.
    Ejemplos: CAT 320D (Tipo: Excavadora, Marca: Caterpillar), Komatsu PC200 (Tipo: Excavadora, Marca: Komatsu).
    
    La combinación de tipo, marca y nombre de modelo debe ser única para evitar duplicados.
    """
    # Campo de clave primaria autoincremental
    modeloEquipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    
    # Nombre del modelo (ej: "CAT 320D", "Komatsu PC200", "Liebherr LTM 1100")
    modeloEquipo = models.CharField(max_length=100, null=False, blank=False)
    
    # Relación con TipoEquipo (tipo de equipo al que pertenece este modelo)
    # CASCADE: Si se elimina el tipo, se eliminan todos sus modelos
    tipoEquipo_id = models.ForeignKey(TipoEquipo, on_delete=models.CASCADE, db_column='tipoEquipo_id', null=True, blank=True)
    
    # Relación con MarcaEquipo (marca del equipo)
    # CASCADE: Si se elimina la marca, se eliminan todos sus modelos
    marcaEquipo_id = models.ForeignKey(MarcaEquipo, on_delete=models.CASCADE, db_column='marcaEquipo_id', null=True, blank=True)

    class Meta:
        """Configuración de metadatos del modelo"""
        verbose_name = 'Modelo de Equipo'  # Nombre singular en español para el admin
        verbose_name_plural = 'Modelos de Equipo'  # Nombre plural en español para el admin
        
        # Restricción de unicidad: Un modelo es único para cada combinación de tipo, marca y nombre
        # Esto previene tener modelos duplicados con el mismo nombre en la misma marca y tipo
        unique_together = [['tipoEquipo_id', 'marcaEquipo_id', 'modeloEquipo']]

    def __str__(self):
        """Representación en string del objeto (usado en admin y shell de Django)"""
        return f"{self.modeloEquipo} ({self.marcaEquipo_id.marcaEquipo})"

class Equipo(models.Model):
    """
    Modelo principal que representa cada equipo físico individual en el sistema.
    
    Un equipo es una instancia específica de un modelo de equipo, perteneciente a una empresa.
    Cada equipo tiene un código interno único dentro de su modelo, y un nombre que se genera
    automáticamente basado en la sigla del tipo, código interno y patente.
    
    Ejemplo: Un equipo puede ser "GT01 - KJL556" (Grúa Torre código 01, patente KJL556).
    """
    # Campo de clave primaria autoincremental
    equipo_id = models.AutoField(primary_key=True, null=False, blank=False)
    
    # Relación con Empresa (empresa propietaria del equipo)
    # CASCADE: Si se elimina la empresa, se eliminan todos sus equipos
    empresa_id = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column='empresa_id', null=False, blank=False)
    
    # Relación con ModeloEquipo (modelo específico del equipo)
    # CASCADE: Si se elimina el modelo, se eliminan todos los equipos de ese modelo
    modeloEquipo_id = models.ForeignKey(ModeloEquipo, on_delete=models.CASCADE, db_column='modeloEquipo_id', null=False, blank=False)
    
    # Código interno único del equipo dentro de su modelo
    # Ejemplo: "01", "02", "A001", etc.
    # Debe ser único por modelo (no puede haber dos equipos del mismo modelo con el mismo código)
    codigoInterno = models.CharField(max_length=100, null=False, blank=False)
    
    # Patente del equipo (opcional)
    # Ejemplo: "KJL556", "ABC123"
    patente = models.CharField(max_length=100, null=True, blank=True)
    
    # Horómetro: Horas de uso del equipo (opcional)
    # Se usa para equipos que miden horas de funcionamiento (grúas, excavadoras, etc.)
    horometro = models.IntegerField(null=True, blank=True)
    
    # Odómetro: Kilómetros recorridos del equipo (opcional)
    # Se usa para equipos que miden distancia recorrida (camiones, vehículos, etc.)
    odometro = models.IntegerField(null=True, blank=True)
    
    # Horómetro superestructural: Horas de uso de la superestructura (opcional)
    # Se usa para equipos con partes separadas que tienen sus propios contadores
    horometroSuperEstructural = models.IntegerField(null=True, blank=True)
    
    # Nombre del equipo generado automáticamente
    # Formato: {siglaTipo}{codigoInterno} - {patente}
    # Ejemplo: "GT01 - KJL556"
    # Se genera en el método save() basado en tipo, código y patente
    nombreEquipo = models.CharField(max_length=100, null=False, blank=True)  # Se genera automáticamente
    
    # Estado de activación del equipo
    # True = activo (disponible para uso), False = inactivo (desactivado)
    # Los equipos nuevos se crean activos por defecto
    activo = models.BooleanField(default=True, null=False, blank=False)
    
    class Meta:
        """Configuración de metadatos del modelo"""
        # Restricción de unicidad: El código interno debe ser único POR MODELO de equipo
        # Esto permite que diferentes modelos tengan equipos con el mismo código interno
        # Ejemplo: Puede haber "GT01" y "EX01" porque son modelos diferentes
        unique_together = [['modeloEquipo_id', 'codigoInterno']]
        
        verbose_name = 'Equipo'  # Nombre singular en español para el admin
        verbose_name_plural = 'Equipos'  # Nombre plural en español para el admin
        
        # Permisos personalizados para acciones específicas dentro del modelo Equipo
        # Estos permisos se pueden asignar a usuarios o grupos para controlar acceso granular
        permissions = [
            ('desactivar_equipo', 'Puede desactivar equipos'),  # Permiso para desactivar equipos
            ('activar_equipo', 'Puede activar equipos'),  # Permiso para activar equipos
            ('exportar_equipos', 'Puede exportar datos de equipos'),  # Permiso para exportar datos
            ('ver_historial_equipo', 'Puede ver historial completo de equipos'),  # Permiso para ver historial
        ]

    def save(self, *args, **kwargs):
        """
        Genera automáticamente el nombreEquipo basado en:
        - siglaEquipo del TipoEquipo (obtenido del modelo)
        - codigoInterno
        - patente (opcional)
        
        Formato: {siglaEquipo}{codigoInterno} - {patente}
        Ejemplo: GT01 - KJL556
        
        Este método se ejecuta automáticamente cada vez que se guarda un equipo,
        asegurando que el nombre siempre esté actualizado según los datos del equipo.
        """
        # Paso 1: Obtener la sigla del tipo de equipo a través de la relación con el modelo
        # La sigla identifica el tipo de equipo (ej: GT para Grúa Torre, EX para Excavadora)
        # Se accede a través de: Equipo -> ModeloEquipo -> TipoEquipo -> siglaEquipo
        sigla = self.modeloEquipo_id.tipoEquipo_id.siglaEquipo if self.modeloEquipo_id and self.modeloEquipo_id.tipoEquipo_id else ''
        
        # Paso 2: Construir el nombre base combinando la sigla con el código interno
        # Ejemplo: "GT" + "01" = "GT01"
        nombre_base = f"{sigla}{self.codigoInterno}"
        
        # Paso 3: Agregar la patente al nombre si existe y no está vacía
        # La patente se agrega separada por guión para mejor legibilidad
        if self.patente and self.patente.strip():
            self.nombreEquipo = f"{nombre_base} - {self.patente.strip()}"  # Ejemplo: "GT01 - KJL556"
        else:
            self.nombreEquipo = nombre_base  # Si no hay patente, solo usar sigla + código
        
        # Paso 4: Llamar al método save() de la clase padre para guardar en la base de datos
        # Esto ejecuta el guardado real del objeto con el nombreEquipo ya generado
        super().save(*args, **kwargs)
    
    @property
    def tipoEquipo(self):
        """
        Propiedad para acceder directamente al tipo de equipo a través del modelo.
        
        Esta propiedad simplifica el acceso al tipo de equipo sin tener que navegar
        manualmente por las relaciones: equipo.modeloEquipo_id.tipoEquipo_id
        
        Retorna:
            TipoEquipo: Instancia del tipo de equipo al que pertenece este equipo
        """
        return self.modeloEquipo_id.tipoEquipo_id
    
    @property
    def marcaEquipo(self):
        """
        Propiedad para acceder directamente a la marca a través del modelo.
        
        Esta propiedad simplifica el acceso a la marca sin tener que navegar
        manualmente por las relaciones: equipo.modeloEquipo_id.marcaEquipo_id
        
        Retorna:
            MarcaEquipo: Instancia de la marca del equipo
        """
        return self.modeloEquipo_id.marcaEquipo_id

    def __str__(self):
        """Representación en string del objeto (usado en admin y shell de Django)"""
        return self.nombreEquipo


class Seccion(models.Model):
    """
    Modelo que representa las secciones o sistemas de un equipo.
    
    Las secciones son partes específicas de un equipo que pueden requerir mantenimiento
    o reparación. Ejemplos: Motor, Radiador, Sistema Hidráulico, Transmisión, etc.
    Cada sección puede tener múltiples tipos de reparación asociados.
    """
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
    """
    Modelo que representa los estados posibles de una Orden de Trabajo.
    
    Los estados permiten rastrear el progreso de una OT desde su creación hasta
    su finalización. Ejemplos: Pendiente, En Proceso, Completada, Cancelada.
    Cada estado tiene un color asociado para visualización en la interfaz.
    """
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
    """
    Modelo que representa los tipos específicos de reparaciones que se pueden realizar.
    
    Cada tipo de reparación pertenece a una sección específica del equipo.
    Ejemplos: Cambio de aceite (Motor), Reemplazo de filtro (Radiador), Ajuste de válvulas (Motor).
    La combinación de sección y nombre debe ser única.
    """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del tipo de reparación seguido del nombre de la sección.
        """
        return f"{self.nombre} ({self.seccion_id.nombre})"


class PautaMantenimientoPreventivo(models.Model):
    """
    Modelo que representa una pauta de mantenimiento preventivo para un modelo de equipo.
    
    Una pauta define qué secciones y tipos de reparación deben revisarse o realizarse
    en un modelo específico de equipo durante el mantenimiento preventivo.
    Cada pauta contiene múltiples items (ItemPauta) que especifican las secciones y reparaciones.
    """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre de la pauta seguido del modelo de equipo.
        """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre de la pauta seguido del nombre de la sección.
        """
        return f"{self.pauta_id.nombre} - {self.seccion_id.nombre}"


# ============================================================================
# MODELOS PARA DOCUMENTACIÓN DE MAQUINARIAS
# ============================================================================

class TipoDocumentoMaquinaria(models.Model):
    """
    Modelo que representa los tipos de documentos que puede tener una maquinaria.
    
    Ejemplos: Revisión Técnica, Seguro, Permiso de Circulación, Certificado de Inspección.
    Cada tipo puede requerir o no una fecha de vencimiento según su naturaleza.
    """
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
    """
    Modelo que representa los documentos actuales asociados a una maquinaria.
    
    Cada documento tiene un archivo, tipo de documento, fecha de vencimiento (si aplica)
    y observaciones. Un equipo solo puede tener un documento activo de cada tipo.
    Los documentos reemplazados se mueven al historial (HistorialDocumentoMaquinaria).
    """
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
        """
        Determina si el documento está vencido.
        
        Un documento está vencido si tiene fecha de vencimiento y esa fecha
        es anterior a la fecha actual.
        
        Returns:
            bool: True si el documento está vencido, False en caso contrario.
        """
        from datetime import date
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < date.today()
    
    @property
    def esta_por_vencer(self):
        """
        Determina si el documento está por vencer (menos de 30 días).
        
        Un documento está por vencer si tiene fecha de vencimiento y quedan
        entre 0 y 30 días para que venza.
        
        Returns:
            bool: True si el documento está por vencer, False en caso contrario.
        """
        from datetime import date, timedelta
        if not self.fecha_vencimiento:
            return False
        dias_restantes = (self.fecha_vencimiento - date.today()).days
        return 0 <= dias_restantes <= 30
    
    def __str__(self):
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del tipo de documento seguido del nombre del equipo.
        """
        return f"{self.tipo_documento_id.nombre} - {self.equipo_id.nombreEquipo}"


class HistorialDocumentoMaquinaria(models.Model):
    """
    Modelo que almacena el historial de documentos reemplazados o eliminados.
    
    Cuando un documento es reemplazado por uno nuevo, el documento anterior se mueve
    a este modelo para mantener un registro histórico. Esto permite rastrear todos
    los documentos que ha tenido un equipo a lo largo del tiempo.
    """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del tipo de documento seguido del nombre del equipo y etiqueta "(Historial)".
        """
        return f"{self.tipo_documento_nombre} - {self.equipo_id.nombreEquipo} (Historial)"


# ============================================================================
# MODELOS PARA ORDEN DE TRABAJO (OT)
# ============================================================================

class TipoMantenimiento(models.Model):
    """
    Modelo que representa los tipos de mantenimiento que se pueden realizar.
    
    Ejemplos: Preventivo, Correctivo, Predictivo, Emergencia.
    Cada orden de trabajo tiene un tipo de mantenimiento asociado.
    """
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
    """
    Modelo que representa los estados posibles de un equipo durante una orden de trabajo.
    
    Los estados indican la condición del equipo mientras se realiza el mantenimiento.
    Ejemplos: Operativo, En Mantenimiento, Fuera de Servicio, En Reparación.
    Cada estado tiene un color asociado para visualización en la interfaz.
    """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del estado de equipo.
        """
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
        """
        Valida que solo haya un estado predeterminado activo.
        
        Si este estado está marcado como predeterminado, verifica que no exista
        otro estado predeterminado activo. Si existe, lanza ValidationError.
        
        Raises:
            ValidationError: Si ya existe otro estado predeterminado activo.
        """
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
        """
        Asegura que solo haya un estado predeterminado.
        
        Si este estado está marcado como predeterminado, desmarca automáticamente
        todos los demás estados predeterminados antes de guardar.
        """
        if self.es_predeterminado:
            # Desmarcar otros estados predeterminados
            EstadoCalendarioEquipo.objects.filter(
                es_predeterminado=True
            ).exclude(pk=self.pk).update(es_predeterminado=False)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del estado de calendario.
        """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del estado de calendario seguido del nombre del estado de equipo.
        """
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
        """
        Valida que la fecha de fin sea mayor o igual a la fecha de inicio.
        
        Raises:
            ValidationError: Si fecha_fin es anterior a fecha_inicio.
        """
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser mayor o igual a la fecha de inicio.')

    def save(self, *args, **kwargs):
        """
        Valida y guarda el estado manual.
        
        Ejecuta clean() antes de guardar para asegurar que las fechas sean válidas.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del equipo, estado y rango de fechas.
        """
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
    """
    Modelo principal que representa una Orden de Trabajo para mantenimiento de equipos.
    
    Una OT registra el trabajo de mantenimiento realizado en un equipo específico,
    incluyendo el tipo de mantenimiento, fechas, personal asignado, secciones a reparar,
    estados y observaciones. Cada OT tiene un folio único y mantiene un historial
    completo de todos los cambios realizados.
    """
    
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
        """
        Representación en string del objeto.
        
        Si el folio ya tiene el prefijo OT-, se muestra tal cual, sino se agrega.
        
        Returns:
            str: Folio de la OT seguido del nombre del equipo.
        """
        folio_display = self.folio if self.folio.startswith('OT-') else f"OT-{self.folio}"
        return f"{folio_display} - {self.equipo_id.nombreEquipo}"
    
    def save(self, *args, **kwargs):
        """
        Genera el folio automáticamente si no existe.
        
        Busca el número más alto de los folios existentes con formato OT-{número}
        y genera el siguiente número secuencial. Si no hay folios previos, usa
        el conteo total de OTs como respaldo.
        """
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
    """
    Modelo que representa una sección específica dentro de una orden de trabajo.
    
    Cada item asocia una sección con múltiples tipos de reparación que deben
    realizarse en esa sección durante la OT. También incluye el estado de la sección.
    Se usa cuando la OT NO corresponde a una pauta de mantenimiento preventivo.
    """
    
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Folio de la OT seguido del nombre de la sección.
        """
        return f"{self.ot_id.folio} - {self.seccion_id.nombre}"


class HistorialObservacionesOT(models.Model):
    """
    Modelo que almacena el historial de observaciones (bitácora) de una OT.
    
    Cada vez que se agrega una observación a una orden de trabajo, se registra
    aquí con el usuario que la agregó y la fecha/hora. Esto permite mantener
    un registro cronológico completo de todas las observaciones realizadas.
    """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Folio de la OT seguido de la fecha y hora de la observación.
        """
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Folio de la OT, acción realizada y fecha/hora.
        """
        return f"{self.ot.folio} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, ot, accion, descripcion, usuario=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial.
        
        Crea un nuevo registro en el historial con la información proporcionada.
        Se usa desde signals y vistas para registrar cambios en las OTs.
        
        Args:
            ot: Instancia de OrdenTrabajo.
            accion: Código de la acción (debe estar en ACCION_CHOICES).
            descripcion: Descripción detallada del cambio.
            usuario: Usuario que realizó la acción (opcional).
            datos_previos: Estado anterior antes del cambio en formato JSON (opcional).
            datos_nuevos: Estado nuevo después del cambio en formato JSON (opcional).
            
        Returns:
            HistorialOT: Instancia del registro de historial creado.
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
        """
        Representación en string del objeto.
        
        Returns:
            str: Nombre del equipo, acción realizada y fecha/hora.
        """
        return f"{self.equipo.nombreEquipo} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, equipo, accion, descripcion, usuario=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial.
        
        Crea un nuevo registro en el historial con la información proporcionada.
        Se usa desde signals y vistas para registrar cambios en los equipos.
        
        Args:
            equipo: Instancia de Equipo.
            accion: Código de la acción (debe estar en ACCION_CHOICES).
            descripcion: Descripción detallada del cambio.
            usuario: Usuario que realizó la acción (opcional).
            datos_previos: Estado anterior antes del cambio en formato JSON (opcional).
            datos_nuevos: Estado nuevo después del cambio en formato JSON (opcional).
            
        Returns:
            HistorialEquipo: Instancia del registro de historial creado.
        """
        return cls.objects.create(
            equipo=equipo,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )