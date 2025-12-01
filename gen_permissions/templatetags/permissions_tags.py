"""
Template tags para verificar permisos en templates de Django.

Este módulo proporciona template tags que permiten verificar permisos
directamente en los templates HTML.

Ejemplo de uso en template:
    {% load permissions_tags %}
    
    {% if user|has_perm:'rrhh_personal.view_personal' %}
        <a href="{% url 'lista_personal' %}">Ver Personal</a>
    {% endif %}
    
    {% if user|has_any_perm:'rrhh_personal.add_personal,rrhh_personal.change_personal' %}
        <button>Gestionar Personal</button>
    {% endif %}
"""

from django import template

register = template.Library()


@register.filter(name='has_perm')
def has_perm(user, permiso_codigo):
    """
    Template filter que verifica si el usuario tiene un permiso específico.
    
    Args:
        user: Usuario a verificar (objeto User de Django)
        permiso_codigo (str): Código del permiso a verificar.
                             Formato: 'app_label.codename'
                             Ejemplo: 'rrhh_personal.view_personal'
    
    Returns:
        bool: True si el usuario tiene el permiso, False en caso contrario
    
    Ejemplo en template:
        {% load permissions_tags %}
        
        {% if user|has_perm:'rrhh_personal.view_personal' %}
            <a href="{% url 'lista_personal' %}">Ver Personal</a>
        {% endif %}
        
        {% if user|has_perm:'rrhh_personal.desactivar_personal' %}
            <button onclick="desactivarPersonal()">Desactivar</button>
        {% endif %}
    """
    # Si no hay usuario o no está autenticado, no tiene permisos
    if not user or not user.is_authenticated:
        return False
    
    # Verificar si el usuario tiene el permiso
    return user.has_perm(permiso_codigo)


@register.filter(name='has_any_perm')
def has_any_perm(user, permisos_codigos):
    """
    Template filter que verifica si el usuario tiene AL MENOS UNO de los permisos especificados.
    
    Args:
        user: Usuario a verificar (objeto User de Django)
        permisos_codigos (str): Códigos de permisos separados por coma.
                               Ejemplo: 'rrhh_personal.add_personal,rrhh_personal.change_personal'
    
    Returns:
        bool: True si el usuario tiene al menos uno de los permisos, False en caso contrario
    
    Ejemplo en template:
        {% load permissions_tags %}
        
        {% if user|has_any_perm:'rrhh_personal.add_personal,rrhh_personal.change_personal' %}
            <button>Gestionar Personal</button>
        {% endif %}
    """
    # Si no hay usuario o no está autenticado, no tiene permisos
    if not user or not user.is_authenticated:
        return False
    
    # Separar los permisos por coma y verificar si tiene al menos uno
    permisos = [p.strip() for p in permisos_codigos.split(',')]
    return any(user.has_perm(perm) for perm in permisos)


@register.filter(name='has_all_perms')
def has_all_perms(user, permisos_codigos):
    """
    Template filter que verifica si el usuario tiene TODOS los permisos especificados.
    
    Args:
        user: Usuario a verificar (objeto User de Django)
        permisos_codigos (str): Códigos de permisos separados por coma.
                               Ejemplo: 'rrhh_personal.view_personal,rrhh_personal.add_personal'
    
    Returns:
        bool: True si el usuario tiene todos los permisos, False en caso contrario
    
    Ejemplo en template:
        {% load permissions_tags %}
        
        {% if user|has_all_perms:'rrhh_personal.view_personal,rrhh_personal.add_personal' %}
            <button>Crear Personal</button>
        {% endif %}
    """
    # Si no hay usuario o no está autenticado, no tiene permisos
    if not user or not user.is_authenticated:
        return False
    
    # Separar los permisos por coma y verificar si tiene todos
    permisos = [p.strip() for p in permisos_codigos.split(',')]
    return all(user.has_perm(perm) for perm in permisos)


@register.simple_tag
def user_rol(user):
    """
    Template tag que retorna el nombre del rol del usuario.
    
    Args:
        user: Usuario a verificar (objeto User de Django)
    
    Returns:
        str: Nombre del rol del usuario, o 'Sin rol asignado' si no tiene rol asignado
    
    Ejemplo en template:
        {% load permissions_tags %}
        
        <p>Rol: {% user_rol user %}</p>
    """
    # Si no hay usuario o no está autenticado, no tiene rol
    if not user or not user.is_authenticated:
        return 'Sin rol asignado'
    
    # Intentar obtener el perfil del usuario
    try:
        if hasattr(user, 'profile') and user.profile.rol:
            return user.profile.rol.nombre
    except:
        pass
    
    return 'Sin rol asignado'

