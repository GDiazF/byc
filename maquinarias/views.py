from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib import messages
from django.conf import settings
import json
import os
import zipfile
import tempfile

# Para generar PDFs
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import (
    Equipo, TipoEquipo, MarcaEquipo, ModeloEquipo, Seccion, TipoReparacion, 
    PautaMantenimientoPreventivo, ItemPauta, TipoDocumentoMaquinaria, 
    DocumentoMaquinaria, HistorialDocumentoMaquinaria,
    TipoMantenimiento, EstadoOT, EstadoEquipo,
    EstadoCalendarioEquipo, EstadoFuenteEquipo, EstadoManualEquipo,
    OrdenTrabajo, ItemSeccionOT, HistorialObservacionesOT, HistorialOT,
    HistorialEquipo, obtener_estado_final_equipo_fecha
)
from gen_settings.models import Empresa
from rrhh_personal.models import Personal, InfoLaboral, Cargo, DeptoEmpresa
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from gen_permissions.decorators import permission_required_custom, permission_required_multiple
from datetime import datetime, date, timedelta
from calendar import monthrange


def obtener_nombre_completo_usuario(usuario):
    """
    Obtiene el nombre completo del usuario, priorizando first_name + last_name.
    Si no tiene nombre completo, retorna el username.
    
    Esta función se usa para mostrar nombres legibles en historiales y registros de auditoría.
    Si el usuario no existe o no tiene datos, retorna 'Sistema' como valor por defecto.
    
    Parámetros:
        usuario: Instancia del modelo User de Django o None
    
    Retorna:
        str: Nombre completo del usuario, username, o 'Sistema' si no hay usuario
    """
    # Paso 1: Validar que existe un usuario
    # Si no hay usuario (None), retornar 'Sistema' como valor por defecto
    if not usuario:
        return 'Sistema'
    
    # Paso 2: Construir nombre completo combinando first_name y last_name
    # Se usa strip() para eliminar espacios en blanco al inicio y final
    nombre_completo = f"{usuario.first_name or ''} {usuario.last_name or ''}".strip()
    
    # Paso 3: Si se construyó un nombre completo válido (no vacío), retornarlo
    if nombre_completo:
        return nombre_completo
    
    # Paso 4: Si no hay nombre completo, usar el username como alternativa
    # Si tampoco hay username, retornar 'Sistema' como último recurso
    return usuario.username or 'Sistema'


@login_required
@permission_required_custom('maquinarias.view_equipo')
def lista_equipos(request):
    """
    Vista principal para mostrar la tabla de equipos activos.
    
    Esta vista renderiza la página HTML que muestra la lista de equipos con filtros y paginación.
    Los datos de los equipos se cargan dinámicamente mediante AJAX desde la API api_listar_equipos.
    Esta función solo prepara los datos necesarios para los filtros del formulario.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    """
    # Paso 1: Obtener datos para poblar los filtros del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    modelos = ModeloEquipo.objects.all().order_by('modeloEquipo')  # Todos los modelos ordenados
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar la página
    context = {
        'empresas': empresas,  # Lista de empresas para el filtro de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el filtro de tipo
        'marcas': marcas,  # Lista de marcas para el filtro de marca
        'modelos': modelos,  # Lista de modelos para el filtro de modelo
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/lista_equipos.html', context)


@login_required
@permission_required_custom('maquinarias.view_equipo')
def equipos_desactivados(request):
    """
    Vista para mostrar equipos desactivados.
    
    Esta vista renderiza la página HTML que muestra la lista de equipos que han sido desactivados.
    Permite reactivar equipos que fueron desactivados previamente.
    Los datos de los equipos se cargan dinámicamente mediante AJAX desde la API api_listar_equipos.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    """
    # Paso 1: Obtener datos para poblar los filtros del formulario
    # Estos datos se envían al template para que el usuario pueda filtrar equipos desactivados
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar la página
    context = {
        'empresas': empresas,  # Lista de empresas para el filtro de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el filtro de tipo
        'marcas': marcas,  # Lista de marcas para el filtro de marca
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/equipos_desactivados.html', context)


@login_required
@permission_required_custom('maquinarias.add_equipo')
def crear_equipo(request):
    """
    Vista para mostrar el formulario de crear equipo.
    
    Esta vista renderiza el formulario HTML para crear un nuevo equipo.
    El formulario se envía mediante AJAX a la API api_guardar_equipo.
    Esta función solo prepara los datos iniciales necesarios para el formulario.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_equipo'
    """
    # Paso 1: Obtener datos para poblar los selects del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar opciones
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar el formulario
    context = {
        'empresas': empresas,  # Lista de empresas para el select de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo (inicia filtros en cascada)
        'es_edicion': False  # Flag que indica que es creación, no edición (afecta el comportamiento del formulario)
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/form_equipo.html', context)


@login_required
@permission_required_custom('maquinarias.change_equipo')
def editar_equipo(request, equipo_id):
    """
    Vista para mostrar el formulario de editar equipo existente.
    
    Esta vista renderiza el formulario HTML prellenado con los datos del equipo a editar.
    El formulario se envía mediante AJAX a la API api_guardar_equipo.
    Si el equipo no existe, redirige a la lista de equipos con un mensaje de error.
    
    Parámetros:
        equipo_id: ID del equipo a editar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.change_equipo'
    """
    try:
        # Paso 1: Obtener el equipo a editar con todas sus relaciones
        # select_related optimiza las consultas SQL trayendo las relaciones en una sola consulta
        equipo = Equipo.objects.select_related(
            'empresa_id',  # Traer datos de la empresa relacionada
            'modeloEquipo_id',  # Traer datos del modelo relacionado
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo de equipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id'  # Traer marca a través del modelo
        ).get(equipo_id=equipo_id)  # Buscar el equipo por su ID
        
        # Paso 2: Obtener datos para poblar los selects del formulario
        # Estos datos se envían al template para que el usuario pueda cambiar las selecciones
        empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
        tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
        
        # Paso 3: Preparar el contexto para el template
        # El contexto contiene todos los datos que el template necesita para renderizar el formulario
        context = {
            'empresas': empresas,  # Lista de empresas para el select de empresa
            'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo
            'equipo': equipo,  # Instancia del equipo a editar (con todos sus datos)
            'es_edicion': True  # Flag que indica que es edición, no creación (afecta el comportamiento del formulario)
        }
        
        # Paso 4: Renderizar el template HTML con el contexto
        # Django combina el template con el contexto para generar el HTML final
        return render(request, 'maquinarias/form_equipo.html', context)
    
    except Equipo.DoesNotExist:
        # CASO ERROR: El equipo no existe en la base de datos
        # Paso 5.1: Mostrar mensaje de error al usuario
        from django.contrib import messages
        messages.error(request, 'Equipo no encontrado')
        
        # Paso 5.2: Redirigir a la lista de equipos
        # Esto evita que el usuario vea una página de error
        from django.shortcuts import redirect
        return redirect('maquinarias:lista_equipos')


@login_required
@permission_required_custom('maquinarias.view_equipo', is_ajax=True)
def api_listar_equipos(request):
    """
    API para listar equipos con filtros y paginación.
    
    Esta función permite obtener una lista paginada de equipos con múltiples filtros opcionales.
    Los filtros se aplican de forma acumulativa (todos los filtros activos se combinan con AND).
    """
    try:
        # Paso 1: Obtener y limpiar parámetros de búsqueda y filtros desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        search = request.GET.get('search', '').strip()  # Texto de búsqueda general
        empresa_id = request.GET.get('empresa', '')  # ID de empresa para filtrar
        tipo_id = request.GET.get('tipo', '')  # ID de tipo de equipo para filtrar
        marca_id = request.GET.get('marca', '')  # ID de marca para filtrar
        modelo_id = request.GET.get('modelo', '')  # ID de modelo para filtrar
        estado = request.GET.get('estado', 'activos')  # Estado: 'activos', 'inactivos' o 'todos'
        
        # Paso 2: Obtener parámetros de paginación y ordenamiento
        # La paginación permite dividir los resultados en páginas para mejor rendimiento
        page = int(request.GET.get('page', 1))  # Número de página actual (por defecto 1)
        page_size = int(request.GET.get('page_size', 25))  # Cantidad de registros por página (por defecto 25)
        ordering = request.GET.get('ordering', '')  # Columna por la cual ordenar
        order_direction = request.GET.get('order_direction', 'asc')  # Dirección del ordenamiento ('asc' o 'desc')
        
        # Paso 3: Construir la consulta base con select_related para optimizar consultas
        # select_related evita consultas N+1 al traer las relaciones en una sola consulta SQL
        equipos = Equipo.objects.select_related(
            'empresa_id',  # Traer datos de la empresa relacionada
            'modeloEquipo_id',  # Traer datos del modelo relacionado
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo de equipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id'  # Traer marca a través del modelo
        ).all()  # Obtener todos los equipos inicialmente
        
        # Paso 4: Aplicar filtro de estado (activos/inactivos/todos)
        # Este filtro determina qué equipos mostrar según su estado de activación
        if estado == 'activos':
            equipos = equipos.filter(activo=True)  # Solo equipos activos
        elif estado == 'inactivos':
            equipos = equipos.filter(activo=False)  # Solo equipos inactivos
        # Si es 'todos', no se aplica filtro de estado
        
        # Paso 5: Aplicar filtros específicos si fueron proporcionados
        # Cada filtro se aplica solo si tiene un valor, permitiendo combinaciones flexibles
        if empresa_id:
            equipos = equipos.filter(empresa_id=empresa_id)  # Filtrar por empresa específica
        
        if tipo_id:
            equipos = equipos.filter(modeloEquipo_id__tipoEquipo_id=tipo_id)  # Filtrar por tipo de equipo
        
        if marca_id:
            equipos = equipos.filter(modeloEquipo_id__marcaEquipo_id=marca_id)  # Filtrar por marca
        
        if modelo_id:
            equipos = equipos.filter(modeloEquipo_id=modelo_id)  # Filtrar por modelo específico
        
        # Paso 6: Aplicar búsqueda de texto si fue proporcionada
        # La búsqueda busca en múltiples campos usando OR (cualquier coincidencia)
        if search:
            equipos = equipos.filter(
                Q(nombreEquipo__icontains=search) |  # Buscar en nombre del equipo
                Q(codigoInterno__icontains=search) |  # Buscar en código interno
                Q(patente__icontains=search) |  # Buscar en patente
                Q(modeloEquipo_id__marcaEquipo_id__marcaEquipo__icontains=search) |  # Buscar en nombre de marca
                Q(modeloEquipo_id__modeloEquipo__icontains=search)  # Buscar en nombre de modelo
            )
        
        # Paso 7: Ordenar los resultados
        # Si se especifica un ordenamiento personalizado, usarlo; si no, usar el ordenamiento por defecto
        if ordering:
            # Mapeo de nombres de columnas del frontend a campos del modelo Django
            ordenamiento_map = {
                'nombre': 'nombreEquipo',
                'tipo': 'modeloEquipo_id__tipoEquipo_id__tipoEquipo',
                'marca': 'modeloEquipo_id__marcaEquipo_id__marcaEquipo',
                'modelo': 'modeloEquipo_id__modeloEquipo',
                'empresa': 'empresa_id__nomFantasia'
            }
            
            # Obtener el campo real del modelo
            campo_ordenamiento = ordenamiento_map.get(ordering)
            
            if campo_ordenamiento:
                # Aplicar prefijo '-' para orden descendente si es necesario
                if order_direction == 'desc':
                    campo_ordenamiento = '-' + campo_ordenamiento
                # Ordenar por el campo especificado, manteniendo activos primero
                equipos = equipos.order_by('-activo', campo_ordenamiento)
            else:
                # Si el campo no existe en el mapeo, usar ordenamiento por defecto
                equipos = equipos.order_by('-activo', 'modeloEquipo_id__tipoEquipo_id__tipoEquipo', 'codigoInterno')
        else:
            # Ordenamiento por defecto: primero por estado activo (activos primero), luego por tipo y código interno
            equipos = equipos.order_by('-activo', 'modeloEquipo_id__tipoEquipo_id__tipoEquipo', 'codigoInterno')
        
        # Paso 8: Aplicar paginación a los resultados filtrados
        # Dividir los resultados en páginas según el tamaño de página solicitado
        paginator = Paginator(equipos, page_size)
        page_obj = paginator.get_page(page)  # Obtener la página solicitada
        
        # Paso 9: Serializar los datos de los equipos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python que luego se convertirán en JSON
        equipos_data = []
        for equipo in page_obj:
            modelo = equipo.modeloEquipo_id  # Obtener el modelo del equipo para acceder a sus relaciones
            equipos_data.append({
                'equipo_id': equipo.equipo_id,  # ID único del equipo
                'nombreEquipo': equipo.nombreEquipo,  # Nombre completo del equipo
                'codigoInterno': equipo.codigoInterno,  # Código interno único
                'patente': equipo.patente or '-',  # Patente o guión si no tiene
                'empresa': {
                    'id': equipo.empresa_id.id,  # ID de la empresa
                    'nombre': equipo.empresa_id.nomFantasia  # Nombre de la empresa
                },
                'tipoEquipo': {
                    'id': modelo.tipoEquipo_id.tipoEquipo_id,  # ID del tipo
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,  # Nombre del tipo
                    'sigla': modelo.tipoEquipo_id.siglaEquipo  # Sigla del tipo (ej: GT, EX)
                },
                'marcaEquipo': {
                    'id': modelo.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
                    'nombre': modelo.marcaEquipo_id.marcaEquipo  # Nombre de la marca
                },
                'modeloEquipo': {
                    'id': modelo.modeloEquipo_id,  # ID del modelo
                    'nombre': modelo.modeloEquipo  # Nombre del modelo
                },
                'horometro': equipo.horometro,  # Horas de uso del equipo
                'odometro': equipo.odometro,  # Kilómetros recorridos
                'horometroSuperEstructural': equipo.horometroSuperEstructural,  # Horas de superestructura
                'activo': equipo.activo  # Estado de activación del equipo
            })
        
        # Paso 10: Retornar respuesta JSON con los datos y metadatos de paginación
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'equipos': equipos_data,  # Lista de equipos serializados
            'pagination': {
                'current_page': page_obj.number,  # Página actual
                'total_pages': paginator.num_pages,  # Total de páginas disponibles
                'total_count': paginator.count,  # Total de registros que cumplen los filtros
                'has_previous': page_obj.has_previous(),  # Si hay página anterior
                'has_next': page_obj.has_next(),  # Si hay página siguiente
                'page_size': page_size  # Tamaño de página usado
            }
        })
    
    except Exception as e:
        # Manejo de errores: retornar mensaje de error en caso de excepción
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.add_equipo', 'maquinarias.change_equipo', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_guardar_equipo(request):
    """
    API unificada para crear o editar un equipo.
    
    Esta función maneja tanto la creación como la edición de equipos en una sola función.
    Determina automáticamente si es creación o edición basándose en la presencia de equipo_id.
    """
    try:
        # Paso 1: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        data = json.loads(request.body)
        equipo_id = data.get('equipo_id')  # Si existe, es edición; si no, es creación
        
        # Paso 2: Validar que los campos requeridos estén presentes
        # Estos campos son obligatorios para crear o editar un equipo
        required_fields = ['empresa_id', 'modeloEquipo_id', 'codigoInterno']
        for field in required_fields:
            if not data.get(field):
                # Retornar error 400 si falta algún campo requerido
                return JsonResponse({
                    'success': False,
                    'error': f'El campo {field} es requerido'
                }, status=400)
        
        # Paso 3: Determinar si es edición o creación y procesar según corresponda
        if equipo_id:
            # MODO EDICIÓN: Actualizar un equipo existente
            try:
                # Paso 3.1: Obtener el equipo existente de la base de datos
                equipo = Equipo.objects.get(equipo_id=equipo_id)
                
                # Paso 3.2: Verificar unicidad del código interno por modelo
                # El código interno debe ser único dentro del mismo modelo, pero puede repetirse en otros modelos
                # Excluimos el equipo actual para permitir que mantenga su código si no cambió
                if Equipo.objects.filter(
                    modeloEquipo_id=data['modeloEquipo_id'],
                    codigoInterno=data['codigoInterno']
                ).exclude(equipo_id=equipo_id).exists():
                    # Si ya existe otro equipo con ese código en ese modelo, retornar error
                    modelo = ModeloEquipo.objects.get(modeloEquipo_id=data['modeloEquipo_id'])
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe otro equipo del modelo {modelo.modeloEquipo} con el código interno {data["codigoInterno"]}'
                    }, status=400)
                
                # Paso 3.3: Actualizar los campos del equipo con los nuevos valores
                # Los valores se normalizan (strip y uppercase) para mantener consistencia
                equipo.empresa_id_id = data['empresa_id']  # Asignar empresa
                equipo.modeloEquipo_id_id = data['modeloEquipo_id']  # Asignar modelo
                equipo.codigoInterno = data['codigoInterno'].strip().upper()  # Normalizar código interno
                equipo.patente = data.get('patente', '').strip().upper() if data.get('patente') else None  # Normalizar patente o None
                equipo.horometro = data.get('horometro')  # Horas de uso actuales
                equipo.odometro = data.get('odometro')  # Kilómetros actuales
                equipo.horometroSuperEstructural = data.get('horometroSuperEstructural')  # Horas de superestructura
                
                # Paso 3.4: Asignar usuario actual para registro en historial
                # Esto permite que las señales Django sepan quién hizo el cambio
                equipo._current_user = request.user
                equipo.save()  # Guardar cambios en la base de datos
                
                # Paso 3.5: Retornar respuesta de éxito con los datos actualizados
                return JsonResponse({
                    'success': True,
                    'message': f'Equipo {equipo.nombreEquipo} actualizado exitosamente',
                    'equipo_id': equipo.equipo_id
                })
            
            except Equipo.DoesNotExist:
                # Si el equipo no existe, retornar error 404
                return JsonResponse({'success': False, 'error': 'Equipo no encontrado'}, status=404)
        
        else:
            # MODO CREACIÓN: Crear un nuevo equipo
            # Paso 4.1: Verificar que no exista ya un equipo con el mismo código interno en el mismo modelo
            # Esta validación previene duplicados al crear
            if Equipo.objects.filter(
                modeloEquipo_id=data['modeloEquipo_id'],
                codigoInterno=data['codigoInterno']
            ).exists():
                # Si ya existe, retornar error con información del modelo
                modelo = ModeloEquipo.objects.get(modeloEquipo_id=data['modeloEquipo_id'])
                return JsonResponse({
                    'success': False,
                    'error': f'Ya existe un equipo del modelo {modelo.modeloEquipo} con el código interno {data["codigoInterno"]}'
                }, status=400)
            
            # Paso 4.2: Crear nueva instancia del modelo Equipo con los datos proporcionados
            # El nombreEquipo se genera automáticamente en el método save() del modelo
            equipo = Equipo(
                empresa_id_id=data['empresa_id'],  # Asignar empresa
                modeloEquipo_id_id=data['modeloEquipo_id'],  # Asignar modelo
                codigoInterno=data['codigoInterno'].strip().upper(),  # Normalizar código interno
                patente=data.get('patente', '').strip().upper() if data.get('patente') else None,  # Normalizar patente
                horometro=data.get('horometro'),  # Horas iniciales de uso
                odometro=data.get('odometro'),  # Kilómetros iniciales
                horometroSuperEstructural=data.get('horometroSuperEstructural'),  # Horas iniciales de superestructura
                activo=True  # Los equipos nuevos se crean activos por defecto
            )
            
            # Paso 4.3: Asignar usuario actual para registro en historial
            # Esto permite registrar quién creó el equipo
            equipo._current_user = request.user
            equipo.save()  # Guardar el nuevo equipo en la base de datos
            
            # Paso 4.4: Retornar respuesta de éxito con los datos del equipo creado
            return JsonResponse({
                'success': True,
                'message': f'Equipo {equipo.nombreEquipo} creado exitosamente',
                'equipo_id': equipo.equipo_id
            })
    
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('maquinarias.delete_equipo', is_ajax=True)
@require_http_methods(["POST"])
def api_eliminar_equipo(request, equipo_id):
    """
    API para eliminar un equipo permanentemente de la base de datos.
    
    Esta función elimina un equipo y todos sus registros relacionados.
    La eliminación se registra automáticamente en el historial mediante señales Django.
    
    Parámetros:
        equipo_id: ID del equipo a eliminar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.delete_equipo'
        - Método HTTP POST
    """
    try:
        # Paso 1: Obtener el equipo a eliminar desde la base de datos
        # Si el equipo no existe, se lanzará una excepción Equipo.DoesNotExist
        equipo = Equipo.objects.get(equipo_id=equipo_id)
        
        # Paso 2: Guardar el nombre del equipo antes de eliminarlo
        # Esto se usa en el mensaje de respuesta y en el historial
        nombre = equipo.nombreEquipo
        
        # Paso 3: Asignar usuario actual para registro en historial
        # Esto permite que las señales Django sepan quién eliminó el equipo
        # La señal pre_delete registrará la eliminación en HistorialEquipo
        equipo._current_user = request.user
        
        # Paso 4: Eliminar el equipo de la base de datos
        # Esto también elimina automáticamente los objetos relacionados configurados con CASCADE
        equipo.delete()
        
        # Paso 5: Retornar respuesta de éxito con mensaje informativo
        return JsonResponse({
            'success': True,
            'message': f'Equipo {nombre} eliminado exitosamente'
        })
    
    except Equipo.DoesNotExist:
        # CASO ERROR: El equipo no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({'success': False, 'error': 'Equipo no encontrado'}, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.desactivar_equipo', 'maquinarias.activar_equipo', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_toggle_activo_equipo(request, equipo_id):
    """
    API para alternar el estado activo/inactivo de un equipo.
    
    Esta función cambia el estado de activación de un equipo:
    - Si está activo, lo desactiva
    - Si está inactivo, lo activa
    
    El cambio se registra automáticamente en el historial mediante señales Django.
    
    Parámetros:
        equipo_id: ID del equipo cuyo estado se va a cambiar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.desactivar_equipo' O 'maquinarias.activar_equipo' (no requiere ambos)
        - Método HTTP POST
    """
    try:
        # Paso 1: Obtener el equipo desde la base de datos
        # Si el equipo no existe, se lanzará una excepción Equipo.DoesNotExist
        equipo = Equipo.objects.get(equipo_id=equipo_id)
        
        # Paso 2: Alternar el estado activo/inactivo
        # Si está activo (True), se convierte en inactivo (False) y viceversa
        equipo.activo = not equipo.activo
        
        # Paso 3: Asignar usuario actual para registro en historial
        # Esto permite que las señales Django sepan quién cambió el estado
        # La señal post_save registrará el cambio en HistorialEquipo
        equipo._current_user = request.user
        
        # Paso 4: Guardar el cambio en la base de datos
        # Esto dispara las señales Django que registran el cambio en el historial
        equipo.save()
        
        # Paso 5: Retornar respuesta de éxito con el nuevo estado
        return JsonResponse({
            'status': 'success',  # Indicador de éxito
            'activo': equipo.activo  # Nuevo estado del equipo (True o False)
        })
    
    except Equipo.DoesNotExist:
        # CASO ERROR: El equipo no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({'status': 'error', 'message': 'Equipo no encontrado'}, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_tipos_equipo(request):
    """
    API para obtener todos los tipos de equipo disponibles.
    
    Esta función retorna una lista de todos los tipos de equipo ordenados alfabéticamente.
    Se usa para poblar selects en formularios y filtros en cascada.
    
    Retorna:
        JSON con lista de tipos de equipo, cada uno con id, nombre y sigla
    """
    try:
        # Paso 1: Obtener todos los tipos de equipo ordenados alfabéticamente
        tipos = TipoEquipo.objects.all().order_by('tipoEquipo')
        
        # Paso 2: Serializar los datos de tipos para enviarlos como JSON
        # Convertir objetos Django a diccionarios Python
        tipos_data = [{
            'id': tipo.tipoEquipo_id,  # ID único del tipo
            'nombre': tipo.tipoEquipo,  # Nombre completo del tipo (ej: "Grúa Torre")
            'sigla': tipo.siglaEquipo  # Sigla del tipo (ej: "GT")
        } for tipo in tipos]
        
        # Paso 3: Retornar respuesta JSON con los tipos
        return JsonResponse({'success': True, 'tipos': tipos_data})
    
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_marcas_equipo(request):
    """
    API para obtener todas las marcas de equipo disponibles.
    
    Esta función retorna una lista de todas las marcas de equipo ordenadas alfabéticamente.
    Se usa para poblar selects en formularios y filtros en cascada.
    
    Retorna:
        JSON con lista de marcas de equipo, cada una con id y nombre
    """
    try:
        # Paso 1: Obtener todas las marcas de equipo ordenadas alfabéticamente
        marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
        
        # Paso 2: Serializar los datos de marcas para enviarlos como JSON
        # Convertir objetos Django a diccionarios Python
        marcas_data = [{
            'id': marca.marcaEquipo_id,  # ID único de la marca
            'nombre': marca.marcaEquipo  # Nombre de la marca (ej: "Caterpillar", "Komatsu")
        } for marca in marcas]
        
        # Paso 3: Retornar respuesta JSON con las marcas
        return JsonResponse({'success': True, 'marcas': marcas_data})
    
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_modelos_equipo(request):
    """
    API para obtener modelos de equipo filtrados opcionalmente por tipo y/o marca.
    
    Esta función retorna una lista de modelos de equipo con sus relaciones (tipo y marca).
    Los filtros son opcionales y se pueden combinar para obtener modelos específicos.
    Se usa para poblar selects en formularios con filtros en cascada.
    
    Parámetros opcionales (query string):
        tipo_id: ID del tipo de equipo para filtrar modelos
        marca_id: ID de la marca para filtrar modelos
    
    Retorna:
        JSON con lista de modelos de equipo, cada uno con id, nombre y datos de tipo y marca
    """
    try:
        # Paso 1: Obtener parámetros opcionales de filtro desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        tipo_id = request.GET.get('tipo_id')  # ID del tipo para filtrar (opcional)
        marca_id = request.GET.get('marca_id')  # ID de la marca para filtrar (opcional)
        
        # Paso 2: Obtener todos los modelos inicialmente
        modelos = ModeloEquipo.objects.all()
        
        # Paso 3: Aplicar filtro por tipo si fue proporcionado
        # Si se especifica un tipo_id, solo se retornan modelos de ese tipo
        if tipo_id:
            modelos = modelos.filter(tipoEquipo_id=tipo_id)
        
        # Paso 4: Aplicar filtro por marca si fue proporcionado
        # Si se especifica un marca_id, solo se retornan modelos de esa marca
        # Este filtro se combina con el anterior si ambos están presentes (AND lógico)
        if marca_id:
            modelos = modelos.filter(marcaEquipo_id=marca_id)
        
        # Paso 5: Optimizar consultas usando select_related para traer relaciones en una sola consulta
        # Esto evita consultas N+1 al acceder a tipoEquipo_id y marcaEquipo_id
        modelos = modelos.select_related('tipoEquipo_id', 'marcaEquipo_id').order_by('modeloEquipo')
        
        # Paso 6: Serializar los datos de modelos para enviarlos como JSON
        # Convertir objetos Django a diccionarios Python con toda la información necesaria
        modelos_data = [{
            'id': modelo.modeloEquipo_id,  # ID único del modelo
            'nombre': modelo.modeloEquipo,  # Nombre del modelo (ej: "CAT 320D", "Komatsu PC200")
            'tipo_id': modelo.tipoEquipo_id.tipoEquipo_id,  # ID del tipo de equipo
            'tipo_nombre': modelo.tipoEquipo_id.tipoEquipo,  # Nombre del tipo
            'tipo_sigla': modelo.tipoEquipo_id.siglaEquipo,  # Sigla del tipo (para generar nombres de equipos)
            'marca_id': modelo.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
            'marca_nombre': modelo.marcaEquipo_id.marcaEquipo  # Nombre de la marca
        } for modelo in modelos]
        
        return JsonResponse({'success': True, 'modelos': modelos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_custom('maquinarias.view_equipo')
def documentacion_equipo(request, equipo_id):
    """
    Vista para mostrar la página de gestión de documentación de un equipo.
    
    Esta vista renderiza el formulario HTML que permite:
    - Ver todos los documentos del equipo
    - Subir nuevos documentos
    - Eliminar documentos existentes
    - Ver el historial de documentos eliminados
    
    Los documentos se cargan dinámicamente mediante AJAX desde la API api_documentos_equipo.
    
    Parámetros:
        equipo_id: ID del equipo cuya documentación se va a gestionar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    """
    try:
        # Paso 1: Obtener el equipo con todas sus relaciones optimizadas
        # select_related evita consultas N+1 al traer las relaciones en una sola consulta SQL
        equipo = Equipo.objects.select_related(
            'empresa_id',  # Traer datos de la empresa relacionada
            'modeloEquipo_id',  # Traer datos del modelo relacionado
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo de equipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id'  # Traer marca a través del modelo
        ).get(equipo_id=equipo_id)  # Buscar el equipo por su ID
        
        # Paso 2: Obtener tipos de documentos activos para el formulario de subida
        # Solo se muestran tipos activos para evitar confusión
        tipos_documentos = TipoDocumentoMaquinaria.objects.filter(activo=True).order_by('nombre')
        
        # Paso 3: Preparar el contexto para el template
        # El contexto contiene todos los datos que el template necesita para renderizar la página
        context = {
            'equipo': equipo,  # Instancia del equipo con todos sus datos
            'tipos_documentos': tipos_documentos,  # Lista de tipos de documentos para el formulario
        }
        
        # Paso 4: Renderizar el template HTML con el contexto
        # Django combina el template con el contexto para generar el HTML final
        return render(request, 'maquinarias/documentacion.html', context)
    
    except Equipo.DoesNotExist:
        # CASO ERROR: El equipo no existe en la base de datos
        # Paso 5.1: Mostrar mensaje de error al usuario
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Equipo no encontrado')
        
        # Paso 5.2: Redirigir a la lista de equipos
        # Esto evita que el usuario vea una página de error
        return redirect('maquinarias:lista_equipos')


# ============================================================================
# APIs PARA DOCUMENTACIÓN DE MAQUINARIAS
# ============================================================================

@login_required
@permission_required_custom('maquinarias.view_equipo', is_ajax=True)
@csrf_exempt
def api_tipos_documentos_maquinaria(request):
    """
    API para listar todos los tipos de documentos de maquinaria activos.
    
    Esta función retorna una lista de tipos de documentos que están activos y disponibles
    para ser asignados a equipos. Se usa para poblar selects en formularios de subida de documentos.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    
    Retorna:
        JSON con lista de tipos de documentos, cada uno con id, nombre, descripción y si requiere fecha de vencimiento
    """
    try:
        # Paso 1: Obtener todos los tipos de documentos activos ordenados alfabéticamente
        # Solo se retornan tipos activos para evitar mostrar opciones no disponibles
        tipos = TipoDocumentoMaquinaria.objects.filter(activo=True).order_by('nombre')
        
        # Paso 2: Serializar los datos de tipos para enviarlos como JSON
        # Convertir objetos Django a diccionarios Python
        tipos_data = [{
            'id': tipo.tipoDocumento_id,  # ID único del tipo de documento
            'nombre': tipo.nombre,  # Nombre del tipo (ej: "Permiso de Circulación", "Revisión Técnica")
            'descripcion': tipo.descripcion or '',  # Descripción del tipo (vacío si no tiene)
            'requiere_fecha_vencimiento': tipo.requiere_fecha_vencimiento  # Si requiere fecha de vencimiento obligatoria
        } for tipo in tipos]
        
        # Paso 3: Retornar respuesta JSON con los tipos de documentos
        return JsonResponse({'success': True, 'tipos': tipos_data})
    
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_custom('maquinarias.view_equipo', is_ajax=True)
@csrf_exempt
def api_documentos_equipo(request, equipo_id):
    """
    API para listar todos los documentos activos de un equipo específico.
    
    Esta función retorna una lista de documentos del equipo con información detallada,
    incluyendo el estado de vencimiento calculado automáticamente.
    
    Parámetros:
        equipo_id: ID del equipo cuyos documentos se van a listar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    
    Retorna:
        JSON con lista de documentos, cada uno con información completa y estado de vencimiento
    """
    try:
        # Paso 1: Obtener el equipo desde la base de datos
        # Si no existe, retorna error 404 automáticamente
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Paso 2: Obtener todos los documentos del equipo con optimización de consultas
        # select_related evita consultas N+1 al traer el tipo de documento en una sola consulta
        documentos = DocumentoMaquinaria.objects.filter(
            equipo_id=equipo  # Filtrar documentos del equipo específico
        ).select_related('tipo_documento_id').order_by('tipo_documento_id__nombre')  # Ordenar por nombre del tipo
        
        # Paso 3: Serializar los documentos y calcular estados de vencimiento
        documentos_data = []
        for doc in documentos:
            # Paso 3.1: Calcular estado de vencimiento del documento
            estado = 'vigente'  # Estado por defecto (documento vigente)
            dias_restantes = None  # Días restantes hasta vencimiento (None si no tiene fecha)
            
            if doc.fecha_vencimiento:
                # Calcular días restantes hasta la fecha de vencimiento
                dias_restantes = (doc.fecha_vencimiento - date.today()).days
                
                if dias_restantes < 0:
                    # Si ya pasó la fecha de vencimiento, el documento está vencido
                    estado = 'vencido'
                elif dias_restantes <= 30:
                    # Si faltan 30 días o menos, el documento está por vencer
                    estado = 'por_vencer'
                # Si faltan más de 30 días, el documento está vigente (estado por defecto)
            
            # Paso 3.2: Agregar datos del documento a la lista
            documentos_data.append({
                'id': doc.documento_id,  # ID único del documento
                'tipo_documento_id': doc.tipo_documento_id.tipoDocumento_id,  # ID del tipo de documento
                'tipo_documento_nombre': doc.tipo_documento_id.nombre,  # Nombre del tipo de documento
                'archivo_url': doc.archivo.url if doc.archivo else None,  # URL para descargar el archivo
                'archivo_nombre': doc.archivo.name.split('/')[-1] if doc.archivo else None,  # Nombre del archivo (solo nombre, sin ruta)
                'fecha_vencimiento': doc.fecha_vencimiento.isoformat() if doc.fecha_vencimiento else None,  # Fecha de vencimiento en formato ISO
                'fecha_subida': doc.fecha_subida.isoformat(),  # Fecha de subida en formato ISO
                'observaciones': doc.observaciones or '',  # Observaciones del documento (vacío si no tiene)
                'estado': estado,  # Estado calculado: 'vigente', 'por_vencer' o 'vencido'
                'dias_restantes': dias_restantes  # Días restantes hasta vencimiento (None si no tiene fecha)
            })
        
        # Paso 4: Retornar respuesta JSON con los documentos serializados
        return JsonResponse({'success': True, 'documentos': documentos_data})
    
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
@permission_required_custom('maquinarias.subir_documento', is_ajax=True)
@require_http_methods(["POST"])
def api_subir_documento_maquinaria(request, equipo_id):
    """
    API para subir/actualizar un documento de maquinaria con lógica de reemplazo automático.
    
    Esta función maneja la subida de documentos PDF para equipos. Si ya existe un documento
    del mismo tipo para el equipo, lo mueve automáticamente al historial antes de crear el nuevo.
    Esto mantiene un registro completo de todos los documentos que ha tenido el equipo.
    """
    try:
        # Paso 1: Obtener el equipo al que se le subirá el documento
        # Si el equipo no existe, retorna error 404 automáticamente
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Paso 2: Extraer datos del formulario enviado
        # Los datos vienen en request.POST (campos de texto) y request.FILES (archivos)
        tipo_documento_id = request.POST.get('tipo_documento_id')  # ID del tipo de documento
        archivo = request.FILES.get('archivo')  # Archivo PDF subido
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None  # Fecha de vencimiento (opcional)
        observaciones = request.POST.get('observaciones', '').strip()  # Observaciones del documento
        
        # Paso 3: Validar que los campos requeridos estén presentes
        # tipo_documento_id y archivo son obligatorios para crear un documento
        if not tipo_documento_id or not archivo:
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos requeridos (tipo_documento_id, archivo)'
            }, status=400)
        
        # Paso 4: Validar que el archivo sea PDF
        # Solo se aceptan archivos PDF por seguridad y consistencia
        if not archivo.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'Solo se aceptan archivos PDF'
            }, status=400)
        
        # Paso 5: Obtener el tipo de documento desde la base de datos
        # Solo se permiten tipos de documento activos
        tipo_documento = get_object_or_404(TipoDocumentoMaquinaria, tipoDocumento_id=tipo_documento_id, activo=True)
        
        # Paso 6: Validar fecha de vencimiento si es requerida
        # Algunos tipos de documento requieren fecha de vencimiento obligatoria
        # "Revisión Técnica" siempre requiere fecha de vencimiento (regla de negocio especial)
        es_revision_tecnica = 'revisión técnica' in tipo_documento.nombre.lower() or 'revision tecnica' in tipo_documento.nombre.lower()
        requiere_fecha = tipo_documento.requiere_fecha_vencimiento or es_revision_tecnica
        
        if requiere_fecha and not fecha_vencimiento:
            return JsonResponse({
                'success': False,
                'error': f'El documento "{tipo_documento.nombre}" requiere una fecha de vencimiento'
            }, status=400)
        
        # Paso 7: Convertir fecha_vencimiento de string a objeto date si existe
        # El formato esperado es YYYY-MM-DD (formato ISO estándar)
        fecha_vencimiento_obj = None
        if fecha_vencimiento:
            try:
                fecha_vencimiento_obj = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Formato de fecha inválido'
                }, status=400)
        
        # Paso 8: Verificar si ya existe un documento de este tipo para este equipo
        # Si existe, se debe mover al historial antes de crear el nuevo
        documento_existente = DocumentoMaquinaria.objects.filter(
            equipo_id=equipo,
            tipo_documento_id=tipo_documento
        ).first()
        
        # Paso 9: Si existe un documento previo, moverlo al historial
        # Esto mantiene un registro completo de todos los documentos que ha tenido el equipo
        if documento_existente:
            # Paso 9.1: Mover archivo físico a carpeta de eliminados ANTES de crear el historial
            # Esto asegura que el archivo esté disponible para copiar al historial
            archivo_ruta_eliminado = None
            if documento_existente.archivo and documento_existente.archivo.name:
                from .models import mover_archivo_a_eliminados_maquinaria
                archivo_ruta_eliminado = mover_archivo_a_eliminados_maquinaria(
                    documento_existente.archivo,  # Campo FileField del documento
                    equipo_id,  # ID del equipo para organizar carpetas
                    tipo_documento.nombre  # Nombre del tipo para el nombre del archivo
                )
            
            # Paso 9.2: Crear registro en el historial con los datos del documento existente
            # El historial guarda información sobre documentos reemplazados
            historial = HistorialDocumentoMaquinaria(
                equipo_id=equipo,  # Equipo al que pertenece el documento
                tipo_documento_id=tipo_documento,  # Tipo de documento
                tipo_documento_nombre=tipo_documento.nombre,  # Nombre del tipo (por si se elimina el tipo)
                fecha_vencimiento=documento_existente.fecha_vencimiento,  # Fecha de vencimiento original
                fecha_subida_original=documento_existente.fecha_subida,  # Cuándo se subió originalmente
                observaciones=documento_existente.observaciones  # Observaciones originales
            )
            
            # Paso 9.3: Si el archivo fue movido exitosamente, copiarlo también al historial
            # Esto permite acceder al archivo histórico incluso después del reemplazo
            if archivo_ruta_eliminado:
                try:
                    historial.save()  # Guardar primero para tener la instancia
                    
                    # Copiar el archivo desde la carpeta de eliminados al historial usando el storage
                    # Esto funciona tanto con S3 como con sistema de archivos local
                    from django.core.files.storage import default_storage
                    
                    if default_storage.exists(archivo_ruta_eliminado):
                        with default_storage.open(archivo_ruta_eliminado, 'rb') as source_file:
                            nombre_archivo = archivo_ruta_eliminado.split('/')[-1]  # Extraer solo el nombre del archivo
                            historial.archivo.save(nombre_archivo, source_file, save=True)  # Guardar copia en historial
                    else:
                        # Si no existe el archivo, guardar historial sin archivo pero con la ruta en observaciones
                        if historial.observaciones:
                            historial.observaciones += f"\n[Archivo eliminado no encontrado: {archivo_ruta_eliminado}]"
                        else:
                            historial.observaciones = f"[Archivo eliminado no encontrado: {archivo_ruta_eliminado}]"
                        historial.save()
                except Exception as e:
                    # Si falla la copia, crear historial sin archivo pero con la ruta en observaciones
                    # Esto permite rastrear dónde está el archivo aunque no se pueda copiar
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error al copiar archivo al historial: {str(e)}")
                    
                    if historial.observaciones:
                        historial.observaciones += f"\n[Error al copiar archivo eliminado: {archivo_ruta_eliminado} - {str(e)}]"
                    else:
                        historial.observaciones = f"[Error al copiar archivo eliminado: {archivo_ruta_eliminado} - {str(e)}]"
                    historial.save()
            else:
                # Si no había archivo o no se pudo mover, crear historial sin archivo
                historial.save()
            
            # Paso 9.4: Eliminar el documento existente de la base de datos
            # El archivo físico ya fue movido, así que esto solo elimina el registro en la BD
            documento_existente.delete()
        
        # Paso 10: Crear nuevo documento con el archivo subido
        # Este es el documento que reemplazará al anterior (si existía)
        nuevo_documento = DocumentoMaquinaria(
            equipo_id=equipo,  # Equipo al que pertenece el documento
            tipo_documento_id=tipo_documento,  # Tipo de documento
            fecha_vencimiento=fecha_vencimiento_obj,  # Fecha de vencimiento (puede ser None)
            observaciones=observaciones  # Observaciones del documento
        )
        nuevo_documento.archivo = archivo  # Asignar el archivo PDF subido
        nuevo_documento.save()  # Guardar en la base de datos (esto también guarda el archivo físicamente)
        
        # Paso 11: Retornar respuesta de éxito con información del documento creado
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': 'Documento subido correctamente',  # Mensaje para el usuario
            'documento_id': nuevo_documento.documento_id  # ID del documento creado para referencia
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@permission_required_custom('maquinarias.eliminar_documento', is_ajax=True)
@require_http_methods(["DELETE"])
def api_eliminar_documento_maquinaria(request, documento_id):
    """
    API para eliminar un documento de maquinaria (mueve el archivo a eliminados).
    
    Esta función no elimina físicamente el archivo, sino que lo mueve a una carpeta de eliminados
    y crea un registro en el historial. Esto permite recuperar documentos eliminados si es necesario.
    """
    try:
        # Paso 1: Obtener el documento a eliminar
        # Si no existe, retorna error 404 automáticamente
        documento = get_object_or_404(DocumentoMaquinaria, documento_id=documento_id)
        
        # Paso 2: Guardar información importante antes de eliminar
        # Esta información se necesita para crear el registro en el historial
        archivo_ruta_original = documento.archivo.name if documento.archivo else None  # Ruta original del archivo
        nombre_documento = documento.tipo_documento_id.nombre  # Nombre del tipo de documento
        equipo_id = documento.equipo_id.equipo_id  # ID del equipo para organizar carpetas
        
        # Paso 3: Mover archivo físico a carpeta de eliminados ANTES de crear el historial
        # Esto asegura que el archivo esté disponible para copiar al historial
        archivo_ruta_eliminado = None
        if documento.archivo and documento.archivo.name:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Eliminando documento. Archivo original: {documento.archivo.name}, Equipo: {equipo_id}, Tipo: {nombre_documento}")
            
            from .models import mover_archivo_a_eliminados_maquinaria
            archivo_ruta_eliminado = mover_archivo_a_eliminados_maquinaria(
                documento.archivo,  # Campo FileField del documento
                equipo_id,  # ID del equipo para organizar en carpetas
                nombre_documento  # Nombre del documento para el nombre del archivo
            )
            
            if archivo_ruta_eliminado:
                logger.info(f"Archivo copiado a eliminados exitosamente: {archivo_ruta_eliminado}")
            else:
                logger.warning(f"No se pudo copiar el archivo a eliminados. Archivo: {documento.archivo.name}")
        
        # Paso 4: Crear registro en el historial con los datos del documento eliminado
        # El historial mantiene un registro de todos los documentos eliminados
        historial = HistorialDocumentoMaquinaria(
            equipo_id=documento.equipo_id,  # Equipo al que pertenecía el documento
            tipo_documento_id=documento.tipo_documento_id,  # Tipo de documento
            tipo_documento_nombre=documento.tipo_documento_id.nombre,  # Nombre del tipo (por si se elimina el tipo)
            fecha_vencimiento=documento.fecha_vencimiento,  # Fecha de vencimiento original
            fecha_subida_original=documento.fecha_subida,  # Cuándo se subió originalmente
            observaciones=documento.observaciones  # Observaciones originales
        )
        
        # Paso 5: Si el archivo fue movido exitosamente, copiarlo también al historial
        # El modelo HistorialDocumentoMaquinaria requiere un archivo, así que copiamos desde la carpeta de eliminados
        if archivo_ruta_eliminado:
            try:
                from django.core.files.storage import default_storage
                
                # Paso 5.1: Guardar el historial primero para tener la instancia
                historial.save()
                
                # Paso 5.2: Copiar el archivo desde la carpeta de eliminados al historial usando el storage
                # Esto funciona tanto con S3 como con sistema de archivos local
                if default_storage.exists(archivo_ruta_eliminado):
                    # Leer el archivo desde el storage (S3 o local)
                    with default_storage.open(archivo_ruta_eliminado, 'rb') as source_file:
                        nombre_archivo = archivo_ruta_eliminado.split('/')[-1]  # Extraer solo el nombre del archivo
                        historial.archivo.save(nombre_archivo, source_file, save=True)  # Guardar copia en historial
                else:
                    # Si no existe el archivo eliminado, guardar historial sin archivo pero con la ruta en observaciones
                    if historial.observaciones:
                        historial.observaciones += f"\n[Archivo eliminado no encontrado: {archivo_ruta_eliminado}]"
                    else:
                        historial.observaciones = f"[Archivo eliminado no encontrado: {archivo_ruta_eliminado}]"
                    historial.save()
            except Exception as e:
                # Paso 5.3: Si falla la copia, crear historial sin archivo pero con la ruta en observaciones
                # Esto permite rastrear dónde está el archivo aunque no se pueda copiar
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al copiar archivo al historial: {str(e)}")
                
                if historial.observaciones:
                    historial.observaciones += f"\n[Error al copiar archivo eliminado: {archivo_ruta_eliminado} - {str(e)}]"
                else:
                    historial.observaciones = f"[Error al copiar archivo eliminado: {archivo_ruta_eliminado} - {str(e)}]"
                historial.save()
        else:
            # Paso 6: Si no había archivo o no se pudo mover, crear historial sin archivo
            historial.save()
        
        # Paso 7: Eliminar el documento de la base de datos
        # El archivo físico ya fue movido, así que esto solo elimina el registro en la BD
        documento.delete()
        
        # Paso 8: Retornar respuesta de éxito
        return JsonResponse({
            'success': True,
            'message': 'Documento eliminado y movido al historial'
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@permission_required_custom('maquinarias.ver_historial_documentos', is_ajax=True)
def api_historial_documentos_equipo(request, equipo_id):
    """
    API para listar el historial completo de documentos eliminados o reemplazados de un equipo.
    
    Esta función retorna todos los documentos que han sido eliminados o reemplazados para un equipo,
    incluyendo información sobre cuándo fueron subidos originalmente y cuándo fueron reemplazados.
    Intenta localizar los archivos tanto en el historial como en la carpeta de eliminados.
    
    Parámetros:
        equipo_id: ID del equipo cuyo historial de documentos se va a consultar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.ver_historial_documentos'
    
    Retorna:
        JSON con lista de documentos históricos, ordenados por fecha de reemplazo (más recientes primero)
    """
    try:
        # Paso 1: Obtener el equipo desde la base de datos
        # Si no existe, retorna error 404 automáticamente
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Paso 2: Obtener todos los registros del historial de documentos del equipo
        # Se ordenan por fecha de reemplazo descendente (más recientes primero)
        historial = HistorialDocumentoMaquinaria.objects.filter(
            equipo_id=equipo  # Filtrar solo documentos históricos de este equipo
        ).order_by('-fecha_reemplazo')  # Ordenar por fecha de reemplazo (más reciente primero)
        
        # Paso 3: Serializar los registros del historial y localizar archivos
        historial_data = []
        for item in historial:
            # Inicializar variables para URL y nombre del archivo
            archivo_url = None
            archivo_nombre = None
            
            # Paso 3.1: Intentar obtener URL del archivo desde el campo archivo del historial
            # Primero se intenta obtener desde el campo archivo del modelo HistorialDocumentoMaquinaria
            if item.archivo:
                try:
                    # Verificar si el archivo existe físicamente en la ubicación del historial
                    if os.path.exists(item.archivo.path):
                        archivo_url = item.archivo.url  # URL para descargar el archivo
                        archivo_nombre = item.archivo.name.split('/')[-1]  # Nombre del archivo (sin ruta)
                except Exception:
                    # Si falla al obtener la URL del archivo del historial, continuar sin archivo
                    pass
            
            # Paso 3.2: Si no se encontró el archivo en el historial, buscar en la carpeta de eliminados
            # Esto es un fallback para casos donde el archivo no se copió al historial pero sí se movió a eliminados
            if not archivo_url:
                try:
                    # Construir ruta de la carpeta de eliminados para este equipo
                    carpeta_eliminados = os.path.join(
                        settings.MEDIA_ROOT,  # Directorio base de archivos media
                        'Documentacion_Eliminada_Maquinarias',  # Carpeta de documentos eliminados
                        str(equipo_id)  # Subcarpeta por equipo
                    )
                    
                    # Verificar si existe la carpeta de eliminados para este equipo
                    if os.path.exists(carpeta_eliminados):
                        # Buscar archivo que coincida con el tipo de documento
                        # El nombre del archivo sigue el patrón: EQUIPO_ID_tipo_documento.pdf
                        nombre_buscar = f"{equipo_id}_{item.tipo_documento_nombre.lower().replace(' ', '_')}"
                        
                        # Buscar archivos en la carpeta que coincidan con el patrón
                        for archivo in os.listdir(carpeta_eliminados):
                            if archivo.startswith(nombre_buscar):
                                # Construir ruta relativa y URL del archivo encontrado
                                ruta_relativa = os.path.join('Documentacion_Eliminada_Maquinarias', str(equipo_id), archivo)
                                archivo_url = os.path.join(settings.MEDIA_URL.rstrip('/'), ruta_relativa).replace('\\', '/')
                                archivo_nombre = archivo
                                break  # Salir del loop una vez encontrado
                except Exception:
                    # Si falla la búsqueda en carpeta de eliminados, continuar sin archivo
                    pass
            
            historial_data.append({
                'id': item.historial_id,
                'tipo_documento_nombre': item.tipo_documento_nombre,
                'archivo_url': archivo_url,
                'archivo_nombre': archivo_nombre,
                'fecha_vencimiento': item.fecha_vencimiento.isoformat() if item.fecha_vencimiento else None,
                'fecha_subida_original': item.fecha_subida_original.isoformat() if item.fecha_subida_original else None,
                'fecha_reemplazo': item.fecha_reemplazo.isoformat(),
                'observaciones': item.observaciones or ''
            })
        
        return JsonResponse({'success': True, 'historial': historial_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== VISTAS PARA SECCIONES ====================

@login_required
@permission_required_custom('maquinarias.view_seccion')
def lista_secciones(request):
    """
    Vista principal para mostrar la tabla de secciones de equipos.
    
    Esta vista renderiza la página HTML que muestra la lista de secciones (partes de equipos).
    Los datos de las secciones se cargan dinámicamente mediante AJAX desde la API api_listar_secciones.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_seccion'
    """
    # Renderizar el template HTML (sin contexto adicional, los datos se cargan vía AJAX)
    return render(request, 'maquinarias/lista_secciones.html')


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_secciones(request):
    """
    API para listar secciones con paginación y búsqueda opcional.
    
    Esta función retorna una lista paginada de secciones de equipos, con capacidad de búsqueda
    por nombre o descripción. Incluye el conteo de tipos de reparación asociados a cada sección.
    
    Parámetros opcionales (query string):
        page: Número de página (por defecto 1)
        per_page: Cantidad de registros por página (por defecto 10)
        search: Término de búsqueda para filtrar por nombre o descripción
    
    Retorna:
        JSON con lista de secciones, total de registros, página actual y total de páginas
    """
    try:
        # Paso 1: Obtener parámetros de paginación y búsqueda desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        page = int(request.GET.get('page', 1))  # Número de página actual (por defecto 1)
        per_page = int(request.GET.get('per_page', 10))  # Cantidad de registros por página (por defecto 10)
        search = request.GET.get('search', '').strip()  # Término de búsqueda (sin espacios al inicio/final)
        
        # Paso 2: Construir la consulta base
        # Obtener todas las secciones inicialmente
        query = Seccion.objects.all()
        
        # Paso 3: Aplicar filtro de búsqueda si fue proporcionado
        # La búsqueda busca en nombre y descripción usando OR (cualquier coincidencia)
        if search:
            query = query.filter(
                Q(nombre__icontains=search) |  # Buscar en nombre (case-insensitive)
                Q(descripcion__icontains=search)  # Buscar en descripción (case-insensitive)
            )
        
        # Paso 4: Ordenar los resultados alfabéticamente por nombre
        query = query.order_by('nombre')
        
        # Paso 5: Contar el total de registros que cumplen los filtros
        # Esto se usa para calcular el total de páginas
        total = query.count()
        
        # Paso 6: Aplicar paginación a los resultados filtrados
        # Dividir los resultados en páginas según el tamaño de página solicitado
        paginator = Paginator(query, per_page)
        secciones_page = paginator.get_page(page)  # Obtener la página solicitada
        
        # Paso 7: Serializar los datos de las secciones para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        secciones_data = []
        for seccion in secciones_page:
            secciones_data.append({
                'seccion_id': seccion.seccion_id,  # ID único de la sección
                'nombre': seccion.nombre,  # Nombre de la sección
                'descripcion': seccion.descripcion or '',  # Descripción (vacío si no tiene)
                'total_tipos_reparacion': seccion.tipos_reparacion.count(),  # Cantidad de tipos de reparación asociados
            })
        
        # Paso 8: Retornar respuesta JSON con los datos y metadatos de paginación
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'secciones': secciones_data,  # Lista de secciones serializadas
            'total': total,  # Total de registros que cumplen los filtros
            'page': page,  # Página actual
            'per_page': per_page,  # Cantidad de registros por página
            'total_pages': paginator.num_pages,  # Total de páginas disponibles
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar secciones: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_seccion(request):
    """
    API unificada para crear o editar una sección de equipo.
    
    Esta función maneja tanto la creación como la edición de secciones en una sola función.
    Determina automáticamente si es creación o edición basándose en la presencia de seccion_id.
    
    Requisitos:
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        data = json.loads(request.body)
        seccion_id = data.get('seccion_id')  # Si existe, es edición; si no, es creación
        nombre = data.get('nombre', '').strip().upper()  # Nombre de la sección (normalizado a mayúsculas)
        descripcion = data.get('descripcion', '').strip()  # Descripción de la sección (opcional)
        
        # Paso 2: Validaciones de campos requeridos
        # El nombre es obligatorio para crear o editar una sección
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Paso 3: Verificar unicidad del nombre
        # El nombre debe ser único (no puede haber dos secciones con el mismo nombre)
        # Si es edición, excluir la sección actual de la verificación
        existing = Seccion.objects.filter(nombre=nombre).exclude(seccion_id=seccion_id).first()
        if existing:
            return JsonResponse({
                'success': False,
                'message': f'Ya existe una sección con el nombre "{nombre}"'
            }, status=400)
        
        # Paso 4: Determinar si es edición o creación y procesar según corresponda
        if seccion_id:
            # MODO EDICIÓN: Actualizar una sección existente
            # Paso 4.1: Obtener la sección existente de la base de datos
            seccion = Seccion.objects.get(seccion_id=seccion_id)
            
            # Paso 4.2: Actualizar los campos de la sección con los nuevos valores
            seccion.nombre = nombre  # Actualizar nombre
            seccion.descripcion = descripcion  # Actualizar descripción
            seccion.save()  # Guardar cambios en la base de datos
            
            message = 'Sección actualizada exitosamente'  # Mensaje de éxito para edición
        else:
            # MODO CREACIÓN: Crear una nueva sección
            # Paso 4.3: Crear nueva instancia del modelo Seccion con los datos proporcionados
            seccion = Seccion.objects.create(
                nombre=nombre,  # Nombre de la nueva sección
                descripcion=descripcion  # Descripción de la nueva sección (opcional)
            )
            message = 'Sección creada exitosamente'  # Mensaje de éxito para creación
        
        # Paso 5: Retornar respuesta de éxito con los datos de la sección guardada
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': message,  # Mensaje descriptivo (creada o actualizada)
            'seccion': {
                'seccion_id': seccion.seccion_id,  # ID único de la sección
                'nombre': seccion.nombre,  # Nombre de la sección
                'descripcion': seccion.descripcion or '',  # Descripción (vacío si no tiene)
            }
        })
        
    except Seccion.DoesNotExist:
        # CASO ERROR: La sección no existe en la base de datos (solo en modo edición)
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Sección no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar sección: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_seccion(request, seccion_id):
    """
    API para eliminar una sección de equipo permanentemente.
    
    Esta función elimina una sección de la base de datos. Si la sección tiene tipos de reparación
    asociados, estos también se eliminarán debido a la relación CASCADE configurada en el modelo.
    
    Parámetros:
        seccion_id: ID de la sección a eliminar
    
    Requisitos:
        - Método HTTP DELETE
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Obtener la sección a eliminar desde la base de datos
        # Si no existe, se lanzará una excepción Seccion.DoesNotExist
        seccion = Seccion.objects.get(seccion_id=seccion_id)
        
        # Paso 2: Verificar si la sección tiene tipos de reparación asociados
        # Si tiene tipos de reparación, no se puede eliminar para mantener la integridad de los datos
        # Esto previene eliminar secciones que están en uso por pautas de mantenimiento u órdenes de trabajo
        if seccion.tipos_reparacion.exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la sección "{seccion.nombre}" porque tiene tipos de reparación asociados'
            }, status=400)
        
        # Paso 3: Verificar si la sección está siendo utilizada en pautas de mantenimiento
        # Si está en uso en pautas, no se puede eliminar para mantener la integridad referencial
        # Esto previene eliminar secciones que están siendo referenciadas por pautas activas
        if ItemPauta.objects.filter(seccion_id=seccion).exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la sección "{seccion.nombre}" porque está siendo utilizada en pautas de mantenimiento'
            }, status=400)
        
        # Paso 4: Guardar el nombre de la sección antes de eliminarla
        # Esto se usa en el mensaje de respuesta después de la eliminación
        nombre = seccion.nombre
        
        # Paso 5: Eliminar la sección de la base de datos
        # Si la sección no tiene tipos de reparación ni está en pautas, se puede eliminar sin problemas
        seccion.delete()
        
        # Paso 6: Retornar respuesta de éxito con mensaje informativo
        return JsonResponse({
            'success': True,
            'message': f'Sección "{nombre}" eliminada exitosamente'
        })
        
    except Seccion.DoesNotExist:
        # CASO ERROR: La sección no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Sección no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar sección: {str(e)}'
        }, status=500)


