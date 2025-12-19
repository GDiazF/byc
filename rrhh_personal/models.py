from django.db import models
from datetime import datetime, date
import os
# from django.core.files.storage import FileSystemStorage  # Solo para desarrollo local
from gen_settings.models import Region, Comuna, Empresa
from django.contrib.auth.models import User
from .storage import MediaS3Storage  # Para producción con S3

# ============================================================================
# FUNCIONES HELPER PARA GESTIÓN DE DOCUMENTOS
# ============================================================================

def obtener_ruta_documento_personal(instance, filename):
    """
    Función de compatibilidad para migraciones antiguas.
    Redirige a obtener_ruta_documento() que es la función actual.
    
    Args:
        instance: Instancia del modelo que contiene el archivo
        filename: Nombre del archivo original
        
    Returns:
        str: Ruta relativa donde se guardará el archivo
    """
    return obtener_ruta_documento(instance, filename)

def obtener_ruta_documento(instance, filename):
    """
    Función unificada para determinar la ruta donde se guardarán todos los documentos.
    Organiza los archivos por RUT del personal y tipo de documento.
    La estructura será: RUT/TIPO_DOCUMENTO/archivo_timestamp.extensión
    
    Args:
        instance: Instancia del modelo que contiene el archivo (Personal, LicenciaPorPersonal, etc.)
        filename: Nombre del archivo original
        
    Returns:
        str: Ruta relativa donde se guardará el archivo
        Ejemplo: "12345678/Licencias/licencia_20240101120000.pdf"
    """
    # Extraer la extensión del archivo original
    extension = os.path.splitext(filename)[1]
    # Generar timestamp para evitar conflictos de nombres
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Determinar el RUT y tipo de documento según la instancia del modelo
    if isinstance(instance, Personal):
        # Para documentos personales, buscar el campo específico que se está guardando
        rut = instance.rut
        # Iterar sobre todos los campos del modelo para encontrar el FileField/ImageField
        for field in instance._meta.fields:
            if isinstance(field, (models.FileField, models.ImageField)):
                value = getattr(instance, field.name)
                # Si el campo coincide con el archivo que se está guardando
                if value and value.name == filename:
                    carpeta = 'Documentos_Personales'
                    # Nombre del archivo: nombre_campo_timestamp.extensión
                    nombre_archivo = f"{field.name}_{timestamp}{extension}"
                    break
        else:
            # Si no se encontró el campo, usar carpeta genérica
            carpeta = 'Otros'
            nombre_archivo = filename
    
    elif isinstance(instance, LicenciaPorPersonal):
        # Para licencias de conducir
        rut = instance.personal_id.rut
        carpeta = 'Licencias'
        nombre_archivo = f"licencia_{timestamp}{extension}"
    
    elif isinstance(instance, LicenciaMedicaPorPersonal):
        # Para licencias médicas
        rut = instance.personal_id.rut
        carpeta = 'Licencias_Medicas'
        # Usar ID de la licencia para evitar conflictos entre registros
        nombre_archivo = f"licenciaMedica_{instance.licenciaMedicaPorPersonal_id or 'new'}{extension}"
    
    elif isinstance(instance, Certificacion):
        # Para certificaciones
        rut = instance.personal_id.rut
        carpeta = 'Certificaciones'
        nombre_archivo = f"certificacion_{instance.tipoCertificacion_id.tipoCertificacion}_{timestamp}{extension}"
    
    elif isinstance(instance, Examen):
        # Para exámenes médicos
        rut = instance.personal_id.rut
        carpeta = 'Examenes'
        nombre_archivo = f"examen_{instance.tipoEx_id.tipoExamen}_{timestamp}{extension}"
    
    else:
        # Caso por defecto para instancias desconocidas
        rut = 'sin_rut'
        carpeta = 'Otros'
        nombre_archivo = filename
    
    # Retornar la ruta relativa (MEDIA_ROOT ya incluye la carpeta base)
    return os.path.join(str(rut), carpeta, nombre_archivo)

