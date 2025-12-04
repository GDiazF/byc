"""
Configuración del Admin de Django para gestionar roles y permisos.

Este módulo configura la interfaz de administración de Django para:
- Roles: Crear y gestionar roles con sus permisos
- UserProfile: Asignar roles a usuarios y ver sus permisos
- PermisoVista: Gestionar permisos de vistas sin modelo
- PermisoAccion: Gestionar permisos personalizados de acciones
"""

from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.forms import ModelForm
from .models import Rol, PermisoVista, PermisoModelo, PermisoAccion, UserProfile
from .utils import es_permiso_tabla_maestra, formatear_nombre_permiso


# Inline para gestionar notificaciones por rol
class ConfiguracionNotificacionRolInline(admin.TabularInline):
    """
    Inline para gestionar qué tipos de notificaciones puede recibir un rol.
    """
    model = None  # Se asignará dinámicamente
    extra = 0
    fields = ('tipo_notificacion', 'activo')
    verbose_name = 'Tipo de Notificación'
    verbose_name_plural = 'Tipos de Notificaciones'
    
    def __init__(self, *args, **kwargs):
        # Importar aquí para evitar imports circulares
        try:
            from notificaciones.models import ConfiguracionNotificacionRol
            self.model = ConfiguracionNotificacionRol
        except ImportError:
            # Si la app notificaciones no está disponible, no hacer nada
            pass
        super().__init__(*args, **kwargs)
    
    def has_add_permission(self, request, obj=None):
        """Permitir agregar configuraciones"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Permitir cambiar configuraciones"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar configuraciones"""
        return True