# ==================== VISTAS PARA TIPOS DE REPARACIÓN ====================

@login_required
@permission_required_custom('maquinarias.view_tiporeparacion')
def lista_tipos_reparacion(request):
    """
    Vista principal para mostrar la tabla de tipos de reparación.
    
    Esta vista renderiza la página HTML que muestra la lista de tipos de reparación.
    Los datos se cargan dinámicamente mediante AJAX desde la API api_listar_tipos_reparacion.
    Se incluyen las secciones en el contexto para poblar filtros.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_tiporeparacion'
    """
    # Paso 1: Obtener todas las secciones ordenadas alfabéticamente
    # Estas secciones se usan para poblar el filtro de sección en el template
    secciones = Seccion.objects.all().order_by('nombre')
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene los datos necesarios para renderizar la página
    context = {
        'secciones': secciones,  # Lista de secciones para el filtro
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    return render(request, 'maquinarias/lista_tipos_reparacion.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_tipos_reparacion(request):
    """
    API para listar tipos de reparación con paginación, búsqueda y filtro por sección.
    
    Esta función retorna una lista paginada de tipos de reparación, con capacidad de búsqueda
    por nombre, descripción o nombre de sección, y filtro opcional por sección específica.
    
    Parámetros opcionales (query string):
        page: Número de página (por defecto 1)
        per_page: Cantidad de registros por página (por defecto 10)
        search: Término de búsqueda para filtrar por nombre, descripción o sección
        seccion_id: ID de sección para filtrar tipos de reparación de una sección específica
    
    Retorna:
        JSON con lista de tipos de reparación, total de registros, página actual y total de páginas
    """
    try:
        # Paso 1: Obtener parámetros de paginación, búsqueda y filtros desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        page = int(request.GET.get('page', 1))  # Número de página actual (por defecto 1)
        per_page = int(request.GET.get('per_page', 10))  # Cantidad de registros por página (por defecto 10)
        search = request.GET.get('search', '').strip()  # Término de búsqueda (sin espacios)
        seccion_id = request.GET.get('seccion_id', '').strip()  # ID de sección para filtrar (opcional)
        
        # Paso 2: Construir la consulta base con optimización
        # select_related evita consultas N+1 al traer la relación con sección en una sola consulta SQL
        query = TipoReparacion.objects.select_related('seccion_id')
        
        # Paso 3: Aplicar filtro por sección si fue proporcionado
        # Si se especifica una sección, solo se retornan tipos de reparación de esa sección
        if seccion_id:
            query = query.filter(seccion_id=seccion_id)
        
        # Paso 4: Aplicar filtro de búsqueda si fue proporcionado
        # La búsqueda busca en nombre, descripción y nombre de sección usando OR (cualquier coincidencia)
        if search:
            query = query.filter(
                Q(nombre__icontains=search) |  # Buscar en nombre del tipo (case-insensitive)
                Q(descripcion__icontains=search) |  # Buscar en descripción (case-insensitive)
                Q(seccion_id__nombre__icontains=search)  # Buscar en nombre de la sección (case-insensitive)
            )
        
        # Paso 5: Ordenar los resultados primero por nombre de sección, luego por nombre del tipo
        # Esto agrupa los tipos de reparación por sección para mejor organización
        query = query.order_by('seccion_id__nombre', 'nombre')
        
        # Paso 6: Contar el total de registros que cumplen los filtros
        # Esto se usa para calcular el total de páginas
        total = query.count()
        
        # Paso 7: Aplicar paginación a los resultados filtrados
        # Dividir los resultados en páginas según el tamaño de página solicitado
        paginator = Paginator(query, per_page)
        tipos_page = paginator.get_page(page)  # Obtener la página solicitada
        
        # Paso 8: Serializar los datos de los tipos de reparación para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        tipos_data = []
        for tipo in tipos_page:
            tipos_data.append({
                'tipoReparacion_id': tipo.tipoReparacion_id,  # ID único del tipo de reparación
                'nombre': tipo.nombre,  # Nombre del tipo de reparación
                'descripcion': tipo.descripcion or '',  # Descripción (vacío si no tiene)
                'seccion_id': tipo.seccion_id.seccion_id,  # ID de la sección a la que pertenece
                'seccion_nombre': tipo.seccion_id.nombre,  # Nombre de la sección
            })
        
        # Paso 9: Retornar respuesta JSON con los datos y metadatos de paginación
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'tipos_reparacion': tipos_data,  # Lista de tipos de reparación serializados
            'total': total,  # Total de registros que cumplen los filtros
            'page': page,  # Página actual
            'per_page': per_page,  # Cantidad de registros por página
            'total_pages': paginator.num_pages,  # Total de páginas disponibles
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar tipos de reparación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_tipo_reparacion(request):
    """
    API unificada para crear o editar un tipo de reparación.
    
    Esta función maneja tanto la creación como la edición de tipos de reparación en una sola función.
    Determina automáticamente si es creación o edición basándose en la presencia de tipoReparacion_id.
    Cada tipo de reparación debe pertenecer a una sección y tener un nombre único dentro de esa sección.
    
    Requisitos:
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        data = json.loads(request.body)
        tipo_id = data.get('tipoReparacion_id')  # Si existe, es edición; si no, es creación
        seccion_id = data.get('seccion_id')  # ID de la sección a la que pertenece (obligatorio)
        nombre = data.get('nombre', '').strip().upper()  # Nombre del tipo (normalizado a mayúsculas)
        descripcion = data.get('descripcion', '').strip()  # Descripción del tipo (opcional)
        
        # Paso 2: Validaciones de campos requeridos
        # La sección es obligatoria porque cada tipo de reparación debe pertenecer a una sección
        if not seccion_id:
            return JsonResponse({
                'success': False,
                'message': 'La sección es requerida'
            }, status=400)
        
        # El nombre es obligatorio para crear o editar un tipo de reparación
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Paso 3: Verificar que la sección existe en la base de datos
        # Si no existe, retornar error antes de continuar
        try:
            seccion = Seccion.objects.get(seccion_id=seccion_id)
        except Seccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'La sección seleccionada no existe'
            }, status=400)
        
        # Paso 4: Verificar unicidad del nombre dentro de la sección
        # El nombre debe ser único dentro de cada sección (puede repetirse en otras secciones)
        # Si es edición, excluir el tipo actual de la verificación
        existing = TipoReparacion.objects.filter(
            seccion_id=seccion_id,  # Misma sección
            nombre=nombre  # Mismo nombre
        ).exclude(tipoReparacion_id=tipo_id).first()  # Excluir el tipo actual si es edición
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': f'Ya existe un tipo de reparación "{nombre}" para la sección "{seccion.nombre}"'
            }, status=400)
        
        # Paso 5: Determinar si es edición o creación y procesar según corresponda
        if tipo_id:
            # MODO EDICIÓN: Actualizar un tipo de reparación existente
            # Paso 5.1: Obtener el tipo existente de la base de datos
            tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
            
            # Paso 5.2: Actualizar los campos del tipo con los nuevos valores
            tipo.seccion_id = seccion  # Actualizar sección
            tipo.nombre = nombre  # Actualizar nombre
            tipo.descripcion = descripcion  # Actualizar descripción
            tipo.save()  # Guardar cambios en la base de datos
            
            message = 'Tipo de reparación actualizado exitosamente'  # Mensaje de éxito para edición
        else:
            # MODO CREACIÓN: Crear un nuevo tipo de reparación
            # Paso 5.3: Crear nueva instancia del modelo TipoReparacion con los datos proporcionados
            tipo = TipoReparacion.objects.create(
                seccion_id=seccion,  # Asignar sección
                nombre=nombre,  # Nombre del nuevo tipo
                descripcion=descripcion  # Descripción del nuevo tipo (opcional)
            )
            message = 'Tipo de reparación creado exitosamente'  # Mensaje de éxito para creación
        
        # Paso 6: Retornar respuesta de éxito con los datos del tipo guardado
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': message,  # Mensaje descriptivo (creado o actualizado)
            'tipo_reparacion': {
                'tipoReparacion_id': tipo.tipoReparacion_id,  # ID único del tipo
                'nombre': tipo.nombre,  # Nombre del tipo
                'descripcion': tipo.descripcion or '',  # Descripción (vacío si no tiene)
                'seccion_id': tipo.seccion_id.seccion_id,  # ID de la sección
                'seccion_nombre': tipo.seccion_id.nombre,  # Nombre de la sección
            }
        })
        
    except TipoReparacion.DoesNotExist:
        # CASO ERROR: El tipo de reparación no existe en la base de datos (solo en modo edición)
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Tipo de reparación no encontrado'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar tipo de reparación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_tipo_reparacion(request, tipo_id):
    """
    API para eliminar un tipo de reparación permanentemente.
    
    Esta función elimina un tipo de reparación de la base de datos. Si el tipo está siendo utilizado
    en pautas de mantenimiento, no se puede eliminar para mantener la integridad de los datos.
    
    Parámetros:
        tipo_id: ID del tipo de reparación a eliminar
    
    Requisitos:
        - Método HTTP DELETE
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Obtener el tipo de reparación a eliminar desde la base de datos
        # Si no existe, se lanzará una excepción TipoReparacion.DoesNotExist
        tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
        
        # Paso 2: Verificar si el tipo está siendo utilizado en pautas de mantenimiento
        # Si está en uso en pautas, no se puede eliminar para mantener la integridad referencial
        # Esto previene eliminar tipos que están siendo referenciados por pautas activas
        if tipo.items_pauta.exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar el tipo de reparación "{tipo.nombre}" porque está siendo utilizado en pautas de mantenimiento'
            }, status=400)
        
        # Paso 3: Guardar el nombre del tipo antes de eliminarlo
        # Esto se usa en el mensaje de respuesta después de la eliminación
        nombre = tipo.nombre
        
        # Paso 4: Eliminar el tipo de reparación de la base de datos
        # Si el tipo no está en uso en pautas, se puede eliminar sin problemas
        tipo.delete()
        
        # Paso 5: Retornar respuesta de éxito con mensaje informativo
        return JsonResponse({
            'success': True,
            'message': f'Tipo de reparación "{nombre}" eliminado exitosamente'
        })
        
    except TipoReparacion.DoesNotExist:
        # CASO ERROR: El tipo de reparación no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Tipo de reparación no encontrado'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar tipo de reparación: {str(e)}'
        }, status=500)


