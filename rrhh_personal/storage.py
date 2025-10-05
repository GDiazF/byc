"""
Custom storage classes for AWS S3 integration
"""
import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class OverwriteS3Storage(S3Boto3Storage):
    """
    Custom S3 storage that overwrites existing files
    """
    
    def get_available_name(self, name, max_length=None):
        """
        Returns the same name - we handle overwriting in _save
        """
        return name
    
    def _save(self, name, content):
        """
        Save the file to S3, deleting any existing file first
        """
        try:
            # Verificar si ya existe un archivo y eliminarlo
            if self.exists(name):
                print(f"Eliminando archivo existente: {name}")
                self.delete(name)
        except Exception as e:
            print(f"Error al verificar/eliminar archivo existente: {e}")
        
        # Guardar el nuevo archivo
        return super()._save(name, content)
    
    def url(self, name):
        """
        Generate URL for accessing files
        """
        try:
            # Asegurar que el nombre incluya el prefijo de location
            if hasattr(self, 'location') and self.location:
                if not name.startswith(self.location + '/'):
                    name = f"{self.location}/{name}"
            
            # Generar URL pública simple (bucket es público)
            return f"https://{self.bucket_name}.s3.amazonaws.com/{name}"
        except Exception as e:
            print(f"Error generating URL: {e}")
            return super().url(name)


class MediaS3Storage(OverwriteS3Storage):
    """
    Storage for media files (user uploads) on S3
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = 'media'
    default_acl = None
    
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = self.bucket_name
        kwargs['location'] = self.location
        kwargs['default_acl'] = self.default_acl
        super().__init__(*args, **kwargs)
