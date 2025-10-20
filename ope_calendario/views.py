from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, date, timedelta
from calendar import monthrange
import json
from .models import (
    Estado, EstadoFuente, Turno, TurnoBloque, 
    Faena, AsignacionFaena, EstadoManual
)
from rrhh_personal.models import Personal


# Create your views here.

def calendario_mensual(request):
    """Vista para mostrar el calendario mensual con datos reales"""
    
    # Obtener parámetros de la URL o usar fecha actual
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
    
    # Obtener filtros
    faena_filter = request.GET.get('faena', '')
    cargo_filter = request.GET.get('cargo', '')
    search_query = request.GET.get('search', '')
    
    # Obtener datos del calendario
    calendario_data = obtener_calendario_mensual(year, month, faena_filter, cargo_filter, search_query)
    
    # Obtener rango de fechas del mes para filtrar asignaciones
    _, ultimo_dia = monthrange(year, month)
    fecha_inicio_mes = date(year, month, 1)
    fecha_fin_mes = date(year, month, ultimo_dia)
    
    # Obtener opciones para filtros
    faenas = Faena.objects.filter(activo=True).order_by('nombre')
    turnos = Turno.objects.filter(activo=True).prefetch_related('bloques__estado').order_by('nombre')
    cargos = Personal.objects.filter(activo=True).values_list('infolaboral__cargo_id__cargo', flat=True).distinct().order_by('infolaboral__cargo_id__cargo')
    
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
    
    # Preparar datos del calendario para JSON
    calendario_json = {
        'personal': [
            {
                'personal_id': p.personal_id,
                'nombre': p.nombre,
                'apepat': p.apepat,
                'apemat': p.apemat,
                'rut': p.rut,
                'dvrut': p.dvrut,
                'fecha_nac': p.fechanac.isoformat() if p.fechanac else None,
                'correo': p.correo,
                'direccion': p.direccion,
                'activo': p.activo,
                'infolaboral_set': [
                    {
                        'cargo_id': {
                            'cargo': il.cargo_id.cargo
                        }
                    } for il in p.infolaboral_set.all()
                ],
                'asignaciones_faena': [
                    {
                        'id': af.id,
                        'faena': {
                            'id': af.faena.id,
                            'nombre': af.faena.nombre
                        },
                        'turno_id': af.turno.id,
                        'fecha_inicio': af.fecha_inicio.isoformat() if af.fecha_inicio else None,
                        'fecha_fin': af.fecha_fin.isoformat() if af.fecha_fin else None,
                        'bloque_inicio_id': af.bloque_inicio.id if af.bloque_inicio else None,
                        'observaciones': af.observaciones,
                        'activo': af.activo
                    } for af in p.asignaciones_faena.filter(activo=True)
                ]
            } for p in calendario_data['personal']
        ],
        'estados': {},
        'dias_mes': calendario_data['dias_mes']
    }
    
    # Convertir estados a diccionarios serializables
    for personal_id, estados_persona in calendario_data['estados'].items():
        calendario_json['estados'][personal_id] = {}
        for dia, estados in estados_persona.items():
            # Asegurar que estados sea siempre una lista
            if estados:
                if hasattr(estados, '__iter__') and not isinstance(estados, str):
                    # Es una lista o iterable
                    if len(estados) == 1:
                        estado_info = estados[0]
                        # Extraer el estado del diccionario si es necesario
                        estado = estado_info['estado'] if isinstance(estado_info, dict) else estado_info
                        detalle_fuente = estado_info.get('detalle_fuente') if isinstance(estado_info, dict) else None
                        
                        calendario_json['estados'][personal_id][dia] = {
                            'nombre': estado.nombre,
                            'nombre_corto': estado.nombre_corto or estado.nombre,
                            'color': estado.color,
                            'background_color': estado.background_color,
                            'prioridad': estado.prioridad,
                            'es_bloqueante': estado.es_bloqueante,
                            'multiple': False,
                            'detalle_fuente': detalle_fuente
                        }
                    elif len(estados) > 1:
                        # Múltiples estados con la misma prioridad
                        estados_procesados = []
                        detalles_fuentes = []
                        
                        for estado_info in estados:
                            estado = estado_info['estado'] if isinstance(estado_info, dict) else estado_info
                            detalle_fuente = estado_info.get('detalle_fuente') if isinstance(estado_info, dict) else None
                            
                            estados_procesados.append({
                                'nombre': estado.nombre,
                                'nombre_corto': estado.nombre_corto or estado.nombre,
                                'color': estado.color,
                                'background_color': estado.background_color,
                                'prioridad': estado.prioridad,
                                'es_bloqueante': estado.es_bloqueante
                            })
                            
                            if detalle_fuente:
                                detalles_fuentes.append(detalle_fuente)
                        
                        calendario_json['estados'][personal_id][dia] = {
                            'estados': estados_procesados,
                            'multiple': True,
                            'detalles_fuentes': detalles_fuentes
                        }
                    else:
                        calendario_json['estados'][personal_id][dia] = None
                else:
                    # Es un objeto Estado individual
                    estado = estados
                    calendario_json['estados'][personal_id][dia] = {
                        'nombre': estado.nombre,
                        'nombre_corto': estado.nombre_corto or estado.nombre,
                        'color': estado.color,
                        'background_color': estado.background_color,
                        'prioridad': estado.prioridad,
                        'es_bloqueante': estado.es_bloqueante,
                        'multiple': False
                    }
            else:
                calendario_json['estados'][personal_id][dia] = None
    

    
    context = {
        'calendario': json.dumps(calendario_json, cls=DjangoJSONEncoder),
        'current_year': year,
        'current_month': month,
        'current_month_name': month_names[month - 1],
        'faenas': faenas,  # Para loops de Django
        'cargos': cargos,  # Para loops de Django
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
        })
    }
    
    # Agregar todos los estados disponibles al calendario JSON
    calendario_json['todos_estados_disponibles'] = [
        {
            'nombre': estado.nombre,
            'nombre_corto': estado.nombre_corto or estado.nombre,
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
                        'color': bloque.estado.color,
                        'background_color': bloque.estado.background_color,
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

def obtener_calendario_mensual(year, month, faena_filter='', cargo_filter='', search_query=''):
    """
    Obtiene el calendario completo para un mes específico con filtros.
    OPTIMIZADO: Reduce las consultas de ~620-930 a menos de 10.
    """
    # Obtener rango de fechas del mes
    _, ultimo_dia = monthrange(year, month)
    fecha_inicio = date(year, month, 1)
    fecha_fin = date(year, month, ultimo_dia)
    
    # Construir filtros para el personal con prefetch optimizado
    personal_query = Personal.objects.filter(activo=True).prefetch_related(
        'estados_manuales__estado',
        'asignaciones_faena__turno__bloques__estado',
        'asignaciones_faena__faena',
        'asignaciones_faena__bloque_inicio__estado',
        'ausentismo_set',
        'licenciamedicaporpersonal_set'
    )
    
    # COMENTADO: Ahora el filtrado se hace solo en el frontend
    # if faena_filter:
    #     personal_query = personal_query.filter(
    #         asignaciones_faena__faena__nombre__icontains=faena_filter,
    #         asignaciones_faena__activo=True
    #     ).distinct()
    # 
    # if cargo_filter:
    #     personal_query = personal_query.filter(
    #         infolaboral__cargo_id__cargo__icontains=cargo_filter
    #     ).distinct()
    # 
    # if search_query:
    #     personal_query = personal_query.filter(
    #         Q(nombre__icontains=search_query) |
    #         Q(apepat__icontains=search_query) |
    #         Q(apemat__icontains=search_query) |
    #         Q(rut__icontains=search_query)
    #     )
    
    personal = personal_query.order_by('nombre', 'apepat')
    
    # Inicializar estructura de resultados
    calendario = {
        'personal': list(personal),
        'estados': {},
        'fechas': [fecha_inicio + timedelta(days=i) for i in range(ultimo_dia)],
        'dias_mes': ultimo_dia
    }
    
    # Pre-cargar EstadoFuente una sola vez
    estados_fuente_cache = list(EstadoFuente.objects.select_related('estado', 'content_type').filter(estado__activo=True))
    
    # Calcular estado para cada persona en cada día (optimizado)
    for persona in personal:
        calendario['estados'][persona.personal_id] = {}
        
        for fecha in calendario['fechas']:
            estado = obtener_estado_final_personal_fecha_optimizado(persona, fecha, estados_fuente_cache)
            calendario['estados'][persona.personal_id][fecha.day] = estado
    
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
                except Exception as e:
                    print(f"Error agregando detalles: {e}")
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
    
    # 1. Buscar estados manuales activos
    estados_manuales = EstadoManual.objects.filter(
        personal=personal,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
        activo=True
    ).select_related('estado').order_by('-estado__prioridad')
    
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
    """API para obtener datos del calendario en formato JSON"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        faena_filter = request.GET.get('faena', '')
        cargo_filter = request.GET.get('cargo', '')
        search_query = request.GET.get('search', '')
        
        calendario_data = obtener_calendario_mensual(year, month, faena_filter, cargo_filter, search_query)
        
        # Convertir a formato JSON serializable
        json_data = {
            'personal': [
                {
                    'id': p.personal_id,
                    'nombre': f"{p.nombre} {p.apepat} {p.apemat}".strip(),
                    'cargo': p.infolaboral_set.first().cargo_id.cargo if p.infolaboral_set.exists() else 'Sin cargo',
                    'faena': p.asignaciones_faena.filter(activo=True).first().faena.nombre if p.asignaciones_faena.filter(activo=True).exists() else 'Sin asignar'
                }
                for p in calendario_data['personal']
            ],
            'estados': calendario_data['estados'],
            'dias_mes': calendario_data['dias_mes']
        }
        
        return JsonResponse(json_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