# ==================== VISTAS PARA PAUTAS DE MANTENIMIENTO ====================

@login_required
@permission_required_custom('maquinarias.view_pautamantenimientopreventivo')
def lista_pautas_mantenimiento(request):
    """
    Vista principal para mostrar la tabla de pautas de mantenimiento preventivo.
    
    Esta vista renderiza la página HTML que muestra la lista de pautas de mantenimiento
    agrupadas por modelo de equipo. Los datos se cargan dinámicamente mediante AJAX
    desde la API api_listar_pautas_mantenimiento.
    Esta función solo prepara los datos necesarios para los filtros del formulario.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_pautamantenimientopreventivo'
    """
    # Paso 1: Obtener datos para poblar los filtros del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')  # Todos los modelos con relaciones optimizadas
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar la página
    context = {
        'empresas': empresas,  # Lista de empresas para el filtro de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el filtro de tipo
        'marcas': marcas,  # Lista de marcas para el filtro de marca
        'modelos': modelos,  # Lista de modelos para el filtro de modelo
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/lista_pautas_mantenimiento.html', context)


@login_required
@permission_required_custom('maquinarias.view_pautamantenimientopreventivo')
def ver_pautas_modelo(request, modelo_id):
    """
    Vista para ver todas las pautas de mantenimiento preventivo de un modelo específico.
    
    Esta vista renderiza una página que muestra todas las pautas (activas e inactivas) asociadas
    a un modelo de equipo específico. Incluye los items de cada pauta con sus secciones y tipos de reparación.
    
    Parámetros:
        modelo_id: ID del modelo de equipo cuyas pautas se van a mostrar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_pautamantenimientopreventivo'
    """
    try:
        # Paso 1: Obtener el modelo de equipo con sus relaciones optimizadas
        # select_related evita consultas N+1 al traer tipo y marca en una sola consulta SQL
        modelo = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',  # Traer datos del tipo de equipo
            'marcaEquipo_id'  # Traer datos de la marca
        ).get(modeloEquipo_id=modelo_id)  # Buscar el modelo por su ID
        
        # Paso 2: Obtener todas las pautas del modelo con sus items optimizados
        # prefetch_related optimiza las consultas para items, secciones y tipos de reparación
        pautas = PautaMantenimientoPreventivo.objects.filter(
            modeloEquipo_id=modelo  # Filtrar solo pautas de este modelo
        ).prefetch_related('items__seccion_id', 'items__tipos_reparacion').order_by('-activo', 'nombre')  # Ordenar: activas primero, luego por nombre
        
        # Paso 3: Preparar el contexto para el template
        # El contexto contiene todos los datos que el template necesita para renderizar la página
        context = {
            'modelo': modelo,  # Instancia del modelo con todos sus datos
            'pautas': pautas,  # Lista de pautas del modelo con sus items cargados
        }
        
        # Paso 4: Renderizar el template HTML con el contexto
        # Django combina el template con el contexto para generar el HTML final
        return render(request, 'maquinarias/ver_pautas_modelo.html', context)
        
    except ModeloEquipo.DoesNotExist:
        # CASO ERROR: El modelo no existe en la base de datos
        # Paso 5.1: Mostrar mensaje de error al usuario
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Modelo de equipo no encontrado')
        
        # Paso 5.2: Redirigir a la lista de pautas
        # Esto evita que el usuario vea una página de error
        return redirect('maquinarias:lista_pautas_mantenimiento')


@login_required
@permission_required_custom('maquinarias.add_pautamantenimientopreventivo')
def crear_pauta_mantenimiento(request):
    """
    Vista para mostrar el formulario de crear una nueva pauta de mantenimiento preventivo.
    
    Esta vista renderiza el formulario HTML para crear una nueva pauta de mantenimiento.
    El formulario permite seleccionar un modelo de equipo y agregar items (secciones y tipos de reparación).
    El formulario se envía mediante AJAX a la API api_guardar_pauta_mantenimiento.
    
    Parámetros opcionales (query string):
        modelo: ID del modelo para preseleccionar en el formulario
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_pautamantenimientopreventivo'
    """
    # Paso 1: Obtener datos para poblar los selects del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar opciones
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')  # Todos los modelos con relaciones optimizadas
    secciones = Seccion.objects.all().order_by('nombre')  # Todas las secciones ordenadas
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')  # Todos los tipos de reparación ordenados
    
    # Paso 2: Capturar modelo_id de la URL si existe (para pre-selección)
    # Esto permite preseleccionar un modelo cuando se crea una pauta desde la vista de un modelo específico
    modelo_id_param = request.GET.get('modelo', None)  # Obtener parámetro modelo de la URL
    modelo_preseleccionado = None  # Variable para almacenar el modelo preseleccionado
    
    if modelo_id_param:
        try:
            # Intentar obtener el modelo preseleccionado con sus relaciones
            modelo_preseleccionado = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').get(modeloEquipo_id=modelo_id_param)
        except ModeloEquipo.DoesNotExist:
            # Si el modelo no existe, continuar sin preselección
            pass
    
    # Paso 3: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar el formulario
    context = {
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo
        'marcas': marcas,  # Lista de marcas para el select de marca
        'modelos': modelos,  # Lista de modelos para el select de modelo
        'secciones': secciones,  # Lista de secciones para agregar items a la pauta
        'tipos_reparacion': tipos_reparacion,  # Lista de tipos de reparación para agregar items
        'es_edicion': False,  # Flag que indica que es creación, no edición
        'modelo_preseleccionado': modelo_preseleccionado,  # Modelo preseleccionado (si existe)
    }
    
    # Paso 4: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/form_pauta_mantenimiento.html', context)


