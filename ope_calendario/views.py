# ============================================================================
# VISTAS DE CALENDARIO DE OPERACIONES
# ============================================================================
# Este módulo contiene todas las vistas y APIs para el sistema de calendario
# de operaciones, incluyendo gestión de faenas, asignaciones de personal y equipos,
# y visualización del calendario mensual.

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from gen_permissions.decorators import permission_required_custom, permission_required_multiple
from datetime import datetime, date, timedelta
from calendar import monthrange
import json
import hashlib
from .models import (
    Estado, EstadoFuente, Turno, TurnoBloque, 
    Faena, AsignacionFaena, AsignacionEquipoFaena, EstadoManual, HistorialFaena
)
from rrhh_personal.models import Personal
from maquinarias.models import OrdenTrabajo, Equipo

@login_required
@permission_required_custom('ope_calendario.view_faena')
def calendario_mensual(request):
    """
    Vista principal para mostrar el calendario mensual con datos reales y paginación.
    Muestra el calendario de planificación con el estado de cada personal para cada día del mes.
    
    Parámetros GET:
        year: int - Año del calendario (por defecto: año actual)
        month: int - Mes del calendario (1-12, por defecto: mes actual)
        page: int - Página de personal a mostrar (por defecto: 1)
        page_size: int - Cantidad de personal por página (10, 25, 50, 100, por defecto: 10)
        faena: str - Filtro por nombre de faena (opcional)
        cargo: str - Filtro por cargo (opcional)
        empresa: str - Filtro por empresa (opcional)
        search: str - Búsqueda por nombre o RUT (opcional)
    
    Retorna:
        HttpResponse: Renderiza el template calendario_mensual.html con los datos del calendario
    """
    # Paso 1: Obtener parámetros de la URL o usar valores por defecto (fecha actual)
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        # Si hay error al convertir, usar valores por defecto
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
    
    # Paso 3: Validar parámetros de paginación
    # La página debe ser al menos 1
    if page < 1:
        page = 1
    # El tamaño de página debe ser uno de los valores permitidos
    if page_size not in [10, 25, 50, 100]:
        page_size = 10
    
    # Paso 4: Obtener filtros de la URL
    # Estos filtros permiten al usuario filtrar el personal mostrado en el calendario
    faena_filter = request.GET.get('faena', '')  # Filtrar por faena asignada
    cargo_filter = request.GET.get('cargo', '')  # Filtrar por cargo
    empresa_filter = request.GET.get('empresa', '')  # Filtrar por empresa
    search_query = request.GET.get('search', '')  # Búsqueda por nombre o RUT
    
    # Paso 5: Cargar TODOS los datos sin paginación para que el filtro local funcione sobre todos los registros
    # Igual que la tabla de personal: cargar todos los datos y filtrar localmente en JavaScript
    calendario_data = obtener_calendario_mensual(
        year, month, faena_filter, cargo_filter, empresa_filter, search_query, 1, 100000  # page_size muy grande para obtener TODOS
    )
    total_personal = calendario_data['total_personal']
    # Para el frontend, siempre mostrar todos los datos (sin paginación real)
    total_pages = 1
    current_page = 1
    page_size = total_personal if total_personal > 0 else 10
    
    # Obtener rango de fechas del mes para filtrar asignaciones
    _, ultimo_dia = monthrange(year, month)
    fecha_inicio_mes = date(year, month, 1)
    fecha_fin_mes = date(year, month, ultimo_dia)
    
    # Obtener opciones para filtros
    faenas = Faena.objects.filter(activo=True).order_by('nombre')
    turnos = Turno.objects.filter(activo=True).prefetch_related('bloques__estado').order_by('nombre')
    cargos = Personal.objects.filter(activo=True).values_list('infolaboral__cargo_id__cargo', flat=True).distinct().order_by('infolaboral__cargo_id__cargo')
    empresas = Personal.objects.filter(activo=True).values_list('infolaboral__empresa_id__nomFantasia', flat=True).distinct().order_by('infolaboral__empresa_id__nomFantasia')
    
    # Obtener TODOS los estados disponibles para la leyenda
    todos_estados = Estado.objects.filter(activo=True).order_by('-prioridad', 'nombre')
    
    # Nombres de meses en español
    month_names = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Convertir datos a formato JSON serializable
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    
    # Preparar datos del calendario para JSON - NUEVO FORMATO LIGERO
    calendario_json = {
        'personal': [
            {
                'personal_id': p.personal_id,
                'nombre': p.nombre,
                'apepat': p.apepat,
                'apemat': p.apemat,
                'rut': p.rut,
                'dvrut': p.dvrut,
                'cargo': p.infolaboral_set.first().cargo_id.cargo if p.infolaboral_set.exists() else 'Sin cargo',
                'empresa': p.infolaboral_set.first().empresa_id.nomFantasia if p.infolaboral_set.exists() and p.infolaboral_set.first().empresa_id else 'Sin empresa',
                'correo': p.correo if p.correo else 'No disponible',
                'direccion': p.direccion if p.direccion else 'No disponible',
            } for p in calendario_data['personal']
        ],
        'asignaciones': [
            {
                'id': asig.id,
                'personal_id': asig.personal.personal_id,
                'faena': {
                    'id': asig.faena.id,
                    'nombre': asig.faena.nombre
                },
                'turno_id': asig.turno.id,
                'fecha_inicio': asig.fecha_inicio.isoformat(),
                'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
                'bloque_inicio_orden': asig.bloque_inicio.orden if asig.bloque_inicio else 1,
                'activo': asig.activo
            } for asig in calendario_data['asignaciones']
        ],
        'estados_manuales': [
            {
                'personal_id': em.personal.personal_id,
                'estado_id': em.estado.id,
                'fecha_inicio': em.fecha_inicio.isoformat(),
                'fecha_fin': em.fecha_fin.isoformat(),
            } for em in calendario_data['estados_manuales']
        ],
        'estados_calculados': {}
    }
    
    # Serializar estados calculados manualmente para tener control
    for personal_id, dias_estados in calendario_data.get('estados_calculados', {}).items():
        calendario_json['estados_calculados'][str(personal_id)] = {}
        for dia, estados_list in dias_estados.items():
            if estados_list:
                estados_serializados_dia = []
                for estado_item in estados_list:
                    if isinstance(estado_item, dict) and 'estado' in estado_item:
                        # Es un diccionario con estructura completa (estado manual o de asignación)
                        estado_ser = {
                            'id': estado_item['estado'].id,
                            'nombre': estado_item['estado'].nombre,
                            'nombre_corto': estado_item['estado'].nombre_corto or estado_item['estado'].nombre[:3],
                            'color': estado_item['estado'].color,
                            'background_color': estado_item['estado'].background_color,
                            'prioridad': estado_item.get('prioridad', estado_item['estado'].prioridad),
                            'tipo': estado_item.get('tipo'),
                            'faena_id': estado_item.get('faena_id'),
                            'faena_nombre': estado_item.get('faena_nombre'),
                        }
                        
                        estados_serializados_dia.append(estado_ser)
                    else:
                        # Es un objeto Estado directo (sin info adicional)
                        estados_serializados_dia.append({
                            'id': estado_item.id,
                            'nombre': estado_item.nombre,
                            'nombre_corto': estado_item.nombre_corto or estado_item.nombre[:3],
                            'color': estado_item.color,
                            'background_color': estado_item.background_color,
                            'prioridad': estado_item.prioridad,
                            'tipo': None,
                            'faena_id': None,
                            'faena_nombre': None
                        })
                
                calendario_json['estados_calculados'][str(personal_id)][str(dia)] = estados_serializados_dia
            else:
                calendario_json['estados_calculados'][str(personal_id)][str(dia)] = []
    
    calendario_json.update({
        'licencias_medicas': [
            {
                'personal_id': lic.personal_id_id,
                'tipo': lic.tipoLicenciaMedica_id.tipoLicenciaMedica if lic.tipoLicenciaMedica_id else 'Sin especificar',
                'fecha_inicio': lic.fechaEmision.isoformat(),
                'fecha_fin': lic.fecha_fin_licencia.isoformat(),
                'dias': lic.dias_licencia
            } for lic in calendario_data.get('licencias_medicas', [])
        ],
        'ausentismos': [
            {
                'personal_id': aus.personal_id_id,
                'tipo': aus.tipoausen_id.tipo if aus.tipoausen_id else 'Sin especificar',
                'fecha_inicio': aus.fechaini.isoformat(),
                'fecha_fin': aus.fechafin.isoformat()
            } for aus in calendario_data.get('ausentismos', [])
        ],
        'dias_mes': calendario_data['dias_mes']
    })
    
    # Obtener estado predeterminado
    estado_predeterminado = Estado.objects.filter(es_predeterminado=True, activo=True).first()
    if estado_predeterminado:
        calendario_json['estado_predeterminado'] = {
            'id': estado_predeterminado.id,
            'nombre': estado_predeterminado.nombre,
            'nombre_corto': estado_predeterminado.nombre_corto or estado_predeterminado.nombre,
            'color': estado_predeterminado.color,
            'background_color': estado_predeterminado.background_color
        }
    
    
    # Usar las variables de paginación ya calculadas (o las que se calcularon arriba)
    # Si no se definieron arriba (caso con filtros), calcularlas ahora
    if 'total_personal' not in locals():
        total_personal = calendario_data.get('total_personal', 0)
        total_pages = (total_personal + page_size - 1) // page_size if total_personal > 0 else 1
        current_page = page
    
    context = {
        'calendario': json.dumps(calendario_json, cls=DjangoJSONEncoder),
        'calendario_data': calendario_data,  # Agregar datos para el template
        'current_year': year,
        'current_month': month,
        'current_month_name': month_names[month - 1],
        'faenas': faenas,  # Para loops de Django
        'cargos': cargos,  # Para loops de Django
        'empresas': empresas,  # Para loops de Django
        'todos_estados': todos_estados,  # Para mostrar la leyenda en el template
        'filtros': json.dumps({
            'faena': faena_filter,
            'cargo': cargo_filter,
            'search': search_query,
        }),
        'mes_anterior': json.dumps({
            'year': year if month > 1 else year - 1,
            'month': month - 1 if month > 1 else 12
        }),
        'mes_siguiente': json.dumps({
            'year': year if month < 12 else year + 1,
            'month': month + 1 if month < 12 else 1
        }),
        # Información de paginación
        'current_page': current_page,
        'page_size': page_size,
        'total_personal': total_personal,
        'total_pages': total_pages,
        'has_previous': current_page > 1,
        'has_next': current_page < total_pages,
        'page_range': range(max(1, current_page - 2), min(total_pages + 1, current_page + 3)),
    }
    
    # Agregar todos los estados disponibles al calendario JSON
    calendario_json['todos_estados_disponibles'] = [
        {
            'id': estado.id,  # IMPORTANTE: agregar ID para búsquedas
            'nombre': estado.nombre,
            'nombre_corto': estado.nombre_corto or estado.nombre[:3].upper(),
            'color': estado.color,
            'background_color': estado.background_color,
            'prioridad': estado.prioridad,
            'es_bloqueante': estado.es_bloqueante
        } for estado in todos_estados
    ]
    
    # Agregar faenas y turnos para los modales
    calendario_json['faenas'] = [
        {
            'id': faena.id,
            'nombre': faena.nombre,
            'ubicacion': faena.ubicacion,
            'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
            'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None,
        }
        for faena in faenas
    ]
    
    calendario_json['turnos'] = [
        {
            'id': turno.id,
            'nombre': turno.nombre,
            'descripcion': turno.descripcion,
            'bloques': [
                {
                    'id': bloque.id,
                    'orden': bloque.orden,
                    'duracion_dias': bloque.duracion_dias,
                    'estado': {
                        'id': bloque.estado.id,
                        'nombre': bloque.estado.nombre,
                        'nombre_corto': bloque.estado.nombre_corto or bloque.estado.nombre,
                        'color': bloque.estado.color,
                        'background_color': bloque.estado.background_color,
                        'prioridad': bloque.estado.prioridad,
                        'es_bloqueante': bloque.estado.es_bloqueante
                    }
                }
                for bloque in turno.bloques.all().order_by('orden')
            ]
        }
        for turno in turnos.prefetch_related('bloques__estado')
    ]
    
    # Agregar cargos para filtros
    calendario_json['cargos'] = list(cargos)
    
    # Agregar información del mes actual para el frontend
    calendario_json['current_year'] = year
    calendario_json['current_month'] = month
    
    # Actualizar el calendario en el context con los estados incluidos
    context['calendario'] = json.dumps(calendario_json, cls=DjangoJSONEncoder)
    
    return render(request, 'calendario/calendario_mensual.html', context)

