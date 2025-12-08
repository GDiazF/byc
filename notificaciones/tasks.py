"""
Tareas para procesar vencimientos y crear notificaciones.
"""

from django.utils import timezone
from datetime import timedelta
from .utils import crear_notificacion_por_tipo
from rrhh_personal.models import (
    Personal, LicenciaPorPersonal, LicenciaMedicaPorPersonal,
    LicenciaInternaPorPersonal, Certificacion, Examen
)
from maquinarias.models import DocumentoMaquinaria
import logging

logger = logging.getLogger(__name__)


def procesar_vencimientos_documentos(forzar_creacion=False):
    """
    Procesa todos los documentos próximos a vencer y crea notificaciones.
    Revisa documentos de personal y equipos.
    
    Procesa documentos con vencimientos <= 45 días:
    - 45, 30, 20, 15, 10 días: Notificación única cuando quedan exactamente esos días
    - 9-1 días: Notificación diaria (crítica)
    - Otros días entre 1-45: Se procesan pero se agrupan por el umbral más cercano
    
    Args:
        forzar_creacion: Si es True, crea notificaciones aunque ya existan hoy (útil para pruebas)
    """
    hoy = timezone.now().date()
    umbrales_unicos = [45, 30, 20, 15, 10]  # Días exactos para notificación única
    
    logger.info(f"Iniciando procesamiento de vencimientos para fecha: {hoy} (forzar_creacion={forzar_creacion})")
    
    try:
    # Procesar documentos de personal
        logger.info("Procesando vencimientos de personal...")
        procesar_vencimientos_personal(hoy, umbrales_unicos, forzar_creacion=forzar_creacion)
        logger.info("Procesamiento de personal completado")
    except Exception as e:
        logger.error(f"Error al procesar vencimientos de personal: {str(e)}", exc_info=True)
    
    try:
    # Procesar documentos de equipos
        logger.info("Procesando vencimientos de equipos...")
        procesar_vencimientos_equipos(hoy, umbrales_unicos, forzar_creacion=forzar_creacion)
        logger.info("Procesamiento de equipos completado")
    except Exception as e:
        logger.error(f"Error al procesar vencimientos de equipos: {str(e)}", exc_info=True)
    
    # Resumen final
    from .models import Notificacion
    notificaciones_creadas_hoy = Notificacion.objects.filter(fecha_creacion__date=hoy).count()
    logger.info(f"Procesamiento de vencimientos finalizado. Total de notificaciones creadas hoy: {notificaciones_creadas_hoy}")


