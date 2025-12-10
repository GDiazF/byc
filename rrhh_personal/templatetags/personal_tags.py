"""
Template tags personalizados para formularios de personal.

Proporciona filtros útiles para trabajar con formularios en los templates.
"""
from django import template

register = template.Library()


@register.filter
def get_field_label(form, field_name):
    """
    Retorna la etiqueta (label) de un campo de formulario.
    
    Si el campo no existe o el formulario no tiene el atributo fields,
    retorna una versión formateada del nombre del campo.
    
    Args:
        form: Instancia del formulario Django
        field_name: Nombre del campo del cual obtener la etiqueta
        
    Returns:
        str: Etiqueta del campo o nombre formateado si no se encuentra
        
    Example:
        {{ form|get_field_label:"nombre" }}  # Retorna "Nombre"
    """
    try:
        return form.fields[field_name].label
    except (KeyError, AttributeError):
        # Si el campo no existe, formatear el nombre del campo
        return field_name.replace('_', ' ').title() 