"""
Vistas personalizadas para autenticación.
"""

from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Vista personalizada de login que detecta intentos fallidos y crea notificaciones.
    """
    
    def form_invalid(self, form):
        """
        Se ejecuta cuando el formulario de login es inválido (credenciales incorrectas).
        """
        # Obtener el username del formulario (aunque sea inválido, el campo username puede tener valor)
        username = form.data.get('username', '') or form.cleaned_data.get('username', '')
        
        # Intentar obtener el usuario (aunque las credenciales sean incorrectas)
        if username:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=username)
                # Si el usuario existe, registrar el intento fallido
                self._registrar_intento_fallido(user)
            except User.DoesNotExist:
                # Usuario no existe, pero aún así notificar a los roles configurados
                # sobre intentos de login con usuarios inexistentes
                self._registrar_intento_fallido_usuario_inexistente(username)
        
        # Llamar al método padre para el comportamiento normal
        return super().form_invalid(form)
    
    def _registrar_intento_fallido(self, user):
        """
        Registra un intento de login fallido y crea notificación si hay muchos intentos.
        Funciona con cualquier backend de cache (local, Redis, Memcached, etc.)
        """
        try:
            # Usar cache para contar intentos fallidos
            # Compatible con cualquier backend: LocMemCache, Redis, Memcached, etc.
            cache_key = f'login_failed_{user.id}'
            intentos = cache.get(cache_key, 0)
            intentos += 1
            
            # Guardar en cache por 15 minutos
            # Si el cache falla, continuamos igual (no bloqueamos el login)
            cache.set(cache_key, intentos, 900)  # 15 minutos = 900 segundos
        except Exception as e:
            # Si el cache no está disponible, usar valor por defecto
            # Esto permite que el sistema funcione incluso si Redis/cache está caído
            logger.warning(f"Cache no disponible para registrar intento fallido: {str(e)}")
            intentos = 1  # Asumir que es el primer intento si no podemos contar
        
        # Crear notificación para los roles configurados (administradores, seguridad, etc.)
        try:
            from notificaciones.utils import crear_notificacion_por_tipo
            
            fecha_intento = timezone.now().strftime('%d/%m/%Y %H:%M')
            ip_address = self.request.META.get('REMOTE_ADDR', '')
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:200]
            
            # Crear notificación para cada intento fallido
            # Esta notificación llegará a los roles que tengan configurada la notificación GENERAL_LOGIN_FALLIDO
            crear_notificacion_por_tipo(
                codigo_tipo='GENERAL_LOGIN_FALLIDO',
                titulo=f'Intento de login fallido: {user.username}',
                mensaje=f'Se detectó un intento de login fallido para la cuenta {user.username} el {fecha_intento}. '
                       f'IP: {ip_address}. '
                       f'Total de intentos fallidos recientes: {intentos}.',
                datos_adicionales={
                    'usuario_intento': user.username,
                    'usuario_id': user.id,
                    'fecha_intento': timezone.now().isoformat(),
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'intentos_fallidos': intentos
                },
                prioridad='ALTA' if intentos >= 3 else 'MEDIA'
            )
            
            # Si hay 3 o más intentos fallidos, crear notificación adicional de seguridad
            if intentos >= 3:
                crear_notificacion_por_tipo(
                    codigo_tipo='GENERAL_LOGIN_FALLIDO',
                    titulo=f'⚠️ ALERTA: Múltiples intentos de login fallidos ({intentos}) - {user.username}',
                    mensaje=f'⚠️ ALERTA DE SEGURIDAD: Se han detectado {intentos} intentos de login fallidos '
                           f'para la cuenta {user.username} en los últimos 15 minutos. '
                           f'IP: {ip_address}. '
                           f'Esto podría indicar un intento de acceso no autorizado.',
                    datos_adicionales={
                        'usuario_intento': user.username,
                        'usuario_id': user.id,
                        'fecha_intento': timezone.now().isoformat(),
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'intentos_fallidos': intentos,
                        'alerta_seguridad': True
                    },
                    prioridad='ALTA'
                )
        except Exception as e:
            logger.error(f"Error al crear notificación de login fallido: {str(e)}")
    
    def _registrar_intento_fallido_usuario_inexistente(self, username):
        """
        Registra un intento de login fallido con un usuario que no existe.
        Notifica a los roles configurados sobre posibles intentos de acceso no autorizado.
        """
        try:
            from notificaciones.utils import crear_notificacion_por_tipo
            
            fecha_intento = timezone.now().strftime('%d/%m/%Y %H:%M')
            ip_address = self.request.META.get('REMOTE_ADDR', '')
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:200]
            
            # Crear notificación para los roles configurados
            crear_notificacion_por_tipo(
                codigo_tipo='GENERAL_LOGIN_FALLIDO',
                titulo=f'Intento de login con usuario inexistente: {username}',
                mensaje=f'Se detectó un intento de login fallido con el usuario "{username}" que no existe en el sistema. '
                       f'Fecha: {fecha_intento}. IP: {ip_address}. '
                       f'Esto podría indicar un intento de acceso no autorizado o un ataque de fuerza bruta.',
                datos_adicionales={
                    'usuario_intento': username,
                    'usuario_existe': False,
                    'fecha_intento': timezone.now().isoformat(),
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'intentos_fallidos': 1
                },
                prioridad='ALTA'  # Alta prioridad porque es un usuario inexistente
            )
        except Exception as e:
            logger.error(f"Error al crear notificación de login fallido (usuario inexistente): {str(e)}")
    
    def form_valid(self, form):
        """
        Se ejecuta cuando el login es exitoso.
        Limpia el contador de intentos fallidos.
        """
        username = form.cleaned_data.get('username')
        user = authenticate(
            username=username,
            password=form.cleaned_data.get('password')
        )
        
        if user:
            # Limpiar contador de intentos fallidos al hacer login exitoso
            try:
                cache_key = f'login_failed_{user.id}'
                cache.delete(cache_key)
            except Exception as e:
                # Si el cache falla, no es crítico, solo logueamos
                logger.warning(f"No se pudo limpiar contador de intentos fallidos: {str(e)}")
        
        return super().form_valid(form)