def procesar_vencimientos_personal(hoy, umbrales_unicos, forzar_creacion=False):
    """
    Procesa vencimientos de documentos de personal.
    Solo considera personal activo.
    Agrupa documentos por persona y crea una notificación consolidada por persona.
    
    Args:
        forzar_creacion: Si es True, crea notificaciones aunque ya existan hoy
    """
    from collections import defaultdict
    
    # Diccionario para agrupar documentos por personal
    # Estructura: {personal_id: {'personal': objeto, 'documentos': [lista de documentos]}}
    documentos_por_personal = defaultdict(lambda: {'personal': None, 'documentos': []})
    
    # 1. Licencias de conducir
    licencias_conducir = LicenciaPorPersonal.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id').prefetch_related('tipos')
    
    logger.info(f"Revisando {licencias_conducir.count()} licencias de conducir")
    for licencia in licencias_conducir:
        if licencia.fechaVencimiento:
            dias_restantes = (licencia.fechaVencimiento - hoy).days
            tipos_str = ", ".join([t.tipoLicencia for t in licencia.tipos.all()])
            
            # Procesar si tiene <= 45 días (incluye umbrales exactos y críticos)
            if dias_restantes <= 45 and dias_restantes >= 0:
                personal_id = licencia.personal_id.personal_id
                documentos_por_personal[personal_id]['personal'] = licencia.personal_id
                documentos_por_personal[personal_id]['documentos'].append({
                    'tipo': 'LICENCIA_CONDUCIR',
                    'nombre': f'Licencia de Conducir ({tipos_str})',
                    'fecha_vencimiento': licencia.fechaVencimiento,
                    'dias_restantes': dias_restantes,
                    'es_critico': 1 <= dias_restantes <= 9
                })
                logger.debug(f"Documento agregado: Licencia de Conducir para personal {personal_id}, {dias_restantes} días restantes")
    
    # 2. Licencias internas
    licencias_internas = LicenciaInternaPorPersonal.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoLicenciaInterna_id')
    
    for licencia in licencias_internas:
        if licencia.fechaVencimiento:
            dias_restantes = (licencia.fechaVencimiento - hoy).days
            tipo_nombre = licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else 'N/A'
            
            # Procesar si tiene <= 45 días
            if dias_restantes <= 45 and dias_restantes >= 0:
                personal_id = licencia.personal_id.personal_id
                documentos_por_personal[personal_id]['personal'] = licencia.personal_id
                documentos_por_personal[personal_id]['documentos'].append({
                    'tipo': 'LICENCIA_INTERNA',
                    'nombre': f'Licencia Interna: {tipo_nombre}',
                    'fecha_vencimiento': licencia.fechaVencimiento,
                    'dias_restantes': dias_restantes,
                    'es_critico': 1 <= dias_restantes <= 9
                })
    
    # NOTA: Las licencias médicas NO generan notificaciones de vencimiento
    # porque es normal que venzan. Solo se notifica su creación (ver signals.py)
    
    # 3. Certificaciones
    certificaciones = Certificacion.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoCertificacion_id')
    
    for cert in certificaciones:
        if cert.fechaVencimiento:
            dias_restantes = (cert.fechaVencimiento - hoy).days
            tipo_nombre = cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else 'N/A'
            
            # Procesar si tiene <= 45 días
            if dias_restantes <= 45 and dias_restantes >= 0:
                personal_id = cert.personal_id.personal_id
                documentos_por_personal[personal_id]['personal'] = cert.personal_id
                documentos_por_personal[personal_id]['documentos'].append({
                    'tipo': 'CERTIFICACION',
                    'nombre': f'Certificación: {tipo_nombre}',
                    'fecha_vencimiento': cert.fechaVencimiento,
                    'dias_restantes': dias_restantes,
                    'es_critico': 1 <= dias_restantes <= 9
                })
    
    # 4. Exámenes
    examenes = Examen.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoEx_id')
    
    for examen in examenes:
        if examen.fechaVencimiento:
            dias_restantes = (examen.fechaVencimiento - hoy).days
            tipo_nombre = examen.tipoEx_id.tipoExamen if examen.tipoEx_id else 'N/A'
            
            # Procesar si tiene <= 45 días
            if dias_restantes <= 45 and dias_restantes >= 0:
                personal_id = examen.personal_id.personal_id
                documentos_por_personal[personal_id]['personal'] = examen.personal_id
                documentos_por_personal[personal_id]['documentos'].append({
                    'tipo': 'EXAMEN',
                    'nombre': f'Examen: {tipo_nombre}',
                    'fecha_vencimiento': examen.fechaVencimiento,
                    'dias_restantes': dias_restantes,
                    'es_critico': 1 <= dias_restantes <= 9
                })
    
    # 5. Carnet (del modelo Personal)
    personal_con_carnet = Personal.objects.filter(
        activo=True,
        fecha_vencimiento_carnet__isnull=False
    )
    
    for personal in personal_con_carnet:
        dias_restantes = (personal.fecha_vencimiento_carnet - hoy).days
        
        # Procesar si tiene <= 45 días
        if dias_restantes <= 45 and dias_restantes >= 0:
            personal_id = personal.personal_id
            documentos_por_personal[personal_id]['personal'] = personal
            documentos_por_personal[personal_id]['documentos'].append({
                'tipo': 'CARNET',
                'nombre': 'Carnet',
                'fecha_vencimiento': personal.fecha_vencimiento_carnet,
                'dias_restantes': dias_restantes,
                'es_critico': 1 <= dias_restantes <= 9
            })
    
    # 6. Crear notificaciones consolidadas por persona
    logger.info(f"Total de personas con documentos por vencer: {len(documentos_por_personal)}")
    if len(documentos_por_personal) == 0:
        logger.warning("No se encontraron personas con documentos por vencer en los umbrales configurados")
        return
    
    contador_procesados = 0
    contador_exitosos = 0
    contador_errores = 0
    
    for personal_id, datos in documentos_por_personal.items():
        personal = datos['personal']
        documentos = datos['documentos']
        
        if personal and documentos:
            contador_procesados += 1
            try:
                logger.info(f"[{contador_procesados}/{len(documentos_por_personal)}] Procesando personal {personal.nombre} {personal.apepat} (ID: {personal_id}) con {len(documentos)} documentos por vencer")
                crear_notificacion_vencimiento_consolidada_personal(personal, documentos, hoy, forzar_creacion=forzar_creacion)
                contador_exitosos += 1
                logger.info(f"✓ Personal {personal_id} procesado exitosamente")
            except Exception as e:
                contador_errores += 1
                logger.error(f"✗ Error al crear notificación para personal {personal_id}: {str(e)}", exc_info=True)
                # Continuar con el siguiente personal aunque haya un error
                continue
    
    logger.info(f"Resumen procesamiento personal: {contador_procesados} procesados, {contador_exitosos} exitosos, {contador_errores} errores")


