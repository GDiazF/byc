from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    """
    Configuración de la aplicación notificaciones.
    
    Esta aplicación gestiona el sistema de notificaciones del sistema, incluyendo
    la creación automática de notificaciones mediante signals, el envío en tiempo
    real mediante Server-Sent Events, y el procesamiento periódico de vencimientos.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'
    
    def ready(self):
        """
        Se ejecuta cuando Django está listo.
        
        Registra los signals de la aplicación y inicia el scheduler de tareas
        periódicas en un thread separado para no bloquear la inicialización.
        El scheduler se inicia con un delay de 1 segundo para asegurar que
        Django esté completamente inicializado y las migraciones estén listas.
        """
        from . import signals
        
        # Iniciar scheduler después de que Django esté completamente listo
        # Usamos un enfoque lazy que retrasa la inicialización hasta después de que las migraciones estén listas
        import threading
        
        def iniciar_scheduler_diferido():
            """
            Inicia el scheduler después de un pequeño delay para asegurar que Django esté completamente listo.
            
            Espera 1 segundo antes de iniciar el scheduler para permitir que Django
            termine de inicializar y las migraciones estén disponibles.
            """
            import time
            time.sleep(1)  # Esperar 1 segundo para que Django termine de inicializar
            try:
                from . import scheduler
                # Solo iniciar una vez
                if not scheduler.scheduler.running:
                    scheduler.start()
            except ImportError:
                # Si django_apscheduler no está instalado, no hacer nada
                pass
            except Exception as e:
                # Si hay algún error, solo loguearlo pero no fallar
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"No se pudo iniciar el scheduler: {str(e)}")
        
        # Iniciar en un thread separado para no bloquear la inicialización
        thread = threading.Thread(target=iniciar_scheduler_diferido, daemon=True)
        thread.start()