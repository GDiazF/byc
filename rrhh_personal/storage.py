"""
Clases de almacenamiento personalizadas para integración con AWS S3.

Este módulo proporciona clases de almacenamiento que permiten sobrescribir
archivos existentes en lugar de crear nuevos, útil para documentos que
pueden ser actualizados.
"""
import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class OverwriteS3Storage(S3Boto3Storage):
    """
    Almacenamiento S3 personalizado que sobrescribe archivos existentes.
    
    En lugar de generar nombres únicos para archivos duplicados,
    esta clase permite sobrescribir archivos con el mismo nombre,
    lo cual es útil para documentos que pueden ser actualizados.
    """
    
    def get_available_name(self, name, max_length=None):
        """
        Retorna un nombre de archivo disponible para usar en el sistema de almacenamiento.
        
        Si el archivo existe, será sobrescrito (eliminado primero).
        Para S3, no necesitamos verificar si el archivo existe localmente,
        ya que S3 sobrescribirá automáticamente cuando subamos con la misma clave.
        
        Args:
            name: Nombre del archivo
            max_length: Longitud máxima del nombre (no utilizado en S3)
            
        Returns:
            str: El mismo nombre del archivo (S3 sobrescribirá si existe)
        """
        # Para S3, no necesitamos verificar si el archivo existe localmente
        # S3 sobrescribirá automáticamente cuando subamos con la misma clave
        return name
    
    def _save(self, name, content):
        """
        Guarda el archivo en S3, sobrescribiendo si existe.
        
        Args:
            name: Nombre del archivo en S3
            content: Contenido del archivo a guardar
            
        Returns:
            str: Nombre del archivo guardado
        """
        # S3 sobrescribe naturalmente archivos con la misma clave
        return super()._save(name, content)


class MediaS3Storage(OverwriteS3Storage):
    """
    Almacenamiento para archivos de media (subidas de usuarios) en S3.
    
    Configura el bucket y la ubicación para archivos de media.
    NOTA: El bucket no permite ACLs (Object Ownership = Bucket owner enforced).
    La publicidad se controla mediante políticas de bucket en AWS, no mediante ACLs.
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = 'media'  # Carpeta en el bucket S3 para archivos de media
    # No configurar default_acl porque el bucket no permite ACLs
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el almacenamiento de media con la configuración de S3.
        
        Configura el nombre del bucket y la ubicación.
        NO configura ACLs porque el bucket no las permite.
        """
        kwargs['bucket_name'] = self.bucket_name
        kwargs['location'] = self.location
        # No pasar default_acl porque el bucket no permite ACLs
        # La publicidad se controla mediante políticas de bucket en AWS
        super().__init__(*args, **kwargs)
