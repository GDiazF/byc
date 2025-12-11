"""
============================================================================
MODELOS PARA GEN_SETTINGS
============================================================================
Este módulo define los modelos para configuraciones generales del sistema:
- Region: Regiones de Chile
- Comuna: Comunas asociadas a regiones
- Empresa: Empresas del sistema
- UnidadMedida: Unidades de medida para inventarios y otros usos
============================================================================
"""

from django.db import models


class Region(models.Model):
    """
    Modelo para representar una región de Chile.
    
    Almacena información básica de las regiones que se utilizan
    para asociar direcciones y ubicaciones geográficas.
    """
    nombre = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'

class Comuna(models.Model):
    """
    Modelo para representar una comuna de Chile.
    
    Cada comuna está asociada a una región. Se utiliza junto con
    Region para formar direcciones completas y ubicaciones geográficas.
    """
    nombre = models.CharField(max_length=100, null=False, blank=False)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'

class Empresa(models.Model):
    """
    Modelo para representar una empresa del sistema.
    
    Almacena información completa de empresas incluyendo datos fiscales,
    contacto y ubicación. Se utiliza en múltiples módulos del sistema
    para asociar recursos (personal, equipos, etc.) a empresas.
    """
    rut = models.CharField(max_length=10, unique=True, null=False, blank=False)
    dv = models.CharField(max_length=1, null=False, blank=False)
    razonSocial = models.CharField(max_length=100, null=False, blank=False)
    nomFantasia = models.CharField(max_length=100)
    giro = models.CharField(max_length=100, null=False, blank=False)
    direccion = models.CharField(max_length=100, null=False, blank=False)
    telefono = models.CharField(max_length=12, null=False, blank=False)
    email = models.EmailField(max_length=100, null=False, blank=False)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    comuna = models.ForeignKey(Comuna, on_delete=models.CASCADE)

    def __str__(self):
        return self.nomFantasia

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

class UnidadMedida(models.Model):
    """
    Modelo para representar una unidad de medida.
    
    Catálogo de unidades de medida utilizadas en el sistema para
    inventarios, materiales, repuestos y otros elementos que requieren
    especificar cantidad con unidad (ej: kg, litros, metros, unidades).
    """
    codigo = models.CharField(max_length=3, unique=True, null=False, blank=False)
    descripcion = models.CharField(max_length=100, null=False, blank=False)