def procesar_vencimientos_equipos(hoy, umbrales_unicos, forzar_creacion=False):
    """
    Procesa vencimientos de documentos de equipos.
    Solo considera equipos activos.
    Agrupa documentos por equipo y crea una notificación consolidada por equipo.
    
    Args:
        forzar_creacion: Si es True, crea notificaciones aunque ya existan hoy
    """
    from collections import defaultdict
    
    # Diccionario para agrupar documentos por equipo
    # Estructura: {equipo_id: {'equipo': objeto, 'documentos': [lista de documentos]}}
    documentos_por_equipo = defaultdict(lambda: {'equipo': None, 'documentos': []})
    
    documentos = DocumentoMaquinaria.objects.filter(
        equipo_id__activo=True,
        fecha_vencimiento__isnull=False
    ).select_related('equipo_id', 'tipo_documento_id')
    
    for documento in documentos:
        if documento.fecha_vencimiento:
            dias_restantes = (documento.fecha_vencimiento - hoy).days
            tipo_nombre = documento.tipo_documento_id.nombre if documento.tipo_documento_id else 'Documento'
            
            # Procesar si tiene <= 45 días (incluye umbrales exactos y críticos)
            if dias_restantes <= 45 and dias_restantes >= 0:
                equipo_id = documento.equipo_id.equipo_id
                documentos_por_equipo[equipo_id]['equipo'] = documento.equipo_id
                documentos_por_equipo[equipo_id]['documentos'].append({
                    'nombre': tipo_nombre,
                    'fecha_vencimiento': documento.fecha_vencimiento,
                    'dias_restantes': dias_restantes,
                    'es_critico': 1 <= dias_restantes <= 9
                })
    
    # Crear notificaciones consolidadas por equipo
    logger.info(f"Total de equipos con documentos por vencer: {len(documentos_por_equipo)}")
    if len(documentos_por_equipo) == 0:
        logger.warning("No se encontraron equipos con documentos por vencer en los umbrales configurados")
        return
    
    contador_procesados = 0
    contador_exitosos = 0
    contador_errores = 0
    
    for equipo_id, datos in documentos_por_equipo.items():
        equipo = datos['equipo']
        documentos = datos['documentos']
        
        if equipo and documentos:
            contador_procesados += 1
            try:
                logger.info(f"[{contador_procesados}/{len(documentos_por_equipo)}] Procesando equipo {equipo.nombreEquipo} (ID: {equipo_id}) con {len(documentos)} documentos por vencer")
                crear_notificacion_vencimiento_consolidada_equipo(equipo, documentos, hoy, forzar_creacion=forzar_creacion)
                contador_exitosos += 1
                logger.info(f"✓ Equipo {equipo_id} procesado exitosamente")
            except Exception as e:
                contador_errores += 1
                logger.error(f"✗ Error al crear notificación para equipo {equipo_id}: {str(e)}", exc_info=True)
                # Continuar con el siguiente equipo aunque haya un error
                continue
    
    logger.info(f"Resumen procesamiento equipos: {contador_procesados} procesados, {contador_exitosos} exitosos, {contador_errores} errores")


