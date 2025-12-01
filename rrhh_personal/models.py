from django.db import models
from datetime import datetime, date
import os
from django.core.files.storage import FileSystemStorage
from gen_settings.models import Region, Comuna, Empresa
from django.contrib.auth.models import User
# from .storage import MediaS3Storage  # Solo para producción con S3

#MODELO PARA RUTAS DE LOS DOCUMENTOS---------------------------------------------------------
def obtener_ruta_documento_personal(instance, filename):
    """
    Esta función se mantiene solo para compatibilidad con migraciones antiguas.
    Use obtener_ruta_documento en su lugar.
    """
    return obtener_ruta_documento(instance, filename)

def obtener_ruta_documento(instance, filename):
    """
    Función unificada para determinar la ruta donde se guardarán todos los documentos.
    La estructura será: Documentacion_Personal/RUT/TIPO_DOCUMENTO/archivo
    """
    extension = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Obtener el RUT y determinar el tipo de documento basado en la instancia
    if isinstance(instance, Personal):
        rut = instance.rut
        # Determinar el campo específico que se está guardando
        for field in instance._meta.fields:
            if isinstance(field, (models.FileField, models.ImageField)):
                value = getattr(instance, field.name)
                if value and value.name == filename:
                    carpeta = 'Documentos_Personales'
                    nombre_archivo = f"{field.name}_{timestamp}{extension}"
                    break
        else:
            carpeta = 'Otros'
            nombre_archivo = filename
    
    elif isinstance(instance, LicenciaPorPersonal):
        rut = instance.personal_id.rut
        carpeta = 'Licencias'
        nombre_archivo = f"licencia_{timestamp}{extension}"
    
    elif isinstance(instance, LicenciaMedicaPorPersonal):
        rut = instance.personal_id.rut
        carpeta = 'Licencias_Medicas'
        # Usar ID de la licencia para evitar conflictos entre registros
        nombre_archivo = f"licenciaMedica_{instance.licenciaMedicaPorPersonal_id or 'new'}{extension}"
    
    elif isinstance(instance, Certificacion):
        rut = instance.personal_id.rut
        carpeta = 'Certificaciones'
        nombre_archivo = f"certificacion_{instance.tipoCertificacion_id.tipoCertificacion}_{timestamp}{extension}"
    
    elif isinstance(instance, Examen):
        rut = instance.personal_id.rut
        carpeta = 'Examenes'
        nombre_archivo = f"examen_{instance.tipoEx_id.tipoExamen}_{timestamp}{extension}"
    
    else:
        rut = 'sin_rut'
        carpeta = 'Otros'
        nombre_archivo = filename
    
    # Retornar la ruta relativa (MEDIA_ROOT ya incluye la carpeta base)
    return os.path.join(str(rut), carpeta, nombre_archivo)

def mover_archivo_a_eliminados(archivo_field, personal_rut, nombre_documento):
    """
    Mueve un archivo a la carpeta de eliminados en lugar de eliminarlo.
    Estructura: Documentacion_Eliminada/RUT/nombre_documento.pdf
    
    Args:
        archivo_field: Campo FileField del modelo
        personal_rut: RUT del personal (string)
        nombre_documento: Nombre descriptivo del documento (ej: "Curriculum Vitae")
    
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
        # Formato: RUT_nombre_documento.pdf
        nombre_limpio = nombre_documento.lower().replace(' ', '_').replace('/', '_')
        # Obtener extensión del archivo original
        extension = os.path.splitext(archivo_field.name)[1]
        nombre_archivo_final = f"{personal_rut}_{nombre_limpio}{extension}"
        
        # Ruta destino: Documentacion_Eliminada/RUT/nombre_documento.pdf
        carpeta_eliminados = os.path.join(settings.MEDIA_ROOT, 'Documentacion_Eliminada', str(personal_rut))
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
        ruta_relativa = os.path.join('Documentacion_Eliminada', str(personal_rut), nombre_archivo_final)
        return ruta_relativa
        
    except Exception as e:
        # Si falla el movimiento, intentar eliminar normalmente
        print(f"Error al mover archivo a eliminados: {str(e)}")
        try:
            archivo_field.delete(save=False)
        except:
            pass
        return None

#RUTA PARA SOBREESCRIBIR ARCHIVO
# ============================================================================
# CONFIGURACIÓN PARA DESARROLLO LOCAL
# ============================================================================
class OverwriteStorage(FileSystemStorage):
    """
    Storage class para desarrollo local que sobrescribe archivos existentes
    """
    def get_available_name(self, name, max_length=None):
        # Eliminar archivo existente si existe
        if self.exists(name):
            self.delete(name)
        return name

# ============================================================================
# CONFIGURACIÓN PARA PRODUCCIÓN EN NUBE (COMENTADO)
# ============================================================================
# class OverwriteStorage(MediaS3Storage):
#     """
#     Storage class that uses S3 and overwrites existing files
#     """
#     def get_available_name(self, name, max_length=None):
#         # S3 naturally overwrites files with the same key
#         return name

