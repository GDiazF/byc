"""
Comando de gestión para crear permisos de navegación.

Este comando crea permisos personalizados para controlar el acceso a las secciones
del navbar. Si un usuario no tiene el permiso de navegación, el elemento del navbar
aparecerá desactivado u oculto.

Uso:
    python manage.py crear_permisos_navegacion
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from gen_permissions.models import PermisoVista


class Command(BaseCommand):
    help = 'Crea permisos de navegación para las secciones del navbar'

    def handle(self, *args, **options):
        """
        Crea los permisos de navegación para cada sección del navbar.
        """
        # Lista de permisos de navegación a crear
        # Formato: (codigo, nombre, app_label, vista_nombre, descripcion)
        permisos_navegacion = [
            (
                'rrhh_personal.navigate_rrhh',
                'Puede navegar a Recursos Humanos',
                'rrhh_personal',
                'navigate_rrhh',
                'Permite acceder a la sección de Recursos Humanos en el navbar'
            ),
            (
                'maquinarias.navigate_maquinarias',
                'Puede navegar a Maquinarias',
                'maquinarias',
                'navigate_maquinarias',
                'Permite acceder a la sección de Maquinarias en el navbar'
            ),
            (
                'ope_calendario.navigate_planificacion',
                'Puede navegar a Planificación',
                'ope_calendario',
                'navigate_planificacion',
                'Permite acceder a la sección de Planificación en el navbar'
            ),
            (
                'gen_settings.navigate_bases',
                'Puede navegar a Bases',
                'gen_settings',
                'navigate_bases',
                'Permite acceder a la sección de Bases en el navbar'
            ),
            (
                'reportes_auditoria.navigate_reportes',
                'Puede navegar a Reportes',
                'reportes_auditoria',
                'navigate_reportes',
                'Permite acceder a la sección de Reportes en el navbar'
            ),
            (
                'dashboards.navigate_dashboards',
                'Puede navegar a Dashboards',
                'dashboards',
                'navigate_dashboards',
                'Permite acceder a la sección de Dashboards en el navbar'
            ),
        ]
        
        # Permisos específicos para cada dashboard individual
        permisos_dashboards = [
            (
                'dashboards.view_dashboard_rrhh',
                'Puede ver Dashboard de RRHH',
                'dashboards',
                'view_dashboard_rrhh',
                'Permite ver el tab de Dashboard de Recursos Humanos'
            ),
            (
                'dashboards.view_dashboard_operaciones',
                'Puede ver Dashboard de Operaciones',
                'dashboards',
                'view_dashboard_operaciones',
                'Permite ver el tab de Dashboard de Operaciones'
            ),
            (
                'dashboards.view_dashboard_maquinarias',
                'Puede ver Dashboard de Maquinarias',
                'dashboards',
                'view_dashboard_maquinarias',
                'Permite ver el tab de Dashboard de Maquinarias'
            ),
            (
                'dashboards.view_dashboard_gerencia',
                'Puede ver Dashboard de Gerencia',
                'dashboards',
                'view_dashboard_gerencia',
                'Permite ver el tab de Dashboard de Gerencia'
            ),
        ]
        
        # Combinar ambas listas
        todos_los_permisos = permisos_navegacion + permisos_dashboards
        
        creados = 0
        existentes = 0
        
        for codigo, nombre, app_label, vista_nombre, descripcion in todos_los_permisos:
            # Verificar si el permiso ya existe
            permiso_vista, created = PermisoVista.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'app_label': app_label,
                    'vista_nombre': vista_nombre,
                    'activo': True
                }
            )
            
            # Si se creó nuevo o si existe pero no tiene Permission asociado, crear/actualizar Permission
            necesita_permission = created or not permiso_vista.permission
            
            if necesita_permission:
                # Crear el Permission de Django asociado
                # Para permisos de vista sin modelo, necesitamos crear un ContentType dummy
                # o usar un ContentType existente de la app
                try:
                    # Intentar obtener un ContentType de la app (cualquiera)
                    content_type = ContentType.objects.filter(app_label=app_label).first()
                    
                    if not content_type:
                        # Si no hay ContentType, crear uno dummy usando el modelo PermisoVista
                        # Esto permite crear permisos para apps sin modelos
                        content_type, ct_created = ContentType.objects.get_or_create(
                            app_label=app_label,
                            model='permisovista'
                        )
                        
                        if ct_created:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠ Creado ContentType dummy para {app_label}'
                                )
                            )
                    
                    # Crear el Permission de Django
                    permission, perm_created = Permission.objects.get_or_create(
                        codename=vista_nombre,
                        content_type=content_type,
                        defaults={
                            'name': nombre
                        }
                    )
                    
                    # Asociar el Permission al PermisoVista
                    permiso_vista.permission = permission
                    permiso_vista.save()
                    
                    if created:
                        creados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Creado: {codigo}')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Actualizado (Permission asociado): {codigo}')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error al crear Permission para {codigo}: {str(e)}')
                    )
            else:
                existentes += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Ya existe: {codigo}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado: {creados} creados, {existentes} ya existían'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '\n💡 Ahora puedes asignar estos permisos a los roles desde el admin de Django.'
            )
        )

