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
from maquinarias.models import HistorialEquipo, HistorialOT, Equipo, OrdenTrabajo
from ope_calendario.models import HistorialFaena, Faena


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
        fecha_desde = request.GET.get('fecha_desde', None)
        fecha_hasta = request.GET.get('fecha_hasta', None)
        
        # Por ahora retornar estructura básica
        # Aquí se implementarán los diferentes tipos de reportes
        
        return JsonResponse({
            'success': True,
            'message': 'API de reportabilidad - En desarrollo',
            'tipo_reporte': tipo_reporte
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
