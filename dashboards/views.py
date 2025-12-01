from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Avg, F
from datetime import datetime, timedelta, date
from gen_permissions.decorators import permission_required_custom, permission_required_multiple

# Importar modelos necesarios
from rrhh_personal.models import (
    Personal, HistorialPersonal, LicenciaMedicaPorPersonal, 
    Ausentismo, Examen, Certificacion, LicenciaPorPersonal,
    LicenciaInternaPorPersonal, TipoAusentismo, TipoLicenciaMedica
)
from maquinarias.models import Equipo, OrdenTrabajo, HistorialEquipo, DocumentoMaquinaria
from ope_calendario.models import Faena, AsignacionFaena


@login_required
@permission_required_multiple(
    'dashboards.view_dashboard_rrhh',
    'dashboards.view_dashboard_operaciones',
    'dashboards.view_dashboard_maquinarias',
    'dashboards.view_dashboard_gerencia',
    require_all=False  # Requiere al menos uno de los permisos
)
def dashboards_view(request):
    """Vista principal de dashboards con tabs por área"""
    return render(request, 'dashboards/dashboards.html')


@csrf_exempt
@login_required
@permission_required_custom('dashboards.view_dashboard_rrhh', is_ajax=True)
@require_http_methods(["GET"])
def api_dashboard_rrhh(request):
    """
    API para obtener datos del dashboard de RRHH
    """
    try:
        hoy = date.today()
        fecha_limite_30_dias = hoy + timedelta(days=30)
        
        # Estadísticas básicas
        total_personal = Personal.objects.filter(activo=True).count()
        total_personal_inactivo = Personal.objects.filter(activo=False).count()
        
        # Personal en faena (con asignaciones activas)
        personal_en_faena_ids = AsignacionFaena.objects.filter(
            activo=True,
            personal__activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).values_list('personal_id', flat=True).distinct()
        
        personal_en_faena_count = len(personal_en_faena_ids)
        
        # Personal con licencia médica activa
        personal_con_licencia_ids = LicenciaMedicaPorPersonal.objects.filter(
            personal_id__activo=True,
            fecha_fin_licencia__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_con_licencia_count = len(personal_con_licencia_ids)
        
        # Personal con ausentismo activo
        personal_con_ausentismo_ids = Ausentismo.objects.filter(
            personal_id__activo=True,
            fechafin__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_con_ausentismo_count = len(personal_con_ausentismo_ids)
        
        # Personal disponible: activo, no en faena, sin licencia, sin ausentismo
        personal_no_disponible_ids = set(personal_en_faena_ids) | set(personal_con_licencia_ids) | set(personal_con_ausentismo_ids)
        personal_disponible_count = total_personal - len(personal_no_disponible_ids)
        
        # Documentos por vencer en 30 días
        documentos_por_vencer = []
        
        # Exámenes por vencer
        examenes_por_vencer = Examen.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoEx_id').order_by('fechaVencimiento')
        
        for examen in examenes_por_vencer:
            dias_restantes = (examen.fechaVencimiento - hoy).days
            documentos_por_vencer.append({
                'tipo': 'Examen',
                'nombre': f"{examen.tipoEx_id}",
                'personal': f"{examen.personal_id.nombre} {examen.personal_id.apepat} {examen.personal_id.apemat}",
                'personal_rut': f"{examen.personal_id.rut}-{examen.personal_id.dvrut}",
                'fecha_vencimiento': examen.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Certificaciones por vencer
        certificaciones_por_vencer = Certificacion.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoCertificacion_id').order_by('fechaVencimiento')
        
        for cert in certificaciones_por_vencer:
            dias_restantes = (cert.fechaVencimiento - hoy).days
            documentos_por_vencer.append({
                'tipo': 'Certificación',
                'nombre': f"{cert.tipoCertificacion_id}",
                'personal': f"{cert.personal_id.nombre} {cert.personal_id.apepat} {cert.personal_id.apemat}",
                'personal_rut': f"{cert.personal_id.rut}-{cert.personal_id.dvrut}",
                'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Licencias de conducir por vencer
        licencias_por_vencer = LicenciaPorPersonal.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id').order_by('fechaVencimiento')
        
        for lic in licencias_por_vencer:
            dias_restantes = (lic.fechaVencimiento - hoy).days
            tipos = ', '.join([t.tipoLicencia for t in lic.tipos.all()])
            documentos_por_vencer.append({
                'tipo': 'Licencia de Conducir',
                'nombre': f"Licencia {tipos}",
                'personal': f"{lic.personal_id.nombre} {lic.personal_id.apepat} {lic.personal_id.apemat}",
                'personal_rut': f"{lic.personal_id.rut}-{lic.personal_id.dvrut}",
                'fecha_vencimiento': lic.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Licencias internas por vencer
        licencias_internas_por_vencer = LicenciaInternaPorPersonal.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoLicenciaInterna_id').order_by('fechaVencimiento')
        
        for lic_int in licencias_internas_por_vencer:
            dias_restantes = (lic_int.fechaVencimiento - hoy).days
            documentos_por_vencer.append({
                'tipo': 'Licencia Interna',
                'nombre': f"{lic_int.tipoLicenciaInterna_id}",
                'personal': f"{lic_int.personal_id.nombre} {lic_int.personal_id.apepat} {lic_int.personal_id.apemat}",
                'personal_rut': f"{lic_int.personal_id.rut}-{lic_int.personal_id.dvrut}",
                'fecha_vencimiento': lic_int.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Carnets por vencer
        carnets_por_vencer = Personal.objects.filter(
            activo=True,
            fecha_vencimiento_carnet__gte=hoy,
            fecha_vencimiento_carnet__lte=fecha_limite_30_dias
        ).exclude(fecha_vencimiento_carnet__isnull=True)
        
        for personal in carnets_por_vencer:
            dias_restantes = (personal.fecha_vencimiento_carnet - hoy).days
            documentos_por_vencer.append({
                'tipo': 'Carnet',
                'nombre': 'Carnet de Identidad',
                'personal': f"{personal.nombre} {personal.apepat} {personal.apemat}",
                'personal_rut': f"{personal.rut}-{personal.dvrut}",
                'fecha_vencimiento': personal.fecha_vencimiento_carnet.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Ordenar por días restantes
        documentos_por_vencer.sort(key=lambda x: x['dias_restantes'])
        
        # Personal por empresa (si existe InfoLaboral)
        from rrhh_personal.models import InfoLaboral
        personal_por_empresa = InfoLaboral.objects.filter(
            personal_id__activo=True
        ).values(
            'empresa_id__nomFantasia'
        ).annotate(
            total=Count('personal_id')
        ).order_by('-total')[:5]
        
        # Cambios recientes (últimos 30 días)
        fecha_limite = datetime.now() - timedelta(days=30)
        cambios_recientes = HistorialPersonal.objects.filter(
            fecha_hora__gte=fecha_limite
        ).count()
        
        # Personal activado/desactivado en el último mes
        activaciones = HistorialPersonal.objects.filter(
            fecha_hora__gte=fecha_limite,
            accion__icontains='ACTIVADO'
        ).count()
        
        desactivaciones = HistorialPersonal.objects.filter(
            fecha_hora__gte=fecha_limite,
            accion__icontains='DESACTIVADO'
        ).count()
        
        # Tipos de ausentismo con conteo de personal activo
        tipos_ausentismo_detalle = []
        for tipo_ausentismo in TipoAusentismo.objects.all():
            count = Ausentismo.objects.filter(
                tipoausen_id=tipo_ausentismo,
                personal_id__activo=True,
                fechafin__gte=hoy
            ).values('personal_id').distinct().count()
            if count > 0:
                tipos_ausentismo_detalle.append({
                    'tipo': tipo_ausentismo.tipo,
                    'cantidad': count
                })
        
        # Tipos de licencia médica con conteo de personal activo
        tipos_licencia_detalle = []
        for tipo_licencia in TipoLicenciaMedica.objects.all():
            count = LicenciaMedicaPorPersonal.objects.filter(
                tipoLicenciaMedica_id=tipo_licencia,
                personal_id__activo=True,
                fecha_fin_licencia__gte=hoy
            ).values('personal_id').distinct().count()
            if count > 0:
                tipos_licencia_detalle.append({
                    'tipo': tipo_licencia.tipoLicenciaMedica,
                    'cantidad': count
                })
        
        # Faenas activas con su personal asignado
        faenas_con_personal = []
        faenas_activas = Faena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).order_by('nombre')
        
        for faena in faenas_activas:
            asignaciones_activas = AsignacionFaena.objects.filter(
                faena=faena,
                activo=True,
                personal__activo=True,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('personal', 'turno').prefetch_related(
                'personal__infolaboral_set__cargo_id',
                'personal__infolaboral_set__empresa_id'
            ).distinct()
            
            personal_lista = []
            for asig in asignaciones_activas:
                info_laboral = asig.personal.infolaboral_set.first() if hasattr(asig.personal, 'infolaboral_set') else None
                cargo = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
                
                personal_lista.append({
                    'nombre': f"{asig.personal.nombre} {asig.personal.apepat} {asig.personal.apemat}",
                    'rut': f"{asig.personal.rut}-{asig.personal.dvrut}",
                    'cargo': cargo,
                    'turno': asig.turno.nombre if asig.turno else 'Sin turno'
                })
            
            if personal_lista:
                faenas_con_personal.append({
                    'id': faena.id,
                    'nombre': faena.nombre,
                    'codigo': faena.codigo,
                    'fecha_inicio': faena.fecha_inicio.strftime('%d/%m/%Y') if faena.fecha_inicio else None,
                    'fecha_fin': faena.fecha_fin.strftime('%d/%m/%Y') if faena.fecha_fin else None,
                    'cantidad_personal': len(personal_lista),
                    'personal': personal_lista
                })
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_personal': total_personal,
                'total_personal_inactivo': total_personal_inactivo,
                'personal_disponible': personal_disponible_count,
                'personal_en_faena': personal_en_faena_count,
                'personal_con_licencia': personal_con_licencia_count,
                'personal_con_ausentismo': personal_con_ausentismo_count,
                'tipos_ausentismo': tipos_ausentismo_detalle,
                'tipos_licencia_medica': tipos_licencia_detalle,
                'faenas_con_personal': faenas_con_personal,
                'documentos_por_vencer': documentos_por_vencer[:20],  # Limitar a 20 más urgentes
                'total_documentos_por_vencer': len(documentos_por_vencer),
                'personal_por_empresa': list(personal_por_empresa),
                'cambios_recientes': cambios_recientes,
                'activaciones': activaciones,
                'desactivaciones': desactivaciones,
            }
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR API Dashboard RRHH]: {str(e)}")
        print(f"[TRACEBACK]: {error_traceback}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': error_traceback if request.user.is_superuser else None  # Solo mostrar traceback a superusuarios
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('dashboards.view_dashboard_operaciones', is_ajax=True)
@require_http_methods(["GET"])
def api_dashboard_operaciones(request):
    """
    API para obtener datos del dashboard de Operaciones/Planificaciones
    """
    try:
        hoy = date.today()
        fecha_limite_30_dias = hoy + timedelta(days=30)
        
        # ========== DATOS DE PERSONAL (igual que RRHH) ==========
        total_personal = Personal.objects.filter(activo=True).count()
        
        # Personal en faena (con asignaciones activas)
        personal_en_faena_ids = AsignacionFaena.objects.filter(
            activo=True,
            personal__activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).values_list('personal_id', flat=True).distinct()
        
        personal_en_faena_count = len(personal_en_faena_ids)
        
        # Personal con licencia médica activa
        personal_con_licencia_ids = LicenciaMedicaPorPersonal.objects.filter(
            personal_id__activo=True,
            fecha_fin_licencia__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_con_licencia_count = len(personal_con_licencia_ids)
        
        # Personal con ausentismo activo
        personal_con_ausentismo_ids = Ausentismo.objects.filter(
            personal_id__activo=True,
            fechafin__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_con_ausentismo_count = len(personal_con_ausentismo_ids)
        
        # Personal disponible: activo, no en faena, sin licencia, sin ausentismo
        personal_no_disponible_ids = set(personal_en_faena_ids) | set(personal_con_licencia_ids) | set(personal_con_ausentismo_ids)
        personal_disponible_count = total_personal - len(personal_no_disponible_ids)
        
        # ========== DATOS DE EQUIPOS ==========
        from maquinarias.models import (
            EstadoCalendarioEquipo, EstadoManualEquipo, EstadoFuenteEquipo, EstadoEquipo
        )
        from ope_calendario.models import AsignacionEquipoFaena
        
        equipos_activos = Equipo.objects.filter(activo=True).count()
        equipos_inactivos = Equipo.objects.filter(activo=False).count()
        
        # Obtener todos los equipos activos para calcular su estado actual
        equipos_todos = Equipo.objects.filter(activo=True)
        
        # Obtener estados manuales activos hoy
        estados_manuales_hoy = EstadoManualEquipo.objects.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).select_related('equipo', 'estado')
        
        # Obtener asignaciones a faenas activas hoy
        asignaciones_faena_hoy = AsignacionEquipoFaena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).select_related('equipo', 'faena')
        
        # Obtener estado "Asignado" para asignaciones a faenas
        estado_asignado_faena = EstadoCalendarioEquipo.objects.filter(
            activo=True, nombre__icontains='asignado'
        ).first()
        
        # Obtener OTs activas (no finalizadas ni canceladas)
        estado_finalizada = None
        estado_cancelada = None
        try:
            from maquinarias.models import EstadoOT
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
        except:
            pass
        
        # Primero obtener todas las OTs sin filtrar por estado_ot_id
        ots_todas = OrdenTrabajo.objects.filter(
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).select_related('equipo_id', 'estado_equipo_id', 'estado_ot_id')
        
        # Ahora filtrar por estados finalizados
        estados_finalizados = []
        if estado_finalizada:
            estados_finalizados.append(estado_finalizada)
        if estado_cancelada:
            estados_finalizados.append(estado_cancelada)
        
        if estados_finalizados:
            ots_activas_query = ots_todas.exclude(estado_ot_id__in=estados_finalizados)
        else:
            ots_activas_query = ots_todas
        
        # Obtener mapeos de EstadoFuenteEquipo
        mapeos_fuente = {}
        fuentes = EstadoFuenteEquipo.objects.select_related('estado_calendario', 'estado_equipo').all()
        for fuente in fuentes:
            if fuente.estado_calendario.activo:
                mapeos_fuente[fuente.estado_equipo.estadoEquipo_id] = fuente.estado_calendario
        
        # También crear un diccionario de fallback: nombre_estado_equipo -> estado_calendario
        # para búsqueda rápida cuando no hay mapeo directo
        estados_calendario_por_nombre = {}
        estados_calendario_activos = EstadoCalendarioEquipo.objects.filter(activo=True)
        for estado_cal in estados_calendario_activos:
            estados_calendario_por_nombre[estado_cal.nombre.lower()] = estado_cal
        
        # Obtener estado predeterminado (Disponible)
        estado_predeterminado = EstadoCalendarioEquipo.objects.filter(
            activo=True, es_predeterminado=True
        ).first()
        
        # Crear diccionarios para acceso rápido
        estados_manuales_por_equipo = {}
        for em in estados_manuales_hoy:
            if em.equipo.equipo_id not in estados_manuales_por_equipo:
                estados_manuales_por_equipo[em.equipo.equipo_id] = []
            estados_manuales_por_equipo[em.equipo.equipo_id].append(em)
        
        asignaciones_faena_por_equipo = {}
        for asig in asignaciones_faena_hoy:
            if asig.equipo.equipo_id not in asignaciones_faena_por_equipo:
                asignaciones_faena_por_equipo[asig.equipo.equipo_id] = []
            asignaciones_faena_por_equipo[asig.equipo.equipo_id].append(asig)
        
        ot_por_equipo = {}
        for ot in ots_activas_query:
            if ot.equipo_id.equipo_id not in ot_por_equipo:
                ot_por_equipo[ot.equipo_id.equipo_id] = []
            ot_por_equipo[ot.equipo_id.equipo_id].append(ot)
        
        # Calcular distribución de equipos por estado
        equipos_por_estado = {}
        equipos_disponibles_count = 0
        equipos_en_faena_count = 0
        
        for equipo in equipos_todos:
            equipo_id = equipo.equipo_id
            estado_actual = None
            
            # 1. Prioridad: Estados manuales (más alta prioridad)
            if equipo_id in estados_manuales_por_equipo:
                manuales = estados_manuales_por_equipo[equipo_id]
                bloqueantes = [em for em in manuales if em.estado.es_bloqueante]
                if bloqueantes:
                    estado_actual = bloqueantes[0].estado
                else:
                    # Ordenar por prioridad y tomar el primero
                    manuales_ordenados = sorted(manuales, key=lambda x: x.estado.prioridad, reverse=True)
                    estado_actual = manuales_ordenados[0].estado
            
            # 2. Si no hay estado manual, revisar OTs
            if not estado_actual and equipo_id in ot_por_equipo:
                ots_del_equipo = ot_por_equipo[equipo_id]
                estados_ot = []
                for ot in ots_del_equipo:
                    if ot.estado_equipo_id:
                        # Buscar mapeo usando estadoEquipo_id como clave
                        estado_calendario = mapeos_fuente.get(ot.estado_equipo_id.estadoEquipo_id)
                        
                        # Si no hay mapeo, buscar un EstadoCalendarioEquipo con el mismo nombre (fallback)
                        if not estado_calendario:
                            nombre_estado_lower = ot.estado_equipo_id.nombre.lower()
                            estado_calendario = estados_calendario_por_nombre.get(nombre_estado_lower)
                        
                        # Si aún no hay estado de calendario, crear uno temporal usando el nombre del estado de equipo
                        if not estado_calendario:
                            # Crear un objeto temporal que simule un EstadoCalendarioEquipo
                            # Usaremos el nombre del estado de equipo directamente
                            class EstadoCalendarioTemporal:
                                def __init__(self, nombre):
                                    self.nombre = nombre
                                    self.prioridad = 5  # Prioridad media
                                    self.es_bloqueante = False
                            
                            estado_calendario = EstadoCalendarioTemporal(ot.estado_equipo_id.nombre)
                        
                        if estado_calendario:
                            estados_ot.append(estado_calendario)
                
                if estados_ot:
                    # Ordenar por prioridad
                    estados_ot_ordenados = sorted(estados_ot, key=lambda x: x.prioridad, reverse=True)
                    bloqueantes_ot = [e for e in estados_ot_ordenados if e.es_bloqueante]
                    if bloqueantes_ot:
                        estado_actual = bloqueantes_ot[0]
                    else:
                        estado_actual = estados_ot_ordenados[0]
            
            # 3. Si no hay OT, revisar asignaciones a faenas
            if not estado_actual and equipo_id in asignaciones_faena_por_equipo and estado_asignado_faena:
                estado_actual = estado_asignado_faena
            
            # 4. Si no hay nada, usar estado predeterminado (Disponible)
            if not estado_actual and estado_predeterminado:
                estado_actual = estado_predeterminado
            
            # Contar por estado
            if estado_actual:
                estado_nombre = estado_actual.nombre
                estado_lower = estado_nombre.lower()
                
                # Contar en el diccionario general de estados
                if estado_nombre not in equipos_por_estado:
                    equipos_por_estado[estado_nombre] = 0
                equipos_por_estado[estado_nombre] += 1
                
                # Contar específicamente disponibles y en faena para las categorías principales
                if estado_lower in ['disponible', 'disponibles']:
                    equipos_disponibles_count += 1
                elif 'asignado' in estado_lower or 'faena' in estado_lower:
                    equipos_en_faena_count += 1
            else:
                # Sin estado definido, contar como disponible
                equipos_disponibles_count += 1
                estado_nombre = 'Disponible'
                if estado_nombre not in equipos_por_estado:
                    equipos_por_estado[estado_nombre] = 0
                equipos_por_estado[estado_nombre] += 1
        
        # Contar equipos en uso (con OTs activas que no tienen estado manual ni son estados especiales)
        equipos_en_uso_count = 0
        estados_especiales = set()  # Para rastrear estados especiales que no deben contarse como "En Uso"
        
        for equipo_id in ot_por_equipo.keys():
            # Solo contar como "En Uso" si no tiene estado manual
            if equipo_id not in estados_manuales_por_equipo:
                # Verificar si el estado de la OT es un estado especial
                ots_del_equipo = ot_por_equipo[equipo_id]
                tiene_estado_especial = False
                for ot in ots_del_equipo:
                    if ot.estado_equipo_id:
                        # Buscar mapeo usando estadoEquipo_id como clave
                        estado_calendario = mapeos_fuente.get(ot.estado_equipo_id.estadoEquipo_id)
                        
                        # Si no hay mapeo, buscar un EstadoCalendarioEquipo con el mismo nombre (fallback)
                        if not estado_calendario:
                            nombre_estado_lower = ot.estado_equipo_id.nombre.lower()
                            estado_calendario = estados_calendario_por_nombre.get(nombre_estado_lower)
                        
                        if estado_calendario:
                            estado_lower = estado_calendario.nombre.lower()
                            # Si es un estado especial (no disponible, no asignado), no contar como "En Uso"
                            if ('disponible' not in estado_lower and 
                                'asignado' not in estado_lower and 
                                'faena' not in estado_lower):
                                tiene_estado_especial = True
                                estados_especiales.add(estado_calendario.nombre)
                                break
                
                if not tiene_estado_especial:
                    equipos_en_uso_count += 1
        
        # Preparar datos de distribución para el gráfico
        distribucion_equipos = {
            'Disponibles': equipos_disponibles_count,
            'En Uso': equipos_en_uso_count,
            'En Faena': equipos_en_faena_count,
            'Inactivos': equipos_inactivos
        }
        
        # Agregar TODOS los estados encontrados (como Shutdown, Operativo con anomalías, etc.)
        # Excluyendo solo los que ya están en las categorías principales
        estados_ya_incluidos = {'Disponibles', 'En Uso', 'En Faena', 'Inactivos', 'Disponible'}
        
        # Preparar información detallada de equipos por estado para modales
        equipos_en_faena_detalle = []
        equipos_con_anomalias_detalle = []
        equipos_shutdown_detalle = []
        
        for estado_nombre, cantidad in equipos_por_estado.items():
            estado_lower = estado_nombre.lower()
            # Solo agregar estados que NO están en las categorías principales
            # y que tienen una cantidad mayor a 0
            es_disponible = 'disponible' in estado_lower
            es_asignado = 'asignado' in estado_lower
            es_faena = 'faena' in estado_lower
            es_en_uso = 'en uso' in estado_lower
            es_inactivo = 'inactivo' in estado_lower
            ya_incluido = estado_nombre in estados_ya_incluidos
            
            if (cantidad > 0 and 
                not ya_incluido and
                not es_disponible and 
                not es_asignado and 
                not es_faena and
                not es_en_uso and
                not es_inactivo):
                # Es un estado especial (Shutdown, Operativo con anomalías, En Mantenimiento, etc.)
                # Agregar directamente con su cantidad
                distribucion_equipos[estado_nombre] = cantidad
        
        # Obtener detalles de equipos en faena
        for asig in asignaciones_faena_hoy:
            codigo = asig.equipo.codigoInterno if hasattr(asig.equipo, 'codigoInterno') and asig.equipo.codigoInterno else 'N/A'
            equipos_en_faena_detalle.append({
                'equipo': asig.equipo.nombreEquipo,
                'codigo': codigo,
                'faena': asig.faena.nombre,
                'faena_codigo': asig.faena.codigo,
                'fecha_inicio': asig.fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': asig.fecha_fin.strftime('%d/%m/%Y') if asig.fecha_fin else 'Sin fecha fin'
            })
        
        # Obtener detalles de equipos con anomalías (Operativo con anomalías)
        # Buscar todos los estados de equipo que contengan "anomalía" o "anomalia"
        estados_anomalias = EstadoEquipo.objects.filter(
            Q(nombre__icontains='anomalía') | Q(nombre__icontains='anomalia')
        )
        
        if estados_anomalias.exists():
            # Obtener todas las OTs activas con estos estados
            ots_anomalias = ots_activas_query.filter(
                estado_equipo_id__in=estados_anomalias
            ).select_related('equipo_id')
            
            equipos_ya_agregados = set()
            for ot in ots_anomalias:
                if ot.equipo_id.equipo_id not in equipos_ya_agregados:
                    equipos_ya_agregados.add(ot.equipo_id.equipo_id)
                    codigo = ot.equipo_id.codigoInterno if hasattr(ot.equipo_id, 'codigoInterno') and ot.equipo_id.codigoInterno else 'N/A'
                    equipos_con_anomalias_detalle.append({
                        'equipo': ot.equipo_id.nombreEquipo,
                        'codigo': codigo,
                        'ot_folio': ot.folio,
                        'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'Sin fecha',
                        'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                        'observaciones': ot.observaciones or 'Sin observaciones'
                    })
        
        # Obtener detalles de equipos en shutdown
        # Puede venir de estados manuales O de OTs con estado shutdown
        estado_shutdown_calendario = EstadoCalendarioEquipo.objects.filter(
            nombre__icontains='shutdown',
            activo=True
        ).first()
        
        # 1. Buscar en estados manuales
        if estado_shutdown_calendario:
            estados_manuales_shutdown = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo')
            
            equipos_shutdown_ids = set()
            for em in estados_manuales_shutdown:
                if em.equipo.equipo_id not in equipos_shutdown_ids:
                    equipos_shutdown_ids.add(em.equipo.equipo_id)
                    codigo = em.equipo.codigoInterno if hasattr(em.equipo, 'codigoInterno') and em.equipo.codigoInterno else 'N/A'
                    equipos_shutdown_detalle.append({
                        'equipo': em.equipo.nombreEquipo,
                        'codigo': codigo,
                        'ot_folio': None,  # Estados manuales no tienen OT
                        'fecha_inicio': em.fecha_inicio.strftime('%d/%m/%Y'),
                        'fecha_fin': em.fecha_fin.strftime('%d/%m/%Y') if em.fecha_fin else 'Sin fecha fin',
                        'observaciones': em.observaciones or 'Sin observaciones'
                    })
        
        # 2. También buscar en OTs con estado shutdown (si existe EstadoEquipo shutdown)
        estados_shutdown_equipo = EstadoEquipo.objects.filter(
            Q(nombre__icontains='shutdown')
        )
        
        if estados_shutdown_equipo.exists():
            ots_shutdown = ots_activas_query.filter(
                estado_equipo_id__in=estados_shutdown_equipo
            ).select_related('equipo_id')
            
            for ot in ots_shutdown:
                # Solo agregar si no está ya en la lista de shutdown manual
                if ot.equipo_id.equipo_id not in equipos_shutdown_ids:
                    equipos_shutdown_ids.add(ot.equipo_id.equipo_id)
                    codigo = ot.equipo_id.codigoInterno if hasattr(ot.equipo_id, 'codigoInterno') and ot.equipo_id.codigoInterno else 'N/A'
                    equipos_shutdown_detalle.append({
                        'equipo': ot.equipo_id.nombreEquipo,
                        'codigo': codigo,
                        'ot_folio': ot.folio,
                        'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'Sin fecha',
                        'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                        'observaciones': ot.observaciones or 'Sin observaciones'
                    })
        
        # ========== DOCUMENTOS POR VENCER DE PERSONAL (30 días) ==========
        documentos_personal_por_vencer = []
        
        # Exámenes por vencer
        examenes_por_vencer = Examen.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoEx_id').order_by('fechaVencimiento')
        
        for examen in examenes_por_vencer:
            dias_restantes = (examen.fechaVencimiento - hoy).days
            documentos_personal_por_vencer.append({
                'tipo': 'Examen',
                'nombre': f"{examen.tipoEx_id}",
                'personal': f"{examen.personal_id.nombre} {examen.personal_id.apepat} {examen.personal_id.apemat}",
                'personal_rut': f"{examen.personal_id.rut}-{examen.personal_id.dvrut}",
                'fecha_vencimiento': examen.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Certificaciones por vencer
        certificaciones_por_vencer = Certificacion.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoCertificacion_id').order_by('fechaVencimiento')
        
        for cert in certificaciones_por_vencer:
            dias_restantes = (cert.fechaVencimiento - hoy).days
            documentos_personal_por_vencer.append({
                'tipo': 'Certificación',
                'nombre': f"{cert.tipoCertificacion_id}",
                'personal': f"{cert.personal_id.nombre} {cert.personal_id.apepat} {cert.personal_id.apemat}",
                'personal_rut': f"{cert.personal_id.rut}-{cert.personal_id.dvrut}",
                'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Licencias de conducir por vencer
        licencias_por_vencer = LicenciaPorPersonal.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id').order_by('fechaVencimiento')
        
        for lic in licencias_por_vencer:
            dias_restantes = (lic.fechaVencimiento - hoy).days
            tipos = ', '.join([t.tipoLicencia for t in lic.tipos.all()])
            documentos_personal_por_vencer.append({
                'tipo': 'Licencia de Conducir',
                'nombre': f"Licencia {tipos}",
                'personal': f"{lic.personal_id.nombre} {lic.personal_id.apepat} {lic.personal_id.apemat}",
                'personal_rut': f"{lic.personal_id.rut}-{lic.personal_id.dvrut}",
                'fecha_vencimiento': lic.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Licencias internas por vencer
        licencias_internas_por_vencer = LicenciaInternaPorPersonal.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_30_dias
        ).select_related('personal_id', 'tipoLicenciaInterna_id').order_by('fechaVencimiento')
        
        for lic_int in licencias_internas_por_vencer:
            dias_restantes = (lic_int.fechaVencimiento - hoy).days
            documentos_personal_por_vencer.append({
                'tipo': 'Licencia Interna',
                'nombre': f"{lic_int.tipoLicenciaInterna_id}",
                'personal': f"{lic_int.personal_id.nombre} {lic_int.personal_id.apepat} {lic_int.personal_id.apemat}",
                'personal_rut': f"{lic_int.personal_id.rut}-{lic_int.personal_id.dvrut}",
                'fecha_vencimiento': lic_int.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Carnets por vencer
        carnets_por_vencer = Personal.objects.filter(
            activo=True,
            fecha_vencimiento_carnet__gte=hoy,
            fecha_vencimiento_carnet__lte=fecha_limite_30_dias
        ).exclude(fecha_vencimiento_carnet__isnull=True)
        
        for personal in carnets_por_vencer:
            dias_restantes = (personal.fecha_vencimiento_carnet - hoy).days
            documentos_personal_por_vencer.append({
                'tipo': 'Carnet',
                'nombre': 'Carnet de Identidad',
                'personal': f"{personal.nombre} {personal.apepat} {personal.apemat}",
                'personal_rut': f"{personal.rut}-{personal.dvrut}",
                'fecha_vencimiento': personal.fecha_vencimiento_carnet.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Ordenar por días restantes
        documentos_personal_por_vencer.sort(key=lambda x: x['dias_restantes'])
        
        # ========== DOCUMENTOS POR VENCER DE MAQUINARIAS (30 días) ==========
        documentos_maquinarias_por_vencer = []
        
        documentos_maquinarias = DocumentoMaquinaria.objects.filter(
            equipo_id__activo=True,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite_30_dias
        ).select_related('equipo_id', 'tipo_documento_id').order_by('fecha_vencimiento')
        
        for doc in documentos_maquinarias:
            dias_restantes = (doc.fecha_vencimiento - hoy).days
            documentos_maquinarias_por_vencer.append({
                'tipo': doc.tipo_documento_id.nombre,
                'equipo': doc.equipo_id.nombreEquipo,
                'equipo_codigo': doc.equipo_id.codigoInterno if hasattr(doc.equipo_id, 'codigoInterno') and doc.equipo_id.codigoInterno else 'N/A',
                'fecha_vencimiento': doc.fecha_vencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Ordenar por días restantes
        documentos_maquinarias_por_vencer.sort(key=lambda x: x['dias_restantes'])
        
        # Tipos de ausentismo con conteo de personal activo (para modal)
        tipos_ausentismo_detalle = []
        for tipo_ausentismo in TipoAusentismo.objects.all():
            count = Ausentismo.objects.filter(
                tipoausen_id=tipo_ausentismo,
                personal_id__activo=True,
                fechafin__gte=hoy
            ).values('personal_id').distinct().count()
            if count > 0:
                tipos_ausentismo_detalle.append({
                    'tipo': tipo_ausentismo.tipo,
                    'cantidad': count
                })
        
        # Tipos de licencia médica con conteo de personal activo (para modal)
        tipos_licencia_detalle = []
        for tipo_licencia in TipoLicenciaMedica.objects.all():
            count = LicenciaMedicaPorPersonal.objects.filter(
                tipoLicenciaMedica_id=tipo_licencia,
                personal_id__activo=True,
                fecha_fin_licencia__gte=hoy
            ).values('personal_id').distinct().count()
            if count > 0:
                tipos_licencia_detalle.append({
                    'tipo': tipo_licencia.tipoLicenciaMedica,
                    'cantidad': count
                })
        
        # Faenas activas con su personal asignado (para modal)
        faenas_con_personal = []
        faenas_activas_list = Faena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).order_by('nombre')
        
        for faena in faenas_activas_list:
            asignaciones_activas = AsignacionFaena.objects.filter(
                faena=faena,
                activo=True,
                personal__activo=True,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('personal', 'turno').prefetch_related(
                'personal__infolaboral_set__cargo_id',
                'personal__infolaboral_set__empresa_id'
            ).distinct()
            
            personal_lista = []
            for asig in asignaciones_activas:
                info_laboral = asig.personal.infolaboral_set.first() if hasattr(asig.personal, 'infolaboral_set') else None
                cargo = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
                
                personal_lista.append({
                    'nombre': f"{asig.personal.nombre} {asig.personal.apepat} {asig.personal.apemat}",
                    'rut': f"{asig.personal.rut}-{asig.personal.dvrut}",
                    'cargo': cargo,
                    'turno': asig.turno.nombre if asig.turno else 'Sin turno'
                })
            
            if personal_lista:
                faenas_con_personal.append({
                    'id': faena.id,
                    'nombre': faena.nombre,
                    'codigo': faena.codigo,
                    'fecha_inicio': faena.fecha_inicio.strftime('%d/%m/%Y') if faena.fecha_inicio else None,
                    'fecha_fin': faena.fecha_fin.strftime('%d/%m/%Y') if faena.fecha_fin else None,
                    'cantidad_personal': len(personal_lista),
                    'personal': personal_lista
                })
        
        # Faenas activas
        faenas_activas = Faena.objects.filter(activo=True).count()
        
        # Faenas por estado (próximas, activas, finalizadas)
        faenas_proximas = Faena.objects.filter(
            activo=True,
            fecha_inicio__gt=hoy
        ).count()
        
        faenas_en_curso = Faena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).count()
        
        faenas_finalizadas = Faena.objects.filter(
            activo=True,
            fecha_fin__lt=hoy
        ).count()
        
        return JsonResponse({
            'success': True,
            'data': {
                # Datos de personal
                'personal_disponible': personal_disponible_count,
                'personal_en_faena': personal_en_faena_count,
                'personal_con_licencia': personal_con_licencia_count,
                'personal_con_ausentismo': personal_con_ausentismo_count,
                'tipos_ausentismo': tipos_ausentismo_detalle,
                'tipos_licencia_medica': tipos_licencia_detalle,
                'faenas_con_personal': faenas_con_personal,
                # Datos de equipos
                'equipos_activos': equipos_activos,
                'equipos_inactivos': equipos_inactivos,
                'equipos_en_uso': equipos_en_uso_count,
                'equipos_disponibles': equipos_disponibles_count,
                'equipos_en_faena': equipos_en_faena_count,
                'distribucion_equipos': distribucion_equipos,
                'equipos_por_estado': equipos_por_estado,
                # Detalles de equipos por estado (para modales)
                'equipos_en_faena_detalle': equipos_en_faena_detalle,
                'equipos_con_anomalias_detalle': equipos_con_anomalias_detalle,
                'equipos_shutdown_detalle': equipos_shutdown_detalle,
                # Datos de faenas
                'faenas_activas': faenas_activas,
                'faenas_proximas': faenas_proximas,
                'faenas_en_curso': faenas_en_curso,
                'faenas_finalizadas': faenas_finalizadas,
                # Documentos por vencer
                'documentos_personal_por_vencer': documentos_personal_por_vencer[:20],
                'total_documentos_personal_por_vencer': len(documentos_personal_por_vencer),
                'documentos_maquinarias_por_vencer': documentos_maquinarias_por_vencer[:20],
                'total_documentos_maquinarias_por_vencer': len(documentos_maquinarias_por_vencer),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('dashboards.view_dashboard_maquinarias', is_ajax=True)
@require_http_methods(["GET"])
def api_dashboard_maquinarias(request):
    """
    API para obtener datos del dashboard de Maquinarias
    """
    try:
        from maquinarias.models import EstadoOT, EstadoEquipo, EstadoCalendarioEquipo, EstadoFuenteEquipo, EstadoManualEquipo, DocumentoMaquinaria
        from ope_calendario.models import AsignacionEquipoFaena
        from datetime import date
        
        hoy = date.today()
        fecha_limite_30_dias = hoy + timedelta(days=30)
        
        # Equipos activos
        equipos_activos = Equipo.objects.filter(activo=True).count()
        equipos_inactivos = Equipo.objects.filter(activo=False).count()
        
        # Órdenes de trabajo por estado (excluyendo finalizadas)
        estados_ot = EstadoOT.objects.filter(activo=True)
        estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
        estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
        
        estados_finalizados_ids = []
        if estado_finalizada:
            estados_finalizados_ids.append(estado_finalizada.estadoOT_id)
        if estado_cancelada:
            estados_finalizados_ids.append(estado_cancelada.estadoOT_id)
        
        ots_por_estado = []
        for estado in estados_ot:
            if estado.estadoOT_id not in estados_finalizados_ids:
                total = OrdenTrabajo.objects.filter(
                    estado_ot_id=estado
                ).count()
                if total > 0:  # Solo incluir estados con OTs
                    ots_por_estado.append({
                        'estado': estado.nombre,
                        'total': total
                    })
        
        # Distribución de equipos (similar a operaciones)
        equipos_query = Equipo.objects.filter(activo=True)
        equipos_por_estado = {}
        
        for equipo in equipos_query:
            estado_actual = None
            
            # 1. Verificar estados manuales (prioridad más alta)
            estado_manual = EstadoManualEquipo.objects.filter(
                equipo=equipo,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).order_by('-fecha_inicio').first()
            
            if estado_manual:
                estado_actual = estado_manual.estado.nombre
            
            # 2. Si no hay estado manual, verificar OTs activas
            if not estado_actual:
                ots_activas = OrdenTrabajo.objects.filter(
                    equipo_id=equipo,
                    fecha_inicio__lte=hoy,
                    fecha_fin__gte=hoy
                ).exclude(
                    estado_ot_id__in=estados_finalizados_ids
                ).select_related('estado_equipo_id', 'estado_ot_id').order_by('-fecha_inicio').first()
                
                if ots_activas and ots_activas.estado_equipo_id:
                    estado_equipo = ots_activas.estado_equipo_id
                    estado_fuente = EstadoFuenteEquipo.objects.filter(
                        estado_equipo=estado_equipo
                    ).first()
                    
                    if estado_fuente and estado_fuente.estado_calendario:
                        estado_actual = estado_fuente.estado_calendario.nombre
                    else:
                        # Buscar por nombre
                        estado_calendario = EstadoCalendarioEquipo.objects.filter(
                            nombre__iexact=estado_equipo.nombre
                        ).first()
                        if estado_calendario:
                            estado_actual = estado_calendario.nombre
                        else:
                            estado_actual = estado_equipo.nombre
            
            # 3. Si no hay OT, verificar asignaciones a faenas
            if not estado_actual:
                asignacion_faena = AsignacionEquipoFaena.objects.filter(
                    equipo=equipo,
                    fecha_inicio__lte=hoy
                ).filter(
                    Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
                ).order_by('-fecha_inicio').first()
                
                if asignacion_faena:
                    estado_actual = "En Faena"
            
            # 4. Estado por defecto
            if not estado_actual:
                estado_actual = "Disponible"
            
            # Contar por estado
            if estado_actual in equipos_por_estado:
                equipos_por_estado[estado_actual] += 1
            else:
                equipos_por_estado[estado_actual] = 1
        
        # Construir distribución de equipos
        distribucion_equipos = {}
        equipos_disponibles_count = equipos_por_estado.get('Disponible', 0)
        equipos_en_faena_count = equipos_por_estado.get('En Faena', 0)
        equipos_inactivos_count = equipos_inactivos
        
        distribucion_equipos['Disponibles'] = equipos_disponibles_count
        distribucion_equipos['En Faena'] = equipos_en_faena_count
        distribucion_equipos['Inactivos'] = equipos_inactivos_count
        
        # Agregar otros estados especiales
        for estado_nombre, cantidad in equipos_por_estado.items():
            if estado_nombre not in ['Disponible', 'En Faena'] and cantidad > 0:
                distribucion_equipos[estado_nombre] = cantidad
        
        # Documentos de maquinarias por vencer (30 días)
        documentos_maquinarias_por_vencer = []
        documentos_maquinarias = DocumentoMaquinaria.objects.filter(
            equipo_id__activo=True,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite_30_dias
        ).select_related('equipo_id', 'tipo_documento_id').order_by('fecha_vencimiento')
        
        for doc in documentos_maquinarias:
            dias_restantes = (doc.fecha_vencimiento - hoy).days
            documentos_maquinarias_por_vencer.append({
                'tipo': doc.tipo_documento_id.nombre,
                'equipo': doc.equipo_id.nombreEquipo,
                'equipo_codigo': doc.equipo_id.codigoInterno if hasattr(doc.equipo_id, 'codigoInterno') and doc.equipo_id.codigoInterno else 'N/A',
                'fecha_vencimiento': doc.fecha_vencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        # Ordenar por días restantes
        documentos_maquinarias_por_vencer.sort(key=lambda x: x['dias_restantes'])
        
        # Preparar información detallada de equipos por estado para modales
        equipos_en_faena_detalle = []
        equipos_con_anomalias_detalle = []
        equipos_shutdown_detalle = []
        
        # Obtener detalles de equipos en faena
        asignaciones_faena_activas = AsignacionEquipoFaena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).select_related('equipo', 'faena')
        
        for asig in asignaciones_faena_activas:
            equipos_en_faena_detalle.append({
                'equipo': asig.equipo.nombreEquipo,
                'codigo': asig.equipo.codigoInterno if hasattr(asig.equipo, 'codigoInterno') and asig.equipo.codigoInterno else 'N/A',
                'faena': asig.faena.nombre,
                'faena_codigo': asig.faena.codigo,
                'fecha_inicio': asig.fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': asig.fecha_fin.strftime('%d/%m/%Y') if asig.fecha_fin else 'Sin fecha fin'
            })
        
        # Obtener detalles de equipos con anomalías (Operativo con anomalías)
        # Buscar todos los estados de equipo que contengan "anomalía" o "anomalia"
        estados_anomalias = EstadoEquipo.objects.filter(
            Q(nombre__icontains='anomalía') | Q(nombre__icontains='anomalia')
        )
        
        if estados_anomalias.exists():
            # Obtener todas las OTs activas con estos estados
            ots_anomalias = OrdenTrabajo.objects.filter(
                estado_equipo_id__in=estados_anomalias,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).select_related('equipo_id')
            
            equipos_ya_agregados = set()
            for ot in ots_anomalias:
                if ot.equipo_id.equipo_id not in equipos_ya_agregados:
                    equipos_ya_agregados.add(ot.equipo_id.equipo_id)
                    equipos_con_anomalias_detalle.append({
                        'equipo': ot.equipo_id.nombreEquipo,
                        'codigo': ot.equipo_id.codigoInterno if hasattr(ot.equipo_id, 'codigoInterno') and ot.equipo_id.codigoInterno else 'N/A',
                        'ot_folio': ot.folio,
                        'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'Sin fecha',
                        'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                        'observaciones': ot.observaciones or 'Sin observaciones'
                    })
        
        # Obtener detalles de equipos en shutdown
        # Puede venir de estados manuales O de OTs con estado shutdown
        estado_shutdown_calendario = EstadoCalendarioEquipo.objects.filter(
            nombre__icontains='shutdown',
            activo=True
        ).first()
        
        equipos_shutdown_ids = set()
        
        # 1. Buscar en estados manuales
        if estado_shutdown_calendario:
            estados_manuales_shutdown = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo')
            
            for em in estados_manuales_shutdown:
                if em.equipo.equipo_id not in equipos_shutdown_ids:
                    equipos_shutdown_ids.add(em.equipo.equipo_id)
                    equipos_shutdown_detalle.append({
                        'equipo': em.equipo.nombreEquipo,
                        'codigo': em.equipo.codigoInterno if hasattr(em.equipo, 'codigoInterno') and em.equipo.codigoInterno else 'N/A',
                        'ot_folio': None,  # Estados manuales no tienen OT
                        'fecha_inicio': em.fecha_inicio.strftime('%d/%m/%Y'),
                        'fecha_fin': em.fecha_fin.strftime('%d/%m/%Y') if em.fecha_fin else 'Sin fecha fin',
                        'observaciones': em.observaciones or 'Sin observaciones'
                    })
        
        # 2. También buscar en OTs con estado shutdown (si existe EstadoEquipo shutdown)
        estados_shutdown_equipo = EstadoEquipo.objects.filter(
            Q(nombre__icontains='shutdown')
        )
        
        if estados_shutdown_equipo.exists():
            ots_shutdown = OrdenTrabajo.objects.filter(
                estado_equipo_id__in=estados_shutdown_equipo,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).select_related('equipo_id')
            
            for ot in ots_shutdown:
                # Solo agregar si no está ya en la lista de shutdown manual
                if ot.equipo_id.equipo_id not in equipos_shutdown_ids:
                    equipos_shutdown_ids.add(ot.equipo_id.equipo_id)
                    equipos_shutdown_detalle.append({
                        'equipo': ot.equipo_id.nombreEquipo,
                        'codigo': ot.equipo_id.codigoInterno if hasattr(ot.equipo_id, 'codigoInterno') and ot.equipo_id.codigoInterno else 'N/A',
                        'ot_folio': ot.folio,
                        'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y') if ot.fecha_inicio else 'Sin fecha',
                        'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                        'observaciones': ot.observaciones or 'Sin observaciones'
                    })
        
        # Ranking de equipos más intervenidos (más OTs históricas)
        ranking_equipos_intervenidos = Equipo.objects.filter(
            activo=True
        ).annotate(
            total_ots=Count('ordenes_trabajo')
        ).filter(
            total_ots__gt=0
        ).order_by('-total_ots')[:20]
        
        ranking_equipos_lista = []
        for idx, equipo in enumerate(ranking_equipos_intervenidos, start=1):
            # Usar codigoInterno que es el campo real del modelo
            codigo = equipo.codigoInterno if hasattr(equipo, 'codigoInterno') and equipo.codigoInterno else 'N/A'
            ranking_equipos_lista.append({
                'posicion': idx,
                'equipo': equipo.nombreEquipo,
                'codigo': codigo,
                'total_ots': equipo.total_ots
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'equipos_activos': equipos_activos,
                'equipos_inactivos': equipos_inactivos,
                'ots_por_estado': ots_por_estado,
                'distribucion_equipos': distribucion_equipos,
                'equipos_por_estado': equipos_por_estado,
                # Detalles de equipos por estado (para modales)
                'equipos_en_faena_detalle': equipos_en_faena_detalle,
                'equipos_con_anomalias_detalle': equipos_con_anomalias_detalle,
                'equipos_shutdown_detalle': equipos_shutdown_detalle,
                'documentos_maquinarias_por_vencer': documentos_maquinarias_por_vencer,
                'total_documentos_maquinarias_por_vencer': len(documentos_maquinarias_por_vencer),
                'ranking_equipos_intervenidos': ranking_equipos_lista,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@permission_required_custom('dashboards.view_dashboard_gerencia', is_ajax=True)
@require_http_methods(["GET"])
def api_dashboard_gerencia(request):
    """
    API para obtener datos del dashboard de Gerencia (métricas estratégicas consolidadas)
    """
    try:
        from maquinarias.models import EstadoOT, EstadoEquipo, EstadoCalendarioEquipo, EstadoFuenteEquipo, EstadoManualEquipo, DocumentoMaquinaria, TipoMantenimiento
        from ope_calendario.models import AsignacionEquipoFaena, AsignacionFaena
        from rrhh_personal.models import Examen, Certificacion, LicenciaPorPersonal, LicenciaMedicaPorPersonal, Ausentismo
        
        hoy = date.today()
        fecha_limite_30_dias = hoy + timedelta(days=30)
        fecha_limite_7_dias = hoy + timedelta(days=7)
        fecha_limite_5_dias = hoy + timedelta(days=5)
        
        # ========== KPIs CONSOLIDADOS ==========
        total_personal = Personal.objects.filter(activo=True).count()
        total_equipos = Equipo.objects.filter(activo=True).count()
        
        # Personal en faena
        personal_en_faena_ids = AsignacionFaena.objects.filter(
            activo=True,
            personal__activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).values_list('personal_id', flat=True).distinct()
        personal_en_faena_count = len(personal_en_faena_ids)
        
        # Personal disponible
        personal_con_licencia_ids = LicenciaMedicaPorPersonal.objects.filter(
            personal_id__activo=True,
            fecha_fin_licencia__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_con_ausentismo_ids = Ausentismo.objects.filter(
            personal_id__activo=True,
            fechafin__gte=hoy
        ).values_list('personal_id', flat=True).distinct()
        
        personal_no_disponible_ids = set(personal_en_faena_ids) | set(personal_con_licencia_ids) | set(personal_con_ausentismo_ids)
        personal_disponible_count = total_personal - len(personal_no_disponible_ids)
        
        # Equipos disponibles
        equipos_en_faena = AsignacionEquipoFaena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).values_list('equipo_id', flat=True).distinct()
        
        # Equipos con estados especiales (shutdown, anomalías)
        equipos_shutdown_ids = set()
        equipos_anomalias_ids = set()
        
        estado_shutdown_calendario = EstadoCalendarioEquipo.objects.filter(
            nombre__icontains='shutdown',
            activo=True
        ).first()
        
        if estado_shutdown_calendario:
            equipos_shutdown_ids = set(EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).values_list('equipo_id', flat=True).distinct())
        
        estado_anomalias = EstadoEquipo.objects.filter(nombre__icontains='anomalía').first()
        if estado_anomalias:
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
            estados_finalizados_ids = []
            if estado_finalizada:
                estados_finalizados_ids.append(estado_finalizada.estadoOT_id)
            if estado_cancelada:
                estados_finalizados_ids.append(estado_cancelada.estadoOT_id)
            
            equipos_anomalias_ids = set(OrdenTrabajo.objects.filter(
                estado_equipo_id=estado_anomalias,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).values_list('equipo_id', flat=True).distinct())
        
        equipos_no_disponibles_ids = set(equipos_en_faena) | equipos_shutdown_ids | equipos_anomalias_ids
        equipos_disponibles_count = total_equipos - len(equipos_no_disponibles_ids)
        
        # Tasa de utilización general
        recursos_totales = total_personal + total_equipos
        recursos_ocupados = len(personal_no_disponible_ids) + len(equipos_no_disponibles_ids)
        tasa_utilizacion = (recursos_ocupados / recursos_totales * 100) if recursos_totales > 0 else 0
        
        # Faenas
        faenas_en_curso = Faena.objects.filter(
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).count()
        
        faenas_planificadas = Faena.objects.filter(
            activo=True,
            fecha_inicio__gt=hoy
        ).count()
        
        faenas_finalizadas = Faena.objects.filter(
            activo=True,
            fecha_fin__lt=hoy
        ).count()
        
        faenas_activas = faenas_en_curso + faenas_planificadas  # Total de faenas activas (no finalizadas)
        
        # ========== ANÁLISIS DE OTs ==========
        estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
        estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
        estados_finalizados_ids = []
        if estado_finalizada:
            estados_finalizados_ids.append(estado_finalizada.estadoOT_id)
        if estado_cancelada:
            estados_finalizados_ids.append(estado_cancelada.estadoOT_id)
        
        # OTs totales
        total_ots = OrdenTrabajo.objects.count()
        ots_finalizadas = OrdenTrabajo.objects.filter(estado_ot_id__in=estados_finalizados_ids).count() if estados_finalizados_ids else 0
        ots_activas = OrdenTrabajo.objects.exclude(estado_ot_id__in=estados_finalizados_ids).count() if estados_finalizados_ids else total_ots
        
        # Tasa de cumplimiento (últimos 30 días)
        fecha_30_dias_atras = hoy - timedelta(days=30)
        ots_creadas_30_dias = OrdenTrabajo.objects.filter(fecha_creacion__gte=fecha_30_dias_atras).count()
        ots_finalizadas_30_dias = OrdenTrabajo.objects.filter(
            fecha_creacion__gte=fecha_30_dias_atras,
            estado_ot_id__in=estados_finalizados_ids
        ).count() if estados_finalizados_ids else 0
        tasa_cumplimiento_ots = (ots_finalizadas_30_dias / ots_creadas_30_dias * 100) if ots_creadas_30_dias > 0 else 0
        
        # Tiempo promedio de OTs (solo finalizadas con fecha_fin)
        ots_con_tiempo = OrdenTrabajo.objects.filter(
            estado_ot_id__in=estados_finalizados_ids,
            fecha_inicio__isnull=False,
            fecha_fin__isnull=False
        ).exclude(fecha_fin__lt=F('fecha_inicio'))
        
        tiempo_promedio_dias = None
        if ots_con_tiempo.exists():
            tiempos = []
            for ot in ots_con_tiempo:
                if ot.fecha_inicio and ot.fecha_fin:
                    tiempo = (ot.fecha_fin - ot.fecha_inicio).days
                    if tiempo >= 0:
                        tiempos.append(tiempo)
            if tiempos:
                tiempo_promedio_dias = sum(tiempos) / len(tiempos)
        
        # Preventivo vs Correctivo (últimos 30 días)
        tipos_preventivos = TipoMantenimiento.objects.filter(
            nombre__icontains='preventivo'
        ).values_list('tipoMantenimiento_id', flat=True)
        
        tipos_correctivos = TipoMantenimiento.objects.filter(
            nombre__icontains='correctivo'
        ).values_list('tipoMantenimiento_id', flat=True)
        
        ots_preventivas_30_dias = OrdenTrabajo.objects.filter(
            tipo_mantenimiento_id__in=tipos_preventivos,
            fecha_creacion__gte=fecha_30_dias_atras
        ).count() if tipos_preventivos.exists() else 0
        
        ots_correctivas_30_dias = OrdenTrabajo.objects.filter(
            tipo_mantenimiento_id__in=tipos_correctivos,
            fecha_creacion__gte=fecha_30_dias_atras
        ).count() if tipos_correctivos.exists() else 0
        
        # ========== ALERTAS CRÍTICAS ==========
        alertas_criticas = []
        
        # Equipos en shutdown
        if estado_shutdown_calendario:
            equipos_shutdown = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo').count()
            if equipos_shutdown > 0:
                alertas_criticas.append({
                    'tipo': 'Equipos en Shutdown',
                    'cantidad': equipos_shutdown,
                    'severidad': 'alta',
                    'icono': 'exclamation-triangle'
                })
        
        # Equipos con anomalías
        if estado_anomalias:
            equipos_anomalias = OrdenTrabajo.objects.filter(
                estado_equipo_id=estado_anomalias,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).values_list('equipo_id', flat=True).distinct().count()
            if equipos_anomalias > 0:
                alertas_criticas.append({
                    'tipo': 'Equipos con Anomalías',
                    'cantidad': equipos_anomalias,
                    'severidad': 'media',
                    'icono': 'exclamation-circle'
                })
        
        # Documentos críticos por vencer (≤5 días) - obtener documentos completos
        documentos_criticos_personal_list = Examen.objects.filter(
            personal_id__activo=True,
            fechaVencimiento__gte=hoy,
            fechaVencimiento__lte=fecha_limite_5_dias
        ).select_related('personal_id', 'tipoEx_id').order_by('fechaVencimiento')[:10]  # Limitar a 10 para no sobrecargar
        
        documentos_criticos_equipos_list = DocumentoMaquinaria.objects.filter(
            equipo_id__activo=True,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite_5_dias
        ).select_related('equipo_id', 'tipo_documento_id').order_by('fecha_vencimiento')[:10]  # Limitar a 10 para no sobrecargar
        
        # Crear lista de documentos detallados
        documentos_detalle = []
        
        for examen in documentos_criticos_personal_list:
            dias_restantes = (examen.fechaVencimiento - hoy).days
            nombre_personal = f"{examen.personal_id.nombre} {examen.personal_id.apepat}"
            if examen.personal_id.apemat:
                nombre_personal += f" {examen.personal_id.apemat}"
            documentos_detalle.append({
                'tipo': 'Personal',
                'tipo_documento': examen.tipoEx_id.tipoExamen if examen.tipoEx_id else 'Examen',
                'nombre': nombre_personal,
                'fecha_vencimiento': examen.fechaVencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        for doc in documentos_criticos_equipos_list:
            dias_restantes = (doc.fecha_vencimiento - hoy).days
            documentos_detalle.append({
                'tipo': 'Equipo',
                'tipo_documento': doc.tipo_documento_id.nombre if hasattr(doc.tipo_documento_id, 'nombre') else 'Documento',
                'nombre': doc.equipo_id.nombreEquipo if hasattr(doc.equipo_id, 'nombreEquipo') else str(doc.equipo_id),
                'fecha_vencimiento': doc.fecha_vencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes
            })
        
        total_documentos_criticos = len(documentos_detalle)
        if total_documentos_criticos > 0:
            alertas_criticas.append({
                'tipo': 'Documentos por Vencer los Próximos 5 Días',
                'cantidad': total_documentos_criticos,
                'severidad': 'alta',
                'icono': 'calendar-x',
                'documentos': documentos_detalle
            })
        
        # ========== DETALLES PARA MODALES ==========
        # Detalles de personal en faena
        personal_en_faena_detalle = []
        asignaciones_faena = AsignacionFaena.objects.filter(
            activo=True,
            personal__activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
        ).select_related('personal', 'faena', 'turno')[:50]  # Limitar a 50 para no sobrecargar
        
        for asignacion in asignaciones_faena:
            nombre_personal = f"{asignacion.personal.nombre} {asignacion.personal.apepat}"
            if asignacion.personal.apemat:
                nombre_personal += f" {asignacion.personal.apemat}"
            personal_en_faena_detalle.append({
                'nombre': nombre_personal,
                'faena': asignacion.faena.nombre if asignacion.faena else 'N/A',
                'turno': asignacion.turno.nombre if asignacion.turno else 'N/A',
                'fecha_inicio': asignacion.fecha_inicio.strftime('%d/%m/%Y') if asignacion.fecha_inicio else 'N/A',
                'fecha_fin': asignacion.fecha_fin.strftime('%d/%m/%Y') if asignacion.fecha_fin else 'Indefinido'
            })
        
        # Detalles de personal no disponible (licencias/ausentismo)
        personal_no_disponible_detalle = []
        personal_con_licencia = LicenciaMedicaPorPersonal.objects.filter(
            personal_id__activo=True,
            fecha_fin_licencia__gte=hoy
        ).select_related('personal_id', 'tipoLicenciaMedica_id')[:30]
        
        for licencia in personal_con_licencia:
            nombre_personal = f"{licencia.personal_id.nombre} {licencia.personal_id.apepat}"
            if licencia.personal_id.apemat:
                nombre_personal += f" {licencia.personal_id.apemat}"
            personal_no_disponible_detalle.append({
                'nombre': nombre_personal,
                'tipo': 'Licencia Médica',
                'tipo_licencia': licencia.tipoLicenciaMedica_id.tipoLicenciaMedica if licencia.tipoLicenciaMedica_id else 'N/A',
                'fecha_fin': licencia.fecha_fin_licencia.strftime('%d/%m/%Y') if licencia.fecha_fin_licencia else 'N/A'
            })
        
        personal_con_ausentismo = Ausentismo.objects.filter(
            personal_id__activo=True,
            fechafin__gte=hoy
        ).select_related('personal_id', 'tipoausen_id')[:30]
        
        for ausentismo in personal_con_ausentismo:
            nombre_personal = f"{ausentismo.personal_id.nombre} {ausentismo.personal_id.apepat}"
            if ausentismo.personal_id.apemat:
                nombre_personal += f" {ausentismo.personal_id.apemat}"
            personal_no_disponible_detalle.append({
                'nombre': nombre_personal,
                'tipo': 'Ausentismo',
                'tipo_ausentismo': ausentismo.tipoausen_id.tipoAusentismo if ausentismo.tipoausen_id else 'N/A',
                'fecha_fin': ausentismo.fechafin.strftime('%d/%m/%Y') if ausentismo.fechafin else 'N/A'
            })
        
        # Detalles de equipos en uso
        equipos_en_uso_detalle = []
        equipos_en_faena_detalle = Equipo.objects.filter(
            equipo_id__in=list(equipos_en_faena)[:30]
        ).values('equipo_id', 'nombreEquipo', 'codigoInterno')
        
        for equipo in equipos_en_faena_detalle:
            # Obtener la faena asignada
            asignacion = AsignacionEquipoFaena.objects.filter(
                equipo_id=equipo['equipo_id'],
                activo=True,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('faena').first()
            
            equipos_en_uso_detalle.append({
                'nombre': equipo['nombreEquipo'],
                'codigo': equipo['codigoInterno'],
                'tipo': 'En Faena',
                'faena': asignacion.faena.nombre if asignacion and asignacion.faena else 'N/A'
            })
        
        # Detalles de equipos con shutdown
        equipos_shutdown_detalle = []
        if estado_shutdown_calendario:
            shutdown_equipos = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo')[:30]
            
            for estado_manual in shutdown_equipos:
                equipos_shutdown_detalle.append({
                    'nombre': estado_manual.equipo.nombreEquipo,
                    'codigo': estado_manual.equipo.codigoInterno,
                    'tipo': 'Shutdown',
                    'fecha_inicio': estado_manual.fecha_inicio.strftime('%d/%m/%Y') if estado_manual.fecha_inicio else 'N/A',
                    'fecha_fin': estado_manual.fecha_fin.strftime('%d/%m/%Y') if estado_manual.fecha_fin else 'Indefinido'
                })
        
        # Detalles de equipos con anomalías
        equipos_anomalias_detalle = []
        if estado_anomalias:
            anomalias_equipos = OrdenTrabajo.objects.filter(
                estado_equipo_id=estado_anomalias,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).select_related('equipo_id')[:30]
            
            for ot in anomalias_equipos:
                equipos_anomalias_detalle.append({
                    'nombre': ot.equipo_id.nombreEquipo,
                    'codigo': ot.equipo_id.codigoInterno,
                    'tipo': 'Anomalía',
                    'ot_folio': ot.folio if hasattr(ot, 'folio') else 'N/A'
                })
        
        # Detalles de OTs activas
        ots_activas_detalle = []
        ots_activas_list = OrdenTrabajo.objects.exclude(
            estado_ot_id__in=estados_finalizados_ids
        ).select_related('equipo_id', 'estado_ot_id')[:50]
        
        for ot in ots_activas_list:
            ots_activas_detalle.append({
                'folio': ot.folio if hasattr(ot, 'folio') else f'OT-{ot.ot_id}',
                'equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                'estado': ot.estado_ot_id.nombre if ot.estado_ot_id else 'N/A',
                'fecha_creacion': ot.fecha_creacion.strftime('%d/%m/%Y') if ot.fecha_creacion else 'N/A'
            })
        
        # Detalles de OTs finalizadas
        ots_finalizadas_detalle = []
        ots_finalizadas_list = OrdenTrabajo.objects.filter(
            estado_ot_id__in=estados_finalizados_ids
        ).select_related('equipo_id', 'estado_ot_id')[:50]
        
        for ot in ots_finalizadas_list:
            ots_finalizadas_detalle.append({
                'folio': ot.folio if hasattr(ot, 'folio') else f'OT-{ot.ot_id}',
                'equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                'estado': ot.estado_ot_id.nombre if ot.estado_ot_id else 'N/A',
                'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'N/A'
            })
        
        # Detalles de OTs preventivas y correctivas
        ots_preventivas_detalle = []
        ots_correctivas_detalle = []
        
        if tipos_preventivos.exists():
            ots_preventivas_list = OrdenTrabajo.objects.filter(
                tipo_mantenimiento_id__in=tipos_preventivos,
                fecha_creacion__gte=fecha_30_dias_atras
            ).select_related('equipo_id')[:30]
            
            for ot in ots_preventivas_list:
                ots_preventivas_detalle.append({
                    'folio': ot.folio if hasattr(ot, 'folio') else f'OT-{ot.ot_id}',
                    'equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                    'fecha_creacion': ot.fecha_creacion.strftime('%d/%m/%Y') if ot.fecha_creacion else 'N/A'
                })
        
        if tipos_correctivos.exists():
            ots_correctivas_list = OrdenTrabajo.objects.filter(
                tipo_mantenimiento_id__in=tipos_correctivos,
                fecha_creacion__gte=fecha_30_dias_atras
            ).select_related('equipo_id')[:30]
            
            for ot in ots_correctivas_list:
                ots_correctivas_detalle.append({
                    'folio': ot.folio if hasattr(ot, 'folio') else f'OT-{ot.ot_id}',
                    'equipo': ot.equipo_id.nombreEquipo if ot.equipo_id else 'N/A',
                    'fecha_creacion': ot.fecha_creacion.strftime('%d/%m/%Y') if ot.fecha_creacion else 'N/A'
                })
        
        # ========== RESUMEN EJECUTIVO ==========
        resumen_ejecutivo = {
            'total_personal_activo': total_personal,
            'personal_disponible': personal_disponible_count,
            'personal_en_faena': personal_en_faena_count,
            'total_equipos_activos': total_equipos,
            'equipos_disponibles': equipos_disponibles_count,
            'equipos_en_uso': len(equipos_no_disponibles_ids),
            'faenas_en_curso': faenas_en_curso,
            'faenas_planificadas': faenas_planificadas,
            'faenas_finalizadas': faenas_finalizadas,
            'ots_activas': ots_activas,
            'ots_finalizadas': ots_finalizadas,
            'alertas_criticas_pendientes': len(alertas_criticas)
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                # KPIs consolidados
                'tasa_utilizacion': round(tasa_utilizacion, 1),
                'tasa_cumplimiento_ots': round(tasa_cumplimiento_ots, 1),
                'tiempo_promedio_ots_dias': round(tiempo_promedio_dias, 1) if tiempo_promedio_dias else None,
                'total_alertas_criticas': len(alertas_criticas),
                
                # Análisis de OTs
                'ots_preventivas_30_dias': ots_preventivas_30_dias,
                'ots_correctivas_30_dias': ots_correctivas_30_dias,
                'ots_activas': ots_activas,
                'ots_finalizadas': ots_finalizadas,
                'total_ots': total_ots,
                
                # Faenas
                'faenas_en_curso': faenas_en_curso,
                'faenas_planificadas': faenas_planificadas,
                'faenas_finalizadas': faenas_finalizadas,
                
                # Alertas críticas
                'alertas_criticas': alertas_criticas,
                
                # Resumen ejecutivo
                'resumen_ejecutivo': resumen_ejecutivo,
                
                # Detalles para modales
                'detalles_personal_en_faena': personal_en_faena_detalle,
                'detalles_personal_no_disponible': personal_no_disponible_detalle,
                'detalles_equipos_en_uso': equipos_en_uso_detalle,
                'detalles_equipos_shutdown': equipos_shutdown_detalle,
                'detalles_equipos_anomalias': equipos_anomalias_detalle,
                'detalles_ots_activas': ots_activas_detalle,
                'detalles_ots_finalizadas': ots_finalizadas_detalle,
                'detalles_ots_preventivas': ots_preventivas_detalle,
                'detalles_ots_correctivas': ots_correctivas_detalle
            }
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e) + '\n' + traceback.format_exc()
        }, status=500)
