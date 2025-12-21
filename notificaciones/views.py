# ============================================================================
# VISTAS PARA EL SISTEMA DE NOTIFICACIONES
# ============================================================================
# Este módulo contiene las vistas para el sistema de notificaciones:
# - ver_notificaciones: Vista principal para mostrar notificaciones
# - api_notificaciones: API para obtener notificaciones
# - api_contar_notificaciones_no_leidas: API para contar notificaciones no leídas
# - api_marcar_leida: API para marcar notificación como leída
# - api_marcar_todas_leidas: API para marcar todas como leídas
# - api_archivar: API para archivar notificación
# - api_desarchivar: API para desarchivar notificación
# - sse_notificaciones: Server-Sent Events para notificaciones en tiempo real
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.timezone import localtime
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
    
    Esta función permite obtener las notificaciones del usuario autenticado
    con filtros opcionales por estado de lectura y archivado.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetros GET:
            - limit (int): Número máximo de notificaciones a retornar (default: 10)
            - leida (str): Filtrar por estado de lectura ('true'/'false')
            - archivada (str): Filtrar por estado de archivado ('true'/'false')
            
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - notificaciones (list): Lista de notificaciones formateadas
            - total (int): Total de notificaciones que cumplen los filtros
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
            'fecha_creacion': localtime(notif.fecha_creacion).strftime('%d/%m/%Y %H:%M'),
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
    
    Usa caché para evitar consultas repetidas a la base de datos.
    El caché se invalida automáticamente cuando se crean/modifican notificaciones.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - count (int): Número de notificaciones no leídas
    """
    from django.core.cache import cache
    
    # Clave de caché única por usuario
    cache_key = f'notif_count_user_{request.user.id}'
    
    # Intentar obtener del caché primero
    count = cache.get(cache_key)
    
    if count is None:
        # Si no está en caché, calcular y guardar por 30 segundos
        count = contar_notificaciones_no_leidas(request.user)
        cache.set(cache_key, count, 30)  # Caché de 30 segundos
    
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
    
    Marca una notificación específica como leída y envía un evento SSE
    para actualizar el contador en tiempo real.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        notificacion_id (int): ID de la notificación a marcar como leída.
        
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - message (str): Mensaje descriptivo
            - count (int): Nuevo contador de notificaciones no leídas
            - error (str): Mensaje de error si success=False
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
    
    Marca todas las notificaciones no leídas y no archivadas del usuario
    como leídas y envía un evento SSE para actualizar el contador en tiempo real.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - message (str): Mensaje descriptivo
            - count (int): Nuevo contador de notificaciones no leídas (debería ser 0)
            - error (str): Mensaje de error si success=False
    """
    try:
        from django.core.cache import cache
        
        # Marcar todas las notificaciones como leídas
        Notificacion.objects.filter(usuario=request.user, leida=False, archivada=False).update(
            leida=True,
            fecha_leida=timezone.now()
        )
        
        # Invalidar el caché del contador para forzar recálculo
        cache_key = f'notif_count_user_{request.user.id}'
        cache.delete(cache_key)
        
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
    
    Archiva una notificación específica del usuario autenticado.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        notificacion_id (int): ID de la notificación a archivar.
        
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - message (str): Mensaje descriptivo
            - error (str): Mensaje de error si success=False
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
    
    Desarchiva una notificación específica del usuario autenticado.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        notificacion_id (int): ID de la notificación a desarchivar.
        
    Returns:
        JsonResponse: Respuesta JSON con:
            - success (bool): Indica si la operación fue exitosa
            - message (str): Mensaje descriptivo
            - error (str): Mensaje de error si success=False
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
    Vista para mostrar la página principal de notificaciones.
    
    Renderiza la página HTML con las notificaciones del usuario autenticado,
    permitiendo filtrar por estado de lectura, archivado y categoría.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetros GET opcionales:
            - leida (str): Filtrar por estado de lectura ('true'/'false')
            - archivada (str): Filtrar por estado de archivado ('true'/'false')
            - categoria (str): Filtrar por categoría de notificación
            
    Returns:
        HttpResponse: Renderiza el template 'notificaciones/notificaciones.html' con:
            - notificaciones: QuerySet de notificaciones filtradas
            - total_no_leidas: Contador de notificaciones no leídas
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
    
    Tipos de eventos enviados:
    - 'connected': Evento inicial cuando se establece la conexión
    - 'notification': Nueva notificación recibida
    - 'count_update': Actualización del contador de notificaciones no leídas
    - 'heartbeat': Mantiene la conexión viva (cada 30 segundos)
    - 'timeout': Conexión cerrada por timeout
    - 'error': Error en la conexión
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP del usuario autenticado.
        
    Returns:
        StreamingHttpResponse: Respuesta streaming con content_type='text/event-stream'
                                que mantiene la conexión abierta y envía eventos SSE.
    """
    import queue
    
    def event_stream():
        """
        Generador que envía eventos SSE al cliente.
        
        Esta función es un generador que mantiene la conexión SSE abierta,
        envía eventos cuando hay notificaciones nuevas y mantiene la conexión
        viva con heartbeats periódicos.
        
        Yields:
            str: Mensajes SSE formateados según el protocolo Server-Sent Events.
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
