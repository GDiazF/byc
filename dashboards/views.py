from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta, date

# Importar modelos necesarios
from rrhh_personal.models import (
    Personal, HistorialPersonal, LicenciaMedicaPorPersonal, 
    Ausentismo, Examen, Certificacion, LicenciaPorPersonal,
    LicenciaInternaPorPersonal, TipoAusentismo, TipoLicenciaMedica
)
from maquinarias.models import Equipo, OrdenTrabajo, HistorialEquipo, DocumentoMaquinaria
from ope_calendario.models import Faena, AsignacionFaena


@login_required
def dashboards_view(request):
    """Vista principal de dashboards con tabs por área"""
    return render(request, 'dashboards/dashboards.html')


@csrf_exempt
@login_required
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
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
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
            equipos_en_faena_detalle.append({
                'equipo': asig.equipo.nombreEquipo,
                'codigo': asig.equipo.codigoEquipo if hasattr(asig.equipo, 'codigoEquipo') else 'N/A',
                'faena': asig.faena.nombre,
                'faena_codigo': asig.faena.codigo,
                'fecha_inicio': asig.fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': asig.fecha_fin.strftime('%d/%m/%Y') if asig.fecha_fin else 'Sin fecha fin'
            })
        
        # Obtener detalles de equipos con anomalías (Operativo con anomalías)
        estado_anomalias = EstadoEquipo.objects.filter(nombre__icontains='anomalía').first()
        if estado_anomalias:
            ots_anomalias = ots_activas_query.filter(estado_equipo_id=estado_anomalias).select_related('equipo_id')
            for ot in ots_anomalias:
                equipos_con_anomalias_detalle.append({
                    'equipo': ot.equipo_id.nombreEquipo,
                    'codigo': ot.equipo_id.codigoEquipo if hasattr(ot.equipo_id, 'codigoEquipo') else 'N/A',
                    'ot_folio': ot.folio,
                    'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                    'observaciones': ot.observaciones or 'Sin observaciones'
                })
        
        # Obtener detalles de equipos en shutdown (estado manual)
        # EstadoManualEquipo.estado es un ForeignKey a EstadoCalendarioEquipo, no a EstadoEquipo
        estado_shutdown_calendario = EstadoCalendarioEquipo.objects.filter(
            nombre__icontains='shutdown',
            activo=True
        ).first()
        
        if estado_shutdown_calendario:
            estados_manuales_shutdown = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo')
            for em in estados_manuales_shutdown:
                equipos_shutdown_detalle.append({
                    'equipo': em.equipo.nombreEquipo,
                    'codigo': em.equipo.codigoEquipo if hasattr(em.equipo, 'codigoEquipo') else 'N/A',
                    'fecha_inicio': em.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin': em.fecha_fin.strftime('%d/%m/%Y') if em.fecha_fin else 'Sin fecha fin',
                    'observaciones': em.observaciones or 'Sin observaciones'
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
                'equipo_codigo': doc.equipo_id.codigoEquipo if hasattr(doc.equipo_id, 'codigoEquipo') else 'N/A',
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
                'equipo_codigo': doc.equipo_id.codigoEquipo if hasattr(doc.equipo_id, 'codigoEquipo') else 'N/A',
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
                'codigo': asig.equipo.codigoEquipo if hasattr(asig.equipo, 'codigoEquipo') else 'N/A',
                'faena': asig.faena.nombre,
                'faena_codigo': asig.faena.codigo,
                'fecha_inicio': asig.fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': asig.fecha_fin.strftime('%d/%m/%Y') if asig.fecha_fin else 'Sin fecha fin'
            })
        
        # Obtener detalles de equipos con anomalías (Operativo con anomalías)
        estado_anomalias = EstadoEquipo.objects.filter(nombre__icontains='anomalía').first()
        if estado_anomalias:
            ots_anomalias = OrdenTrabajo.objects.filter(
                estado_equipo_id=estado_anomalias,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).exclude(
                estado_ot_id__in=estados_finalizados_ids
            ).select_related('equipo_id')
            
            for ot in ots_anomalias:
                equipos_con_anomalias_detalle.append({
                    'equipo': ot.equipo_id.nombreEquipo,
                    'codigo': ot.equipo_id.codigoEquipo if hasattr(ot.equipo_id, 'codigoEquipo') else 'N/A',
                    'ot_folio': ot.folio,
                    'fecha_inicio': ot.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin': ot.fecha_fin.strftime('%d/%m/%Y') if ot.fecha_fin else 'Sin fecha fin',
                    'observaciones': ot.observaciones or 'Sin observaciones'
                })
        
        # Obtener detalles de equipos en shutdown (estado manual)
        # EstadoManualEquipo.estado es un ForeignKey a EstadoCalendarioEquipo, no a EstadoEquipo
        estado_shutdown_calendario = EstadoCalendarioEquipo.objects.filter(
            nombre__icontains='shutdown',
            activo=True
        ).first()
        
        if estado_shutdown_calendario:
            estados_manuales_shutdown = EstadoManualEquipo.objects.filter(
                estado=estado_shutdown_calendario,
                fecha_inicio__lte=hoy
            ).filter(
                Q(fecha_fin__gte=hoy) | Q(fecha_fin__isnull=True)
            ).select_related('equipo')
            
            for em in estados_manuales_shutdown:
                equipos_shutdown_detalle.append({
                    'equipo': em.equipo.nombreEquipo,
                    'codigo': em.equipo.codigoEquipo if hasattr(em.equipo, 'codigoEquipo') else 'N/A',
                    'fecha_inicio': em.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin': em.fecha_fin.strftime('%d/%m/%Y') if em.fecha_fin else 'Sin fecha fin',
                    'observaciones': em.observaciones or 'Sin observaciones'
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
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_dashboard_gerencia(request):
    """
    API para obtener datos del dashboard de Gerencia (vista consolidada)
    """
    try:
        # Resumen general
        total_personal = Personal.objects.filter(activo=True).count()
        total_equipos = Equipo.objects.filter(activo=True).count()
        total_faenas_activas = Faena.objects.filter(activo=True).count()
        total_ots = OrdenTrabajo.objects.count()
        
        # Actividad reciente (últimos 7 días)
        fecha_limite = datetime.now() - timedelta(days=7)
        
        cambios_personal = HistorialPersonal.objects.filter(
            fecha_hora__gte=fecha_limite
        ).count()
        
        cambios_equipos = HistorialEquipo.objects.filter(
            fecha_hora__gte=fecha_limite
        ).count()
        
        from ope_calendario.models import HistorialFaena
        cambios_faenas = HistorialFaena.objects.filter(
            fecha_hora__gte=fecha_limite
        ).count()
        
        return JsonResponse({
            'success': True,
            'data': {
                'resumen': {
                    'total_personal': total_personal,
                    'total_equipos': total_equipos,
                    'total_faenas_activas': total_faenas_activas,
                    'total_ots': total_ots,
                },
                'actividad_reciente': {
                    'cambios_personal': cambios_personal,
                    'cambios_equipos': cambios_equipos,
                    'cambios_faenas': cambios_faenas,
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
