# ============================================================================
# MANAGEMENT COMMAND PARA CREAR NOTIFICACIONES DE PRUEBA
# ============================================================================
# Este comando permite crear notificaciones de prueba para usuarios específicos,
# útil para testing y desarrollo.
# ============================================================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notificaciones.utils import crear_notificacion_por_tipo, crear_notificacion_para_usuario


class Command(BaseCommand):
    help = 'Crea notificaciones de prueba para el usuario actual o especificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario para el que crear notificaciones (opcional, usa el primer superuser si no se especifica)',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            default='RRHH_PERSONAL_ACTIVADO',
            help='Código del tipo de notificación a crear',
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=1,
            help='Cantidad de notificaciones a crear',
        )

    def handle(self, *args, **options):
        username = options.get('usuario')
        tipo_codigo = options.get('tipo')
        cantidad = options.get('cantidad')
        
        # Obtener usuario
        if username:
            try:
                usuario = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario "{username}" no encontrado')
                )
                return
        else:
            # Usar el primer superuser disponible
            usuario = User.objects.filter(is_superuser=True).first()
            if not usuario:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios superuser disponibles')
                )
                return
        
        self.stdout.write(
            self.style.SUCCESS(f'Creando {cantidad} notificación(es) de tipo "{tipo_codigo}" para usuario "{usuario.username}"')
        )
        
        # Crear notificaciones
        creadas = 0
        for i in range(cantidad):
            notif = crear_notificacion_para_usuario(
                usuario=usuario,
                codigo_tipo=tipo_codigo,
                titulo=f'Notificación de prueba #{i+1}',
                mensaje=f'Esta es una notificación de prueba número {i+1} del tipo {tipo_codigo}.',
                datos_adicionales={'prueba': True, 'numero': i+1}
            )
            if notif:
                creadas += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {creadas} notificación(es) creada(s) exitosamente')
        )