def obtener_calendario_mensual(year, month, faena_filter='', cargo_filter='', empresa_filter='', search_query='', page=1, page_size=10):
    """
    Obtiene datos para el calendario mensual con paginación y filtros.
    Esta función implementa una arquitectura escalable donde se envían las asignaciones
    al frontend y los estados se calculan en JavaScript, evitando cálculos pesados en el servidor.
    
    Arquitectura:
    - Envía asignaciones al frontend (datos ligeros)
    - Estados se calculan en JavaScript (distribuye la carga)
    - Escalable: O(1) - El tiempo no aumenta proporcionalmente con más trabajadores
    
    Parámetros:
        year: int - Año del calendario
        month: int - Mes del calendario (1-12)
        faena_filter: str - Filtro por nombre de faena (opcional)
        cargo_filter: str - Filtro por cargo (opcional)
        empresa_filter: str - Filtro por empresa (opcional)
        search_query: str - Búsqueda por nombre o RUT (opcional)
        page: int - Página actual (por defecto: 1)
        page_size: int - Cantidad de registros por página (por defecto: 10)
    
    Retorna:
        dict: Diccionario con datos del calendario, personal paginado, asignaciones y estados
    """
    # Obtener rango de fechas del mes
    _, ultimo_dia = monthrange(year, month)
    fecha_inicio = date(year, month, 1)
    fecha_fin = date(year, month, ultimo_dia)
    
    # Construir filtros para el personal
    personal_query = Personal.objects.filter(activo=True).select_related(
        'sexo_id', 'estcivil_id'
    ).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id'
    )
    
    # FILTROS EN EL BACKEND
    filtros_aplicados = []
    
    if faena_filter and faena_filter.strip():
        if faena_filter.lower() == 'sin asignar':
            # Filtrar personal SIN asignaciones activas en el mes actual
            # Incluir tanto asignaciones con fecha_fin como asignaciones indefinidas (sin fecha_fin)
            personal_con_asignaciones = AsignacionFaena.objects.filter(
                Q(activo=True) &
                Q(fecha_inicio__lte=fecha_fin) &
                (Q(fecha_fin__gte=fecha_inicio) | Q(fecha_fin__isnull=True))
            ).values_list('personal_id', flat=True).distinct()
            
            personal_query = personal_query.exclude(
                personal_id__in=personal_con_asignaciones
            )
            filtros_aplicados.append("faena=Sin asignar")
        else:
            # Filtrar por faena específica (incluir personal con asignaciones O estados manuales en esa faena)
            personal_query = personal_query.filter(
                Q(asignaciones_faena__faena__nombre__icontains=faena_filter,
                  asignaciones_faena__activo=True) |
                Q(estados_manuales__faena__nombre__icontains=faena_filter)
            ).distinct()
            filtros_aplicados.append(f"faena={faena_filter}")
    
    if cargo_filter and cargo_filter.strip():
        personal_query = personal_query.filter(
            infolaboral__cargo_id__cargo__icontains=cargo_filter
        ).distinct()
        filtros_aplicados.append(f"cargo={cargo_filter}")
    
    if empresa_filter and empresa_filter.strip():
        personal_query = personal_query.filter(
            infolaboral__empresa_id__nomFantasia__icontains=empresa_filter
        ).distinct()
        filtros_aplicados.append(f"empresa={empresa_filter}")
    
    if search_query and search_query.strip():
        personal_query = personal_query.filter(
            Q(nombre__icontains=search_query) |
            Q(apepat__icontains=search_query) |
            Q(apemat__icontains=search_query) |
            Q(rut__icontains=search_query)
        )
        filtros_aplicados.append(f"búsqueda={search_query}")
    
    # Contar total antes de paginar
    total_personal = personal_query.count()
    
    # Aplicar paginación
    offset = (page - 1) * page_size
    personal_list = list(personal_query.order_by('apepat', 'nombre')[offset:offset + page_size])
    
    # Obtener IDs del personal paginado
    personal_ids = [p.personal_id for p in personal_list]
    
    # Obtener SOLO las asignaciones activas de este personal en este mes
    # Esto es mucho más eficiente que calcular estados
    asignaciones = AsignacionFaena.objects.filter(
        personal_id__in=personal_ids,
        activo=True,
        fecha_inicio__lte=fecha_fin
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)
    ).select_related(
        'personal', 'faena', 'turno', 'bloque_inicio__estado'
    ).prefetch_related(
        'turno__bloques__estado'
    )
    
    # Obtener estados manuales de este personal en este mes (solo personal activo)
    estados_manuales_query = EstadoManual.objects.filter(
        personal_id__in=personal_ids,
        personal__activo=True,  # Filtrar solo personal activo
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio
    )
    
    # Si hay filtro de faena, también filtrar los estados manuales por esa faena
    if faena_filter and faena_filter.strip() and faena_filter.lower() != 'sin asignar':
        estados_manuales_query = estados_manuales_query.filter(
            faena__nombre__icontains=faena_filter
        )
    
    estados_manuales = estados_manuales_query.select_related('personal', 'estado', 'faena')
    
    # OPTIMIZACIÓN: Obtener TODOS los datos necesarios de UNA VEZ
    from rrhh_personal.models import Ausentismo, LicenciaMedicaPorPersonal
    from .models import EstadoFuente
    
    # 1. Obtener todas las fuentes de estado configuradas
    fuentes_estado = EstadoFuente.objects.select_related('estado', 'content_type').all()
    
    # 2. Obtener TODOS los registros de TODAS las fuentes para este mes
    registros_por_fuente = {}
    
    for fuente in fuentes_estado:
        if not fuente.estado.activo:
            continue
            
        modelo = fuente.content_type.model_class()
        if not modelo:
            continue
        
        # Construir consulta para obtener todos los registros del mes
        try:
            registros = modelo.objects.filter(**{
                f"{fuente.campo_personal}_id__in": personal_ids,
                f"{fuente.campo_fecha_inicio}__lte": fecha_fin,
                f"{fuente.campo_fecha_fin}__gte": fecha_inicio,
            })
            
            # Aplicar filtros extra si existen
            if fuente.filtro_extra:
                for campo, valor in fuente.filtro_extra.items():
                    registros = registros.filter(**{campo: valor})
            
            registros_por_fuente[fuente.estado.id] = {
                'estado': fuente.estado,
                'registros': list(registros),
                'campo_personal': fuente.campo_personal,
                'campo_inicio': fuente.campo_fecha_inicio,
                'campo_fin': fuente.campo_fecha_fin
            }
        except Exception as e:
            # Silenciosamente continuar si hay error en una fuente
            continue
    
    # 3. Procesar estados en MEMORIA (sin consultas adicionales)
    estados_por_personal = {}
    
    for persona in personal_list:
        estados_por_personal[persona.personal_id] = {}
        
        for dia in range(1, ultimo_dia + 1):
            fecha_actual = date(year, month, dia)
            estados_del_dia = []
            
            # Revisar estados manuales
            for em in estados_manuales:
                if (em.personal.personal_id == persona.personal_id and 
                    em.fecha_inicio <= fecha_actual <= em.fecha_fin):
                    estados_del_dia.append({
                        'estado': em.estado,
                        'tipo': 'manual',
                        'prioridad': em.estado.prioridad,
                        'es_bloqueante': em.estado.es_bloqueante,
                        'faena': em.faena,
                        'faena_id': em.faena.id if em.faena else None,
                        'faena_nombre': em.faena.nombre if em.faena else 'Sin faena'
                    })
            
            # Revisar estados de fuentes externas
            for estado_id, datos in registros_por_fuente.items():
                for registro in datos['registros']:
                    # Verificar que sea de esta persona
                    personal_registro = getattr(registro, datos['campo_personal'])
                    if personal_registro.personal_id != persona.personal_id:
                        continue
                    
                    # Verificar que la fecha esté en el rango
                    fecha_inicio_reg = getattr(registro, datos['campo_inicio'])
                    fecha_fin_reg = getattr(registro, datos['campo_fin'])
                    
                    if fecha_inicio_reg <= fecha_actual <= fecha_fin_reg:
                        # Crear una copia del estado con detalles del registro
                        estado_con_detalles = type('Estado', (), {})()
                        for attr in ['id', 'nombre', 'nombre_corto', 'color', 'background_color', 'prioridad', 'es_bloqueante']:
                            setattr(estado_con_detalles, attr, getattr(datos['estado'], attr))
                        
                        # Agregar detalles específicos del registro fuente
                        detalles = {}
                        modelo_name = registro.__class__.__name__.lower()
                        
                        if modelo_name == 'ausentismo':
                            detalles = {
                                'tipo': 'Permiso',
                                'tipo_detalle': registro.tipoausen_id.tipo if hasattr(registro, 'tipoausen_id') else 'Sin especificar',
                                'fecha_inicio': fecha_inicio_reg.strftime('%d/%m/%Y'),
                                'fecha_fin': fecha_fin_reg.strftime('%d/%m/%Y'),
                                'observacion': getattr(registro, 'observacion', '')
                            }
                        elif modelo_name == 'licenciamedicaporpersonal':
                            detalles = {
                                'tipo': 'Licencia Médica',
                                'tipo_detalle': registro.tipoLicenciaMedica_id.tipoLicenciaMedica if hasattr(registro, 'tipoLicenciaMedica_id') else 'Sin especificar',
                                'fecha_inicio': fecha_inicio_reg.strftime('%d/%m/%Y'),
                                'fecha_fin': fecha_fin_reg.strftime('%d/%m/%Y'),
                                'dias': getattr(registro, 'dias_licencia', 0),
                                'observacion': getattr(registro, 'observacion', '')
                            }
                        else:
                            detalles = {
                                'tipo': datos['estado'].nombre,
                                'fecha_inicio': fecha_inicio_reg.strftime('%d/%m/%Y'),
                                'fecha_fin': fecha_fin_reg.strftime('%d/%m/%Y')
                            }
                        
                        estado_con_detalles.detalles = detalles
                        
                        estados_del_dia.append({
                            'estado': estado_con_detalles,
                            'tipo': 'fuente',
                            'prioridad': datos['estado'].prioridad,
                            'es_bloqueante': datos['estado'].es_bloqueante
                        })
                        break  # Solo necesitamos saber que existe
            
            # Revisar estado de turno
            for asig in asignaciones:
                if (asig.personal.personal_id == persona.personal_id and
                    asig.fecha_inicio <= fecha_actual and
                    (not asig.fecha_fin or asig.fecha_fin >= fecha_actual) and
                    asig.activo):
                    estado_turno = asig.obtener_estado_en_fecha(fecha_actual)
                    if estado_turno:
                        estados_del_dia.append({
                            'estado': estado_turno,
                            'tipo': 'turno',
                            'prioridad': estado_turno.prioridad,
                            'es_bloqueante': estado_turno.es_bloqueante
                        })
                    break
            
            # Resolver prioridades
            if estados_del_dia:
                # Si hay bloqueantes, tomar el de mayor prioridad
                bloqueantes = [e for e in estados_del_dia if e['es_bloqueante']]
                if bloqueantes:
                    bloqueantes.sort(key=lambda x: x['prioridad'], reverse=True)
                    estados_por_personal[persona.personal_id][dia] = [bloqueantes[0]]  # Guardar el diccionario completo
                else:
                    # Ordenar por prioridad y tomar el mayor
                    estados_del_dia.sort(key=lambda x: x['prioridad'], reverse=True)
                    max_prioridad = estados_del_dia[0]['prioridad']
                    estados_misma_prioridad = [e for e in estados_del_dia if e['prioridad'] == max_prioridad]  # Guardar diccionarios completos
                    estados_por_personal[persona.personal_id][dia] = estados_misma_prioridad
            else:
                estados_por_personal[persona.personal_id][dia] = []
    
    # Obtener licencias médicas y ausentismos activos para validaciones
    licencias_medicas = LicenciaMedicaPorPersonal.objects.filter(
        personal_id_id__in=personal_ids,
        fechaEmision__lte=fecha_fin,
        fecha_fin_licencia__gte=fecha_inicio
    ).select_related('personal_id', 'tipoLicenciaMedica_id')
    
    ausentismos = Ausentismo.objects.filter(
        personal_id_id__in=personal_ids,
        fechaini__lte=fecha_fin,
        fechafin__gte=fecha_inicio
    ).select_related('personal_id', 'tipoausen_id')
    
    # Estructura con estados calculados
    calendario = {
        'personal': personal_list,
        'asignaciones': list(asignaciones),
        'estados_manuales': list(estados_manuales),
        'estados_calculados': estados_por_personal,  # NUEVO: Estados ya calculados
        'licencias_medicas': list(licencias_medicas),
        'ausentismos': list(ausentismos),
        'dias_mes': ultimo_dia,
        'total_personal': total_personal,
        'page': page,
        'page_size': page_size,
        'has_more': offset + page_size < total_personal,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    
    return calendario

def obtener_estado_final_personal_fecha_optimizado(personal, fecha, estados_fuente_cache):
    """
    Función helper optimizada para calcular el estado final de un personal en una fecha específica.
    Esta versión usa un caché de estados_fuente para evitar consultas repetidas a la base de datos.
    Reduce consultas de ~620 a menos de 10 por carga de página.
    
    Orden de prioridad:
    1. Estados manuales (más alta prioridad)
    2. Estados de fuentes externas (según prioridad del estado)
    3. Estados derivados de turnos (más baja prioridad)
    
    Parámetros:
        personal: Personal - Instancia del personal para calcular el estado
        fecha: date - Fecha para la cual calcular el estado
        estados_fuente_cache: dict - Caché de estados_fuente para optimización
    
    Retorna:
        list: Lista de estados (normalmente uno, pero puede haber múltiples con misma prioridad)
    """
    from django.db.models import Q
    
    # 1. Buscar estados manuales (ya pre-cargados con prefetch_related)
    estados_manuales = [em for em in personal.estados_manuales.all() 
                       if em.fecha_inicio <= fecha <= em.fecha_fin and em.activo]
    
    if estados_manuales:
        estados_manuales.sort(key=lambda x: x.estado.prioridad, reverse=True)
        bloqueantes = [em for em in estados_manuales if em.estado.es_bloqueante]
        if bloqueantes:
            return [bloqueantes[0].estado]
        return [estados_manuales[0].estado]
    
    # 2. Buscar estados de fuentes externas (usando cache)
    estados_fuente = []
    for estado_fuente in estados_fuente_cache:
        modelo_name = estado_fuente.content_type.model
        
        # Buscar en los datos pre-cargados según el modelo
        if modelo_name == 'ausentismo':
            registros = personal.ausentismo_set.all()
        elif modelo_name == 'licenciamedicaporpersonal':
            registros = personal.licenciamedicaporpersonal_set.all()
        else:
            continue  # Otros modelos no implementados aún
        
        # Verificar si algún registro coincide con la fecha
        for registro in registros:
            fecha_inicio_campo = getattr(registro, estado_fuente.campo_fecha_inicio, None)
            fecha_fin_campo = getattr(registro, estado_fuente.campo_fecha_fin, None)
            
            if (fecha_inicio_campo and fecha_fin_campo and 
                fecha_inicio_campo <= fecha <= fecha_fin_campo):
                # Incluir información detallada de la fuente
                estado_con_detalle = {
                    'estado': estado_fuente.estado,
                    'tipo_fuente': 'externa',
                    'fuente_nombre': estado_fuente.content_type.model,
                    'fecha_inicio': fecha_inicio_campo,
                    'fecha_fin': fecha_fin_campo,
                    'registro_id': registro.pk,
                    'detalles': {}
                }
                
                # Agregar detalles específicos según el tipo
                try:
                    if modelo_name == 'ausentismo':
                        estado_con_detalle['detalles'] = {
                            'motivo': getattr(registro, 'motivo', 'Sin motivo'),
                            'tipo': 'Ausentismo'
                        }
                    elif modelo_name == 'licenciamedicaporpersonal':
                        estado_con_detalle['detalles'] = {
                            'motivo': getattr(registro, 'motivo', 'Licencia médica'),
                            'tipo': 'Licencia Médica',
                        'fecha_emision': str(getattr(registro, 'fechaEmision', '')) if getattr(registro, 'fechaEmision', None) else None
                    }
                except Exception:
                    estado_con_detalle['detalles'] = {'tipo': 'Error al cargar detalles'}
                
                estados_fuente.append(estado_con_detalle)
                break
    
    # 3. Buscar estado derivado de turno (ya pre-cargado)
    estado_turno = None
    for asignacion in personal.asignaciones_faena.all():
        if (asignacion.activo and 
            asignacion.fecha_inicio <= fecha and 
            (not asignacion.fecha_fin or asignacion.fecha_fin >= fecha)):
            estado_turno = asignacion.obtener_estado_en_fecha(fecha)
            break
    
    # 4. Resolver conflictos de prioridad
    todos_estados = []
    
    for estado_detalle in estados_fuente:
        if isinstance(estado_detalle, dict):
            # Nuevo formato con detalles
            todos_estados.append({
                'estado': estado_detalle['estado'],
                'tipo': 'fuente',
                'prioridad': estado_detalle['estado'].prioridad,
                'detalle_fuente': estado_detalle
            })
        else:
            # Formato anterior (fallback)
            todos_estados.append({
                'estado': estado_detalle,
                'tipo': 'fuente',
                'prioridad': estado_detalle.prioridad
            })
    
    if estado_turno:
        todos_estados.append({
            'estado': estado_turno,
            'tipo': 'turno',
            'prioridad': estado_turno.prioridad
        })
    
    if not todos_estados:
        # Buscar estado predeterminado (cache esto también)
        try:
            from .models import Estado
            estado_predeterminado = Estado.objects.filter(
                activo=True,
                es_predeterminado=True
            ).first()
            
            if estado_predeterminado:
                return [estado_predeterminado]
            return []
        except:
            return []
    
    # Ordenar y resolver prioridades
    todos_estados.sort(key=lambda x: x['prioridad'], reverse=True)
    
    bloqueantes = [x for x in todos_estados if x['estado'].es_bloqueante]
    if bloqueantes:
        return [bloqueantes[0]['estado']]
    
    prioridad_maxima = todos_estados[0]['prioridad']
    estados_misma_prioridad = [
        x['estado'] for x in todos_estados 
        if x['prioridad'] == prioridad_maxima
    ]
    
    return estados_misma_prioridad

def obtener_estado_final_personal_fecha(personal, fecha):
    """
    Función helper para calcular el estado final de un personal en una fecha específica.
    Considera todas las fuentes de estados (manuales, fuentes externas, turnos) y aplica prioridades.
    
    Orden de prioridad:
    1. Estados manuales (más alta prioridad)
    2. Estados de fuentes externas (según prioridad del estado)
    3. Estados derivados de turnos (más baja prioridad)
    
    Si hay estados bloqueantes, retorna solo el de mayor prioridad.
    Si hay múltiples estados con la misma prioridad máxima, retorna todos.
    
    Parámetros:
        personal: Personal - Instancia del personal para calcular el estado
        fecha: date - Fecha para la cual calcular el estado
    
    Retorna:
        list: Lista de estados con detalles (normalmente uno, pero puede haber múltiples con misma prioridad)
    """
    from django.db.models import Q
    
    # 1. Buscar estados manuales
    estados_manuales = EstadoManual.objects.filter(
        personal=personal,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    ).select_related('estado', 'faena').order_by('-estado__prioridad')
    
    if estados_manuales.exists():
        # Si hay estados bloqueantes, retornar el de mayor prioridad
        bloqueantes = [em for em in estados_manuales if em.estado.es_bloqueante]
        if bloqueantes:
            return [bloqueantes[0].estado]
        # Si no hay bloqueantes, retornar el de mayor prioridad
        return [estados_manuales.first().estado]
    
    # 2. Buscar estados de fuentes externas
    estados_fuente = []
    for estado_fuente in EstadoFuente.objects.select_related('estado', 'content_type').all():
        if not estado_fuente.estado.activo:
            continue
            
        # Construir consulta dinámica
        modelo = estado_fuente.content_type.model_class()
        if not modelo:
            continue
            
        filtros = Q(**{
            f"{estado_fuente.campo_personal}": personal,
            f"{estado_fuente.campo_fecha_inicio}__lte": fecha,
            f"{estado_fuente.campo_fecha_fin}__gte": fecha,
        })
        
        # Aplicar filtros extra si existen
        if estado_fuente.filtro_extra:
            for campo, valor in estado_fuente.filtro_extra.items():
                filtros &= Q(**{campo: valor})
        
        if modelo.objects.filter(filtros).exists():
            estados_fuente.append(estado_fuente.estado)
    
    # 3. Buscar estado derivado de turno
    estado_turno = None
    asignaciones_activas = AsignacionFaena.objects.filter(
        personal=personal,
        fecha_inicio__lte=fecha,
        activo=True
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha)
    ).select_related('turno').first()
    
    if asignaciones_activas:
        estado_turno = asignaciones_activas.obtener_estado_en_fecha(fecha)
    
    # 4. Resolver conflictos de prioridad
    todos_estados = []
    
    # Agregar estados de fuentes externas
    for estado_detalle in estados_fuente:
        if isinstance(estado_detalle, dict):
            # Nuevo formato con detalles
            todos_estados.append({
                'estado': estado_detalle['estado'],
                'tipo': 'fuente',
                'prioridad': estado_detalle['estado'].prioridad,
                'detalle_fuente': estado_detalle
            })
        else:
            # Formato anterior (fallback)
            todos_estados.append({
                'estado': estado_detalle,
                'tipo': 'fuente',
                'prioridad': estado_detalle.prioridad
            })
    
    # Agregar estado de turno si existe
    if estado_turno:
        # Incluir información detallada del turno
        estado_turno_detalle = {
            'estado': estado_turno,
            'tipo_fuente': 'turno',
            'fuente_nombre': 'asignacion_faena',
            'fecha_inicio': asignaciones_activas.fecha_inicio,
            'fecha_fin': asignaciones_activas.fecha_fin,
            'detalles': {
                'faena': asignaciones_activas.faena.nombre,
                'turno': asignaciones_activas.turno.nombre,
                'tipo': 'Asignación de Faena'
            }
        }
        todos_estados.append({
            'estado': estado_turno,
            'tipo': 'turno',
            'prioridad': estado_turno.prioridad,
            'detalle_fuente': estado_turno_detalle
        })
    
    if not todos_estados:
        # Si no hay nada, retornar estado por defecto
        try:
            estado_predeterminado = Estado.objects.filter(
                activo=True,
                es_predeterminado=True
            ).first()
            
            if estado_predeterminado:
                return [estado_predeterminado]
            
            return []
        except:
            return []
    
    # Ordenar por prioridad (mayor número = mayor prioridad)
    todos_estados.sort(key=lambda x: x['prioridad'], reverse=True)
    
    # Si hay estados bloqueantes, solo retornar el de mayor prioridad
    bloqueantes = [x for x in todos_estados if x['estado'].es_bloqueante]
    if bloqueantes:
        return [bloqueantes[0]['estado']]
    
    # Obtener la prioridad más alta
    prioridad_maxima = todos_estados[0]['prioridad']
    
    # Retornar todos los estados que tengan la prioridad más alta con sus detalles
    estados_misma_prioridad = [
        x for x in todos_estados 
        if x['prioridad'] == prioridad_maxima
    ]
    
    return estados_misma_prioridad

