"""
Vistas para el sistema de notificaciones.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Notificacion
from .utils import contar_notificaciones_no_leidas, obtener_notificaciones_no_leidas
from .sse_manager import sse_manager
import json
import time


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
            
            # Enviar evento SSE para actualizar el contador en tiempo real
            sse_manager.send_to_user(
                user_id=request.user.id,
                event_type='count_update',
                data={'count': nuevo_contador}
            )
        else:
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
        
        # Enviar evento SSE para actualizar el contador en tiempo real
        sse_manager.send_to_user(
            user_id=request.user.id,
            event_type='count_update',
            data={'count': nuevo_contador}
        )
        
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


@login_required
@require_http_methods(["GET"])
def sse_notificaciones(request):
    """
    Vista Server-Sent Events (SSE) para notificaciones en tiempo real.
    
    Mantiene una conexión abierta con el cliente y envía eventos cuando
    hay notificaciones nuevas. La conexión se cierra automáticamente después
    de 5 minutos de inactividad por seguridad.
    """
    import queue
    
    def event_stream():
        """
        Generador que envía eventos SSE al cliente.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Crear cola para recibir eventos
        event_queue = queue.Queue(maxsize=10)  # Máximo 10 eventos en cola
        
        # Registrar esta conexión
        try:
            sse_manager.add_connection(request.user, event_queue)
            logger.info(f'Conexión SSE registrada para usuario {request.user.id} ({request.user.username})')
        except Exception as e:
            logger.error(f'Error al registrar conexión SSE: {str(e)}')
        
        try:
            # Enviar evento inicial de conexión
            initial_count = contar_notificaciones_no_leidas(request.user)
            logger.info(f'Enviando evento inicial de conexión para usuario {request.user.id}, contador: {initial_count}')
            yield f"event: connected\ndata: {json.dumps({'count': initial_count, 'message': 'Conexión establecida'})}\n\n"
            
            # Mantener conexión abierta y enviar heartbeat periódico
            start_time = time.time()
            last_heartbeat = time.time()
            heartbeat_interval = 30  # Enviar heartbeat cada 30 segundos
            connection_timeout = 300  # Cerrar conexión después de 5 minutos
            
            while True:
                # Verificar timeout
                elapsed = time.time() - start_time
                if elapsed > connection_timeout:
                    yield f"event: timeout\ndata: {json.dumps({'message': 'Conexión cerrada por timeout de seguridad'})}\n\n"
                    break
                
                # Intentar obtener eventos de la cola (no bloqueante)
                try:
                    event_type, event_data = event_queue.get_nowait()
                    logger.info(f'Enviando evento SSE tipo {event_type} para usuario {request.user.id}')
                    yield f"event: {event_type}\ndata: {event_data}\n\n"
                except queue.Empty:
                    # No hay eventos nuevos, continuar
                    pass
                except Exception as e:
                    logger.error(f'Error al obtener evento de la cola: {str(e)}')
                
                # Enviar heartbeat periódico para mantener conexión viva
                if time.time() - last_heartbeat >= heartbeat_interval:
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': time.time()})}\n\n"
                    last_heartbeat = time.time()
                
                # Esperar un poco antes de la siguiente iteración
                time.sleep(0.5)  # Revisar cada medio segundo
                
        except GeneratorExit:
            # Cliente cerró la conexión
            pass
        except Exception as e:
            # Error en la conexión
            try:
                yield f"event: error\ndata: {json.dumps({'message': 'Error en la conexión', 'error': str(e)})}\n\n"
            except:
                pass
        finally:
            # Remover conexión cuando se cierra
            sse_manager.remove_connection(request.user, event_queue)
    
    # Crear respuesta streaming con headers SSE
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Deshabilitar buffering en Nginx
    # No establecer 'Connection: keep-alive' - el servidor de desarrollo de Django no lo permite
    # En producción con Gunicorn/Nginx esto se maneja automáticamente
    
    return response
