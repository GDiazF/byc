"""
Widgets personalizados para el admin de permisos.

Este módulo proporciona widgets personalizados que muestran etiquetas visuales
para diferenciar permisos de tablas maestras de permisos de tablas principales.
"""

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .utils import es_permiso_tabla_maestra


class PermisosFilteredSelectMultiple(FilteredSelectMultiple):
    """
    Widget personalizado que extiende FilteredSelectMultiple para mostrar
    etiquetas visuales en permisos de tablas maestras.
    
    Muestra "(Maestra)" junto a los permisos que pertenecen a tablas maestras,
    facilitando la identificación visual al asignar permisos a roles.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el widget y carga los permisos en memoria para formateo rápido.
        """
        super().__init__(*args, **kwargs)
        # Cache de permisos para evitar múltiples consultas
        self._permisos_cache = {}
    
    def render_option(self, selected_choices, option_value, option_label):
        """
        Renderiza una opción del select con etiqueta especial si es tabla maestra.
        
        Este método se llama para cada opción en el select. Agrega la etiqueta
        "(Maestra)" y estilos especiales a los permisos de tablas maestras.
        """
        # Obtener el permiso para verificar si es tabla maestra
        from django.contrib.auth.models import Permission
        
        # Usar cache para evitar múltiples consultas
        if option_value not in self._permisos_cache:
            try:
                permission = Permission.objects.select_related('content_type').get(pk=option_value)
                self._permisos_cache[option_value] = permission
            except Permission.DoesNotExist:
                self._permisos_cache[option_value] = None
        
        permission = self._permisos_cache.get(option_value)
        
        if permission and es_permiso_tabla_maestra(permission):
            # Agregar etiqueta visual "(Maestra)" al texto de la opción
            option_label = f"{option_label} (Maestra)"
        
        # Llamar al método padre para el renderizado normal
        # El padre renderiza el <option> con el texto formateado
        return super().render_option(selected_choices, option_value, option_label)
    
    def format_value(self, value):
        """
        Formatea el valor antes de renderizarlo.
        """
        return super().format_value(value)
    
    def format_label(self, option):
        """
        Formatea el label de una opción agregando "(Maestra)" si corresponde.
        """
        from django.contrib.auth.models import Permission
        
        label = option.get('label', '')
        value = option.get('value', '')
        
        if value:
            # Obtener el permiso
            if value not in self._permisos_cache:
                try:
                    permission = Permission.objects.select_related('content_type').get(pk=value)
                    self._permisos_cache[value] = permission
                except Permission.DoesNotExist:
                    self._permisos_cache[value] = None
            
            permission = self._permisos_cache.get(value)
            if permission and es_permiso_tabla_maestra(permission):
                # Agregar "(Maestra)" al label
                return f"{label} (Maestra)"
        
        return label
    
    class Media:
        """
        Media adicional para agregar estilos CSS y JavaScript si es necesario.
        """
        css = {
            'all': ('gen_permissions/css/admin_permisos.css',)
        }
        js = ('gen_permissions/js/admin_permisos.js',)

