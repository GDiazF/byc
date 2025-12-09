from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from gen_permissions.models import PermisoVista


class Command(BaseCommand):
    help = 'Crea el permiso exportar_auditoria para reportes_auditoria'

    def handle(self, *args, **options):
        # Verificar si ya existe
        codigo_permiso = 'reportes_auditoria.exportar_auditoria'
        
        permiso_vista, created = PermisoVista.objects.get_or_create(
            codigo=codigo_permiso,
            defaults={
                'nombre': 'Exportar Auditoria',
                'descripcion': 'Puede exportar eventos de auditoria a Excel',
                'app_label': 'reportes_auditoria',
                'vista_nombre': 'exportar_auditoria',
                'activo': True,
            }
        )
        
        # Crear o actualizar el Permission de Django asociado
        # Intentar usar ContentType de reportes_auditoria primero
        content_type_reportes = ContentType.objects.filter(app_label='reportes_auditoria').first()
        
        if not content_type_reportes:
            # Si no existe, crear uno dummy para reportes_auditoria
            content_type_reportes, _ = ContentType.objects.get_or_create(
                app_label='reportes_auditoria',
                model='permisovista'
            )
        
        # Buscar si ya existe el permiso (puede estar en gen_permissions o reportes_auditoria)
        permission_existente = Permission.objects.filter(codename='exportar_auditoria').first()
        
        if permission_existente:
            # Si existe pero esta en otra app, actualizarlo
            if permission_existente.content_type.app_label != 'reportes_auditoria':
                permission_existente.content_type = content_type_reportes
                permission_existente.name = 'Puede exportar auditoria'
                permission_existente.save()
                self.stdout.write(self.style.SUCCESS(f'Permission actualizado a reportes_auditoria'))
            permission = permission_existente
        else:
            # Crear nuevo permiso
            permission, perm_created = Permission.objects.get_or_create(
                codename='exportar_auditoria',
                content_type=content_type_reportes,
                defaults={'name': 'Puede exportar auditoria'}
            )
            if perm_created:
                self.stdout.write(self.style.SUCCESS(f'Permission de Django creado'))
        
        # Asociar el Permission al PermisoVista
        if not permiso_vista.permission or permiso_vista.permission != permission:
            permiso_vista.permission = permission
            permiso_vista.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'Permiso {codigo_permiso} creado exitosamente'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Permiso {codigo_permiso} actualizado'))
        else:
            if created:
                self.stdout.write(self.style.SUCCESS(f'Permiso {codigo_permiso} creado exitosamente'))
            else:
                self.stdout.write(self.style.WARNING(f'El permiso {codigo_permiso} ya existe'))


