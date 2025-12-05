"""
Vistas para el panel de vencimientos de documentos.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import date, timedelta
from gen_permissions.decorators import permission_required_custom

from rrhh_personal.models import (
    Personal, LicenciaPorPersonal, LicenciaInternaPorPersonal,
    LicenciaMedicaPorPersonal, Certificacion, Examen
)
from maquinarias.models import Equipo, DocumentoMaquinaria
from .utils import calcular_estado_vencimiento


@login_required
@permission_required_custom('vencimientos_documentos.view_vencimientos')
def vencimientos_view(request):
    """
    Vista principal del panel de vencimientos de documentos.
    """
    return render(request, 'vencimientos_documentos/vencimientos.html')


def aplicar_filtros_documento(estado: dict, filtro_estado: str, filtro_tipo: str, filtro_dias: str, tipo_doc: str) -> bool:
    """
    Aplica los filtros a un documento para determinar si debe incluirse en los resultados.
    
    Args:
        estado: Diccionario con el estado del documento
        filtro_estado: Filtro por estado ('todos', 'vencidos', 'por_vencer', 'vigentes')
        filtro_tipo: Filtro por tipo de documento
        filtro_dias: Filtro por rango de días (número como string)
        tipo_doc: Tipo de documento actual
    
    Returns:
        True si el documento debe incluirse, False en caso contrario
    """
    # Filtro por tipo de documento
    if filtro_tipo and filtro_tipo != tipo_doc:
        return False
    
    # Filtro por estado
    dias_restantes = estado.get('dias_restantes')
    
    if filtro_estado == 'vencidos':
        if dias_restantes is None or dias_restantes >= 0:
            return False
    elif filtro_estado == 'por_vencer':
        if dias_restantes is None or dias_restantes < 0 or dias_restantes >= 45:
            return False
    elif filtro_estado == 'vigentes':
        if dias_restantes is None or dias_restantes < 0:
            return False
    
    # Filtro por rango de días
    if filtro_dias:
        try:
            dias_maximos = int(filtro_dias)
            if dias_restantes is None or dias_restantes > dias_maximos:
                return False
        except ValueError:
            pass
    
    return True


def _obtener_documentos_personal(request):
    """
    Función auxiliar para obtener documentos de personal (reutilizable).
    Retorna la lista de documentos sin crear respuesta JSON.
    """
    documentos = []
    
    try:
        hoy = date.today()
        
        # Obtener filtros de la request
        filtro_estado = request.GET.get('estado', 'todos')
        filtro_tipo = request.GET.get('tipo', '')
        filtro_dias = request.GET.get('dias', '')
        buscar = request.GET.get('buscar', '').strip()
        solo_activos = request.GET.get('solo_activos', 'true').lower() == 'true'
        
        # Query base para personal
        personal_query = Personal.objects.all()
        if solo_activos:
            personal_query = personal_query.filter(activo=True)
        
        # Aplicar búsqueda
        if buscar:
            personal_query = personal_query.filter(
                Q(nombre__icontains=buscar) |
                Q(apepat__icontains=buscar) |
                Q(apemat__icontains=buscar) |
                Q(rut__icontains=buscar) |
                Q(dvrut__icontains=buscar)
            )
        
        personal_list = list(personal_query.select_related('region_id', 'comuna_id'))
        
        if not personal_list:
            return documentos
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error inicial en _obtener_documentos_personal: {str(e)}", exc_info=True)
        raise
    
    # 1. Documentos directos del modelo Personal (con fecha de vencimiento)
    for personal in personal_list:
        # Carnet con fecha de vencimiento
        if personal.fecha_vencimiento_carnet:
            estado = calcular_estado_vencimiento(personal.fecha_vencimiento_carnet)
            
            # Aplicar filtros
            if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'CARNET'):
                documentos.append({
                    'tipo': 'DOCUMENTO_PERSONAL',
                    'tipo_nombre': 'Carnet',
                    'nombre': 'Fotocopia Carnet',
                    'personal_id': personal.personal_id,
                    'personal_nombre': f"{personal.nombre} {personal.apepat} {personal.apemat or ''}".strip(),
                    'personal_rut': f"{personal.rut}-{personal.dvrut}",
                    'fecha_vencimiento': personal.fecha_vencimiento_carnet.strftime('%d/%m/%Y'),
                    'fecha_vencimiento_iso': personal.fecha_vencimiento_carnet.isoformat(),
                    'dias_restantes': estado['dias_restantes'],
                    'estado': estado['estado'],
                    'color': estado['color'],
                    'badge_class': estado['badge_class'],
                    'icono': estado['icono'],
                    'texto_estado': estado['texto'],
                    'identificador': f"carnet_{personal.personal_id}",
                    'url_editar': f"/rrhh/personal/{personal.personal_id}/documentation/"
                })
    
    # 2. Licencias de conducir (múltiples por personal)
    licencias_conducir = LicenciaPorPersonal.objects.filter(
        personal_id__in=[p.personal_id for p in personal_list]
    ).select_related('personal_id').prefetch_related('tipos')
    
    for licencia in licencias_conducir:
        if not licencia.fechaVencimiento or not licencia.personal_id:
            continue
        try:
            estado = calcular_estado_vencimiento(licencia.fechaVencimiento)
            tipos_list = list(licencia.tipos.all())
            tipos_str = ", ".join([t.tipoLicencia for t in tipos_list]) if tipos_list else ""
        
            if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'LICENCIA_CONDUCIR'):
                documentos.append({
                    'tipo': 'LICENCIA_CONDUCIR',
                    'tipo_nombre': 'Licencia de Conducir',
                    'nombre': f'Licencia de Conducir ({tipos_str})' if tipos_str else 'Licencia de Conducir',
                    'personal_id': licencia.personal_id.personal_id,
                    'personal_nombre': f"{licencia.personal_id.nombre} {licencia.personal_id.apepat} {licencia.personal_id.apemat or ''}".strip(),
                    'personal_rut': f"{licencia.personal_id.rut}-{licencia.personal_id.dvrut}",
                    'fecha_vencimiento': licencia.fechaVencimiento.strftime('%d/%m/%Y'),
                    'fecha_vencimiento_iso': licencia.fechaVencimiento.isoformat(),
                    'dias_restantes': estado['dias_restantes'],
                    'estado': estado['estado'],
                    'color': estado['color'],
                    'badge_class': estado['badge_class'],
                    'icono': estado['icono'],
                    'texto_estado': estado['texto'],
                    'identificador': f"licencia_conducir_{licencia.licenciaPorPersonal_id}",
                    'url_editar': f"/rrhh/personal/{licencia.personal_id.personal_id}/documentation/"
                })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error procesando licencia {licencia.licenciaPorPersonal_id}: {str(e)}")
            continue
    
    # 3. Licencias internas (múltiples por personal)
    licencias_internas = LicenciaInternaPorPersonal.objects.filter(
        personal_id__in=[p.personal_id for p in personal_list]
    ).select_related('personal_id', 'tipoLicenciaInterna_id')
    
    for licencia in licencias_internas:
        if not licencia.fechaVencimiento or not licencia.personal_id:
            continue
        estado = calcular_estado_vencimiento(licencia.fechaVencimiento)
        tipo_nombre = licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else 'N/A'
        
        if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'LICENCIA_INTERNA'):
            documentos.append({
                'tipo': 'LICENCIA_INTERNA',
                'tipo_nombre': 'Licencia Interna',
                'nombre': f'Licencia Interna: {tipo_nombre}',
                'personal_id': licencia.personal_id.personal_id,
                'personal_nombre': f"{licencia.personal_id.nombre} {licencia.personal_id.apepat} {licencia.personal_id.apemat or ''}".strip(),
                'personal_rut': f"{licencia.personal_id.rut}-{licencia.personal_id.dvrut}",
                'fecha_vencimiento': licencia.fechaVencimiento.strftime('%d/%m/%Y'),
                'fecha_vencimiento_iso': licencia.fechaVencimiento.isoformat(),
                'dias_restantes': estado['dias_restantes'],
                'estado': estado['estado'],
                'color': estado['color'],
                'badge_class': estado['badge_class'],
                'icono': estado['icono'],
                'texto_estado': estado['texto'],
                'identificador': f"licencia_interna_{licencia.licenciaInterna_id}",
                'url_editar': f"/rrhh/personal/{licencia.personal_id.personal_id}/documentation/"
            })
    
    # 4. Licencias médicas (múltiples por personal)
    licencias_medicas = LicenciaMedicaPorPersonal.objects.filter(
        personal_id__in=[p.personal_id for p in personal_list]
    ).select_related('personal_id', 'tipoLicenciaMedica_id')
    
    for licencia in licencias_medicas:
        if not licencia.fecha_fin_licencia or not licencia.personal_id:
            continue
        estado = calcular_estado_vencimiento(licencia.fecha_fin_licencia)
        tipo_nombre = licencia.tipoLicenciaMedica_id.tipoLicenciaMedica if licencia.tipoLicenciaMedica_id else 'N/A'
        
        if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'LICENCIA_MEDICA'):
            documentos.append({
                'tipo': 'LICENCIA_MEDICA',
                'tipo_nombre': 'Licencia Médica',
                'nombre': f'Licencia Médica: {tipo_nombre}',
                'personal_id': licencia.personal_id.personal_id,
                'personal_nombre': f"{licencia.personal_id.nombre} {licencia.personal_id.apepat} {licencia.personal_id.apemat or ''}".strip(),
                'personal_rut': f"{licencia.personal_id.rut}-{licencia.personal_id.dvrut}",
                'fecha_vencimiento': licencia.fecha_fin_licencia.strftime('%d/%m/%Y'),
                'fecha_vencimiento_iso': licencia.fecha_fin_licencia.isoformat(),
                'dias_restantes': estado['dias_restantes'],
                'estado': estado['estado'],
                'color': estado['color'],
                'badge_class': estado['badge_class'],
                'icono': estado['icono'],
                'texto_estado': estado['texto'],
                'identificador': f"licencia_medica_{licencia.licenciaMedicaPorPersonal_id}",
                'url_editar': f"/rrhh/personal/{licencia.personal_id.personal_id}/documentation/"
            })
    
    # 5. Certificaciones (múltiples por personal)
    certificaciones = Certificacion.objects.filter(
        personal_id__in=[p.personal_id for p in personal_list]
    ).select_related('personal_id', 'tipoCertificacion_id')
    
    for cert in certificaciones:
        if not cert.fechaVencimiento or not cert.personal_id:
            continue
        estado = calcular_estado_vencimiento(cert.fechaVencimiento)
        tipo_nombre = cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else 'N/A'
        
        if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'CERTIFICACION'):
            documentos.append({
                'tipo': 'CERTIFICACION',
                'tipo_nombre': 'Certificación',
                'nombre': f'Certificación: {tipo_nombre}',
                'personal_id': cert.personal_id.personal_id,
                'personal_nombre': f"{cert.personal_id.nombre} {cert.personal_id.apepat} {cert.personal_id.apemat or ''}".strip(),
                'personal_rut': f"{cert.personal_id.rut}-{cert.personal_id.dvrut}",
                'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
                'fecha_vencimiento_iso': cert.fechaVencimiento.isoformat(),
                'dias_restantes': estado['dias_restantes'],
                'estado': estado['estado'],
                'color': estado['color'],
                'badge_class': estado['badge_class'],
                'icono': estado['icono'],
                'texto_estado': estado['texto'],
                'identificador': f"certificacion_{cert.certif_id}",
                'url_editar': f"/rrhh/personal/{cert.personal_id.personal_id}/documentation/"
            })
    
    # 6. Exámenes (múltiples por personal)
    examenes = Examen.objects.filter(
        personal_id__in=[p.personal_id for p in personal_list]
    ).select_related('personal_id', 'tipoEx_id')
    
    for examen in examenes:
        if not examen.fechaVencimiento or not examen.personal_id:
            continue
        estado = calcular_estado_vencimiento(examen.fechaVencimiento)
        tipo_nombre = examen.tipoEx_id.tipoExamen if examen.tipoEx_id else 'N/A'
        
        if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'EXAMEN'):
            documentos.append({
                'tipo': 'EXAMEN',
                'tipo_nombre': 'Examen',
                'nombre': f'Examen: {tipo_nombre}',
                'personal_id': examen.personal_id.personal_id,
                'personal_nombre': f"{examen.personal_id.nombre} {examen.personal_id.apepat} {examen.personal_id.apemat or ''}".strip(),
                'personal_rut': f"{examen.personal_id.rut}-{examen.personal_id.dvrut}",
                'fecha_vencimiento': examen.fechaVencimiento.strftime('%d/%m/%Y'),
                'fecha_vencimiento_iso': examen.fechaVencimiento.isoformat(),
                'dias_restantes': estado['dias_restantes'],
                'estado': estado['estado'],
                'color': estado['color'],
                'badge_class': estado['badge_class'],
                'icono': estado['icono'],
                'texto_estado': estado['texto'],
                'identificador': f"examen_{examen.examen_id}",
                'url_editar': f"/rrhh/personal/{examen.personal_id.personal_id}/documentation/"
            })
    
    # Ordenar por días restantes (más críticos primero, luego por fecha)
    documentos.sort(key=lambda x: (
        x['dias_restantes'] if x['dias_restantes'] is not None else 9999,
        x['fecha_vencimiento_iso'] if x.get('fecha_vencimiento_iso') else ''
    ))
    
    return documentos


@login_required
@permission_required_custom('vencimientos_documentos.view_vencimientos')
@require_http_methods(["GET"])
def api_vencimientos_personal(request):
    """
    API para obtener todos los documentos de personal con sus estados de vencimiento.
    """
    try:
        documentos = _obtener_documentos_personal(request)
        
        return JsonResponse({
            'success': True,
            'documentos': documentos,
            'total': len(documentos)
        })
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        error_trace = traceback.format_exc()
        logger.error(f"Error en api_vencimientos_personal: {str(e)}\n{error_trace}")
        return JsonResponse({
            'success': False,
            'error': f"{str(e)}. Revisa los logs del servidor para más detalles.",
            'documentos': [],
            'total': 0
        }, status=500)


def _obtener_documentos_maquinarias(request):
    """
    Función auxiliar para obtener documentos de maquinarias (reutilizable).
    Retorna la lista de documentos sin crear respuesta JSON.
    """
    hoy = date.today()
    
    # Obtener filtros de la request
    filtro_estado = request.GET.get('estado', 'todos')
    filtro_tipo = request.GET.get('tipo', '')
    filtro_dias = request.GET.get('dias', '')
    buscar = request.GET.get('buscar', '').strip()
    solo_activos = request.GET.get('solo_activos', 'true').lower() == 'true'
    
    documentos = []
    
    # Query base para equipos
    equipos_query = Equipo.objects.all()
    if solo_activos:
        equipos_query = equipos_query.filter(activo=True)
    
    # Aplicar búsqueda
    if buscar:
        equipos_query = equipos_query.filter(
            Q(nombreEquipo__icontains=buscar) |
            Q(codigoInterno__icontains=buscar) |
            Q(patente__icontains=buscar)
        )
    
    equipos_list = list(equipos_query.select_related('empresa_id', 'modeloEquipo_id'))
    
    if not equipos_list:
        return documentos
    
    # Obtener todos los documentos de los equipos
    documentos_maquinarias = DocumentoMaquinaria.objects.filter(
        equipo_id__in=[e.equipo_id for e in equipos_list]
    ).select_related('equipo_id', 'tipo_documento_id')
    
    for doc in documentos_maquinarias:
        estado = calcular_estado_vencimiento(doc.fecha_vencimiento)
        
        if aplicar_filtros_documento(estado, filtro_estado, filtro_tipo, filtro_dias, 'DOCUMENTO_MAQUINARIA'):
            documentos.append({
                'tipo': 'DOCUMENTO_MAQUINARIA',
                'tipo_nombre': 'Documento de Maquinaria',
                'nombre': doc.tipo_documento_id.nombre,
                'equipo_id': doc.equipo_id.equipo_id,
                'equipo_nombre': doc.equipo_id.nombreEquipo,
                'equipo_codigo': doc.equipo_id.codigoInterno,
                'equipo_patente': doc.equipo_id.patente or '',
                'fecha_vencimiento': doc.fecha_vencimiento.strftime('%d/%m/%Y') if doc.fecha_vencimiento else None,
                'fecha_vencimiento_iso': doc.fecha_vencimiento.isoformat() if doc.fecha_vencimiento else None,
                'dias_restantes': estado['dias_restantes'],
                'estado': estado['estado'],
                'color': estado['color'],
                'badge_class': estado['badge_class'],
                'icono': estado['icono'],
                'texto_estado': estado['texto'],
                'identificador': f"doc_maquinaria_{doc.documento_id}",
                'url_editar': f"/maquinarias/equipos/{doc.equipo_id.equipo_id}/documentacion/"
            })
    
    # Ordenar por días restantes (más críticos primero)
    documentos.sort(key=lambda x: (
        x['dias_restantes'] if x['dias_restantes'] is not None else 9999,
        x['fecha_vencimiento_iso'] if x.get('fecha_vencimiento_iso') else ''
    ))
    
    return documentos


@login_required
@permission_required_custom('vencimientos_documentos.view_vencimientos')
@require_http_methods(["GET"])
def api_vencimientos_maquinarias(request):
    """
    API para obtener todos los documentos de maquinarias con sus estados de vencimiento.
    """
    try:
        documentos = _obtener_documentos_maquinarias(request)
        
        return JsonResponse({
            'success': True,
            'documentos': documentos,
            'total': len(documentos)
        })
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        error_trace = traceback.format_exc()
        logger.error(f"Error en api_vencimientos_maquinarias: {str(e)}\n{error_trace}")
        return JsonResponse({
            'success': False,
            'error': f"{str(e)}. Revisa los logs del servidor para más detalles.",
            'documentos': [],
            'total': 0
        }, status=500)


@login_required
@permission_required_custom('vencimientos_documentos.view_vencimientos')
@require_http_methods(["GET"])
def exportar_excel_personal(request):
    """
    Exporta los documentos de personal a Excel.
    """
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    
    # Obtener datos usando la función auxiliar
    documentos = _obtener_documentos_personal(request)
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vencimientos Personal"
    
    # Encabezados
    headers = ['Personal', 'RUT', 'Tipo Documento', 'Nombre Documento', 'Fecha Vencimiento', 'Días Restantes', 'Estado']
    ws.append(headers)
    
    # Estilos para encabezados
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Colores para estados
    color_map = {
        'vencido': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'critico': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'naranja': PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid"),
        'amarillo': PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid"),
        'verde': PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid"),
    }
    
    # Agregar datos
    for doc in documentos:
        row = [
            doc['personal_nombre'],
            doc['personal_rut'],
            doc['tipo_nombre'],
            doc['nombre'],
            doc['fecha_vencimiento'],
            doc['dias_restantes'] if doc['dias_restantes'] is not None else 'N/A',
            doc['texto_estado']
        ]
        ws.append(row)
        
        # Aplicar color según estado
        estado = doc.get('estado', '')
        if estado in color_map:
            for col_num in range(1, len(headers) + 1):
                ws.cell(row=ws.max_row, column=col_num).fill = color_map[estado]
    
    # Ajustar ancho de columnas
    column_widths = [25, 15, 20, 30, 18, 15, 20]
    for col_num, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = width
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="vencimientos_personal.xlsx"'
    
    wb.save(response)
    return response


@login_required
@permission_required_custom('vencimientos_documentos.view_vencimientos')
@require_http_methods(["GET"])
def exportar_excel_maquinarias(request):
    """
    Exporta los documentos de maquinarias a Excel.
    """
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    
    # Obtener datos usando la función auxiliar
    documentos = _obtener_documentos_maquinarias(request)
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vencimientos Maquinarias"
    
    # Encabezados
    headers = ['Equipo', 'Código', 'Patente', 'Tipo Documento', 'Fecha Vencimiento', 'Días Restantes', 'Estado']
    ws.append(headers)
    
    # Estilos para encabezados
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Colores para estados
    color_map = {
        'vencido': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'critico': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'naranja': PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid"),
        'amarillo': PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid"),
        'verde': PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid"),
    }
    
    # Agregar datos
    for doc in documentos:
        row = [
            doc['equipo_nombre'],
            doc['equipo_codigo'],
            doc.get('equipo_patente', ''),
            doc['nombre'],
            doc['fecha_vencimiento'] if doc.get('fecha_vencimiento') else 'N/A',
            doc['dias_restantes'] if doc['dias_restantes'] is not None else 'N/A',
            doc['texto_estado']
        ]
        ws.append(row)
        
        # Aplicar color según estado
        estado = doc.get('estado', '')
        if estado in color_map:
            for col_num in range(1, len(headers) + 1):
                ws.cell(row=ws.max_row, column=col_num).fill = color_map[estado]
    
    # Ajustar ancho de columnas
    column_widths = [25, 15, 15, 25, 18, 15, 20]
    for col_num, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = width
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="vencimientos_maquinarias.xlsx"'
    
    wb.save(response)
    return response