def mover_archivo_a_eliminados(archivo_field, personal_rut, nombre_documento):
    """
    Copia un archivo a la carpeta de eliminados en lugar de eliminarlo físicamente.
    Esto permite mantener un historial de documentos eliminados para auditoría.
    Funciona tanto con S3 como con sistema de archivos local.
    Estructura: Documentacion_Eliminada/RUT/nombre_documento.pdf
    
    Args:
        archivo_field: Campo FileField del modelo que contiene el archivo
        personal_rut: RUT del personal (string) para organizar por carpeta
        nombre_documento: Nombre descriptivo del documento (ej: "Curriculum Vitae")
    
    Returns:
        str: Ruta relativa del archivo copiado, o None si hubo error
    """
    # Validar que el campo tenga un archivo
    if not archivo_field or not archivo_field.name:
        return None
    
    try:
        from django.core.files.storage import default_storage
        from django.conf import settings
        import logging
        logger = logging.getLogger(__name__)
        
        archivo_ruta_original = archivo_field.name
        logger.info(f"Copiando archivo a eliminados. Ruta original: {archivo_ruta_original}, RUT: {personal_rut}, Nombre: {nombre_documento}")
        
        # Verificar que el archivo existe en el storage (S3 o local)
        if not default_storage.exists(archivo_ruta_original):
            logger.warning(f"El archivo no existe en el storage: {archivo_ruta_original}")
            return None
        
        # Crear nombre de archivo limpio (sin caracteres especiales)
        # Formato: RUT_nombre_documento.pdf
        nombre_limpio = nombre_documento.lower().replace(' ', '_').replace('/', '_')
        # Obtener extensión del archivo original
        extension = os.path.splitext(archivo_ruta_original)[1]
        nombre_archivo_final = f"{personal_rut}_{nombre_limpio}{extension}"
        
        # Construir ruta relativa de destino (MediaS3Storage agregará 'media/' automáticamente)
        # La estructura final será: media/Documentacion_Eliminada/RUT/nombre_archivo
        ruta_relativa_destino = os.path.join('Documentacion_Eliminada', str(personal_rut), nombre_archivo_final)
        logger.info(f"Ruta de destino para archivo eliminado: {ruta_relativa_destino}")
        
        # Manejar archivos duplicados
        if default_storage.exists(ruta_relativa_destino):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            nombre_base, ext = os.path.splitext(nombre_archivo_final)
            nombre_archivo_final = f"{nombre_base}_{timestamp}{ext}"
            ruta_relativa_destino = os.path.join('Documentacion_Eliminada', str(personal_rut), nombre_archivo_final)
            logger.info(f"Archivo duplicado detectado, usando nombre con timestamp: {ruta_relativa_destino}")
        
        # Copiar el archivo desde su ubicación original a la carpeta de eliminados
        # MediaS3Storage automáticamente agregará el prefijo 'media/' a la ruta
        logger.info(f"Copiando archivo desde {archivo_ruta_original} a {ruta_relativa_destino}")
        with default_storage.open(archivo_ruta_original, 'rb') as source_file:
            ruta_guardada = default_storage.save(ruta_relativa_destino, source_file)
            logger.info(f"Archivo copiado exitosamente a: {ruta_guardada}")
        
        # Retornar ruta relativa para guardar en el historial
        # La ruta retornada será relativa (sin el prefijo 'media/') para que sea consistente
        return ruta_relativa_destino
        
    except Exception as e:
        # Manejo de errores: si falla la copia, registrar el error pero continuar
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al copiar archivo a eliminados: {str(e)}", exc_info=True)
        return None

# ============================================================================
# CLASE DE STORAGE PARA SOBREESCRIBIR ARCHIVOS
# ============================================================================
# CONFIGURACIÓN PARA DESARROLLO LOCAL (COMENTADO PARA AWS)
# ============================================================================
# class OverwriteStorage(FileSystemStorage):
#     """
#     Storage class para desarrollo local que sobrescribe archivos existentes.
#     Cuando se sube un archivo con el mismo nombre, elimina el anterior y lo reemplaza.
#     Esto evita la acumulación de archivos con nombres similares (archivo_1.pdf, archivo_2.pdf, etc.)
#     """
#     def get_available_name(self, name, max_length=None):
#         """
#         Obtiene un nombre disponible para el archivo, eliminando el existente si ya existe.
#         
#         Args:
#             name: Nombre del archivo
#             max_length: Longitud máxima permitida (no usado en esta implementación)
#             
#         Returns:
#             str: Nombre del archivo (el mismo, ya que se sobrescribe)
#         """
#         # Eliminar archivo existente si existe para permitir sobrescritura
#         if self.exists(name):
#             self.delete(name)
#         return name

# ============================================================================
# CONFIGURACIÓN PARA PRODUCCIÓN EN NUBE (AWS S3)
# ============================================================================
class OverwriteStorage(MediaS3Storage):
    """
    Storage class that uses S3 and overwrites existing files.
    S3 naturally overwrites files with the same key, so we just return the name.
    """
    def get_available_name(self, name, max_length=None):
        # S3 naturally overwrites files with the same key
        return name

# ============================================================================
# MODELOS DE DATOS PERSONALES BÁSICOS
# ============================================================================

