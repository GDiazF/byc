"""
Configuración de URLs para la app rrhh_personal.

Este módulo define todas las rutas URL para la gestión de personal,
documentos, licencias, certificaciones, exámenes, ausentismos, etc.
"""
from django.urls import path
# Importar vistas individualmente para claridad
from .views import (
    PersonalListView,
    PersonalDesactivadoListView,
    PersonalCreateView,
    PersonalUpdateView,
    PersonalDeleteView,
    get_cargos,
    toggle_personal_status,
    toggle_personal_activo,
    personal_documentation,
    add_license,
    add_exam,
    delete_license,
    delete_exam,
    add_internal_license,
    edit_internal_license,
    delete_internal_license,
    upload_personal_document,
    edit_license,
    edit_certification,
    edit_exam,
    upload_carnet_document,
    delete_personal_document,
    documentation_view,
    save_certification,
    delete_certification,
    LicenciaMedicaPorPersonalCreateView,
    LicenciaMedicaPorPersonalUpdateView,
    delete_licencia_medica,
    listar_licencias_medicas_personal,
    gestionar_ausencias,
    listar_ausentismos_personal,
    crear_ausentismo,
    actualizar_ausentismo,
    eliminar_ausentismo,
    api_historial_personal,
    api_historial_documentos_personal,
    api_obtener_info_personal,
    descargar_documentacion_zip,
)

