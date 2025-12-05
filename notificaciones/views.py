"""
Vistas para el sistema de notificaciones.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Notificacion
from .utils import contar_notificaciones_no_leidas, obtener_notificaciones_no_leidas
import json


@login_required
@require_http_methods(["GET"])
def api_notificaciones(request):
    """
    API para obtener las notificaciones del usuario actual.
    
    Parámetros opcionales:
    - limit: Número máximo de notificaciones a retornar (default: 10)
    - leida: Filtrar por estado de lectura (true/false)
    - archivada: Filtrar por estado de archivado (true/false)
    """
    limit = int(request.GET.get('limit', 10))
    leida = request.GET.get('leida')
    archivada = request.GET.get('archivada')
    
    queryset = Notificacion.objects.filter(usuario=request.user).select_related('tipo_notificacion')
    
    if leida is not None:
        queryset = queryset.filter(leida=leida.lower() == 'true')
    
    if archivada is not None:
        queryset = queryset.filter(archivada=archivada.lower() == 'true')
    
    notificaciones = queryset.order_by('-fecha_creacion')[:limit]
    
    data = []
    for notif in notificaciones:
        data.append({
            'id': notif.id,
            'titulo': notif.titulo,
            'mensaje': notif.mensaje,
            'tipo': notif.tipo_notificacion.nombre,
            'codigo_tipo': notif.tipo_notificacion.codigo,
            'categoria': notif.tipo_notificacion.categoria,
            'prioridad': notif.prioridad,
            'leida': notif.leida,
            'archivada': notif.archivada,
            'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'datos_adicionales': notif.datos_adicionales
        })
    
    return JsonResponse({
        'success': True,
        'notificaciones': data,
        'total': queryset.count()
    })


@login_required
@require_http_methods(["GET"])
def api_contar_notificaciones_no_leidas(request):
    """
    API para obtener el conteo de notificaciones no leídas del usuario actual.
    """
    count = contar_notificaciones_no_leidas(request.user)
    return JsonResponse({
        'success': True,
        'count': count
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_marcar_leida(request, notificacion_id):
    """
    API para marcar una notificación como leída.
    Retorna el nuevo contador de notificaciones no leídas.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        
        # Solo marcar como leída si no está leída
        if not notificacion.leida:
            notificacion.marcar_como_leida()
        
        # Obtener el nuevo contador después de marcar como leída
        nuevo_contador = contar_notificaciones_no_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída',
            'count': nuevo_contador  # Retornar el nuevo contador
        })
    except Notificacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=404)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_marcar_todas_leidas(request):
    """
    API para marcar todas las notificaciones del usuario como leídas.
    Retorna el nuevo contador (debería ser 0).
    """
    try:
        Notificacion.objects.filter(usuario=request.user, leida=False, archivada=False).update(
            leida=True,
            fecha_leida=timezone.now()
        )
        
        # Obtener el nuevo contador después de marcar todas como leídas
        nuevo_contador = contar_notificaciones_no_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Todas las notificaciones marcadas como leídas',
            'count': nuevo_contador  # Retornar el nuevo contador
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_archivar(request, notificacion_id):
    """
    API para archivar una notificación.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        notificacion.archivar()
        return JsonResponse({
            'success': True,
            'message': 'Notificación archivada'
        })
    except Notificacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=404)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_desarchivar(request, notificacion_id):
    """
    API para desarchivar una notificación.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        notificacion.desarchivar()
        return JsonResponse({
            'success': True,
            'message': 'Notificación desarchivada'
        })
    except Notificacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=404)


@login_required
def ver_notificaciones(request):
    """
    Vista para mostrar la página de notificaciones.
    """
    from django.shortcuts import render
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).select_related('tipo_notificacion').order_by('-fecha_creacion')
    
    # Filtrar por parámetros GET
    leida = request.GET.get('leida', '')
    archivada = request.GET.get('archivada', 'false')
    categoria = request.GET.get('categoria', '')
    
    # Filtrar por estado de lectura
    if leida == 'true':
        notificaciones = notificaciones.filter(leida=True)
    elif leida == 'false':
        notificaciones = notificaciones.filter(leida=False)
    
    # Filtrar por estado de archivado
    if archivada == 'true':
        notificaciones = notificaciones.filter(archivada=True)
    elif archivada == 'false':
        notificaciones = notificaciones.filter(archivada=False)
    # Si archivada es vacío (''), no se filtra (muestra todas)
    
    # Filtrar por categoría
    if categoria:
        notificaciones = notificaciones.filter(tipo_notificacion__categoria=categoria)
    
    context = {
        'notificaciones': notificaciones,
        'total_no_leidas': contar_notificaciones_no_leidas(request.user)
    }
    
    return render(request, 'notificaciones/notificaciones.html', context)