class Sexo(models.Model):
    """
    Modelo para almacenar los tipos de sexo (Masculino, Femenino, Otro, etc.)
    """
    sexo_id = models.AutoField(primary_key=True, null=False, blank=False)
    sexo = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.sexo
    
    class Meta:
        db_table = 'sexo'

class EstadoCivil(models.Model):
    """
    Modelo para almacenar los estados civiles (Soltero, Casado, Divorciado, etc.)
    """
    estcivil_id = models.AutoField(primary_key=True, null=False, blank=False)
    estadocivil = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.estadocivil
    
    class Meta:
        db_table = 'estadocivil'


# ============================================================================
# MODELO PRINCIPAL: PERSONAL
# ============================================================================

class Personal(models.Model):
    """
    Modelo principal que representa a un trabajador/personal de la empresa.
    Contiene información personal básica, documentos y relaciones con otros modelos.
    """
    # Identificador único
    personal_id = models.AutoField(primary_key=True, null=False, blank=False)
    
    # Relaciones con modelos de referencia
    sexo_id = models.ForeignKey(Sexo, on_delete=models.CASCADE, db_column='sexo_id', null=True, blank=True)
    estcivil_id = models.ForeignKey(EstadoCivil, on_delete=models.CASCADE, db_column='estcivil_id', null=True, blank=True)
    region_id = models.ForeignKey(Region, on_delete=models.CASCADE, db_column='region_id', null=True, blank=True)
    comuna_id = models.ForeignKey(Comuna, on_delete=models.CASCADE, db_column='comuna_id', null=True, blank=True)
    
    # Información de identificación
    rut = models.CharField(max_length=8, null=False, blank=False, unique=True)
    dvrut = models.CharField(max_length=1, null=False, blank=False)
    
    # Información personal
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apepat = models.CharField(max_length=50, null=False, blank=False)
    apemat = models.CharField(max_length=50, null=True, blank=True)
    fechanac = models.DateField(null=True, blank=True)
    
    # Información de contacto
    correo = models.CharField(max_length=100, null=False, blank=False, unique=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    
    # Estado del personal (activo/inactivo)
    activo = models.BooleanField(default=True, verbose_name='Estado')
    
    # Campos de documentos
    curriculum = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Curriculum Vitae'
    )
    certificado_antecedentes = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Certificado de Antecedentes'
    )
    hoja_vida_conductor = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Hoja de Vida del Conductor'
    )
    foto_carnet = models.ImageField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Foto tipo Carnet'
    )
    certificado_afp = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Certificado de Afiliación AFP'
    )
    certificado_salud = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Certificado de Afiliación de Salud'
    )
    certificado_estudios = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Certificado de Estudios'
    )
    certificado_residencia = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Certificado de Residencia'
    )
    fotocopia_carnet = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Fotocopia de Carnet'
    )
    fecha_vencimiento_carnet = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Fecha de Vencimiento del Carnet',
        help_text='Fecha en que vence el carnet de identidad'
    )
    fotocopia_finiquito = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Fotocopia de Último Finiquito'
    )
    comprobante_banco = models.FileField(
        upload_to=obtener_ruta_documento,
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name='Formulario de Depósito Bancario'
    )

    def __str__(self):
        """Representación en string del personal: nombre completo"""
        nombre_completo = self.nombre + " " + self.apepat
        if self.apemat:
            nombre_completo += " " + self.apemat
        return nombre_completo
    
    def get_licencias_activas_count(self):
        """
        Retorna la cantidad de licencias médicas activas del personal.
        Una licencia se considera activa si su fecha de fin es mayor o igual a hoy.
        
        Returns:
            int: Cantidad de licencias médicas activas
        """
        from datetime import date
        return self.licenciamedicaporpersonal_set.filter(
            fecha_fin_licencia__gte=date.today()
        ).count()
    
    def get_ausentismos_activos_count(self):
        """
        Retorna la cantidad de ausentismos activos del personal.
        Un ausentismo se considera activo si su fecha de fin es mayor o igual a hoy.
        
        Returns:
            int: Cantidad de ausentismos activos
        """
        from datetime import date
        return self.ausentismo_set.filter(
            fechafin__gte=date.today()
        ).count()
    
    class Meta:
        db_table = 'Personal'
        # Permisos personalizados para acciones específicas dentro del modelo Personal
        # Estos permisos permiten control granular sobre qué acciones puede realizar cada usuario
        permissions = [
            # Permisos estándar (add, change, delete, view) se crean automáticamente por Django
            # Permisos personalizados adicionales:
            ('desactivar_personal', 'Puede desactivar personal'),  # Solo jefes pueden desactivar
            ('activar_personal', 'Puede activar personal'),  # Solo jefes pueden activar
            ('exportar_personal', 'Puede exportar datos de personal'),  # Para reportes
            ('ver_salarios', 'Puede ver información salarial'),  # Información sensible
            ('ver_historial_personal', 'Puede ver historial completo de personal'),  # Para ver historial de cambios
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para normalizar los datos antes de guardar.
        Convierte todos los campos de texto a mayúsculas para mantener consistencia.
        """
        # Normalizar a mayúsculas todos los campos de texto
        self.rut = self.rut.upper()
        self.dvrut = self.dvrut.upper()
        self.nombre = self.nombre.upper()
        self.apepat = self.apepat.upper()
        self.apemat = self.apemat.upper() if self.apemat else None
        self.correo = self.correo.upper()
        self.direccion = self.direccion.upper() if self.direccion else None
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete para eliminar físicamente los archivos asociados
        antes de eliminar el registro de la base de datos.
        También elimina la carpeta del personal si queda vacía.
        """
        # Lista de campos de archivo que deben eliminarse
        file_fields = [
            'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
            'foto_carnet', 'certificado_afp', 'certificado_salud',
            'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
            'fotocopia_finiquito', 'comprobante_banco'
        ]
        
        # Eliminar cada archivo físicamente del sistema de archivos
        for field_name in file_fields:
            file = getattr(self, field_name)
            if file:
                try:
                    if os.path.isfile(file.path):
                        os.remove(file.path)
                except Exception as e:
                    print(f"Error al eliminar {field_name}: {e}")
                
        # Eliminar la carpeta del personal si está vacía
        rut_folder = os.path.join('media', 'Documentacion_Personal', self.rut)
        try:
            if os.path.exists(rut_folder) and not os.listdir(rut_folder):
                os.rmdir(rut_folder)
        except Exception as e:
            print(f"Error al eliminar carpeta: {e}")
            
        # Llamar al método delete del padre para eliminar el registro
        super().delete(*args, **kwargs)



# ============================================================================
# MODELOS DE INFORMACIÓN LABORAL
# ============================================================================

class DeptoEmpresa(models.Model):
    """
    Modelo para almacenar los departamentos de la empresa.
    Ejemplos: Recursos Humanos, Operaciones, Administración, etc.
    """
    depto_id = models.AutoField(primary_key=True, blank=False, null=False)
    depto = models.CharField(max_length=50, db_column='depto', blank=False, null=False)

    def __str__(self):
        return self.depto


class Cargo(models.Model):
    """
    Modelo para almacenar los cargos dentro de la empresa.
    Cada cargo pertenece a un departamento específico.
    Ejemplos: Jefe de Operaciones, Operador, Supervisor, etc.
    """
    cargo_id = models.AutoField(primary_key=True, blank=False, null=False)
    depto_id = models.ForeignKey(DeptoEmpresa, on_delete=models.CASCADE, db_column='depto_id', blank=False, null=False)
    cargo = models.CharField(max_length=50, db_column='cargo', blank=False, null=False)

    def __str__(self):
        return self.cargo


class InfoLaboral(models.Model):
    """
    Modelo que relaciona el personal con su información laboral:
    empresa, departamento, cargo y fecha de contratación.
    Un personal puede tener múltiples registros de información laboral (historial).
    """
    infolab_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    empresa_id = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column='empresa_id', null=False, blank=False)
    depto_id = models.ForeignKey(DeptoEmpresa, on_delete=models.CASCADE, db_column='depto_id', null=False, blank=False)
    cargo_id = models.ForeignKey(Cargo, on_delete=models.CASCADE, db_column='cargo_id',blank=False, null=False)
    fechacontrata = models.DateField(blank=False, null=False)


