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


def procesar_vencimientos_documentos():
    """
    Procesa todos los documentos próximos a vencer y crea notificaciones.
    Revisa documentos de personal y equipos.
    
    Umbrales:
    - 45, 30, 20, 15, 10 días: Notificación única cuando quedan exactamente esos días
    - 9-1 días: Notificación diaria (crítica)
    """
    hoy = timezone.now().date()
    umbrales_unicos = [45, 30, 20, 15, 10]  # Días exactos para notificación única
    
    # Procesar documentos de personal
    procesar_vencimientos_personal(hoy, umbrales_unicos)
    
    # Procesar documentos de equipos
    procesar_vencimientos_equipos(hoy, umbrales_unicos)


def procesar_vencimientos_personal(hoy, umbrales_unicos):
    """
    Procesa vencimientos de documentos de personal.
    """
    # Licencias de conducir (LicenciaPorPersonal)
    licencias_conducir = LicenciaPorPersonal.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id')
    
    for licencia in licencias_conducir:
        if licencia.fechaVencimiento:
            dias_restantes = (licencia.fechaVencimiento - hoy).days
            tipos_str = ", ".join([t.tipoLicencia for t in licencia.tipos.all()])
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_personal(
                    licencia.personal_id,
                    'LICENCIA_CONDUCIR',
                    f'Licencia de Conducir ({tipos_str})',
                    licencia.fechaVencimiento,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_personal(
                    licencia.personal_id,
                    'LICENCIA_CONDUCIR',
                    f'Licencia de Conducir ({tipos_str})',
                    licencia.fechaVencimiento,
                    dias_restantes
                )
    
    # Licencias internas
    licencias_internas = LicenciaInternaPorPersonal.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoLicenciaInterna_id')
    
    for licencia in licencias_internas:
        if licencia.fechaVencimiento:
            dias_restantes = (licencia.fechaVencimiento - hoy).days
            tipo_nombre = licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else 'N/A'
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_personal(
                    licencia.personal_id,
                    'LICENCIA_INTERNA',
                    f'Licencia Interna: {tipo_nombre}',
                    licencia.fechaVencimiento,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_personal(
                    licencia.personal_id,
                    'LICENCIA_INTERNA',
                    f'Licencia Interna: {tipo_nombre}',
                    licencia.fechaVencimiento,
                    dias_restantes
                )
    
    # Licencias médicas
    licencias_medicas = LicenciaMedicaPorPersonal.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoLicenciaMedica_id')
    
    for licencia in licencias_medicas:
        if licencia.fecha_fin_licencia:
            dias_restantes = (licencia.fecha_fin_licencia - hoy).days
            tipo_nombre = licencia.tipoLicenciaMedica_id.tipoLicenciaMedica if licencia.tipoLicenciaMedica_id else 'N/A'
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_personal(
                    licencia.personal_id,
                    'LICENCIA_MEDICA',
                    f'Licencia Médica: {tipo_nombre}',
                    licencia.fecha_fin_licencia,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_personal(
                    licencia.personal_id,
                    'LICENCIA_MEDICA',
                    f'Licencia Médica: {tipo_nombre}',
                    licencia.fecha_fin_licencia,
                    dias_restantes
                )
    
    # Certificaciones
    certificaciones = Certificacion.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoCertificacion_id')
    
    for cert in certificaciones:
        if cert.fechaVencimiento:
            dias_restantes = (cert.fechaVencimiento - hoy).days
            tipo_nombre = cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else 'N/A'
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_personal(
                    cert.personal_id,
                    'CERTIFICACION',
                    f"Certificación: {tipo_nombre}",
                    cert.fechaVencimiento,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_personal(
                    cert.personal_id,
                    'CERTIFICACION',
                    f"Certificación: {tipo_nombre}",
                    cert.fechaVencimiento,
                    dias_restantes
                )
    
    # Exámenes
    examenes = Examen.objects.filter(
        personal_id__activo=True
    ).select_related('personal_id', 'tipoEx_id')
    
    for examen in examenes:
        if examen.fechaVencimiento:
            dias_restantes = (examen.fechaVencimiento - hoy).days
            tipo_nombre = examen.tipoEx_id.tipoExamen if examen.tipoEx_id else 'N/A'
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_personal(
                    examen.personal_id,
                    'EXAMEN',
                    f"Examen: {tipo_nombre}",
                    examen.fechaVencimiento,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_personal(
                    examen.personal_id,
                    'EXAMEN',
                    f"Examen: {tipo_nombre}",
                    examen.fechaVencimiento,
                    dias_restantes
                )


def procesar_vencimientos_equipos(hoy, umbrales_unicos):
    """
    Procesa vencimientos de documentos de equipos.
    """
    documentos = DocumentoMaquinaria.objects.filter(
        equipo_id__activo=True
    ).select_related('equipo_id', 'tipo_documento_id')
    
    for documento in documentos:
        if documento.fecha_vencimiento:
            dias_restantes = (documento.fecha_vencimiento - hoy).days
            tipo_nombre = documento.tipo_documento_id.nombre if documento.tipo_documento_id else 'Documento'
            
            # Notificación única para umbrales exactos
            if dias_restantes in umbrales_unicos:
                crear_notificacion_vencimiento_equipo(
                    documento.equipo_id,
                    tipo_nombre,
                    documento.fecha_vencimiento,
                    dias_restantes
                )
            # Notificación diaria para rango crítico (9-1 días)
            elif 1 <= dias_restantes <= 9:
                crear_notificacion_vencimiento_critico_equipo(
                    documento.equipo_id,
                    tipo_nombre,
                    documento.fecha_vencimiento,
                    dias_restantes
                )


def crear_notificacion_vencimiento_personal(personal, tipo_doc, nombre_doc, fecha_vencimiento, dias_restantes):
    """
    Crea notificación de vencimiento para documentos de personal.
    """
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
    """
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
    """
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
    """
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