@login_required
@permission_required_custom('maquinarias.change_pautamantenimientopreventivo')
def editar_pauta_mantenimiento(request, pauta_id):
    """
    Vista para mostrar el formulario de editar una pauta de mantenimiento existente.
    
    Esta vista renderiza el formulario HTML prellenado con los datos de la pauta a editar.
    El formulario permite modificar el modelo, nombre, descripción y items de la pauta.
    El formulario se envía mediante AJAX a la API api_guardar_pauta_mantenimiento.
    
    Parámetros:
        pauta_id: ID de la pauta a editar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.change_pautamantenimientopreventivo'
    """
    try:
        # Paso 1: Obtener la pauta a editar con su relación con el modelo optimizada
        # select_related evita consultas N+1 al traer el modelo en una sola consulta SQL
        pauta = PautaMantenimientoPreventivo.objects.select_related('modeloEquipo_id').get(pauta_id=pauta_id)
        
        # Paso 2: Obtener datos para poblar los selects del formulario
        # Estos datos se envían al template para que el usuario pueda cambiar las selecciones
        tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
        marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
        modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')  # Todos los modelos con relaciones optimizadas
        secciones = Seccion.objects.all().order_by('nombre')  # Todas las secciones ordenadas
        tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')  # Todos los tipos de reparación ordenados
        
        # Paso 3: Obtener los items actuales de la pauta con sus tipos de reparación optimizados
        # prefetch_related optimiza las consultas para tipos de reparación de cada item
        items = ItemPauta.objects.filter(pauta_id=pauta).select_related('seccion_id').prefetch_related('tipos_reparacion')
        
        # Paso 4: Preparar el contexto para el template
        # El contexto contiene todos los datos que el template necesita para renderizar el formulario
        context = {
            'pauta': pauta,  # Instancia de la pauta con todos sus datos
            'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo
            'marcas': marcas,  # Lista de marcas para el select de marca
            'modelos': modelos,  # Lista de modelos para el select de modelo
            'secciones': secciones,  # Lista de secciones para agregar items a la pauta
            'tipos_reparacion': tipos_reparacion,  # Lista de tipos de reparación para agregar items
            'items': items,  # Items actuales de la pauta con sus tipos de reparación
            'es_edicion': True,  # Flag que indica que es edición, no creación
        }
        
        # Paso 5: Renderizar el template HTML con el contexto
        # Django combina el template con el contexto para generar el HTML final
        return render(request, 'maquinarias/form_pauta_mantenimiento.html', context)
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        # CASO ERROR: La pauta no existe en la base de datos
        # Paso 6.1: Mostrar mensaje de error al usuario
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Pauta de mantenimiento no encontrada')
        
        # Paso 6.2: Redirigir a la lista de pautas
        # Esto evita que el usuario vea una página de error
        return redirect('maquinarias:lista_pautas_mantenimiento')


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_pautas_mantenimiento(request):
    """
    API para listar TODOS los modelos de equipo con información de sus pautas.
    
    Esta función retorna una lista paginada de modelos de equipo, incluyendo el conteo
    de pautas asociadas a cada modelo. Muestra TODOS los modelos, tengan o no pautas.
    Permite filtrar por tipo, marca, modelo y buscar por texto, además de ordenar por diferentes campos.
    
    Parámetros opcionales (query string):
        page: Número de página (por defecto 1)
        per_page: Cantidad de registros por página (por defecto 10)
        search: Término de búsqueda para filtrar por nombre de modelo, tipo o marca
        tipo_equipo_id: ID del tipo de equipo para filtrar modelos
        marca_id: ID de la marca para filtrar modelos
        modelo_id: ID del modelo específico para filtrar
        order_by: Campo por el cual ordenar ('tipo', 'marca', 'modelo', 'pautas')
        direction: Dirección de ordenamiento ('asc' o 'desc', por defecto 'asc')
    
    Retorna:
        JSON con lista de modelos, total de registros, página actual y total de páginas
    """
    try:
        from django.db.models import Count
        
        # Paso 1: Obtener parámetros de paginación, búsqueda, filtros y ordenamiento desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        page = int(request.GET.get('page', 1))  # Número de página actual (por defecto 1)
        per_page = int(request.GET.get('per_page', 10))  # Cantidad de registros por página (por defecto 10)
        search = request.GET.get('search', '').strip()  # Término de búsqueda (sin espacios)
        tipo_equipo_id = request.GET.get('tipo_equipo_id', '').strip()  # ID del tipo para filtrar (opcional)
        marca_id = request.GET.get('marca_id', '').strip()  # ID de la marca para filtrar (opcional)
        modelo_id = request.GET.get('modelo_id', '').strip()  # ID del modelo para filtrar (opcional)
        order_by = request.GET.get('order_by', '').strip()  # Campo por el cual ordenar (opcional)
        direction = request.GET.get('direction', 'asc').strip()  # Dirección de ordenamiento (asc o desc)
        
        # Paso 2: Construir la consulta base para TODOS los modelos (tengan o no pautas)
        # select_related evita consultas N+1 al traer tipo y marca en una sola consulta SQL
        # annotate agrega un campo calculado con el conteo de pautas asociadas a cada modelo
        modelos_query = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',  # Traer datos del tipo de equipo
            'marcaEquipo_id'  # Traer datos de la marca
        ).annotate(
            total_pautas=Count('pautas_mantenimiento')  # Contar pautas asociadas a cada modelo
        )
        
        # Paso 3: Aplicar filtros específicos si fueron proporcionados
        # Cada filtro se aplica solo si tiene un valor, permitiendo combinaciones flexibles
        if tipo_equipo_id:
            modelos_query = modelos_query.filter(tipoEquipo_id=tipo_equipo_id)  # Filtrar por tipo
        
        if marca_id:
            modelos_query = modelos_query.filter(marcaEquipo_id=marca_id)  # Filtrar por marca
        
        if modelo_id:
            modelos_query = modelos_query.filter(modeloEquipo_id=modelo_id)  # Filtrar por modelo específico
        
        # Paso 4: Aplicar filtro de búsqueda si fue proporcionado
        # La búsqueda busca en nombre de modelo, tipo y marca usando OR (cualquier coincidencia)
        if search:
            modelos_query = modelos_query.filter(
                Q(modeloEquipo__icontains=search) |  # Buscar en nombre del modelo
                Q(tipoEquipo_id__tipoEquipo__icontains=search) |  # Buscar en nombre del tipo
                Q(marcaEquipo_id__marcaEquipo__icontains=search)  # Buscar en nombre de la marca
            )
        
        # Paso 5: Configurar ordenamiento según los parámetros recibidos
        # Por defecto se ordena por nombre de modelo
        order_field = 'modeloEquipo'  # Campo por defecto
        if order_by == 'tipo':
            order_field = 'tipoEquipo_id__tipoEquipo'  # Ordenar por nombre del tipo
        elif order_by == 'marca':
            order_field = 'marcaEquipo_id__marcaEquipo'  # Ordenar por nombre de la marca
        elif order_by == 'modelo':
            order_field = 'modeloEquipo'  # Ordenar por nombre del modelo
        elif order_by == 'pautas':
            order_field = 'total_pautas'  # Ordenar por cantidad de pautas
        
        # Aplicar dirección de ordenamiento (ascendente o descendente)
        if direction == 'desc':
            order_field = '-' + order_field  # Prefijo '-' indica orden descendente
        
        modelos_query = modelos_query.order_by(order_field)  # Aplicar ordenamiento
        
        # Paso 6: Contar el total de modelos que cumplen los filtros
        # Esto se usa para calcular el total de páginas
        total = modelos_query.count()
        
        # Paso 7: Aplicar paginación a los resultados filtrados
        # Dividir los resultados en páginas según el tamaño de página solicitado
        paginator = Paginator(modelos_query, per_page)
        modelos_page = paginator.get_page(page)  # Obtener la página solicitada
        
        # Paso 8: Serializar los datos de los modelos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        modelos_data = []
        for modelo in modelos_page:
            modelos_data.append({
                'modeloEquipo': {
                    'modeloEquipo_id': modelo.modeloEquipo_id,  # ID único del modelo
                    'nombre': modelo.modeloEquipo,  # Nombre del modelo
                },
                'tipoEquipo': {
                    'tipoEquipo_id': modelo.tipoEquipo_id.tipoEquipo_id,  # ID del tipo
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,  # Nombre del tipo
                    'sigla': modelo.tipoEquipo_id.siglaEquipo,  # Sigla del tipo
                },
                'marcaEquipo': {
                    'marcaEquipo_id': modelo.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
                    'nombre': modelo.marcaEquipo_id.marcaEquipo,  # Nombre de la marca
                },
                'total_pautas': modelo.total_pautas,  # Cantidad de pautas asociadas (calculado con annotate)
            })
        
        # Paso 9: Retornar respuesta JSON con los datos y metadatos de paginación
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'modelos': modelos_data,  # Lista de modelos serializados
            'total': total,  # Total de registros que cumplen los filtros
            'page': page,  # Página actual
            'per_page': per_page,  # Cantidad de registros por página
            'total_pages': paginator.num_pages,  # Total de páginas disponibles
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar modelos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_pautas_por_modelo(request, modelo_id):
    """
    API para obtener todas las pautas de un modelo específico con detalles completos.
    
    Esta función retorna todas las pautas (activas e inactivas) asociadas a un modelo de equipo,
    incluyendo información detallada de cada pauta: items, secciones, tipos de reparación,
    fechas de creación y modificación.
    
    Parámetros:
        modelo_id: ID del modelo de equipo cuyas pautas se van a obtener
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con información del modelo y lista completa de pautas con sus items y tipos de reparación
    """
    try:
        # Paso 1: Obtener el modelo de equipo con sus relaciones optimizadas
        # select_related evita consultas N+1 al traer tipo y marca en una sola consulta SQL
        modelo = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',  # Traer datos del tipo de equipo
            'marcaEquipo_id'  # Traer datos de la marca
        ).get(modeloEquipo_id=modelo_id)  # Buscar el modelo por su ID
        
        # Paso 2: Obtener todas las pautas del modelo con sus items optimizados
        # prefetch_related optimiza las consultas para items, secciones y tipos de reparación
        pautas = PautaMantenimientoPreventivo.objects.filter(
            modeloEquipo_id=modelo  # Filtrar solo pautas de este modelo
        ).prefetch_related('items__seccion_id', 'items__tipos_reparacion').order_by('-activo', 'nombre')  # Ordenar: activas primero, luego por nombre
        
        # Paso 3: Serializar las pautas con todos sus items y tipos de reparación
        pautas_data = []
        for pauta in pautas:
            # Paso 3.1: Obtener items de la pauta con sus tipos de reparación
            items_data = []
            for item in pauta.items.all():
                # Paso 3.1.1: Serializar tipos de reparación del item
                tipos_reparacion = []
                for tipo in item.tipos_reparacion.all():
                    tipos_reparacion.append({
                        'tipoReparacion_id': tipo.tipoReparacion_id,  # ID único del tipo de reparación
                        'nombre': tipo.nombre,  # Nombre del tipo de reparación
                        'descripcion': tipo.descripcion or '',  # Descripción (vacío si no tiene)
                    })
                
                # Paso 3.1.2: Agregar datos del item con su sección y tipos de reparación
                items_data.append({
                    'seccion': {
                        'seccion_id': item.seccion_id.seccion_id,  # ID de la sección
                        'nombre': item.seccion_id.nombre,  # Nombre de la sección
                    },
                    'tipos_reparacion': tipos_reparacion  # Lista de tipos de reparación del item
                })
            
            # Paso 3.2: Agregar datos de la pauta con sus items
            pautas_data.append({
                'pauta_id': pauta.pauta_id,  # ID único de la pauta
                'nombre': pauta.nombre,  # Nombre de la pauta
                'descripcion': pauta.descripcion or '',  # Descripción (vacío si no tiene)
                'activo': pauta.activo,  # Estado de activación de la pauta
                'items': items_data,  # Lista de items con sus secciones y tipos de reparación
                'total_items': len(items_data),  # Cantidad total de items en la pauta
                'fecha_creacion': pauta.fecha_creacion.strftime('%Y-%m-%d'),  # Fecha de creación formateada
                'fecha_modificacion': pauta.fecha_modificacion.strftime('%Y-%m-%d %H:%M'),  # Fecha de modificación formateada
            })
        
        # Paso 4: Retornar respuesta JSON con información del modelo y sus pautas
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'modelo': {
                'modeloEquipo_id': modelo.modeloEquipo_id,  # ID único del modelo
                'nombre': modelo.modeloEquipo,  # Nombre del modelo
                'tipoEquipo': {
                    'tipoEquipo_id': modelo.tipoEquipo_id.tipoEquipo_id,  # ID del tipo
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,  # Nombre del tipo
                    'sigla': modelo.tipoEquipo_id.siglaEquipo,  # Sigla del tipo
                },
                'marcaEquipo': {
                    'marcaEquipo_id': modelo.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
                    'nombre': modelo.marcaEquipo_id.marcaEquipo,  # Nombre de la marca
                },
            },
            'pautas': pautas_data  # Lista completa de pautas con todos sus detalles
        })
        
    except ModeloEquipo.DoesNotExist:
        # CASO ERROR: El modelo no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Modelo de equipo no encontrado'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar pautas del modelo: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.add_pautamantenimientopreventivo', 'maquinarias.change_pautamantenimientopreventivo', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_guardar_pauta_mantenimiento(request):
    """
    API unificada para crear o editar una pauta de mantenimiento preventivo.
    
    Esta función maneja tanto la creación como la edición de pautas en una sola función.
    Determina automáticamente si es creación o edición basándose en la presencia de pauta_id.
    Usa transacciones atómicas para asegurar que todos los cambios se completen o se reviertan.
    En modo edición, elimina todos los items antiguos y crea nuevos items según los datos recibidos.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_pautamantenimientopreventivo' O 'maquinarias.change_pautamantenimientopreventivo'
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        from django.db import transaction
        
        # Paso 1: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        data = json.loads(request.body)
        pauta_id = data.get('pauta_id')  # Si existe, es edición; si no, es creación
        modelo_equipo_id = data.get('modeloEquipo_id')  # ID del modelo de equipo (obligatorio)
        nombre = data.get('nombre', '').strip().upper()  # Nombre de la pauta (normalizado a mayúsculas)
        descripcion = data.get('descripcion', '').strip()  # Descripción de la pauta (opcional)
        items_data = data.get('items', [])  # Lista de items: [{seccion_id, tipos_reparacion_ids[]}, ...]
        
        # Paso 2: Validaciones de campos requeridos
        # El modelo de equipo es obligatorio porque cada pauta debe pertenecer a un modelo específico
        if not modelo_equipo_id:
            return JsonResponse({
                'success': False,
                'message': 'El modelo de equipo es requerido'
            }, status=400)
        
        # El nombre es obligatorio para crear o editar una pauta
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Paso 3: Verificar que el modelo existe en la base de datos
        # Si no existe, retornar error antes de continuar
        try:
            modelo = ModeloEquipo.objects.get(modeloEquipo_id=modelo_equipo_id)
        except ModeloEquipo.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'El modelo de equipo seleccionado no existe'
            }, status=400)
        
        # Paso 4: Usar transacción atómica para asegurar integridad de datos
        # Si falla cualquier parte del proceso, se revierten todos los cambios
        with transaction.atomic():
            # Paso 5: Determinar si es edición o creación y procesar según corresponda
            if pauta_id:
                # MODO EDICIÓN: Actualizar una pauta existente
                # Paso 5.1: Obtener la pauta existente de la base de datos
                pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
                
                # Paso 5.2: Actualizar los campos de la pauta con los nuevos valores
                pauta.modeloEquipo_id = modelo  # Actualizar modelo
                pauta.nombre = nombre  # Actualizar nombre
                pauta.descripcion = descripcion  # Actualizar descripción
                pauta.save()  # Guardar cambios en la base de datos
                
                # Paso 5.3: Eliminar todos los items antiguos de la pauta
                # Esto permite reemplazar completamente los items con los nuevos datos
                ItemPauta.objects.filter(pauta_id=pauta).delete()
                
                message = 'Pauta de mantenimiento actualizada exitosamente'  # Mensaje de éxito para edición
            else:
                # MODO CREACIÓN: Crear una nueva pauta
                # Paso 5.4: Crear nueva instancia del modelo PautaMantenimientoPreventivo
                pauta = PautaMantenimientoPreventivo.objects.create(
                    modeloEquipo_id=modelo,  # Asignar modelo
                    nombre=nombre,  # Nombre de la nueva pauta
                    descripcion=descripcion  # Descripción de la nueva pauta (opcional)
                )
                message = 'Pauta de mantenimiento creada exitosamente'  # Mensaje de éxito para creación
            
            # Paso 6: Crear los nuevos items de la pauta
            # Cada item contiene una sección y múltiples tipos de reparación
            for item_data in items_data:
                seccion_id = item_data.get('seccion_id')  # ID de la sección del item
                tipos_ids = item_data.get('tipos_reparacion_ids', [])  # Lista de IDs de tipos de reparación
                
                # Paso 6.1: Validar que el item tiene sección y tipos de reparación
                # Si falta alguno, saltar este item y continuar con el siguiente
                if not seccion_id or not tipos_ids:
                    continue  # Saltar items incompletos
                
                try:
                    # Paso 6.2: Obtener la sección desde la base de datos
                    seccion = Seccion.objects.get(seccion_id=seccion_id)
                    
                    # Paso 6.3: Crear el ItemPauta asociado a la pauta y la sección
                    item = ItemPauta.objects.create(
                        pauta_id=pauta,  # Asignar a la pauta
                        seccion_id=seccion  # Asignar sección
                    )
                    
                    # Paso 6.4: Agregar los tipos de reparación al item
                    # Cada tipo de reparación se agrega a la relación many-to-many
                    for tipo_id in tipos_ids:
                        try:
                            tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
                            item.tipos_reparacion.add(tipo)  # Agregar tipo a la relación many-to-many
                        except TipoReparacion.DoesNotExist:
                            # Si el tipo no existe, continuar sin agregarlo (no crítico)
                            pass
                    
                except Seccion.DoesNotExist:
                    # Si la sección no existe, continuar sin crear el item (no crítico)
                    pass
        
        # Paso 7: Retornar respuesta de éxito con el ID de la pauta guardada
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': message,  # Mensaje descriptivo (creada o actualizada)
            'pauta_id': pauta.pauta_id  # ID de la pauta para referencia
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        # CASO ERROR: La pauta no existe en la base de datos (solo en modo edición)
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar pauta de mantenimiento: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.desactivar_pauta', 'maquinarias.activar_pauta', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_toggle_activo_pauta(request, pauta_id):
    """
    API para alternar el estado activo/inactivo de una pauta de mantenimiento.
    
    Esta función cambia el estado de activación de una pauta:
    - Si está activa, la desactiva
    - Si está inactiva, la activa
    
    Las pautas inactivas no se muestran en los formularios de creación de órdenes de trabajo.
    
    Parámetros:
        pauta_id: ID de la pauta cuyo estado se va a cambiar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.desactivar_pauta' O 'maquinarias.activar_pauta' (no requiere ambos)
        - Método HTTP POST
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Obtener la pauta desde la base de datos
        # Si la pauta no existe, se lanzará una excepción PautaMantenimientoPreventivo.DoesNotExist
        pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
        
        # Paso 2: Alternar el estado activo/inactivo
        # Si está activa (True), se convierte en inactiva (False) y viceversa
        pauta.activo = not pauta.activo
        
        # Paso 3: Guardar el cambio en la base de datos
        pauta.save()
        
        # Paso 4: Determinar el texto del estado para el mensaje
        # Se usa para mostrar un mensaje descriptivo al usuario
        estado = "activada" if pauta.activo else "desactivada"
        
        # Paso 5: Retornar respuesta de éxito con el nuevo estado
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': f'Pauta "{pauta.nombre}" {estado} exitosamente',  # Mensaje descriptivo
            'activo': pauta.activo  # Nuevo estado de la pauta (True o False)
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        # CASO ERROR: La pauta no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar estado: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('maquinarias.delete_pautamantenimientopreventivo', is_ajax=True)
@require_http_methods(["DELETE"])
def api_eliminar_pauta(request, pauta_id):
    """
    API para eliminar una pauta de mantenimiento permanentemente.
    
    Esta función elimina una pauta y todos sus items asociados de la base de datos.
    Los items se eliminan automáticamente debido a la relación CASCADE configurada en el modelo.
    
    Parámetros:
        pauta_id: ID de la pauta a eliminar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.delete_pautamantenimientopreventivo'
        - Método HTTP DELETE
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Obtener la pauta a eliminar desde la base de datos
        # Si no existe, se lanzará una excepción PautaMantenimientoPreventivo.DoesNotExist
        pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
        
        # Paso 2: Guardar el nombre de la pauta antes de eliminarla
        # Esto se usa en el mensaje de respuesta después de la eliminación
        nombre = pauta.nombre
        
        # Paso 3: Eliminar la pauta de la base de datos
        # Esto también elimina automáticamente todos los ItemPauta relacionados (CASCADE)
        pauta.delete()
        
        # Paso 4: Retornar respuesta de éxito con mensaje informativo
        return JsonResponse({
            'success': True,
            'message': f'Pauta "{nombre}" eliminada exitosamente'
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        # CASO ERROR: La pauta no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar pauta: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_pauta(request, pauta_id):
    """
    API para obtener el detalle completo de una pauta de mantenimiento con todos sus items.
    
    Esta función retorna información completa de una pauta específica, incluyendo:
    - Información básica de la pauta (nombre, descripción, estado)
    - Información del modelo asociado (con tipo y marca)
    - Todos los items de la pauta con sus secciones y tipos de reparación
    
    Parámetros:
        pauta_id: ID de la pauta cuyo detalle se va a obtener
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con información completa de la pauta, modelo e items
    """
    try:
        # Paso 1: Obtener la pauta con todas sus relaciones optimizadas
        # select_related evita consultas N+1 al traer modelo, tipo y marca en una sola consulta SQL
        pauta = PautaMantenimientoPreventivo.objects.select_related(
            'modeloEquipo_id',  # Traer datos del modelo
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo de equipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id'  # Traer marca a través del modelo
        ).get(pauta_id=pauta_id)  # Buscar la pauta por su ID
        
        # Paso 2: Obtener items de la pauta con sus tipos de reparación optimizados
        # prefetch_related optimiza las consultas para tipos de reparación de cada item
        items = ItemPauta.objects.filter(pauta_id=pauta).select_related('seccion_id').prefetch_related('tipos_reparacion')
        
        # Paso 3: Serializar los items con sus tipos de reparación
        items_data = []
        for item in items:
            # Paso 3.1: Serializar tipos de reparación del item
            tipos_reparacion = []
            for tipo in item.tipos_reparacion.all():
                tipos_reparacion.append({
                    'tipoReparacion_id': tipo.tipoReparacion_id,  # ID único del tipo de reparación
                    'nombre': tipo.nombre,  # Nombre del tipo de reparación
                    'descripcion': tipo.descripcion or '',  # Descripción (vacío si no tiene)
                })
            
            # Paso 3.2: Agregar datos del item con su sección y tipos de reparación
            items_data.append({
                'itemPauta_id': item.itemPauta_id,  # ID único del item
                'seccion': {
                    'seccion_id': item.seccion_id.seccion_id,  # ID de la sección
                    'nombre': item.seccion_id.nombre,  # Nombre de la sección
                },
                'tipos_reparacion': tipos_reparacion  # Lista de tipos de reparación del item
            })
        
        # Paso 4: Construir objeto con información completa de la pauta
        pauta_data = {
            'pauta_id': pauta.pauta_id,  # ID único de la pauta
            'nombre': pauta.nombre,  # Nombre de la pauta
            'descripcion': pauta.descripcion or '',  # Descripción (vacío si no tiene)
            'activo': pauta.activo,  # Estado de activación de la pauta
            'modeloEquipo': {
                'modeloEquipo_id': pauta.modeloEquipo_id.modeloEquipo_id,  # ID del modelo
                'nombre': pauta.modeloEquipo_id.modeloEquipo,  # Nombre del modelo
                'tipoEquipo_id': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo_id,  # ID del tipo
                'marcaEquipo_id': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
            },
            'tipoEquipo': {
                'tipoEquipo_id': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo_id,  # ID del tipo
                'nombre': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo,  # Nombre del tipo
                'sigla': pauta.modeloEquipo_id.tipoEquipo_id.siglaEquipo,  # Sigla del tipo
            },
            'marcaEquipo': {
                'marcaEquipo_id': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo_id,  # ID de la marca
                'nombre': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo,  # Nombre de la marca
            },
            'items': items_data,  # Lista de items con sus secciones y tipos de reparación
            'fecha_creacion': pauta.fecha_creacion.strftime('%Y-%m-%d %H:%M'),  # Fecha de creación formateada
            'fecha_modificacion': pauta.fecha_modificacion.strftime('%Y-%m-%d %H:%M'),  # Fecha de modificación formateada
        }
        
        # Paso 5: Retornar respuesta JSON con información completa de la pauta
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'pauta': pauta_data  # Objeto completo con todos los datos de la pauta
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        # CASO ERROR: La pauta no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de pauta: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA ORDEN DE TRABAJO (OT)
# ============================================================================

@login_required
@permission_required_custom('maquinarias.view_ordentrabajo')
def lista_ordenes_trabajo(request):
    """
    Vista principal para mostrar la lista de órdenes de trabajo.
    
    Esta vista renderiza la página HTML que muestra la lista de órdenes de trabajo.
    Los datos de las órdenes se cargan dinámicamente mediante AJAX desde la API api_listar_ordenes_trabajo.
    Esta función solo prepara los datos necesarios para los filtros del formulario.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_ordentrabajo'
    """
    # Paso 1: Obtener datos para poblar los filtros del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')  # Solo tipos de mantenimiento activos
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')  # Solo estados activos, ordenados por orden y nombre
    
    # Paso 2: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar la página
    context = {
        'empresas': empresas,  # Lista de empresas para el filtro de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el filtro de tipo
        'tipos_mantenimiento': tipos_mantenimiento,  # Lista de tipos de mantenimiento para el filtro
        'estados_ot': estados_ot,  # Lista de estados para el filtro de estado
    }
    
    # Paso 3: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/lista_ordenes_trabajo.html', context)


def obtener_calendario_maquinarias_optimizado(year, month, empresa_filter='', tipo_filter='', faena_filter='', search_query='', page=1, page_size=25):
    """
    Obtiene datos optimizados para el calendario de maquinarias con paginación.
    
    Esta función implementa una arquitectura optimizada que obtiene todos los datos necesarios
    de una vez y calcula los estados en memoria, evitando consultas N+1 y mejorando significativamente
    el rendimiento. Es escalable: el tiempo de ejecución no aumenta significativamente con más equipos.
    
    La función calcula el estado de cada equipo para cada día del mes basándose en:
    - Estados manuales asignados directamente a equipos
    - Estados de equipos desde órdenes de trabajo activas
    - Asignaciones a faenas (que pueden tener estados específicos)
    
    Parámetros:
        year: Año del calendario
        month: Mes del calendario (1-12)
        empresa_filter: Filtro opcional por nombre de empresa
        tipo_filter: Filtro opcional por tipo de equipo
        faena_filter: Filtro opcional por nombre de faena o "sin asignar"
        search_query: Término de búsqueda opcional para filtrar equipos
        page: Número de página para paginación (por defecto 1)
        page_size: Cantidad de equipos por página (por defecto 25)
    
    Retorna:
        dict: Diccionario con equipos, órdenes de trabajo, asignaciones a faenas,
              estados calculados y total de equipos
    """
    # Paso 1: Obtener rango de fechas del mes seleccionado
    # Se calcula el primer y último día del mes para filtrar datos
    _, ultimo_dia = monthrange(year, month)  # Obtener último día del mes
    fecha_inicio = date(year, month, 1)  # Primer día del mes
    fecha_fin = date(year, month, ultimo_dia)  # Último día del mes
    
    # Paso 2: Construir consulta base de equipos con relaciones optimizadas
    # select_related evita consultas N+1 al traer tipo, marca y empresa en una sola consulta SQL
    equipos_query = Equipo.objects.filter(activo=True).select_related(
        'modeloEquipo_id__tipoEquipo_id',  # Traer tipo de equipo a través del modelo
        'modeloEquipo_id__marcaEquipo_id',  # Traer marca a través del modelo
        'empresa_id'  # Traer datos de la empresa
    )
    
    # Paso 3: Aplicar filtros opcionales a la consulta de equipos
    # Cada filtro se aplica solo si fue proporcionado y no está vacío
    if empresa_filter and empresa_filter.strip():
        equipos_query = equipos_query.filter(empresa_id__nomFantasia__icontains=empresa_filter)  # Filtrar por nombre de empresa
    
    if tipo_filter and tipo_filter.strip():
        equipos_query = equipos_query.filter(modeloEquipo_id__tipoEquipo_id__tipoEquipo__icontains=tipo_filter)  # Filtrar por tipo de equipo
    
    if search_query and search_query.strip():
        equipos_query = equipos_query.filter(
            Q(nombreEquipo__icontains=search_query) |  # Buscar en nombre del equipo
            Q(codigoInterno__icontains=search_query) |  # Buscar en código interno
            Q(modeloEquipo_id__modeloEquipo__icontains=search_query)  # Buscar en nombre del modelo
        )
    
    # Paso 4: Aplicar filtro de faena (filtrar equipos que tienen asignación activa a esa faena)
    # Este filtro es más complejo porque requiere consultar asignaciones a faenas
    if faena_filter and faena_filter.strip():
        from ope_calendario.models import AsignacionEquipoFaena
        if faena_filter.lower() == 'sin asignar':
            # CASO: Filtrar equipos SIN asignaciones activas en el mes actual
            # Incluir tanto asignaciones con fecha_fin como asignaciones indefinidas (sin fecha_fin)
            equipos_con_asignaciones = AsignacionEquipoFaena.objects.filter(
                Q(activo=True) &  # Solo asignaciones activas
                Q(fecha_inicio__lte=fecha_fin) &  # La asignación comienza antes o en el último día del mes
                (Q(fecha_fin__gte=fecha_inicio) | Q(fecha_fin__isnull=True))  # La asignación termina después o en el primer día, o es indefinida
            ).values_list('equipo__equipo_id', flat=True).distinct()  # Obtener solo IDs únicos de equipos
            
            equipos_query = equipos_query.exclude(
                equipo_id__in=equipos_con_asignaciones  # Excluir equipos que tienen asignaciones
            )
        else:
            # CASO: Filtrar equipos que tienen asignación activa a esa faena específica
            equipos_en_faena = AsignacionEquipoFaena.objects.filter(
                faena__nombre__icontains=faena_filter,  # Filtrar por nombre de faena
                activo=True,  # Solo asignaciones activas
                fecha_inicio__lte=fecha_fin  # La asignación comienza antes o en el último día del mes
            ).filter(
                Q(fecha_fin__gte=fecha_inicio) | Q(fecha_fin__isnull=True)  # La asignación termina después o en el primer día, o es indefinida
            ).values_list('equipo__equipo_id', flat=True).distinct()  # Obtener solo IDs únicos de equipos
            
            equipos_query = equipos_query.filter(equipo_id__in=equipos_en_faena)  # Incluir solo equipos en esa faena
    
    # Paso 5: Contar total de equipos antes de aplicar paginación
    # Esto se necesita para calcular el total de páginas
    total_equipos = equipos_query.count()
    
    # Paso 6: Aplicar paginación a la consulta de equipos
    # Se calcula el offset y se obtienen solo los equipos de la página solicitada
    offset = (page - 1) * page_size  # Calcular desplazamiento (ej: página 2 con tamaño 25 = offset 25)
    equipos_list = list(equipos_query.order_by('nombreEquipo')[offset:offset + page_size])  # Obtener equipos ordenados alfabéticamente
    
    # Paso 7: Obtener IDs de los equipos paginados
    # Estos IDs se usan para filtrar los datos relacionados (OTs, asignaciones, estados)
    equipos_ids = [e.equipo_id for e in equipos_list]
    
    # Paso 8: Obtener TODOS los datos necesarios de UNA VEZ (optimización clave)
    # En lugar de hacer consultas individuales por equipo, se obtienen todos los datos relacionados
    # de una sola vez y luego se procesan en memoria
    
    # Paso 8.1: Obtener estados manuales de estos equipos en este mes
    # Los estados manuales son asignados directamente a equipos por fechas específicas
    estados_manuales = EstadoManualEquipo.objects.filter(
        equipo_id__in=equipos_ids,  # Solo equipos de la página actual
        fecha_inicio__lte=fecha_fin,  # El estado comienza antes o en el último día del mes
        fecha_fin__gte=fecha_inicio  # El estado termina después o en el primer día del mes
    ).select_related('equipo', 'estado')  # Optimizar carga de relaciones
    
    # Paso 8.2: Obtener todas las órdenes de trabajo que afectan estos equipos en este mes
    # Las OTs pueden cambiar el estado de los equipos durante su duración
    ordenes_trabajo = OrdenTrabajo.objects.filter(
        equipo_id__in=equipos_ids  # Solo equipos de la página actual
    ).filter(
        Q(fecha_inicio__lte=fecha_fin) & (  # La OT comienza antes o en el último día del mes
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)  # Y termina después o en el primer día, o es indefinida
        )
    ).select_related(
        'equipo_id', 'estado_equipo_id'  # Optimizar carga de relaciones
    )
    
    # Paso 8.3: Obtener todas las asignaciones a faenas de estos equipos en este mes
    # Las asignaciones a faenas muestran dónde está trabajando cada equipo
    from ope_calendario.models import AsignacionEquipoFaena
    asignaciones_faena = AsignacionEquipoFaena.objects.filter(
        equipo__equipo_id__in=equipos_ids,  # Solo equipos de la página actual
        activo=True  # Solo asignaciones activas
    ).filter(
        Q(fecha_inicio__lte=fecha_fin) & (  # La asignación comienza antes o en el último día del mes
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)  # Y termina después o en el primer día, o es indefinida
        )
    ).select_related('equipo', 'faena')  # Optimizar carga de relaciones
    
    # Paso 8.4: Obtener todos los mapeos de EstadoFuenteEquipo de una vez
    # Los mapeos relacionan estados de equipo (de OTs) con estados del calendario
    # Crear un diccionario para acceso rápido: estado_equipo_id -> estado_calendario
    mapeos_fuente = {}
    fuentes = EstadoFuenteEquipo.objects.select_related('estado_calendario', 'estado_equipo').all()
    for fuente in fuentes:
        if fuente.estado_calendario.activo:  # Solo incluir estados activos
            mapeos_fuente[fuente.estado_equipo.estadoEquipo_id] = fuente.estado_calendario
    
    # Paso 8.5: Obtener estado "Asignado" para asignaciones a faenas
    # Este estado se usa cuando un equipo está asignado a una faena pero no tiene OT
    estado_asignado_faena = EstadoCalendarioEquipo.objects.filter(
        activo=True, nombre__icontains='asignado'  # Buscar estado que contenga "asignado" en el nombre
    ).first()
    
    # Paso 8.6: Obtener estado predeterminado una sola vez
    # Este estado se usa cuando un equipo no tiene ningún estado específico en un día
    estado_predeterminado = EstadoCalendarioEquipo.objects.filter(
        activo=True, es_predeterminado=True  # Solo estados predeterminados activos
    ).first()
    
    # Paso 9: Crear diccionarios para acceso rápido en memoria
    # Estos diccionarios organizan los datos por equipo para facilitar el cálculo de estados
    
    # Paso 9.1: Organizar estados manuales por equipo
    estados_manuales_por_equipo = {}
    for em in estados_manuales:
        if em.equipo.equipo_id not in estados_manuales_por_equipo:
            estados_manuales_por_equipo[em.equipo.equipo_id] = []  # Crear lista si no existe
        estados_manuales_por_equipo[em.equipo.equipo_id].append(em)  # Agregar estado manual
    
    # Paso 9.2: Organizar órdenes de trabajo por equipo
    ot_por_equipo = {}
    for ot in ordenes_trabajo:
        if ot.equipo_id.equipo_id not in ot_por_equipo:
            ot_por_equipo[ot.equipo_id.equipo_id] = []  # Crear lista si no existe
        ot_por_equipo[ot.equipo_id.equipo_id].append(ot)  # Agregar orden de trabajo
    
    # Paso 9.3: Organizar asignaciones a faenas por equipo
    asignaciones_faena_por_equipo = {}
    for asig in asignaciones_faena:
        equipo_id = asig.equipo.equipo_id
        if equipo_id not in asignaciones_faena_por_equipo:
            asignaciones_faena_por_equipo[equipo_id] = []  # Crear lista si no existe
        asignaciones_faena_por_equipo[equipo_id].append(asig)  # Agregar asignación
    
    # Paso 10: Calcular estados en MEMORIA (sin consultas adicionales a la base de datos)
    # Esta es la parte clave de la optimización: todos los cálculos se hacen en memoria
    estados_calculados = {}
    
    for equipo in equipos_list:
        equipo_id = equipo.equipo_id
        estados_calculados[equipo_id] = {}  # Crear diccionario por equipo
        
        # Paso 10.1: Calcular estado para cada día del mes
        for day in range(1, ultimo_dia + 1):
            fecha_actual = date(year, month, day)  # Fecha del día actual
            estados_del_dia = []  # Lista de estados para este día (puede haber múltiples)
            
            # Paso 10.1.1: Revisar estados manuales primero (tienen mayor prioridad)
            # Los estados manuales son asignados directamente y tienen precedencia sobre otros estados
            if equipo_id in estados_manuales_por_equipo:
                manuales_del_dia = [
                    em for em in estados_manuales_por_equipo[equipo_id]
                    if em.fecha_inicio <= fecha_actual <= em.fecha_fin  # Verificar que el estado aplica a este día
                ]
                if manuales_del_dia:
                    # Ordenar por prioridad y tomar el más alto
                    manuales_del_dia.sort(key=lambda x: x.estado.prioridad, reverse=True)  # Ordenar descendente por prioridad
                    bloqueantes = [em for em in manuales_del_dia if em.estado.es_bloqueante]  # Filtrar estados bloqueantes
                    if bloqueantes:
                        estados_del_dia.append(bloqueantes[0].estado)  # Usar el estado bloqueante de mayor prioridad
                    else:
                        estados_del_dia.append(manuales_del_dia[0].estado)  # Usar el estado de mayor prioridad
            
            # Paso 10.1.2: Si no hay estados manuales, revisar órdenes de trabajo
            # Las OTs pueden cambiar el estado del equipo durante su duración
            if not estados_del_dia and equipo_id in ot_por_equipo:
                ot_del_dia = []
                for ot in ot_por_equipo[equipo_id]:
                    # Verificar que la OT está activa en este día
                    if ot.fecha_inicio <= fecha_actual:  # La OT ya comenzó
                        if ot.fecha_fin is None or ot.fecha_fin >= fecha_actual:  # La OT aún no ha terminado o es indefinida
                            if ot.estado_equipo_id:
                                # Buscar mapeo usando estadoEquipo_id como clave
                                # El mapeo convierte el estado de equipo a estado del calendario
                                estado_calendario = mapeos_fuente.get(ot.estado_equipo_id.estadoEquipo_id)
                                if estado_calendario:
                                    ot_del_dia.append({
                                        'estado': estado_calendario,  # Estado del calendario correspondiente
                                        'prioridad': estado_calendario.prioridad  # Prioridad del estado
                                    })
                
                if ot_del_dia:
                    # Ordenar por prioridad (mayor prioridad primero)
                    ot_del_dia.sort(key=lambda x: x['prioridad'], reverse=True)
                    bloqueantes_ot = [x for x in ot_del_dia if x['estado'].es_bloqueante]  # Filtrar estados bloqueantes
                    if bloqueantes_ot:
                        estados_del_dia.append(bloqueantes_ot[0]['estado'])  # Usar el estado bloqueante de mayor prioridad
                    else:
                        estados_del_dia.append(ot_del_dia[0]['estado'])  # Usar el estado de mayor prioridad
            
            # Paso 10.1.3: Si no hay estados manuales ni OT, revisar asignaciones a faenas
            # Las asignaciones a faenas muestran que el equipo está trabajando en una faena
            if not estados_del_dia and equipo_id in asignaciones_faena_por_equipo and estado_asignado_faena:
                asignaciones_del_dia = [
                    asig for asig in asignaciones_faena_por_equipo[equipo_id]
                    if asig.fecha_inicio <= fecha_actual and (  # La asignación ya comenzó
                        asig.fecha_fin is None or asig.fecha_fin >= fecha_actual  # La asignación aún no ha terminado o es indefinida
                    )
                ]
                if asignaciones_del_dia:
                    estados_del_dia.append(estado_asignado_faena)  # Usar estado "Asignado"
            
            # Paso 10.1.4: Si no hay nada, usar estado predeterminado
            # Este es el estado por defecto cuando el equipo no tiene ningún estado específico
            if not estados_del_dia and estado_predeterminado:
                estados_del_dia.append(estado_predeterminado)
            
            # Paso 10.1.5: Guardar estados calculados para este día
            estados_calculados[equipo_id][day] = estados_del_dia
    
    # Paso 11: Serializar asignaciones a faenas para el frontend
    # Se convierten a formato JSON para enviarlos al template
    asignaciones_faena_json = []
    for asig in asignaciones_faena:
        asignaciones_faena_json.append({
            'id': asig.id,  # ID único de la asignación
            'equipo_id': asig.equipo.equipo_id,  # ID del equipo asignado
            'faena_id': asig.faena.id,  # ID de la faena
            'faena_nombre': asig.faena.nombre,  # Nombre de la faena
            'faena_codigo': asig.faena.codigo,  # Código de la faena
            'fecha_inicio': asig.fecha_inicio.isoformat(),  # Fecha de inicio en formato ISO
            'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,  # Fecha de fin en formato ISO (o None)
            'observaciones': asig.observaciones or ''  # Observaciones de la asignación
        })
    
    # Paso 12: Retornar diccionario con todos los datos calculados
    # Este diccionario contiene toda la información necesaria para renderizar el calendario
    return {
        'equipos': equipos_list,  # Lista de equipos de la página actual
        'ordenes_trabajo': list(ordenes_trabajo),  # Lista de órdenes de trabajo que afectan estos equipos
        'asignaciones_faena': asignaciones_faena_json,  # Asignaciones a faenas serializadas en JSON
        'estados_calculados': estados_calculados,  # Estados calculados por equipo y día (diccionario anidado)
        'total_equipos': total_equipos,  # Total de equipos que cumplen los filtros (antes de paginación)
        'fecha_inicio': fecha_inicio,  # Primer día del mes
        'fecha_fin': fecha_fin,  # Último día del mes
        'dias_mes': ultimo_dia  # Cantidad de días en el mes
    }


@login_required
@permission_required_custom('maquinarias.view_ordentrabajo')
def calendario_maquinarias(request):
    """
    Vista para mostrar el calendario de maquinarias con órdenes de trabajo.
    
    Esta vista renderiza una página HTML que muestra un calendario mensual con información
    de equipos y sus órdenes de trabajo. Permite filtrar por empresa, tipo de equipo, faena
    y búsqueda de texto. Los datos se obtienen de forma optimizada mediante la función
    obtener_calendario_maquinarias_optimizado.
    
    Parámetros opcionales (query string):
        year: Año del calendario (por defecto año actual)
        month: Mes del calendario (por defecto mes actual)
        page: Número de página para paginación (por defecto 1)
        page_size: Cantidad de equipos por página (por defecto 10, opciones: 10, 25, 50, 100)
        empresa: Filtro por nombre de empresa
        tipo: Filtro por tipo de equipo
        faena: Filtro por nombre de faena o "sin asignar"
        search: Término de búsqueda para filtrar equipos
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
    
    Retorna:
        HttpResponse con template HTML renderizado del calendario
    """
    # Paso 1: Obtener parámetros de la URL o usar valores por defecto (fecha actual)
    # Se valida que los parámetros sean enteros válidos
    try:
        year = int(request.GET.get('year', datetime.now().year))  # Año del calendario
        month = int(request.GET.get('month', datetime.now().month))  # Mes del calendario
        page = int(request.GET.get('page', 1))  # Número de página
        page_size = int(request.GET.get('page_size', 10))  # Cantidad de equipos por página
    except (ValueError, TypeError):
        # Si hay error al convertir a entero, usar valores por defecto
        year = datetime.now().year
        month = datetime.now().month
        page = 1
        page_size = 10
    
    # Paso 2: Validar rango de fechas
    # Asegurar que el mes esté entre 1 y 12
    if month < 1 or month > 12:
        month = datetime.now().month
    # Asegurar que el año esté en un rango razonable
    if year < 1900 or year > 2100:
        year = datetime.now().year
    
    # Paso 3: Validar paginación
    # Asegurar que la página sea al menos 1
    if page < 1:
        page = 1
    # Asegurar que el tamaño de página sea uno de los valores permitidos
    if page_size not in [10, 25, 50, 100]:
        page_size = 10
    
    # Paso 4: Obtener filtros desde la URL
    # Estos filtros se pasan a la función optimizada para filtrar los equipos
    empresa_filter = request.GET.get('empresa', '')  # Filtro por nombre de empresa
    tipo_filter = request.GET.get('tipo', '')  # Filtro por tipo de equipo
    faena_filter = request.GET.get('faena', '')  # Filtro por nombre de faena o "sin asignar"
    search_query = request.GET.get('search', '')  # Término de búsqueda
    
    # Paso 5: Si no hay filtros de búsqueda activos, cargar TODOS los datos sin paginación
    # Esto permite que el filtro local funcione sobre todos los datos, igual que la tabla de personal
    # Si hay filtros de búsqueda activos, usar paginación normal
    if not search_query and not empresa_filter and not tipo_filter and not faena_filter:
        # Cargar todos los datos sin paginación para filtrado local
        calendario_data = obtener_calendario_maquinarias_optimizado(
            year, month, '', '', '', '', 1, 10000  # page_size muy grande para obtener todos
        )
        # Actualizar total_equipos y page_size para reflejar que se cargaron todos
        total_equipos = calendario_data['total_equipos']
        page_size = total_equipos  # Mostrar todos en una "página"
        total_pages = 1
        current_page = 1
    else:
        # Usar paginación normal cuando hay filtros activos
        calendario_data = obtener_calendario_maquinarias_optimizado(
            year, month, empresa_filter, tipo_filter, faena_filter, search_query, page, page_size
        )
        total_equipos = calendario_data['total_equipos']
        total_pages = (total_equipos + page_size - 1) // page_size if total_equipos > 0 else 1
        current_page = page
    
    # Paso 6: Obtener rango de fechas del mes para mostrar en el template
    # Se calcula el primer y último día del mes seleccionado
    _, ultimo_dia = monthrange(year, month)  # Obtener último día del mes
    fecha_inicio_mes = date(year, month, 1)  # Primer día del mes
    fecha_fin_mes = date(year, month, ultimo_dia)  # Último día del mes
    
    # Paso 7: Definir nombres de meses en español para mostrar en el template
    month_names = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Paso 8: Obtener empresas para filtros del formulario
    # Estas empresas se muestran en un select para filtrar el calendario
    empresas = Empresa.objects.all().order_by('nomFantasia')
    
    # Paso 9: Obtener faenas activas para filtros del formulario
    # Estas faenas se muestran en un select para filtrar equipos por faena
    from ope_calendario.models import Faena
    faenas = Faena.objects.filter(activo=True).order_by('nombre')
    
    # Paso 10: Obtener estados del calendario ordenados por prioridad
    # Los estados se usan para mostrar el estado de cada equipo en cada día del calendario
    estados_calendario = EstadoCalendarioEquipo.objects.filter(activo=True).order_by('-prioridad', 'nombre')
    
    # Paso 11: Preparar estados del calendario para JSON
    # Se serializan para enviarlos al frontend y renderizar el calendario
    from django.core.serializers.json import DjangoJSONEncoder
    estados_calendario_json = [
        {
            'id': estado.id,  # ID único del estado
            'nombre': estado.nombre,  # Nombre completo del estado
            'nombre_corto': estado.nombre_corto or estado.nombre[:3].upper(),  # Nombre corto (3 caracteres)
            'color': estado.color,  # Color del texto del estado
            'background_color': estado.background_color,  # Color de fondo del estado
            'prioridad': estado.prioridad,  # Prioridad del estado (para ordenar)
            'es_bloqueante': estado.es_bloqueante,  # Si el estado bloquea otras acciones
            'es_predeterminado': estado.es_predeterminado  # Si es el estado predeterminado
        }
        for estado in estados_calendario
    ]
    
    # Paso 12: Obtener estado predeterminado del calendario
    # Este estado se usa cuando un equipo no tiene estado específico en un día
    estado_predeterminado = EstadoCalendarioEquipo.objects.filter(es_predeterminado=True, activo=True).first()
    estado_predeterminado_json = None
    if estado_predeterminado:
        estado_predeterminado_json = {
            'id': estado_predeterminado.id,  # ID único del estado predeterminado
            'nombre': estado_predeterminado.nombre,  # Nombre completo
            'nombre_corto': estado_predeterminado.nombre_corto or estado_predeterminado.nombre[:3].upper(),  # Nombre corto
            'color': estado_predeterminado.color,  # Color del texto
            'background_color': estado_predeterminado.background_color  # Color de fondo
        }
    
    # Paso 13: Preparar estados calculados para JSON (serializar)
    # Los estados calculados muestran el estado de cada equipo en cada día del mes
    estados_calculados_json = {}
    for equipo_id, dias_estados in calendario_data['estados_calculados'].items():
        estados_calculados_json[str(equipo_id)] = {}  # Crear diccionario por equipo
        for dia, estados_lista in dias_estados.items():
            estados_serializados = []
            for estado in estados_lista:
                estados_serializados.append({
                    'id': estado.id,  # ID único del estado
                    'nombre': estado.nombre,  # Nombre completo
                    'nombre_corto': estado.nombre_corto or estado.nombre[:3].upper(),  # Nombre corto
                    'color': estado.color,  # Color del texto
                    'background_color': estado.background_color,  # Color de fondo
                    'prioridad': estado.prioridad,  # Prioridad del estado
                    'es_bloqueante': estado.es_bloqueante  # Si bloquea otras acciones
                })
            estados_calculados_json[str(equipo_id)][str(dia)] = estados_serializados  # Asignar estados al día
    
    # Paso 14: Usar las variables de paginación ya calculadas (o las que se calcularon arriba)
    # Si no se definieron arriba (caso con filtros), calcularlas ahora
    if 'total_pages' not in locals():
        total_pages = (calendario_data['total_equipos'] + page_size - 1) // page_size if calendario_data['total_equipos'] > 0 else 1
        current_page = page
    
    # Paso 15: Crear rango de páginas para el template
    # Esto permite mostrar los números de página en la interfaz
    page_range = range(1, total_pages + 1)
    
    # Paso 16: Serializar asignaciones a faenas para JSON
    # Las asignaciones muestran qué equipos están asignados a qué faenas en cada día
    asignaciones_faena_json = json.dumps(calendario_data['asignaciones_faena'], cls=DjangoJSONEncoder)
    
    # Paso 17: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar el calendario
    context = {
        'current_year': year,  # Año actual del calendario
        'current_month': month,  # Mes actual del calendario
        'current_month_name': month_names[month - 1],
        'empresas': empresas,
        'faenas': faenas,
        'estados_calendario': estados_calendario,
        'estados_calendario_json': json.dumps(estados_calendario_json, cls=DjangoJSONEncoder),
        'estado_predeterminado_json': json.dumps(estado_predeterminado_json, cls=DjangoJSONEncoder) if estado_predeterminado_json else 'null',
        'equipos': calendario_data['equipos'],
        'ordenes_trabajo': calendario_data['ordenes_trabajo'],
        'asignaciones_faena_json': asignaciones_faena_json,
        'estados_calculados': calendario_data['estados_calculados'],
        'estados_calculados_json': json.dumps(estados_calculados_json, cls=DjangoJSONEncoder),
        'fecha_inicio_mes': fecha_inicio_mes,
        'fecha_fin_mes': fecha_fin_mes,
        'dias_mes': ultimo_dia,
        'total_equipos': calendario_data['total_equipos'],
        'current_page': current_page,
        'page_size': page_size,
        'total_pages': total_pages,
        'page_range': page_range,
    }
    
    return render(request, 'maquinarias/calendario_maquinarias.html', context)


@login_required
@permission_required_custom('maquinarias.add_ordentrabajo')
def crear_orden_trabajo(request):
    """
    Vista para mostrar el formulario de crear una nueva orden de trabajo.
    
    Esta vista renderiza el formulario HTML para crear una nueva orden de trabajo.
    El formulario permite seleccionar equipo, tipo de mantenimiento, personal, fechas, etc.
    El formulario se envía mediante AJAX a la API api_guardar_orden_trabajo.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_ordentrabajo'
    """
    # Paso 1: Obtener datos para poblar los selects del formulario
    # Estos datos se envían al template para que el usuario pueda seleccionar opciones
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')  # Todos los modelos con relaciones optimizadas
    secciones = Seccion.objects.all().order_by('nombre')  # Todas las secciones ordenadas
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')  # Todos los tipos de reparación ordenados
    
    # Paso 2: Obtener tipos de mantenimiento, estados OT y estados equipo
    # Solo se muestran los activos para evitar opciones obsoletas
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')  # Solo tipos de mantenimiento activos
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')  # Solo estados OT activos, ordenados por orden y nombre
    estados_equipo = EstadoEquipo.objects.filter(activo=True).order_by('orden', 'nombre')  # Solo estados de equipo activos, ordenados por orden y nombre
    
    # Paso 3: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar el formulario
    context = {
        'empresas': empresas,  # Lista de empresas para el select de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo
        'marcas': marcas,  # Lista de marcas para el select de marca
        'modelos': modelos,  # Lista de modelos para el select de modelo
        'secciones': secciones,  # Lista de secciones para agregar items a la OT
        'tipos_reparacion': tipos_reparacion,  # Lista de tipos de reparación para agregar items
        'tipos_mantenimiento': tipos_mantenimiento,  # Lista de tipos de mantenimiento para el select
        'estados_ot': estados_ot,  # Lista de estados OT para el select
        'estados_equipo': estados_equipo,  # Lista de estados de equipo para el select
        'es_edicion': False,  # Flag que indica que es creación, no edición
    }
    
    # Paso 4: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/form_orden_trabajo.html', context)


@login_required
@permission_required_custom('maquinarias.change_ordentrabajo')
def editar_orden_trabajo(request, ot_id):
    """
    Vista para mostrar el formulario de editar una orden de trabajo existente.
    
    Esta vista renderiza el formulario HTML prellenado con los datos de la orden a editar.
    El formulario permite modificar todos los campos de la orden excepto si está finalizada o cancelada.
    El formulario se envía mediante AJAX a la API api_guardar_orden_trabajo.
    
    Parámetros:
        ot_id: ID de la orden de trabajo a editar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.change_ordentrabajo'
    """
    # Paso 1: Obtener la orden de trabajo desde la base de datos
    # Si no existe, se retorna un error 404 automáticamente
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
    
    # Paso 2: Verificar si la OT está finalizada o cancelada
    # Las órdenes finalizadas o canceladas no se pueden editar para mantener la integridad de los datos
    estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()  # Buscar estado "FINALIZADA"
    estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()  # Buscar estado "CANCELADA"
    
    # Si la OT está en estado finalizada o cancelada, no permitir edición
    if (estado_finalizada and ot.estado_ot_id == estado_finalizada) or (estado_cancelada and ot.estado_ot_id == estado_cancelada):
        messages.error(request, 'No se puede editar una orden de trabajo finalizada o cancelada.')
        return redirect('maquinarias:lista_ordenes_trabajo')  # Redirigir a la lista de órdenes
    
    # Paso 3: Obtener datos para poblar los selects del formulario
    # Estos datos se envían al template para que el usuario pueda cambiar las selecciones
    empresas = Empresa.objects.all().order_by('nomFantasia')  # Todas las empresas ordenadas por nombre
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')  # Todos los tipos de equipo ordenados
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')  # Todas las marcas ordenadas
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')  # Todos los modelos con relaciones optimizadas
    secciones = Seccion.objects.all().order_by('nombre')  # Todas las secciones ordenadas
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')  # Todos los tipos de reparación ordenados
    
    # Paso 4: Obtener tipos de mantenimiento, estados OT y estados equipo
    # Solo se muestran los activos para evitar opciones obsoletas
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')  # Solo tipos de mantenimiento activos
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')  # Solo estados OT activos, ordenados por orden y nombre
    estados_equipo = EstadoEquipo.objects.filter(activo=True).order_by('orden', 'nombre')  # Solo estados de equipo activos, ordenados por orden y nombre
    
    # Paso 5: Obtener items de secciones de la OT con sus relaciones optimizadas
    # prefetch_related optimiza las consultas para tipos de reparación, estados y secciones
    items_secciones = ItemSeccionOT.objects.filter(ot_id=ot).prefetch_related('tipos_reparacion', 'estado_seccion_id', 'seccion_id')
    
    # Paso 6: Obtener historial de observaciones de la OT ordenado por fecha descendente
    # Las observaciones más recientes aparecen primero
    historial_observaciones = HistorialObservacionesOT.objects.filter(ot_id=ot).order_by('-fecha')
    
    # Paso 7: Preparar el contexto para el template
    # El contexto contiene todos los datos que el template necesita para renderizar el formulario
    context = {
        'ot': ot,  # Instancia de la orden de trabajo con todos sus datos
        'empresas': empresas,  # Lista de empresas para el select de empresa
        'tipos_equipo': tipos_equipo,  # Lista de tipos para el select de tipo
        'marcas': marcas,  # Lista de marcas para el select de marca
        'modelos': modelos,  # Lista de modelos para el select de modelo
        'secciones': secciones,  # Lista de secciones para agregar items a la OT
        'tipos_reparacion': tipos_reparacion,  # Lista de tipos de reparación para agregar items
        'tipos_mantenimiento': tipos_mantenimiento,  # Lista de tipos de mantenimiento para el select
        'estados_ot': estados_ot,  # Lista de estados OT para el select
        'estados_equipo': estados_equipo,  # Lista de estados de equipo para el select
        'items_secciones': items_secciones,  # Items actuales de la OT con sus tipos de reparación
        'historial_observaciones': historial_observaciones,  # Historial de observaciones de la OT
        'es_edicion': True,  # Flag que indica que es edición, no creación
    }
    
    # Paso 8: Renderizar el template HTML con el contexto
    # Django combina el template con el contexto para generar el HTML final
    return render(request, 'maquinarias/form_orden_trabajo.html', context)


# ============================================================================
# APIs PARA ORDEN DE TRABAJO
# ============================================================================

@csrf_exempt
@login_required
@permission_required_custom('maquinarias.view_ordentrabajo', is_ajax=True)
@require_http_methods(["GET"])
def api_listar_ordenes_trabajo(request):
    """
    API para listar órdenes de trabajo con filtros múltiples y paginación.
    
    Esta función retorna una lista paginada de órdenes de trabajo con capacidad de filtrado
    por empresa, tipo de equipo, estado OT, estado equipo, tipo de mantenimiento y búsqueda de texto.
    También incluye lógica automática para finalizar órdenes cuya fecha de fin ha vencido.
    
    Parámetros opcionales (query string):
        empresa_id: ID de la empresa para filtrar
        tipo_equipo_id: ID del tipo de equipo para filtrar
        estado_ot: ID del estado OT para filtrar
        estado_equipo: ID del estado de equipo para filtrar
        tipo_mantenimiento: ID del tipo de mantenimiento para filtrar
        solo_finalizadas: 'true' para mostrar solo finalizadas/canceladas, 'false' para excluirlas
        search: Término de búsqueda para filtrar por folio, nombre de equipo, código interno u observaciones
        page: Número de página (por defecto 1)
        per_page: Cantidad de registros por página (por defecto 10)
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_ordentrabajo'
        - Método HTTP GET
    
    Retorna:
        JSON con lista de órdenes de trabajo, total de registros, página actual y total de páginas
    """
    try:
        # Paso 1: Verificar y actualizar OTs con fecha de fin vencida automáticamente
        # Esto asegura que las órdenes se finalicen automáticamente cuando su fecha de fin ha pasado
        estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()  # Buscar estado "FINALIZADA"
        estado_disponible = EstadoEquipo.objects.filter(nombre__iexact='Disponible').first()  # Buscar estado "Disponible"
        
        if estado_finalizada and estado_disponible:
            # Usar timezone para obtener la fecha de hoy en la zona horaria de Chile
            from django.utils import timezone
            hoy = timezone.now().date()
            # Buscar OTs activas con fecha de fin vencida
            # Se finaliza cuando la fecha de fin es menor que hoy (es decir, ya pasó)
            # Si fecha_fin es el día 5, se finaliza el día 6 (al día siguiente)
            ots_vencidas = OrdenTrabajo.objects.filter(
                fecha_fin__lt=hoy,
                estado_ot_id__isnull=False
            ).exclude(
                estado_ot_id=estado_finalizada
            ).select_related('estado_ot_id', 'estado_equipo_id')
            
            for ot in ots_vencidas:
                estado_ot_anterior = ot.estado_ot_id
                estado_equipo_anterior = ot.estado_equipo_id
                
                # Cambiar estado OT a FINALIZADA
                ot.estado_ot_id = estado_finalizada
                
                # Cambiar estado equipo a DISPONIBLE
                ot.estado_equipo_id = estado_disponible
                ot.save()
                
                # Registrar en historial
                HistorialOT.registrar(
                    ot=ot,
                    accion='ESTADO_OT_CAMBIADO',
                    descripcion=f"OT finalizada automáticamente por vencimiento de fecha de fin (fecha fin: {ot.fecha_fin.strftime('%d/%m/%Y')}). Estado cambiado de '{estado_ot_anterior.nombre if estado_ot_anterior else 'N/A'}' a '{estado_finalizada.nombre}'",
                    usuario=None,  # Sistema automático
                    datos_previos={'estado_ot_id': estado_ot_anterior.estadoOT_id if estado_ot_anterior else None, 'estado_ot_nombre': estado_ot_anterior.nombre if estado_ot_anterior else None},
                    datos_nuevos={'estado_ot_id': estado_finalizada.estadoOT_id, 'estado_ot_nombre': estado_finalizada.nombre}
                )
                
                if estado_equipo_anterior != estado_disponible:
                    HistorialOT.registrar(
                        ot=ot,
                        accion='ESTADO_EQUIPO_CAMBIADO',
                        descripcion=f"Estado de equipo cambiado automáticamente a DISPONIBLE al finalizar la OT. Estado cambiado de '{estado_equipo_anterior.nombre if estado_equipo_anterior else 'N/A'}' a '{estado_disponible.nombre}'",
                        usuario=None,  # Sistema automático
                        datos_previos={'estado_equipo_id': estado_equipo_anterior.estadoEquipo_id if estado_equipo_anterior else None, 'estado_equipo_nombre': estado_equipo_anterior.nombre if estado_equipo_anterior else None},
                        datos_nuevos={'estado_equipo_id': estado_disponible.estadoEquipo_id, 'estado_equipo_nombre': estado_disponible.nombre}
                    )
        
        # Paso 2: Obtener parámetros de filtro y paginación desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        empresa_id = request.GET.get('empresa_id', None)  # ID de empresa para filtrar (opcional)
        tipo_equipo_id = request.GET.get('tipo_equipo_id', None)  # ID de tipo de equipo para filtrar (opcional)
        estado_ot = request.GET.get('estado_ot', None)  # ID de estado OT para filtrar (opcional)
        estado_equipo = request.GET.get('estado_equipo', None)  # ID de estado de equipo para filtrar (opcional)
        tipo_mantenimiento = request.GET.get('tipo_mantenimiento', None)  # ID de tipo de mantenimiento para filtrar (opcional)
        solo_finalizadas = request.GET.get('solo_finalizadas', 'false').lower() == 'true'  # Flag para mostrar solo finalizadas o excluirlas
        search = request.GET.get('search', '').strip()  # Término de búsqueda (sin espacios)
        page = int(request.GET.get('page', 1))  # Número de página actual (por defecto 1)
        per_page = int(request.GET.get('per_page', 10))  # Cantidad de registros por página (por defecto 10)
        
        # Paso 3: Construir la consulta base con optimización
        # select_related evita consultas N+1 al traer todas las relaciones en una sola consulta SQL
        # prefetch_related optimiza la carga de personal_asignado (relación many-to-many)
        queryset = OrdenTrabajo.objects.select_related(
            'equipo_id',  # Traer datos del equipo
            'equipo_id__modeloEquipo_id',  # Traer modelo a través del equipo
            'equipo_id__modeloEquipo_id__tipoEquipo_id',  # Traer tipo a través del modelo
            'equipo_id__modeloEquipo_id__marcaEquipo_id',  # Traer marca a través del modelo
            'empresa_id',  # Traer datos de la empresa
            'pauta_id',  # Traer datos de la pauta (si existe)
            'tipo_mantenimiento_id',  # Traer datos del tipo de mantenimiento
            'estado_ot_id',  # Traer datos del estado OT
            'estado_equipo_id'  # Traer datos del estado de equipo
        ).prefetch_related('personal_asignado').all()  # Cargar personal asignado de forma optimizada
        
        # Paso 4: Filtrar por finalizadas o activas según el parámetro solo_finalizadas
        # Esto permite mostrar solo órdenes finalizadas/canceladas o excluirlas de los resultados
        if solo_finalizadas:
            # CASO: Mostrar solo órdenes finalizadas o canceladas
            # Obtener los estados "FINALIZADA" y "CANCELADA" para incluirlos en el filtro
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
            estados_finalizados = []
            if estado_finalizada:
                estados_finalizados.append(estado_finalizada.estadoOT_id)
            if estado_cancelada:
                estados_finalizados.append(estado_cancelada.estadoOT_id)
            if estados_finalizados:
                queryset = queryset.filter(estado_ot_id__in=estados_finalizados)  # Incluir solo finalizadas/canceladas
        else:
            # CASO: Excluir órdenes finalizadas y canceladas (mostrar solo activas)
            # Obtener los estados "FINALIZADA" y "CANCELADA" para excluirlos del filtro
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
            estados_finalizados = []
            if estado_finalizada:
                estados_finalizados.append(estado_finalizada.estadoOT_id)
            if estado_cancelada:
                estados_finalizados.append(estado_cancelada.estadoOT_id)
            if estados_finalizados:
                queryset = queryset.exclude(estado_ot_id__in=estados_finalizados)  # Excluir finalizadas/canceladas
        
        # Paso 5: Aplicar filtros específicos si fueron proporcionados
        # Cada filtro se aplica solo si tiene un valor, permitiendo combinaciones flexibles
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)  # Filtrar por empresa específica
        
        if tipo_equipo_id:
            queryset = queryset.filter(equipo_id__modeloEquipo_id__tipoEquipo_id=tipo_equipo_id)  # Filtrar por tipo de equipo
        
        if estado_ot:
            queryset = queryset.filter(estado_ot_id=estado_ot)  # Filtrar por estado OT específico
        
        if estado_equipo:
            queryset = queryset.filter(estado_equipo_id=estado_equipo)  # Filtrar por estado de equipo específico
        
        if tipo_mantenimiento:
            queryset = queryset.filter(tipo_mantenimiento_id=tipo_mantenimiento)  # Filtrar por tipo de mantenimiento
        
        # Paso 6: Aplicar filtro de búsqueda si fue proporcionado
        # La búsqueda busca en folio, nombre de equipo, código interno y observaciones usando OR
        if search:
            queryset = queryset.filter(
                Q(folio__icontains=search) |  # Buscar en folio de la OT
                Q(equipo_id__nombreEquipo__icontains=search) |  # Buscar en nombre del equipo
                Q(equipo_id__codigoInterno__icontains=search) |  # Buscar en código interno del equipo
                Q(observaciones__icontains=search)  # Buscar en observaciones de la OT
            )
        
        # Paso 7: Ordenar los resultados por fecha de creación descendente
        # Las órdenes más recientes aparecen primero
        queryset = queryset.order_by('-fecha_creacion')
        
        # Paso 8: Aplicar paginación a los resultados filtrados
        # Dividir los resultados en páginas según el tamaño de página solicitado
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)  # Obtener la página solicitada
        
        # Paso 9: Serializar los datos de las órdenes para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        ordenes = []
        for ot in page_obj:
            # Paso 9.1: Serializar personal asignado a la orden
            personal_asignado = []
            for p in ot.personal_asignado.all():
                # Obtener información laboral del personal para obtener su cargo
                info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
                cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
                personal_asignado.append({
                    'personal_id': p.personal_id,  # ID único del personal
                    'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",  # Nombre completo
                    'cargo': cargo_nombre  # Nombre del cargo
                })
            
            # Paso 9.2: Agregar datos de la orden con toda su información
            ordenes.append({
                'ot_id': ot.ot_id,  # ID único de la orden
                'folio': ot.folio,  # Folio de la orden
                'equipo': {
                    'equipo_id': ot.equipo_id.equipo_id,  # ID del equipo
                    'nombreEquipo': ot.equipo_id.nombreEquipo,  # Nombre del equipo
                    'codigoInterno': ot.equipo_id.codigoInterno,  # Código interno del equipo
                    'tipoEquipo': ot.equipo_id.modeloEquipo_id.tipoEquipo_id.tipoEquipo if ot.equipo_id.modeloEquipo_id.tipoEquipo_id else '',  # Tipo de equipo
                },
                'empresa': {
                    'empresa_id': ot.empresa_id.id if hasattr(ot.empresa_id, 'id') else None,  # ID de la empresa
                    'nomFantasia': ot.empresa_id.nomFantasia,  # Nombre de la empresa
                },
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else '',  # Nombre del tipo de mantenimiento
                'tipo_mantenimiento_id': ot.tipo_mantenimiento_id.tipoMantenimiento_id if ot.tipo_mantenimiento_id else None,  # ID del tipo de mantenimiento
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else 'No disponible',  # Nombre del estado OT
                'estado_ot_id': ot.estado_ot_id.estadoOT_id if ot.estado_ot_id else None,  # ID del estado OT
                'estado_ot_color': ot.estado_ot_id.color if ot.estado_ot_id else 'secondary',  # Color del estado OT
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else 'No disponible',  # Nombre del estado de equipo
                'estado_equipo_id': ot.estado_equipo_id.estadoEquipo_id if ot.estado_equipo_id else None,  # ID del estado de equipo
                'estado_equipo_color': ot.estado_equipo_id.color if ot.estado_equipo_id else 'secondary',  # Color del estado de equipo
                'fecha_creacion': ot.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if ot.fecha_creacion else None,  # Fecha de creación formateada
                'fecha_inicio': ot.fecha_inicio.strftime('%Y-%m-%d') if ot.fecha_inicio else None,  # Fecha de inicio formateada
                'fecha_fin': ot.fecha_fin.strftime('%Y-%m-%d') if ot.fecha_fin else None,  # Fecha de fin formateada
                'personal_asignado': personal_asignado,  # Lista de personal asignado
            })
        
        # Paso 10: Retornar respuesta JSON con los datos y metadatos de paginación
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'ordenes': ordenes,  # Lista de órdenes serializadas
            'pagination': {
                'page': page,  # Página actual
                'per_page': per_page,  # Cantidad de registros por página
                'total': paginator.count,  # Total de registros que cumplen los filtros
                'pages': paginator.num_pages,  # Total de páginas disponibles
                'has_next': page_obj.has_next(),  # Si hay página siguiente
                'has_prev': page_obj.has_previous(),  # Si hay página anterior
            }
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al listar ordenes de trabajo: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_equipos_filtrados(request):
    """
    API para obtener equipos activos filtrados por empresa, tipo, marca y modelo.
    
    Esta función retorna una lista de equipos activos que cumplen con los filtros especificados.
    Se usa principalmente para poblar selects en formularios de órdenes de trabajo.
    
    Parámetros opcionales (query string):
        empresa_id: ID de la empresa para filtrar equipos
        tipo_equipo_id: ID del tipo de equipo para filtrar
        marca_equipo_id: ID de la marca para filtrar
        modelo_equipo_id: ID del modelo para filtrar
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con lista de equipos que cumplen los filtros
    """
    try:
        # Paso 1: Obtener parámetros de filtro desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        empresa_id = request.GET.get('empresa_id', None)  # ID de empresa para filtrar (opcional)
        tipo_equipo_id = request.GET.get('tipo_equipo_id', None)  # ID de tipo para filtrar (opcional)
        marca_equipo_id = request.GET.get('marca_equipo_id', None)  # ID de marca para filtrar (opcional)
        modelo_equipo_id = request.GET.get('modelo_equipo_id', None)  # ID de modelo para filtrar (opcional)
        
        # Paso 2: Construir la consulta base solo con equipos activos y optimizada
        # select_related evita consultas N+1 al traer modelo, tipo, marca y empresa en una sola consulta SQL
        queryset = Equipo.objects.filter(activo=True).select_related(
            'modeloEquipo_id',  # Traer datos del modelo
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id',  # Traer marca a través del modelo
            'empresa_id'  # Traer datos de la empresa
        )
        
        # Paso 3: Aplicar filtros específicos si fueron proporcionados
        # Cada filtro se aplica solo si tiene un valor, permitiendo combinaciones flexibles
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)  # Filtrar por empresa específica
        
        if tipo_equipo_id:
            queryset = queryset.filter(modeloEquipo_id__tipoEquipo_id=tipo_equipo_id)  # Filtrar por tipo de equipo
        
        if marca_equipo_id:
            queryset = queryset.filter(modeloEquipo_id__marcaEquipo_id=marca_equipo_id)  # Filtrar por marca
        
        if modelo_equipo_id:
            queryset = queryset.filter(modeloEquipo_id=modelo_equipo_id)  # Filtrar por modelo específico
        
        # Paso 4: Serializar los equipos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        equipos = []
        for equipo in queryset.order_by('nombreEquipo'):  # Ordenar alfabéticamente por nombre
            equipos.append({
                'equipo_id': equipo.equipo_id,  # ID único del equipo
                'nombreEquipo': equipo.nombreEquipo,  # Nombre completo del equipo
                'codigoInterno': equipo.codigoInterno,  # Código interno único
                'patente': equipo.patente or '',  # Patente (vacío si no tiene)
                'horometro': equipo.horometro,  # Horas de uso del equipo
                'odometro': equipo.odometro,  # Kilómetros recorridos
                'horometroSuperEstructural': equipo.horometroSuperEstructural,  # Horas de superestructura
                'modeloEquipo_id': equipo.modeloEquipo_id.modeloEquipo_id if equipo.modeloEquipo_id else None,  # ID del modelo
                'tipoEquipo': equipo.modeloEquipo_id.tipoEquipo_id.tipoEquipo if equipo.modeloEquipo_id.tipoEquipo_id else '',  # Nombre del tipo
                'marcaEquipo': equipo.modeloEquipo_id.marcaEquipo_id.marcaEquipo if equipo.modeloEquipo_id.marcaEquipo_id else '',  # Nombre de la marca
                'modeloEquipo': equipo.modeloEquipo_id.modeloEquipo if equipo.modeloEquipo_id else '',  # Nombre del modelo
            })
        
        # Paso 5: Retornar respuesta JSON con la lista de equipos
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'equipos': equipos  # Lista de equipos serializados
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener equipos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_personal_maquinarias(request):
    """
    API para obtener personal activo con su cargo, empresa y departamento (con filtros opcionales).
    
    Esta función retorna una lista de personal activo que pertenece al departamento MAQUINARIAS
    y tiene el cargo MECÁNICO. Siempre filtra automáticamente por estos criterios.
    Permite filtros adicionales por búsqueda de texto y empresa.
    
    Parámetros opcionales (query string):
        search: Término de búsqueda para filtrar por nombre, apellidos o RUT
        empresa_id: ID de la empresa para filtrar personal de una empresa específica
    
    Requisitos:
        - Método HTTP GET
        - Debe existir el departamento "MAQUINARIAS" en la base de datos
        - Debe existir el cargo "MECÁNICO" en el departamento MAQUINARIAS
    
    Retorna:
        JSON con lista de personal que cumple los criterios (departamento MAQUINARIAS y cargo MECÁNICO)
    """
    try:
        # Paso 1: Obtener parámetros de filtro desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        search = request.GET.get('search', '').strip()  # Término de búsqueda (sin espacios)
        empresa_id = request.GET.get('empresa_id', None)  # ID de empresa para filtrar (opcional)
        
        # Paso 2: Buscar departamento MAQUINARIAS (case insensitive)
        # Este departamento es obligatorio para filtrar el personal
        depto_maquinarias = DeptoEmpresa.objects.filter(
            depto__iexact='MAQUINARIAS'  # Buscar sin importar mayúsculas/minúsculas
        ).first()
        
        # Si no existe el departamento, retornar error
        if not depto_maquinarias:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró el departamento MAQUINARIAS'
            }, status=404)
        
        # Paso 3: Buscar cargo MECÁNICO o MECANICO (case insensitive)
        # Este cargo es obligatorio para filtrar el personal
        cargo_mecanico = Cargo.objects.filter(
            depto_id=depto_maquinarias  # Buscar solo en el departamento MAQUINARIAS
        ).filter(
            Q(cargo__iexact='MECÁNICO') | Q(cargo__iexact='MECANICO')  # Aceptar ambas variantes
        ).first()
        
        # Si no existe el cargo, retornar error
        if not cargo_mecanico:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró el cargo MECÁNICO en el departamento MAQUINARIAS'
            }, status=404)
        
        # Paso 4: Obtener IDs de personal que tienen InfoLaboral con depto MAQUINARIAS y cargo MECÁNICO
        # Esto filtra el personal que cumple con los criterios obligatorios
        info_laboral_ids = InfoLaboral.objects.filter(
            depto_id=depto_maquinarias,  # Departamento MAQUINARIAS
            cargo_id=cargo_mecanico  # Cargo MECÁNICO
        ).values_list('personal_id', flat=True)  # Obtener solo los IDs de personal
        
        # Paso 5: Construir la consulta base de personal activo con los filtros aplicados
        # prefetch_related optimiza las consultas para información laboral, cargo, departamento y empresa
        queryset = Personal.objects.filter(
            activo=True,  # Solo personal activo
            personal_id__in=info_laboral_ids  # Solo personal que cumple los criterios
        ).prefetch_related('infolaboral_set__cargo_id', 'infolaboral_set__depto_id', 'infolaboral_set__empresa_id')
        
        # Paso 6: Aplicar filtro de búsqueda si fue proporcionado
        # La búsqueda busca en nombre, apellidos y RUT usando OR (cualquier coincidencia)
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |  # Buscar en nombre
                Q(apepat__icontains=search) |  # Buscar en apellido paterno
                Q(apemat__icontains=search) |  # Buscar en apellido materno
                Q(rut__icontains=search)  # Buscar en RUT
            )
        
        # Paso 7: Serializar el personal para enviarlo como JSON
        # Convertir los objetos Django a diccionarios Python
        personal = []
        for p in queryset:
            # Paso 7.1: Obtener InfoLaboral que coincida con los filtros (MAQUINARIAS y MECÁNICO)
            # Esto asegura que solo se incluya personal con la información laboral correcta
            info_laboral = InfoLaboral.objects.filter(
                personal_id=p,  # Personal actual
                depto_id=depto_maquinarias,  # Departamento MAQUINARIAS
                cargo_id=cargo_mecanico  # Cargo MECÁNICO
            ).first()
            
            # Si no tiene InfoLaboral que coincida, saltar este personal
            if not info_laboral:
                continue
            
            # Paso 7.2: Extraer información del cargo, departamento y empresa
            cargo_nombre = info_laboral.cargo_id.cargo if info_laboral.cargo_id else 'Sin cargo'
            cargo_id_val = info_laboral.cargo_id.cargo_id if info_laboral.cargo_id else None
            depto_nombre = info_laboral.depto_id.depto if info_laboral.depto_id else 'Sin departamento'
            depto_id_val = info_laboral.depto_id.depto_id if info_laboral.depto_id else None
            empresa_nombre = info_laboral.empresa_id.nomFantasia if info_laboral.empresa_id else 'Sin empresa'
            empresa_id_val = info_laboral.empresa_id.id if info_laboral.empresa_id else None
            
            # Paso 7.3: Aplicar filtro de empresa si se especifica
            # Si se solicita filtrar por empresa y el personal no pertenece a esa empresa, saltarlo
            if empresa_id and empresa_id_val != int(empresa_id):
                continue
            
            # Paso 7.4: Agregar datos del personal a la lista
            personal.append({
                'personal_id': p.personal_id,  # ID único del personal
                'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",  # Nombre completo
                'rut': f"{p.rut}-{p.dvrut}",  # RUT completo con dígito verificador
                'cargo': cargo_nombre,  # Nombre del cargo
                'cargo_id': cargo_id_val,  # ID del cargo
                'departamento': depto_nombre,  # Nombre del departamento
                'depto_id': depto_id_val,  # ID del departamento
                'empresa': empresa_nombre,  # Nombre de la empresa
                'empresa_id': empresa_id_val,  # ID de la empresa
            })
        
        # Paso 8: Retornar respuesta JSON con la lista de personal
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'personal': personal  # Lista de personal serializado
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener personal: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_marcas_por_tipo(request):
    """
    API para obtener marcas filtradas por tipo de equipo (para filtros en cascada).
    
    Esta función retorna las marcas que tienen modelos asociados a un tipo de equipo específico.
    Se usa para implementar filtros en cascada: primero se selecciona el tipo, luego se muestran
    solo las marcas que tienen modelos de ese tipo.
    
    Parámetros (query string):
        tipo_id: ID del tipo de equipo para filtrar marcas
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con lista de marcas que tienen modelos del tipo especificado
    """
    try:
        # Paso 1: Obtener parámetro tipo_id desde la URL
        # Este parámetro viene como query string en la petición GET
        tipo_id = request.GET.get('tipo_id', None)  # ID del tipo de equipo
        
        # Paso 2: Validar que se proporcionó el tipo_id
        # Si no se proporciona, retornar lista vacía (no hay marcas para mostrar)
        if not tipo_id:
            return JsonResponse({
                'success': True,  # Éxito pero sin datos
                'marcas': []  # Lista vacía de marcas
            })
        
        # Paso 3: Obtener modelos del tipo seleccionado con optimización
        # select_related evita consultas N+1 al traer la marca en una sola consulta SQL
        modelos = ModeloEquipo.objects.filter(tipoEquipo_id=tipo_id).select_related('marcaEquipo_id')
        
        # Paso 4: Obtener IDs únicos de marcas que tienen modelos del tipo especificado
        # distinct() asegura que no haya IDs duplicados
        marcas_ids = modelos.values_list('marcaEquipo_id', flat=True).distinct()
        
        # Paso 5: Obtener las marcas correspondientes ordenadas alfabéticamente
        marcas = MarcaEquipo.objects.filter(marcaEquipo_id__in=marcas_ids).order_by('marcaEquipo')
        
        # Paso 6: Serializar las marcas para enviarlas como JSON
        # Convertir los objetos Django a diccionarios Python
        marcas_list = [{
            'marcaEquipo_id': m.marcaEquipo_id,  # ID único de la marca
            'marcaEquipo': m.marcaEquipo  # Nombre de la marca
        } for m in marcas]
        
        # Paso 7: Retornar respuesta JSON con la lista de marcas
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'marcas': marcas_list  # Lista de marcas serializadas
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener marcas: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_modelos_por_tipo_marca(request):
    """
    API para obtener modelos filtrados por tipo y marca (para filtros en cascada).
    
    Esta función retorna los modelos que pertenecen a un tipo de equipo y una marca específicos.
    Se usa para implementar filtros en cascada: primero se selecciona el tipo, luego la marca,
    y finalmente se muestran solo los modelos que cumplen ambas condiciones.
    
    Parámetros (query string):
        tipo_id: ID del tipo de equipo para filtrar modelos
        marca_id: ID de la marca para filtrar modelos
    
    Requisitos:
        - Método HTTP GET
        - Ambos parámetros (tipo_id y marca_id) son requeridos
    
    Retorna:
        JSON con lista de modelos que pertenecen al tipo y marca especificados
    """
    try:
        # Paso 1: Obtener parámetros tipo_id y marca_id desde la URL
        # Estos parámetros vienen como query strings en la petición GET
        tipo_id = request.GET.get('tipo_id', None)  # ID del tipo de equipo
        marca_id = request.GET.get('marca_id', None)  # ID de la marca
        
        # Paso 2: Validar que se proporcionaron ambos parámetros
        # Si falta alguno, retornar lista vacía (no hay modelos para mostrar)
        if not tipo_id or not marca_id:
            return JsonResponse({
                'success': True,  # Éxito pero sin datos
                'modelos': []  # Lista vacía de modelos
            })
        
        # Paso 3: Obtener modelos que cumplen ambas condiciones con optimización
        # select_related evita consultas N+1 al traer tipo y marca en una sola consulta SQL
        modelos = ModeloEquipo.objects.filter(
            tipoEquipo_id=tipo_id,  # Filtrar por tipo de equipo
            marcaEquipo_id=marca_id  # Filtrar por marca
        ).select_related('tipoEquipo_id', 'marcaEquipo_id').order_by('modeloEquipo')  # Ordenar alfabéticamente
        
        # Paso 4: Serializar los modelos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        modelos_list = [{
            'modeloEquipo_id': m.modeloEquipo_id,  # ID único del modelo
            'modeloEquipo': m.modeloEquipo  # Nombre del modelo
        } for m in modelos]
        
        # Paso 5: Retornar respuesta JSON con la lista de modelos
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'modelos': modelos_list  # Lista de modelos serializados
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener modelos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_cargos_por_depto(request):
    """
    API para obtener cargos filtrados por departamento.
    
    Esta función retorna los cargos que pertenecen a un departamento específico.
    Se usa para implementar filtros en cascada: primero se selecciona el departamento,
    luego se muestran solo los cargos de ese departamento.
    
    Parámetros (query string):
        depto_id: ID del departamento para filtrar cargos
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con lista de cargos que pertenecen al departamento especificado
    """
    try:
        # Paso 1: Obtener parámetro depto_id desde la URL
        # Este parámetro viene como query string en la petición GET
        depto_id = request.GET.get('depto_id', None)  # ID del departamento
        
        # Paso 2: Validar que se proporcionó el depto_id
        # Si no se proporciona, retornar lista vacía (no hay cargos para mostrar)
        if not depto_id:
            return JsonResponse({
                'success': True,  # Éxito pero sin datos
                'cargos': []  # Lista vacía de cargos
            })
        
        # Paso 3: Importar modelo Cargo desde la app rrhh_personal
        # Este modelo está en otra app del proyecto
        from rrhh_personal.models import Cargo
        
        # Paso 4: Obtener cargos del departamento especificado ordenados alfabéticamente
        cargos = Cargo.objects.filter(depto_id=depto_id).order_by('cargo')
        
        # Paso 5: Serializar los cargos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        cargos_list = [{
            'cargo_id': c.cargo_id,  # ID único del cargo
            'cargo': c.cargo  # Nombre del cargo
        } for c in cargos]
        
        # Paso 6: Retornar respuesta JSON con la lista de cargos
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'cargos': cargos_list  # Lista de cargos serializados
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener cargos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_departamentos(request):
    """
    API para obtener todos los departamentos de la empresa.
    
    Esta función retorna una lista completa de todos los departamentos disponibles en el sistema.
    Se usa para poblar selects en formularios que requieren seleccionar un departamento.
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con lista completa de departamentos ordenados alfabéticamente
    """
    try:
        # Paso 1: Importar modelo DeptoEmpresa desde la app rrhh_personal
        # Este modelo está en otra app del proyecto
        from rrhh_personal.models import DeptoEmpresa
        
        # Paso 2: Obtener todos los departamentos ordenados alfabéticamente
        departamentos = DeptoEmpresa.objects.all().order_by('depto')
        
        # Paso 3: Serializar los departamentos para enviarlos como JSON
        # Convertir los objetos Django a diccionarios Python
        deptos_list = [{
            'depto_id': d.depto_id,  # ID único del departamento
            'depto': d.depto  # Nombre del departamento
        } for d in departamentos]
        
        # Paso 4: Retornar respuesta JSON con la lista de departamentos
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'departamentos': deptos_list  # Lista de departamentos serializados
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener departamentos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_pauta_ot(request, pauta_id):
    """
    API para obtener detalle de una pauta con sus secciones y estados (para mostrar en formulario de OT).
    
    Esta función retorna información completa de una pauta de mantenimiento, incluyendo sus items
    (secciones y tipos de reparación). Si se proporciona un ot_id, también incluye los estados
    actuales de cada sección en esa orden de trabajo.
    
    Parámetros:
        pauta_id: ID de la pauta cuyo detalle se va a obtener
    
    Parámetros opcionales (query string):
        ot_id: ID de la orden de trabajo para obtener estados actuales de las secciones
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con información completa de la pauta, items y estados de secciones (si hay OT)
    """
    try:
        # Paso 1: Obtener la pauta desde la base de datos
        # Si no existe, se retorna un error 404 automáticamente
        pauta = get_object_or_404(PautaMantenimientoPreventivo, pauta_id=pauta_id)
        
        # Paso 2: Verificar si se proporciona ot_id para obtener estados actuales
        # Si se proporciona ot_id, se obtienen los estados de ItemSeccionOT de esa OT
        ot_id = request.GET.get('ot_id', None)  # ID de la orden de trabajo (opcional)
        items_ot = None  # Variable para almacenar items de la OT
        
        if ot_id:
            try:
                # Paso 2.1: Obtener la orden de trabajo que usa esta pauta
                ot = OrdenTrabajo.objects.get(ot_id=ot_id, pauta_id=pauta)
                
                # Paso 2.2: Obtener items de secciones de la OT con sus estados optimizados
                # select_related evita consultas N+1 al traer estado y sección en una sola consulta SQL
                items_ot = ItemSeccionOT.objects.filter(ot_id=ot).select_related('estado_seccion_id', 'seccion_id')
                
                # Paso 2.3: Crear un diccionario para acceso rápido por seccion_id
                # Esto permite buscar rápidamente el estado de una sección específica
                estados_ot_dict = {item.seccion_id.seccion_id: item.estado_seccion_id for item in items_ot if item.estado_seccion_id}
            except OrdenTrabajo.DoesNotExist:
                # Si la OT no existe o no usa esta pauta, continuar sin estados
                items_ot = None
        
        # Paso 3: Obtener items de la pauta con sus relaciones optimizadas
        # prefetch_related optimiza las consultas para tipos de reparación de cada item
        items_pauta = ItemPauta.objects.filter(pauta_id=pauta).prefetch_related(
            'seccion_id',  # Traer datos de la sección
            'tipos_reparacion'  # Traer tipos de reparación del item
        )
        
        # Paso 4: Serializar los items de la pauta con sus estados (si hay OT)
        items = []
        for item in items_pauta:
            # Paso 4.1: Determinar el estado de la sección
            # Si hay OT, usar el estado de ItemSeccionOT; si no hay OT, no hay estado (se establecerá al crear la OT)
            estado_seccion = None
            if items_ot:
                estado_seccion = estados_ot_dict.get(item.seccion_id.seccion_id)  # Buscar estado por ID de sección
            
            # Paso 4.2: Agregar datos del item con su sección, tipos de reparación y estado
            items.append({
                'itemPauta_id': item.itemPauta_id,  # ID único del item de la pauta
                'seccion_id': item.seccion_id.seccion_id,  # ID de la sección
                'seccion_nombre': item.seccion_id.nombre,  # Nombre de la sección
                'tipos_reparacion': [{  # Lista de tipos de reparación del item
                    'tipoReparacion_id': tr.tipoReparacion_id,  # ID del tipo de reparación
                    'nombre': tr.nombre  # Nombre del tipo de reparación
                } for tr in item.tipos_reparacion.all()],
                'estado_seccion_id': estado_seccion.estadoOT_id if estado_seccion else None,  # ID del estado (si existe)
                'estado_seccion_nombre': estado_seccion.nombre if estado_seccion else None,  # Nombre del estado (si existe)
            })
        
        # Paso 5: Retornar respuesta JSON con información completa de la pauta
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'pauta': {
                'pauta_id': pauta.pauta_id,  # ID único de la pauta
                'nombre': pauta.nombre,  # Nombre de la pauta
                'descripcion': pauta.descripcion,  # Descripción de la pauta
                'modeloEquipo_id': pauta.modeloEquipo_id.modeloEquipo_id,  # ID del modelo asociado
            },
            'items': items  # Lista de items con secciones, tipos de reparación y estados
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de pauta: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.add_ordentrabajo', 'maquinarias.change_ordentrabajo', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_validar_disponibilidad_ot(request):
    """
    API para validar disponibilidad de equipo y mecánicos para una orden de trabajo.
    
    Esta función verifica si un equipo y los mecánicos seleccionados están disponibles
    en el rango de fechas especificado. Detecta conflictos con:
    - Asignaciones de faenas (equipos y personal asignados a faenas)
    - Otras órdenes de trabajo activas (no finalizadas ni canceladas)
    
    Si se proporciona ot_id, se excluye esa orden de la validación (útil en modo edición).
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_ordentrabajo' O 'maquinarias.change_ordentrabajo'
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición
    
    Retorna:
        JSON con indicador de disponibilidad y lista de conflictos encontrados
    """
    try:
        # Paso 1: Importar módulos necesarios
        from django.utils import timezone  # Para obtener fecha actual con zona horaria
        from ope_calendario.models import AsignacionFaena, AsignacionEquipoFaena  # Modelos de asignaciones
        from datetime import datetime, timedelta  # Para manejo de fechas
        
        # Paso 2: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        data = json.loads(request.body)
        equipo_id = data.get('equipo_id')  # ID del equipo a validar (opcional)
        personal_ids = data.get('personal_ids', [])  # Lista de IDs de personal/mecánicos a validar
        fecha_inicio = data.get('fecha_inicio')  # Fecha de inicio en formato 'YYYY-MM-DD' (requerida)
        fecha_fin = data.get('fecha_fin')  # Fecha de fin en formato 'YYYY-MM-DD' (opcional)
        ot_id = data.get('ot_id')  # ID de la OT actual (para excluirla en modo edición)
        
        # Paso 3: Validar que se proporcionó la fecha de inicio
        # La fecha de inicio es obligatoria para realizar la validación
        if not fecha_inicio:
            return JsonResponse({
                'success': False,
                'message': 'La fecha de inicio es requerida'
            }, status=400)
        
        # Paso 4: Convertir fecha de inicio de string a objeto date
        # Validar formato y convertir a objeto date de Python
        try:
            fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Formato de fecha de inicio inválido'
            }, status=400)
        
        # Paso 5: Convertir fecha de fin de string a objeto date (si fue proporcionada)
        # La fecha de fin es opcional; si no se proporciona, se considera indefinida
        fecha_fin_date = None
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de fecha de fin inválido'
                }, status=400)
        
        # Paso 6: Inicializar estructura para almacenar conflictos encontrados
        # Se separan conflictos de equipo y de personal para mejor organización
        conflictos = {
            'equipo': [],  # Lista de conflictos del equipo
            'personal': []  # Lista de conflictos del personal
        }
        
        # Paso 7: Validar disponibilidad del equipo
        # Se verifica si el equipo tiene conflictos con asignaciones de faenas u otras OTs
        if equipo_id:
            # Paso 7.1: Verificar asignaciones de faenas del equipo que se solapan con el rango de fechas
            # Buscar asignaciones activas que se solapan con el rango de fechas de la nueva OT
            asignaciones_faena_equipo = AsignacionEquipoFaena.objects.filter(
                equipo_id=equipo_id,  # Filtrar por equipo específico
                activo=True  # Solo asignaciones activas
            ).filter(
                Q(fecha_inicio__lte=fecha_fin_date if fecha_fin_date else timezone.now().date()) &  # La asignación comienza antes o en la fecha fin
                (Q(fecha_fin__gte=fecha_inicio_date) | Q(fecha_fin__isnull=True))  # La asignación termina después o en la fecha inicio, o es indefinida
            )
            
            # Paso 7.2: Agregar conflictos de asignaciones de faenas encontradas
            for asignacion in asignaciones_faena_equipo:
                conflictos['equipo'].append({
                    'tipo': 'faena',  # Tipo de conflicto: asignación a faena
                    'faena': asignacion.faena.nombre,  # Nombre de la faena
                    'fecha_inicio': asignacion.fecha_inicio.strftime('%d/%m/%Y'),  # Fecha de inicio formateada
                    'fecha_fin': asignacion.fecha_fin.strftime('%d/%m/%Y') if asignacion.fecha_fin else 'Indefinida'  # Fecha de fin formateada o "Indefinida"
                })
            
            # Paso 7.3: Verificar OTs activas del equipo que se solapan con el rango de fechas
            # Buscar OTs que no estén finalizadas ni canceladas y que tengan fecha de inicio
            ots_equipo = OrdenTrabajo.objects.filter(
                equipo_id=equipo_id,  # Filtrar por equipo específico
                fecha_inicio__isnull=False  # Solo OTs con fecha de inicio definida
            ).exclude(
                estado_ot_id__nombre__iexact='FINALIZADA'  # Excluir OTs finalizadas
            ).exclude(
                estado_ot_id__nombre__iexact='CANCELADA'  # Excluir OTs canceladas
            )
            
            # Paso 7.4: Si es edición, excluir la OT actual de la validación
            # Esto evita que la OT se detecte como conflicto consigo misma
            if ot_id:
                ots_equipo = ots_equipo.exclude(ot_id=ot_id)
            
            # Paso 7.5: Verificar solapamiento de fechas con otras OTs activas
            for ot in ots_equipo:
                if ot.fecha_inicio:
                    # Paso 7.5.1: Determinar fecha de fin de la OT existente
                    # Si no tiene fecha de fin, se considera indefinida (365 días desde hoy)
                    ot_fin = ot.fecha_fin if ot.fecha_fin else timezone.now().date() + timedelta(days=365)
                    
                    # Paso 7.5.2: Determinar fecha de fin de la nueva OT
                    # Si no tiene fecha de fin, se considera indefinida (365 días desde hoy)
                    nueva_fin = fecha_fin_date if fecha_fin_date else timezone.now().date() + timedelta(days=365)
                    
                    # Paso 7.5.3: Verificar si hay solapamiento de fechas
                    # Hay solapamiento si: ot_inicio <= nueva_fin AND nueva_inicio <= ot_fin
                    # Esto significa que los rangos de fechas se superponen
                    if ot.fecha_inicio <= nueva_fin and fecha_inicio_date <= ot_fin:
                        conflictos['equipo'].append({
                            'tipo': 'ot',  # Tipo de conflicto: otra orden de trabajo
                            'folio': ot.folio,  # Folio de la OT conflictiva
                            'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'N/A',  # Fecha de inicio formateada
                            'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Indefinida'  # Fecha de fin formateada o "Indefinida"
                        })
        
        # Paso 8: Validar disponibilidad del personal (mecánicos)
        # NOTA: Los mecánicos pueden ser asignados a múltiples OTs independientemente de las fechas
        # Por lo tanto, NO se validan conflictos de personal con otras OTs o faenas
        # Solo se valida disponibilidad del equipo
        
        disponible = len(conflictos['equipo']) == 0
        
        return JsonResponse({
            'success': True,
            'disponible': disponible,
            'conflictos': conflictos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al validar disponibilidad: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_multiple('maquinarias.add_ordentrabajo', 'maquinarias.change_ordentrabajo', require_all=False, is_ajax=True)
@require_http_methods(["POST"])
def api_guardar_orden_trabajo(request):
    """
    API unificada para crear o editar una orden de trabajo.
    
    Esta función maneja tanto la creación como la edición de órdenes de trabajo en una sola función.
    Determina automáticamente si es creación o edición basándose en la presencia de ot_id.
    
    En modo edición, solo actualiza estados, fechas y personal asignado (no modifica datos básicos).
    En modo creación, crea una nueva orden completa con todos sus datos.
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.add_ordentrabajo' O 'maquinarias.change_ordentrabajo'
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Paso 1: Parsear los datos JSON recibidos en el cuerpo de la petición
        # Los datos vienen como JSON desde el frontend
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON en api_guardar_orden_trabajo: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al parsear los datos JSON: {str(e)}'
            }, status=400)
        
        ot_id = data.get('ot_id')  # Si existe, es edición; si no, es creación
        logger.info(f"api_guardar_orden_trabajo: ot_id={ot_id}, modo={'EDICIÓN' if ot_id else 'CREACIÓN'}")
        logger.info(f"Datos recibidos: estados_secciones={data.get('estados_secciones', [])}, estados_pauta={data.get('estados_pauta', [])}")
        
        if ot_id:
            # MODO EDICIÓN: Actualizar una orden de trabajo existente
            # Paso 2: Obtener la orden existente desde la base de datos
            # Si no existe, se retorna un error 404 automáticamente
            ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
            
            # Paso 3: Guardar estados anteriores para comparación y registro en historial
            # Estos valores se usan para detectar cambios y registrar en el historial
            estado_ot_anterior = ot.estado_ot_id  # Estado OT anterior
            estado_equipo_anterior = ot.estado_equipo_id  # Estado de equipo anterior
            fecha_fin_anterior = ot.fecha_fin  # Fecha de fin anterior
            
            # Paso 4: Obtener estados OT y de equipo desde los datos recibidos
            # Si no se proporcionan, se usan valores por defecto
            estado_ot_id = data.get('estado_ot_id')  # ID del estado OT (opcional)
            if not estado_ot_id:
                # Si no se proporciona estado OT, usar "Pendiente" por defecto
                estado_ot = EstadoOT.objects.filter(nombre='Pendiente').first()
                if not estado_ot:
                    # Si no existe "Pendiente", usar el primer estado activo disponible
                    estado_ot = EstadoOT.objects.filter(activo=True).first()
            else:
                # Si se proporciona estado OT, obtenerlo desde la base de datos
                estado_ot = get_object_or_404(EstadoOT, estadoOT_id=estado_ot_id)
            
            estado_equipo_id = data.get('estado_equipo_id')  # ID del estado de equipo (opcional)
            if not estado_equipo_id:
                # Si no se proporciona estado de equipo, usar "Disponible" por defecto
                estado_equipo = EstadoEquipo.objects.filter(nombre='Disponible').first()
                if not estado_equipo:
                    # Si no existe "Disponible", usar el primer estado activo disponible
                    estado_equipo = EstadoEquipo.objects.filter(activo=True).first()
            else:
                # Si se proporciona estado de equipo, obtenerlo desde la base de datos
                estado_equipo = get_object_or_404(EstadoEquipo, estadoEquipo_id=estado_equipo_id)
            
            # Paso 5: Inicializar lista para rastrear cambios registrados en historial
            # Esto permite saber qué cambios se realizaron para retornar información al usuario
            cambios_registrados = []
            
            # Paso 6: Detectar y registrar cambio de estado OT
            # Solo se registra si el estado realmente cambió
            if estado_ot_anterior != estado_ot:
                # Paso 6.1: Registrar cambio en el historial de la OT
                HistorialOT.registrar(
                    ot=ot,  # Orden de trabajo afectada
                    accion='ESTADO_OT_CAMBIADO',  # Tipo de acción realizada
                    descripcion=f"Estado de OT cambiado de '{estado_ot_anterior.nombre if estado_ot_anterior else 'N/A'}' a '{estado_ot.nombre}'",  # Descripción del cambio
                    usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó el cambio
                    datos_previos={'estado_ot_id': estado_ot_anterior.estadoOT_id if estado_ot_anterior else None, 'estado_ot_nombre': estado_ot_anterior.nombre if estado_ot_anterior else None},  # Estado anterior
                    datos_nuevos={'estado_ot_id': estado_ot.estadoOT_id, 'estado_ot_nombre': estado_ot.nombre}  # Estado nuevo
                )
                cambios_registrados.append('estado_ot')  # Marcar que se cambió el estado OT
                
                # Paso 6.2: Si la OT se marca como FINALIZADA o CANCELADA, cambiar automáticamente el estado del equipo a DISPONIBLE
                # Esto asegura que el equipo quede disponible cuando la OT termina
                estado_ot_nombre_upper = estado_ot.nombre.upper()  # Convertir a mayúsculas para comparación
                if estado_ot_nombre_upper == 'FINALIZADA' or estado_ot_nombre_upper == 'CANCELADA':
                    estado_disponible = EstadoEquipo.objects.filter(nombre__iexact='Disponible').first()  # Buscar estado "Disponible"
                    if estado_disponible and estado_equipo != estado_disponible:
                        estado_equipo_anterior = estado_equipo  # Actualizar estado anterior para registrar el cambio
                        estado_equipo = estado_disponible  # Cambiar a "Disponible"
            
            # Paso 7: Detectar y registrar cambio de estado de equipo
            # Solo se registra si el estado realmente cambió
            if estado_equipo_anterior != estado_equipo:
                # Paso 7.1: Registrar cambio en el historial de la OT
                HistorialOT.registrar(
                    ot=ot,  # Orden de trabajo afectada
                    accion='ESTADO_EQUIPO_CAMBIADO',  # Tipo de acción realizada
                    descripcion=f"Estado de equipo cambiado de '{estado_equipo_anterior.nombre if estado_equipo_anterior else 'N/A'}' a '{estado_equipo.nombre}'",  # Descripción del cambio
                    usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó el cambio
                    datos_previos={'estado_equipo_id': estado_equipo_anterior.estadoEquipo_id if estado_equipo_anterior else None, 'estado_equipo_nombre': estado_equipo_anterior.nombre if estado_equipo_anterior else None},  # Estado anterior
                    datos_nuevos={'estado_equipo_id': estado_equipo.estadoEquipo_id, 'estado_equipo_nombre': estado_equipo.nombre}  # Estado nuevo
                )
                cambios_registrados.append('estado_equipo')  # Marcar que se cambió el estado de equipo
            
            # Paso 8: Detectar y registrar cambio de fecha de fin
            # La fecha de fin puede ser modificada o eliminada
            fecha_fin_nueva = data.get('fecha_fin')  # Nueva fecha de fin desde los datos (puede ser None)
            if fecha_fin_nueva:
                # CASO: Se proporcionó una nueva fecha de fin
                try:
                    # Paso 8.1: Convertir fecha de string a objeto date
                    fecha_fin_parsed = datetime.strptime(fecha_fin_nueva, '%Y-%m-%d').date()
                    
                    # Paso 8.2: Verificar si la fecha realmente cambió
                    if fecha_fin_anterior != fecha_fin_parsed:
                        # Paso 8.3: Registrar cambio en el historial
                        HistorialOT.registrar(
                            ot=ot,  # Orden de trabajo afectada
                            accion='FECHA_FIN_CAMBIADA',  # Tipo de acción realizada
                            descripcion=f"Fecha de fin cambiada de '{fecha_fin_anterior.strftime('%d/%m/%Y') if fecha_fin_anterior else 'No definida'}' a '{fecha_fin_parsed.strftime('%d/%m/%Y')}'",  # Descripción del cambio
                            usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó el cambio
                            datos_previos={'fecha_fin': fecha_fin_anterior.strftime('%Y-%m-%d') if fecha_fin_anterior else None},  # Fecha anterior
                            datos_nuevos={'fecha_fin': fecha_fin_nueva}  # Fecha nueva
                        )
                        cambios_registrados.append('fecha_fin')  # Marcar que se cambió la fecha de fin
                        ot.fecha_fin = fecha_fin_parsed  # Actualizar fecha de fin en la OT
                except (ValueError, TypeError):
                    # Si hay error en el formato de fecha, ignorar (no actualizar)
                    pass
            elif fecha_fin_anterior:  # CASO: Se eliminó la fecha de fin (había una fecha anterior)
                # Paso 8.4: Registrar eliminación de fecha de fin en el historial
                HistorialOT.registrar(
                    ot=ot,  # Orden de trabajo afectada
                    accion='FECHA_FIN_CAMBIADA',  # Tipo de acción realizada
                    descripcion=f"Fecha de fin eliminada (anteriormente era '{fecha_fin_anterior.strftime('%d/%m/%Y')}')",  # Descripción del cambio
                    usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó el cambio
                    datos_previos={'fecha_fin': fecha_fin_anterior.strftime('%Y-%m-%d')},  # Fecha anterior
                    datos_nuevos={'fecha_fin': None}  # Fecha nueva (None = eliminada)
                )
                cambios_registrados.append('fecha_fin')  # Marcar que se cambió la fecha de fin
                ot.fecha_fin = None  # Eliminar fecha de fin de la OT
            
            # Paso 9: Validar disponibilidad antes de actualizar personal o fechas
            # Esta validación asegura que no se asignen equipos o mecánicos que ya están ocupados
            # Verificar que el equipo existe antes de acceder a sus propiedades
            if not ot.equipo_id:
                return JsonResponse({
                    'success': False,
                    'message': 'La orden de trabajo no tiene un equipo asignado'
                }, status=400)
            
            equipo_id = ot.equipo_id.equipo_id  # ID del equipo de la OT
            fecha_inicio_ot = ot.fecha_inicio  # Fecha de inicio de la OT
            fecha_fin_nueva = data.get('fecha_fin')  # Nueva fecha de fin (si se proporciona)
            personal_ids_nuevo = data.get('personal_asignado', [])  # Nuevo personal asignado
            
            # Solo validar si hay fecha de inicio y hay cambios en personal o fecha fin
            if fecha_inicio_ot:
                # Determinar fecha fin a usar para validación
                fecha_fin_validacion = None
                if fecha_fin_nueva:
                    try:
                        fecha_fin_validacion = datetime.strptime(fecha_fin_nueva, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        pass
                elif ot.fecha_fin:
                    fecha_fin_validacion = ot.fecha_fin
                
                # Validar disponibilidad del equipo
                from django.utils import timezone
                from ope_calendario.models import AsignacionEquipoFaena
                from datetime import timedelta
                
                # Verificar conflictos de equipo con otras OTs
                ots_equipo_conflicto = OrdenTrabajo.objects.filter(
                    equipo_id=equipo_id,
                    fecha_inicio__isnull=False
                ).exclude(
                    estado_ot_id__nombre__iexact='FINALIZADA'
                ).exclude(
                    estado_ot_id__nombre__iexact='CANCELADA'
                ).exclude(
                    ot_id=ot_id  # Excluir la OT actual
                )
                
                nueva_fin = fecha_fin_validacion if fecha_fin_validacion else timezone.now().date() + timedelta(days=365)
                
                # Acumular todos los conflictos antes de retornar
                conflictos_equipo_edicion = []
                
                # Validar conflictos de equipo
                for ot_conflicto in ots_equipo_conflicto:
                    if ot_conflicto.fecha_inicio:
                        ot_fin = ot_conflicto.fecha_fin if ot_conflicto.fecha_fin else timezone.now().date() + timedelta(days=365)
                        if ot_conflicto.fecha_inicio <= nueva_fin and fecha_inicio_ot <= ot_fin:
                            conflictos_equipo_edicion.append({
                                'tipo': 'ot',
                                'folio': ot_conflicto.folio,
                                'fecha_inicio': ot_conflicto.fecha_inicio.strftime('%d/%m/%Y') if ot_conflicto.fecha_inicio else 'N/A',
                                'fecha_fin': ot_conflicto.fecha_fin.strftime('%d/%m/%Y') if ot_conflicto.fecha_fin else 'Indefinida'
                            })
                
                # NOTA: Los mecánicos pueden ser asignados a múltiples OTs independientemente de las fechas
                # Por lo tanto, NO se validan conflictos de personal con otras OTs
                
                # Si hay conflictos de equipo, retornar error
                if conflictos_equipo_edicion:
                    mensaje = 'No se puede guardar la orden de trabajo debido a conflictos de disponibilidad. El equipo está asignado a otra OT'
                    
                    return JsonResponse({
                        'success': False,
                        'message': mensaje,
                        'conflictos': {
                            'equipo': conflictos_equipo_edicion
                        }
                    }, status=400)
            
            # Paso 10: Actualizar personal asignado a la orden
            # El personal asignado es una relación many-to-many que puede cambiar
            personal_ids = data.get('personal_asignado', [])  # Lista de IDs de personal desde los datos
            if personal_ids is not None:
                # Paso 9.1: Obtener personal anterior para comparar
                # Se ordenan las listas para comparación correcta
                personal_anterior_ids = list(ot.personal_asignado.values_list('personal_id', flat=True))
                personal_anterior_ids.sort()  # Ordenar para comparación
                personal_nuevo_ids = sorted([int(pid) for pid in personal_ids])  # Convertir a int y ordenar
                
                # Paso 9.2: Solo actualizar si hay cambios en el personal asignado
                if personal_anterior_ids != personal_nuevo_ids:
                    # Paso 9.3: Actualizar la relación many-to-many con el nuevo personal
                    ot.personal_asignado.set(personal_ids)
                    
                    # Paso 9.4: Obtener objetos de personal para obtener nombres completos
                    personal_anterior = Personal.objects.filter(personal_id__in=personal_anterior_ids)
                    personal_nuevo = Personal.objects.filter(personal_id__in=personal_nuevo_ids)
                    
                    # Paso 9.5: Construir listas de nombres completos para el historial
                    nombres_anterior = [f"{p.nombre} {p.apepat}" for p in personal_anterior]
                    nombres_nuevo = [f"{p.nombre} {p.apepat}" for p in personal_nuevo]
                    
                    # Paso 9.6: Registrar cambio en el historial
                    HistorialOT.registrar(
                        ot=ot,  # Orden de trabajo afectada
                        accion='PERSONAL_ASIGNADO_CAMBIADO',  # Tipo de acción realizada
                        descripcion=f"Personal asignado cambiado. Anterior: {', '.join(nombres_anterior) if nombres_anterior else 'Ninguno'}. Nuevo: {', '.join(nombres_nuevo) if nombres_nuevo else 'Ninguno'}",  # Descripción del cambio
                        usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó el cambio
                        datos_previos={'personal_ids': personal_anterior_ids, 'personal_nombres': nombres_anterior},  # Personal anterior
                        datos_nuevos={'personal_ids': personal_nuevo_ids, 'personal_nombres': nombres_nuevo}  # Personal nuevo
                    )
                    cambios_registrados.append('personal_asignado')  # Marcar que se cambió el personal asignado
            
            # Paso 11: Actualizar estados y fecha de fin en la orden
            # Estos son los campos principales que se pueden modificar en modo edición
            ot.estado_ot_id = estado_ot  # Actualizar estado OT
            ot.estado_equipo_id = estado_equipo  # Actualizar estado de equipo
            
            # Paso 11.1: Permitir cambiar la pauta en modo edición (si se proporciona)
            pauta_id_nueva = data.get('pauta_id')
            if pauta_id_nueva:
                try:
                    pauta_nueva = get_object_or_404(PautaMantenimientoPreventivo, pauta_id=pauta_id_nueva)
                    pauta_anterior = ot.pauta_id
                    
                    # Solo actualizar si cambió la pauta
                    if pauta_anterior != pauta_nueva:
                        # Eliminar items de secciones antiguos de la pauta anterior
                        ItemSeccionOT.objects.filter(ot_id=ot).delete()
                        
                        # Actualizar la pauta
                        ot.pauta_id = pauta_nueva
                        ot.corresponde_pauta = True
                        
                        # Registrar cambio en historial
                        HistorialOT.registrar(
                            ot=ot,
                            accion='PAUTA_CAMBIADA',
                            descripcion=f"Pauta de mantenimiento cambiada de '{pauta_anterior.nombre if pauta_anterior else 'Ninguna'}' a '{pauta_nueva.nombre}'",
                            usuario=request.user if request.user.is_authenticated else None,
                            datos_previos={
                                'pauta_id': pauta_anterior.pauta_id if pauta_anterior else None,
                                'pauta_nombre': pauta_anterior.nombre if pauta_anterior else None
                            },
                            datos_nuevos={
                                'pauta_id': pauta_nueva.pauta_id,
                                'pauta_nombre': pauta_nueva.nombre
                            }
                        )
                        
                        # Crear nuevos items de secciones desde la nueva pauta
                        items_pauta_nueva = ItemPauta.objects.filter(pauta_id=pauta_nueva).prefetch_related('tipos_reparacion')
                        estado_pendiente = EstadoOT.objects.filter(nombre='Pendiente').first()
                        if not estado_pendiente:
                            estado_pendiente = EstadoOT.objects.filter(activo=True).first()
                        
                        for item_pauta in items_pauta_nueva:
                            item_seccion = ItemSeccionOT.objects.create(
                                ot_id=ot,
                                seccion_id=item_pauta.seccion_id,
                                estado_seccion_id=estado_pendiente
                            )
                            item_seccion.tipos_reparacion.set(item_pauta.tipos_reparacion.all())
                            
                            # Registrar agregado de sección en historial
                            tipos_nombres = list(item_seccion.tipos_reparacion.values_list('nombre', flat=True))
                            HistorialOT.registrar(
                                ot=ot,
                                accion='SECCION_AGREGADA',
                                descripcion=f"Sección '{item_pauta.seccion_id.nombre}' agregada desde nueva pauta. Tipos de reparación: {', '.join(tipos_nombres) if tipos_nombres else 'Ninguno'}. Estado: {estado_pendiente.nombre}",
                                usuario=request.user if request.user.is_authenticated else None,
                                datos_previos=None,
                                datos_nuevos={
                                    'seccion_id': item_pauta.seccion_id.seccion_id,
                                    'seccion_nombre': item_pauta.seccion_id.nombre,
                                    'tipos_reparacion_ids': list(item_seccion.tipos_reparacion.values_list('tipoReparacion_id', flat=True)),
                                    'tipos_reparacion_nombres': tipos_nombres,
                                    'estado_seccion_id': estado_pendiente.estadoOT_id,
                                    'estado_seccion_nombre': estado_pendiente.nombre
                                }
                            )
                except PautaMantenimientoPreventivo.DoesNotExist:
                    pass  # Si la pauta no existe, ignorar
            
            ot.save()  # Guardar cambios en la base de datos
            
            # Actualizar estados de secciones si se enviaron
            estados_pauta = data.get('estados_pauta', [])
            estados_secciones = data.get('estados_secciones', [])
            
            # Actualizar estados de pauta (los estados se guardan en ItemSeccionOT, no en ItemPauta)
            if estados_pauta and ot.pauta_id:
                for estado_data in estados_pauta:
                    item_pauta_id = estado_data.get('itemPauta_id')
                    seccion_id = estado_data.get('seccion_id')
                    estado_seccion_id = estado_data.get('estado_seccion_id')
                    
                    if seccion_id and estado_seccion_id:
                        try:
                            # Obtener el ItemPauta para validar que existe y obtener la sección
                            item_pauta = ItemPauta.objects.get(itemPauta_id=item_pauta_id, pauta_id=ot.pauta_id)
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                            
                            # Buscar o crear el ItemSeccionOT correspondiente
                            item_seccion_ot = ItemSeccionOT.objects.filter(
                                ot_id=ot,
                                seccion_id=item_pauta.seccion_id
                            ).first()
                            
                            if item_seccion_ot:
                                # Obtener estado anterior para comparar y registrar en historial
                                estado_seccion_anterior = item_seccion_ot.estado_seccion_id
                                
                                # Registrar cambio si el estado cambió
                                if estado_seccion_anterior != estado_seccion:
                                    HistorialOT.registrar(
                                        ot=ot,
                                        accion='ESTADO_SECCION_CAMBIADO',
                                        descripcion=f"Estado de sección '{item_pauta.seccion_id.nombre}' cambiado de '{estado_seccion_anterior.nombre if estado_seccion_anterior else 'Sin estado'}' a '{estado_seccion.nombre}'",
                                        usuario=request.user if request.user.is_authenticated else None,
                                        datos_previos={
                                            'seccion_id': item_pauta.seccion_id.seccion_id,
                                            'seccion_nombre': item_pauta.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion_anterior.estadoOT_id if estado_seccion_anterior else None,
                                            'estado_seccion_nombre': estado_seccion_anterior.nombre if estado_seccion_anterior else None
                                        },
                                        datos_nuevos={
                                            'seccion_id': item_pauta.seccion_id.seccion_id,
                                            'seccion_nombre': item_pauta.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion.estadoOT_id,
                                            'estado_seccion_nombre': estado_seccion.nombre
                                        }
                                    )
                                
                                # Actualizar estado en ItemSeccionOT (aquí es donde se guarda realmente)
                                item_seccion_ot.estado_seccion_id = estado_seccion
                                item_seccion_ot.save()
                        except (ItemPauta.DoesNotExist, EstadoOT.DoesNotExist):
                            pass
            
            # Paso 12: En modo edición, NO se permiten agregar/modificar/eliminar secciones
            # Solo se pueden cambiar los estados de las secciones existentes (manejado en estados_secciones)
            # En modo edición, NO procesar items_secciones (las secciones no se pueden modificar)
            # Solo se procesan cambios de estado a través de estados_secciones
            
            # Actualizar estados de secciones manuales (compatibilidad con código anterior)
            if estados_secciones:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Procesando {len(estados_secciones)} estados de secciones para OT {ot.ot_id}")
                
                # Obtener todos los items de secciones de la OT
                items_secciones_ot = ItemSeccionOT.objects.filter(ot_id=ot).select_related('seccion_id', 'estado_seccion_id')
                logger.info(f"Items de secciones encontrados en OT: {items_secciones_ot.count()}")
                
                # Mapear estados por sección_id
                for estado_data in estados_secciones:
                    seccion_id = estado_data.get('seccion_id')
                    estado_seccion_id = estado_data.get('estado_seccion_id')
                    logger.info(f"Procesando estado: seccion_id={seccion_id}, estado_seccion_id={estado_seccion_id}")
                    
                    if seccion_id and estado_seccion_id:
                        try:
                            # Convertir a entero si viene como string
                            seccion_id = int(seccion_id) if isinstance(seccion_id, str) else seccion_id
                            estado_seccion_id = int(estado_seccion_id) if isinstance(estado_seccion_id, str) else estado_seccion_id
                            logger.info(f"Valores convertidos: seccion_id={seccion_id} (type: {type(seccion_id)}), estado_seccion_id={estado_seccion_id} (type: {type(estado_seccion_id)})")
                            
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                            logger.info(f"EstadoOT obtenido: {estado_seccion.nombre} (ID: {estado_seccion.estadoOT_id})")
                            
                            # Actualizar el item de sección específico
                            # Usar seccion_id__seccion_id porque seccion_id es una ForeignKey, no un entero
                            item_ot = items_secciones_ot.filter(seccion_id__seccion_id=seccion_id).first()
                            logger.info(f"ItemSeccionOT encontrado: {item_ot is not None}")
                            
                            if item_ot:
                                logger.info(f"ItemSeccionOT: ot_id={item_ot.ot_id.ot_id}, seccion_id={item_ot.seccion_id.seccion_id}, estado_actual={item_ot.estado_seccion_id.nombre if item_ot.estado_seccion_id else 'None'}")
                                
                                # Obtener estado anterior para comparar
                                estado_seccion_anterior = item_ot.estado_seccion_id
                                
                                # Registrar cambio si el estado cambió
                                if estado_seccion_anterior != estado_seccion:
                                    logger.info(f"Estado cambió de {estado_seccion_anterior.nombre if estado_seccion_anterior else 'None'} a {estado_seccion.nombre}")
                                    try:
                                        HistorialOT.registrar(
                                            ot=ot,
                                            accion='ESTADO_SECCION_CAMBIADO',
                                            descripcion=f"Estado de sección '{item_ot.seccion_id.nombre}' cambiado de '{estado_seccion_anterior.nombre if estado_seccion_anterior else 'Sin estado'}' a '{estado_seccion.nombre}'",
                                            usuario=request.user if request.user.is_authenticated else None,
                                            datos_previos={
                                                'seccion_id': item_ot.seccion_id.seccion_id,
                                                'seccion_nombre': item_ot.seccion_id.nombre,
                                                'estado_seccion_id': estado_seccion_anterior.estadoOT_id if estado_seccion_anterior else None,
                                                'estado_seccion_nombre': estado_seccion_anterior.nombre if estado_seccion_anterior else None
                                            },
                                            datos_nuevos={
                                                'seccion_id': item_ot.seccion_id.seccion_id,
                                                'seccion_nombre': item_ot.seccion_id.nombre,
                                                'estado_seccion_id': estado_seccion.estadoOT_id,
                                                'estado_seccion_nombre': estado_seccion.nombre
                                            }
                                        )
                                        logger.info("Historial registrado exitosamente")
                                    except Exception as hist_error:
                                        logger.error(f"Error al registrar historial: {str(hist_error)}", exc_info=True)
                                        # No re-lanzar, continuar con el guardado del estado aunque falle el historial
                                
                                logger.info(f"Actualizando estado de ItemSeccionOT {item_ot.itemSeccionOT_id}")
                                item_ot.estado_seccion_id = estado_seccion
                                item_ot.save()
                                logger.info(f"ItemSeccionOT guardado exitosamente")
                            else:
                                # Si no se encuentra el item, registrar un warning pero no fallar
                                logger.warning(f"No se encontró ItemSeccionOT para seccion_id={seccion_id} en OT {ot.ot_id}")
                                # Listar los items disponibles para debugging
                                available_items = list(items_secciones_ot.values_list('seccion_id__seccion_id', flat=True))
                                logger.warning(f"Items disponibles: {available_items}")
                        except (EstadoOT.DoesNotExist, ValueError, TypeError) as e:
                            # Registrar el error pero continuar con las demás secciones
                            logger.error(f"Error al actualizar estado de sección {seccion_id}: {str(e)}", exc_info=True)
                            # No re-lanzar, continuar con las demás secciones para no fallar toda la operación
                            continue
                        except Exception as e:
                            logger.error(f"Error inesperado al actualizar estado de sección {seccion_id}: {str(e)}", exc_info=True)
                            # No re-lanzar, continuar con las demás secciones para no fallar toda la operación
                            continue
            
            return JsonResponse({
                'success': True,
                'message': 'Orden de trabajo actualizada exitosamente',
                'ot_id': ot.ot_id,
                'folio': ot.folio
            })
        
        # MODO CREACIÓN: Crear una nueva orden de trabajo
        # Paso 11: Validaciones básicas de campos requeridos
        equipo_id = data.get('equipo_id')  # ID del equipo (requerido)
        if not equipo_id:
            return JsonResponse({
                'success': False,
                'message': 'El equipo es requerido'
            }, status=400)
        
        # Paso 12: Obtener el equipo desde la base de datos
        # Si no existe, se retorna un error 404 automáticamente
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Paso 13: Obtener tipo de mantenimiento (requerido)
        tipo_mantenimiento_id = data.get('tipo_mantenimiento_id')  # ID del tipo de mantenimiento
        if not tipo_mantenimiento_id:
            return JsonResponse({
                'success': False,
                'message': 'Tipo de mantenimiento es requerido'
            }, status=400)
        
        tipo_mantenimiento = get_object_or_404(TipoMantenimiento, tipoMantenimiento_id=tipo_mantenimiento_id)
        
        # Paso 14: Establecer estado OT inicial
        # En creación, SIEMPRE usar PENDIENTE para la OT (no se puede crear en otro estado)
        estado_ot = EstadoOT.objects.filter(nombre='Pendiente').first()
        if not estado_ot:
            # Si no existe "Pendiente", usar el primer estado activo disponible
            estado_ot = EstadoOT.objects.filter(activo=True).first()
        
        # Paso 15: Establecer estado de equipo inicial
        estado_equipo_id = data.get('estado_equipo_id')  # ID del estado de equipo (opcional)
        if not estado_equipo_id:
            # Si no se proporciona, usar "Disponible" por defecto
            estado_equipo = EstadoEquipo.objects.filter(nombre='Disponible').first()
            if not estado_equipo:
                # Si no existe "Disponible", usar el primer estado activo disponible
                estado_equipo = EstadoEquipo.objects.filter(activo=True).first()
        else:
            # Si se proporciona estado de equipo, obtenerlo desde la base de datos
            estado_equipo = get_object_or_404(EstadoEquipo, estadoEquipo_id=estado_equipo_id)
        
        # Paso 16: Crear nueva instancia de OrdenTrabajo
        ot = OrdenTrabajo()
        
        # Paso 17: Asignar campos básicos de la orden (solo en creación)
        ot.equipo_id = equipo  # Asignar equipo
        ot.empresa_id = equipo.empresa_id  # Asignar empresa del equipo (automático)
        ot.tipo_mantenimiento_id = tipo_mantenimiento  # Asignar tipo de mantenimiento
        ot.estado_ot_id = estado_ot  # Asignar estado OT inicial (Pendiente)
        ot.estado_equipo_id = estado_equipo  # Asignar estado de equipo inicial
        
        # Paso 18: Copiar campos automáticos del equipo a la orden
        # Estos valores se copian desde el equipo al momento de crear la OT
        ot.horometro = equipo.horometro  # Horas de uso del equipo
        ot.odometro = equipo.odometro  # Kilómetros recorridos del equipo
        ot.horometro_superestructura = equipo.horometroSuperEstructural  # Horas de superestructura
        
        # Paso 19: Asignar fechas de la orden
        fecha_inicio = data.get('fecha_inicio')  # Fecha de inicio (opcional)
        if fecha_inicio:
            ot.fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()  # Convertir string a date
        
        fecha_fin = data.get('fecha_fin')  # Fecha de fin (opcional)
        if fecha_fin:
            ot.fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()  # Convertir string a date
        
        # Paso 20: Configurar pauta de mantenimiento (solo si es preventivo)
        if tipo_mantenimiento.nombre.lower() == 'preventivo':
            # CASO: Mantenimiento Preventivo
            corresponde_pauta = data.get('corresponde_pauta', False)  # Flag que indica si corresponde usar pauta
            ot.corresponde_pauta = corresponde_pauta
            
            if corresponde_pauta:
                # Si corresponde pauta, obtener la pauta seleccionada
                pauta_id = data.get('pauta_id')  # ID de la pauta (opcional)
                if pauta_id:
                    ot.pauta_id = get_object_or_404(PautaMantenimientoPreventivo, pauta_id=pauta_id)
                else:
                    ot.pauta_id = None  # Si no se proporciona pauta, dejar en None
            else:
                ot.pauta_id = None  # Si no corresponde pauta, dejar en None
        else:
            # CASO: Mantenimiento Correctivo u otro tipo
            ot.corresponde_pauta = False  # No corresponde pauta
            ot.pauta_id = None  # No hay pauta asociada
        
        # Paso 21: Asignar observaciones iniciales
        observaciones = data.get('observaciones', '').strip() if data.get('observaciones') else ''  # Observaciones (opcional)
        ot.observaciones = observaciones if observaciones else None  # Guardar solo si hay contenido
        
        # Paso 22: Validar que haya al menos una sección con tipos de reparación antes de guardar
        # Esta validación es obligatoria para todas las OTs
        tiene_secciones_validas = False
        
        if tipo_mantenimiento.nombre.lower() == 'preventivo' and ot.corresponde_pauta and ot.pauta_id:
            # CASO: Preventivo con pauta - validar que la pauta tenga items con tipos de reparación
            items_pauta_temp = ItemPauta.objects.filter(pauta_id=ot.pauta_id).prefetch_related('tipos_reparacion')
            for item_pauta_temp in items_pauta_temp:
                if item_pauta_temp.tipos_reparacion.exists():
                    tiene_secciones_validas = True
                    break
        else:
            # CASO: Preventivo sin pauta o Correctivo - validar items_secciones
            items_secciones_temp = data.get('items_secciones', [])
            for item_temp in items_secciones_temp:
                seccion_id_temp = item_temp.get('seccion_id')
                tipos_reparacion_ids_temp = item_temp.get('tipos_reparacion_ids', [])
                if seccion_id_temp and tipos_reparacion_ids_temp and len(tipos_reparacion_ids_temp) > 0:
                    tiene_secciones_validas = True
                    break
        
        if not tiene_secciones_validas:
            return JsonResponse({
                'success': False,
                'message': 'Debe asignar al menos una sección con al menos un tipo de reparación'
            }, status=400)
        
        # Paso 23: Guardar la orden en la base de datos
        # Esto genera automáticamente el folio y fecha_creacion
        ot.save()
        
        # Paso 24: Registrar creación de la orden en el historial
        # Esto documenta quién creó la orden y cuándo
        HistorialOT.registrar(
            ot=ot,  # Orden de trabajo creada
            accion='OT_CREADA',  # Tipo de acción realizada
            descripcion=f"Orden de Trabajo creada. Equipo: {ot.equipo_id.nombreEquipo}, Tipo: {ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else 'N/A'}",  # Descripción de la creación
            usuario=request.user if request.user.is_authenticated else None,  # Usuario que creó la orden
            datos_nuevos={  # Datos de la nueva orden
                'folio': ot.folio,  # Folio generado automáticamente
                'equipo_id': ot.equipo_id.equipo_id,  # ID del equipo
                'equipo_nombre': ot.equipo_id.nombreEquipo,  # Nombre del equipo
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else None,  # Tipo de mantenimiento
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else None,  # Estado OT inicial
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else None,  # Estado de equipo inicial
            }
        )
        
        # Paso 25: Si hay observaciones iniciales, agregarlas al historial de observaciones
        # Las observaciones se guardan en una tabla separada para mejor organización
        if observaciones:
            HistorialObservacionesOT.objects.create(
                ot_id=ot,  # Orden de trabajo asociada
                observacion=observaciones,  # Texto de la observación
                usuario=request.user if request.user.is_authenticated else None  # Usuario que agregó la observación
            )
        
        # Paso 26: Asignar personal a la orden (relación many-to-many)
        # El personal se asigna después de crear la orden porque requiere que la orden exista
        personal_ids = data.get('personal_asignado', [])  # Lista de IDs de personal
        ot.personal_asignado.set(personal_ids)  # Establecer relación many-to-many
        
        # Paso 27: Registrar asignación de personal en el historial
        # Solo se registra si se asignó personal
        if personal_ids:
            personal_list = Personal.objects.filter(personal_id__in=personal_ids)  # Obtener objetos de personal
            nombres_personal = [f"{p.nombre} {p.apepat}" for p in personal_list]  # Construir lista de nombres
            HistorialOT.registrar(
                ot=ot,  # Orden de trabajo afectada
                accion='PERSONAL_ASIGNADO',  # Tipo de acción realizada
                descripcion=f"Personal asignado: {', '.join(nombres_personal)}",  # Descripción con nombres
                usuario=request.user if request.user.is_authenticated else None,  # Usuario que asignó el personal
                datos_nuevos={'personal_ids': list(personal_ids)}  # IDs del personal asignado
            )
        
        # Si es preventivo con pauta, crear items de secciones desde la pauta
        if tipo_mantenimiento.nombre.lower() == 'preventivo' and ot.corresponde_pauta and ot.pauta_id:
            # Eliminar items existentes
            ItemSeccionOT.objects.filter(ot_id=ot).delete()
            
            # Obtener items de la pauta
            items_pauta = ItemPauta.objects.filter(pauta_id=ot.pauta_id).prefetch_related('tipos_reparacion')
            
            # Obtener estados de pauta desde el formulario (si se enviaron)
            estados_pauta = data.get('estados_pauta', [])
            estados_pauta_dict = {item['seccion_id']: item['estado_seccion_id'] for item in estados_pauta if item.get('estado_seccion_id')}
            
            # Obtener estado por defecto (Pendiente)
            estado_pendiente = EstadoOT.objects.filter(nombre='Pendiente').first()
            if not estado_pendiente:
                estado_pendiente = EstadoOT.objects.filter(activo=True).first()
            
            # Crear items de secciones desde la pauta
            # En creación, SIEMPRE usar PENDIENTE para las secciones
            for item_pauta in items_pauta:
                # Siempre usar PENDIENTE en creación, ignorar estados del formulario
                estado_seccion = estado_pendiente
                
                item_seccion = ItemSeccionOT.objects.create(
                    ot_id=ot,
                    seccion_id=item_pauta.seccion_id,
                    estado_seccion_id=estado_seccion
                )
                item_seccion.tipos_reparacion.set(item_pauta.tipos_reparacion.all())
            
            # Actualizar estados de las secciones en la pauta si se enviaron
            # NOTA: Los estados se guardan en ItemSeccionOT, no en ItemPauta
            # En creación, los estados siempre se establecen como PENDIENTE, así que no hay nada que actualizar aquí
            # Esta sección se mantiene por compatibilidad pero no hace nada en creación
        
        # Si NO es pauta o es correctivo, guardar items de secciones manuales
        elif (tipo_mantenimiento.nombre.lower() == 'preventivo' and not ot.corresponde_pauta) or tipo_mantenimiento.nombre.lower() == 'correctivo':
            items_secciones = data.get('items_secciones', [])
            # Eliminar items existentes
            ItemSeccionOT.objects.filter(ot_id=ot).delete()
            
            # Obtener estado por defecto (Pendiente)
            estado_pendiente = EstadoOT.objects.filter(nombre='Pendiente').first()
            if not estado_pendiente:
                estado_pendiente = EstadoOT.objects.filter(activo=True).first()
            
            # Crear nuevos items
            for item in items_secciones:
                seccion_id = item.get('seccion_id')
                tipos_reparacion_ids = item.get('tipos_reparacion_ids', [])
                estado_seccion_id = item.get('estado_seccion_id')
                
                if seccion_id and tipos_reparacion_ids:
                    estado_seccion = None
                    # En creación, siempre usar PENDIENTE por defecto para las secciones
                    if estado_seccion_id:
                        try:
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                        except EstadoOT.DoesNotExist:
                            estado_seccion = estado_pendiente
                    else:
                        # Siempre PENDIENTE en creación
                        estado_seccion = estado_pendiente
                    
                    item_seccion = ItemSeccionOT.objects.create(
                        ot_id=ot,
                        seccion_id_id=seccion_id,
                        estado_seccion_id=estado_seccion
                    )
                    item_seccion.tipos_reparacion.set(tipos_reparacion_ids)
        
        return JsonResponse({
            'success': True,
            'message': 'Orden de trabajo guardada exitosamente',
            'ot_id': ot.ot_id,
            'folio': ot.folio
        })
        
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_traceback = traceback.format_exc()
        logger.error(f"Error en api_guardar_orden_trabajo: {str(e)}\n{error_traceback}")
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar orden de trabajo: {str(e)}',
            'error_detail': str(e) if hasattr(e, '__str__') else repr(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
@permission_required_custom('maquinarias.agregar_observacion_ot', is_ajax=True)
def api_agregar_observacion_ot(request, ot_id):
    """
    API para agregar una observación al historial de una orden de trabajo.
    
    Esta función permite agregar una observación (comentario) a una orden de trabajo.
    La observación se guarda en HistorialObservacionesOT y también se registra en HistorialOT
    para mantener un registro completo de todas las acciones realizadas.
    
    Parámetros:
        ot_id: ID de la orden de trabajo a la que se agregará la observación
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.agregar_observacion_ot'
        - Método HTTP POST
        - Datos JSON en el cuerpo de la petición con campo 'observacion'
    
    Retorna:
        JSON con éxito o error según el resultado de la operación
    """
    try:
        # Paso 1: Obtener la orden de trabajo desde la base de datos
        # Si no existe, se retorna un error 404 automáticamente
        ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
        
        # Paso 2: Parsear los datos JSON recibidos en el cuerpo de la petición
        data = json.loads(request.body)
        
        # Paso 3: Obtener y validar la observación
        observacion = data.get('observacion', '').strip()  # Texto de la observación (sin espacios al inicio/final)
        if not observacion:
            return JsonResponse({
                'success': False,
                'message': 'La observación es requerida'
            }, status=400)
        
        # Paso 4: Crear registro en HistorialObservacionesOT
        # Esta tabla almacena todas las observaciones de la orden
        historial = HistorialObservacionesOT.objects.create(
            ot_id=ot,  # Orden de trabajo asociada
            observacion=observacion,  # Texto de la observación
            usuario=request.user if request.user.is_authenticated else None  # Usuario que agregó la observación
        )
        
        # Paso 5: Registrar la acción en el historial de cambios de la OT
        # Esto mantiene un registro completo de todas las acciones realizadas
        HistorialOT.registrar(
            ot=ot,  # Orden de trabajo afectada
            accion='OBSERVACION_AGREGADA',  # Tipo de acción realizada
            descripcion=f"Observación agregada: {observacion[:100]}...",  # Descripción (primeros 100 caracteres)
            usuario=request.user if request.user.is_authenticated else None,  # Usuario que realizó la acción
            datos_nuevos={'observacion': observacion}  # Texto completo de la observación
        )
        
        # Paso 6: Retornar respuesta de éxito con los datos de la observación creada
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'message': 'Observación agregada exitosamente',  # Mensaje descriptivo
            'historial': {
                'historial_id': historial.historial_id,  # ID único del registro de historial
                'observacion': historial.observacion,  # Texto de la observación
                'usuario': historial.usuario.username if historial.usuario else None,  # Usuario que agregó la observación
                'fecha': historial.fecha.strftime('%Y-%m-%d %H:%M:%S')  # Fecha y hora formateadas
            }
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar observación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_ot(request, ot_id):
    """
    API para obtener detalles completos de una orden de trabajo.
    
    Esta función retorna información completa de una orden de trabajo específica, incluyendo:
    - Información básica de la orden (folio, fechas, estados)
    - Información del equipo asociado
    - Personal asignado con sus cargos
    - Secciones y tipos de reparación (de pauta o manuales)
    - Historial de observaciones
    - Historial de cambios
    
    Parámetros:
        ot_id: ID de la orden de trabajo cuyo detalle se va a obtener
    
    Requisitos:
        - Método HTTP GET
    
    Retorna:
        JSON con información completa de la orden de trabajo
    """
    try:
        # Paso 1: Obtener la orden de trabajo con todas sus relaciones optimizadas
        # select_related evita consultas N+1 al traer todas las relaciones en una sola consulta SQL
        # prefetch_related optimiza la carga de relaciones many-to-many y reverse foreign keys
        ot = get_object_or_404(OrdenTrabajo.objects.select_related(
            'equipo_id',  # Traer datos del equipo
            'equipo_id__modeloEquipo_id',  # Traer modelo a través del equipo
            'equipo_id__modeloEquipo_id__tipoEquipo_id',  # Traer tipo a través del modelo
            'equipo_id__modeloEquipo_id__marcaEquipo_id',  # Traer marca a través del modelo
            'empresa_id',  # Traer datos de la empresa
            'pauta_id',  # Traer datos de la pauta (si existe)
            'tipo_mantenimiento_id',  # Traer datos del tipo de mantenimiento
            'estado_ot_id',  # Traer datos del estado OT
            'estado_equipo_id'  # Traer datos del estado de equipo
        ).prefetch_related('personal_asignado', 'items_secciones__seccion_id', 'items_secciones__tipos_reparacion', 'items_secciones__estado_seccion_id'), ot_id=ot_id)
        
        # Paso 2: Serializar personal asignado a la orden
        # Obtener información completa de cada persona asignada incluyendo su cargo
        personal_asignado = []
        for p in ot.personal_asignado.all():
            # Obtener información laboral del personal para obtener su cargo
            info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
            cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
            personal_asignado.append({
                'personal_id': p.personal_id,  # ID único del personal
                'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",  # Nombre completo
                'rut': f"{p.rut}-{p.dvrut}",  # RUT completo con dígito verificador
                'cargo': cargo_nombre  # Nombre del cargo
            })
        
        # Paso 3: Serializar secciones de la pauta (si la orden usa pauta)
        # Las secciones vienen de la pauta pero los estados se guardan en ItemSeccionOT
        secciones_pauta = []
        if ot.corresponde_pauta and ot.pauta_id:
            # Obtener items de la pauta con sus relaciones optimizadas
            items_pauta = ItemPauta.objects.filter(pauta_id=ot.pauta_id).select_related('seccion_id').prefetch_related('tipos_reparacion')
            for item in items_pauta:
                # Buscar el estado actual en ItemSeccionOT si existe
                # El estado se guarda en ItemSeccionOT, no en ItemPauta
                item_seccion_ot = ItemSeccionOT.objects.filter(ot_id=ot, seccion_id=item.seccion_id).select_related('estado_seccion_id').first()
                estado_actual = item_seccion_ot.estado_seccion_id if item_seccion_ot and item_seccion_ot.estado_seccion_id else None
                
                secciones_pauta.append({
                    'seccion_id': item.seccion_id.seccion_id,  # ID de la sección
                    'seccion_nombre': item.seccion_id.nombre,  # Nombre de la sección
                    'tipos_reparacion': [tr.nombre for tr in item.tipos_reparacion.all()],  # Lista de nombres de tipos de reparación
                    'estado_seccion': estado_actual.nombre if estado_actual else 'Pendiente',  # Nombre del estado actual
                    'estado_seccion_id': estado_actual.estadoOT_id if estado_actual else None,  # ID del estado actual
                    'estado_seccion_color': estado_actual.color if estado_actual else 'secondary'  # Color del estado actual
                })
        
        # Paso 4: Serializar secciones manuales (si la orden NO usa pauta o es correctivo)
        # Estas secciones fueron agregadas manualmente al crear la orden
        secciones_manuales = []
        if not ot.corresponde_pauta or not ot.pauta_id:
            # Obtener items de secciones con sus relaciones optimizadas
            items_secciones = ItemSeccionOT.objects.filter(ot_id=ot).select_related('seccion_id', 'estado_seccion_id').prefetch_related('tipos_reparacion')
            for item in items_secciones:
                secciones_manuales.append({
                    'seccion_id': item.seccion_id.seccion_id,  # ID de la sección
                    'seccion_nombre': item.seccion_id.nombre,  # Nombre de la sección
                    'tipos_reparacion': [tr.nombre for tr in item.tipos_reparacion.all()],  # Lista de nombres de tipos de reparación
                    'estado_seccion': item.estado_seccion_id.nombre if item.estado_seccion_id else 'Pendiente',  # Nombre del estado actual
                    'estado_seccion_id': item.estado_seccion_id.estadoOT_id if item.estado_seccion_id else None,  # ID del estado actual
                    'estado_seccion_color': item.estado_seccion_id.color if item.estado_seccion_id else 'secondary'  # Color del estado actual
                })
        
        # Paso 5: Serializar historial de observaciones
        # Las observaciones se ordenan por fecha descendente (más recientes primero)
        historial_observaciones = []
        for obs in HistorialObservacionesOT.objects.filter(ot_id=ot).select_related('usuario').order_by('-fecha'):
            historial_observaciones.append({
                'fecha': obs.fecha.strftime('%Y-%m-%d %H:%M:%S'),  # Fecha y hora formateadas
                'usuario': obs.usuario.username if obs.usuario else 'Sistema',  # Usuario que agregó la observación
                'observacion': obs.observacion  # Texto de la observación
            })
        
        # Paso 6: Serializar historial de cambios
        # Los cambios se ordenan por fecha descendente (más recientes primero)
        historial_cambios = []
        for cambio in HistorialOT.objects.filter(ot=ot).select_related('usuario').order_by('-fecha_hora'):
            historial_cambios.append({
                'fecha_hora': cambio.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),  # Fecha y hora formateadas
                'usuario': cambio.usuario.username if cambio.usuario else 'Sistema',  # Usuario que realizó el cambio
                'accion': cambio.get_accion_display(),  # Nombre legible de la acción
                'descripcion': cambio.descripcion  # Descripción detallada del cambio
            })
        
        # Paso 7: Retornar respuesta JSON con información completa de la orden
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'ot': {
                'ot_id': ot.ot_id,  # ID único de la orden
                'folio': ot.folio,  # Folio de la orden
                'equipo': {
                    'equipo_id': ot.equipo_id.equipo_id,  # ID del equipo
                    'nombreEquipo': ot.equipo_id.nombreEquipo,  # Nombre del equipo
                    'codigoInterno': ot.equipo_id.codigoInterno,  # Código interno del equipo
                    'tipoEquipo': ot.equipo_id.modeloEquipo_id.tipoEquipo_id.tipoEquipo if ot.equipo_id.modeloEquipo_id.tipoEquipo_id else '',  # Tipo de equipo
                    'marcaEquipo': ot.equipo_id.modeloEquipo_id.marcaEquipo_id.marcaEquipo if ot.equipo_id.modeloEquipo_id.marcaEquipo_id else '',  # Marca del equipo
                    'modeloEquipo': ot.equipo_id.modeloEquipo_id.modeloEquipo if ot.equipo_id.modeloEquipo_id else '',  # Modelo del equipo
                },
                'empresa': {
                    'empresa_id': ot.empresa_id.id if hasattr(ot.empresa_id, 'id') else None,  # ID de la empresa
                    'nomFantasia': ot.empresa_id.nomFantasia,  # Nombre de la empresa
                },
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else '',  # Tipo de mantenimiento
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else '',  # Estado OT
                'estado_ot_color': ot.estado_ot_id.color if ot.estado_ot_id else 'secondary',  # Color del estado OT
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else '',  # Estado de equipo
                'estado_equipo_color': ot.estado_equipo_id.color if ot.estado_equipo_id else 'secondary',  # Color del estado de equipo
                'fecha_creacion': ot.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if ot.fecha_creacion else None,  # Fecha de creación formateada
                'fecha_inicio': ot.fecha_inicio.strftime('%Y-%m-%d') if ot.fecha_inicio else None,  # Fecha de inicio formateada
                'fecha_fin': ot.fecha_fin.strftime('%Y-%m-%d') if ot.fecha_fin else None,  # Fecha de fin formateada
                'horometro': ot.horometro,  # Horas de uso del equipo
                'odometro': ot.odometro,  # Kilómetros recorridos del equipo
                'horometro_superestructura': ot.horometro_superestructura,  # Horas de superestructura
                'corresponde_pauta': ot.corresponde_pauta,  # Flag que indica si corresponde usar pauta
                'pauta_nombre': ot.pauta_id.nombre if ot.pauta_id else None,  # Nombre de la pauta (si existe)
                'observaciones': ot.observaciones,  # Observaciones generales de la orden
                'personal_asignado': personal_asignado,  # Lista de personal asignado
                'secciones_pauta': secciones_pauta,  # Lista de secciones de la pauta (si usa pauta)
                'secciones_manuales': secciones_manuales,  # Lista de secciones manuales (si no usa pauta)
                'historial_observaciones': historial_observaciones,  # Historial de observaciones
                'historial_cambios': historial_cambios  # Historial de cambios
            }
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de OT: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
@permission_required_custom('maquinarias.ver_historial_ot', is_ajax=True)
def api_historial_ot(request, ot_id):
    """
    API para obtener el historial completo de una orden de trabajo en formato JSON.
    
    Esta función retorna todos los cambios registrados en el historial de una orden de trabajo,
    incluyendo información detallada de cada cambio: fecha, usuario, acción, descripción y datos
    previos/nuevos. Para acciones relacionadas con personal, también incluye información completa
    del personal involucrado.
    
    Parámetros:
        ot_id: ID de la orden de trabajo cuyo historial se va a obtener
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.ver_historial_ot'
        - Método HTTP GET
    
    Retorna:
        JSON con lista completa de cambios en el historial ordenados por fecha descendente
    """
    try:
        # Paso 1: Obtener la orden de trabajo desde la base de datos
        # Si no existe, se retorna un error 404 automáticamente
        ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
        
        # Paso 2: Obtener todos los cambios del historial ordenados por fecha descendente
        # select_related optimiza la carga del usuario en cada cambio
        historial_data = []
        for cambio in HistorialOT.objects.filter(ot=ot).select_related('usuario').order_by('-fecha_hora'):
            # Paso 2.1: Obtener información de personal desde datos_nuevos si existe
            # Esto se hace solo para acciones relacionadas con personal (PERSONAL_ASIGNADO, PERSONAL_ELIMINADO)
            personal_info = None
            if cambio.accion in ['PERSONAL_ASIGNADO', 'PERSONAL_ELIMINADO'] and cambio.datos_nuevos:
                personal_ids = cambio.datos_nuevos.get('personal_ids', [])  # Obtener IDs de personal
                if personal_ids:
                    try:
                        # Obtener objetos de personal para obtener información completa
                        personal_list = Personal.objects.filter(personal_id__in=personal_ids)
                        if personal_list.exists():
                            personal_info = [{
                                'personal_id': p.personal_id,  # ID único del personal
                                'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",  # Nombre completo
                                'rut': f"{p.rut}-{p.dvrut}"  # RUT completo con dígito verificador
                            } for p in personal_list]
                    except Exception:
                        # Si hay error al obtener personal, simplemente no incluir información
                        pass
            
            # Paso 2.2: Agregar datos del cambio al historial
            historial_data.append({
                'fecha_hora': cambio.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),  # Fecha y hora en formato ISO
                'fecha_hora_formateada': cambio.fecha_hora.strftime('%d/%m/%Y %H:%M'),  # Fecha y hora formateada para mostrar
                'usuario': cambio.usuario.username if cambio.usuario else 'Sistema',  # Username del usuario
                'usuario_nombre': obtener_nombre_completo_usuario(cambio.usuario) if cambio.usuario else 'Sistema',  # Nombre completo del usuario
                'accion': cambio.accion,  # Código de la acción (ej: 'ESTADO_OT_CAMBIADO')
                'accion_display': cambio.get_accion_display(),  # Nombre legible de la acción (ej: 'Estado OT Cambiado')
                'descripcion': cambio.descripcion,  # Descripción detallada del cambio
                'personal': personal_info,  # Información del personal (solo para acciones relacionadas)
                'datos_previos': cambio.datos_previos,  # Datos anteriores (JSON)
                'datos_nuevos': cambio.datos_nuevos  # Datos nuevos (JSON)
            })
        
        # Paso 3: Retornar respuesta JSON con el historial completo
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'historial': historial_data,  # Lista de cambios en el historial
            'total': len(historial_data)  # Total de cambios registrados
        })
        
    except OrdenTrabajo.DoesNotExist:
        # CASO ERROR: La orden de trabajo no existe en la base de datos
        # Retornar error 404 (Not Found) con mensaje descriptivo
        return JsonResponse({
            'success': False,
            'message': 'Orden de trabajo no encontrada'
        }, status=404)
    
    except Exception as e:
        # CASO EXCEPCIÓN: Cualquier otro error no previsto
        # Retornar error 500 (Internal Server Error) con el mensaje de la excepción
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener historial: {str(e)}'
        }, status=500)


