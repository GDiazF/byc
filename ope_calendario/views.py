from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from datetime import datetime, date, timedelta
from calendar import monthrange
import json
import hashlib
from .models import (
    Estado, EstadoFuente, Turno, TurnoBloque, 
    Faena, AsignacionFaena, EstadoManual
)
from rrhh_personal.models import Personal


# Create your views here.

def calendario_mensual(request):
    """Vista para mostrar el calendario mensual con datos reales y paginación"""
    
    # Obtener parámetros de la URL o usar fecha actual
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
        page = 1
        page_size = 25
    
    # Validar rango de fechas
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 1900 or year > 2100:
        year = datetime.now().year
    
    # Validar paginación
    if page < 1:
        page = 1
    if page_size not in [25, 50, 100]:
        page_size = 25
    
    # Obtener filtros
    faena_filter = request.GET.get('faena', '')
    cargo_filter = request.GET.get('cargo', '')
    empresa_filter = request.GET.get('empresa', '')
    search_query = request.GET.get('search', '')
    
    # Obtener datos del calendario con paginación
    calendario_data = obtener_calendario_mensual(
        year, month, faena_filter, cargo_filter, empresa_filter, search_query, page, page_size
    )
    
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
    
    
    # Calcular información de paginación
    total_personal = calendario_data.get('total_personal', 0)
    total_pages = (total_personal + page_size - 1) // page_size if total_personal > 0 else 1
    
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
        'current_page': page,
        'page_size': page_size,
        'total_personal': total_personal,
        'total_pages': total_pages,
        'has_previous': page > 1,
        'has_next': page < total_pages,
        'page_range': range(max(1, page - 2), min(total_pages + 1, page + 3)),
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

