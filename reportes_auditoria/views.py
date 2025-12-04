from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from gen_permissions.decorators import permission_required_custom

# Importar modelos de historial
from rrhh_personal.models import HistorialPersonal, HistorialDocumentoPersonal, Personal
from maquinarias.models import HistorialEquipo, HistorialOT, Equipo, OrdenTrabajo, EstadoEquipo
from ope_calendario.models import HistorialFaena, Faena, AsignacionFaena, AsignacionEquipoFaena
from django.utils.dateparse import parse_date


@login_required
@permission_required_custom('reportes_auditoria.view_auditoria')
def auditoria_view(request):
    """Vista principal de auditoría - muestra todos los historiales consolidados"""
    # Obtener lista de usuarios para el filtro
    from django.contrib.auth.models import User
    usuarios = User.objects.filter(is_active=True).order_by('username')
    context = {
        'usuarios': usuarios
    }
    return render(request, 'reportes_auditoria/auditoria.html', context)


@login_required
@permission_required_custom('reportes_auditoria.view_reportabilidad')
def reportabilidad_view(request):
    """Vista principal de reportabilidad - consultas estadísticas"""
    return render(request, 'reportes_auditoria/reportabilidad.html')


@csrf_exempt
@login_required
@permission_required_custom('reportes_auditoria.view_auditoria', is_ajax=True)
@require_http_methods(["GET"])
def api_auditoria(request):
    """
    API para obtener todos los historiales consolidados con filtros y paginación
    """
    try:
        # Parámetros de paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 25))
        
        # Filtros
        tipo_entidad = request.GET.getlist('tipo_entidad[]', [])  # ['PERSONAL', 'EQUIPO', 'FAENA', 'OT', 'DOCUMENTO']
        fecha_desde = request.GET.get('fecha_desde', None)
        fecha_hasta = request.GET.get('fecha_hasta', None)
        usuario_id = request.GET.get('usuario_id', None)
        accion = request.GET.get('accion', None)
        busqueda = request.GET.get('busqueda', '').strip()
        
        # Convertir usuario_id a int si existe
        if usuario_id:
            try:
                usuario_id = int(usuario_id)
            except (ValueError, TypeError):
                usuario_id = None
        
        # Lista para consolidar todos los eventos
        eventos = []
        
        # 1. Historial de Personal
        if not tipo_entidad or 'PERSONAL' in tipo_entidad:
            historial_personal = HistorialPersonal.objects.select_related('personal', 'usuario').all()
            
            if fecha_desde:
                historial_personal = historial_personal.filter(fecha_hora__gte=fecha_desde)
            if fecha_hasta:
                historial_personal = historial_personal.filter(fecha_hora__lte=fecha_hasta)
            if usuario_id:
                historial_personal = historial_personal.filter(usuario_id=usuario_id)
            if accion:
                historial_personal = historial_personal.filter(accion=accion)
            if busqueda:
                historial_personal = historial_personal.filter(
                    Q(descripcion__icontains=busqueda) |
                    Q(personal__nombre__icontains=busqueda) |
                    Q(personal__apepat__icontains=busqueda) |
                    Q(personal__rut__icontains=busqueda)
                )
            
            for evento in historial_personal:
                eventos.append({
                    'id': f"PERSONAL_{evento.id}",
                    'tipo_entidad': 'PERSONAL',
                    'tipo_entidad_display': 'Personal',
                    'entidad_id': evento.personal.personal_id,
                    'entidad_nombre': f"{evento.personal.nombre} {evento.personal.apepat} {evento.personal.apemat}".strip(),
                    'entidad_info': f"RUT: {evento.personal.rut}-{evento.personal.dvrut}",
                    'fecha_hora': evento.fecha_hora,
                    'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                    'usuario_nombre': f"{evento.usuario.first_name} {evento.usuario.last_name}".strip() if evento.usuario and (evento.usuario.first_name or evento.usuario.last_name) else (evento.usuario.username if evento.usuario else 'Sistema'),
                    'accion': evento.accion,
                    'accion_display': evento.get_accion_display(),
                    'descripcion': evento.descripcion,
                    'datos_previos': evento.datos_previos,
                    'datos_nuevos': evento.datos_nuevos,
                })
        
        # 2. Historial de Documentos de Personal
        if not tipo_entidad or 'DOCUMENTO' in tipo_entidad:
            historial_docs = HistorialDocumentoPersonal.objects.select_related('personal', 'usuario').all()
            
            if fecha_desde:
                historial_docs = historial_docs.filter(fecha_hora__gte=fecha_desde)
            if fecha_hasta:
                historial_docs = historial_docs.filter(fecha_hora__lte=fecha_hasta)
            if usuario_id:
                historial_docs = historial_docs.filter(usuario_id=usuario_id)
            if accion:
                historial_docs = historial_docs.filter(accion=accion)
            if busqueda:
                historial_docs = historial_docs.filter(
                    Q(descripcion__icontains=busqueda) |
                    Q(nombre_documento__icontains=busqueda) |
                    Q(personal__nombre__icontains=busqueda) |
                    Q(personal__apepat__icontains=busqueda)
                )
            
            for evento in historial_docs:
                eventos.append({
                    'id': f"DOCUMENTO_{evento.id}",
                    'tipo_entidad': 'DOCUMENTO',
                    'tipo_entidad_display': 'Documento Personal',
                    'entidad_id': evento.personal.personal_id,
                    'entidad_nombre': f"{evento.personal.nombre} {evento.personal.apepat} {evento.personal.apemat}".strip(),
                    'entidad_info': f"Documento: {evento.nombre_documento}",
                    'fecha_hora': evento.fecha_hora,
                    'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                    'usuario_nombre': f"{evento.usuario.first_name} {evento.usuario.last_name}".strip() if evento.usuario and (evento.usuario.first_name or evento.usuario.last_name) else (evento.usuario.username if evento.usuario else 'Sistema'),
                    'accion': evento.accion,
                    'accion_display': evento.get_accion_display(),
                    'descripcion': evento.descripcion,
                    'datos_previos': evento.datos_previos,
                    'datos_nuevos': evento.datos_nuevos,
                })
        
        # 3. Historial de Equipos
        if not tipo_entidad or 'EQUIPO' in tipo_entidad:
            historial_equipos = HistorialEquipo.objects.select_related('equipo', 'usuario').all()
            
            if fecha_desde:
                historial_equipos = historial_equipos.filter(fecha_hora__gte=fecha_desde)
            if fecha_hasta:
                historial_equipos = historial_equipos.filter(fecha_hora__lte=fecha_hasta)
            if usuario_id:
                historial_equipos = historial_equipos.filter(usuario_id=usuario_id)
            if accion:
                historial_equipos = historial_equipos.filter(accion=accion)
            if busqueda:
                historial_equipos = historial_equipos.filter(
                    Q(descripcion__icontains=busqueda) |
                    Q(equipo__nombreEquipo__icontains=busqueda) |
                    Q(equipo__codigoInterno__icontains=busqueda)
                )
            
            for evento in historial_equipos:
                eventos.append({
                    'id': f"EQUIPO_{evento.id}",
                    'tipo_entidad': 'EQUIPO',
                    'tipo_entidad_display': 'Equipo',
                    'entidad_id': evento.equipo.equipo_id,
                    'entidad_nombre': evento.equipo.nombreEquipo,
                    'entidad_info': f"Código: {evento.equipo.codigoInterno}",
                    'fecha_hora': evento.fecha_hora,
                    'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                    'usuario_nombre': f"{evento.usuario.first_name} {evento.usuario.last_name}".strip() if evento.usuario and (evento.usuario.first_name or evento.usuario.last_name) else (evento.usuario.username if evento.usuario else 'Sistema'),
                    'accion': evento.accion,
                    'accion_display': evento.get_accion_display(),
                    'descripcion': evento.descripcion,
                    'datos_previos': evento.datos_previos,
                    'datos_nuevos': evento.datos_nuevos,
                })
        
        # 4. Historial de Faenas
        if not tipo_entidad or 'FAENA' in tipo_entidad:
            historial_faenas = HistorialFaena.objects.select_related('faena', 'usuario', 'personal').all()
            
            if fecha_desde:
                historial_faenas = historial_faenas.filter(fecha_hora__gte=fecha_desde)
            if fecha_hasta:
                historial_faenas = historial_faenas.filter(fecha_hora__lte=fecha_hasta)
            if usuario_id:
                historial_faenas = historial_faenas.filter(usuario_id=usuario_id)
            if accion:
                historial_faenas = historial_faenas.filter(accion=accion)
            if busqueda:
                historial_faenas = historial_faenas.filter(
                    Q(descripcion__icontains=busqueda) |
                    Q(faena__nombre__icontains=busqueda)
                )
            
            for evento in historial_faenas:
                eventos.append({
                    'id': f"FAENA_{evento.id}",
                    'tipo_entidad': 'FAENA',
                    'tipo_entidad_display': 'Faena',
                    'entidad_id': evento.faena.id,
                    'entidad_nombre': evento.faena.nombre,
                    'entidad_info': f"Fechas: {evento.faena.fecha_inicio.strftime('%d/%m/%Y')} - {evento.faena.fecha_fin.strftime('%d/%m/%Y') if evento.faena.fecha_fin else 'Indefinido'}",
                    'fecha_hora': evento.fecha_hora,
                    'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                    'usuario_nombre': f"{evento.usuario.first_name} {evento.usuario.last_name}".strip() if evento.usuario and (evento.usuario.first_name or evento.usuario.last_name) else (evento.usuario.username if evento.usuario else 'Sistema'),
                    'accion': evento.accion,
                    'accion_display': evento.get_accion_display(),
                    'descripcion': evento.descripcion,
                    'datos_previos': evento.datos_previos,
                    'datos_nuevos': evento.datos_nuevos,
                })
        
        # 5. Historial de OTs
        if not tipo_entidad or 'OT' in tipo_entidad:
            historial_ots = HistorialOT.objects.select_related('ot', 'usuario').all()
            
            if fecha_desde:
                historial_ots = historial_ots.filter(fecha_hora__gte=fecha_desde)
            if fecha_hasta:
                historial_ots = historial_ots.filter(fecha_hora__lte=fecha_hasta)
            if usuario_id:
                historial_ots = historial_ots.filter(usuario_id=usuario_id)
            if accion:
                historial_ots = historial_ots.filter(accion=accion)
            if busqueda:
                historial_ots = historial_ots.filter(
                    Q(descripcion__icontains=busqueda) |
                    Q(ot__folio__icontains=busqueda)
                )
            
            for evento in historial_ots:
                eventos.append({
                    'id': f"OT_{evento.id}",
                    'tipo_entidad': 'OT',
                    'tipo_entidad_display': 'Orden de Trabajo',
                    'entidad_id': evento.ot.ot_id,
                    'entidad_nombre': f"OT-{evento.ot.folio}",
                    'entidad_info': f"Equipo: {evento.ot.equipo_id.nombreEquipo if evento.ot.equipo_id else 'N/A'}",
                    'fecha_hora': evento.fecha_hora,
                    'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                    'usuario_nombre': f"{evento.usuario.first_name} {evento.usuario.last_name}".strip() if evento.usuario and (evento.usuario.first_name or evento.usuario.last_name) else (evento.usuario.username if evento.usuario else 'Sistema'),
                    'accion': evento.accion,
                    'accion_display': evento.get_accion_display(),
                    'descripcion': evento.descripcion,
                    'datos_previos': evento.datos_previos,
                    'datos_nuevos': evento.datos_nuevos,
                })
        
        # Ordenar por fecha_hora descendente
        eventos.sort(key=lambda x: x['fecha_hora'], reverse=True)
        
        # Si per_page es muy grande (exportación), devolver todos sin paginación
        if per_page >= 10000:
            # Formatear fechas para el frontend
            eventos_data = []
            for evento in eventos:
                eventos_data.append({
                    **evento,
                    'fecha_hora': evento['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S'),
                    'fecha_hora_formateada': evento['fecha_hora'].strftime('%d/%m/%Y %H:%M'),
                })
            
            return JsonResponse({
                'success': True,
                'eventos': eventos_data,
                'pagination': {
                    'page': 1,
                    'per_page': len(eventos_data),
                    'total': len(eventos_data),
                    'pages': 1,
                    'has_next': False,
                    'has_previous': False,
                }
            })
        
        # Paginación normal
        paginator = Paginator(eventos, per_page)
        page_obj = paginator.get_page(page)
        
        # Formatear fechas para el frontend
        eventos_data = []
        for evento in page_obj:
            eventos_data.append({
                **evento,
                'fecha_hora': evento['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_formateada': evento['fecha_hora'].strftime('%d/%m/%Y %H:%M'),
            })
        
        return JsonResponse({
            'success': True,
            'eventos': eventos_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('reportes_auditoria.view_reportabilidad', is_ajax=True)
@require_http_methods(["GET"])
def api_reportabilidad(request):
    """
    API para consultas estadísticas y reportes
    """
    try:
        tipo_reporte = request.GET.get('tipo_reporte', None)
        fecha_desde_str = request.GET.get('fecha_desde', None)
        fecha_hasta_str = request.GET.get('fecha_hasta', None)
        fecha_str = request.GET.get('fecha', None)
        
        # Convertir fechas de formato DD/MM/YYYY a objetos date
        fecha_desde = None
        fecha_hasta = None
        fecha = None
        
        if fecha_desde_str:
            try:
                # Formato esperado: DD/MM/YYYY
                partes = fecha_desde_str.split('/')
                if len(partes) == 3:
                    fecha_desde = datetime(int(partes[2]), int(partes[1]), int(partes[0])).date()
            except:
                pass
        
        if fecha_hasta_str:
            try:
                partes = fecha_hasta_str.split('/')
                if len(partes) == 3:
                    fecha_hasta = datetime(int(partes[2]), int(partes[1]), int(partes[0])).date()
            except:
                pass
        
        if fecha_str:
            try:
                partes = fecha_str.split('/')
                if len(partes) == 3:
                    fecha = datetime(int(partes[2]), int(partes[1]), int(partes[0])).date()
            except:
                pass
        
        # Parámetros adicionales según el tipo de reporte
        incluir_personal = request.GET.get('incluir_personal', 'true').lower() == 'true'
        incluir_equipos = request.GET.get('incluir_equipos', 'true').lower() == 'true'
        tipo_estado = request.GET.get('tipo_estado', '')
        tipo_asignacion = request.GET.get('tipo_asignacion', '')
        estado_ot = request.GET.get('estado_ot', '')
        
        if not tipo_reporte:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de reporte no especificado'
            }, status=400)
        
        datos = []
        columnas = []
        
        if tipo_reporte == 'faenas_activas':
            # Reporte de Faenas Activas
            faenas = Faena.objects.filter(activo=True)
            
            if fecha_desde:
                faenas = faenas.filter(fecha_inicio__lte=fecha_hasta if fecha_hasta else datetime.now().date())
            if fecha_hasta:
                faenas = faenas.filter(fecha_fin__gte=fecha_desde if fecha_desde else datetime.now().date())
            
            columnas = ['Código', 'Nombre', 'Ubicación', 'Fecha Inicio', 'Fecha Fin', 'Estado']
            if incluir_personal:
                columnas.append('Personal Asignado')
            if incluir_equipos:
                columnas.append('Equipos Asignados')
            
            for faena in faenas:
                fila = {
                    'Código': faena.codigo,
                    'Nombre': faena.nombre,
                    'Ubicación': faena.ubicacion or '',
                    'Fecha Inicio': faena.fecha_inicio.strftime('%d/%m/%Y'),
                    'Fecha Fin': faena.fecha_fin.strftime('%d/%m/%Y') if faena.fecha_fin else 'Indefinido',
                    'Estado': 'Activa' if faena.activo else 'Inactiva'
                }
                
                if incluir_personal:
                    asignaciones = AsignacionFaena.objects.filter(
                        faena=faena,
                        activo=True
                    ).select_related('personal', 'turno')
                    if fecha_desde or fecha_hasta:
                        if fecha_desde:
                            asignaciones = asignaciones.filter(fecha_inicio__lte=fecha_hasta if fecha_hasta else datetime.now().date())
                        if fecha_hasta:
                            asignaciones = asignaciones.filter(
                                Q(fecha_fin__gte=fecha_desde if fecha_desde else datetime.now().date()) | Q(fecha_fin__isnull=True)
                            )
                    personal_list = [f"{a.personal.nombre} {a.personal.apepat} ({a.turno.nombre})" for a in asignaciones]
                    fila['Personal Asignado'] = ', '.join(personal_list) if personal_list else 'Ninguno'
                
                if incluir_equipos:
                    asignaciones_eq = AsignacionEquipoFaena.objects.filter(
                        faena=faena,
                        activo=True
                    ).select_related('equipo')
                    if fecha_desde or fecha_hasta:
                        if fecha_desde:
                            asignaciones_eq = asignaciones_eq.filter(fecha_inicio__lte=fecha_hasta if fecha_hasta else datetime.now().date())
                        if fecha_hasta:
                            asignaciones_eq = asignaciones_eq.filter(
                                Q(fecha_fin__gte=fecha_desde if fecha_desde else datetime.now().date()) | Q(fecha_fin__isnull=True)
                            )
                    equipos_list = [a.equipo.nombreEquipo for a in asignaciones_eq]
                    fila['Equipos Asignados'] = ', '.join(equipos_list) if equipos_list else 'Ninguno'
                
                datos.append(fila)
        
        elif tipo_reporte == 'personal_activo':
            # Reporte de Personal Activo
            if fecha:
                # Una fecha específica
                asignaciones = AsignacionFaena.objects.filter(
                    activo=True,
                    fecha_inicio__lte=fecha,
                ).filter(
                    Q(fecha_fin__gte=fecha) | Q(fecha_fin__isnull=True)
                ).select_related('personal', 'faena', 'turno')
            elif fecha_desde and fecha_hasta:
                # Rango de fechas
                asignaciones = AsignacionFaena.objects.filter(
                    activo=True,
                    fecha_inicio__lte=fecha_hasta,
                ).filter(
                    Q(fecha_fin__gte=fecha_desde) | Q(fecha_fin__isnull=True)
                ).select_related('personal', 'faena', 'turno')
            else:
                # Fecha actual
                hoy = datetime.now().date()
                asignaciones = AsignacionFaena.objects.filter(
                    activo=True,
                    fecha_inicio__lte=hoy,
                ).filter(
                    Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
                ).select_related('personal', 'faena', 'turno')
            
            columnas = ['RUT', 'Nombre Completo', 'Faena', 'Turno', 'Fecha Inicio', 'Fecha Fin']
            
            personal_visto = set()
            for asignacion in asignaciones:
                personal_id = asignacion.personal.personal_id
                if personal_id not in personal_visto:
                    personal_visto.add(personal_id)
                    datos.append({
                        'RUT': f"{asignacion.personal.rut}-{asignacion.personal.dvrut}",
                        'Nombre Completo': f"{asignacion.personal.nombre} {asignacion.personal.apepat} {asignacion.personal.apemat}".strip(),
                        'Faena': asignacion.faena.nombre,
                        'Turno': asignacion.turno.nombre,
                        'Fecha Inicio': asignacion.fecha_inicio.strftime('%d/%m/%Y'),
                        'Fecha Fin': asignacion.fecha_fin.strftime('%d/%m/%Y') if asignacion.fecha_fin else 'Indefinido'
                    })
        
        elif tipo_reporte == 'equipos_mantencion':
            # Reporte de Equipos en Mantención
            # El estado del equipo se obtiene a través de las OTs activas
            hoy = datetime.now().date()
            fecha_filtro_desde = fecha_desde if fecha_desde else hoy
            fecha_filtro_hasta = fecha_hasta if fecha_hasta else hoy
            
            # Obtener equipos activos
            equipos_query = Equipo.objects.filter(activo=True).select_related('modeloEquipo_id')
            
            # Obtener estados de equipos que coincidan con el filtro
            estados_filtro = None
            if tipo_estado == 'mantencion':
                estados_filtro = EstadoEquipo.objects.filter(
                    Q(nombre__icontains='mantención') | Q(nombre__icontains='mantencion')
                )
            elif tipo_estado == 'detenido':
                estados_filtro = EstadoEquipo.objects.filter(nombre__icontains='detenido')
            
            columnas = ['Código', 'Nombre', 'Modelo', 'Estado', 'OT Folio', 'Fecha Inicio OT', 'Fecha Fin OT']
            
            equipos_con_estado = set()
            
            for equipo in equipos_query:
                # Buscar OTs activas del equipo en el rango de fechas
                ots_activas = OrdenTrabajo.objects.filter(
                    equipo_id=equipo,
                    fecha_inicio__lte=fecha_filtro_hasta
                ).filter(
                    Q(fecha_fin__gte=fecha_filtro_desde) | Q(fecha_fin__isnull=True)
                ).select_related('estado_equipo_id').order_by('-fecha_inicio')
                
                # Si hay filtro de tipo de estado, filtrar las OTs
                if estados_filtro:
                    ots_activas = ots_activas.filter(estado_equipo_id__in=estados_filtro)
                
                # Si no hay filtro o hay OTs que coinciden, agregar al reporte
                if not estados_filtro or ots_activas.exists():
                    for ot in ots_activas:
                        estado_nombre = ot.estado_equipo_id.nombre if ot.estado_equipo_id else 'N/A'
                        
                        # Evitar duplicados si un equipo tiene múltiples OTs
                        clave = f"{equipo.equipo_id}_{ot.ot_id}"
                        if clave not in equipos_con_estado:
                            equipos_con_estado.add(clave)
                            datos.append({
                                'Código': equipo.codigoInterno,
                                'Nombre': equipo.nombreEquipo,
                                'Modelo': str(equipo.modeloEquipo_id),
                                'Estado': estado_nombre,
                                'OT Folio': ot.folio,
                                'Fecha Inicio OT': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'N/A',
                                'Fecha Fin OT': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Indefinido'
                            })
        
        elif tipo_reporte == 'asignaciones_personal':
            # Reporte de Asignaciones de Personal
            asignaciones = AsignacionFaena.objects.filter(activo=True).select_related('personal', 'faena', 'turno')
            
            if fecha_desde:
                asignaciones = asignaciones.filter(fecha_inicio__lte=fecha_hasta if fecha_hasta else datetime.now().date())
            if fecha_hasta:
                asignaciones = asignaciones.filter(
                    Q(fecha_fin__gte=fecha_desde if fecha_desde else datetime.now().date()) | Q(fecha_fin__isnull=True)
                )
            
            columnas = ['RUT', 'Nombre Completo', 'Faena', 'Turno', 'Fecha Inicio', 'Fecha Fin']
            
            for asignacion in asignaciones:
                datos.append({
                    'RUT': f"{asignacion.personal.rut}-{asignacion.personal.dvrut}",
                    'Nombre Completo': f"{asignacion.personal.nombre} {asignacion.personal.apepat} {asignacion.personal.apemat}".strip(),
                    'Faena': asignacion.faena.nombre,
                    'Turno': asignacion.turno.nombre,
                    'Fecha Inicio': asignacion.fecha_inicio.strftime('%d/%m/%Y'),
                    'Fecha Fin': asignacion.fecha_fin.strftime('%d/%m/%Y') if asignacion.fecha_fin else 'Indefinido'
                })
        
        elif tipo_reporte == 'asignaciones_equipos':
            # Reporte de Asignaciones de Equipos
            if tipo_asignacion == 'faena':
                asignaciones = AsignacionEquipoFaena.objects.filter(activo=True).select_related('equipo', 'faena')
            elif tipo_asignacion == 'ot':
                # Asignaciones a OTs (a través de la relación en OrdenTrabajo)
                ots = OrdenTrabajo.objects.filter(
                    equipo_id__isnull=False
                ).select_related('equipo_id')
                
                if fecha_desde:
                    ots = ots.filter(fecha_creacion__gte=fecha_desde)
                if fecha_hasta:
                    ots = ots.filter(fecha_creacion__lte=fecha_hasta)
                
                columnas = ['Equipo', 'Código', 'OT Folio', 'Fecha Creación', 'Estado']
                for ot in ots:
                    datos.append({
                        'Equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                        'Código': ot.equipo_id.codigoInterno if ot.equipo_id else 'N/A',
                        'OT Folio': ot.folio,
                        'Fecha Creación': ot.fecha_creacion.strftime('%d/%m/%Y') if ot.fecha_creacion else 'N/A',
                        'Estado': ot.estado_ot_id.nombreEstado if ot.estado_ot_id else 'N/A'
                    })
                
                return JsonResponse({
                    'success': True,
                    'tipo_reporte': tipo_reporte,
                    'columnas': columnas,
                    'datos': datos,
                    'total': len(datos)
                })
            else:
                # Todas las asignaciones (faenas)
                asignaciones = AsignacionEquipoFaena.objects.filter(activo=True).select_related('equipo', 'faena')
            
            if fecha_desde:
                asignaciones = asignaciones.filter(fecha_inicio__lte=fecha_hasta if fecha_hasta else datetime.now().date())
            if fecha_hasta:
                asignaciones = asignaciones.filter(
                    Q(fecha_fin__gte=fecha_desde if fecha_desde else datetime.now().date()) | Q(fecha_fin__isnull=True)
                )
            
            columnas = ['Equipo', 'Código', 'Faena', 'Fecha Inicio', 'Fecha Fin']
            
            for asignacion in asignaciones:
                datos.append({
                    'Equipo': asignacion.equipo.nombreEquipo,
                    'Código': asignacion.equipo.codigoInterno,
                    'Faena': asignacion.faena.nombre,
                    'Fecha Inicio': asignacion.fecha_inicio.strftime('%d/%m/%Y'),
                    'Fecha Fin': asignacion.fecha_fin.strftime('%d/%m/%Y') if asignacion.fecha_fin else 'Indefinido'
                })
        
        elif tipo_reporte == 'ordenes_trabajo':
            # Reporte de Órdenes de Trabajo
            ots = OrdenTrabajo.objects.select_related('equipo_id', 'estado_ot_id', 'tipo_mantenimiento_id')
            
            if fecha_desde:
                ots = ots.filter(fecha_creacion__gte=fecha_desde)
            if fecha_hasta:
                ots = ots.filter(fecha_creacion__lte=fecha_hasta)
            if estado_ot:
                ots = ots.filter(estado_ot_id__nombre__icontains=estado_ot)
            
            columnas = ['Folio', 'Equipo', 'Tipo Mantención', 'Estado', 'Fecha Creación']
            
            for ot in ots:
                datos.append({
                    'Folio': ot.folio,
                    'Equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                    'Tipo Mantención': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else 'N/A',
                    'Estado': ot.estado_ot_id.nombre if ot.estado_ot_id else 'N/A',
                    'Fecha Creación': ot.fecha_creacion.strftime('%d/%m/%Y') if ot.fecha_creacion else 'N/A'
                })
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Tipo de reporte desconocido: {tipo_reporte}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'tipo_reporte': tipo_reporte,
            'columnas': columnas,
            'datos': datos,
            'total': len(datos)
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
