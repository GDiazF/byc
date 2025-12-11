# ============================================================================
# WIDGETS PERSONALIZADOS PARA EL ADMIN DE PERMISOS
# ============================================================================
# Este modulo proporciona widgets personalizados que muestran etiquetas visuales
# para diferenciar permisos de tablas maestras de permisos de tablas principales.
# ============================================================================

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import Widget
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .utils import es_permiso_tabla_maestra


class PermisosFilteredSelectMultiple(FilteredSelectMultiple):
    """
    Widget personalizado que extiende FilteredSelectMultiple para mostrar etiquetas visuales.
    
    Muestra "(Maestra)" junto a los permisos que pertenecen a tablas maestras,
    facilitando la identificación visual al asignar permisos a roles en el admin de Django.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el widget y carga los permisos en memoria para formateo rápido.
        
        Args:
            *args: Argumentos posicionales del widget padre.
            **kwargs: Argumentos de palabra clave del widget padre.
        """
        super().__init__(*args, **kwargs)
        # Cache de permisos para evitar multiples consultas
        self._permisos_cache = {}
    
    def render_option(self, selected_choices, option_value, option_label):
        """
        Renderiza una opción del select con etiqueta especial si es tabla maestra.
        
        Este método se llama para cada opción en el select. Agrega la etiqueta
        "(Maestra)" a los permisos de tablas maestras para facilitar la identificación visual.
        
        Args:
            selected_choices: Lista de valores seleccionados.
            option_value: Valor de la opción.
            option_label: Etiqueta de la opción.
            
        Returns:
            str: HTML de la opción renderizada.
        """
        # Obtener el permiso para verificar si es tabla maestra
        from django.contrib.auth.models import Permission
        
        # Usar cache para evitar multiples consultas
        if option_value not in self._permisos_cache:
            try:
                permission = Permission.objects.select_related('content_type').get(pk=option_value)
                self._permisos_cache[option_value] = permission
            except Permission.DoesNotExist:
                self._permisos_cache[option_value] = None
        
        permission = self._permisos_cache.get(option_value)
        
        if permission and es_permiso_tabla_maestra(permission):
            # Agregar etiqueta visual "(Maestra)" al texto de la opcion
            option_label = f"{option_label} (Maestra)"
        
        # Llamar al metodo padre para el renderizado normal
        # El padre renderiza el <option> con el texto formateado
        return super().render_option(selected_choices, option_value, option_label)
    
    def format_value(self, value):
        """
        Formatea el valor antes de renderizarlo.
        
        Args:
            value: Valor a formatear.
            
        Returns:
            str: Valor formateado.
        """
        return super().format_value(value)
    
    def format_label(self, option):
        """
        Formatea el label de una opción agregando "(Maestra)" si corresponde.
        
        Args:
            option: Diccionario con información de la opción (debe tener 'label' y 'value').
            
        Returns:
            str: Label formateado con etiqueta "(Maestra)" si es tabla maestra.
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
        # Media adicional para agregar estilos CSS y JavaScript si es necesario.
        css = {
            'all': ('gen_permissions/css/admin_permisos.css',)
        }
        js = ('gen_permissions/js/admin_permisos.js',)


class NotificacionesCheckboxWidget(Widget):
    """
    Widget personalizado que muestra checkboxes de notificaciones agrupadas por categoría.
    
    Muestra todas las notificaciones existentes como checkboxes organizadas por categoría
    (RRHH, MAQUINARIAS, PLANIFICACION, GENERAL) para facilitar la selección en el admin.
    """
    
    template_name = 'gen_permissions/widgets/notificaciones_checkboxes.html'
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.choices = None
    
    def get_context(self, name, value, attrs):
        """
        Obtiene el contexto para renderizar el widget.
        
        Agrupa las notificaciones por categoría y prepara los valores seleccionados
        para mostrarlos en el template.
        
        Args:
            name: Nombre del campo.
            value: Valor actual del campo (puede ser lista o None).
            attrs: Atributos HTML del widget.
            
        Returns:
            dict: Contexto con notificaciones agrupadas y valores seleccionados.
        """
        context = super().get_context(name, value, attrs)
        
        # Obtener todas las notificaciones activas agrupadas por categoria
        try:
            from notificaciones.models import TipoNotificacion
            
            # Obtener todas las notificaciones activas ordenadas por categoria
            notificaciones = TipoNotificacion.objects.filter(activo=True).order_by('categoria', 'nombre')
            
            # Agrupar por categoria
            notificaciones_por_categoria = {}
            for notif in notificaciones:
                categoria = notif.get_categoria_display()
                if categoria not in notificaciones_por_categoria:
                    notificaciones_por_categoria[categoria] = []
                notificaciones_por_categoria[categoria].append({
                    'id': notif.id,
                    'codigo': notif.codigo,
                    'nombre': notif.nombre,
                    'descripcion': notif.descripcion,
                    'prioridad': notif.get_prioridad_display(),
                })
            
            context['notificaciones_por_categoria'] = notificaciones_por_categoria
        except ImportError:
            context['notificaciones_por_categoria'] = {}
        
        # Convertir value a lista si es necesario
        if value is None:
            value = []
        elif not isinstance(value, (list, tuple)):
            value = [value] if value else []
        
        # Asegurar que todos los valores sean enteros
        selected_values = []
        for v in value:
            if v:
                try:
                    selected_values.append(int(v))
                except (ValueError, TypeError):
                    pass
        
        context['selected_values'] = selected_values
        context['widget']['name'] = name
        
        return context
    
    def value_from_datadict(self, data, files, name):
        """
        Obtiene los valores seleccionados del formulario.
        
        Los checkboxes con el mismo name envían múltiples valores. Este método
        los recopila y los convierte a una lista de enteros.
        
        Args:
            data: Diccionario con los datos del formulario.
            files: Diccionario con archivos subidos (no usado).
            name: Nombre del campo.
            
        Returns:
            list: Lista de IDs de notificaciones seleccionadas.
        """
        # Obtener todos los valores con el mismo nombre (multiples checkboxes)
        values = data.getlist(name)
        
        # Convertir a enteros y filtrar valores vacios
        result = []
        for v in values:
            if v:
                try:
                    result.append(int(v))
                except (ValueError, TypeError):
                    pass
        
        return result if result else []
    
    class Media:
        css = {
            'all': ('gen_permissions/css/notificaciones_checkboxes.css',)
        }
        js = ('gen_permissions/js/notificaciones_checkboxes.js',)