def crear_notificacion_vencimiento_consolidada_personal(personal, documentos, hoy, forzar_creacion=False):
    """
    Crea una notificación consolidada para un personal con todos sus documentos por vencer.
    
    Args:
        personal: Objeto Personal
        documentos: Lista de diccionarios con información de documentos por vencer
        hoy: Fecha actual
        forzar_creacion: Si es True, crea la notificación aunque ya exista una hoy
    """
    if not personal.activo:
        logger.info(f"Personal {personal.personal_id} no está activo, omitiendo")
        return
    
    # Separar documentos críticos y no críticos
    documentos_criticos = [d for d in documentos if d['es_critico']]
    documentos_normales = [d for d in documentos if not d['es_critico']]
    
    # Determinar si es crítica (tiene al menos un documento crítico)
    es_critica = len(documentos_criticos) > 0
    
    # Ordenar documentos por días restantes (más críticos primero)
    todos_documentos = sorted(documentos, key=lambda x: x['dias_restantes'])
    
    # Construir mensaje consolidado
    if es_critica:
        codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_CRITICO'
        titulo = f"⚠️ Vencimientos críticos: {personal.nombre} {personal.apepat}"
        prefijo_mensaje = "⚠️ Los siguientes documentos de "
    else:
        # Usar el código según el menor número de días restantes
        # Mapear a los tipos disponibles: 45D, 30D, 20D, 15D, 10D
        dias_minimos = min(d['dias_restantes'] for d in documentos)
        if dias_minimos >= 45:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_45D'
        elif dias_minimos >= 30:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_30D'
        elif dias_minimos >= 20:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_20D'
        elif dias_minimos >= 15:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_15D'
        else:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_10D'
        titulo = f"Vencimientos próximos: {personal.nombre} {personal.apepat}"
        prefijo_mensaje = "Los siguientes documentos de "
    
    mensaje = (
        f"{prefijo_mensaje}{personal.nombre} {personal.apepat} "
        f"(RUT: {personal.rut}-{personal.dvrut}) están próximos a vencer:\n\n"
    )
    
    # Agregar lista de documentos
    for i, doc in enumerate(todos_documentos, 1):
        estado = "⚠️ CRÍTICO" if doc['es_critico'] else ""
        mensaje += (
            f"{i}. {doc['nombre']} - "
            f"{doc['dias_restantes']} día(s) restantes "
            f"(Vence: {doc['fecha_vencimiento'].strftime('%d/%m/%Y')}) {estado}\n"
        )
    
    # Preparar datos adicionales con todos los documentos
    datos_adicionales = {
        'personal_id': personal.personal_id,
        'total_documentos': len(documentos),
        'documentos_criticos': len(documentos_criticos),
        'documentos': [
            {
                'tipo': doc.get('tipo', ''),
                'nombre': doc['nombre'],
                'fecha_vencimiento': doc['fecha_vencimiento'].isoformat(),
                'dias_restantes': doc['dias_restantes'],
                'es_critico': doc['es_critico']
            }
            for doc in todos_documentos
        ]
    }
    
    # Verificar si ya existe una notificación para este personal HOY
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
        logger.info(f"Tipo de notificación {codigo_tipo} encontrado")
        
        # Verificar existencia usando una búsqueda más simple
        # Buscar notificaciones del mismo tipo y personal creadas hoy
        existe = False
        try:
            notificaciones_hoy = Notificacion.objects.filter(
                tipo_notificacion=tipo_notif,
                fecha_creacion__date=hoy
            )
            logger.info(f"Buscando notificaciones existentes para personal {personal.personal_id}: {notificaciones_hoy.count()} notificaciones del tipo {codigo_tipo} hoy")
            
            # Verificar manualmente en los datos adicionales porque JSONField puede tener problemas con lookups
            for notif in notificaciones_hoy:
                notif_personal_id = notif.datos_adicionales.get('personal_id')
                if notif_personal_id == personal.personal_id:
                    existe = True
                    logger.info(f"Encontrada notificación existente ID {notif.id} para personal {personal.personal_id}")
                    break
        except Exception as e:
            logger.warning(f"Error al verificar notificaciones existentes para personal {personal.personal_id}: {str(e)}")
            # Continuar de todas formas, asumir que no existe
        
        if existe and not forzar_creacion:
            logger.info(f"Ya existe notificación para personal {personal.personal_id} ({personal.nombre} {personal.apepat}) con código {codigo_tipo} hoy - omitiendo")
            return
        elif existe and forzar_creacion:
            logger.info(f"Ya existe notificación para personal {personal.personal_id} pero forzar_creacion=True, creando nueva")
        
        logger.info(f"Creando notificación para personal {personal.personal_id} ({personal.nombre} {personal.apepat}) con código {codigo_tipo}")
        logger.info(f"Mensaje: {titulo}")
        logger.info(f"Documentos a incluir: {len(documentos)}")
        
        try:
            notificaciones_creadas = crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje.strip(),
                datos_adicionales=datos_adicionales
            )
            
            if notificaciones_creadas:
                logger.info(f"✓ Se crearon {len(notificaciones_creadas)} notificaciones para personal {personal.personal_id}")
                for notif in notificaciones_creadas:
                    logger.info(f"  - Notificación ID {notif.id} para usuario {notif.usuario.username}")
            else:
                logger.warning(f"⚠ No se crearon notificaciones para personal {personal.personal_id} - posiblemente no hay usuarios con roles configurados para {codigo_tipo}")
        except Exception as e:
            logger.error(f"✗ Error al llamar crear_notificacion_por_tipo para personal {personal.personal_id}: {str(e)}", exc_info=True)
            raise  # Re-lanzar para que el try-except externo lo capture
            
    except TipoNotificacion.DoesNotExist:
        # Si no existe el tipo específico, usar el crítico como fallback
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe, usando crítico como fallback")
        try:
            codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_CRITICO'
            tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
            
            # Verificar existencia manualmente
            existe = False
            notificaciones_hoy = Notificacion.objects.filter(
                tipo_notificacion=tipo_notif,
                fecha_creacion__date=hoy
            )
            
            for notif in notificaciones_hoy:
                if notif.datos_adicionales.get('personal_id') == personal.personal_id:
                    existe = True
                    break
            
            if existe:
                logger.info(f"Ya existe notificación crítica para personal {personal.personal_id} hoy - omitiendo")
                return
            
            logger.info(f"Creando notificación crítica para personal {personal.personal_id}")
            notificaciones_creadas = crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje.strip(),
                datos_adicionales=datos_adicionales
            )
            if notificaciones_creadas:
                logger.info(f"✓ Se crearon {len(notificaciones_creadas)} notificaciones críticas para personal {personal.personal_id}")
            else:
                logger.warning(f"⚠ No se crearon notificaciones críticas para personal {personal.personal_id} - posiblemente no hay usuarios con roles configurados")
        except TipoNotificacion.DoesNotExist:
            logger.error(f"✗ Tipo de notificación crítico RRHH_DOCUMENTO_VENCIMIENTO_CRITICO tampoco existe")
    except Exception as e:
        logger.error(f"✗ Error inesperado al crear notificación para personal {personal.personal_id}: {str(e)}", exc_info=True)