@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.view_faena', is_ajax=True)
def api_calendario_mensual(request):
    """
    API endpoint para obtener datos del calendario mensual en formato JSON.
    Útil para actualizaciones dinámicas del calendario sin recargar la página.
    
    Parámetros GET:
        year: int - Año del calendario (por defecto: año actual)
        month: int - Mes del calendario (1-12, por defecto: mes actual)
        page: int - Página actual (por defecto: 1)
        page_size: int - Cantidad de registros por página (por defecto: 10)
        faena: str - Filtro por nombre de faena (opcional)
        cargo: str - Filtro por cargo (opcional)
        empresa: str - Filtro por empresa (opcional)
        search: str - Búsqueda por nombre o RUT (opcional)
    
    Retorna:
        JsonResponse: Datos del calendario en formato JSON con personal, asignaciones y estados
    """
    """API para obtener datos del calendario en formato JSON con paginación"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        faena_filter = request.GET.get('faena', '')
        cargo_filter = request.GET.get('cargo', '')
        search_query = request.GET.get('search', '')
        
        # Obtener datos del calendario paginados
        calendario_data = obtener_calendario_mensual(
            year, month, faena_filter, cargo_filter, search_query, page, page_size
        )
        
        # Convertir estados a formato serializable
        estados_serializados = {}
        for personal_id, estados_persona in calendario_data.get('estados_calculados', {}).items():
            estados_serializados[personal_id] = {}
            for dia, estados in estados_persona.items():
                if estados:
                    if isinstance(estados, list) and len(estados) > 0:
                        estado_dict = estados[0] if isinstance(estados[0], dict) else {}
                        estado_obj = estado_dict.get('estado') if isinstance(estado_dict, dict) else estados[0]
                        
                        # Debug para estados manuales
                        if isinstance(estado_dict, dict) and estado_dict.get('tipo') == 'manual':
                            print(f"\n=== DEBUG Estado Manual ===")
                            print(f"Día: {dia}, Personal: {personal_id}")
                            print(f"estado_dict completo: {estado_dict}")
                            print(f"Keys disponibles: {estado_dict.keys()}")
                        
                        estado_serializado = {
                            'id': estado_obj.id,
                            'nombre': estado_obj.nombre,
                            'nombre_corto': estado_obj.nombre_corto or estado_obj.nombre,
                            'color': estado_obj.color,
                            'background_color': estado_obj.background_color,
                            'prioridad': estado_obj.prioridad,
                            'es_bloqueante': estado_obj.es_bloqueante
                        }
                        
                        # Si es un estado manual o de asignación, incluir info de faena
                        if isinstance(estado_dict, dict):
                            if 'tipo' in estado_dict:
                                estado_serializado['tipo'] = estado_dict['tipo']
                            if 'faena_id' in estado_dict and estado_dict['faena_id']:
                                estado_serializado['faena_id'] = estado_dict['faena_id']
                                estado_serializado['faena_nombre'] = estado_dict['faena_nombre']
                        
                        estados_serializados[personal_id][dia] = estado_serializado
                    else:
                        estados_serializados[personal_id][dia] = None
                else:
                    estados_serializados[personal_id][dia] = None
        
        # Construir diccionario de faenas por personal (considerando asignaciones y estados manuales)
        # Calcular fechas del mes para filtrar estados manuales
        from calendar import monthrange
        fecha_inicio_mes = date(year, month, 1)
        fecha_fin_mes = date(year, month, monthrange(year, month)[1])
        
        faenas_por_personal = {}
        for p in calendario_data['personal']:
            # Buscar asignación activa
            asignacion = p.asignaciones_faena.filter(activo=True).first()
            if asignacion:
                faenas_por_personal[p.personal_id] = asignacion.faena.nombre
            else:
                # Si no tiene asignación de turno, buscar estado manual
                estado_manual = p.estados_manuales.filter(
                    fecha_inicio__lte=fecha_fin_mes,
                    fecha_fin__gte=fecha_inicio_mes
                ).first()
                if estado_manual:
                    faenas_por_personal[p.personal_id] = estado_manual.faena.nombre
                else:
                    faenas_por_personal[p.personal_id] = 'Sin asignar'
        
        # Convertir a formato JSON serializable
        json_data = {
            'personal': [
                {
                    'personal_id': p.personal_id,
                    'nombre': p.nombre,
                    'apepat': p.apepat,
                    'apemat': p.apemat,
                    'rut': p.rut,
                    'dvrut': p.dvrut,
                    'cargo': p.infolaboral_set.first().cargo_id.cargo if p.infolaboral_set.exists() else 'Sin cargo',
                    'faena': faenas_por_personal.get(p.personal_id, 'Sin asignar'),
                    'correo': p.correo if p.correo else 'No disponible',
                    'direccion': p.direccion if p.direccion else 'No disponible',
                }
                for p in calendario_data['personal']
            ],
            'estados': estados_serializados,
            'dias_mes': calendario_data['dias_mes'],
            'total_personal': calendario_data['total_personal'],
            'page': calendario_data['page'],
            'page_size': calendario_data['page_size'],
            'has_more': calendario_data['has_more'],
            'total_pages': (calendario_data['total_personal'] + page_size - 1) // page_size
        }
        
        return JsonResponse(json_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def invalidar_cache_calendario():
    """
    Función helper para invalidar el caché del calendario.
    Se llama cuando hay cambios en asignaciones, estados manuales o faenas
    para asegurar que los datos mostrados estén actualizados.
    Incrementa la versión del caché para invalidar todos los calendarios en caché.
    """
    # Incrementar versión del caché para invalidar todos los calendarios
    current_version = cache.get('calendario_version', 0)
    new_version = current_version + 1
    cache.set('calendario_version', new_version, None)  # Sin expiración


@login_required
@permission_required_custom('ope_calendario.view_faena', is_ajax=True)
@require_http_methods(["GET"])
def obtener_info_personal(request, personal_id):
    """
    API endpoint para obtener información detallada de un personal específico.
    Incluye datos personales, asignaciones activas, estados, licencias, certificaciones y exámenes.
    
    Parámetros:
        request: HttpRequest - Request HTTP
        personal_id: int - ID del personal a consultar
    
    Retorna:
        JsonResponse: Información completa del personal en formato JSON, incluyendo documentación
    """
    try:
        from rrhh_personal.models import (
            Personal, LicenciaPorPersonal, LicenciaInternaPorPersonal,
            Certificacion, Examen
        )
        from datetime import date
        
        personal = Personal.objects.get(personal_id=personal_id, activo=True)
        
        # Información básica
        info = {
            'personal_id': personal.personal_id,
            'nombre': personal.nombre,
            'apepat': personal.apepat,
            'apemat': personal.apemat,
            'rut': personal.rut,
            'dvrut': personal.dvrut,
            'correo': personal.correo or 'No disponible',
            'direccion': personal.direccion or 'No disponible',
            'cargo': personal.infolaboral_set.first().cargo_id.cargo if personal.infolaboral_set.exists() else 'Sin cargo',
            'empresa': personal.infolaboral_set.first().empresa_id.nomFantasia if personal.infolaboral_set.exists() and personal.infolaboral_set.first().empresa_id else 'Sin empresa',
        }
        
        # Documentos personales
        documentos_personales = []
        documentos_campos = {
            'curriculum': 'Curriculum Vitae',
            'certificado_antecedentes': 'Certificado de Antecedentes',
            'hoja_vida_conductor': 'Hoja de Vida del Conductor',
            'foto_carnet': 'Foto Carnet',
            'certificado_afp': 'Certificado de Afiliación AFP',
            'certificado_salud': 'Certificado de Afiliación de Salud',
            'certificado_estudios': 'Certificado de Estudios',
            'certificado_residencia': 'Certificado de Residencia',
            'fotocopia_carnet': 'Fotocopia de Carnet',
            'fotocopia_finiquito': 'Fotocopia de Último Finiquito',
            'comprobante_banco': 'Comprobante de Cuenta Bancaria'
        }
        
        for campo, nombre in documentos_campos.items():
            documento = getattr(personal, campo, None)
            fecha_vencimiento = None
            vigente = None
            
            # Solo fotocopia_carnet tiene fecha de vencimiento
            if campo == 'fotocopia_carnet' and personal.fecha_vencimiento_carnet:
                fecha_vencimiento = personal.fecha_vencimiento_carnet.strftime('%d/%m/%Y')
                vigente = personal.fecha_vencimiento_carnet >= date.today()
            
            if documento:
                try:
                    documento_url = documento.url
                    documentos_personales.append({
                        'campo': campo,
                        'nombre': nombre,
                        'url': documento_url,
                        'tiene_documento': True,
                        'fecha_vencimiento': fecha_vencimiento,
                        'vigente': vigente
                    })
                except Exception:
                    documentos_personales.append({
                        'campo': campo,
                        'nombre': nombre,
                        'url': None,
                        'tiene_documento': False,
                        'fecha_vencimiento': fecha_vencimiento,
                        'vigente': vigente
                    })
            else:
                documentos_personales.append({
                    'campo': campo,
                    'nombre': nombre,
                    'url': None,
                    'tiene_documento': False,
                    'fecha_vencimiento': fecha_vencimiento,
                    'vigente': vigente
                })
        
        info['documentos_personales'] = documentos_personales
        
        # Licencias de conducir
        licencias = LicenciaPorPersonal.objects.filter(
            personal_id=personal
        ).prefetch_related('tipos')
        
        info['licencias_conducir'] = [{
            'id': lic.licenciaPorPersonal_id,
            'clases': ', '.join([t.tipoLicencia for t in lic.tipos.all()]),
            'fecha_emision': lic.fechaEmision.strftime('%d/%m/%Y'),
            'fecha_vencimiento': lic.fechaVencimiento.strftime('%d/%m/%Y'),
            'vigente': lic.fechaVencimiento >= date.today(),
            'tiene_documento': bool(lic.rutaDoc),
            'documento_url': lic.rutaDoc.url if lic.rutaDoc else None
        } for lic in licencias]
        
        # Licencias internas
        licencias_internas = LicenciaInternaPorPersonal.objects.filter(
            personal_id=personal
        ).select_related('tipoLicenciaInterna_id')
        
        info['licencias_internas'] = [{
            'id': lic.licenciaInterna_id,
            'tipo': lic.tipoLicenciaInterna_id.tipoLicenciaInterna,
            'numero': lic.numero_licencia or '-',
            'empresa': lic.empresa_emisora or '-',
            'fecha_emision': lic.fechaEmision.strftime('%d/%m/%Y'),
            'fecha_vencimiento': lic.fechaVencimiento.strftime('%d/%m/%Y'),
            'vigente': lic.esta_activa,
            'tiene_documento': bool(lic.rutaDoc),
            'documento_url': lic.rutaDoc.url if lic.rutaDoc else None
        } for lic in licencias_internas]
        
        # Certificaciones
        certificaciones = Certificacion.objects.filter(
            personal_id=personal
        ).select_related('tipoCertificacion_id', 'proveedor_id')
        
        info['certificaciones'] = [{
            'id': cert.certif_id,
            'tipo': cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else 'N/A',
            'proveedor': str(cert.proveedor_id) if cert.proveedor_id else 'N/A',
            'fecha_emision': cert.fechaEmision.strftime('%d/%m/%Y'),
            'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
            'vigente': cert.fechaVencimiento >= date.today(),
            'tiene_documento': bool(cert.rutaDoc),
            'documento_url': cert.rutaDoc.url if cert.rutaDoc else None
        } for cert in certificaciones]
        
        # Exámenes
        examenes = Examen.objects.filter(
            personal_id=personal
        ).select_related('tipoEx_id', 'resultadoEx_id', 'proveedor_id')
        
        info['examenes'] = [{
            'id': exam.examen_id,
            'tipo': exam.tipoEx_id.tipoExamen if exam.tipoEx_id else 'N/A',
            'resultado': exam.resultadoEx_id.resultado if exam.resultadoEx_id else '-',
            'proveedor': str(exam.proveedor_id) if exam.proveedor_id else 'N/A',
            'fecha_emision': exam.fechaEmision.strftime('%d/%m/%Y'),
            'fecha_vencimiento': exam.fechaVencimiento.strftime('%d/%m/%Y'),
            'vigente': exam.fechaVencimiento >= date.today(),
            'tiene_documento': bool(exam.rutaDoc),
            'documento_url': exam.rutaDoc.url if exam.rutaDoc else None
        } for exam in examenes]
        
        return JsonResponse({
            'status': 'success',
            'data': info
        })
        
    except Personal.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Personal no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@permission_required_custom('ope_calendario.view_faena')
def limpiar_cache_calendario(request):
    """
    Vista administrativa para limpiar el caché del calendario manualmente.
    Útil cuando se necesita forzar una actualización de los datos después de cambios.
    
    Parámetros:
        request: HttpRequest - Request HTTP
    
    Retorna:
        HttpResponse: Redirección al calendario con mensaje de confirmación
    """
    from django.contrib import messages
    
    current_version = cache.get('calendario_version', 0)
    cache.clear()  # Limpiar todo el caché
    cache.set('calendario_version', 0)  # Resetear versión
    
    messages.success(request, f'Caché del calendario limpiado exitosamente. Versión reseteada de {current_version} a 0.')
    return redirect('calendario:calendario_mensual')


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.add_asignacionfaena', is_ajax=True)
@require_http_methods(["POST"])
def crear_asignacion(request):
    """
    API endpoint para crear una nueva asignación de personal a faena.
    Valida los datos, verifica conflictos con asignaciones existentes y OTs,
    crea la asignación y registra en el historial.
    
    Parámetros POST (JSON):
        personal_id: int - ID del personal a asignar
        faena_id: int - ID de la faena
        turno_id: int - ID del turno
        fecha_inicio: str - Fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Fecha de fin (formato ISO: YYYY-MM-DD, opcional)
        bloque_inicio_id: int - ID del bloque de inicio del turno (opcional)
        observaciones: str - Observaciones opcionales
        activo: bool - Estado activo/inactivo (por defecto: True)
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error y mensaje
    """
    try:
        data = json.loads(request.body)
        
        personal_id = data.get('personal_id')
        faena_id = data.get('faena_id')
        turno_id = data.get('turno_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin', None)
        bloque_inicio_id = data.get('bloque_inicio_id', None)
        observaciones = data.get('observaciones', '')
        activo = data.get('activo', True)
        
        # Validaciones
        if not all([personal_id, faena_id, turno_id, fecha_inicio]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            personal = Personal.objects.get(personal_id=personal_id)
            faena = Faena.objects.get(id=faena_id)
            turno = Turno.objects.get(id=turno_id)
            bloque_inicio = None
            if bloque_inicio_id:
                bloque_inicio = TurnoBloque.objects.get(id=bloque_inicio_id, turno=turno)
        except (Personal.DoesNotExist, Faena.DoesNotExist, Turno.DoesNotExist, TurnoBloque.DoesNotExist):
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
        
        # Verificar solapamiento de fechas con asignaciones existentes
        from django.db.models import Q
        
        # Convertir fechas string a objetos date
        fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_date = None
        if fecha_fin:
            fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Buscar asignaciones a otras faenas que se solapen
        solapamiento_query = Q(personal=personal, activo=True)
        
        if fecha_fin_date:
            # Nueva asignación tiene fecha fin: buscar cualquier solapamiento
            # Dos rangos se solapan si: inicio1 <= fin2 AND inicio2 <= fin1
            solapamiento_query &= (
                Q(fecha_inicio__lte=fecha_fin_date) & 
                (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
            )
        else:
            # Nueva asignación sin fecha fin: buscar asignaciones que estén activas en la fecha de inicio
            # Una asignación sin fin se solapa con cualquier asignación que esté activa en esa fecha
            solapamiento_query &= (
                Q(fecha_inicio__lte=fecha_inicio_date) & 
                (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
            )
        
        asignaciones_solapadas = AsignacionFaena.objects.filter(solapamiento_query).select_related('faena')
        
        if asignaciones_solapadas.exists():
            conflicto = asignaciones_solapadas.first()
            fecha_fin_str = conflicto.fecha_fin.strftime('%d/%m/%Y') if conflicto.fecha_fin else 'Indefinido'
            return JsonResponse({
                'error': f'Las fechas se solapan con una asignación existente en la faena "{conflicto.faena.nombre}" '
                         f'({conflicto.fecha_inicio.strftime("%d/%m/%Y")} → {fecha_fin_str}). '
                         f'Revisa las fechas de las asignaciones actuales.'
            }, status=400)
        
        # Verificar si tiene OT asignadas en fechas que interfieren
        ot_conflictivas = OrdenTrabajo.objects.filter(
            personal_asignado=personal
        ).filter(
            Q(fecha_inicio__isnull=False)
        )
        
        # Verificar solapamiento de fechas con OT
        if fecha_fin_date:
            ot_conflictivas = ot_conflictivas.filter(
                Q(fecha_inicio__lte=fecha_fin_date) & (
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
                )
            )
        else:
            ot_conflictivas = ot_conflictivas.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
            )
        
        ot_conflictivas = ot_conflictivas.select_related('equipo_id').order_by('-fecha_inicio')[:1]
        
        if ot_conflictivas.exists():
            ot_conflicto = ot_conflictivas.first()
            fecha_fin_ot = ot_conflicto.fecha_fin.strftime('%d/%m/%Y') if ot_conflicto.fecha_fin else 'Indefinido'
            fecha_inicio_ot = ot_conflicto.fecha_inicio.strftime('%d/%m/%Y') if ot_conflicto.fecha_inicio else 'N/A'
            equipo_nombre = ot_conflicto.equipo_id.nombreEquipo if ot_conflicto.equipo_id else 'N/A'
            return JsonResponse({
                'error': f'El trabajador tiene una OT asignada "{ot_conflicto.folio}" (Equipo: {equipo_nombre}) '
                         f'que se solapa con las fechas de asignación ({fecha_inicio_ot} → {fecha_fin_ot}). '
                         f'No se puede asignar a la faena en estas fechas.'
            }, status=400)
        
        # Crear nueva asignación
        asignacion = AsignacionFaena.objects.create(
            personal=personal,
            faena=faena,
            turno=turno,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin if fecha_fin else None,
            bloque_inicio=bloque_inicio,
            observaciones=observaciones,
            activo=activo
        )
        
        # Marcar que el historial se registrará manualmente (evitar duplicado en señal)
        asignacion._historial_registrado = True
        
        # Registrar en historial
        HistorialFaena.registrar(
            faena=faena,
            accion='PERSONAL_ASIGNADO',
            descripcion=f"{personal.nombre} {personal.apepat} asignado con turno {turno.nombre} del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y') if fecha_fin else 'indefinido'}",
            usuario=request.user if request.user.is_authenticated else None,
            personal=personal,
            datos_nuevos={
                'personal_id': personal.personal_id,
                'personal_nombre': f"{personal.nombre} {personal.apepat} {personal.apemat}",
                'turno': turno.nombre,
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat() if fecha_fin else None
            }
        )
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación creada correctamente',
            'asignacion_id': asignacion.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.modificar_asignacion_personal', is_ajax=True)
@require_http_methods(["POST"])
def actualizar_asignacion(request):
    """
    API endpoint para actualizar una asignación de personal a faena existente.
    Valida los datos, verifica conflictos, actualiza la asignación y registra en el historial.
    
    Parámetros POST (JSON):
        asignacion_id: int - ID de la asignación a actualizar
        faena_id: int - ID de la faena
        turno_id: int - ID del turno
        fecha_inicio: str - Nueva fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Nueva fecha de fin (formato ISO: YYYY-MM-DD, opcional)
        bloque_inicio_id: int - ID del bloque de inicio (opcional)
        observaciones: str - Observaciones opcionales
        activo: bool - Estado activo/inactivo (opcional)
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error y mensaje
    """
    try:
        data = json.loads(request.body)
        
        asignacion_id = data.get('asignacion_id')
        faena_id = data.get('faena_id')
        turno_id = data.get('turno_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin', None)
        bloque_inicio_id = data.get('bloque_inicio_id', None)
        observaciones = data.get('observaciones', '')
        activo = data.get('activo', True)
        
        # Validaciones
        if not all([asignacion_id, faena_id, turno_id, fecha_inicio]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            asignacion = AsignacionFaena.objects.get(id=asignacion_id)
            faena = Faena.objects.get(id=faena_id)
            turno = Turno.objects.get(id=turno_id)
            bloque_inicio = None
            if bloque_inicio_id:
                bloque_inicio = TurnoBloque.objects.get(id=bloque_inicio_id, turno=turno)
        except (AsignacionFaena.DoesNotExist, Faena.DoesNotExist, Turno.DoesNotExist, TurnoBloque.DoesNotExist):
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
        
        # Verificar solapamiento de fechas con otras asignaciones (excluyendo la actual)
        from django.db.models import Q
        
        # Convertir fechas string a objetos date
        fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_date = None
        if fecha_fin:
            fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Buscar asignaciones que se solapen (excluyendo la que estamos editando)
        solapamiento_query = Q(personal=asignacion.personal, activo=True) & ~Q(id=asignacion.id)
        
        if fecha_fin_date:
            # Asignación editada tiene fecha fin: buscar cualquier solapamiento
            solapamiento_query &= (
                Q(fecha_inicio__lte=fecha_fin_date) & 
                (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
            )
        else:
            # Asignación editada sin fecha fin: buscar asignaciones que empiecen antes o en la fecha de inicio
            solapamiento_query &= (
                Q(fecha_inicio__lte=fecha_inicio_date) & 
                (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
            )
        
        asignaciones_solapadas = AsignacionFaena.objects.filter(solapamiento_query).select_related('faena')
        
        if asignaciones_solapadas.exists():
            conflicto = asignaciones_solapadas.first()
            fecha_fin_str = conflicto.fecha_fin.strftime('%d/%m/%Y') if conflicto.fecha_fin else 'Indefinido'
            return JsonResponse({
                'error': f'Las fechas se solapan con otra asignación existente en la faena "{conflicto.faena.nombre}" '
                         f'({conflicto.fecha_inicio.strftime("%d/%m/%Y")} → {fecha_fin_str}). '
                         f'Revisa las fechas de las asignaciones actuales.'
            }, status=400)
        
        # Verificar si tiene OT asignadas en fechas que interfieren
        ot_conflictivas = OrdenTrabajo.objects.filter(
            personal_asignado=asignacion.personal
        ).filter(
            Q(fecha_inicio__isnull=False)
        )
        
        # Verificar solapamiento de fechas con OT
        if fecha_fin_date:
            ot_conflictivas = ot_conflictivas.filter(
                Q(fecha_inicio__lte=fecha_fin_date) & (
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
                )
            )
        else:
            ot_conflictivas = ot_conflictivas.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
            )
        
        ot_conflictivas = ot_conflictivas.select_related('equipo_id').order_by('-fecha_inicio')[:1]
        
        if ot_conflictivas.exists():
            ot_conflicto = ot_conflictivas.first()
            fecha_fin_ot = ot_conflicto.fecha_fin.strftime('%d/%m/%Y') if ot_conflicto.fecha_fin else 'Indefinido'
            fecha_inicio_ot = ot_conflicto.fecha_inicio.strftime('%d/%m/%Y') if ot_conflicto.fecha_inicio else 'N/A'
            equipo_nombre = ot_conflicto.equipo_id.nombreEquipo if ot_conflicto.equipo_id else 'N/A'
            return JsonResponse({
                'error': f'El trabajador tiene una OT asignada "{ot_conflicto.folio}" (Equipo: {equipo_nombre}) '
                         f'que se solapa con las fechas de asignación ({fecha_inicio_ot} → {fecha_fin_ot}). '
                         f'No se puede asignar a la faena en estas fechas.'
            }, status=400)
        
        # Guardar datos anteriores para historial
        datos_anteriores = {
            'turno': asignacion.turno.nombre,
            'fecha_inicio': asignacion.fecha_inicio.isoformat() if asignacion.fecha_inicio else None,
            'fecha_fin': asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None
        }
        
        # Actualizar asignación
        asignacion.faena = faena
        asignacion.turno = turno
        asignacion.fecha_inicio = fecha_inicio
        asignacion.fecha_fin = fecha_fin if fecha_fin else None
        asignacion.bloque_inicio = bloque_inicio
        asignacion.observaciones = observaciones
        asignacion.activo = activo
        asignacion.save()
        
        # Registrar en historial
        HistorialFaena.registrar(
            faena=faena,
            accion='ASIGNACION_MODIFICADA',
            descripcion=f"Asignación de {asignacion.personal.nombre} {asignacion.personal.apepat} modificada. Turno: {turno.nombre}",
            usuario=request.user if request.user.is_authenticated else None,
            personal=asignacion.personal,
            datos_previos=datos_anteriores,
            datos_nuevos={
                'turno': turno.nombre,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
        )
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación actualizada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.delete_asignacionfaena', is_ajax=True)
@require_http_methods(["POST"])
def eliminar_asignacion(request):
    """
    API endpoint para eliminar una asignación de personal a faena.
    Elimina la asignación físicamente y registra la acción en el historial.
    
    Parámetros POST (JSON):
        asignacion_id: int - ID de la asignación a eliminar
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error y mensaje
    """
    try:
        data = json.loads(request.body)
        asignacion_id = data.get('asignacion_id')
        
        if not asignacion_id:
            return JsonResponse({'error': 'ID de asignación requerido'}, status=400)
        
        try:
            asignacion = AsignacionFaena.objects.select_related('personal', 'faena', 'turno').get(id=asignacion_id)
            
            # Guardar datos antes de eliminar para el historial
            datos_asignacion = {
                'personal_id': asignacion.personal.personal_id,
                'personal_nombre': f"{asignacion.personal.nombre} {asignacion.personal.apepat} {asignacion.personal.apemat}",
                'turno': asignacion.turno.nombre,
                'fecha_inicio': asignacion.fecha_inicio.isoformat(),
                'fecha_fin': asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None
            }
            personal_eliminado = asignacion.personal
            faena_ref = asignacion.faena
            
            # Marcar que el historial se registrará manualmente (evitar duplicado en señal)
            asignacion._historial_registrado = True
            
            # Registrar en historial ANTES de eliminar
            HistorialFaena.registrar(
                faena=faena_ref,
                accion='PERSONAL_ELIMINADO',
                descripcion=f"{personal_eliminado.nombre} {personal_eliminado.apepat} eliminado de la faena. Turno: {asignacion.turno.nombre}",
                usuario=request.user if request.user.is_authenticated else None,
                personal=personal_eliminado,
                datos_previos=datos_asignacion
            )
            
            asignacion.delete()
            
            # Invalidar caché del calendario
            invalidar_cache_calendario()
        except AsignacionFaena.DoesNotExist:
            return JsonResponse({'error': 'Asignación no encontrada'}, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación eliminada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# GESTIÓN DE FAENAS - VISTA PRINCIPAL
# ============================================================================

@login_required
@permission_required_custom('ope_calendario.asignar_personal_faena')
def asignar_personal_faena(request, faena_id):
    """
    Vista para mostrar el formulario de asignación de personal a una faena específica.
    Muestra lista de personal disponible y personal ya asignado, con filtros y paginación.
    Incluye información de conflictos con asignaciones existentes y OTs.
    
    Parámetros:
        request: HttpRequest - Request HTTP
        faena_id: int - ID de la faena para la cual asignar personal
    
    Retorna:
        HttpResponse: Renderiza el template asignar_personal_faena.html con todos los datos necesarios
    """
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Obtener la faena
    try:
        faena = Faena.objects.get(id=faena_id, activo=True)
    except Faena.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Faena no encontrada')
        return redirect('calendario:gestionar_faenas')
    
    # Obtener personal activo con sus asignaciones - optimizado
    from datetime import date
    personal_list = Personal.objects.filter(activo=True).select_related(
        'sexo_id', 'estcivil_id'
    ).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        Prefetch(
            'asignaciones_faena',
            queryset=AsignacionFaena.objects.filter(
                activo=True
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=date.today())
            ).select_related('faena', 'turno'),
            to_attr='asignaciones_activas_prefetch'
        ),
        Prefetch(
            'ordenes_trabajo',
            queryset=OrdenTrabajo.objects.filter(
                fecha_inicio__isnull=False
            ).select_related('estado_ot_id', 'equipo_id'),
            to_attr='ots_prefetch'
        )
    ).order_by('apepat', 'apemat', 'nombre')
    
    # Obtener turnos disponibles
    turnos = Turno.objects.filter(activo=True).prefetch_related(
        'bloques__estado'
    ).order_by('nombre')
    
    # Obtener otras faenas para filtro
    otras_faenas = Faena.objects.filter(activo=True).exclude(id=faena_id).order_by('nombre')
    
    # Preparar datos del personal
    personal_data = []
    cargos_set = set()
    empresas_set = set()
    
    # Precalcular fechas de la faena para evitar repetir en el loop
    faena_inicio = faena.fecha_inicio
    faena_fin = faena.fecha_fin
    
    for p in personal_list:
        # Usar asignaciones ya prefetchadas (evita consultas adicionales)
        asignaciones_activas = getattr(p, 'asignaciones_activas_prefetch', [])
        asignacion_activa = asignaciones_activas[0] if asignaciones_activas else None
        
        # Usar info laboral ya prefetchada (evita consultas adicionales)
        info_laboral = next(iter(p.infolaboral_set.all()), None)
        cargo = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
        empresa = info_laboral.empresa_id.nomFantasia if info_laboral and info_laboral.empresa_id else 'Sin empresa'
        cargos_set.add(cargo)
        empresas_set.add(empresa)
        
        # Verificar si la asignación a faena interfiere con las fechas de esta faena
        tiene_asignacion_conflictiva = False
        asignacion_data = None
        
        if asignacion_activa and faena.fecha_inicio:
            # Determinar el rango de fechas de la asignación
            asig_inicio = asignacion_activa.fecha_inicio
            asig_fin = asignacion_activa.fecha_fin if asignacion_activa.fecha_fin else faena.fecha_fin
            
            # Determinar el rango de fechas de la faena actual
            faena_inicio = faena.fecha_inicio
            faena_fin = faena.fecha_fin if faena.fecha_fin else asig_fin
            
            # Verificar si hay solapamiento de fechas
            if asig_inicio and faena_inicio:
                # Hay solapamiento si:
                # - La asignación comienza antes de que termine la faena Y
                # - La asignación termina después de que comience la faena
                if asig_fin and faena_fin:
                    tiene_asignacion_conflictiva = (asig_inicio <= faena_fin) and (asig_fin >= faena_inicio)
                elif faena_fin:
                    # Si la asignación no tiene fecha fin, solo verificar que comience antes de que termine la faena
                    tiene_asignacion_conflictiva = asig_inicio <= faena_fin
                else:
                    # Si ninguna tiene fecha fin definida, hay conflicto si hay cualquier asignación
                    tiene_asignacion_conflictiva = True
            
            # Solo mostrar datos de asignación si hay conflicto
            if tiene_asignacion_conflictiva:
                asignacion_data = {
                    'tipo': 'faena',
                    'faena': asignacion_activa.faena.nombre,
                    'turno': asignacion_activa.turno.nombre,
                    'fecha_inicio': asignacion_activa.fecha_inicio.isoformat(),
                    'fecha_fin': asignacion_activa.fecha_fin.isoformat() if asignacion_activa.fecha_fin else None
                }
        
        # Verificar si tiene OT asignadas en fechas que interfieren con la faena
        # Usar OTs ya prefetchadas (evita consultas adicionales)
        tiene_ot_asignada = False
        ot_data = None
        
        if faena_inicio:
            # Filtrar OTs prefetchadas que se solapan con las fechas de la faena
            ots_prefetch = getattr(p, 'ots_prefetch', [])
            ot_asignadas = []
            
            for ot in ots_prefetch:
                if ot.fecha_inicio:
                    ot_fin = ot.fecha_fin if ot.fecha_fin else None
                    # Verificar solapamiento
                    if faena_fin:
                        if ot_fin:
                            if ot.fecha_inicio <= faena_fin and ot_fin >= faena_inicio:
                                ot_asignadas.append(ot)
                        else:
                            if ot.fecha_inicio <= faena_fin:
                                ot_asignadas.append(ot)
                    else:
                        if not ot_fin or ot_fin >= faena_inicio:
                            ot_asignadas.append(ot)
            
            if ot_asignadas:
                # Ordenar por fecha_inicio descendente y tomar la primera
                ot_asignadas.sort(key=lambda x: x.fecha_inicio, reverse=True)
                ot = ot_asignadas[0]
                tiene_ot_asignada = True
                ot_data = {
                    'tipo': 'ot',
                    'folio': ot.folio,
                    'equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                    'fecha_inicio': ot.fecha_inicio.isoformat() if ot.fecha_inicio else None,
                    'fecha_fin': ot.fecha_fin.isoformat() if ot.fecha_fin else None
                }
        
        # Si tiene OT asignada, mostrar esa información en lugar de la asignación a faena
        if tiene_ot_asignada:
            tiene_asignacion_conflictiva = True
            asignacion_data = ot_data
        
        personal_data.append({
            'id': p.personal_id,
            'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
            'rut': f"{p.rut}-{p.dvrut}",
            'cargo': cargo,
            'empresa': empresa,
            'tiene_asignacion': tiene_asignacion_conflictiva,
            'asignacion_actual': asignacion_data
        })
    
    # Preparar datos de turnos
    turnos_data = []
    for turno in turnos:
        bloques_data = []
        for bloque in turno.bloques.all().order_by('orden'):
            bloques_data.append({
                'id': bloque.id,
                'orden': bloque.orden,
                'duracion_dias': bloque.duracion_dias,
                'estado': {
                    'id': bloque.estado.id,
                    'nombre': bloque.estado.nombre,
                    'nombre_corto': bloque.estado.nombre_corto or bloque.estado.nombre,
                    'color': bloque.estado.color,
                    'background_color': bloque.estado.background_color
                }
            })
        
        turnos_data.append({
            'id': turno.id,
            'nombre': turno.nombre,
            'descripcion': turno.descripcion or '',
            'bloques': bloques_data,
            'longitud_ciclo': sum([b.duracion_dias for b in turno.bloques.all()])
        })
    
    # Obtener asignaciones activas de la faena (solo personal activo)
    asignaciones_faena = faena.asignaciones.filter(
        activo=True,
        personal__activo=True  # Filtrar solo personal activo
    ).select_related(
        'personal', 'turno', 'bloque_inicio'
    ).prefetch_related('turno__bloques')
    
    # Preparar datos de asignaciones
    asignaciones_data = []
    for asig in asignaciones_faena:
        asignaciones_data.append({
            'id': asig.id,
            'personal': {
                'id': asig.personal.personal_id,
                'nombre': f"{asig.personal.nombre} {asig.personal.apepat} {asig.personal.apemat}",
                'rut': f"{asig.personal.rut}-{asig.personal.dvrut}",
                'cargo': asig.personal.infolaboral_set.first().cargo_id.cargo if asig.personal.infolaboral_set.exists() else 'Sin cargo',
                'empresa': asig.personal.infolaboral_set.first().empresa_id.nomFantasia if asig.personal.infolaboral_set.exists() and asig.personal.infolaboral_set.first().empresa_id else 'Sin empresa'
            },
            'turno': {
                'id': asig.turno.id,
                'nombre': asig.turno.nombre
            },
            'bloque_inicio': {
                'id': asig.bloque_inicio.id,
                'orden': asig.bloque_inicio.orden,
                'duracion_dias': asig.bloque_inicio.duracion_dias,
                'estado_nombre': asig.bloque_inicio.estado.nombre
            } if asig.bloque_inicio else None,
            'fecha_inicio': asig.fecha_inicio.isoformat(),
            'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
            'observaciones': asig.observaciones or ''
        })
    
    # Preparar datos de la faena
    faena_data = {
        'id': faena.id,
        'nombre': faena.nombre,
        'descripcion': faena.descripcion or '',
        'asignaciones': asignaciones_data
    }
    
    # Contar asignados actuales
    total_asignados = len(asignaciones_data)
    
    # Obtener estados manuales de esta faena (solo personal activo)
    estados_manuales_faena = EstadoManual.objects.filter(
        faena=faena,
        personal__activo=True  # Filtrar solo personal activo
    ).select_related(
        'personal', 
        'estado'
    ).prefetch_related(
        'personal__infolaboral_set__cargo_id',
        'personal__infolaboral_set__empresa_id'
    ).order_by('-fecha_inicio', 'personal__apepat')
    
    # Agregar información de días a cada estado manual
    estados_manuales_list = []
    for estado in estados_manuales_faena:
        dias_duracion = (estado.fecha_fin - estado.fecha_inicio).days + 1
        estados_manuales_list.append({
            'estado': estado,
            'dias_duracion': dias_duracion
        })
    
    total_estados_manuales = len(estados_manuales_list)
    
    # Calcular duración si tiene ambas fechas
    duracion_dias = None
    if faena.fecha_inicio and faena.fecha_fin:
        duracion_dias = (faena.fecha_fin - faena.fecha_inicio).days + 1
    
    # Obtener estados disponibles para asignación manual (no bloqueantes ni predeterminados)
    estados_disponibles = Estado.objects.filter(
        es_bloqueante=False,
        es_predeterminado=False
    ).order_by('nombre')
    
    context = {
        'faena_id': faena_id,
        'faena_codigo': faena.codigo,
        'faena_nombre': faena.nombre,
        'faena_descripcion': faena.descripcion,
        'faena_fecha_inicio': faena.fecha_inicio,
        'faena_fecha_fin': faena.fecha_fin,
        'faena_duracion_dias': duracion_dias,
        'total_asignados': total_asignados,
        'estados_manuales': estados_manuales_list,
        'total_estados_manuales': total_estados_manuales,
        'estados_disponibles': estados_disponibles,
        'personal_json': json.dumps(personal_data, cls=DjangoJSONEncoder),
        'turnos_json': json.dumps(turnos_data, cls=DjangoJSONEncoder),
        'faena_json': json.dumps(faena_data, cls=DjangoJSONEncoder),
        'cargos_unicos': sorted(cargos_set),
        'empresas_unicas': sorted(empresas_set),
        'otras_faenas': otras_faenas,
        'faena': faena,  # Pasar el objeto completo también
    }
    
    return render(request, 'calendario/asignar_personal_faena.html', context)


@login_required
@permission_required_custom('ope_calendario.asignar_equipos_faena')
def asignar_equipos_faena(request, faena_id):
    """
    Vista para mostrar el formulario de asignación de equipos a una faena específica.
    Muestra lista de equipos disponibles y equipos ya asignados, con filtros y paginación.
    Incluye información de conflictos con asignaciones existentes y OTs.
    
    Parámetros:
        request: HttpRequest - Request HTTP
        faena_id: int - ID de la faena para la cual asignar equipos
    
    Retorna:
        HttpResponse: Renderiza el template asignar_equipos_faena.html con todos los datos necesarios
    """
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Obtener la faena
    try:
        faena = Faena.objects.get(id=faena_id, activo=True)
    except Faena.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Faena no encontrada')
        return redirect('calendario:gestionar_faenas')
    
    # Obtener equipos activos con sus asignaciones - optimizado
    equipos_list = Equipo.objects.filter(activo=True).select_related(
        'empresa_id', 'modeloEquipo_id__tipoEquipo_id', 'modeloEquipo_id__marcaEquipo_id'
    ).prefetch_related(
        Prefetch(
            'asignaciones_faena',
            queryset=AsignacionEquipoFaena.objects.filter(
                activo=True
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=date.today())
            ).select_related('faena'),
            to_attr='asignaciones_activas_prefetch'
        ),
        Prefetch(
            'ordenes_trabajo',
            queryset=OrdenTrabajo.objects.filter(
                fecha_inicio__isnull=False
            ).select_related('estado_ot_id', 'equipo_id'),
            to_attr='ots_prefetch'
        )
    ).order_by('codigoInterno', 'nombreEquipo')
    
    # Obtener otras faenas para filtro
    otras_faenas = Faena.objects.filter(activo=True).exclude(id=faena_id).order_by('nombre')
    
    # Preparar datos de los equipos
    equipos_data = []
    empresas_set = set()
    tipos_set = set()
    
    # Precalcular fechas de la faena para evitar repetir en el loop
    faena_inicio_eq = faena.fecha_inicio
    faena_fin_eq = faena.fecha_fin
    
    for eq in equipos_list:
        # Usar asignaciones ya prefetchadas (evita consultas adicionales)
        asignaciones_activas = getattr(eq, 'asignaciones_activas_prefetch', [])
        asignacion_activa = asignaciones_activas[0] if asignaciones_activas else None
        
        empresa = eq.empresa_id.nomFantasia if eq.empresa_id else 'Sin empresa'
        tipo = eq.modeloEquipo_id.tipoEquipo_id.tipoEquipo if eq.modeloEquipo_id and eq.modeloEquipo_id.tipoEquipo_id else 'Sin tipo'
        empresas_set.add(empresa)
        tipos_set.add(tipo)
        
        # Verificar si la asignación a faena interfiere con las fechas de esta faena
        tiene_asignacion_conflictiva = False
        asignacion_data = None
        
        if asignacion_activa and faena.fecha_inicio:
            # Determinar el rango de fechas de la asignación
            asig_inicio = asignacion_activa.fecha_inicio
            asig_fin = asignacion_activa.fecha_fin if asignacion_activa.fecha_fin else faena.fecha_fin
            
            # Determinar el rango de fechas de la faena actual
            faena_inicio = faena.fecha_inicio
            faena_fin = faena.fecha_fin if faena.fecha_fin else asig_fin
            
            # Verificar si hay solapamiento de fechas
            if asig_inicio and faena_inicio:
                # Hay solapamiento si:
                # - La asignación comienza antes de que termine la faena Y
                # - La asignación termina después de que comience la faena
                if asig_fin and faena_fin:
                    tiene_asignacion_conflictiva = (asig_inicio <= faena_fin) and (asig_fin >= faena_inicio)
                elif faena_fin:
                    # Si la asignación no tiene fecha fin, solo verificar que comience antes de que termine la faena
                    tiene_asignacion_conflictiva = asig_inicio <= faena_fin
                else:
                    # Si ninguna tiene fecha fin definida, hay conflicto si hay cualquier asignación
                    tiene_asignacion_conflictiva = True
            
            # Solo mostrar datos de asignación si hay conflicto
            if tiene_asignacion_conflictiva:
                asignacion_data = {
                    'tipo': 'faena',
                    'faena': asignacion_activa.faena.nombre,
                    'fecha_inicio': asignacion_activa.fecha_inicio.isoformat(),
                    'fecha_fin': asignacion_activa.fecha_fin.isoformat() if asignacion_activa.fecha_fin else None
                }
        
        # Verificar si tiene OT asignadas en fechas que interfieren con la faena
        # Usar OTs ya prefetchadas (evita consultas adicionales)
        tiene_ot_asignada = False
        ot_data = None
        
        if faena_inicio_eq:
            # Filtrar OTs prefetchadas que se solapan con las fechas de la faena
            ots_prefetch = getattr(eq, 'ots_prefetch', [])
            ot_asignadas = []
            
            for ot in ots_prefetch:
                if ot.fecha_inicio:
                    ot_fin = ot.fecha_fin if ot.fecha_fin else None
                    # Verificar solapamiento
                    if faena_fin_eq:
                        if ot_fin:
                            if ot.fecha_inicio <= faena_fin_eq and ot_fin >= faena_inicio_eq:
                                ot_asignadas.append(ot)
                        else:
                            if ot.fecha_inicio <= faena_fin_eq:
                                ot_asignadas.append(ot)
                    else:
                        if not ot_fin or ot_fin >= faena_inicio_eq:
                            ot_asignadas.append(ot)
            
            if ot_asignadas:
                # Ordenar por fecha_inicio descendente y tomar la primera
                ot_asignadas.sort(key=lambda x: x.fecha_inicio, reverse=True)
                ot = ot_asignadas[0]
                tiene_ot_asignada = True
                ot_data = {
                    'tipo': 'ot',
                    'folio': ot.folio,
                    'fecha_inicio': ot.fecha_inicio.isoformat() if ot.fecha_inicio else None,
                    'fecha_fin': ot.fecha_fin.isoformat() if ot.fecha_fin else None
                }
        
        # Si tiene OT asignada, mostrar esa información en lugar de la asignación a faena
        if tiene_ot_asignada:
            tiene_asignacion_conflictiva = True
            asignacion_data = ot_data
        
        equipos_data.append({
            'id': eq.equipo_id,
            'codigo_interno': eq.codigoInterno,
            'nombre': eq.nombreEquipo,
            'patente': eq.patente or '',
            'empresa': empresa,
            'tipo': tipo,
            'modelo': eq.modeloEquipo_id.modeloEquipo if eq.modeloEquipo_id else 'N/A',
            'marca': eq.modeloEquipo_id.marcaEquipo_id.marcaEquipo if eq.modeloEquipo_id and eq.modeloEquipo_id.marcaEquipo_id else 'N/A',
            'tiene_asignacion': tiene_asignacion_conflictiva,
            'asignacion_actual': asignacion_data
        })
    
    # Obtener asignaciones activas de equipos a la faena
    asignaciones_equipos = faena.asignaciones_equipos.filter(
        activo=True,
        equipo__activo=True
    ).select_related('equipo__empresa_id', 'equipo__modeloEquipo_id__tipoEquipo_id', 'equipo__modeloEquipo_id__marcaEquipo_id')
    
    # Preparar datos de asignaciones
    asignaciones_data = []
    for asig in asignaciones_equipos:
        asignaciones_data.append({
            'id': asig.id,
            'equipo': {
                'id': asig.equipo.equipo_id,
                'codigo_interno': asig.equipo.codigoInterno,
                'nombre': asig.equipo.nombreEquipo,
                'patente': asig.equipo.patente or '',
                'empresa': asig.equipo.empresa_id.nomFantasia if asig.equipo.empresa_id else 'Sin empresa',
                'tipo': asig.equipo.modeloEquipo_id.tipoEquipo_id.tipoEquipo if asig.equipo.modeloEquipo_id and asig.equipo.modeloEquipo_id.tipoEquipo_id else 'Sin tipo',
                'modelo': asig.equipo.modeloEquipo_id.modeloEquipo if asig.equipo.modeloEquipo_id else 'N/A',
                'marca': asig.equipo.modeloEquipo_id.marcaEquipo_id.marcaEquipo if asig.equipo.modeloEquipo_id and asig.equipo.modeloEquipo_id.marcaEquipo_id else 'N/A'
            },
            'fecha_inicio': asig.fecha_inicio.isoformat(),
            'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
            'observaciones': asig.observaciones or ''
        })
    
    # Obtener todas las asignaciones activas de equipos a otras faenas (para validación dinámica en frontend)
    # Esto permite validar conflictos cuando el usuario selecciona fechas específicas
    todas_asignaciones_equipos = AsignacionEquipoFaena.objects.filter(
        activo=True,
        equipo__activo=True
    ).exclude(
        faena=faena  # Excluir asignaciones de esta faena
    ).select_related('equipo', 'faena').order_by('equipo', 'fecha_inicio')
    
    # Preparar datos de todas las asignaciones para validación en frontend
    todas_asignaciones_data = []
    for asig in todas_asignaciones_equipos:
        todas_asignaciones_data.append({
            'equipo_id': asig.equipo.equipo_id,
            'faena_id': asig.faena.id,
            'faena_nombre': asig.faena.nombre,
            'fecha_inicio': asig.fecha_inicio.isoformat(),
            'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
            'tipo': 'faena'
        })
    
    # También incluir OTs activas para validación
    ots_activas = OrdenTrabajo.objects.filter(
        fecha_inicio__isnull=False
    ).exclude(
        estado_ot_id__nombre__iexact='FINALIZADA'
    ).exclude(
        estado_ot_id__nombre__iexact='CANCELADA'
    ).select_related('equipo_id').order_by('equipo_id', 'fecha_inicio')

    for ot in ots_activas:
        todas_asignaciones_data.append({
            'equipo_id': ot.equipo_id.equipo_id,
            'faena_id': None,  # No aplica para OT
            'faena_nombre': f"OT: {ot.folio}",
            'fecha_inicio': ot.fecha_inicio.isoformat(),
            'fecha_fin': ot.fecha_fin.isoformat() if ot.fecha_fin else None,
            'tipo': 'ot'
        })
    
    # Preparar datos de la faena
    faena_data = {
        'id': faena.id,
        'nombre': faena.nombre,
        'descripcion': faena.descripcion or '',
        'asignaciones': asignaciones_data
    }
    
    # Contar asignados actuales
    total_asignados = len(asignaciones_data)
    
    # Calcular duración si tiene ambas fechas
    duracion_dias = None
    if faena.fecha_inicio and faena.fecha_fin:
        duracion_dias = (faena.fecha_fin - faena.fecha_inicio).days + 1
    
    context = {
        'faena_id': faena_id,
        'faena_codigo': faena.codigo,
        'faena_nombre': faena.nombre,
        'faena_descripcion': faena.descripcion,
        'faena_fecha_inicio': faena.fecha_inicio,
        'faena_fecha_fin': faena.fecha_fin,
        'faena_duracion_dias': duracion_dias,
        'total_asignados': total_asignados,
        'equipos_json': json.dumps(equipos_data, cls=DjangoJSONEncoder),
        'faena_json': json.dumps(faena_data, cls=DjangoJSONEncoder),
        'todas_asignaciones_equipos_json': json.dumps(todas_asignaciones_data, cls=DjangoJSONEncoder),
        'empresas_unicas': sorted(empresas_set),
        'tipos_unicos': sorted(tipos_set),
        'otras_faenas': otras_faenas,
        'faena': faena,
    }
    
    return render(request, 'calendario/asignar_equipos_faena.html', context)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.add_asignacionequipofaena', is_ajax=True)
@require_http_methods(["POST"])
def crear_asignacion_equipos(request):
    """
    API endpoint para crear asignaciones masivas de equipos a faena.
    Permite asignar múltiples equipos a una faena en una sola operación.
    Valida conflictos con asignaciones existentes y OTs antes de crear.
    
    Parámetros POST (JSON):
        faena_id: int - ID de la faena
        equipos_ids: list - Lista de IDs de equipos a asignar
        fecha_inicio: str - Fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Fecha de fin (formato ISO: YYYY-MM-DD, opcional)
        observaciones: str - Observaciones opcionales
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, cantidad de asignaciones creadas y lista de errores
    """
    try:
        data = json.loads(request.body)
        
        faena_id = data.get('faena_id')
        equipos_ids = data.get('equipos_ids', [])
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        observaciones = data.get('observaciones', '')
        
        if not faena_id or not equipos_ids or not fecha_inicio:
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            faena = Faena.objects.get(id=faena_id, activo=True)
        except Faena.DoesNotExist:
            return JsonResponse({'error': 'Faena no encontrada'}, status=404)
        
        # Validar y convertir fechas
        from datetime import datetime
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
        
        if fecha_fin_obj and fecha_fin_obj < fecha_inicio_obj:
            return JsonResponse({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}, status=400)
        
        # Verificar conflictos y crear asignaciones
        asignaciones_creadas = 0
        errores = []
        
        for equipo_id in equipos_ids:
            try:
                equipo = Equipo.objects.get(equipo_id=equipo_id, activo=True)
            except Equipo.DoesNotExist:
                errores.append(f'Equipo ID {equipo_id}: No encontrado')
                continue
            
            # Verificar conflictos con otras asignaciones de faena
            asignaciones_conflictivas = AsignacionEquipoFaena.objects.filter(
                equipo=equipo,
                activo=True
            ).exclude(
                faena=faena
            ).filter(
                fecha_inicio__lte=(fecha_fin_obj if fecha_fin_obj else fecha_inicio_obj)
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_obj)
            )
            
            if asignaciones_conflictivas.exists():
                asignacion_conflicto = asignaciones_conflictivas.first()
                fecha_fin_texto = asignacion_conflicto.fecha_fin.strftime('%d/%m/%Y') if asignacion_conflicto.fecha_fin else 'Indefinido'
                errores.append(
                    f"{equipo.nombreEquipo} ({equipo.codigoInterno}): "
                    f"Ya asignado en faena '{asignacion_conflicto.faena.nombre}' "
                    f"({asignacion_conflicto.fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin_texto})"
                )
                continue
            
            # Verificar conflictos con OT
            ot_conflictivas = OrdenTrabajo.objects.filter(
                equipo_id=equipo
            ).filter(
                Q(fecha_inicio__lte=(fecha_fin_obj if fecha_fin_obj else fecha_inicio_obj)) & (
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_obj)
                )
            )
            
            if ot_conflictivas.exists():
                ot_conflicto = ot_conflictivas.first()
                fecha_fin_ot = ot_conflicto.fecha_fin.strftime('%d/%m/%Y') if ot_conflicto.fecha_fin else 'Indefinido'
                errores.append(
                    f"{equipo.nombreEquipo} ({equipo.codigoInterno}): "
                    f"Tiene OT asignada ({ot_conflicto.folio}) "
                    f"({ot_conflicto.fecha_inicio.strftime('%d/%m/%Y') if ot_conflicto.fecha_inicio else 'N/A'} → {fecha_fin_ot})"
                )
                continue
            
            # Crear asignación
            AsignacionEquipoFaena.objects.create(
                equipo=equipo,
                faena=faena,
                fecha_inicio=fecha_inicio_obj,
                fecha_fin=fecha_fin_obj,
                observaciones=observaciones,
                activo=True
            )
            
            # Registrar en historial
            HistorialFaena.registrar(
                faena=faena,
                accion='EQUIPO_ASIGNADO',
                descripcion=f"Equipo {equipo.nombreEquipo} ({equipo.codigoInterno}) asignado. Fechas: {fecha_inicio_obj.strftime('%d/%m/%Y')} → {fecha_fin_obj.strftime('%d/%m/%Y') if fecha_fin_obj else 'Indefinida'}",
                usuario=request.user if request.user.is_authenticated else None,
                datos_nuevos={
                    'equipo_id': equipo.equipo_id,
                    'equipo_nombre': equipo.nombreEquipo,
                    'equipo_codigo': equipo.codigoInterno,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                }
            )
            
            asignaciones_creadas += 1
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        if len(errores) > 0 and asignaciones_creadas == 0:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo asignar ningún equipo',
                'errores': errores
            }, status=400)
        
        mensaje = f'{asignaciones_creadas} equipo(s) asignado(s) correctamente'
        if errores:
            mensaje += f'. {len(errores)} equipo(s) no se pudieron asignar por conflictos.'
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'asignaciones_creadas': asignaciones_creadas,
            'errores': errores
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.delete_asignacionequipofaena', is_ajax=True)
@require_http_methods(["POST"])
def eliminar_asignacion_equipo(request):
    """
    API endpoint para eliminar una asignación de equipo a faena.
    Desactiva la asignación (soft delete) y registra la acción en el historial.
    
    Parámetros POST (JSON):
        asignacion_id: int - ID de la asignación a eliminar
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error y mensaje
    """
    try:
        data = json.loads(request.body)
        asignacion_id = data.get('asignacion_id')
        
        if not asignacion_id:
            return JsonResponse({'error': 'ID de asignación requerido'}, status=400)
        
        try:
            asignacion = AsignacionEquipoFaena.objects.get(id=asignacion_id, activo=True)
        except AsignacionEquipoFaena.DoesNotExist:
            return JsonResponse({'error': 'Asignación no encontrada'}, status=404)
        
        equipo = asignacion.equipo
        faena = asignacion.faena
        
        # Registrar en historial antes de eliminar
        HistorialFaena.registrar(
            faena=faena,
            accion='EQUIPO_ELIMINADO',
            descripcion=f"Equipo {equipo.nombreEquipo} ({equipo.codigoInterno}) eliminado de la faena",
            usuario=request.user if request.user.is_authenticated else None,
            datos_previos={
                'equipo_id': equipo.equipo_id,
                'equipo_nombre': equipo.nombreEquipo,
                'equipo_codigo': equipo.codigoInterno,
                'fecha_inicio': asignacion.fecha_inicio.isoformat(),
                'fecha_fin': asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None
            }
        )
        
        # Desactivar asignación (soft delete)
        asignacion.activo = False
        asignacion.save()
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación eliminada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.modificar_asignacion_equipo', is_ajax=True)
@require_http_methods(["POST"])
def actualizar_asignacion_equipo(request):
    """
    API endpoint para actualizar una asignación de equipo a faena existente.
    Valida los datos, verifica conflictos, actualiza la asignación y registra en el historial.
    
    Parámetros POST (JSON):
        asignacion_id: int - ID de la asignación a actualizar
        faena_id: int - ID de la faena
        fecha_inicio: str - Nueva fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Nueva fecha de fin (formato ISO: YYYY-MM-DD, opcional)
        observaciones: str - Observaciones opcionales
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error y mensaje
    """
    try:
        data = json.loads(request.body)
        
        asignacion_id = data.get('asignacion_id')
        faena_id = data.get('faena_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin', None)
        observaciones = data.get('observaciones', '')
        
        # Validaciones
        if not all([asignacion_id, faena_id, fecha_inicio]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            asignacion = AsignacionEquipoFaena.objects.get(id=asignacion_id, activo=True)
            faena = Faena.objects.get(id=faena_id)
        except (AsignacionEquipoFaena.DoesNotExist, Faena.DoesNotExist):
            return JsonResponse({'error': 'Asignación o faena no encontrada'}, status=404)
        
        # Validar y convertir fechas
        from datetime import datetime
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_obj = None
        if fecha_fin:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        if fecha_fin_obj and fecha_fin_obj < fecha_inicio_obj:
            return JsonResponse({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}, status=400)
        
        # Verificar solapamiento de fechas con otras asignaciones (excluyendo la actual)
        from django.db.models import Q
        
        # Buscar asignaciones que se solapen (excluyendo la que estamos editando)
        # Usar equipo_id en lugar de equipo para evitar joins innecesarios que causan confusión con el campo 'activo'
        solapamiento_query = Q(equipo_id=asignacion.equipo.equipo_id) & Q(activo=True) & ~Q(id=asignacion.id)
        
        if fecha_fin_obj:
            # Rango con fecha fin: buscar solapamientos
            solapamiento_query &= (
                Q(fecha_inicio__lte=fecha_fin_obj, fecha_fin__gte=fecha_inicio_obj) |
                Q(fecha_inicio__lte=fecha_fin_obj, fecha_fin__isnull=True)
            )
        else:
            # Rango sin fecha fin: buscar cualquier asignación que empiece antes o durante
            solapamiento_query &= Q(fecha_inicio__lte=fecha_inicio_obj) & (
                Q(fecha_fin__gte=fecha_inicio_obj) | Q(fecha_fin__isnull=True)
            )
        
        # Excluir asignaciones de la misma faena
        solapamiento_query &= ~Q(faena=faena)
        
        solapamientos = AsignacionEquipoFaena.objects.filter(solapamiento_query)
        
        if solapamientos.exists():
            conflictos = []
            for solap in solapamientos:
                ffin_str = solap.fecha_fin.strftime('%d/%m/%Y') if solap.fecha_fin else 'Indefinida'
                conflictos.append(f"{solap.faena.nombre} ({solap.fecha_inicio.strftime('%d/%m/%Y')} → {ffin_str})")
            
            return JsonResponse({
                'error': f'El equipo ya está asignado a otra faena en ese período: {", ".join(conflictos)}'
            }, status=400)
        
        # Guardar datos anteriores para historial
        datos_anteriores = {
            'equipo_id': asignacion.equipo.equipo_id,
            'equipo_nombre': asignacion.equipo.nombreEquipo,
            'equipo_codigo': asignacion.equipo.codigoInterno,
            'fecha_inicio': asignacion.fecha_inicio.isoformat(),
            'fecha_fin': asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None,
            'observaciones': asignacion.observaciones
        }
        
        # Actualizar asignación
        asignacion.fecha_inicio = fecha_inicio_obj
        asignacion.fecha_fin = fecha_fin_obj
        asignacion.observaciones = observaciones
        asignacion.save()
        
        # Registrar en historial
        HistorialFaena.registrar(
            faena=faena,
            accion='EQUIPO_MODIFICADO',
            descripcion=f"Asignación de equipo {asignacion.equipo.nombreEquipo} ({asignacion.equipo.codigoInterno}) modificada. Fechas: {fecha_inicio_obj.strftime('%d/%m/%Y')} → {fecha_fin_obj.strftime('%d/%m/%Y') if fecha_fin_obj else 'Indefinida'}",
            usuario=request.user if request.user.is_authenticated else None,
            datos_previos=datos_anteriores,
            datos_nuevos={
                'equipo_id': asignacion.equipo.equipo_id,
                'equipo_nombre': asignacion.equipo.nombreEquipo,
                'equipo_codigo': asignacion.equipo.codigoInterno,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'observaciones': observaciones
            }
        )
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación de equipo actualizada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required_custom('ope_calendario.view_faena')
def gestionar_faenas(request):
    """
    Vista principal para gestionar faenas (listar, crear, editar, eliminar).
    Muestra lista de faenas con opciones de filtrado y búsqueda.
    Incluye información de asignaciones de personal y equipos.
    
    Retorna:
        HttpResponse: Renderiza el template gestionar_faenas.html con la lista de faenas
    """
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Obtener todas las faenas activas
    faenas = Faena.objects.filter(activo=True).prefetch_related(
        'asignaciones__personal',
        'asignaciones__turno__bloques__estado',
        'asignaciones__bloque_inicio'
    ).order_by('nombre')
    
    # Obtener todo el personal activo para asignar (optimizado)
    personal = Personal.objects.filter(activo=True).select_related(
        'sexo_id', 'estcivil_id'
    ).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        Prefetch(
            'asignaciones_faena',
            queryset=AsignacionFaena.objects.filter(activo=True).select_related('faena')
        )
    ).order_by('apepat', 'apemat', 'nombre')
    
    # Obtener turnos disponibles
    turnos = Turno.objects.filter(activo=True).prefetch_related(
        'bloques__estado'
    ).order_by('nombre')
    
    # Preparar datos para JSON (optimizado)
    # Usar asignaciones ya prefetchadas en lugar de hacer consultas adicionales
    faenas_data = []
    for faena in faenas:
        # Las asignaciones ya vienen en prefetch_related, usar directamente
        asignaciones_activas = [a for a in faena.asignaciones.all() 
                               if a.activo and a.personal.activo]
        
        # Pre-contar para evitar count() en cada iteración
        total_personal = len(asignaciones_activas)
        
        asignaciones_list = []
        for asig in asignaciones_activas:
            # Obtener info laboral de forma eficiente (ya viene en prefetch)
            info_laboral = next(iter(asig.personal.infolaboral_set.all()), None)
            cargo = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
            
            asignaciones_list.append({
                'id': asig.id,
                'personal': {
                    'id': asig.personal.personal_id,
                    'nombre': f"{asig.personal.nombre} {asig.personal.apepat} {asig.personal.apemat}",
                    'rut': f"{asig.personal.rut}-{asig.personal.dvrut}",
                    'cargo': cargo
                },
                'turno': {
                    'id': asig.turno.id,
                    'nombre': asig.turno.nombre
                },
                'fecha_inicio': asig.fecha_inicio.isoformat(),
                'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
                'bloque_inicio': {
                    'id': asig.bloque_inicio.id,
                    'orden': asig.bloque_inicio.orden,
                    'estado_nombre': asig.bloque_inicio.estado.nombre
                } if asig.bloque_inicio else None,
                'observaciones': asig.observaciones or '',
                'activo': asig.activo
            })
        
        faenas_data.append({
            'id': faena.id,
            'codigo': faena.codigo,
            'nombre': faena.nombre,
            'ubicacion': faena.ubicacion or '',
            'descripcion': faena.descripcion or '',
            'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
            'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None,
            'activo': faena.activo,
            'total_personal': total_personal,
            'asignaciones': asignaciones_list
        })
    
    # Preparar personal para JSON (optimizado)
    personal_data = []
    for p in personal:
        # Obtener info laboral una sola vez (ya viene en prefetch)
        info_laboral = next(iter(p.infolaboral_set.all()), None)
        cargo = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
        empresa = info_laboral.empresa_id.razonSocial if info_laboral and info_laboral.empresa_id else 'Sin empresa'
        
        # Obtener asignaciones activas (ya viene en prefetch)
        asignaciones_activas = [a for a in p.asignaciones_faena.all() 
                               if a.activo and (not a.fecha_fin or a.fecha_fin >= date.today())]
        tiene_asignacion = len(asignaciones_activas) > 0
        
        personal_data.append({
            'id': p.personal_id,
            'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
            'rut': f"{p.rut}-{p.dvrut}",
            'cargo': cargo,
            'empresa': empresa,
            'tiene_asignacion': tiene_asignacion,
            'asignacion_actual': {
                'faena': asignaciones_activas[0].faena.nombre if asignaciones_activas else None
            } if tiene_asignacion else None
        })
    
    # Preparar turnos para JSON
    turnos_data = []
    for turno in turnos:
        bloques_data = []
        for bloque in turno.bloques.all().order_by('orden'):
            bloques_data.append({
                'id': bloque.id,
                'orden': bloque.orden,
                'duracion_dias': bloque.duracion_dias,
                'estado': {
                    'id': bloque.estado.id,
                    'nombre': bloque.estado.nombre,
                    'nombre_corto': bloque.estado.nombre_corto or bloque.estado.nombre,
                    'color': bloque.estado.color,
                    'background_color': bloque.estado.background_color
                }
            })
        
        turnos_data.append({
            'id': turno.id,
            'nombre': turno.nombre,
            'descripcion': turno.descripcion or '',
            'bloques': bloques_data,
            'longitud_ciclo': sum([b.duracion_dias for b in turno.bloques.all()])
        })
    
    # Verificar permisos del usuario para pasar al template
    user = request.user
    permisos = {
        'can_add_faena': user.has_perm('ope_calendario.add_faena'),
        'can_change_faena': user.has_perm('ope_calendario.change_faena'),
        'can_delete_faena': user.has_perm('ope_calendario.delete_faena'),
        'can_view_faena': user.has_perm('ope_calendario.view_faena'),
        'can_add_asignacionfaena': user.has_perm('ope_calendario.add_asignacionfaena'),
        'can_add_asignacionequipofaena': user.has_perm('ope_calendario.add_asignacionequipofaena'),
        'can_ver_historial_faena': user.has_perm('ope_calendario.ver_historial_faena') or user.has_perm('ope_calendario.view_historialfaena'),
    }
    
    context = {
        'faenas_json': json.dumps(faenas_data, cls=DjangoJSONEncoder),
        'personal_json': json.dumps(personal_data, cls=DjangoJSONEncoder),
        'turnos_json': json.dumps(turnos_data, cls=DjangoJSONEncoder),
        'total_faenas': len(faenas_data),
        'total_personal': len(personal_data),
        'permisos_json': json.dumps(permisos),
    }
    
    return render(request, 'calendario/gestionar_faenas.html', context)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.add_faena', is_ajax=True)
@require_http_methods(["POST"])
def crear_faena(request):
    """
    API endpoint para crear una nueva faena.
    Valida los datos, verifica que el código sea único, crea la faena y registra en el historial.
    
    Parámetros POST (JSON):
        codigo: str - Código único de la faena (se convierte a mayúsculas)
        nombre: str - Nombre de la faena
        ubicacion: str - Ubicación (opcional)
        descripcion: str - Descripción (opcional)
        fecha_inicio: str - Fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Fecha de fin (formato ISO: YYYY-MM-DD)
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, mensaje y datos de la faena creada
    """
    try:
        data = json.loads(request.body)
        
        codigo = data.get('codigo', '').upper()
        nombre = data.get('nombre')
        ubicacion = data.get('ubicacion', '')
        descripcion = data.get('descripcion', '')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if not codigo:
            return JsonResponse({'error': 'El código de la faena es requerido'}, status=400)
        
        if not nombre:
            return JsonResponse({'error': 'El nombre de la faena es requerido'}, status=400)
        
        if not fecha_inicio:
            return JsonResponse({'error': 'La fecha de inicio es requerida'}, status=400)
        
        if not fecha_fin:
            return JsonResponse({'error': 'La fecha de fin es requerida'}, status=400)
        
        # Verificar si ya existe una faena con ese código
        if Faena.objects.filter(codigo__iexact=codigo).exists():
            return JsonResponse({'error': 'Ya existe una faena con ese código'}, status=400)
        
        # Convertir y validar fechas
        from datetime import datetime
        fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Validar que fecha fin sea posterior a fecha inicio
        if fecha_fin_date < fecha_inicio_date:
            return JsonResponse({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}, status=400)
        
        faena = Faena.objects.create(
            codigo=codigo,
            nombre=nombre,
            ubicacion=ubicacion,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date,
            activo=True
        )
        
        # Registrar en historial
        HistorialFaena.registrar(
            faena=faena,
            accion='FAENA_CREADA',
            descripcion=f"Faena '{faena.nombre}' creada del {fecha_inicio_date.strftime('%d/%m/%Y')} al {fecha_fin_date.strftime('%d/%m/%Y')}",
            usuario=request.user if request.user.is_authenticated else None,
            datos_nuevos={
                'codigo': codigo,
                'nombre': nombre,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'descripcion': descripcion
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Faena creada exitosamente',
            'faena': {
                'id': faena.id,
                'codigo': faena.codigo,
                'nombre': faena.nombre,
                'ubicacion': faena.ubicacion,
                'descripcion': faena.descripcion,
                'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
                'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.change_faena', is_ajax=True)
@require_http_methods(["POST"])
def actualizar_faena(request):
    """
    API endpoint para actualizar una faena existente y ajustar asignaciones automáticamente.
    Valida los datos, actualiza la faena, ajusta asignaciones que coincidan con las fechas anteriores
    y registra todos los cambios en el historial.
    
    Parámetros POST (JSON):
        faena_id: int - ID de la faena a actualizar
        codigo: str - Nuevo código (se convierte a mayúsculas)
        nombre: str - Nuevo nombre
        ubicacion: str - Nueva ubicación (opcional)
        descripcion: str - Nueva descripción (opcional)
        fecha_inicio: str - Nueva fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Nueva fecha de fin (formato ISO: YYYY-MM-DD)
        activo: bool - Estado activo/inactivo (opcional)
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, mensaje y detalles de asignaciones ajustadas
    """
    try:
        data = json.loads(request.body)
        
        faena_id = data.get('faena_id')
        codigo = data.get('codigo', '').upper()
        nombre = data.get('nombre')
        ubicacion = data.get('ubicacion', '')
        descripcion = data.get('descripcion', '')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        activo = data.get('activo', True)
        
        if not faena_id or not codigo or not nombre:
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        if not fecha_inicio:
            return JsonResponse({'error': 'La fecha de inicio es requerida'}, status=400)
        
        if not fecha_fin:
            return JsonResponse({'error': 'La fecha de fin es requerida'}, status=400)
        
        try:
            faena = Faena.objects.get(id=faena_id)
        except Faena.DoesNotExist:
            return JsonResponse({'error': 'Faena no encontrada'}, status=404)
        
        # Verificar si el nuevo código ya está en uso por otra faena
        if Faena.objects.filter(codigo__iexact=codigo).exclude(id=faena_id).exists():
            return JsonResponse({'error': 'Ya existe otra faena con ese código'}, status=400)
        
        # Validar y convertir fechas
        from datetime import datetime
        nueva_fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        nueva_fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        if nueva_fecha_fin < nueva_fecha_inicio:
            return JsonResponse({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}, status=400)
        
        # Guardar datos anteriores para comparación e historial
        datos_anteriores = {
            'codigo': faena.codigo,
            'nombre': faena.nombre,
            'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
            'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None,
            'descripcion': faena.descripcion,
            'ubicacion': faena.ubicacion or ''
        }
        fecha_inicio_anterior = faena.fecha_inicio
        fecha_fin_anterior = faena.fecha_fin
        
        # Construir descripción detallada de los cambios
        cambios = []
        
        if faena.codigo != codigo:
            cambios.append(f"Código: {faena.codigo} → {codigo}")
        
        if faena.nombre != nombre:
            cambios.append(f"Nombre: {faena.nombre} → {nombre}")
        
        if fecha_inicio_anterior != nueva_fecha_inicio:
            fecha_inicio_ant_str = fecha_inicio_anterior.strftime('%d/%m/%Y') if fecha_inicio_anterior else 'Sin fecha'
            cambios.append(f"Fecha inicio: {fecha_inicio_ant_str} → {nueva_fecha_inicio.strftime('%d/%m/%Y')}")
        
        if fecha_fin_anterior != nueva_fecha_fin:
            fecha_fin_ant_str = fecha_fin_anterior.strftime('%d/%m/%Y') if fecha_fin_anterior else 'Sin fecha'
            cambios.append(f"Fecha fin: {fecha_fin_ant_str} → {nueva_fecha_fin.strftime('%d/%m/%Y')}")
        
        if (faena.descripcion or '') != descripcion:
            cambios.append("Descripción modificada")
        
        if (faena.ubicacion or '') != ubicacion:
            cambios.append("Ubicación modificada")
        
        if faena.activo != activo:
            estado_ant = "Activa" if faena.activo else "Inactiva"
            estado_nuevo = "Activa" if activo else "Inactiva"
            cambios.append(f"Estado: {estado_ant} → {estado_nuevo}")
        
        # Generar descripción
        if cambios:
            descripcion_historial = f"Faena modificada. Cambios: {', '.join(cambios)}"
        else:
            descripcion_historial = "Faena modificada (sin cambios detectados)"
        
        # Actualizar la faena
        faena.codigo = codigo
        faena.nombre = nombre
        faena.ubicacion = ubicacion
        faena.descripcion = descripcion
        faena.fecha_inicio = nueva_fecha_inicio
        faena.fecha_fin = nueva_fecha_fin
        faena.activo = activo
        faena.save()
        
        # Registrar en historial
        HistorialFaena.registrar(
            faena=faena,
            accion='FAENA_MODIFICADA',
            descripcion=descripcion_historial,
            usuario=request.user if request.user.is_authenticated else None,
            datos_previos=datos_anteriores,
            datos_nuevos={
                'codigo': codigo,
                'nombre': nombre,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'descripcion': descripcion,
                'ubicacion': ubicacion,
                'activo': activo
            }
        )
        
        # LÓGICA INTELIGENTE: Actualizar asignaciones que coincidan exactamente con las fechas anteriores
        asignaciones_actualizadas = 0
        conflictos = []
        asignaciones = AsignacionFaena.objects.filter(faena=faena, activo=True, personal__activo=True)
        
        for asignacion in asignaciones:
            actualizado = False
            nueva_fecha_inicio_asig = asignacion.fecha_inicio
            nueva_fecha_fin_asig = asignacion.fecha_fin
            
            # Regla 1: Si la fecha de inicio de la asignación coincide exactamente con la fecha de inicio anterior de la faena
            # Y las fechas cambiaron, actualizar
            if (fecha_inicio_anterior and asignacion.fecha_inicio == fecha_inicio_anterior 
                and nueva_fecha_inicio and nueva_fecha_inicio != fecha_inicio_anterior):
                nueva_fecha_inicio_asig = nueva_fecha_inicio
                actualizado = True
            
            # Regla 2: Si la fecha de fin de la asignación coincide exactamente con la fecha de fin anterior de la faena
            # Y las fechas cambiaron, actualizar
            if (fecha_fin_anterior and asignacion.fecha_fin == fecha_fin_anterior 
                and nueva_fecha_fin and nueva_fecha_fin != fecha_fin_anterior):
                nueva_fecha_fin_asig = nueva_fecha_fin
                actualizado = True
            
            # Regla 3: Si la fecha de fin anterior era None y ahora hay una, NO actualizar asignaciones indefinidas
            # (el usuario las dejó indefinidas intencionalmente)
            
            if actualizado:
                # VALIDAR CONFLICTOS: Verificar si las nuevas fechas crean solapamiento con otras asignaciones
                solapamiento_query = Q(personal=asignacion.personal, activo=True) & ~Q(id=asignacion.id) & ~Q(faena=faena)
                
                if nueva_fecha_fin_asig:
                    solapamiento_query &= (
                        Q(fecha_inicio__lte=nueva_fecha_fin_asig) & 
                        (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=nueva_fecha_inicio_asig))
                    )
                else:
                    solapamiento_query &= (
                        Q(fecha_inicio__lte=nueva_fecha_inicio_asig) & 
                        (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=nueva_fecha_inicio_asig))
                    )
                
                asignaciones_conflictivas = AsignacionFaena.objects.filter(solapamiento_query).select_related('faena')
                
                if asignaciones_conflictivas.exists():
                    # HAY CONFLICTO: Registrar y DESACTIVAR la asignación problemática
                    conflicto_info = asignaciones_conflictivas.first()
                    conflictos.append({
                        'personal': f"{asignacion.personal.nombre} {asignacion.personal.apepat} {asignacion.personal.apemat}",
                        'faena_conflicto': conflicto_info.faena.nombre,
                        'codigo_conflicto': conflicto_info.faena.codigo,
                        'fecha_inicio_conflicto': conflicto_info.fecha_inicio.isoformat(),
                        'fecha_fin_conflicto': conflicto_info.fecha_fin.isoformat() if conflicto_info.fecha_fin else 'Indefinido'
                    })
                    # DESACTIVAR la asignación en lugar de dejarla con fechas inconsistentes
                    asignacion.activo = False
                    asignacion.observaciones = f"DESACTIVADA AUTOMÁTICAMENTE: Conflicto al actualizar fechas de faena. {asignacion.observaciones or ''}"
                    asignacion.save()
                else:
                    # Sin conflictos, actualizar
                    asignacion.fecha_inicio = nueva_fecha_inicio_asig
                    asignacion.fecha_fin = nueva_fecha_fin_asig
                    asignacion.save()
                    asignaciones_actualizadas += 1
        
        # Si hay conflictos, devolverlos como advertencia
        if conflictos:
            mensaje_conflicto = f'{len(conflictos)} asignación(es) se DESACTIVARON automáticamente por conflictos al cambiar fechas de la faena:\n\n'
            for conf in conflictos[:5]:  # Limitar a 5 para no saturar
                mensaje_conflicto += f"• {conf['personal']} tiene conflicto con faena '{conf['codigo_conflicto']}' ({conf['fecha_inicio_conflicto']} → {conf['fecha_fin_conflicto']})\n"
            if len(conflictos) > 5:
                mensaje_conflicto += f"\n... y {len(conflictos) - 5} conflicto(s) más."
            
            mensaje_conflicto += "\n\nEstas asignaciones fueron desactivadas para evitar solapamientos. Puede reactivarlas manualmente ajustando las fechas."
            
            return JsonResponse({
                'success': True,
                'message': f'Faena actualizada. {asignaciones_actualizadas} asignación(es) ajustadas correctamente.',
                'warning': mensaje_conflicto,
                'asignaciones_actualizadas': asignaciones_actualizadas,
                'asignaciones_desactivadas': len(conflictos),
                'conflictos': conflictos
            })
        
        # Invalidar caché del calendario
        invalidar_cache_calendario()
        
        mensaje = 'Faena actualizada exitosamente'
        if asignaciones_actualizadas > 0:
            mensaje += f'. Se ajustaron automáticamente {asignaciones_actualizadas} asignación(es) que coincidían con las fechas anteriores de la faena.'
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'asignaciones_actualizadas': asignaciones_actualizadas
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.view_faena', is_ajax=True)
@require_http_methods(["GET"])
def listar_faenas_api(request):
    """
    API endpoint para listar todas las faenas activas en formato JSON.
    Útil para obtener datos de faenas sin recargar la página.
    Incluye información de asignaciones de personal.
    
    Retorna:
        JsonResponse: Lista de faenas en formato JSON con sus datos y cantidad de personal asignado
    """
    try:
        from django.core.serializers.json import DjangoJSONEncoder
        
        faenas = Faena.objects.filter(activo=True).prefetch_related(
            'asignaciones__personal',
            'asignaciones__turno'
        ).order_by('codigo', 'nombre')
        
        faenas_data = []
        for faena in faenas:
            asignaciones_activas = faena.asignaciones.filter(activo=True, personal__activo=True)
            
            faenas_data.append({
                'id': faena.id,
                'codigo': faena.codigo,
                'nombre': faena.nombre,
                'ubicacion': faena.ubicacion or '',
                'descripcion': faena.descripcion or '',
                'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
                'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None,
                'activo': faena.activo,
                'total_personal': asignaciones_activas.count()
            })
        
        return JsonResponse({
            'success': True,
            'faenas': faenas_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.delete_faena', is_ajax=True)
@require_http_methods(["POST"])
def eliminar_faena(request):
    """
    API endpoint para eliminar una faena físicamente (CASCADE elimina asignaciones).
    Elimina la faena y todas sus asignaciones de personal y equipos en cascada.
    
    Parámetros POST (JSON):
        faena_id: int - ID de la faena a eliminar
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, mensaje y cantidad de asignaciones eliminadas
    """
    try:
        data = json.loads(request.body)
        faena_id = data.get('faena_id')
        
        if not faena_id:
            return JsonResponse({'error': 'ID de faena requerido'}, status=400)
        
        try:
            faena = Faena.objects.get(id=faena_id)
            
            # Contar asignaciones que se eliminarán
            total_asignaciones = faena.asignaciones.count()
            
            # Guardar nombre para el mensaje
            nombre_faena = faena.nombre
            
            # Eliminar la faena (CASCADE eliminará automáticamente las asignaciones)
            faena.delete()
            
            # Invalidar caché del calendario
            invalidar_cache_calendario()
            
            # Mensaje según si tenía asignaciones o no
            if total_asignaciones > 0:
                mensaje = f'Faena "{nombre_faena}" eliminada correctamente junto con {total_asignaciones} asignación(es) de personal.'
            else:
                mensaje = f'Faena "{nombre_faena}" eliminada correctamente.'
            
        except Faena.DoesNotExist:
            return JsonResponse({'error': 'Faena no encontrada'}, status=404)
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'asignaciones_eliminadas': total_asignaciones
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def obtener_nombre_completo_usuario(usuario):
    """
    Función helper para obtener el nombre completo de un usuario.
    Prioriza nombre completo (first_name + last_name) sobre username, con fallback a 'Sistema'.
    
    Parámetros:
        usuario: User - Instancia del usuario de Django (puede ser None)
    
    Retorna:
        str: Nombre completo del usuario, username, o 'Sistema' si no hay información
    """
    if not usuario:
        return 'Sistema'
    
    nombre_completo = f"{usuario.first_name or ''} {usuario.last_name or ''}".strip()
    if nombre_completo:
        return nombre_completo
    return usuario.username or 'Sistema'

@csrf_exempt
@login_required
@permission_required_multiple('ope_calendario.ver_historial_faena', 'ope_calendario.view_historialfaena', require_all=False, is_ajax=True)
@require_http_methods(["GET"])
def api_historial_faena(request, faena_id):
    """
    API endpoint para obtener el historial completo de una faena.
    Retorna todos los eventos y cambios registrados en el historial de la faena,
    incluyendo información de usuarios y personal involucrado.
    
    Parámetros:
        request: HttpRequest - Request HTTP
        faena_id: int - ID de la faena para la cual obtener el historial
    
    Retorna:
        JsonResponse: Historial de la faena en formato JSON con todos los eventos ordenados por fecha descendente
    """
    try:
        faena = get_object_or_404(Faena, id=faena_id)
        historial = HistorialFaena.objects.filter(faena=faena).select_related(
            'usuario', 'personal'
        ).order_by('-fecha_hora')
        
        # Preparar historial con nombre completo de usuario
        historial_data = []
        for evento in historial:
            historial_data.append({
                'id': evento.id,
                'fecha_hora': evento.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_formateada': evento.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                'usuario_nombre': obtener_nombre_completo_usuario(evento.usuario),
                'accion': evento.accion,
                'accion_display': evento.get_accion_display(),
                'descripcion': evento.descripcion,
                'personal': {
                    'id': evento.personal.personal_id if evento.personal else None,
                    'nombre_completo': f"{evento.personal.nombre} {evento.personal.apepat} {evento.personal.apemat}" if evento.personal else None,
                    'rut': f"{evento.personal.rut}-{evento.personal.dvrut}" if evento.personal else None
                } if evento.personal else None,
                'datos_previos': evento.datos_previos,
                'datos_nuevos': evento.datos_nuevos
            })
        
        return JsonResponse({
            'success': True,
            'faena': {
                'id': faena.id,
                'codigo': faena.codigo,
                'nombre': faena.nombre
            },
            'historial': historial_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener historial de faena: {str(e)}'
        }, status=500)

@login_required
@permission_required_multiple('ope_calendario.ver_historial_faena', 'ope_calendario.view_historialfaena', require_all=False)
def ver_historial_faena(request, faena_id):
    """
    Vista para mostrar el historial completo de una faena en una página dedicada.
    Muestra todos los eventos y cambios registrados en el historial.
    Mantenida por compatibilidad (la funcionalidad principal está en el modal).
    
    Parámetros:
        request: HttpRequest - Request HTTP
        faena_id: int - ID de la faena para la cual mostrar el historial
    
    Retorna:
        HttpResponse: Renderiza el template historial_faena.html con el historial completo
    """
    from django.core.serializers.json import DjangoJSONEncoder
    
    try:
        faena = Faena.objects.get(id=faena_id)
        historial = HistorialFaena.objects.filter(faena=faena).select_related(
            'usuario', 'personal'
        ).order_by('-fecha_hora')
        
        # Preparar historial con nombre completo de usuario
        historial_data = []
        for evento in historial:
            historial_data.append({
                'id': evento.id,
                'fecha_hora': evento.fecha_hora,
                'fecha_hora_formateada': evento.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                'usuario_nombre': obtener_nombre_completo_usuario(evento.usuario),
                'accion': evento.accion,
                'accion_display': evento.get_accion_display(),
                'descripcion': evento.descripcion,
                'personal': {
                    'id': evento.personal.personal_id if evento.personal else None,
                    'nombre_completo': f"{evento.personal.nombre} {evento.personal.apepat} {evento.personal.apemat}" if evento.personal else None,
                    'rut': f"{evento.personal.rut}-{evento.personal.dvrut}" if evento.personal else None
                } if evento.personal else None,
                'datos_previos': evento.datos_previos,
                'datos_nuevos': evento.datos_nuevos
            })
        
        context = {
            'faena': faena,
            'historial': historial,
            'historial_json': json.dumps(historial_data, cls=DjangoJSONEncoder, default=str),
        }
        
        return render(request, 'calendario/historial_faena.html', context)
        
    except Faena.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Faena no encontrada')
        return redirect('calendario:gestionar_faenas')


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.asignacion_masiva_personal', is_ajax=True)
@require_http_methods(["POST"])
def crear_asignacion_masiva(request):
    """
    API endpoint para crear asignaciones masivas de personal a faena.
    Permite asignar múltiples personal a una faena en una sola operación.
    Valida conflictos con asignaciones existentes y OTs para cada personal antes de crear.
    
    Parámetros POST (JSON):
        faena_id: int - ID de la faena
        personal_ids: list - Lista de IDs de personal a asignar
        turno_id: int - ID del turno
        fecha_inicio: str - Fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Fecha de fin (formato ISO: YYYY-MM-DD, opcional)
        bloque_inicio_id: int - ID del bloque de inicio del turno (opcional)
        observaciones: str - Observaciones opcionales
        activo: bool - Estado activo/inactivo (por defecto: True)
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, cantidad de asignaciones creadas y lista de errores
    """
    try:
        data = json.loads(request.body)
        
        personal_ids = data.get('personal_ids', [])
        faena_id = data.get('faena_id')
        turno_id = data.get('turno_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin', None)
        bloque_inicio_id = data.get('bloque_inicio_id', None)
        observaciones = data.get('observaciones', '')
        activo = data.get('activo', True)
        
        # Validaciones
        if not personal_ids or not isinstance(personal_ids, list):
            return JsonResponse({'error': 'Debe seleccionar al menos un trabajador'}, status=400)
        
        if not all([faena_id, turno_id, fecha_inicio]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            faena = Faena.objects.get(id=faena_id)
            turno = Turno.objects.get(id=turno_id)
            bloque_inicio = None
            if bloque_inicio_id:
                bloque_inicio = TurnoBloque.objects.get(id=bloque_inicio_id, turno=turno)
        except (Faena.DoesNotExist, Turno.DoesNotExist, TurnoBloque.DoesNotExist):
            return JsonResponse({'error': 'Datos inválidos (faena, turno o bloque)'}, status=400)
        
        # Convertir fechas
        fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_date = None
        if fecha_fin:
            fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Validar cada trabajador y crear asignaciones
        asignaciones_creadas = []
        errores = []
        
        for personal_id in personal_ids:
            try:
                personal_obj = Personal.objects.get(personal_id=personal_id)
                
                # Verificar solapamiento con asignaciones a otras faenas
                solapamiento_query = Q(personal=personal_obj, activo=True)
                
                if fecha_fin_date:
                    solapamiento_query &= (
                        Q(fecha_inicio__lte=fecha_fin_date) & 
                        (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
                    )
                else:
                    solapamiento_query &= (
                        Q(fecha_inicio__lte=fecha_inicio_date) & 
                        (Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date))
                    )
                
                asignaciones_conflictivas = AsignacionFaena.objects.filter(solapamiento_query).select_related('faena')
                
                if asignaciones_conflictivas.exists():
                    # Generar mensaje detallado del conflicto
                    conflicto = asignaciones_conflictivas.first()
                    fecha_fin_str = conflicto.fecha_fin.strftime('%d/%m/%Y') if conflicto.fecha_fin else 'Indefinido'
                    errores.append(
                        f"{personal_obj.nombre} {personal_obj.apepat} {personal_obj.apemat}: "
                        f"Ya asignado en faena '{conflicto.faena.nombre}' "
                        f"({conflicto.fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin_str})"
                    )
                    continue
                
                # Verificar si tiene OT asignadas en fechas que interfieren
                ot_conflictivas = OrdenTrabajo.objects.filter(
                    personal_asignado=personal_obj
                ).filter(
                    Q(fecha_inicio__isnull=False)
                )
                
                # Verificar solapamiento de fechas con OT
                if fecha_fin_date:
                    ot_conflictivas = ot_conflictivas.filter(
                        Q(fecha_inicio__lte=fecha_fin_date) & (
                            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
                        )
                    )
                else:
                    ot_conflictivas = ot_conflictivas.filter(
                        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio_date)
                    )
                
                ot_conflictivas = ot_conflictivas.select_related('equipo_id').order_by('-fecha_inicio')[:1]
                
                if ot_conflictivas.exists():
                    ot_conflicto = ot_conflictivas.first()
                    fecha_fin_ot = ot_conflicto.fecha_fin.strftime('%d/%m/%Y') if ot_conflicto.fecha_fin else 'Indefinido'
                    fecha_inicio_ot = ot_conflicto.fecha_inicio.strftime('%d/%m/%Y') if ot_conflicto.fecha_inicio else 'N/A'
                    equipo_nombre = ot_conflicto.equipo_id.nombreEquipo if ot_conflicto.equipo_id else 'N/A'
                    errores.append(
                        f"{personal_obj.nombre} {personal_obj.apepat} {personal_obj.apemat}: "
                        f"Tiene OT asignada '{ot_conflicto.folio}' (Equipo: {equipo_nombre}) "
                        f"({fecha_inicio_ot} → {fecha_fin_ot})"
                    )
                    continue
                
                # Crear asignación
                asignacion = AsignacionFaena.objects.create(
                    personal=personal_obj,
                    faena=faena,
                    turno=turno,
                    fecha_inicio=fecha_inicio_date,
                    fecha_fin=fecha_fin_date,
                    bloque_inicio=bloque_inicio,
                    observaciones=observaciones,
                    activo=activo
                )
                # Marcar que el historial se registrará manualmente (evitar duplicado en señal)
                asignacion._historial_registrado = True
                
                asignaciones_creadas.append(asignacion)
                
                # Registrar en historial
                from .models import HistorialFaena
                HistorialFaena.registrar(
                    faena=faena,
                    accion='PERSONAL_ASIGNADO',
                    descripcion=f"{personal_obj.nombre} {personal_obj.apepat} asignado con turno {turno.nombre} del {fecha_inicio_date.strftime('%d/%m/%Y')} al {fecha_fin_date.strftime('%d/%m/%Y') if fecha_fin_date else 'indefinido'}",
                    usuario=request.user if request.user.is_authenticated else None,
                    personal=personal_obj,
                    datos_nuevos={
                        'personal_id': personal_obj.personal_id,
                        'personal_nombre': f"{personal_obj.nombre} {personal_obj.apepat} {personal_obj.apemat}",
                        'turno': turno.nombre,
                        'fecha_inicio': fecha_inicio_date.isoformat(),
                        'fecha_fin': fecha_fin_date.isoformat() if fecha_fin_date else None
                    }
                )
                
            except Personal.DoesNotExist:
                errores.append(f"Trabajador ID {personal_id}: No encontrado")
            except Exception as e:
                errores.append(f"Trabajador ID {personal_id}: {str(e)}")
        
        # Invalidar caché del calendario si se crearon asignaciones
        if asignaciones_creadas:
            invalidar_cache_calendario()
        
        # Preparar respuesta
        total_exitosos = len(asignaciones_creadas)
        total_errores = len(errores)
        
        if total_exitosos > 0 and total_errores == 0:
            return JsonResponse({
                'success': True,
                'message': f'{total_exitosos} trabajador{"es" if total_exitosos > 1 else ""} asignado{"s" if total_exitosos > 1 else ""} correctamente',
                'total_asignados': total_exitosos,
                'total_errores': 0
            })
        elif total_exitosos > 0 and total_errores > 0:
            return JsonResponse({
                'success': True,
                'message': f'{total_exitosos} trabajador{"es" if total_exitosos > 1 else ""} asignado{"s" if total_exitosos > 1 else ""} correctamente',
                'warning': True,
                'total_asignados': total_exitosos,
                'total_errores': total_errores,
                'errores': errores
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'No se pudo asignar ningún trabajador',
                'total_asignados': 0,
                'total_errores': total_errores,
                'errores': errores
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.view_faena', is_ajax=True)
def api_estados(request):
    """
    API endpoint para obtener la lista de todos los estados disponibles.
    Útil para poblar dropdowns y mostrar la leyenda de estados en el frontend.
    
    Retorna:
        JsonResponse: Lista de estados activos en formato JSON, ordenados por prioridad descendente
    """
    estados = Estado.objects.filter(activo=True).order_by('-prioridad', 'nombre')
    estados_data = [
        {
            'id': estado.id,
            'nombre': estado.nombre,
            'nombre_corto': estado.nombre_corto,
            'background_color': estado.background_color,
            'color': estado.color,
            'prioridad': estado.prioridad
        } for estado in estados
    ]
    return JsonResponse({'estados': estados_data})


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.view_faena', is_ajax=True)
def api_personal_faena(request, faena_id):
    """
    API endpoint para obtener el personal asignado a una faena específica.
    Incluye información detallada de cada asignación, turnos y bloques.
    Filtra por mes y año si se proporcionan en los parámetros GET.
    
    Parámetros GET (opcionales):
        year: int - Año para filtrar asignaciones (por defecto: año actual)
        month: int - Mes para filtrar asignaciones (por defecto: mes actual)
    
    Parámetros:
        request: HttpRequest - Request HTTP
        faena_id: int - ID de la faena para la cual obtener el personal
    
    Retorna:
        JsonResponse: Lista de personal asignado en formato JSON con sus asignaciones y turnos
    """
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    # Validar rango de fechas
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 1900 or year > 2100:
        year = datetime.now().year
    
    # Obtener rango de fechas del mes
    _, ultimo_dia = monthrange(year, month)
    fecha_inicio_mes = date(year, month, 1)
    fecha_fin_mes = date(year, month, ultimo_dia)
    
    try:
        faena = Faena.objects.get(id=faena_id)
    except Faena.DoesNotExist:
        return JsonResponse({'error': 'Faena no encontrada'}, status=404)
    
    # Obtener asignaciones activas de esta faena que se superpongan con el mes (solo personal activo)
    asignaciones = AsignacionFaena.objects.filter(
        faena=faena,
        activo=True,
        personal__activo=True,  # Filtrar solo personal activo
        fecha_inicio__lte=fecha_fin_mes
    ).filter(
        Q(fecha_fin__gte=fecha_inicio_mes) | Q(fecha_fin__isnull=True)
    ).select_related(
        'personal', 'turno', 'bloque_inicio'
    ).prefetch_related(
        'turno__bloques__estado',
        'personal__infolaboral_set__cargo_id',
        'personal__infolaboral_set__empresa_id'
    ).order_by('personal__apepat', 'personal__apemat', 'personal__nombre')
    
    # Agrupar por personal
    personal_dict = {}
    for asig in asignaciones:
        personal_id = asig.personal.personal_id
        
        if personal_id not in personal_dict:
            infolaboral = asig.personal.infolaboral_set.first()
            personal_dict[personal_id] = {
                'personal_id': personal_id,
                'nombre': asig.personal.nombre,
                'apepat': asig.personal.apepat,
                'apemat': asig.personal.apemat,
                'rut': asig.personal.rut,
                'dvrut': asig.personal.dvrut,
                'cargo': infolaboral.cargo_id.cargo if infolaboral and infolaboral.cargo_id else 'Sin cargo',
                'empresa': infolaboral.empresa_id.nomFantasia if infolaboral and infolaboral.empresa_id else 'Sin empresa',
                'asignaciones': []
            }
        
        # Agregar asignación
        turno_data = {
            'id': asig.turno.id,
            'nombre': asig.turno.nombre,
            'longitud_ciclo': asig.turno.longitud_ciclo,
            'bloques': []
        }
        
        # Agregar bloques del turno
        dias_acum = 0
        for bloque in asig.turno.bloques.all().order_by('orden'):
            turno_data['bloques'].append({
                'orden': bloque.orden,
                'duracion_dias': bloque.duracion_dias,
                'dias_acumulados_hasta': dias_acum,
                'estado': {
                    'id': bloque.estado.id,
                    'nombre': bloque.estado.nombre,
                    'nombre_corto': bloque.estado.nombre_corto,
                    'background_color': bloque.estado.background_color,
                    'color': bloque.estado.color
                }
            })
            dias_acum += bloque.duracion_dias
        
        personal_dict[personal_id]['asignaciones'].append({
            'id': asig.id,
            'fecha_inicio': asig.fecha_inicio.isoformat(),
            'fecha_fin': asig.fecha_fin.isoformat() if asig.fecha_fin else None,
            'bloque_inicio_orden': sum(b.duracion_dias for b in asig.turno.bloques.filter(orden__lt=asig.bloque_inicio.orden)) if asig.bloque_inicio else 0,
            'turno': turno_data
        })
    
    return JsonResponse({
        'personal': list(personal_dict.values()),
        'total': len(personal_dict)
    })


@login_required
@permission_required_custom('ope_calendario.eliminar_estado_manual')
@require_http_methods(["POST"])
def eliminar_estado_manual(request, estado_id):
    """
    Vista para eliminar un estado manual específico.
    Elimina permanentemente el estado manual del personal e invalida el caché del calendario.
    
    Parámetros:
        request: HttpRequest - Request HTTP
        estado_id: int - ID del estado manual a eliminar
    
    Retorna:
        JsonResponse: Resultado de la operación con status (success/error) y mensaje
    """
    from django.core.cache import cache
    
    try:
        estado_manual = EstadoManual.objects.get(id=estado_id)
        
        # Guardar info antes de eliminar
        personal_nombre = f"{estado_manual.personal.nombre} {estado_manual.personal.apepat}"
        
        # Eliminar permanentemente
        estado_manual.delete()
        
        # Invalidar caché del calendario
        cache.delete('calendario_data')
        
        return JsonResponse({
            'status': 'success',
            'message': f'Estado manual de {personal_nombre} eliminado correctamente'
        })
    except EstadoManual.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Estado manual no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al eliminar el estado manual: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('ope_calendario.asignar_estado_manual', is_ajax=True)
@require_http_methods(["POST"])
def asignar_estado_manual_api(request):
    """
    API endpoint para asignar estados manuales a múltiples trabajadores.
    Crea estados manuales que sobrescriben los estados calculados por turnos.
    Valida que las fechas estén dentro del rango de la faena.
    
    Parámetros POST (JSON):
        faena_id: int - ID de la faena
        estado: str - ID del estado a asignar (como string)
        fecha_inicio: str - Fecha de inicio (formato ISO: YYYY-MM-DD)
        fecha_fin: str - Fecha de fin (formato ISO: YYYY-MM-DD)
        observaciones: str - Observaciones opcionales
        personal_ids: list - Lista de IDs de personal a los que asignar el estado
    
    Retorna:
        JsonResponse: Resultado de la operación con success/error, cantidad de estados creados y lista de errores
    """
    import json
    from django.core.cache import cache
    from datetime import datetime
    
    try:
        data = json.loads(request.body)
        
        faena_id = data.get('faena_id')
        estado_nombre = data.get('estado')
        fecha_inicio_str = data.get('fecha_inicio')
        fecha_fin_str = data.get('fecha_fin')
        observaciones = data.get('observaciones', '')
        personal_ids = data.get('personal_ids', [])
        
        # Validaciones
        if not all([faena_id, estado_nombre, fecha_inicio_str, fecha_fin_str]):
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos requeridos'
            }, status=400)
        
        if not personal_ids:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos un trabajador'
            }, status=400)
        
        # Obtener objetos
        try:
            faena = Faena.objects.get(id=faena_id)
        except Faena.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Faena no encontrada'
            }, status=404)
        
        # Obtener el estado por ID
        try:
            estado_id = int(estado_nombre)
            estado = Estado.objects.get(id=estado_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'ID de estado no válido'
            }, status=400)
        except Estado.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Estado no encontrado en el sistema'
            }, status=404)
        
        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        
        if fecha_fin < fecha_inicio:
            return JsonResponse({
                'success': False,
                'error': 'La fecha de fin no puede ser anterior a la fecha de inicio'
            }, status=400)
        
        # Validar que las fechas estén dentro del rango de la faena
        if faena.fecha_inicio and fecha_inicio < faena.fecha_inicio:
            return JsonResponse({
                'success': False,
                'error': f'La fecha de inicio ({fecha_inicio.strftime("%d/%m/%Y")}) es anterior al inicio de la faena ({faena.fecha_inicio.strftime("%d/%m/%Y")})'
            }, status=400)
        
        if faena.fecha_fin and fecha_fin > faena.fecha_fin:
            return JsonResponse({
                'success': False,
                'error': f'La fecha de fin ({fecha_fin.strftime("%d/%m/%Y")}) es posterior al fin de la faena ({faena.fecha_fin.strftime("%d/%m/%Y")})'
            }, status=400)
        
        # Crear estados manuales
        creados = 0
        errores = []
        
        for personal_id in personal_ids:
            try:
                personal = Personal.objects.get(personal_id=personal_id)
                
                # Verificar conflictos con otras asignaciones de faena
                # Buscar asignaciones activas que se solapen con el período solicitado
                asignaciones_conflictivas = AsignacionFaena.objects.filter(
                    personal=personal,
                    activo=True
                ).exclude(
                    faena=faena  # Excluir la misma faena
                ).filter(
                    fecha_inicio__lte=fecha_fin
                ).filter(
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)
                )
                
                if asignaciones_conflictivas.exists():
                    asignacion_conflicto = asignaciones_conflictivas.first()
                    fecha_fin_texto = asignacion_conflicto.fecha_fin.strftime('%d/%m/%Y') if asignacion_conflicto.fecha_fin else 'Indefinido'
                    errores.append(
                        f"{personal.nombre} {personal.apepat} {personal.apemat}: "
                        f"Ya asignado en faena '{asignacion_conflicto.faena.nombre}' "
                        f"({asignacion_conflicto.fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin_texto})"
                    )
                    continue
                
                EstadoManual.objects.create(
                    personal=personal,
                    estado=estado,
                    faena=faena,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    motivo=observaciones  # El modelo usa 'motivo', no 'observaciones'
                )
                creados += 1
                
            except Personal.DoesNotExist:
                errores.append(f'Trabajador ID {personal_id}: No encontrado')
            except Exception as e:
                errores.append(f'Trabajador ID {personal_id}: {str(e)}')
        
        # Invalidar caché
        cache.delete('calendario_data')
        
        # Preparar respuesta (mismo formato que crear_asignacion_masiva)
        total_exitosos = creados
        total_errores = len(errores)
        
        if total_exitosos > 0 and total_errores == 0:
            return JsonResponse({
                'success': True,
                'message': f'{total_exitosos} trabajador{"es" if total_exitosos > 1 else ""} con estado manual asignado{"s" if total_exitosos > 1 else ""} correctamente',
                'total_asignados': total_exitosos,
                'total_errores': 0
            })
        elif total_exitosos > 0 and total_errores > 0:
            return JsonResponse({
                'success': True,
                'message': f'{total_exitosos} trabajador{"es" if total_exitosos > 1 else ""} con estado manual asignado{"s" if total_exitosos > 1 else ""} correctamente',
                'warning': True,
                'total_asignados': total_exitosos,
                'total_errores': total_errores,
                'errores': errores
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'No se pudo asignar ningún trabajador',
                'total_asignados': 0,
                'total_errores': total_errores,
                'errores': errores
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)