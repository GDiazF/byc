# ============================================================================
# CONFIGURACIÓN DE APSCHEDULER PARA TAREAS PERIÓDICAS
# ============================================================================
# Este módulo configura APScheduler para ejecutar tareas periódicas relacionadas
# con notificaciones, como el procesamiento de vencimientos de documentos.
# ============================================================================

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution, DjangoJob
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Scheduler global
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

def procesar_vencimientos():
    """
    Tarea periódica que procesa vencimientos de documentos y crea notificaciones.
    
    Se ejecuta todos los días a las 2:00 AM mediante APScheduler.
    Llama a la función procesar_vencimientos_documentos() del módulo tasks.
    """
    from .tasks import procesar_vencimientos_documentos
    
    try:
        procesar_vencimientos_documentos()
        logger.info("Tarea de vencimientos ejecutada correctamente")
    except Exception as e:
        logger.error(f"Error al ejecutar tarea de vencimientos: {str(e)}")


def start():
    """
    Inicia el scheduler y programa las tareas periódicas.
    
    Configura APScheduler con DjangoJobStore para persistir trabajos en la BD,
    programa la tarea de procesamiento de vencimientos y registra eventos
    para logging. Verifica que las tablas de django_apscheduler existan antes
    de iniciar.
    
    Raises:
        Exception: Si hay un error al iniciar el scheduler (se loguea pero no se propaga)
    """
    if scheduler.running:
        logger.warning("Scheduler ya está corriendo")
        return
    
    # Verificar que las tablas de django_apscheduler existan antes de iniciar
    # Usamos un try/except simple para evitar acceder a la BD durante inicialización
    try:
        from django.db.utils import OperationalError
        
        # Intentar acceder a DjangoJob para verificar que la tabla existe
        # Esto solo se ejecuta cuando start() es llamado explícitamente, no durante imports
        try:
            DjangoJob.objects.count()
        except OperationalError:
            logger.warning("Tablas de django_apscheduler no existen aún. Ejecuta 'python manage.py migrate' primero.")
            return
        except Exception as e:
            # Si hay otro error (ej: tabla no existe), también retornar
            logger.warning(f"No se pudo verificar las tablas de django_apscheduler: {str(e)}")
            return
    except Exception as e:
        logger.warning(f"Error al verificar tablas de django_apscheduler: {str(e)}")
        return
    
    try:
        # Usar DjangoJobStore para persistir trabajos en la base de datos
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Programar tarea de vencimientos: todos los días a las 2:00 AM
        scheduler.add_job(
            procesar_vencimientos,
            trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM todos los días
            id='procesar_vencimientos',
            name='Procesar vencimientos de documentos',
            replace_existing=True,
        )
        
        # Registrar eventos para logging
        register_events(scheduler)
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("Scheduler iniciado correctamente")
        
        # Limpiar ejecuciones antiguas (opcional, mantener solo las últimas 100)
        try:
            DjangoJobExecution.objects.delete_old_job_executions(max_age=604800)  # 7 días
        except Exception as e:
            logger.warning(f"Error al limpiar ejecuciones antiguas: {str(e)}")
    except Exception as e:
        logger.error(f"Error al iniciar scheduler: {str(e)}")

