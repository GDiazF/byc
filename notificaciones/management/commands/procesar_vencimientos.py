"""
Management command para procesar vencimientos de documentos manualmente.
"""

from django.core.management.base import BaseCommand
from notificaciones.tasks import procesar_vencimientos_documentos
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Procesa vencimientos de documentos y crea notificaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simular',
            action='store_true',
            help='Solo muestra qué documentos se procesarían sin crear notificaciones',
        )

    def handle(self, *args, **options):
        simular = options['simular']
        
        if simular:
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN: No se crearán notificaciones'))
            self.stdout.write('=' * 60)
        
        hoy = timezone.now().date()
        self.stdout.write(f'Fecha actual: {hoy.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Umbrales de notificación única: 45, 30, 20, 15, 10 días')
        self.stdout.write(f'Notificación diaria crítica: 9-1 días')
        self.stdout.write('=' * 60)
        
        if not simular:
            try:
                procesar_vencimientos_documentos()
                self.stdout.write(
                    self.style.SUCCESS('\n✓ Procesamiento de vencimientos completado')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ Error al procesar vencimientos: {str(e)}')
                )
        else:
            # Modo simulación: mostrar qué se procesaría
            self.mostrar_simulacion(hoy)
    
    def mostrar_simulacion(self, hoy):
        """Muestra qué documentos se procesarían sin crear notificaciones"""
        from rrhh_personal.models import (
            LicenciaPorPersonal, LicenciaMedicaPorPersonal,
            LicenciaInternaPorPersonal, Certificacion, Examen
        )
        from maquinarias.models import DocumentoMaquinaria
        
        umbrales_unicos = [45, 30, 20, 15, 10]
        encontrados = False
        
        # Personal - Licencias de conducir
        licencias_conducir = LicenciaPorPersonal.objects.filter(
            personal_id__activo=True
        ).select_related('personal_id')
        
        self.stdout.write('\n📋 LICENCIAS DE CONDUCIR:')
        for licencia in licencias_conducir:
            if licencia.fechaVencimiento:
                dias_restantes = (licencia.fechaVencimiento - hoy).days
                tipos_str = ", ".join([t.tipoLicencia for t in licencia.tipos.all()])
                if dias_restantes in umbrales_unicos:
                    encontrados = True
                    self.stdout.write(
                        f'  • {licencia.personal_id.nombre} {licencia.personal_id.apepat} - '
                        f'Licencia ({tipos_str}): {dias_restantes} días restantes [ÚNICA] '
                        f'(Vence: {licencia.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
                elif 1 <= dias_restantes <= 9:
                    encontrados = True
                    self.stdout.write(
                        f'  • {licencia.personal_id.nombre} {licencia.personal_id.apepat} - '
                        f'Licencia ({tipos_str}): {dias_restantes} días restantes [CRÍTICA DIARIA] '
                        f'(Vence: {licencia.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
        
        # Personal - Licencias internas
        licencias_internas = LicenciaInternaPorPersonal.objects.filter(
            personal_id__activo=True
        ).select_related('personal_id', 'tipoLicenciaInterna_id')
        
        self.stdout.write('\n📋 LICENCIAS INTERNAS:')
        for licencia in licencias_internas:
            if licencia.fechaVencimiento:
                dias_restantes = (licencia.fechaVencimiento - hoy).days
                tipo_nombre = licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else 'N/A'
                if dias_restantes in umbrales_unicos:
                    encontrados = True
                    self.stdout.write(
                        f'  • {licencia.personal_id.nombre} {licencia.personal_id.apepat} - '
                        f'Licencia Interna ({tipo_nombre}): {dias_restantes} días restantes [ÚNICA] '
                        f'(Vence: {licencia.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
                elif 1 <= dias_restantes <= 9:
                    encontrados = True
                    self.stdout.write(
                        f'  • {licencia.personal_id.nombre} {licencia.personal_id.apepat} - '
                        f'Licencia Interna ({tipo_nombre}): {dias_restantes} días restantes [CRÍTICA DIARIA] '
                        f'(Vence: {licencia.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
        
        # Personal - Certificaciones
        certificaciones = Certificacion.objects.filter(
            personal_id__activo=True
        ).select_related('personal_id', 'tipoCertificacion_id')
        
        self.stdout.write('\n📋 CERTIFICACIONES:')
        for cert in certificaciones:
            if cert.fechaVencimiento:
                dias_restantes = (cert.fechaVencimiento - hoy).days
                tipo_nombre = cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else 'N/A'
                if dias_restantes in umbrales_unicos:
                    encontrados = True
                    self.stdout.write(
                        f'  • {cert.personal_id.nombre} {cert.personal_id.apepat} - '
                        f'Certificación ({tipo_nombre}): {dias_restantes} días restantes [ÚNICA] '
                        f'(Vence: {cert.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
                elif 1 <= dias_restantes <= 9:
                    encontrados = True
                    self.stdout.write(
                        f'  • {cert.personal_id.nombre} {cert.personal_id.apepat} - '
                        f'Certificación ({tipo_nombre}): {dias_restantes} días restantes [CRÍTICA DIARIA] '
                        f'(Vence: {cert.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
        
        # Personal - Exámenes
        examenes = Examen.objects.filter(
            personal_id__activo=True
        ).select_related('personal_id', 'tipoEx_id')
        
        self.stdout.write('\n📋 EXÁMENES:')
        for examen in examenes:
            if examen.fechaVencimiento:
                dias_restantes = (examen.fechaVencimiento - hoy).days
                tipo_nombre = examen.tipoEx_id.tipoExamen if examen.tipoEx_id else 'N/A'
                if dias_restantes in umbrales_unicos:
                    encontrados = True
                    self.stdout.write(
                        f'  • {examen.personal_id.nombre} {examen.personal_id.apepat} - '
                        f'Examen ({tipo_nombre}): {dias_restantes} días restantes [ÚNICA] '
                        f'(Vence: {examen.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
                elif 1 <= dias_restantes <= 9:
                    encontrados = True
                    self.stdout.write(
                        f'  • {examen.personal_id.nombre} {examen.personal_id.apepat} - '
                        f'Examen ({tipo_nombre}): {dias_restantes} días restantes [CRÍTICA DIARIA] '
                        f'(Vence: {examen.fechaVencimiento.strftime("%d/%m/%Y")})'
                    )
        
        # Equipos
        documentos = DocumentoMaquinaria.objects.filter(
            equipo_id__activo=True
        ).select_related('equipo_id', 'tipo_documento_id')
        
        self.stdout.write('\n📋 DOCUMENTOS DE EQUIPOS:')
        for documento in documentos:
            if documento.fecha_vencimiento:
                dias_restantes = (documento.fecha_vencimiento - hoy).days
                tipo_nombre = documento.tipo_documento_id.nombre if documento.tipo_documento_id else 'Documento'
                if dias_restantes in umbrales_unicos:
                    encontrados = True
                    self.stdout.write(
                        f'  • {documento.equipo_id.nombreEquipo} ({documento.equipo_id.codigoInterno}) - '
                        f'{tipo_nombre}: {dias_restantes} días restantes [ÚNICA] '
                        f'(Vence: {documento.fecha_vencimiento.strftime("%d/%m/%Y")})'
                    )
                elif 1 <= dias_restantes <= 9:
                    encontrados = True
                    self.stdout.write(
                        f'  • {documento.equipo_id.nombreEquipo} ({documento.equipo_id.codigoInterno}) - '
                        f'{tipo_nombre}: {dias_restantes} días restantes [CRÍTICA DIARIA] '
                        f'(Vence: {documento.fecha_vencimiento.strftime("%d/%m/%Y")})'
                    )
        
        if not encontrados:
            self.stdout.write(self.style.WARNING('\n⚠ No se encontraron documentos próximos a vencer en los umbrales configurados (45, 30, 20, 15, 10 días o 9-1 días crítico)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Se procesarían {sum(1 for _ in [])} documentos'))
        
        # Mostrar documentos que vencen en otros períodos (para referencia)
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN POR RANGO DE DÍAS:')
        
        rangos = {
            '45-31 días': (31, 45),
            '30-21 días': (21, 30),
            '20-16 días': (16, 20),
            '15-11 días': (11, 15),
            '10 días': (10, 10),
            '9-1 días (crítico)': (1, 9),
            'Vencidos': (-999, 0)
        }
        
        for nombre_rango, (min_dias, max_dias) in rangos.items():
            count = 0
            # Contar documentos de personal
            for licencia in licencias_conducir:
                if licencia.fechaVencimiento:
                    dias = (licencia.fechaVencimiento - hoy).days
                    if min_dias <= dias <= max_dias:
                        count += 1
            for licencia in licencias_internas:
                if licencia.fechaVencimiento:
                    dias = (licencia.fechaVencimiento - hoy).days
                    if min_dias <= dias <= max_dias:
                        count += 1
            for cert in certificaciones:
                if cert.fechaVencimiento:
                    dias = (cert.fechaVencimiento - hoy).days
                    if min_dias <= dias <= max_dias:
                        count += 1
            for examen in examenes:
                if examen.fechaVencimiento:
                    dias = (examen.fechaVencimiento - hoy).days
                    if min_dias <= dias <= max_dias:
                        count += 1
            # Contar documentos de equipos
            for documento in documentos:
                if documento.fecha_vencimiento:
                    dias = (documento.fecha_vencimiento - hoy).days
                    if min_dias <= dias <= max_dias:
                        count += 1
            
            if count > 0:
                self.stdout.write(f'  • {nombre_rango}: {count} documento(s)')

