from django.db import models
from datetime import datetime
import os
from django.core.files.storage import FileSystemStorage
from gen_settings.models import Region, Comuna, Empresa

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
    
    # Retornar la ruta completa
    return os.path.join('Documentacion_Personal', str(rut), carpeta, nombre_archivo)

#RUTA PARA SOBREESCRIBIR ARCHIVO
class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # Si el archivo existe, lo elimina
        if self.exists(name):
            try:
                file_path = os.path.join(self.location, name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Archivo sobrescrito: {file_path}")
            except Exception as e:
                print(f"Error al sobrescribir archivo {name}: {e}")
        return name

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
    
    class Meta:
        db_table = 'Personal'

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
    fechaini = models.DateField(null=False, blank=False)
    fechafin = models.DateField(null=False, blank=False)
    observacion = models.TextField(max_length=250, blank=True, null=True)

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
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, storage=OverwriteStorage, null=False, blank=False)
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
    numero_folio = models.CharField(max_length=50, null=True, blank=True, verbose_name='N° Folio', default='0')
    fechaEmision = models.DateField(null=False, blank=False)
    dias_licencia = models.IntegerField(null=False, blank=False)
    fecha_fin_licencia = models.DateField(null=False, blank=False, editable=False, default=datetime.now)
    rutaDoc = models.FileField(upload_to=obtener_ruta_documento, storage=OverwriteStorage, null=False, blank=False)
    observacion = models.TextField(max_length=250, null=True, blank=True)

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if self.fechaEmision and self.dias_licencia:
            self.fecha_fin_licencia = self.fechaEmision + timedelta(days=self.dias_licencia - 1)
        super().save(*args, **kwargs)



    def __str__(self):
        return f"Licencia Médica de {self.personal_id} - {self.tipoLicenciaMedica_id}"

    def delete(self, *args, **kwargs):
        # Guardar la ruta del archivo antes de eliminar el registro
        if self.rutaDoc:
            try:
                file_path = self.rutaDoc.path
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Archivo eliminado: {file_path}")
                
                # Intentar eliminar la carpeta Licencias_Medicas si está vacía
                license_folder = os.path.dirname(file_path)
                if os.path.exists(license_folder) and not os.listdir(license_folder):
                    os.rmdir(license_folder)
                    print(f"Carpeta vacía eliminada: {license_folder}")
                    
            except Exception as e:
                print(f"Error al eliminar archivo de licencia médica: {e}")
                
        super().delete(*args, **kwargs)