def crear_notificacion_vencimiento_consolidada_equipo(equipo, documentos, hoy, forzar_creacion=False):
    """
    Crea una notificación consolidada para un equipo con todos sus documentos por vencer.
    
    Args:
        equipo: Objeto Equipo
        documentos: Lista de diccionarios con información de documentos por vencer
        hoy: Fecha actual
        forzar_creacion: Si es True, crea la notificación aunque ya exista una hoy
    """
    if not equipo.activo:
        logger.info(f"Equipo {equipo.equipo_id} no está activo, omitiendo")
        return
    
    # Separar documentos críticos y no críticos
    documentos_criticos = [d for d in documentos if d['es_critico']]
    documentos_normales = [d for d in documentos if not d['es_critico']]
    
    # Determinar si es crítica (tiene al menos un documento crítico)
    es_critica = len(documentos_criticos) > 0
    
    # Ordenar documentos por días restantes (más críticos primero)
    todos_documentos = sorted(documentos, key=lambda x: x['dias_restantes'])
    
    # Construir mensaje consolidado
    if es_critica:
        codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_CRITICO'
        titulo = f"⚠️ Vencimientos críticos: {equipo.nombreEquipo}"
        prefijo_mensaje = "⚠️ Los siguientes documentos del equipo "
    else:
        # Usar el código según el menor número de días restantes
        # Mapear a los tipos disponibles: 45D, 30D, 20D, 15D, 10D
        dias_minimos = min(d['dias_restantes'] for d in documentos)
        if dias_minimos >= 45:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_45D'
        elif dias_minimos >= 30:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_30D'
        elif dias_minimos >= 20:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_20D'
        elif dias_minimos >= 15:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_15D'
        else:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_10D'
        titulo = f"Vencimientos próximos: {equipo.nombreEquipo}"
        prefijo_mensaje = "Los siguientes documentos del equipo "
    
    mensaje = (
        f"{prefijo_mensaje}{equipo.nombreEquipo} "
        f"(Código: {equipo.codigoInterno}) están próximos a vencer:\n\n"
    )
    
    # Agregar lista de documentos
    for i, doc in enumerate(todos_documentos, 1):
        estado = "⚠️ CRÍTICO" if doc['es_critico'] else ""
        mensaje += (
            f"{i}. {doc['nombre']} - "
            f"{doc['dias_restantes']} día(s) restantes "
            f"(Vence: {doc['fecha_vencimiento'].strftime('%d/%m/%Y')}) {estado}\n"
        )
    
    # Preparar datos adicionales con todos los documentos
    datos_adicionales = {
        'equipo_id': equipo.equipo_id,
        'total_documentos': len(documentos),
        'documentos_criticos': len(documentos_criticos),
        'documentos': [
            {
                'nombre': doc['nombre'],
                'fecha_vencimiento': doc['fecha_vencimiento'].isoformat(),
                'dias_restantes': doc['dias_restantes'],
                'es_critico': doc['es_critico']
            }
            for doc in todos_documentos
        ]
    }
    
    # Verificar si ya existe una notificación para este equipo HOY
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
        logger.info(f"Tipo de notificación {codigo_tipo} encontrado")
        
        # Verificar existencia usando una búsqueda más simple
        # Buscar notificaciones del mismo tipo y equipo creadas hoy
        existe = False
        try:
            notificaciones_hoy = Notificacion.objects.filter(
                tipo_notificacion=tipo_notif,
                fecha_creacion__date=hoy
            )
            logger.info(f"Buscando notificaciones existentes para equipo {equipo.equipo_id}: {notificaciones_hoy.count()} notificaciones del tipo {codigo_tipo} hoy")
            
            # Verificar manualmente en los datos adicionales porque JSONField puede tener problemas con lookups
            for notif in notificaciones_hoy:
                notif_equipo_id = notif.datos_adicionales.get('equipo_id')
                if notif_equipo_id == equipo.equipo_id:
                    existe = True
                    logger.info(f"Encontrada notificación existente ID {notif.id} para equipo {equipo.equipo_id}")
                    break
        except Exception as e:
            logger.warning(f"Error al verificar notificaciones existentes para equipo {equipo.equipo_id}: {str(e)}")
            # Continuar de todas formas, asumir que no existe
        
        if existe and not forzar_creacion:
            logger.info(f"Ya existe notificación para equipo {equipo.equipo_id} ({equipo.nombreEquipo}) con código {codigo_tipo} hoy - omitiendo")
            return
        elif existe and forzar_creacion:
            logger.info(f"Ya existe notificación para equipo {equipo.equipo_id} pero forzar_creacion=True, creando nueva")
        
        logger.info(f"Creando notificación para equipo {equipo.equipo_id} ({equipo.nombreEquipo}) con código {codigo_tipo}")
        logger.info(f"Mensaje: {titulo}")
        logger.info(f"Documentos a incluir: {len(documentos)}")
        
        try:
            notificaciones_creadas = crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje.strip(),
                datos_adicionales=datos_adicionales
            )
            
            if notificaciones_creadas:
                logger.info(f"✓ Se crearon {len(notificaciones_creadas)} notificaciones para equipo {equipo.equipo_id}")
                for notif in notificaciones_creadas:
                    logger.info(f"  - Notificación ID {notif.id} para usuario {notif.usuario.username}")
            else:
                logger.warning(f"⚠ No se crearon notificaciones para equipo {equipo.equipo_id} - posiblemente no hay usuarios con roles configurados para {codigo_tipo}")
        except Exception as e:
            logger.error(f"✗ Error al llamar crear_notificacion_por_tipo para equipo {equipo.equipo_id}: {str(e)}", exc_info=True)
            raise  # Re-lanzar para que el try-except externo lo capture
            
    except TipoNotificacion.DoesNotExist:
        # Si no existe el tipo específico, usar el crítico como fallback
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe, usando crítico como fallback")
        try:
            codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_CRITICO'
            tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo, activo=True)
            
            # Verificar existencia manualmente
            existe = False
            notificaciones_hoy = Notificacion.objects.filter(
                tipo_notificacion=tipo_notif,
                fecha_creacion__date=hoy
            )
            
            for notif in notificaciones_hoy:
                if notif.datos_adicionales.get('equipo_id') == equipo.equipo_id:
                    existe = True
                    break
            
            if existe:
                logger.info(f"Ya existe notificación crítica para equipo {equipo.equipo_id} hoy - omitiendo")
                return
            
            logger.info(f"Creando notificación crítica para equipo {equipo.equipo_id}")
            notificaciones_creadas = crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje.strip(),
                datos_adicionales=datos_adicionales
            )
            if notificaciones_creadas:
                logger.info(f"✓ Se crearon {len(notificaciones_creadas)} notificaciones críticas para equipo {equipo.equipo_id}")
            else:
                logger.warning(f"⚠ No se crearon notificaciones críticas para equipo {equipo.equipo_id} - posiblemente no hay usuarios con roles configurados")
        except TipoNotificacion.DoesNotExist:
            logger.error(f"✗ Tipo de notificación crítico MAQUINARIAS_DOCUMENTO_VENCIMIENTO_CRITICO tampoco existe")
    except Exception as e:
        logger.error(f"✗ Error inesperado al crear notificación para equipo {equipo.equipo_id}: {str(e)}", exc_info=True)