@login_required
@permission_required_custom('maquinarias.generar_pdf_ot')
def generar_pdf_ot(request, ot_id):
    """
    Vista para generar un PDF de una orden de trabajo.
    
    Esta función genera un documento PDF completo con toda la información de una orden de trabajo,
    incluyendo datos del equipo, personal asignado, secciones, tipos de reparación, estados y observaciones.
    El PDF se genera usando la librería reportlab y se retorna como respuesta HTTP para descarga o visualización.
    
    Parámetros:
        ot_id: ID de la orden de trabajo cuyo PDF se va a generar
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.generar_pdf_ot'
        - Librería reportlab instalada
    
    Retorna:
        HttpResponse con contenido PDF o redirección con mensaje de error
    """
    # Paso 1: Verificar que la librería reportlab está disponible
    # Si no está instalada, mostrar mensaje de error y redirigir
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'La librería reportlab no está instalada. Por favor, instálela con: pip install reportlab')
        return redirect('maquinarias:lista_ordenes_trabajo')
    
    try:
        # Paso 2: Obtener la orden de trabajo con todas las relaciones necesarias optimizadas
        # select_related evita consultas N+1 al traer todas las relaciones en una sola consulta SQL
        # prefetch_related optimiza la carga de relaciones many-to-many y reverse foreign keys
        ot = get_object_or_404(
            OrdenTrabajo.objects.select_related(
                'equipo_id',  # Traer datos del equipo
                'equipo_id__modeloEquipo_id',  # Traer modelo a través del equipo
                'equipo_id__modeloEquipo_id__tipoEquipo_id',  # Traer tipo a través del modelo
                'equipo_id__modeloEquipo_id__marcaEquipo_id',  # Traer marca a través del modelo
                'empresa_id',  # Traer datos de la empresa
                'pauta_id',  # Traer datos de la pauta (si existe)
                'tipo_mantenimiento_id',  # Traer datos del tipo de mantenimiento
                'estado_ot_id',  # Traer datos del estado OT
                'estado_equipo_id'  # Traer datos del estado de equipo
            ).prefetch_related(
                'personal_asignado',  # Cargar personal asignado de forma optimizada
                'items_secciones__seccion_id',  # Cargar secciones de items optimizadas
                'items_secciones__tipos_reparacion',  # Cargar tipos de reparación optimizados
                'items_secciones__estado_seccion_id'  # Cargar estados de secciones optimizados
            ),
            ot_id=ot_id
        )
        
        # Paso 3: Crear respuesta HTTP con tipo de contenido PDF
        # El PDF se puede visualizar en el navegador o descargar
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="OT_{ot.folio}.pdf"'  # Nombre del archivo PDF
        
        # Paso 4: Crear el documento PDF con márgenes configurados
        # Los márgenes más pequeños permiten más espacio para el contenido
        doc = SimpleDocTemplate(response, pagesize=A4, 
                              rightMargin=1.5*cm, leftMargin=1.5*cm,  # Márgenes laterales
                              topMargin=1.5*cm, bottomMargin=1.5*cm)  # Márgenes superior e inferior
        
        # Paso 5: Inicializar contenedor para los elementos del PDF
        # Los elementos se agregan en orden y se renderizan al construir el PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#212529'),
            spaceAfter=8,
            spaceBefore=5,
            alignment=1  # Centrado
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#212529'),
            spaceAfter=4,
            spaceBefore=6,
            fontName='Helvetica-Bold',
            alignment=0,  # LEFT alignment
            leftIndent=0,  # Sin indentación, comienza desde el borde
            rightIndent=0,
            firstLineIndent=0
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            leading=9
        )
        
        label_style = ParagraphStyle(
            'CustomLabel',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=9
        )
        
        label_style_white = ParagraphStyle(
            'CustomLabelWhite',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            leading=9
        )
        
        # Logo (si existe)
        logo_path = None
        # Buscar el logo en diferentes ubicaciones posibles
        base_dir = str(settings.BASE_DIR)
        
        # Ruta principal: main_home/static/img/logoGruas.png
        ruta_principal = os.path.join(base_dir, 'main_home', 'static', 'img', 'logoGruas.png')
        ruta_principal_abs = os.path.abspath(ruta_principal)
        
        if os.path.exists(ruta_principal_abs) and os.path.isfile(ruta_principal_abs):
            logo_path = ruta_principal_abs
        else:
            # Rutas alternativas
            posibles_rutas = [
                os.path.join(base_dir, 'static', 'img', 'logoGruas.png'),
            ]
            
            if settings.STATICFILES_DIRS:
                for static_dir in settings.STATICFILES_DIRS:
                    static_dir_str = str(static_dir) if not isinstance(static_dir, str) else static_dir
                    posibles_rutas.append(os.path.join(static_dir_str, 'img', 'logoGruas.png'))
                    posibles_rutas.append(os.path.join(static_dir_str, 'main_home', 'static', 'img', 'logoGruas.png'))
            
            if settings.STATIC_ROOT:
                static_root_str = str(settings.STATIC_ROOT) if not isinstance(settings.STATIC_ROOT, str) else settings.STATIC_ROOT
                posibles_rutas.append(os.path.join(static_root_str, 'img', 'logoGruas.png'))
            
            # Buscar la primera ruta que exista
            for ruta in posibles_rutas:
                ruta_normalizada = os.path.normpath(ruta)
                ruta_absoluta = os.path.abspath(ruta_normalizada)
                if os.path.exists(ruta_absoluta) and os.path.isfile(ruta_absoluta):
                    logo_path = ruta_absoluta
                    break
        
        # Crear tabla con logo y título
        header_data = []
        if logo_path and os.path.exists(logo_path) and os.path.isfile(logo_path):
            try:
                # Obtener dimensiones originales de la imagen para mantener proporción
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(logo_path) as img:
                        img_width, img_height = img.size
                        # Calcular tamaño manteniendo proporción (ancho máximo 3.5cm)
                        max_width = 3.5 * cm
                        aspect_ratio = img_height / img_width
                        logo_width = max_width
                        logo_height = max_width * aspect_ratio
                except ImportError:
                    # Si PIL no está disponible, usar tamaño por defecto
                    logo_width = 3.5 * cm
                    logo_height = None
                except Exception:
                    # Si hay error leyendo la imagen, usar tamaño por defecto
                    logo_width = 3.5 * cm
                    logo_height = None
                
                # Crear imagen con dimensiones calculadas
                if logo_height:
                    logo = Image(logo_path, width=logo_width, height=logo_height)
                else:
                    logo = Image(logo_path, width=logo_width)
                
                # Logo arriba a la izquierda, título abajo centrado
                header_data = [
                    [logo],  # Primera fila: logo a la izquierda
                    [Paragraph(f"<b>ORDEN DE TRABAJO N° {ot.folio}</b>", title_style)]  # Segunda fila: título centrado
                ]
                header_table = Table(header_data, colWidths=[16*cm])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Logo a la izquierda
                    ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Título centrado
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (0, 0), 3),  # Padding inferior en logo
                    ('TOPPADDING', (0, 0), (0, 0), 0),  # Sin padding superior en logo
                    ('BOTTOMPADDING', (0, 1), (0, 1), 3),  # Padding inferior en título
                    ('TOPPADDING', (0, 1), (0, 1), 3),  # Padding superior en título
                ]))
                elements.append(header_table)
            except Exception as e:
                # Si hay error con el logo, solo mostrar título
                # En producción, podrías loggear el error: import logging; logging.error(f"Error cargando logo: {e}")
                elements.append(Paragraph(f"<b>ORDEN DE TRABAJO N° {ot.folio}</b>", title_style))
        else:
            elements.append(Paragraph(f"<b>ORDEN DE TRABAJO N° {ot.folio}</b>", title_style))
        
        elements.append(Spacer(1, 0.2*cm))
        
        # Información de la empresa
        empresa_data = [
            [Paragraph('<b>Empresa:</b>', label_style), Paragraph(ot.empresa_id.nomFantasia, normal_style)],
            [Paragraph('<b>RUT:</b>', label_style), Paragraph(f"{ot.empresa_id.rut}-{ot.empresa_id.dv}", normal_style)],
            [Paragraph('<b>Dirección:</b>', label_style), Paragraph(ot.empresa_id.direccion, normal_style)],
        ]
        empresa_table = Table(empresa_data, colWidths=[3.5*cm, 12.5*cm])
        empresa_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(empresa_table)
        elements.append(Spacer(1, 0.2*cm))
        
        # Información del equipo
        # Crear título como tabla para alinearlo con el borde de las tablas
        titulo_equipo_data = [[Paragraph("INFORMACIÓN DEL EQUIPO", heading_style)]]
        titulo_equipo_table = Table(titulo_equipo_data, colWidths=[16*cm])
        titulo_equipo_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(titulo_equipo_table)
        equipo_data = [
            [Paragraph('<b>Equipo:</b>', label_style), Paragraph(ot.equipo_id.nombreEquipo, normal_style)],
            [Paragraph('<b>Código Interno:</b>', label_style), Paragraph(ot.equipo_id.codigoInterno or 'N/A', normal_style)],
            [Paragraph('<b>Tipo:</b>', label_style), Paragraph(ot.equipo_id.modeloEquipo_id.tipoEquipo_id.tipoEquipo if ot.equipo_id.modeloEquipo_id and ot.equipo_id.modeloEquipo_id.tipoEquipo_id else 'N/A', normal_style)],
            [Paragraph('<b>Marca:</b>', label_style), Paragraph(ot.equipo_id.modeloEquipo_id.marcaEquipo_id.marcaEquipo if ot.equipo_id.modeloEquipo_id and ot.equipo_id.modeloEquipo_id.marcaEquipo_id else 'N/A', normal_style)],
            [Paragraph('<b>Modelo:</b>', label_style), Paragraph(ot.equipo_id.modeloEquipo_id.modeloEquipo if ot.equipo_id.modeloEquipo_id else 'N/A', normal_style)],
            [Paragraph('<b>Horómetro:</b>', label_style), Paragraph(str(ot.horometro) if ot.horometro else 'N/A', normal_style)],
            [Paragraph('<b>Odómetro:</b>', label_style), Paragraph(str(ot.odometro) if ot.odometro else 'N/A', normal_style)],
            [Paragraph('<b>Horómetro Superestructura:</b>', label_style), Paragraph(str(ot.horometro_superestructura) if ot.horometro_superestructura else 'N/A', normal_style)],
        ]
        equipo_table = Table(equipo_data, colWidths=[5*cm, 11*cm])
        equipo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(equipo_table)
        elements.append(Spacer(1, 0.2*cm))
        
        # Información de la OT
        # Crear título como tabla para alinearlo con el borde de las tablas
        titulo_ot_data = [[Paragraph("INFORMACIÓN DE LA ORDEN DE TRABAJO", heading_style)]]
        titulo_ot_table = Table(titulo_ot_data, colWidths=[16*cm])
        titulo_ot_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(titulo_ot_table)
        ot_data = [
            [Paragraph('<b>Folio:</b>', label_style), Paragraph(ot.folio, normal_style)],
            [Paragraph('<b>Tipo de Mantenimiento:</b>', label_style), Paragraph(ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else 'N/A', normal_style)],
            [Paragraph('<b>Estado OT:</b>', label_style), Paragraph(ot.estado_ot_id.nombre if ot.estado_ot_id else 'N/A', normal_style)],
            [Paragraph('<b>Estado Equipo:</b>', label_style), Paragraph(ot.estado_equipo_id.nombre if ot.estado_equipo_id else 'N/A', normal_style)],
            [Paragraph('<b>Fecha de Creación:</b>', label_style), Paragraph(ot.fecha_creacion.strftime('%d/%m/%Y %H:%M') if ot.fecha_creacion else 'N/A', normal_style)],
            [Paragraph('<b>Fecha de Inicio:</b>', label_style), Paragraph(ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'N/A', normal_style)],
            [Paragraph('<b>Fecha de Fin:</b>', label_style), Paragraph(ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'N/A', normal_style)],
        ]
        if ot.corresponde_pauta and ot.pauta_id:
            ot_data.append([Paragraph('<b>Pauta de Mantenimiento:</b>', label_style), Paragraph(ot.pauta_id.nombre, normal_style)])
        
        ot_table = Table(ot_data, colWidths=[5*cm, 11*cm])
        ot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(ot_table)
        elements.append(Spacer(1, 0.2*cm))
        
        # Personal asignado
        personal_asignado = ot.personal_asignado.all()
        if personal_asignado:
            # Crear título como tabla para alinearlo con el borde de las tablas
            titulo_personal_data = [[Paragraph("PERSONAL ASIGNADO", heading_style)]]
            titulo_personal_table = Table(titulo_personal_data, colWidths=[16*cm])
            titulo_personal_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(titulo_personal_table)
            personal_headers = [[Paragraph('<b>Nombre Completo</b>', label_style_white), Paragraph('<b>RUT</b>', label_style_white), Paragraph('<b>Cargo</b>', label_style_white)]]
            personal_rows = []
            for p in personal_asignado:
                info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
                cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
                personal_rows.append([
                    Paragraph(f"{p.nombre} {p.apepat} {p.apemat}", normal_style),
                    Paragraph(f"{p.rut}-{p.dvrut}", normal_style),
                    Paragraph(cargo_nombre, normal_style)
                ])
            
            personal_table_data = personal_headers + personal_rows
            personal_table = Table(personal_table_data, colWidths=[7*cm, 4*cm, 5*cm])
            personal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            elements.append(personal_table)
            elements.append(Spacer(1, 0.2*cm))
        
        # Secciones y tipos de reparación
        if ot.corresponde_pauta and ot.pauta_id:
            # Secciones de pauta
            # Crear título como tabla para alinearlo con el borde de las tablas
            titulo_secciones_data = [[Paragraph("SECCIONES Y TIPOS DE REPARACIÓN", heading_style)]]
            titulo_secciones_table = Table(titulo_secciones_data, colWidths=[16*cm])
            titulo_secciones_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(titulo_secciones_table)
            items_pauta = ItemPauta.objects.filter(pauta_id=ot.pauta_id).select_related('seccion_id').prefetch_related('tipos_reparacion')
            secciones_headers = [[Paragraph('<b>Sección</b>', label_style_white), Paragraph('<b>Tipos de Reparación</b>', label_style_white), Paragraph('<b>Estado</b>', label_style_white)]]
            secciones_rows = []
            for item in items_pauta:
                item_seccion_ot = ItemSeccionOT.objects.filter(ot_id=ot, seccion_id=item.seccion_id).first()
                estado_actual = item_seccion_ot.estado_seccion_id.nombre if item_seccion_ot and item_seccion_ot.estado_seccion_id else 'Pendiente'
                tipos_reparacion_list = [tr.nombre for tr in item.tipos_reparacion.all()]
                if tipos_reparacion_list:
                    tipos_reparacion_html = '<br/>'.join([f'• {tr}' for tr in tipos_reparacion_list])
                else:
                    tipos_reparacion_html = 'N/A'
                secciones_rows.append([
                    Paragraph(item.seccion_id.nombre, normal_style),
                    Paragraph(tipos_reparacion_html, normal_style),
                    Paragraph(estado_actual, normal_style)
                ])
            
            if secciones_rows:
                secciones_table_data = secciones_headers + secciones_rows
                secciones_table = Table(secciones_table_data, colWidths=[4.5*cm, 9*cm, 2.5*cm])
                secciones_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                    ('TOPPADDING', (0, 0), (-1, 0), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                    ('TOPPADDING', (0, 1), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                elements.append(secciones_table)
                elements.append(Spacer(1, 0.2*cm))
        else:
            # Secciones manuales
            items_secciones = ItemSeccionOT.objects.filter(ot_id=ot).select_related('seccion_id', 'estado_seccion_id').prefetch_related('tipos_reparacion')
            if items_secciones.exists():
                # Crear título como tabla para alinearlo con el borde de las tablas
                titulo_secciones_data = [[Paragraph("SECCIONES Y TIPOS DE REPARACIÓN", heading_style)]]
                titulo_secciones_table = Table(titulo_secciones_data, colWidths=[16*cm])
                titulo_secciones_table.setStyle(TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(titulo_secciones_table)
                secciones_headers = [[Paragraph('<b>Sección</b>', label_style_white), Paragraph('<b>Tipos de Reparación</b>', label_style_white), Paragraph('<b>Estado</b>', label_style_white)]]
                secciones_rows = []
                for item in items_secciones:
                    tipos_reparacion_list = [tr.nombre for tr in item.tipos_reparacion.all()]
                    if tipos_reparacion_list:
                        tipos_reparacion_html = '<br/>'.join([f'• {tr}' for tr in tipos_reparacion_list])
                    else:
                        tipos_reparacion_html = 'N/A'
                    estado_actual = item.estado_seccion_id.nombre if item.estado_seccion_id else 'Pendiente'
                    secciones_rows.append([
                        Paragraph(item.seccion_id.nombre, normal_style),
                        Paragraph(tipos_reparacion_html, normal_style),
                        Paragraph(estado_actual, normal_style)
                    ])
                
                secciones_table_data = secciones_headers + secciones_rows
                secciones_table = Table(secciones_table_data, colWidths=[4.5*cm, 9*cm, 2.5*cm])
                secciones_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                    ('TOPPADDING', (0, 0), (-1, 0), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                    ('TOPPADDING', (0, 1), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                elements.append(secciones_table)
                elements.append(Spacer(1, 0.2*cm))
        
        # Observaciones
        if ot.observaciones:
            # Crear título como tabla para alinearlo con el borde de las tablas
            titulo_observaciones_data = [[Paragraph("OBSERVACIONES", heading_style)]]
            titulo_observaciones_table = Table(titulo_observaciones_data, colWidths=[16*cm])
            titulo_observaciones_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Sin padding, desde el borde de la tabla
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(titulo_observaciones_table)
            observaciones_para = Paragraph(ot.observaciones.replace('\n', '<br/>'), normal_style)
            elements.append(observaciones_para)
            elements.append(Spacer(1, 0.2*cm))
        
        # Construir el PDF
        doc.build(elements)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('maquinarias:lista_ordenes_trabajo')


# ============================================================================
# APIs PARA HISTORIAL DE EQUIPOS
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@permission_required_custom('maquinarias.ver_historial_equipo', is_ajax=True)
def api_historial_equipo(request, equipo_id):
    """
    API para obtener el historial completo de un equipo en formato JSON.
    
    Esta función retorna todos los cambios registrados en el historial de un equipo,
    incluyendo información detallada de cada cambio: fecha, usuario, acción, descripción
    y datos previos/nuevos. El historial se genera automáticamente mediante signals cuando
    se modifican los datos del equipo.
    
    Parámetros:
        equipo_id: ID del equipo cuyo historial se va a obtener
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.ver_historial_equipo'
        - Método HTTP GET
    
    Retorna:
        JSON con lista completa de cambios en el historial ordenados por fecha descendente
    """
    try:
        # Paso 1: Obtener el equipo desde la base de datos
        # Si no existe, se retorna un error 404 automáticamente
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Paso 2: Obtener todos los eventos del historial ordenados por fecha descendente
        # select_related optimiza la carga del usuario en cada evento
        historial = HistorialEquipo.objects.filter(equipo=equipo).select_related(
            'usuario'  # Traer datos del usuario que realizó el cambio
        ).order_by('-fecha_hora')  # Ordenar por fecha descendente (más recientes primero)
        
        # Paso 3: Preparar historial con nombre completo de usuario
        # Convertir los objetos Django a diccionarios Python para serialización JSON
        historial_data = []
        for evento in historial:
            historial_data.append({
                'id': evento.id,  # ID único del evento de historial
                'fecha_hora': evento.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),  # Fecha y hora en formato ISO
                'fecha_hora_formateada': evento.fecha_hora.strftime('%d/%m/%Y %H:%M'),  # Fecha y hora formateada para mostrar
                'usuario': evento.usuario.username if evento.usuario else 'Sistema',  # Username del usuario
                'usuario_nombre': obtener_nombre_completo_usuario(evento.usuario),  # Nombre completo del usuario
                'accion': evento.accion,  # Código de la acción (ej: 'EQUIPO_CREADO', 'EQUIPO_MODIFICADO')
                'accion_display': evento.get_accion_display(),  # Nombre legible de la acción
                'descripcion': evento.descripcion,  # Descripción detallada del cambio
                'datos_previos': evento.datos_previos,  # Datos anteriores (JSON)
                'datos_nuevos': evento.datos_nuevos  # Datos nuevos (JSON)
            })
        
        # Paso 4: Retornar respuesta JSON con el historial completo
        return JsonResponse({
            'success': True,  # Indicador de éxito
            'equipo': {
                'id': equipo.equipo_id,  # ID único del equipo
                'nombre': equipo.nombreEquipo,  # Nombre del equipo
                'codigo_interno': equipo.codigoInterno  # Código interno del equipo
            },
            'historial': historial_data  # Lista de eventos en el historial
        })
        
    except Exception as e:
        # Manejo de errores: capturar cualquier excepción y retornar mensaje de error
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener historial de equipo: {str(e)}'
        }, status=500)


# ============================================================================
# VISTA PARA DESCARGAR DOCUMENTACIÓN DE EQUIPOS EN ZIP
# ============================================================================

@login_required
@permission_required_custom('maquinarias.view_equipo')
@require_POST
def descargar_documentacion_zip_equipos(request):
    """
    Vista para generar un archivo ZIP con la documentación de múltiples equipos seleccionados.
    
    Esta función genera un archivo ZIP que contiene todos los documentos de los equipos seleccionados,
    organizados en carpetas por equipo y tipo de documento. La estructura del ZIP es:
    
    Documentacion_Equipos/
        EQUIPO_ID_Nombre_Codigo/
            Tipo_Documento_1/
                archivo1.pdf
                archivo2.pdf
            Tipo_Documento_2/
                archivo3.pdf
        EQUIPO_ID2_Nombre_Codigo/
            ...
    
    Requisitos:
        - Usuario autenticado
        - Permiso 'maquinarias.view_equipo'
        - Método HTTP POST
        - Parámetro 'equipo_ids' en el cuerpo de la petición (lista de IDs)
    
    Retorna:
        HttpResponse con archivo ZIP para descarga o redirección con mensaje de error
    """
    try:
        # Paso 1: Obtener IDs de los equipos desde el cuerpo de la petición POST
        # Los IDs vienen como lista desde el formulario
        equipo_ids = request.POST.getlist('equipo_ids')
        
        # Paso 2: Validar que se seleccionaron equipos
        # Si no se seleccionó ningún equipo, mostrar error y redirigir
        if not equipo_ids:
            messages.error(request, 'No se seleccionó ningún equipo')
            return redirect('maquinarias:lista_equipos')
        
        # Paso 3: Convertir IDs de string a enteros
        # Los IDs vienen como strings desde el formulario HTML
        equipo_ids = [int(eid) for eid in equipo_ids]
        
        # Paso 4: Obtener los equipos desde la base de datos con relaciones optimizadas
        # select_related evita consultas N+1 al traer empresa, modelo, tipo y marca en una sola consulta SQL
        equipos_list = Equipo.objects.filter(equipo_id__in=equipo_ids).select_related(
            'empresa_id',  # Traer datos de la empresa
            'modeloEquipo_id',  # Traer datos del modelo
            'modeloEquipo_id__tipoEquipo_id',  # Traer tipo a través del modelo
            'modeloEquipo_id__marcaEquipo_id'  # Traer marca a través del modelo
        )
        
        # Paso 5: Validar que se encontraron los equipos
        # Si no se encontraron, mostrar error y redirigir
        if not equipos_list.exists():
            messages.error(request, 'No se encontraron los equipos seleccionados')
            return redirect('maquinarias:lista_equipos')
        
        # Paso 6: Inicializar contador de archivos agregados
        # Se usa para verificar si se agregaron archivos al ZIP
        archivos_agregados = 0
        
        # Paso 7: Crear archivo ZIP temporal en el sistema de archivos
        # Se crea un archivo temporal que se eliminará después de leerlo
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = temp_zip.name  # Guardar ruta del archivo temporal
        temp_zip.close()  # Cerrar el archivo temporal
        
        # Paso 8: Configurar logging para rastrear el proceso
        # Esto ayuda a diagnosticar problemas si hay errores al leer archivos
        import logging
        logger = logging.getLogger(__name__)
        
        # Paso 9: Crear archivo ZIP y agregar documentos de cada equipo
        # Se usa compresión ZIP_DEFLATED para reducir el tamaño del archivo
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for equipo in equipos_list:
                logger.info(f"Procesando equipo: {equipo.nombreEquipo} (ID: {equipo.equipo_id})")
                
                # Paso 9.1: Crear nombre de carpeta para este equipo
                # El nombre incluye ID, nombre y código interno del equipo
                nombre_carpeta = f"{equipo.equipo_id}_{equipo.nombreEquipo}_{equipo.codigoInterno}"
                nombre_carpeta = nombre_carpeta.replace('/', '_').replace('\\', '_')  # Limpiar caracteres especiales que no son válidos en nombres de carpeta
                
                # Paso 9.2: Obtener todos los documentos del equipo con relación optimizada
                # select_related evita consultas N+1 al traer el tipo de documento
                documentos = DocumentoMaquinaria.objects.filter(equipo_id=equipo).select_related('tipo_documento_id')
                logger.info(f"  Encontrados {documentos.count()} documentos para el equipo {equipo.nombreEquipo}")
                
                # Paso 9.3: Agregar cada documento al ZIP
                for documento in documentos:
                    logger.info(f"    Procesando documento: {documento.tipo_documento_id.nombre} (ID: {documento.documento_id})")
                    logger.info(f"      Archivo: {documento.archivo.name if documento.archivo else 'None'}")
                    
                    # Paso 9.3.1: Verificar que el documento tiene archivo y nombre válido
                    if documento.archivo and documento.archivo.name:
                        try:
                            # Paso 9.3.2: Abrir y leer el contenido del archivo
                            # Se lee en modo binario ('rb') para manejar cualquier tipo de archivo
                            with documento.archivo.open('rb') as archivo:
                                contenido_archivo = archivo.read()
                            
                            logger.info(f"      Tamaño del archivo leído: {len(contenido_archivo) if contenido_archivo else 0} bytes")
                            
                            # Paso 9.3.3: Verificar que el archivo tiene contenido
                            # Solo se agregan archivos con contenido válido
                            if contenido_archivo and len(contenido_archivo) > 0:
                                # Paso 9.3.4: Limpiar nombre del tipo de documento para usar como nombre de carpeta
                                # Se reemplazan espacios y barras por guiones bajos
                                tipo_doc_nombre = documento.tipo_documento_id.nombre.replace(' ', '_').replace('/', '_')
                                
                                # Paso 9.3.5: Construir ruta completa del archivo dentro del ZIP
                                # Estructura: EQUIPO_ID_Nombre_Codigo/Tipo_Documento/nombre_archivo.ext
                                nombre_archivo_zip = f"{nombre_carpeta}/{tipo_doc_nombre}/{os.path.basename(documento.archivo.name)}"
                                
                                # Paso 9.3.6: Agregar archivo al ZIP
                                zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                archivos_agregados += 1  # Incrementar contador
                                logger.info(f"      ✓ Archivo agregado al ZIP: {nombre_archivo_zip}")
                            else:
                                logger.warning(f"      ✗ Archivo vacío o sin contenido para {documento.tipo_documento_id.nombre}")
                        except Exception as e:
                            # Si hay error al leer un archivo específico, registrar pero continuar con los demás
                            logger.error(f"      ✗ Error al agregar documento {documento.tipo_documento_id.nombre} de {equipo.nombreEquipo}: {e}", exc_info=True)
                    else:
                        logger.warning(f"      ✗ Documento sin archivo o nombre de archivo vacío")
        
        logger.info(f"Total de archivos agregados al ZIP: {archivos_agregados}")
        
        # Paso 10: Verificar si se agregaron archivos al ZIP
        # Si no se agregó ningún archivo, mostrar mensaje de error detallado
        if archivos_agregados == 0:
            # Paso 10.1: Contar documentos totales encontrados para el mensaje de error
            # Esto ayuda a diagnosticar si el problema es que no hay documentos o que no se pueden leer
            total_documentos_encontrados = 0
            equipos_con_docs = []
            for equipo in equipos_list:
                count = DocumentoMaquinaria.objects.filter(equipo_id=equipo).count()
                if count > 0:
                    equipos_con_docs.append(f"{equipo.nombreEquipo} ({count} docs)")
                    total_documentos_encontrados += count
            
            # Paso 10.2: Construir mensaje de error descriptivo
            mensaje_error = f'No se encontraron documentos para descargar. '
            if total_documentos_encontrados > 0:
                mensaje_error += f'Se encontraron {total_documentos_encontrados} documentos en la base de datos pero no se pudieron leer. '
                mensaje_error += f'Equipos con documentos: {", ".join(equipos_con_docs)}. '
                mensaje_error += 'Revisa los logs del servidor para más detalles.'
            else:
                mensaje_error += 'Los equipos seleccionados no tienen documentos asociados.'
            
            logger.warning(mensaje_error)
            messages.error(request, mensaje_error)
            
            # Paso 10.3: Eliminar archivo ZIP temporal si existe
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            
            return redirect('maquinarias:lista_equipos')
        
        # Paso 11: Leer el contenido del archivo ZIP generado
        # Se lee en modo binario para obtener los bytes del archivo
        with open(temp_zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Paso 12: Eliminar archivo temporal del sistema de archivos
        # Ya se leyó el contenido, así que se puede eliminar
        os.unlink(temp_zip_path)
        
        # Paso 13: Crear respuesta HTTP con el archivo ZIP
        # Se genera un nombre de archivo único con fecha y hora
        fecha_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"Documentacion_Equipos_{fecha_hora}.zip"
        
        response = HttpResponse(zip_content, content_type='application/zip')  # Tipo de contenido ZIP
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'  # Forzar descarga con nombre específico
        response['Content-Length'] = len(zip_content)  # Tamaño del archivo en bytes
        
        return response
        
    except Exception as e:
        # Manejo de errores: eliminar archivo temporal si existe y mostrar mensaje de error
        if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)
        
        messages.error(request, f'Error al generar el archivo ZIP: {str(e)}')
        import traceback
        traceback.print_exc()  # Imprimir traceback completo para debugging
        return redirect('maquinarias:lista_equipos')