def obtener_calendario_mensual(year, month, faena_filter='', cargo_filter='', empresa_filter='', search_query='', page=1, page_size=25):
    """
    Obtiene datos para el calendario con paginación.
    NUEVA ARQUITECTURA: Envía asignaciones al frontend, estados se calculan en JavaScript
    ESCALABLE: O(1) - El tiempo no aumenta con más trabajadores
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
    Versión optimizada que usa datos pre-cargados en memoria.
    Reduce consultas de ~620 a menos de 10 por carga de página.
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
    Calcula el estado final de una persona en una fecha específica,
    considerando todas las fuentes y prioridades.
    
    Orden de prioridad:
    1. Estados manuales (más alta prioridad)
    2. Estados de fuentes externas (según prioridad del estado)
    3. Estados derivados de turnos (más baja prioridad)
    
    Retorna una lista de estados cuando hay conflictos de prioridad.
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

def api_calendario_mensual(request):
    """API para obtener datos del calendario en formato JSON con paginación"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
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
        faenas_por_personal = {}
        for p in calendario_data['personal']:
            # Buscar asignación activa
            asignacion = p.asignaciones_faena.filter(activo=True).first()
            if asignacion:
                faenas_por_personal[p.personal_id] = asignacion.faena.nombre
            else:
                # Si no tiene asignación de turno, buscar estado manual
                estado_manual = p.estados_manuales.filter(
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
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
    """Invalida todo el caché del calendario incrementando la versión"""
    # Incrementar versión del caché para invalidar todos los calendarios
    current_version = cache.get('calendario_version', 0)
    new_version = current_version + 1
    cache.set('calendario_version', new_version, None)  # Sin expiración


@require_http_methods(["GET"])
def obtener_info_personal(request, personal_id):
    """API para obtener información completa del personal incluyendo documentación"""
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
            'tiene_documento': bool(lic.rutaDoc)
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
            'tiene_documento': bool(lic.rutaDoc)
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
            'tiene_documento': bool(cert.rutaDoc)
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
            'tiene_documento': bool(exam.rutaDoc)
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

def limpiar_cache_calendario(request):
    """Vista administrativa para limpiar el caché del calendario manualmente"""
    from django.contrib import messages
    
    current_version = cache.get('calendario_version', 0)
    cache.clear()  # Limpiar todo el caché
    cache.set('calendario_version', 0)  # Resetear versión
    
    messages.success(request, f'Caché del calendario limpiado exitosamente. Versión reseteada de {current_version} a 0.')
    return redirect('calendario:calendario_mensual')


@csrf_exempt
@require_http_methods(["POST"])
def crear_asignacion(request):
    """API para crear una nueva asignación de faena"""
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
        
        # Buscar asignaciones que se solapen
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
        
        asignaciones_solapadas = AsignacionFaena.objects.filter(solapamiento_query)
        
        if asignaciones_solapadas.exists():
            return JsonResponse({
                'error': f'Las fechas se solapan con una asignación existente. Revisa las fechas de las asignaciones actuales.'
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
@require_http_methods(["POST"])
def actualizar_asignacion(request):
    """API para actualizar una asignación de faena existente"""
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
        
        asignaciones_solapadas = AsignacionFaena.objects.filter(solapamiento_query)
        
        if asignaciones_solapadas.exists():
            return JsonResponse({
                'error': f'Las fechas se solapan con otra asignación existente. Revisa las fechas de las asignaciones actuales.'
            }, status=400)
        
        # Actualizar asignación
        asignacion.faena = faena
        asignacion.turno = turno
        asignacion.fecha_inicio = fecha_inicio
        asignacion.fecha_fin = fecha_fin if fecha_fin else None
        asignacion.bloque_inicio = bloque_inicio
        asignacion.observaciones = observaciones
        asignacion.activo = activo
        asignacion.save()
        
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
@require_http_methods(["POST"])
def eliminar_asignacion(request):
    """API para eliminar una asignación de faena"""
    try:
        data = json.loads(request.body)
        asignacion_id = data.get('asignacion_id')
        
        if not asignacion_id:
            return JsonResponse({'error': 'ID de asignación requerido'}, status=400)
        
        try:
            asignacion = AsignacionFaena.objects.get(id=asignacion_id)
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

def asignar_personal_faena(request, faena_id):
    """Vista para asignar personal a una faena específica - PÁGINA COMPLETA"""
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Obtener la faena
    try:
        faena = Faena.objects.get(id=faena_id, activo=True)
    except Faena.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Faena no encontrada')
        return redirect('calendario:gestionar_faenas')
    
    # Obtener personal activo con sus asignaciones
    personal_list = Personal.objects.filter(activo=True).select_related(
        'sexo_id', 'estcivil_id'
    ).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        'asignaciones_faena__faena',
        'asignaciones_faena__turno'
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
    
    for p in personal_list:
        # Verificar asignación activa
        asignacion_activa = p.asignaciones_faena.filter(
            activo=True
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=date.today())
        ).select_related('faena', 'turno').first()
        
        cargo = p.infolaboral_set.first().cargo_id.cargo if p.infolaboral_set.exists() else 'Sin cargo'
        empresa = p.infolaboral_set.first().empresa_id.nomFantasia if p.infolaboral_set.exists() and p.infolaboral_set.first().empresa_id else 'Sin empresa'
        cargos_set.add(cargo)
        empresas_set.add(empresa)
        
        # Verificar si la asignación interfiere con las fechas de esta faena
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
                    'faena': asignacion_activa.faena.nombre,
                    'turno': asignacion_activa.turno.nombre,
                    'fecha_inicio': asignacion_activa.fecha_inicio.isoformat(),
                    'fecha_fin': asignacion_activa.fecha_fin.isoformat() if asignacion_activa.fecha_fin else None
                }
        
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


def gestionar_faenas(request):
    """Vista principal para gestionar faenas y sus asignaciones"""
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Obtener todas las faenas activas
    faenas = Faena.objects.filter(activo=True).prefetch_related(
        'asignaciones__personal',
        'asignaciones__turno__bloques__estado',
        'asignaciones__bloque_inicio'
    ).order_by('nombre')
    
    # Obtener todo el personal activo para asignar
    personal = Personal.objects.filter(activo=True).select_related(
        'sexo_id', 'estcivil_id'
    ).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        'asignaciones_faena__faena'
    ).order_by('apepat', 'apemat', 'nombre')
    
    # Obtener turnos disponibles
    turnos = Turno.objects.filter(activo=True).prefetch_related(
        'bloques__estado'
    ).order_by('nombre')
    
    # Preparar datos para JSON
    faenas_data = []
    for faena in faenas:
        asignaciones_activas = faena.asignaciones.filter(
            activo=True,
            personal__activo=True  # Filtrar solo personal activo
        ).select_related('personal', 'turno', 'bloque_inicio')
        
        faenas_data.append({
            'id': faena.id,
            'codigo': faena.codigo,
            'nombre': faena.nombre,
            'ubicacion': faena.ubicacion or '',
            'descripcion': faena.descripcion or '',
            'fecha_inicio': faena.fecha_inicio.isoformat() if faena.fecha_inicio else None,
            'fecha_fin': faena.fecha_fin.isoformat() if faena.fecha_fin else None,
            'activo': faena.activo,
            'total_personal': asignaciones_activas.count(),
            'asignaciones': [
                {
                    'id': asig.id,
                    'personal': {
                        'id': asig.personal.personal_id,
                        'nombre': f"{asig.personal.nombre} {asig.personal.apepat} {asig.personal.apemat}",
                        'rut': f"{asig.personal.rut}-{asig.personal.dvrut}",
                        'cargo': asig.personal.infolaboral_set.first().cargo_id.cargo if asig.personal.infolaboral_set.exists() else 'Sin cargo'
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
                } for asig in asignaciones_activas
            ]
        })
    
    # Preparar personal para JSON
    personal_data = []
    for p in personal:
        # Verificar si ya tiene asignaciones activas
        tiene_asignacion = p.asignaciones_faena.filter(
            activo=True,
            fecha_fin__isnull=True
        ).exists() or p.asignaciones_faena.filter(
            activo=True,
            fecha_fin__gte=date.today()
        ).exists()
        
        personal_data.append({
            'id': p.personal_id,
            'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
            'rut': f"{p.rut}-{p.dvrut}",
            'cargo': p.infolaboral_set.first().cargo_id.cargo if p.infolaboral_set.exists() else 'Sin cargo',
            'empresa': p.infolaboral_set.first().empresa_id.razonSocial if p.infolaboral_set.exists() else 'Sin empresa',
            'tiene_asignacion': tiene_asignacion,
            'asignacion_actual': {
                'faena': p.asignaciones_faena.filter(activo=True).first().faena.nombre if p.asignaciones_faena.filter(activo=True).exists() else None
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
    
    context = {
        'faenas_json': json.dumps(faenas_data, cls=DjangoJSONEncoder),
        'personal_json': json.dumps(personal_data, cls=DjangoJSONEncoder),
        'turnos_json': json.dumps(turnos_data, cls=DjangoJSONEncoder),
        'total_faenas': len(faenas_data),
        'total_personal': len(personal_data),
    }
    
    return render(request, 'calendario/gestionar_faenas.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def crear_faena(request):
    """API para crear una nueva faena"""
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
@require_http_methods(["POST"])
def actualizar_faena(request):
    """API para actualizar una faena existente y ajustar asignaciones automáticamente"""
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
        
        # Guardar fechas antiguas para comparación
        fecha_inicio_anterior = faena.fecha_inicio
        fecha_fin_anterior = faena.fecha_fin
        
        # Actualizar la faena
        faena.codigo = codigo
        faena.nombre = nombre
        faena.ubicacion = ubicacion
        faena.descripcion = descripcion
        faena.fecha_inicio = nueva_fecha_inicio
        faena.fecha_fin = nueva_fecha_fin
        faena.activo = activo
        faena.save()
        
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
@require_http_methods(["GET"])
def listar_faenas_api(request):
    """API para obtener lista de faenas con sus asignaciones"""
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
@require_http_methods(["POST"])
def eliminar_faena(request):
    """API para eliminar una faena (en cascada con sus asignaciones)"""
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


@csrf_exempt
@require_http_methods(["POST"])
def crear_asignacion_masiva(request):
    """API para crear múltiples asignaciones a la vez (asignación masiva)"""
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
                
                # Verificar solapamiento para este trabajador
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
                asignaciones_creadas.append(asignacion)
                
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


def api_estados(request):
    """API para obtener todos los estados disponibles"""
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


def api_personal_faena(request, faena_id):
    """API para obtener el personal asignado a una faena específica con sus asignaciones"""
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
@require_http_methods(["POST"])
def eliminar_estado_manual(request, estado_id):
    """
    Elimina permanentemente un estado manual
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


@login_required
@require_http_methods(["POST"])
def asignar_estado_manual_api(request):
    """
    API para asignar estados manuales a múltiples trabajadores
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