# Funciones antiguas mantenidas por compatibilidad (ya no se usan)
def crear_notificacion_vencimiento_personal(personal, tipo_doc, nombre_doc, fecha_vencimiento, dias_restantes):
    """
    Crea notificación de vencimiento para documentos de personal.
    Solo crea notificaciones para personal activo.
    """
    # Verificar que el personal esté activo antes de crear la notificación
    if not personal.activo:
        return
    
    codigo_tipo = f'RRHH_DOCUMENTO_VENCIMIENTO_{dias_restantes}D'
    
    titulo = f"Vencimiento próximo: {nombre_doc}"
    mensaje = (
        f"El documento '{nombre_doc}' de {personal.nombre} {personal.apepat} "
        f"(RUT: {personal.rut}-{personal.dvrut}) vence en {dias_restantes} días "
        f"({fecha_vencimiento.strftime('%d/%m/%Y')})."
    )
    
    datos_adicionales = {
        'personal_id': personal.personal_id,
        'tipo_documento': tipo_doc,
        'fecha_vencimiento': fecha_vencimiento.isoformat(),
        'dias_restantes': dias_restantes
    }
    
    # Verificar si ya existe una notificación para este documento y umbral
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo)
        existe = Notificacion.objects.filter(
            tipo_notificacion=tipo_notif,
            datos_adicionales__personal_id=personal.personal_id,
            datos_adicionales__tipo_documento=tipo_doc,
            datos_adicionales__dias_restantes=dias_restantes,
            fecha_creacion__date=timezone.now().date()
        ).exists()
        
        if not existe:
            crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
    except TipoNotificacion.DoesNotExist:
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe")


