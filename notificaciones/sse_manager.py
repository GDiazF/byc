# ============================================================================
# GESTOR DE CONEXIONES SERVER-SENT EVENTS (SSE)
# ============================================================================
# Este módulo gestiona las conexiones SSE activas de los usuarios para
# enviar notificaciones en tiempo real. Como solo hay una instancia del servidor,
# usamos un diccionario en memoria.
# ============================================================================

import json
import time
import threading
import queue
from typing import Dict, List
from django.contrib.auth.models import User


class SSEManager:
    """
    Gestor de conexiones Server-Sent Events (SSE).
    
    Mantiene un registro de todas las conexiones SSE activas de los usuarios
    y permite enviar eventos a usuarios específicos usando colas thread-safe.
    Como solo hay una instancia del servidor, usa un diccionario en memoria.
    """
    
    def __init__(self):
        # Diccionario: user_id -> lista de colas (una por conexión)
        self._connections: Dict[int, List[queue.Queue]] = {}
        # Lock para thread-safety
        self._lock = threading.Lock()
        # Timeout de conexión en segundos (5 minutos por seguridad)
        self._connection_timeout = 300  # 5 minutos
        
    def add_connection(self, user: User, event_queue: queue.Queue):
        """
        Agrega una nueva conexión SSE para un usuario.
        
        Registra una nueva cola de eventos para el usuario, permitiendo
        que se le envíen eventos SSE en tiempo real.
        
        Args:
            user (User): Usuario autenticado
            event_queue (queue.Queue): Cola para enviar eventos al cliente
        """
        user_id = user.id
        with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = []
            self._connections[user_id].append(event_queue)
    
    def remove_connection(self, user: User, event_queue: queue.Queue):
        """
        Remueve una conexión SSE de un usuario.
        
        Elimina la cola de eventos del registro de conexiones activas.
        Si no quedan conexiones para el usuario, elimina su entrada del diccionario.
        
        Args:
            user (User): Usuario autenticado
            event_queue (queue.Queue): Cola que se debe remover
        """
        user_id = user.id
        with self._lock:
            if user_id in self._connections:
                try:
                    self._connections[user_id].remove(event_queue)
                    # Si no quedan conexiones, eliminar la entrada
                    if not self._connections[user_id]:
                        del self._connections[user_id]
                except ValueError:
                    # La cola no estaba en la lista (ya fue removida)
                    pass
    
    def send_to_user(self, user_id: int, event_type: str, data: dict):
        """
        Envía un evento SSE a todas las conexiones activas de un usuario.
        
        Envía el evento a todas las conexiones SSE abiertas del usuario.
        Si una cola está llena o hay un error, se remueve automáticamente.
        
        Args:
            user_id (int): ID del usuario destinatario
            event_type (str): Tipo de evento ('notification', 'count_update', etc.)
            data (dict): Datos del evento (debe ser serializable a JSON)
        """
        with self._lock:
            if user_id not in self._connections:
                return  # Usuario no tiene conexiones activas
            
            # Crear el mensaje SSE
            message = {
                'type': event_type,
                'data': data,
                'timestamp': time.time()
            }
            
            # Enviar a todas las conexiones del usuario
            connections_to_remove = []
            for event_queue in self._connections[user_id]:
                try:
                    # Intentar poner el evento en la cola (no bloqueante)
                    event_queue.put_nowait((event_type, json.dumps(message)))
                except queue.Full:
                    # Cola llena, marcar para remover
                    connections_to_remove.append(event_queue)
                except Exception:
                    # Error, marcar para remover
                    connections_to_remove.append(event_queue)
            
            # Remover conexiones que fallaron
            for event_queue in connections_to_remove:
                try:
                    self._connections[user_id].remove(event_queue)
                except ValueError:
                    pass
            
            # Limpiar entrada si no quedan conexiones
            if user_id in self._connections and not self._connections[user_id]:
                del self._connections[user_id]
    
    def get_active_connections_count(self, user_id: int = None) -> int:
        """
        Obtiene el número de conexiones activas.
        
        Args:
            user_id (int, optional): Si se especifica, cuenta solo las conexiones
                                    de ese usuario. Si es None, cuenta todas las conexiones.
                                    
        Returns:
            int: Número de conexiones activas
        """
        with self._lock:
            if user_id:
                return len(self._connections.get(user_id, []))
            else:
                return sum(len(conns) for conns in self._connections.values())
    
    def cleanup_old_connections(self):
        """
        Limpia conexiones antiguas (útil si implementamos tracking de tiempo).
        
        Por ahora, las conexiones se limpian automáticamente cuando se cierran.
        Esta función puede expandirse en el futuro si necesitamos limpiar conexiones
        basadas en tiempo de inactividad.
        """
        pass


# Instancia global del gestor SSE
# Se usa una única instancia compartida en toda la aplicación
sse_manager = SSEManager()

