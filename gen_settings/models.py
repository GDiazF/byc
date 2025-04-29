from django.db import models

# Create your models here.

class Region(models.Model):
    nombre = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'

class Comuna(models.Model):
    nombre = models.CharField(max_length=100, null=False, blank=False)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'

class Empresa(models.Model):
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

class UnidadMedida(models.Model):
    codigo = models.CharField(max_length=3, unique=True, null=False, blank=False)
    descripcion = models.CharField(max_length=100, null=False, blank=False)