class Sexo(models.Model):
    sexo_id = models.AutoField(primary_key=True, null=False, blank=False)
    sexo = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.sexo
    
    class Meta:
        db_table = 'sexo'

class EstadoCivil(models.Model):
    estcivil_id = models.AutoField(primary_key=True, null=False, blank=False)
    estadocivil = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.estadocivil
    
    class Meta:
        db_table = 'estadocivil'


class Personal(models.Model):
    personal_id = models.AutoField(primary_key=True, null=False, blank=False)
    sexo_id = models.ForeignKey(Sexo, on_delete=models.CASCADE, db_column='sexo_id', null=True, blank=True)
    estcivil_id = models.ForeignKey(EstadoCivil, on_delete=models.CASCADE, db_column='estcivil_id', null=True, blank=True)
    region_id = models.ForeignKey(Region, on_delete=models.CASCADE, db_column='region_id', null=True, blank=True)
    comuna_id = models.ForeignKey(Comuna, on_delete=models.CASCADE, db_column='comuna_id', null=True, blank=True)
    rut = models.CharField(max_length=8, null=False, blank=False, unique=True)
    dvrut = models.CharField(max_length=1, null=False, blank=False)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apepat = models.CharField(max_length=50, null=False, blank=False)
    apemat = models.CharField(max_length=50)
    fechanac = models.DateField(null=True, blank=True)
    correo = models.CharField(max_length=100, null=False, blank=False, unique=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
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
        return self.nombre + " " + self.apepat + " " + self.apemat
    
    def get_licencias_activas_count(self):
        """Retorna la cantidad de licencias médicas activas del personal"""
        from datetime import date
        return self.licenciamedicaporpersonal_set.filter(
            fecha_fin_licencia__gte=date.today()
        ).count()
    
    def get_ausentismos_activos_count(self):
        """Retorna la cantidad de ausentismos activos del personal"""
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
        self.rut = self.rut.upper()
        self.dvrut = self.dvrut.upper()
        self.nombre = self.nombre.upper()
        self.apepat = self.apepat.upper()
        self.apemat = self.apemat.upper()
        self.correo = self.correo.upper()
        self.direccion = self.direccion.upper() if self.direccion else None
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Lista de campos de archivo
        file_fields = [
            'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
            'foto_carnet', 'certificado_afp', 'certificado_salud',
            'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
            'fotocopia_finiquito', 'comprobante_banco'
        ]
        
        # Eliminar cada archivo
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
            
        super().delete(*args, **kwargs)



class DeptoEmpresa(models.Model):
    depto_id = models.AutoField(primary_key=True, blank=False, null=False)
    depto = models.CharField(max_length=50, db_column='depto', blank=False, null=False)

    def __str__(self):
        return self.depto


class Cargo(models.Model):
    cargo_id = models.AutoField(primary_key=True, blank=False, null=False)
    depto_id = models.ForeignKey(DeptoEmpresa, on_delete=models.CASCADE, db_column='depto_id', blank=False, null=False)
    cargo = models.CharField(max_length=50, db_column='cargo', blank=False, null=False)

    def __str__(self):
        return self.cargo


class InfoLaboral(models.Model):
    infolab_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    empresa_id = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column='empresa_id', null=False, blank=False)
    depto_id = models.ForeignKey(DeptoEmpresa, on_delete=models.CASCADE, db_column='depto_id', null=False, blank=False)
    cargo_id = models.ForeignKey(Cargo, on_delete=models.CASCADE, db_column='cargo_id',blank=False, null=False)
    fechacontrata = models.DateField(blank=False, null=False)