def crear_notificacion_vencimiento_critico_personal(personal, tipo_doc, nombre_doc, fecha_vencimiento, dias_restantes):
    """
    Crea notificación crítica de vencimiento para documentos de personal (9-1 días).
    Se ejecuta diariamente mientras el documento esté en este rango.
    Solo crea notificaciones para personal activo.
    """
    # Verificar que el personal esté activo antes de crear la notificación
    if not personal.activo:
        return
    
    codigo_tipo = 'RRHH_DOCUMENTO_VENCIMIENTO_CRITICO'
    
    titulo = f"⚠️ Vencimiento crítico: {nombre_doc}"
    mensaje = (
        f"⚠️ El documento '{nombre_doc}' de {personal.nombre} {personal.apepat} "
        f"(RUT: {personal.rut}-{personal.dvrut}) vence en {dias_restantes} día(s) "
        f"({fecha_vencimiento.strftime('%d/%m/%Y')})."
    )
    
    datos_adicionales = {
        'personal_id': personal.personal_id,
        'tipo_documento': tipo_doc,
        'fecha_vencimiento': fecha_vencimiento.isoformat(),
        'dias_restantes': dias_restantes
    }
    
    # Verificar si ya existe una notificación creada HOY para este documento
    # (para evitar duplicados si se ejecuta múltiples veces el mismo día)
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo)
        existe = Notificacion.objects.filter(
            tipo_notificacion=tipo_notif,
            datos_adicionales__personal_id=personal.personal_id,
            datos_adicionales__tipo_documento=tipo_doc,
            datos_adicionales__dias_restantes=dias_restantes,
            fecha_creacion__date=timezone.now().date()
        ).exists()
        
        if not existe:
            crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
    except TipoNotificacion.DoesNotExist:
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe")


