"""
Comando de diagnóstico para verificar permisos de navegación
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from gen_permissions.models import UserProfile, Rol, PermisoVista


class Command(BaseCommand):
    help = 'Diagnostica problemas con permisos de navegación'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("DIAGNÓSTICO DE PERMISOS DE NAVEGACIÓN")
        self.stdout.write("=" * 80)

        # 1. Verificar que el permiso existe en la BD
        self.stdout.write("\n1. VERIFICANDO PERMISO EN LA BD:")
        permiso_vista = PermisoVista.objects.filter(codigo='rrhh_personal.navigate_rrhh').first()
        if permiso_vista:
            self.stdout.write(self.style.SUCCESS(f"   ✓ PermisoVista encontrado: {permiso_vista.codigo}"))
            self.stdout.write(f"     - Nombre: {permiso_vista.nombre}")
            self.stdout.write(f"     - App Label: {permiso_vista.app_label}")
            self.stdout.write(f"     - Vista Nombre: {permiso_vista.vista_nombre}")
            if permiso_vista.permission:
                self.stdout.write(self.style.SUCCESS(f"     - Permission asociado: {permiso_vista.permission.id}"))
                self.stdout.write(f"       * Codename: {permiso_vista.permission.codename}")
                self.stdout.write(f"       * ContentType: {permiso_vista.permission.content_type.app_label}.{permiso_vista.permission.content_type.model}")
            else:
                self.stdout.write(self.style.ERROR(f"     ✗ NO tiene Permission asociado!"))
        else:
            self.stdout.write(self.style.ERROR(f"   ✗ PermisoVista NO encontrado!"))

        # 2. Buscar el Permission directamente
        self.stdout.write("\n2. BUSCANDO PERMISSION DIRECTAMENTE:")
        permission = Permission.objects.filter(codename='navigate_rrhh').first()
        if permission:
            self.stdout.write(self.style.SUCCESS(f"   ✓ Permission encontrado: {permission.codename}"))
            self.stdout.write(f"     - ID: {permission.id}")
            self.stdout.write(f"     - Name: {permission.name}")
            self.stdout.write(f"     - ContentType: {permission.content_type.app_label}.{permission.content_type.model}")
            
            # Verificar formato completo
            permiso_completo = f"{permission.content_type.app_label}.{permission.codename}"
            self.stdout.write(f"     - Formato completo: {permiso_completo}")
        else:
            self.stdout.write(self.style.ERROR(f"   ✗ Permission NO encontrado!"))

        # 3. Verificar usuarios y sus roles
        self.stdout.write("\n3. VERIFICANDO USUARIOS Y ROLES:")
        usuarios = User.objects.all()[:5]  # Primeros 5 usuarios
        for usuario in usuarios:
            self.stdout.write(f"\n   Usuario: {usuario.username}")
            try:
                profile = usuario.profile
                if profile.rol:
                    self.stdout.write(f"     - Rol: {profile.rol.nombre}")
                    
                    # Verificar permisos del rol
                    permisos_rol = profile.rol.permisos.all()
                    permiso_navigate = permisos_rol.filter(codename='navigate_rrhh').first()
                    if permiso_navigate:
                        self.stdout.write(self.style.SUCCESS(f"     ✓ El rol TIENE el permiso 'navigate_rrhh'"))
                        self.stdout.write(f"       * Permission ID: {permiso_navigate.id}")
                        self.stdout.write(f"       * ContentType: {permiso_navigate.content_type.app_label}.{permiso_navigate.content_type.model}")
                    else:
                        self.stdout.write(self.style.WARNING(f"     ✗ El rol NO tiene el permiso 'navigate_rrhh'"))
                    
                    # Verificar permisos del usuario
                    permisos_usuario = usuario.user_permissions.all()
                    permiso_usuario_navigate = permisos_usuario.filter(codename='navigate_rrhh').first()
                    if permiso_usuario_navigate:
                        self.stdout.write(self.style.SUCCESS(f"     ✓ El usuario TIENE el permiso asignado directamente"))
                    else:
                        self.stdout.write(self.style.WARNING(f"     ✗ El usuario NO tiene el permiso asignado directamente"))
                    
                    # Verificar con has_perm
                    tiene_permiso = usuario.has_perm('rrhh_personal.navigate_rrhh')
                    if tiene_permiso:
                        self.stdout.write(self.style.SUCCESS(f"     ✓ has_perm('rrhh_personal.navigate_rrhh'): {tiene_permiso}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"     ✗ has_perm('rrhh_personal.navigate_rrhh'): {tiene_permiso}"))
                    
                    # Si no tiene permiso pero el rol sí, forzar actualización
                    if permiso_navigate and not permiso_usuario_navigate:
                        self.stdout.write(self.style.WARNING(f"     ⚠ PROBLEMA: El rol tiene el permiso pero el usuario no"))
                        self.stdout.write(f"     Forzando actualización...")
                        profile.asignar_permisos_del_rol()
                        usuario.refresh_from_db()
                        tiene_permiso_despues = usuario.has_perm('rrhh_personal.navigate_rrhh')
                        if tiene_permiso_despues:
                            self.stdout.write(self.style.SUCCESS(f"     ✓ has_perm después de actualizar: {tiene_permiso_despues}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"     ✗ has_perm después de actualizar: {tiene_permiso_despues}"))
                else:
                    self.stdout.write(f"     - Sin rol asignado")
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"     ✗ Sin perfil"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("FIN DEL DIAGNÓSTICO")
        self.stdout.write("=" * 80)