class TipoAusentismo(models.Model):
    tipoausen_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipo = models.CharField(max_length=100, null=False, blank=False, db_column='tipo' )

    def __str__(self):
        return self.tipo


class Ausentismo(models.Model):
    ausentismo_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoausen_id = models.ForeignKey(TipoAusentismo, on_delete=models.CASCADE, db_column='tipoausen_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    fechaini = models.DateField(null=False, blank=False, verbose_name='Fecha de Inicio')
    dias_ausentismo = models.IntegerField(null=False, blank=False, verbose_name='Días de Ausentismo', default=1)
    fechafin = models.DateField(null=False, blank=False, editable=False, verbose_name='Fecha de Fin')
    observacion = models.TextField(max_length=250, blank=True, null=True, verbose_name='Observaciones')

    def save(self, *args, **kwargs):
        """Calcula automáticamente la fecha de fin basándose en fecha inicio + días"""
        from datetime import timedelta
        if self.fechaini and self.dias_ausentismo:
            self.fechafin = self.fechaini + timedelta(days=self.dias_ausentismo - 1)
        super().save(*args, **kwargs)

    @property
    def dias_totales(self):
        """Calcula los días totales del ausentismo"""
        if self.fechaini and self.fechafin:
            return (self.fechafin - self.fechaini).days + 1
        return self.dias_ausentismo if hasattr(self, 'dias_ausentismo') else 0
    
    @property
    def esta_activo(self):
        """Determina si el ausentismo está activo basándose en la fecha de fin"""
        from datetime import date
        return self.fechafin >= date.today() if self.fechafin else False

    def __str__(self):
        trabajador = f"{self.personal_id.nombre} {self.personal_id.apepat} {self.personal_id.apemat}"
        return f"{self.tipoausen_id} - {trabajador} ({self.fechaini} a {self.fechafin})"


#PROVEEDOR -------------------------------------------------------------------------------------

class Proveedor(models.Model):
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
    tipoClasi_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipo = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.tipo 



class ClasificacionProveedor(models.Model):
    clasifProv_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoClasi_id = models.ForeignKey(TipoClasificacion, on_delete=models.CASCADE, db_column='tipoClasi_id', null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)


#----------------------------------------------------------------------------------------- 


#EXAMENES---------------------------------------------------------------------------------
class TipoExamen(models.Model):
    tipoEx_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoExamen = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoExamen
 

class ResultadoExamen(models.Model):
    resultadoEx_id = models.AutoField(primary_key=True, null=False, blank=False)
    resultado = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.resultado


class Examen(models.Model):
    examen_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoEx_id = models.ForeignKey(TipoExamen, on_delete=models.CASCADE, db_column='tipoEx_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    resultadoEx_id = models.ForeignKey(ResultadoExamen, on_delete=models.CASCADE, db_column='resultadoEx_id', null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)
    fechaEmision = models.DateField(null=False, blank=False)
    fechaVencimiento = models.DateField(null=False, blank=False)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.personal_id} - {self.tipoEx_id}"
    
    def delete(self, *args, **kwargs):
        if self.rutaDoc:
            file_path = self.rutaDoc.path
            if os.path.isfile(file_path):
                os.remove(file_path)
            
            # Intentar eliminar la carpeta Examenes si está vacía
            exam_folder = os.path.dirname(file_path)
            if os.path.exists(exam_folder) and not os.listdir(exam_folder):
                os.rmdir(exam_folder)
                
        super().delete(*args, **kwargs)



#---------------------------------------------------------------------------------------------
#CERTIFICACION---------------------------------------------------------------------------------

class TipoCertificacion(models.Model):
    tipoCertificacion_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoCertificacion = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoCertificacion


class Certificacion(models.Model):
    certif_id = models.AutoField(primary_key=True, null=False, blank=False)
    proveedor_id = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='proveedor_id', null=False, blank=False)
    tipoCertificacion_id = models.ForeignKey(TipoCertificacion, on_delete=models.CASCADE, db_column='tipoCertificacion_id', null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False) 
    fechaEmision = models.DateField(null=False, blank=False)
    fechaVencimiento = models.DateField(null=False, blank=False)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.personal_id} - {self.tipoCertificacion_id}"

    def delete(self, *args, **kwargs):
        if self.rutaDoc:
            file_path = self.rutaDoc.path
            if os.path.isfile(file_path):
                os.remove(file_path)
            
            # Intentar eliminar la carpeta Certificaciones si está vacía
            cert_folder = os.path.dirname(file_path)
            if os.path.exists(cert_folder) and not os.listdir(cert_folder):
                os.rmdir(cert_folder)
                
        super().delete(*args, **kwargs)


