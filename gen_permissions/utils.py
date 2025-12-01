"""
Utilidades para el sistema de permisos.

Este módulo proporciona funciones helper para identificar y gestionar permisos,
especialmente para diferenciar entre permisos de tablas principales y tablas maestras.
"""

# Lista de modelos que son TABLAS MAESTRAS (catálogos) por app
# Estos modelos generalmente solo deben ser modificados por administradores
TABLAS_MAESTRAS = {
    'rrhh_personal': [
        'sexo',              # Catálogo de sexos
        'estadocivil',       # Catálogo de estados civiles
        'deptoempresa',      # Catálogo de departamentos
        'cargo',             # Catálogo de cargos
        'tipoausentismo',    # Catálogo de tipos de ausentismo
        'proveedor',         # Catálogo de proveedores
        'tipoclasificacion', # Catálogo de tipos de clasificación
        'clasificacionproveedor', # Catálogo de clasificaciones de proveedores
        'tipoexamen',        # Catálogo de tipos de examen
        'resultadoexamen',   # Catálogo de resultados de examen
        'tipocertificacion', # Catálogo de tipos de certificación
        'tipolicencia',      # Catálogo de tipos de licencia
        'tipolicenciainterna', # Catálogo de tipos de licencia interna
        'tipolicenciamedica',  # Catálogo de tipos de licencia médica
    ],
    'maquinarias': [
        'tipoequipo',        # Catálogo de tipos de equipo
        'marcaequipo',       # Catálogo de marcas
        'modeloequipo',      # Catálogo de modelos
        'seccion',           # Catálogo de secciones
        'tiporeparacion',    # Catálogo de tipos de reparación
        'tipodocumentomaquinaria', # Catálogo de tipos de documentos
        'tipomantenimiento', # Catálogo de tipos de mantenimiento
        'estadoot',          # Catálogo de estados de OT
        'estadoequipo',      # Catálogo de estados de equipo
        'estadocalendarioequipo', # Catálogo de estados de calendario
        'estadofuenteequipo', # Catálogo de estados de fuente
        'estadomanualequipo', # Catálogo de estados manuales
    ],
    'gen_settings': [
        'region',            # Catálogo de regiones
        'comuna',            # Catálogo de comunas
        'empresa',           # Catálogo de empresas (aunque puede ser principal también)
        'unidadmedida',      # Catálogo de unidades de medida
    ],
    'ope_calendario': [
        'estado',            # Catálogo de estados
        'estadofuente',      # Catálogo de estados de fuente
        'turno',             # Catálogo de turnos
        'turnobloque',       # Catálogo de bloques de turno
        'estadomanual',      # Catálogo de estados manuales
    ],
}


def es_tabla_maestra(app_label, model_name):
    """
    Verifica si un modelo es una tabla maestra (catálogo).
    
    Args:
        app_label (str): Nombre de la app (ej: 'rrhh_personal')
        model_name (str): Nombre del modelo en minúsculas (ej: 'sexo')
    
    Returns:
        bool: True si es tabla maestra, False en caso contrario
    
    Ejemplo:
        >>> es_tabla_maestra('rrhh_personal', 'sexo')
        True
        >>> es_tabla_maestra('rrhh_personal', 'personal')
        False
    """
    # Convertir a minúsculas para comparación case-insensitive
    app_label = app_label.lower()
    model_name = model_name.lower()
    
    # Verificar si la app está en el diccionario
    if app_label not in TABLAS_MAESTRAS:
        return False
    
    # Verificar si el modelo está en la lista de tablas maestras de esa app
    return model_name in TABLAS_MAESTRAS[app_label]


def es_permiso_tabla_maestra(permission):
    """
    Verifica si un Permission de Django es de una tabla maestra.
    NO marca permisos de navegación o dashboards como maestras.
    
    Args:
        permission: Objeto Permission de Django
    
    Returns:
        bool: True si es permiso de tabla maestra, False en caso contrario
    
    Ejemplo:
        >>> perm = Permission.objects.get(codename='add_sexo')
        >>> es_permiso_tabla_maestra(perm)
        True
        >>> perm = Permission.objects.get(codename='navigate_rrhh')
        >>> es_permiso_tabla_maestra(perm)
        False
    """
    if not permission or not permission.content_type:
        return False
    
    # Excluir permisos de navegación y dashboards
    # Estos permisos tienen codename que empieza con "navigate_" o "view_dashboard_"
    codename = permission.codename.lower()
    if codename.startswith('navigate_') or codename.startswith('view_dashboard_'):
        return False
    
    # Extraer el nombre del modelo del codename del permiso
    # Formato: {action}_{modelo} (ej: 'add_sexo', 'change_personal')
    
    # Los permisos tienen formato: add_sexo, change_sexo, delete_sexo, view_sexo
    # Necesitamos extraer el nombre del modelo
    acciones = ['add_', 'change_', 'delete_', 'view_']
    model_name = codename
    
    for accion in acciones:
        if codename.startswith(accion):
            model_name = codename[len(accion):]  # Remover el prefijo de acción
            break
    
    # Verificar si es tabla maestra
    return es_tabla_maestra(permission.content_type.app_label, model_name)


def formatear_nombre_permiso(permission):
    """
    Formatea el nombre de un permiso agregando etiqueta si es tabla maestra.
    
    Args:
        permission: Objeto Permission de Django
    
    Returns:
        str: Nombre del permiso con etiqueta "(Maestra)" si corresponde
    
    Ejemplo:
        >>> perm = Permission.objects.get(codename='add_sexo')
        >>> formatear_nombre_permiso(perm)
        'Can add sexo (Maestra)'
        
        >>> perm = Permission.objects.get(codename='add_personal')
        >>> formatear_nombre_permiso(perm)
        'Can add personal'
    """
    nombre_base = str(permission.name) if hasattr(permission, 'name') else permission.codename
    
    # Si es tabla maestra, agregar etiqueta
    if es_permiso_tabla_maestra(permission):
        return f"{nombre_base} (Maestra)"
    
    return nombre_base


def obtener_modelos_maestros(app_label):
    """
    Retorna la lista de modelos maestros de una app específica.
    
    Args:
        app_label (str): Nombre de la app
    
    Returns:
        list: Lista de nombres de modelos maestros (en minúsculas)
    """
    app_label = app_label.lower()
    return TABLAS_MAESTRAS.get(app_label, [])


def obtener_modelos_principales(app_label):
    """
    Retorna la lista de modelos principales (NO maestros) de una app específica.
    
    Esto se calcula obteniendo todos los ContentTypes de la app y excluyendo los maestros.
    
    Args:
        app_label (str): Nombre de la app
    
    Returns:
        list: Lista de nombres de modelos principales (en minúsculas)
    """
    from django.contrib.contenttypes.models import ContentType
    
    # Obtener todos los ContentTypes de la app
    content_types = ContentType.objects.filter(app_label=app_label)
    modelos_maestros = obtener_modelos_maestros(app_label)
    
    # Filtrar los que NO son maestros
    modelos_principales = []
    for ct in content_types:
        if ct.model.lower() not in modelos_maestros:
            modelos_principales.append(ct.model.lower())
    
    return modelos_principales