# ============================================================================
# MODELOS DE AUSENTISMO
# ============================================================================

class TipoAusentismo(models.Model):
    """
    Modelo para almacenar los tipos de ausentismo.
    Ejemplos: Vacaciones, Permiso sin goce de sueldo, Permiso administrativo, etc.
    """
    tipoausen_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipo = models.CharField(max_length=100, null=False, blank=False, db_column='tipo' )

    def __str__(self):
        return self.tipo


class Ausentismo(models.Model):
    """
    Modelo que registra los ausentismos del personal.
    Calcula automáticamente la fecha de fin basándose en la fecha de inicio y los días.
    """
    ausentismo_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoausen_id = models.ForeignKey(TipoAusentismo, on_delete=models.CASCADE, db_column='tipoausen_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    fechaini = models.DateField(null=False, blank=False, verbose_name='Fecha de Inicio')
    dias_ausentismo = models.IntegerField(null=False, blank=False, verbose_name='Días de Ausentismo', default=1)
    fechafin = models.DateField(null=False, blank=False, editable=False, verbose_name='Fecha de Fin')
    observacion = models.TextField(max_length=250, blank=True, null=True, verbose_name='Observaciones')

    def save(self, *args, **kwargs):
        """
        Calcula automáticamente la fecha de fin basándose en fecha inicio + días.
        La fecha de fin se calcula como: fecha_inicio + (días - 1)
        Ejemplo: Si inicia el 1 de enero y son 3 días, termina el 3 de enero.
        """
        from datetime import timedelta
        if self.fechaini and self.dias_ausentismo:
            # Restar 1 porque el día de inicio cuenta como día 1
            self.fechafin = self.fechaini + timedelta(days=self.dias_ausentismo - 1)
        super().save(*args, **kwargs)

    @property
    def dias_totales(self):
        """
        Calcula los días totales del ausentismo.
        
        Returns:
            int: Cantidad total de días del ausentismo
        """
        if self.fechaini and self.fechafin:
            return (self.fechafin - self.fechaini).days + 1
        return self.dias_ausentismo if hasattr(self, 'dias_ausentismo') else 0
    
    @property
    def esta_activo(self):
        """
        Determina si el ausentismo está activo basándose en la fecha de fin.
        
        Returns:
            bool: True si la fecha de fin es mayor o igual a hoy, False en caso contrario
        """
        from datetime import date
        return self.fechafin >= date.today() if self.fechafin else False

    def __str__(self):
        apemat_str = f" {self.personal_id.apemat}" if self.personal_id.apemat else ""
        trabajador = f"{self.personal_id.nombre} {self.personal_id.apepat}{apemat_str}"
        return f"{self.tipoausen_id} - {trabajador} ({self.fechaini} a {self.fechafin})"


# ============================================================================
# MODELOS DE PROVEEDORES
# ============================================================================

class Proveedor(models.Model):
    """
    Modelo para almacenar información de proveedores externos.
    Se utiliza para registrar proveedores de servicios médicos, exámenes, certificaciones, etc.
    """
    proveedor_id = models.AutoField(primary_key=True, null=False, blank=False)
    region_id = models.ForeignKey(Region, on_delete=models.CASCADE, db_column='region_id', null=False, blank=False)
    comuna_id = models.ForeignKey(Comuna, on_delete=models.CASCADE, db_column='comuna_id', null=False, blank=False)
    rut = models.CharField(max_length=8, null=False, blank=False)
    dvRut = models.CharField(max_length=1, null=False, blank=False)
    razonSocial = models.CharField(max_length=100, null=False, blank=False)
    nombreFant = models.CharField(max_length=100, null=True, blank=True)
    giro = models.CharField(max_length=100, null=False, blank=False)
    direccion = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.razonSocial
    


class TipoClasificacion(models.Model):
    """
    Modelo para clasificar proveedores por tipo.
    Ejemplos: Clínica, Laboratorio, Centro de Exámenes, etc.
    """
    tipoClasi_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipo = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.tipo 



class ClasificacionProveedor(models.Model):
    """
    Modelo de relación muchos a muchos entre Proveedor y TipoClasificacion.
    Permite que un proveedor tenga múltiples clasificaciones.
    """
    clasifProv_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoClasi_id = models.ForeignKey(TipoClasificacion, on_delete=models.CASCADE, db_column='tipoClasi_id', null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)


# ============================================================================
# MODELOS DE EXÁMENES
# ============================================================================

class TipoExamen(models.Model):
    """
    Modelo para almacenar los tipos de exámenes médicos.
    Ejemplos: Examen de Vista, Examen de Audición, Examen Psicológico, etc.
    """
    tipoEx_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoExamen = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoExamen 
 

class ResultadoExamen(models.Model):
    """
    Modelo para almacenar los posibles resultados de un examen.
    Ejemplos: Apto, No Apto, Apto con Restricciones, etc.
    """
    resultadoEx_id = models.AutoField(primary_key=True, null=False, blank=False)
    resultado = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.resultado


class Examen(models.Model):
    """
    Modelo que registra los exámenes médicos realizados al personal.
    Incluye tipo de examen, resultado, proveedor, fechas y documento asociado.
    """
    examen_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoEx_id = models.ForeignKey(TipoExamen, on_delete=models.CASCADE, db_column='tipoEx_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    resultadoEx_id = models.ForeignKey(ResultadoExamen, on_delete=models.CASCADE, db_column='resultadoEx_id', null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)
    fechaEmision = models.DateField(null=False, blank=False)
    fechaVencimiento = models.DateField(null=False, blank=False)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, storage=MediaS3Storage(), null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.personal_id} - {self.tipoEx_id}"
    
    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete.
        
        NOTA: El archivo físico NO se elimina aquí porque la señal pre_delete
        ya lo copia a la carpeta de eliminados antes de que se ejecute este método.
        El archivo original se eliminará automáticamente cuando se elimine el registro
        del modelo (si está en S3) o permanecerá en eliminados (si se copió correctamente).
        """
        # La señal pre_delete ya maneja la copia del archivo a eliminados
        # Solo eliminamos el registro de la base de datos
        super().delete(*args, **kwargs)



# ============================================================================
# MODELOS DE CERTIFICACIONES
# ============================================================================

class TipoCertificacion(models.Model):
    """
    Modelo para almacenar los tipos de certificaciones.
    Ejemplos: Certificación de Operador de Grúa, Certificación de Altura, etc.
    """
    tipoCertificacion_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoCertificacion = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoCertificacion


class Certificacion(models.Model):
    """
    Modelo que registra las certificaciones obtenidas por el personal.
    Incluye tipo de certificación, proveedor, fechas y documento asociado.
    """
    certif_id = models.AutoField(primary_key=True, null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)
    tipoCertificacion_id = models.ForeignKey(TipoCertificacion, on_delete=models.CASCADE, db_column='tipoCertificacion_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False) 
    fechaEmision = models.DateField(null=False, blank=False)
    fechaVencimiento = models.DateField(null=False, blank=False)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, storage=MediaS3Storage(), null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.personal_id} - {self.tipoCertificacion_id}"

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete.
        
        NOTA: El archivo físico NO se elimina aquí porque la señal pre_delete
        ya lo copia a la carpeta de eliminados antes de que se ejecute este método.
        El archivo original se eliminará automáticamente cuando se elimine el registro
        del modelo (si está en S3) o permanecerá en eliminados (si se copió correctamente).
        """
        # La señal pre_delete ya maneja la copia del archivo a eliminados
        # Solo eliminamos el registro de la base de datos
        super().delete(*args, **kwargs)


# ============================================================================
# MODELOS DE LICENCIAS DE CONDUCIR
# ============================================================================

class TipoLicencia(models.Model):
    """
    Modelo para almacenar los tipos de licencias de conducir.
    Ejemplos: Clase A, Clase B, Clase C, Clase D, Clase E, etc.
    """
    tipoLicencia_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoLicencia = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoLicencia

class LicenciaPorPersonal(models.Model):
    """
    Modelo que registra las licencias de conducir del personal.
    Una licencia puede tener múltiples tipos (ManyToMany).
    Incluye fechas de emisión y vencimiento, y documento asociado.
    """
    licenciaPorPersonal_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    tipos = models.ManyToManyField(TipoLicencia, related_name='licencias_personales')
    fechaEmision = models.DateField(null=False, blank=False)
    fechaVencimiento = models.DateField(null=False, blank=False)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, storage=OverwriteStorage(), null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def __str__(self):
        tipos_str = ", ".join([t.tipoLicencia for t in self.tipos.all()])
        return f"Licencia de {self.personal_id} (Tipos: {tipos_str or 'Ninguno'})"

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete.
        
        NOTA: El archivo físico NO se elimina aquí porque la señal pre_delete
        ya lo copia a la carpeta de eliminados antes de que se ejecute este método.
        El archivo original se eliminará automáticamente cuando se elimine el registro
        del modelo (si está en S3) o permanecerá en eliminados (si se copió correctamente).
        """
        # La señal pre_delete ya maneja la copia del archivo a eliminados
        # Solo eliminamos el registro de la base de datos
        super().delete(*args, **kwargs)




# ============================================================================
# MODELOS DE LICENCIAS MÉDICAS
# ============================================================================

class TipoLicenciaMedica(models.Model):
    """
    Modelo para almacenar los tipos de licencias médicas.
    Ejemplos: Enfermedad Común, Accidente del Trabajo, Enfermedad Profesional, etc.
    """
    tipoLicenciaMedica_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoLicenciaMedica = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoLicenciaMedica

class LicenciaMedicaPorPersonal(models.Model):
    """
    Modelo que registra las licencias médicas del personal.
    Calcula automáticamente la fecha de fin basándose en la fecha de emisión y los días.
    """
    licenciaMedicaPorPersonal_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    tipoLicenciaMedica_id = models.ForeignKey(TipoLicenciaMedica, on_delete=models.CASCADE, db_column='tipoLicenciaMedica_id', null=False, blank=False)
    fechaEmision = models.DateField(null=False, blank=False, verbose_name='Fecha de Emisión')
    dias_licencia = models.IntegerField(null=False, blank=False, verbose_name='Días de Licencia')
    fecha_fin_licencia = models.DateField(null=False, blank=False, editable=False, default=datetime.now, verbose_name='Fecha de Fin')
    observacion = models.TextField(max_length=250, null=True, blank=True, verbose_name='Observaciones')

    def save(self, *args, **kwargs):
        """
        Calcula automáticamente la fecha de fin basándose en fecha emisión + días.
        La fecha de fin se calcula como: fecha_emision + (días - 1)
        Ejemplo: Si se emite el 1 de enero y son 3 días, termina el 3 de enero.
        """
        from datetime import timedelta
        if self.fechaEmision and self.dias_licencia:
            # Restar 1 porque el día de emisión cuenta como día 1
            self.fecha_fin_licencia = self.fechaEmision + timedelta(days=self.dias_licencia - 1)
        super().save(*args, **kwargs)

    @property
    def esta_activa(self):
        """
        Determina si la licencia médica está activa basándose en la fecha de fin.
        
        Returns:
            bool: True si la fecha de fin es mayor o igual a hoy, False en caso contrario
        """
        from datetime import date
        return self.fecha_fin_licencia >= date.today() if self.fecha_fin_licencia else False

    def __str__(self):
        return f"Licencia Médica de {self.personal_id} - {self.tipoLicenciaMedica_id}"
    
    class Meta:
        db_table = 'licencia_medica_por_personal'
        verbose_name = 'Licencia Médica'
        verbose_name_plural = 'Licencias Médicas'
        ordering = ['-fechaEmision']


# ============================================================================
# MODELOS DE LICENCIAS INTERNAS DE CONDUCIR
# ============================================================================

class TipoLicenciaInterna(models.Model):
    """
    Modelo para almacenar los tipos de licencias internas de conducir.
    Estas son licencias emitidas por la empresa/faena, no por el estado.
    Ejemplos: Tipo A (Vehículos Ligeros), Tipo B (Vehículos Pesados), etc.
    """
    tipoLicenciaInterna_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoLicenciaInterna = models.CharField(max_length=100, null=False, blank=False, verbose_name='Tipo de Licencia Interna')
    descripcion = models.TextField(max_length=250, null=True, blank=True, verbose_name='Descripción')
    
    class Meta:
        db_table = 'tipo_licencia_interna'
        verbose_name = 'Tipo de Licencia Interna'
        verbose_name_plural = 'Tipos de Licencias Internas'
        ordering = ['tipoLicenciaInterna']
    
    def __str__(self):
        return self.tipoLicenciaInterna


class LicenciaInternaPorPersonal(models.Model):
    """
    Modelo que registra las licencias internas de conducir emitidas por la empresa/faena.
    Estas licencias son específicas de la empresa y pueden tener diferentes requisitos
    que las licencias estatales.
    """
    licenciaInterna_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(
        Personal, 
        on_delete=models.CASCADE, 
        db_column='personal_id', 
        null=False, 
        blank=False,
        related_name='licencias_internas'
    )
    tipoLicenciaInterna_id = models.ForeignKey(
        TipoLicenciaInterna,
        on_delete=models.CASCADE,
        db_column='tipoLicenciaInterna_id',
        null=False,
        blank=False,
        verbose_name='Tipo de Licencia Interna'
    )
    numero_licencia = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name='N° de Licencia Interna'
    )
    fechaEmision = models.DateField(null=False, blank=False, verbose_name='Fecha de Emisión')
    fechaVencimiento = models.DateField(null=False, blank=False, verbose_name='Fecha de Vencimiento')
    empresa_emisora = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name='Empresa/Faena Emisora',
        help_text='Empresa o faena que emitió la licencia interna'
    )
    rutaDoc = models.FileField(
        upload_to=obtener_ruta_documento, 
        storage=OverwriteStorage(), 
        null=False, 
        blank=False,
        default=None,
        verbose_name='Documento'
    )
    observacion = models.TextField(max_length=250, null=True, blank=True, verbose_name='Observaciones')
    
    @property
    def esta_activa(self):
        """
        Determina si la licencia está activa basándose en la fecha de vencimiento.
        
        Returns:
            bool: True si la fecha de vencimiento es mayor o igual a hoy, False en caso contrario
        """
        from datetime import date
        return self.fechaVencimiento >= date.today() if self.fechaVencimiento else False
    
    class Meta:
        db_table = 'licencia_interna_por_personal'
        verbose_name = 'Licencia Interna de Conducir'
        verbose_name_plural = 'Licencias Internas de Conducir'
        ordering = ['-fechaEmision']

    def __str__(self):
        return f"Licencia Interna de {self.personal_id} - {self.tipoLicenciaInterna_id.tipoLicenciaInterna}"
    
    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete.
        
        NOTA: El archivo físico NO se elimina aquí porque la señal pre_delete
        ya lo copia a la carpeta de eliminados antes de que se ejecute este método.
        El archivo original se eliminará automáticamente cuando se elimine el registro
        del modelo (si está en S3) o permanecerá en eliminados (si se copió correctamente).
        """
        # La señal pre_delete ya maneja la copia del archivo a eliminados
        # Solo eliminamos el registro de la base de datos
        super().delete(*args, **kwargs)


# ============================================================================
# MODELOS DE HISTORIAL PARA AUDITORÍA Y REPORTABILIDAD
# ============================================================================

class HistorialPersonal(models.Model):
    """
    Registra todos los cambios y acciones realizadas en el Personal.
    Permite auditoría completa de modificaciones, activaciones/desactivaciones.
    """
    ACCION_CHOICES = [
        ('PERSONAL_CREADO', 'Personal Creado'),
        ('PERSONAL_MODIFICADO', 'Personal Modificado'),
        ('PERSONAL_ACTIVADO', 'Personal Activado'),
        ('PERSONAL_DESACTIVADO', 'Personal Desactivado'),
        ('PERSONAL_ELIMINADO', 'Personal Eliminado'),
    ]
    
    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name="historial",
        db_index=True,
        verbose_name='Personal'
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
        verbose_name = "Historial de Personal"
        verbose_name_plural = "Historial de Personal"
        db_table = 'rrhh_personal_historialpersonal'
        indexes = [
            models.Index(fields=["personal", "-fecha_hora"]),
            models.Index(fields=["usuario", "-fecha_hora"]),
        ]
    
    def __str__(self):
        return f"{self.personal.nombre} {self.personal.apepat} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, personal, accion, descripcion, usuario=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial.
        """
        return cls.objects.create(
            personal=personal,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )


class HistorialDocumentoPersonal(models.Model):
    """
    Registra todos los cambios en documentos del personal (agregado, eliminado, modificado).
    Incluye documentos personales, licencias, certificaciones, exámenes, etc.
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('DOCUMENTO_PERSONAL', 'Documento Personal'),
        ('LICENCIA_CONDUCIR', 'Licencia de Conducir'),
        ('LICENCIA_INTERNA', 'Licencia Interna'),
        ('LICENCIA_MEDICA', 'Licencia Médica'),
        ('CERTIFICACION', 'Certificación'),
        ('EXAMEN', 'Examen'),
    ]
    
    ACCION_CHOICES = [
        ('DOCUMENTO_AGREGADO', 'Documento Agregado'),
        ('DOCUMENTO_MODIFICADO', 'Documento Modificado'),
        ('DOCUMENTO_ELIMINADO', 'Documento Eliminado'),
        ('DOCUMENTO_REEMPLAZADO', 'Documento Reemplazado'),
    ]
    
    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name="historial_documentos",
        db_index=True,
        verbose_name='Personal'
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
    tipo_documento = models.CharField(
        max_length=50,
        choices=TIPO_DOCUMENTO_CHOICES,
        help_text="Tipo de documento afectado",
        verbose_name='Tipo de Documento'
    )
    accion = models.CharField(
        max_length=50,
        choices=ACCION_CHOICES,
        help_text="Tipo de acción realizada",
        verbose_name='Acción'
    )
    nombre_documento = models.CharField(
        max_length=255,
        help_text="Nombre o descripción del documento",
        verbose_name='Nombre del Documento'
    )
    campo_documento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Campo del modelo donde se almacena (si aplica)",
        verbose_name='Campo del Documento'
    )
    archivo_ruta = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Ruta del archivo (si fue eliminado, se guarda la ruta anterior)",
        verbose_name='Ruta del Archivo'
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
        verbose_name = "Historial de Documento de Personal"
        verbose_name_plural = "Historial de Documentos de Personal"
        db_table = 'rrhh_personal_historialdocumentopersonal'
        indexes = [
            models.Index(fields=["personal", "-fecha_hora"]),
            models.Index(fields=["usuario", "-fecha_hora"]),
            models.Index(fields=["tipo_documento", "-fecha_hora"]),
        ]
    
    def __str__(self):
        return f"{self.personal.nombre} {self.personal.apepat} - {self.get_tipo_documento_display()} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, personal, tipo_documento, accion, nombre_documento, descripcion, usuario=None, campo_documento=None, archivo_ruta=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial de documentos.
        """
        return cls.objects.create(
            personal=personal,
            tipo_documento=tipo_documento,
            accion=accion,
            nombre_documento=nombre_documento,
            descripcion=descripcion,
            usuario=usuario,
            campo_documento=campo_documento,
            archivo_ruta=archivo_ruta,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )
