"""
Configuración del Django Admin para los modelos de RRHH Personal.

Este módulo personaliza la interfaz de administración de Django para todos los modelos
relacionados con personal, licencias, certificaciones, exámenes, ausentismos, etc.
Incluye personalizaciones de visualización, filtros, búsqueda y métodos helper.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Personal, Sexo, EstadoCivil, 
    DeptoEmpresa, Cargo, InfoLaboral,
    TipoAusentismo, Ausentismo, 
    TipoLicenciaMedica, LicenciaMedicaPorPersonal,
    Proveedor, TipoClasificacion, ClasificacionProveedor,
    TipoExamen, ResultadoExamen, Examen,
    TipoCertificacion, Certificacion,
    TipoLicencia, LicenciaPorPersonal,
    TipoLicenciaInterna, LicenciaInternaPorPersonal
)

# ============================================================================
# ADMIN PARA MODELOS DE PERSONAL
# ============================================================================

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Personal.
    
    Personaliza la visualización de la lista de personal con campos calculados,
    filtros, búsqueda y organización de campos en fieldsets.
    """
    list_display = [
        'rut_completo', 'nombre_completo', 'correo', 'sexo_id', 
        'fechanac', 'region_id', 'activo', 'documentos_count'
    ]
    list_filter = ['activo', 'sexo_id', 'estcivil_id', 'region_id', 'fechanac']
    search_fields = ['nombre', 'apepat', 'apemat', 'rut', 'correo']
    ordering = ['apepat', 'apemat', 'nombre']
    readonly_fields = ['personal_id']  # El ID es auto-generado, no debe editarse
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('personal_id', 'rut', 'dvrut', 'nombre', 'apepat', 'apemat', 
                      'fechanac', 'sexo_id', 'estcivil_id', 'activo')
        }),
        ('Contacto y Ubicación', {
            'fields': ('correo', 'direccion', 'region_id', 'comuna_id')
        }),
        ('Documentos', {
            'fields': (
                'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                'foto_carnet', 'certificado_afp', 'certificado_salud',
                'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                'fotocopia_finiquito', 'comprobante_banco'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def rut_completo(self, obj):
        """
        Muestra el RUT completo con dígito verificador.
        
        Args:
            obj: Instancia del modelo Personal
            
        Returns:
            str: RUT en formato "12345678-9"
        """
        return f"{obj.rut}-{obj.dvrut}"
    rut_completo.short_description = "RUT"
    rut_completo.admin_order_field = 'rut'
    
    def nombre_completo(self, obj):
        """
        Muestra el nombre completo del personal.
        
        Args:
            obj: Instancia del modelo Personal
            
        Returns:
            str: Nombre completo "Nombre ApellidoPaterno ApellidoMaterno"
        """
        return f"{obj.nombre} {obj.apepat} {obj.apemat}"
    nombre_completo.short_description = "Nombre Completo"
    nombre_completo.admin_order_field = 'nombre'
    
    def documentos_count(self, obj):
        """
        Cuenta cuántos documentos tiene cargados el personal y muestra un indicador visual.
        
        El color cambia según la cantidad:
        - Verde (#27ae60): 8 o más documentos (completo)
        - Amarillo (#f39c12): 5-7 documentos (parcial)
        - Rojo (#e74c3c): Menos de 5 documentos (incompleto)
        
        Args:
            obj: Instancia del modelo Personal
            
        Returns:
            str: HTML con el conteo de documentos y color indicador
        """
        # Lista de todos los campos de documentos
        docs = [
            obj.curriculum, obj.certificado_antecedentes, obj.hoja_vida_conductor,
            obj.foto_carnet, obj.certificado_afp, obj.certificado_salud,
            obj.certificado_estudios, obj.certificado_residencia, obj.fotocopia_carnet,
            obj.fotocopia_finiquito, obj.comprobante_banco
        ]
        # Contar cuántos documentos tienen archivo cargado
        count = sum(1 for doc in docs if doc)
        total = len(docs)
        # Determinar color según la cantidad de documentos
        color = '#27ae60' if count >= 8 else '#f39c12' if count >= 5 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color, count, total
        )
    documentos_count.short_description = "Documentos"

@admin.register(Sexo)
class SexoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Sexo.
    """
    list_display = ['sexo_id', 'sexo']
    search_fields = ['sexo']
    ordering = ['sexo']

@admin.register(EstadoCivil)
class EstadoCivilAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoCivil.
    """
    list_display = ['estcivil_id', 'estadocivil']
    search_fields = ['estadocivil']
    ordering = ['estadocivil']

# ============================================================================
# ADMIN PARA INFORMACIÓN LABORAL
# ============================================================================

@admin.register(DeptoEmpresa)
class DeptoEmpresaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo DeptoEmpresa.
    """
    list_display = ['depto_id', 'depto']
    search_fields = ['depto']
    ordering = ['depto']

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Cargo.
    Permite filtrar y buscar cargos por departamento.
    """
    list_display = ['cargo_id', 'cargo', 'depto_id']
    list_filter = ['depto_id']
    search_fields = ['cargo', 'depto_id__depto']
    ordering = ['depto_id', 'cargo']

@admin.register(InfoLaboral)
class InfoLaboralAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo InfoLaboral.
    
    Optimiza las consultas usando select_related para evitar consultas N+1
    al mostrar información laboral con sus relaciones.
    """
    list_display = ['personal_id', 'empresa_id', 'depto_id', 'cargo_id', 'fechacontrata']
    list_filter = ['empresa_id', 'depto_id', 'cargo_id', 'fechacontrata']
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'empresa_id__razon_social', 'cargo_id__cargo'
    ]
    date_hierarchy = 'fechacontrata'  # Navegación por fecha de contratación
    ordering = ['personal_id', 'fechacontrata']
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related para cargar relaciones en una sola consulta.
        
        Args:
            request: Objeto HttpRequest
            
        Returns:
            QuerySet: QuerySet optimizado con select_related
        """
        return super().get_queryset(request).select_related(
            'personal_id', 'empresa_id', 'depto_id', 'cargo_id'
        )

# ============================================================================
# ADMIN PARA AUSENTISMO
# ============================================================================

@admin.register(TipoAusentismo)
class TipoAusentismoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo TipoAusentismo.
    """
    list_display = ['tipoausen_id', 'tipo']
    search_fields = ['tipo']
    ordering = ['tipo']

@admin.register(Ausentismo)
class AusentismoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Ausentismo.
    
    Muestra información visual con badges de estado y días,
    y optimiza las consultas con select_related.
    """
    list_display = [
        'personal_id', 'tipoausen_id', 'fechaini', 'fechafin', 
        'dias_badge', 'estado_badge', 'observacion_short'
    ]
    list_filter = ['tipoausen_id', 'fechaini', 'fechafin']
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat', 
        'observacion'
    ]
    date_hierarchy = 'fechaini'  # Navegación por fecha de inicio
    ordering = ['-fechaini']  # Más recientes primero
    
    def dias_badge(self, obj):
        """
        Muestra los días de ausentismo con un badge azul.
        
        Args:
            obj: Instancia del modelo Ausentismo
            
        Returns:
            str: HTML con badge mostrando los días
        """
        dias = obj.dias_totales
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px;">{} días</span>',
            dias
        )
    dias_badge.short_description = "Días"
    
    def estado_badge(self, obj):
        """
        Muestra el estado del ausentismo (Activo/Vencido) con badge de color.
        
        Args:
            obj: Instancia del modelo Ausentismo
            
        Returns:
            str: HTML con badge verde (activo) o gris (vencido)
        """
        if obj.esta_activo:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 3px 8px; border-radius: 3px;">Vencido</span>'
        )
    estado_badge.short_description = "Estado"
    
    def observacion_short(self, obj):
        """
        Muestra una versión truncada de la observación (máximo 50 caracteres).
        
        Args:
            obj: Instancia del modelo Ausentismo
            
        Returns:
            str: Observación truncada o "-" si no hay observación
        """
        if obj.observacion:
            return obj.observacion[:50] + "..." if len(obj.observacion) > 50 else obj.observacion
        return "-"
    observacion_short.short_description = "Observación"
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related.
        
        Args:
            request: Objeto HttpRequest
            
        Returns:
            QuerySet: QuerySet optimizado
        """
        return super().get_queryset(request).select_related('personal_id', 'tipoausen_id')

# ============================================================================
# ADMIN PARA LICENCIAS MÉDICAS
# ============================================================================

@admin.register(TipoLicenciaMedica)
class TipoLicenciaMedicaAdmin(admin.ModelAdmin):
    list_display = ['tipoLicenciaMedica_id', 'tipoLicenciaMedica']
    search_fields = ['tipoLicenciaMedica']
    ordering = ['tipoLicenciaMedica']

@admin.register(LicenciaMedicaPorPersonal)
class LicenciaMedicaPorPersonalAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo LicenciaMedicaPorPersonal.
    
    La fecha de fin es calculada automáticamente, por lo que es de solo lectura.
    """
    list_display = [
        'personal_id', 'tipoLicenciaMedica_id', 
        'fechaEmision', 'dias_licencia', 'fecha_fin_licencia', 
        'estado_badge', 'observacion_short'
    ]
    list_filter = ['tipoLicenciaMedica_id', 'fechaEmision', 'fecha_fin_licencia']
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'observacion'
    ]
    date_hierarchy = 'fechaEmision'
    ordering = ['-fechaEmision']  # Más recientes primero
    readonly_fields = ['fecha_fin_licencia']  # Calculada automáticamente
    
    fieldsets = (
        ('Información General', {
            'fields': ('personal_id', 'tipoLicenciaMedica_id')
        }),
        ('Fechas', {
            'fields': ('fechaEmision', 'dias_licencia', 'fecha_fin_licencia')
        }),
        ('Observaciones', {
            'fields': ('observacion',)
        }),
    )
    
    def estado_badge(self, obj):
        """
        Muestra el estado de la licencia médica (Activa/Vencida) con badge de color.
        
        Args:
            obj: Instancia del modelo LicenciaMedicaPorPersonal
            
        Returns:
            str: HTML con badge verde (activa) o gris (vencida)
        """
        if obj.esta_activa:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 3px 8px; border-radius: 3px;">Vencida</span>'
        )
    estado_badge.short_description = "Estado"
    
    def observacion_short(self, obj):
        """
        Muestra una versión truncada de la observación (máximo 50 caracteres).
        
        Args:
            obj: Instancia del modelo LicenciaMedicaPorPersonal
            
        Returns:
            str: Observación truncada o "-" si no hay observación
        """
        if obj.observacion:
            return obj.observacion[:50] + "..." if len(obj.observacion) > 50 else obj.observacion
        return "-"
    observacion_short.short_description = "Observación"
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related.
        
        Args:
            request: Objeto HttpRequest
            
        Returns:
            QuerySet: QuerySet optimizado
        """
        return super().get_queryset(request).select_related('personal_id', 'tipoLicenciaMedica_id')

# ============================================================================
# ADMIN PARA PROVEEDORES
# ============================================================================

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = [
        'rut_completo_prov', 'razonSocial', 'nombreFant', 'giro', 
        'region_id', 'comuna_id'
    ]
    list_filter = ['region_id', 'comuna_id']
    search_fields = ['razonSocial', 'nombreFant', 'rut', 'giro']
    ordering = ['razonSocial']
    
    fieldsets = (
        ('Información del Proveedor', {
            'fields': ('rut', 'dvRut', 'razonSocial', 'nombreFant', 'giro')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'region_id', 'comuna_id')
        }),
    )
    
    def rut_completo_prov(self, obj):
        return f"{obj.rut}-{obj.dvRut}"
    rut_completo_prov.short_description = "RUT"
    rut_completo_prov.admin_order_field = 'rut'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('region_id', 'comuna_id')

@admin.register(TipoClasificacion)
class TipoClasificacionAdmin(admin.ModelAdmin):
    list_display = ['tipoClasi_id', 'tipo']
    search_fields = ['tipo']
    ordering = ['tipo']

@admin.register(ClasificacionProveedor)
class ClasificacionProveedorAdmin(admin.ModelAdmin):
    list_display = ['clasifProv_id', 'proveedor_id', 'tipoClasi_id']
    list_filter = ['tipoClasi_id']
    search_fields = ['proveedor_id__razonSocial', 'tipoClasi_id__tipo']
    ordering = ['proveedor_id']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proveedor_id', 'tipoClasi_id')

# ============================================================================
# ADMIN PARA EXÁMENES
# ============================================================================

@admin.register(TipoExamen)
class TipoExamenAdmin(admin.ModelAdmin):
    list_display = ['tipoEx_id', 'tipoExamen']
    search_fields = ['tipoExamen']
    ordering = ['tipoExamen']

@admin.register(ResultadoExamen)
class ResultadoExamenAdmin(admin.ModelAdmin):
    list_display = ['resultadoEx_id', 'resultado']
    search_fields = ['resultado']
    ordering = ['resultado']

@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Examen.
    
    Muestra estado de vigencia basado en la fecha de vencimiento y si tiene documento asociado.
    """
    list_display = [
        'personal_id', 'tipoEx_id', 'resultadoEx_id', 'proveedor_id',
        'fechaEmision', 'fechaVencimiento', 'estado_vigencia', 
        'tiene_documento', 'observacion_short'
    ]
    list_filter = [
        'tipoEx_id', 'resultadoEx_id', 'proveedor_id', 
        'fechaEmision', 'fechaVencimiento'
    ]
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'tipoEx_id__tipoExamen', 'proveedor_id__razonSocial', 'observacion'
    ]
    date_hierarchy = 'fechaEmision'
    ordering = ['-fechaEmision']
    
    fieldsets = (
        ('Información del Examen', {
            'fields': ('personal_id', 'tipoEx_id', 'resultadoEx_id', 'proveedor_id')
        }),
        ('Fechas', {
            'fields': ('fechaEmision', 'fechaVencimiento')
        }),
        ('Documentación', {
            'fields': ('rutaDoc', 'observacion')
        }),
    )
    
    def estado_vigencia(self, obj):
        """
        Calcula y muestra el estado de vigencia del examen basado en la fecha de vencimiento.
        
        Estados:
        - VENCIDO (rojo): Fecha de vencimiento pasada
        - POR VENCER (amarillo): Vence en 30 días o menos
        - VIGENTE (verde): Vence en más de 30 días
        
        Args:
            obj: Instancia del modelo Examen
            
        Returns:
            str: HTML con badge del estado de vigencia
        """
        from datetime import date
        if obj.fechaVencimiento:
            dias_restantes = (obj.fechaVencimiento - date.today()).days
            if dias_restantes < 0:
                return format_html(
                    '<span style="background-color: #e74c3c; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VENCIDO</span>'
                )
            elif dias_restantes <= 30:
                return format_html(
                    '<span style="background-color: #f39c12; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">POR VENCER ({} días)</span>',
                    dias_restantes
                )
            else:
                return format_html(
                    '<span style="background-color: #27ae60; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VIGENTE</span>'
                )
        return "-"
    estado_vigencia.short_description = "Estado"
    
    def tiene_documento(self, obj):
        """
        Indica si el examen tiene documento asociado.
        
        Args:
            obj: Instancia del modelo Examen
            
        Returns:
            str: HTML con indicador verde (sí) o rojo (no)
        """
        if obj.rutaDoc:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: #e74c3c;">✗ No</span>'
        )
    tiene_documento.short_description = "Documento"
    
    def observacion_short(self, obj):
        if obj.observacion:
            return obj.observacion[:50] + "..." if len(obj.observacion) > 50 else obj.observacion
        return "-"
    observacion_short.short_description = "Observación"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'personal_id', 'tipoEx_id', 'resultadoEx_id', 'proveedor_id'
        )

# ============================================================================
# ADMIN PARA CERTIFICACIONES
# ============================================================================

@admin.register(TipoCertificacion)
class TipoCertificacionAdmin(admin.ModelAdmin):
    list_display = ['tipoCertificacion_id', 'tipoCertificacion']
    search_fields = ['tipoCertificacion']
    ordering = ['tipoCertificacion']

@admin.register(Certificacion)
class CertificacionAdmin(admin.ModelAdmin):
    list_display = [
        'personal_id', 'tipoCertificacion_id', 'proveedor_id',
        'fechaEmision', 'fechaVencimiento', 'estado_vigencia',
        'tiene_documento', 'observacion_short'
    ]
    list_filter = [
        'tipoCertificacion_id', 'proveedor_id', 
        'fechaEmision', 'fechaVencimiento'
    ]
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'tipoCertificacion_id__tipoCertificacion', 'proveedor_id__razonSocial', 
        'observacion'
    ]
    date_hierarchy = 'fechaEmision'
    ordering = ['-fechaEmision']
    
    fieldsets = (
        ('Información de la Certificación', {
            'fields': ('personal_id', 'tipoCertificacion_id', 'proveedor_id')
        }),
        ('Fechas', {
            'fields': ('fechaEmision', 'fechaVencimiento')
        }),
        ('Documentación', {
            'fields': ('rutaDoc', 'observacion')
        }),
    )
    
    def estado_vigencia(self, obj):
        from datetime import date
        if obj.fechaVencimiento:
            dias_restantes = (obj.fechaVencimiento - date.today()).days
            if dias_restantes < 0:
                return format_html(
                    '<span style="background-color: #e74c3c; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VENCIDA</span>'
                )
            elif dias_restantes <= 30:
                return format_html(
                    '<span style="background-color: #f39c12; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">POR VENCER ({} días)</span>',
                    dias_restantes
                )
            else:
                return format_html(
                    '<span style="background-color: #27ae60; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VIGENTE</span>'
                )
        return "-"
    estado_vigencia.short_description = "Estado"
    
    def tiene_documento(self, obj):
        if obj.rutaDoc:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: #e74c3c;">✗ No</span>'
        )
    tiene_documento.short_description = "Documento"
    
    def observacion_short(self, obj):
        if obj.observacion:
            return obj.observacion[:50] + "..." if len(obj.observacion) > 50 else obj.observacion
        return "-"
    observacion_short.short_description = "Observación"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'personal_id', 'tipoCertificacion_id', 'proveedor_id'
        )

# ============================================================================
# ADMIN PARA LICENCIAS DE CONDUCIR
# ============================================================================

@admin.register(TipoLicencia)
class TipoLicenciaAdmin(admin.ModelAdmin):
    list_display = ['tipoLicencia_id', 'tipoLicencia']
    search_fields = ['tipoLicencia']
    ordering = ['tipoLicencia']

@admin.register(LicenciaPorPersonal)
class LicenciaPorPersonalAdmin(admin.ModelAdmin):
    list_display = [
        'personal_id', 'tipos_display', 'fechaEmision', 'fechaVencimiento',
        'estado_vigencia', 'tiene_documento', 'observacion_short'
    ]
    list_filter = ['fechaEmision', 'fechaVencimiento', 'tipos']
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'observacion'
    ]
    date_hierarchy = 'fechaEmision'
    ordering = ['-fechaEmision']
    filter_horizontal = ['tipos']
    
    fieldsets = (
        ('Información de la Licencia', {
            'fields': ('personal_id', 'tipos')
        }),
        ('Fechas', {
            'fields': ('fechaEmision', 'fechaVencimiento')
        }),
        ('Documentación', {
            'fields': ('rutaDoc', 'observacion')
        }),
    )
    
    def tipos_display(self, obj):
        tipos = obj.tipos.all()
        if tipos:
            return ", ".join([t.tipoLicencia for t in tipos])
        return "Sin tipo"
    tipos_display.short_description = "Tipos de Licencia"
    
    def estado_vigencia(self, obj):
        from datetime import date
        if obj.fechaVencimiento:
            dias_restantes = (obj.fechaVencimiento - date.today()).days
            if dias_restantes < 0:
                return format_html(
                    '<span style="background-color: #e74c3c; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VENCIDA</span>'
                )
            elif dias_restantes <= 30:
                return format_html(
                    '<span style="background-color: #f39c12; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">POR VENCER ({} días)</span>',
                    dias_restantes
                )
            else:
                return format_html(
                    '<span style="background-color: #27ae60; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-weight: bold;">VIGENTE</span>'
                )
        return "-"
    estado_vigencia.short_description = "Estado"
    
    def tiene_documento(self, obj):
        if obj.rutaDoc:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: #e74c3c;">✗ No</span>'
        )
    tiene_documento.short_description = "Documento"
    
    def observacion_short(self, obj):
        if obj.observacion:
            return obj.observacion[:50] + "..." if len(obj.observacion) > 50 else obj.observacion
        return "-"
    observacion_short.short_description = "Observación"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('personal_id').prefetch_related('tipos')