#---------------------------------------------------------------------------------------------
#LICENCIAS-------------------------------------------------------------------------------------

class TipoLicencia(models.Model):
    tipoLicencia_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoLicencia = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoLicencia

class LicenciaPorPersonal(models.Model):
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
        # Guardar la ruta del archivo antes de eliminar el registro
        if self.rutaDoc:
            file_path = self.rutaDoc.path
            if os.path.isfile(file_path):
                os.remove(file_path)
            
            # Intentar eliminar la carpeta Licencias si está vacía
            license_folder = os.path.dirname(file_path)
            if os.path.exists(license_folder) and not os.listdir(license_folder):
                os.rmdir(license_folder)
                
        super().delete(*args, **kwargs)




#---------------------------------------------------------------------------------------------
#LICENCIAS MEDICAS-------------------------------------------------------------------------------------

class TipoLicenciaMedica(models.Model):
    tipoLicenciaMedica_id = models.AutoField(primary_key=True, null=False, blank=False)
    tipoLicenciaMedica = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.tipoLicenciaMedica

class LicenciaMedicaPorPersonal(models.Model):
    licenciaMedicaPorPersonal_id = models.AutoField(primary_key=True, null=False, blank=False)
    personal_id = models.ForeignKey(Personal, on_delete=models.CASCADE, db_column='personal_id', null=False, blank=False)
    tipoLicenciaMedica_id = models.ForeignKey(TipoLicenciaMedica, on_delete=models.CASCADE, db_column='tipoLicenciaMedica_id', null=False, blank=False)
    fechaEmision = models.DateField(null=False, blank=False, verbose_name='Fecha de Emisión')
    dias_licencia = models.IntegerField(null=False, blank=False, verbose_name='Días de Licencia')
    fecha_fin_licencia = models.DateField(null=False, blank=False, editable=False, default=datetime.now, verbose_name='Fecha de Fin')
    observacion = models.TextField(max_length=250, null=True, blank=True, verbose_name='Observaciones')

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if self.fechaEmision and self.dias_licencia:
            self.fecha_fin_licencia = self.fechaEmision + timedelta(days=self.dias_licencia - 1)
        super().save(*args, **kwargs)

    @property
    def esta_activa(self):
        """Determina si la licencia médica está activa basándose en la fecha de fin"""
        from datetime import date
        return self.fecha_fin_licencia >= date.today() if self.fecha_fin_licencia else False

    def __str__(self):
        return f"Licencia Médica de {self.personal_id} - {self.tipoLicenciaMedica_id}"
    
    class Meta:
        db_table = 'licencia_medica_por_personal'
        verbose_name = 'Licencia Médica'
        verbose_name_plural = 'Licencias Médicas'
        ordering = ['-fechaEmision']


#---------------------------------------------------------------------------------------------
#LICENCIAS INTERNAS DE CONDUCIR------------------------------------------------------------

class TipoLicenciaInterna(models.Model):
    """Tipos de licencias internas de conducir (A, B, C, D, E, etc.)"""
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
    """Licencias internas de conducir emitidas por la empresa/faena"""
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
        """Determina si la licencia está activa basándose en la fecha de vencimiento"""
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
        # Guardar la ruta del archivo antes de eliminar el registro
        if self.rutaDoc:
            try:
                file_path = self.rutaDoc.path
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Archivo eliminado: {file_path}")
                
                # Intentar eliminar la carpeta si está vacía
                license_folder = os.path.dirname(file_path)
                if os.path.exists(license_folder) and not os.listdir(license_folder):
                    os.rmdir(license_folder)
                    print(f"Carpeta vacía eliminada: {license_folder}")
                    
            except Exception as e:
                print(f"Error al eliminar archivo de licencia interna: {e}")
                
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
