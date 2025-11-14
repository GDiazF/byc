from django.core.management.base import BaseCommand
from maquinarias.models import TipoMantenimiento, EstadoOT, EstadoEquipo


class Command(BaseCommand):
    help = 'Pobla los datos iniciales para Tipos de Mantenimiento, Estados OT y Estados Equipo'

    def handle(self, *args, **options):
        # Crear Tipos de Mantenimiento
        tipos_mantenimiento = [
            {'nombre': 'Preventivo', 'descripcion': 'Mantenimiento preventivo programado'},
            {'nombre': 'Correctivo', 'descripcion': 'Mantenimiento correctivo por falla'},
        ]
        
        for tipo_data in tipos_mantenimiento:
            tipo, created = TipoMantenimiento.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado Tipo de Mantenimiento: {tipo.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'Tipo de Mantenimiento ya existe: {tipo.nombre}'))
        
        # Crear Estados OT
        estados_ot = [
            {'nombre': 'Pendiente', 'color': 'secondary', 'orden': 1},
            {'nombre': 'En Proceso', 'color': 'primary', 'orden': 2},
            {'nombre': 'Terminada', 'color': 'success', 'orden': 3},
            {'nombre': 'Cancelada', 'color': 'danger', 'orden': 4},
        ]
        
        for estado_data in estados_ot:
            estado, created = EstadoOT.objects.get_or_create(
                nombre=estado_data['nombre'],
                defaults=estado_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado Estado OT: {estado.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'Estado OT ya existe: {estado.nombre}'))
        
        # Crear Estados Equipo
        estados_equipo = [
            {'nombre': 'Disponible', 'color': 'success', 'orden': 1},
            {'nombre': 'Shutdown', 'color': 'danger', 'orden': 2},
            {'nombre': 'En Reparación', 'color': 'warning', 'orden': 3},
            {'nombre': 'En Reparación Disponible', 'color': 'info', 'orden': 4},
        ]
        
        for estado_data in estados_equipo:
            estado, created = EstadoEquipo.objects.get_or_create(
                nombre=estado_data['nombre'],
                defaults=estado_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado Estado Equipo: {estado.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'Estado Equipo ya existe: {estado.nombre}'))
        
        self.stdout.write(self.style.SUCCESS('\nDatos iniciales poblados exitosamente'))

