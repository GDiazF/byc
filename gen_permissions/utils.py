# ============================================================================
# UTILIDADES PARA EL SISTEMA DE PERMISOS
# ============================================================================
# Este modulo proporciona funciones helper para identificar y gestionar permisos,
# especialmente para diferenciar entre permisos de tablas principales y tablas maestras.
# ============================================================================

# Lista de modelos que son TABLAS MAESTRAS (catalogos) por app
# Estos modelos generalmente solo deben ser modificados por administradores
TABLAS_MAESTRAS = {
    'rrhh_personal': [
        'sexo',              # Catalogo de sexos
        'estadocivil',       # Catalogo de estados civiles
        'deptoempresa',      # Catalogo de departamentos
        'cargo',             # Catalogo de cargos
        'tipoausentismo',    # Catalogo de tipos de ausentismo
        'proveedor',         # Catalogo de proveedores
        'tipoclasificacion', # Catalogo de tipos de clasificacion
        'clasificacionproveedor', # Catalogo de clasificaciones de proveedores
        'tipoexamen',        # Catalogo de tipos de examen
        'resultadoexamen',   # Catalogo de resultados de examen
        'tipocertificacion', # Catalogo de tipos de certificacion
        'tipolicencia',      # Catalogo de tipos de licencia
        'tipolicenciainterna', # Catalogo de tipos de licencia interna
        'tipolicenciamedica',  # Catalogo de tipos de licencia medica
    ],
    'maquinarias': [
        'tipoequipo',        # Catalogo de tipos de equipo
        'marcaequipo',       # Catalogo de marcas
        'modeloequipo',      # Catalogo de modelos
        'seccion',           # Catalogo de secciones
        'tiporeparacion',    # Catalogo de tipos de reparacion
        'tipodocumentomaquinaria', # Catalogo de tipos de documentos
        'tipomantenimiento', # Catalogo de tipos de mantenimiento
        'estadoot',          # Catalogo de estados de OT
        'estadoequipo',      # Catalogo de estados de equipo
        'estadocalendarioequipo', # Catalogo de estados de calendario
        'estadofuenteequipo', # Catalogo de estados de fuente
        'estadomanualequipo', # Catalogo de estados manuales
    ],
    'gen_settings': [
        'region',            # Catalogo de regiones
        'comuna',            # Catalogo de comunas
        'empresa',           # Catalogo de empresas (aunque puede ser principal tambien)
        'unidadmedida',      # Catalogo de unidades de medida
    ],
    'ope_calendario': [
        'estado',            # Catalogo de estados
        'estadofuente',      # Catalogo de estados de fuente
        'turno',             # Catalogo de turnos
        'turnobloque',       # Catalogo de bloques de turno
        'estadomanual',      # Catalogo de estados manuales
    ],
}


def es_tabla_maestra(app_label, model_name):
    """
    Verifica si un modelo es una tabla maestra (catálogo).
    
    Las tablas maestras son modelos de catálogo que generalmente solo deben ser
    modificados por administradores (ej: Sexo, EstadoCivil, TipoEquipo, etc.).
    
    Args:
        app_label (str): Nombre de la app (ej: 'rrhh_personal').
        model_name (str): Nombre del modelo en minúsculas (ej: 'sexo').
        
    Returns:
        bool: True si es tabla maestra, False en caso contrario.
        
    Ejemplo:
        >>> es_tabla_maestra('rrhh_personal', 'sexo')
        True
        >>> es_tabla_maestra('rrhh_personal', 'personal')
        False
    """
    # Convertir a minusculas para comparacion case-insensitive
    app_label = app_label.lower()
    model_name = model_name.lower()
    
    # Verificar si la app esta en el diccionario
    if app_label not in TABLAS_MAESTRAS:
        return False
    
    # Verificar si el modelo esta en la lista de tablas maestras de esa app
    return model_name in TABLAS_MAESTRAS[app_label]


def es_permiso_tabla_maestra(permission):
    """
    Verifica si un Permission de Django es de una tabla maestra.
    
    NO marca permisos de navegación o dashboards como maestras, solo permisos
    de modelos que están en el catálogo TABLAS_MAESTRAS.
    
    Args:
        permission: Objeto Permission de Django.
        
    Returns:
        bool: True si es permiso de tabla maestra, False en caso contrario.
        
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
    
    # Excluir permisos de navegacion y dashboards
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
            model_name = codename[len(accion):]  # Remover el prefijo de accion
            break
    
    # Verificar si es tabla maestra
    return es_tabla_maestra(permission.content_type.app_label, model_name)


def formatear_nombre_permiso(permission):
    """
    Formatea el nombre de un permiso agregando etiqueta si es tabla maestra.
    
    Útil para mostrar visualmente en el admin qué permisos pertenecen a tablas
    maestras y cuáles a tablas principales.
    
    Args:
        permission: Objeto Permission de Django.
        
    Returns:
        str: Nombre del permiso con etiqueta "(Maestra)" si corresponde.
        
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
        app_label (str): Nombre de la app.
        
    Returns:
        list: Lista de nombres de modelos maestros (en minúsculas).
    """
    app_label = app_label.lower()
    return TABLAS_MAESTRAS.get(app_label, [])


def obtener_modelos_principales(app_label):
    """
    Retorna la lista de modelos principales (NO maestros) de una app específica.
    
    Esto se calcula obteniendo todos los ContentTypes de la app y excluyendo los maestros.
    Los modelos principales son aquellos que no están en el catálogo TABLAS_MAESTRAS.
    
    Args:
        app_label (str): Nombre de la app.
        
    Returns:
        list: Lista de nombres de modelos principales (en minúsculas).
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


