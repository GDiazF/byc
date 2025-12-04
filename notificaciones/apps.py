from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'
    
    def ready(self):
        """
        Se ejecuta cuando Django está listo.
        Aquí registramos signals. El scheduler se inicia después de que Django esté completamente inicializado.
        """
        # Importar signals para que se registren
        from . import signals
        
        # Iniciar scheduler después de que Django esté completamente listo
        # Usamos un enfoque lazy que retrasa la inicialización hasta después de que las migraciones estén listas
        import threading
        
        def iniciar_scheduler_diferido():
            """Inicia el scheduler después de un pequeño delay para asegurar que Django esté completamente listo"""
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