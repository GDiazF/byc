"""
Filtros de template para depuración.

Proporciona filtros útiles para debugging en los templates.
"""
from django import template

register = template.Library()


@register.filter(name='type_filter')
def type_filter(value):
    """
    Retorna el nombre del tipo de una variable.
    
    Útil para debugging en templates, permite verificar el tipo
    de una variable directamente en el template.
    
    Args:
        value: Valor del cual obtener el tipo
        
    Returns:
        str: Nombre del tipo de la variable (ej: 'str', 'int', 'dict', etc.)
        
    Example:
        {{ variable|type_filter }}  # Retorna "str", "int", "dict", etc.
    """
    return type(value).__name__ 