# Formulario personalizado para Rol que formatea los nombres de permisos
class RolForm(ModelForm):
    """
    Formulario personalizado para Rol que usa un widget personalizado
    para mostrar etiquetas "(Maestra)" en permisos de tablas maestras.
    """
    class Meta:
        model = Rol
        fields = '__all__'
        # Usar widget personalizado para el campo permisos
        widgets = {
            'permisos': None  # Se configurará en __init__
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar widget personalizado para el campo permisos
        if 'permisos' in self.fields:
            # Importar el widget personalizado
            from .widgets import PermisosFilteredSelectMultiple
            
            # Usar el widget personalizado que agrega etiquetas "(Maestra)"
            self.fields['permisos'].widget = PermisosFilteredSelectMultiple(
                verbose_name='Permisos',
                is_stacked=False
            )
            
            # Ordenar permisos por app y codename para mejor visualización
            self.fields['permisos'].queryset = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'codename')


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Rol.
    
    Permite crear roles y asignarles permisos usando un widget mejorado
    (filter_horizontal) que facilita la selección de múltiples permisos.
    Los permisos de tablas maestras se muestran con la etiqueta "(Maestra)".
    También permite gestionar qué tipos de notificaciones puede recibir cada rol.
    """
    # Usar formulario personalizado que formatea los nombres de permisos
    form = RolForm
    
    # Campos que se muestran en la lista de roles
    list_display = ('nombre', 'descripcion', 'activo', 'permisos_count', 'usuarios_count')
    # Filtros disponibles en el panel lateral
    list_filter = ('activo',)
    # Campos por los que se puede buscar
    search_fields = ('nombre', 'descripcion')
    # Widget mejorado para seleccionar múltiples permisos (más fácil que el default)
    # Usamos filter_horizontal que Django convierte automáticamente en FilteredSelectMultiple
    # Nuestro widget personalizado PermisosFilteredSelectMultiple extiende FilteredSelectMultiple
    # y se aplica mediante el formulario personalizado RolForm
    filter_horizontal = ('permisos',)
    
    # Inline para gestionar notificaciones
    inlines = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar inline de notificaciones si la app está disponible
        try:
            from notificaciones.models import ConfiguracionNotificacionRol
            if ConfiguracionNotificacionRolInline.model:
                self.inlines = [ConfiguracionNotificacionRolInline]
        except ImportError:
            pass
    
    # Organización de campos en el formulario
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'activo'),
            'description': 'Información básica del rol'
        }),
        ('Permisos', {
            'fields': ('permisos',),
            'description': 'Selecciona los permisos que tendrán todos los usuarios con este rol. '
                         'Los permisos de tablas maestras aparecen marcados con "(Maestra)". '
                         'Puedes buscar permisos escribiendo en el campo de búsqueda.'
        }),
    )
    
    class Media:
        """
        Agregar CSS y JavaScript personalizados para mejorar la visualización.
        """
        css = {
            'all': ('gen_permissions/css/admin_permisos.css',)
        }
        js = ('gen_permissions/js/admin_permisos.js',)
    
    def permisos_count(self, obj):
        """
        Muestra la cantidad de permisos asignados al rol.
        
        Esto ayuda a ver rápidamente cuántos permisos tiene cada rol.
        """
        return obj.permisos.count()
    permisos_count.short_description = 'Cantidad de Permisos'
    permisos_count.admin_order_field = 'permisos'
    
    def usuarios_count(self, obj):
        """
        Muestra la cantidad de usuarios que tienen este rol.
        
        Esto ayuda a ver cuántos usuarios están usando cada rol.
        """
        return obj.userprofile_set.count()
    usuarios_count.short_description = 'Usuarios con este Rol'
    usuarios_count.admin_order_field = 'userprofile'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo UserProfile.
    
    Permite asignar roles a usuarios. Al asignar un rol, el usuario hereda
    automáticamente todos los permisos de ese rol.
    """
    # Campos que se muestran en la lista de perfiles
    list_display = ('user', 'rol', 'fecha_asignacion_rol', 'permisos_count')
    # Filtros disponibles en el panel lateral
    list_filter = ('rol', 'fecha_asignacion_rol')
    # Campos por los que se puede buscar
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    # Campos de solo lectura (no se pueden editar)
    readonly_fields = ('fecha_asignacion_rol', 'fecha_modificacion_rol', 'permisos_list')
    # Organización de campos en el formulario
    fieldsets = (
        ('Usuario', {
            'fields': ('user',),
            'description': 'Usuario asociado a este perfil'
        }),
        ('Rol', {
            'fields': ('rol',),
            'description': 'Al asignar un rol, el usuario heredará automáticamente todos sus permisos. '
                         'Si cambias el rol, los permisos se actualizarán automáticamente.'
        }),
        ('Información', {
            'fields': ('fecha_asignacion_rol', 'fecha_modificacion_rol', 'permisos_list'),
            'classes': ('collapse',),  # Sección colapsable
            'description': 'Información sobre la asignación del rol'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Sobrescribe save_model para asegurar que los permisos se asignen después de guardar.
        """
        super().save_model(request, obj, form, change)
        # Forzar asignación de permisos después de guardar desde el admin
        # Esto asegura que funcione incluso si hay problemas con signals
        obj.asignar_permisos_del_rol()
    
    def permisos_count(self, obj):
        """
        Muestra la cantidad de permisos que tiene el usuario según su rol.
        
        Si no tiene rol, muestra 0.
        """
        if obj.rol:
            return obj.rol.permisos.count()
        return 0
    permisos_count.short_description = 'Permisos del Rol'
    
    def permisos_list(self, obj):
        """
        Muestra una lista HTML de los permisos asignados al usuario.
        
        Solo muestra los primeros 10 permisos para no sobrecargar la vista.
        Si hay más, muestra un mensaje indicando cuántos más hay.
        Los permisos de tablas maestras se muestran con etiqueta "(Maestra)".
        """
        if obj.rol:
            permisos = obj.rol.permisos.all()[:10]  # Primeros 10 permisos
            lista = '<ul style="margin: 0; padding-left: 20px;">'
            for perm in permisos:
                # Formatear el nombre del permiso (agregar "(Maestra)" si corresponde)
                nombre_formateado = formatear_nombre_permiso(perm)
                # Formato: app_label.codename (Maestra) si es tabla maestra
                estilo = ''
                if es_permiso_tabla_maestra(perm):
                    estilo = ' style="color: #856404; font-weight: bold;"'
                lista += f'<li{estilo}>{perm.content_type.app_label}.{perm.codename} - {nombre_formateado}</li>'
            if obj.rol.permisos.count() > 10:
                lista += f'<li><em>... y {obj.rol.permisos.count() - 10} más</em></li>'
            lista += '</ul>'
            return format_html(lista)
        return 'Sin rol asignado'
    permisos_list.short_description = 'Permisos Asignados'


@admin.register(PermisoVista)
class PermisoVistaAdmin(admin.ModelAdmin):
    """Configuración del admin para permisos de vistas sin modelo"""
    list_display = ('codigo', 'nombre', 'app_label', 'vista_nombre', 'activo')
    list_filter = ('activo', 'app_label')
    search_fields = ('codigo', 'nombre', 'app_label', 'vista_nombre')
    readonly_fields = ('permission',)


@admin.register(PermisoAccion)
class PermisoAccionAdmin(admin.ModelAdmin):
    """Configuración del admin para permisos de acciones personalizadas"""
    list_display = ('codigo', 'nombre', 'modelo', 'accion', 'activo')
    list_filter = ('activo', 'modelo')
    search_fields = ('codigo', 'nombre', 'accion')
    readonly_fields = ('permission',)


@admin.register(PermisoModelo)
class PermisoModeloAdmin(admin.ModelAdmin):
    """Configuración del admin para el catálogo de permisos por modelo"""
    list_display = ('app_label', 'modelo_nombre', 'modelo')
    list_filter = ('app_label',)
    search_fields = ('app_label', 'modelo_nombre')
