from django.db import models
from gen_settings.models import Empresa

# Create your models here.

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
    
    def __str__(self):
        return f"{self.nombre} - {self.modeloEquipo_id}"


class ItemPauta(models.Model):
    """Relación entre una pauta, una sección y sus tipos de reparación"""
    itemPauta_id = models.AutoField(primary_key=True, null=False, blank=False)
    pauta_id = models.ForeignKey(PautaMantenimientoPreventivo, on_delete=models.CASCADE, db_column='pauta_id', related_name='items', null=False, blank=False)
    seccion_id = models.ForeignKey(Seccion, on_delete=models.CASCADE, db_column='seccion_id', related_name='items_pauta', null=False, blank=False)
    tipos_reparacion = models.ManyToManyField(TipoReparacion, related_name='items_pauta')
    
    class Meta:
        db_table = 'maquinarias_itempauta'
        verbose_name = 'Item de Pauta'
        verbose_name_plural = 'Items de Pauta'
        unique_together = [['pauta_id', 'seccion_id']]
    
    def __str__(self):
        return f"{self.pauta_id.nombre} - {self.seccion_id.nombre}"