urlpatterns = [
    # ========================================================================
    # RUTAS PRINCIPALES DE PERSONAL
    # ========================================================================
    # Vista principal de la tabla de personal
    path('personal/', PersonalListView.as_view(), name='table_personal'),
    path('personal/', PersonalListView.as_view(), name='personal_list'),  # Alias para claridad
    # Vista de personal desactivado
    path('personal/desactivados/', PersonalDesactivadoListView.as_view(), name='personal_desactivado'),
    # Cambiar estado activo/inactivo del personal
    path('personal/toggle-activo/', toggle_personal_activo, name='toggle_personal_activo'),
    # Crear nuevo personal
    path('personal/create/', PersonalCreateView.as_view(), name='personal_create'),
    # Obtener cargos por departamento (AJAX)
    path('personal/get_cargos/', get_cargos, name='get_cargos'),
    # Editar personal existente
    path('personal/<int:pk>/update/', PersonalUpdateView.as_view(), name='personal_update'),
    # Eliminar personal
    path('personal/<int:pk>/delete/', PersonalDeleteView.as_view(), name='personal_delete'),
    # Cambiar estado del personal (alternativa)
    path('personal/<int:pk>/toggle-status/', toggle_personal_status, name='toggle_personal_status'),
    
    # ========================================================================
    # RUTAS DE DOCUMENTACIÓN Y DOCUMENTOS PERSONALES
    # ========================================================================
    # Vista de documentación completa del personal
    path('personal/<int:pk>/documentation/', documentation_view, name='documentation'),
    # Subir documento personal individual
    path('personal/<int:personal_id>/upload_document/', upload_personal_document, name='upload_personal_document'),
    # Subir documento de carnet (con validación especial)
    path('personal/<int:personal_id>/upload_carnet/', upload_carnet_document, name='upload_carnet_document'),
    # Eliminar documento personal
    path('personal/<int:personal_id>/delete_document/', delete_personal_document, name='delete_personal_document'),
    
    # ========================================================================
    # RUTAS DE LICENCIAS DE CONDUCIR
    # ========================================================================
    # Agregar licencia de conducir (estatal)
    path('personal/<int:personal_id>/add_license/', add_license, name='add_license'),
    # Editar licencia de conducir existente
    path('personal/<int:license_id>/edit_license/', edit_license, name='edit_license'),
    # Eliminar licencia de conducir
    path('personal/<int:license_id>/delete_license/', delete_license, name='delete_license'),
    
    # ========================================================================
    # RUTAS DE LICENCIAS INTERNAS
    # ========================================================================
    # Agregar licencia interna de conducir
    path('personal/<int:personal_id>/add_internal_license/', add_internal_license, name='add_internal_license'),
    # Editar licencia interna existente
    path('personal/<int:license_id>/edit_internal_license/', edit_internal_license, name='edit_internal_license'),
    # Eliminar licencia interna
    path('personal/<int:license_id>/delete_internal_license/', delete_internal_license, name='delete_internal_license'),
    
    # ========================================================================
    # RUTAS DE EXÁMENES
    # ========================================================================
    # Agregar examen médico
    path('personal/<int:personal_id>/add_exam/', add_exam, name='add_exam'),
    # Editar examen existente
    path('personal/<int:exam_id>/edit_exam/', edit_exam, name='edit_exam'),
    # Eliminar examen
    path('personal/<int:exam_id>/delete_exam/', delete_exam, name='delete_exam'),
    
    # ========================================================================
    # RUTAS DE CERTIFICACIONES
    # ========================================================================
    # Guardar certificación nueva
    path('personal/<int:pk>/save_certification/', save_certification, name='save_certification'),
    # Editar certificación existente
    path('personal/<int:cert_id>/edit_certification/', edit_certification, name='edit_certification'),
    # Eliminar certificación
    path('personal/<int:pk>/delete_certification/<int:certification_id>/', delete_certification, name='delete_certification'),
    
    # ========================================================================
    # RUTAS DE LICENCIAS MÉDICAS
    # ========================================================================
    # Agregar licencia médica
    path('personal/<int:personal_id>/add_licencia_medica/', LicenciaMedicaPorPersonalCreateView.as_view(), name='add_licencia_medica'),
    # Listar licencias médicas de un personal
    path('personal/<int:personal_id>/licencias_medicas/', listar_licencias_medicas_personal, name='listar_licencias_medicas_personal'),
    # Editar licencia médica existente
    path('licencia_medica/<int:pk>/edit/', LicenciaMedicaPorPersonalUpdateView.as_view(), name='edit_licencia_medica'),
    # Eliminar licencia médica
    path('licencia_medica/<int:licencia_id>/delete/', delete_licencia_medica, name='delete_licencia_medica'),
    
    # ========================================================================
    # RUTAS DE AUSENTISMOS
    # ========================================================================
    # Vista unificada de ausencias (licencias médicas y ausentismos)
    path('ausencias/', gestionar_ausencias, name='gestionar_ausencias'),
    # Listar ausentismos de un personal
    path('personal/<int:personal_id>/ausentismos/', listar_ausentismos_personal, name='listar_ausentismos_personal'),
    # Crear nuevo ausentismo
    path('personal/<int:personal_id>/ausentismos/create/', crear_ausentismo, name='crear_ausentismo'),
    # Actualizar ausentismo existente
    path('personal/<int:personal_id>/ausentismos/<int:ausentismo_id>/update/', actualizar_ausentismo, name='actualizar_ausentismo'),
    # Eliminar ausentismo
    path('personal/ausentismos/<int:ausentismo_id>/delete/', eliminar_ausentismo, name='eliminar_ausentismo'),
    
    # ========================================================================
    # RUTAS DE API (JSON)
    # ========================================================================
    # API para obtener historial de cambios del personal
    path('api/personal/<int:personal_id>/historial/', api_historial_personal, name='api_historial_personal'),
    # API para obtener historial de documentos del personal
    path('api/personal/<int:personal_id>/historial/documentos/', api_historial_documentos_personal, name='api_historial_documentos_personal'),
    # API para obtener información completa del personal (JSON)
    path('api/personal/<int:personal_id>/info/', api_obtener_info_personal, name='api_obtener_info_personal'),
    
    # ========================================================================
    # RUTAS DE DESCARGA
    # ========================================================================
    # Descargar toda la documentación del personal en un archivo ZIP
    path('personal/descargar-documentacion-zip/', descargar_documentacion_zip, name='descargar_documentacion_zip'),
]