"""
Custom storage classes for AWS S3 integration
"""
import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class OverwriteS3Storage(S3Boto3Storage):
    """
    Custom S3 storage that overwrites existing files instead of creating new ones
    """
    
    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's available for use in the target storage system.
        If the file exists, it will be overwritten (deleted first).
        """
        # For S3, we don't need to check if file exists locally
        # S3 will overwrite automatically when we upload with the same key
        return name
    
    def _save(self, name, content):
        """
        Save the file to S3, overwriting if it exists
        """
        # S3 naturally overwrites files with the same key
        return super()._save(name, content)


class MediaS3Storage(OverwriteS3Storage):
    """
    Storage for media files (user uploads) on S3
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = 'media'  # Folder in S3 bucket for media files
    default_acl = 'private'  # Keep documents private
    
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = self.bucket_name
        kwargs['location'] = self.location
        kwargs['default_acl'] = self.default_acl
        super().__init__(*args, **kwargs)