# ============================================================================
# ADMIN PARA LICENCIAS INTERNAS DE CONDUCIR
# ============================================================================

@admin.register(TipoLicenciaInterna)
class TipoLicenciaInternaAdmin(admin.ModelAdmin):
    list_display = ['tipoLicenciaInterna', 'descripcion_short']
    search_fields = ['tipoLicenciaInterna', 'descripcion']
    ordering = ['tipoLicenciaInterna']
    
    fieldsets = (
        (None, {
            'fields': ('tipoLicenciaInterna', 'descripcion')
        }),
    )
    
    def descripcion_short(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_short.short_description = "Descripción"


@admin.register(LicenciaInternaPorPersonal)
class LicenciaInternaPorPersonalAdmin(admin.ModelAdmin):
    list_display = [
        'personal_nombre', 'tipoLicenciaInterna_id', 'numero_licencia', 
        'fechaEmision', 'fechaVencimiento', 'empresa_emisora', 
        'estado_badge', 'documento_badge'
    ]
    list_filter = ['tipoLicenciaInterna_id', 'fechaEmision', 'fechaVencimiento', 'empresa_emisora']
    search_fields = [
        'personal_id__nombre', 'personal_id__apepat', 'personal_id__apemat',
        'personal_id__rut', 'numero_licencia', 'empresa_emisora',
        'tipoLicenciaInterna_id__tipoLicenciaInterna'
    ]
    ordering = ['-fechaEmision']
    
    fieldsets = (
        ('Información del Personal', {
            'fields': ('personal_id',)
        }),
        ('Detalles de la Licencia Interna', {
            'fields': ('tipoLicenciaInterna_id', 'numero_licencia', 'empresa_emisora')
        }),
        ('Fechas', {
            'fields': ('fechaEmision', 'fechaVencimiento')
        }),
        ('Documentación', {
            'fields': ('rutaDoc', 'observacion')
        }),
    )
    
    def personal_nombre(self, obj):
        return f"{obj.personal_id.nombre} {obj.personal_id.apepat} {obj.personal_id.apemat}"
    personal_nombre.short_description = "Personal"
    personal_nombre.admin_order_field = 'personal_id__apepat'
    
    def estado_badge(self, obj):
        if obj.esta_activa:
            color = '#28a745'
            texto = 'ACTIVA'
            icono = '✓'
        else:
            color = '#6c757d'
            texto = 'INACTIVA'
            icono = '✗'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 0.75rem;">{} {}</span>',
            color, icono, texto
        )
    estado_badge.short_description = "Estado"
    
    def documento_badge(self, obj):
        if obj.rutaDoc:
            return format_html(
                '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold; font-size: 0.75rem;">📄 Sí</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 0.75rem;">✗ No</span>'
        )
    documento_badge.short_description = "Documento"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('personal_id', 'tipoLicenciaInterna_id')


# ============================================================================
# PERSONALIZACIÓN DEL SITE ADMIN
# ============================================================================

admin.site.site_header = "Administración de Recursos Humanos"
admin.site.site_title = "RRHH Admin"
admin.site.index_title = "Panel de Control de Recursos Humanos"