def crear_notificacion_vencimiento_equipo(equipo, nombre_doc, fecha_vencimiento, dias_restantes):
    """
    Crea notificación de vencimiento para documentos de equipos.
    Solo crea notificaciones para equipos activos.
    """
    # Verificar que el equipo esté activo antes de crear la notificación
    if not equipo.activo:
        return
    
    codigo_tipo = f'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_{dias_restantes}D'
    
    titulo = f"Vencimiento próximo: {nombre_doc}"
    mensaje = (
        f"El documento '{nombre_doc}' del equipo {equipo.nombreEquipo} "
        f"(Código: {equipo.codigoInterno}) vence en {dias_restantes} días "
        f"({fecha_vencimiento.strftime('%d/%m/%Y')})."
    )
    
    datos_adicionales = {
        'equipo_id': equipo.equipo_id,
        'tipo_documento': nombre_doc,
        'fecha_vencimiento': fecha_vencimiento.isoformat(),
        'dias_restantes': dias_restantes
    }
    
    # Verificar si ya existe una notificación para este documento y umbral
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo)
        existe = Notificacion.objects.filter(
            tipo_notificacion=tipo_notif,
            datos_adicionales__equipo_id=equipo.equipo_id,
            datos_adicionales__tipo_documento=nombre_doc,
            datos_adicionales__dias_restantes=dias_restantes,
            fecha_creacion__date=timezone.now().date()
        ).exists()
        
        if not existe:
            crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
    except TipoNotificacion.DoesNotExist:
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe")


def crear_notificacion_vencimiento_critico_equipo(equipo, nombre_doc, fecha_vencimiento, dias_restantes):
    """
    Crea notificación crítica de vencimiento para documentos de equipos (9-1 días).
    Se ejecuta diariamente mientras el documento esté en este rango.
    Solo crea notificaciones para equipos activos.
    """
    # Verificar que el equipo esté activo antes de crear la notificación
    if not equipo.activo:
        return
    
    codigo_tipo = 'MAQUINARIAS_DOCUMENTO_VENCIMIENTO_CRITICO'
    
    titulo = f"⚠️ Vencimiento crítico: {nombre_doc}"
    mensaje = (
        f"⚠️ El documento '{nombre_doc}' del equipo {equipo.nombreEquipo} "
        f"(Código: {equipo.codigoInterno}) vence en {dias_restantes} día(s) "
        f"({fecha_vencimiento.strftime('%d/%m/%Y')})."
    )
    
    datos_adicionales = {
        'equipo_id': equipo.equipo_id,
        'tipo_documento': nombre_doc,
        'fecha_vencimiento': fecha_vencimiento.isoformat(),
        'dias_restantes': dias_restantes
    }
    
    # Verificar si ya existe una notificación creada HOY para este documento
    # (para evitar duplicados si se ejecuta múltiples veces el mismo día)
    from .models import Notificacion, TipoNotificacion
    try:
        tipo_notif = TipoNotificacion.objects.get(codigo=codigo_tipo)
        existe = Notificacion.objects.filter(
            tipo_notificacion=tipo_notif,
            datos_adicionales__equipo_id=equipo.equipo_id,
            datos_adicionales__tipo_documento=nombre_doc,
            datos_adicionales__dias_restantes=dias_restantes,
            fecha_creacion__date=timezone.now().date()
        ).exists()
        
        if not existe:
            crear_notificacion_por_tipo(
                codigo_tipo=codigo_tipo,
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
    except TipoNotificacion.DoesNotExist:
        logger.warning(f"Tipo de notificación {codigo_tipo} no existe")

