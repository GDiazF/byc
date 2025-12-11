# ============================================================================
# VISTAS PERSONALIZADAS PARA AUTENTICACIÓN
# ============================================================================
# Este archivo contiene vistas personalizadas para el sistema de login
# que detectan intentos fallidos y crean notificaciones de seguridad.
# ============================================================================

from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Vista personalizada de login que detecta intentos fallidos y crea notificaciones.
    
    Extiende la vista de login de Django para agregar funcionalidad de seguridad:
    - Detecta intentos de login fallidos
    - Cuenta intentos consecutivos usando cache
    - Crea notificaciones de seguridad cuando se alcanzan 3 intentos fallidos
    - Limpia el contador cuando el login es exitoso
    """
    
    def form_invalid(self, form):
        """
        Se ejecuta cuando el formulario de login es inválido (credenciales incorrectas).
        
        Registra el intento fallido en cache y crea una notificación de seguridad
        cuando se alcanzan 3 intentos fallidos consecutivos. Solo registra intentos
        para usuarios que existen en la base de datos para evitar spam.
        
        Args:
            form: Formulario de login inválido.
            
        Returns:
            HttpResponse: Respuesta del método padre con el formulario inválido.
        """
        # Obtener el username del formulario (aunque sea inválido, el campo username puede tener valor)
        username = form.data.get('username', '') or form.cleaned_data.get('username', '')
        
        # Intentar obtener el usuario (aunque las credenciales sean incorrectas)
        # SOLO registrar intentos fallidos si el usuario existe en la BDD
        if username:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=username)
                # Si el usuario existe, registrar el intento fallido
                # Solo se notificará cuando se alcancen 3 intentos fallidos consecutivos
                self._registrar_intento_fallido(user)
            except User.DoesNotExist:
                # Usuario no existe - NO crear notificaciones para evitar spam
                # Solo loguear para debugging
                logger.debug(f"Intento de login con usuario inexistente: {username} (no se creará notificación)")
                pass
        
        # Llamar al método padre para el comportamiento normal
        return super().form_invalid(form)
    
    def _registrar_intento_fallido(self, user):
        """
        Registra un intento de login fallido y crea notificación cuando se alcancen 3 intentos.
        
        Usa el sistema de cache de Django para contar intentos fallidos por usuario.
        Cada usuario tiene su propio contador independiente que expira después de 15 minutos.
        Solo crea una notificación cuando se alcanzan exactamente 3 intentos fallidos
        para evitar spam de notificaciones.
        
        Funciona con cualquier backend de cache (LocMemCache, Redis, Memcached, etc.).
        Si el cache no está disponible, no crea notificaciones para evitar falsos positivos.
        
        Args:
            user (User): Usuario para el cual se registra el intento fallido.
        """
        cache_key = f'login_failed_{user.id}'
        intentos = 0
        
        try:
            # Usar cache para contar intentos fallidos por usuario
            # Compatible con cualquier backend: LocMemCache, Redis, Memcached, etc.
            intentos = cache.get(cache_key, 0)
            intentos += 1
            
            # Guardar en cache por 15 minutos
            # Si el cache falla, continuamos igual (no bloqueamos el login)
            cache.set(cache_key, intentos, 900)  # 15 minutos = 900 segundos
            
            logger.debug(f"Intento fallido #{intentos} para usuario {user.username} (ID: {user.id})")
        except Exception as e:
            # Si el cache no está disponible, no podemos contar intentos
            # No crear notificaciones si no podemos contar correctamente
            logger.warning(f"Cache no disponible para registrar intento fallido del usuario {user.username}: {str(e)}")
            return  # Salir sin crear notificación si no podemos contar
        
        # Crear notificación SOLO cuando se alcancen exactamente 3 intentos fallidos
        # No crear notificación en el primer o segundo intento
        if intentos == 3:
            try:
                from notificaciones.utils import crear_notificacion_por_tipo
                
                fecha_intento = timezone.now().strftime('%d/%m/%Y %H:%M')
                ip_address = self.request.META.get('REMOTE_ADDR', '')
                user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:200]
                
                # Crear notificación solo cuando se alcancen 3 intentos fallidos
                crear_notificacion_por_tipo(
                    codigo_tipo='GENERAL_LOGIN_FALLIDO',
                    titulo=f'⚠️ ALERTA: Múltiples intentos de login fallidos ({intentos}) - {user.username}',
                    mensaje=f'⚠️ ALERTA DE SEGURIDAD: Se han detectado {intentos} intentos de login fallidos consecutivos '
                           f'para la cuenta {user.username} en los últimos 15 minutos. '
                           f'Fecha del último intento: {fecha_intento}. '
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
    
    def form_valid(self, form):
        """
        Se ejecuta cuando el login es exitoso.
        
        Limpia el contador de intentos fallidos del usuario en cache
        para resetear el contador después de un login exitoso.
        
        Args:
            form: Formulario de login válido.
            
        Returns:
            HttpResponse: Respuesta del método padre con el login exitoso.
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
