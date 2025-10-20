from django.urls import path
# Importar vistas individualmente para claridad
from .views import (
    PersonalListView,
    PersonalCreateView,
    PersonalDocumentCreateView,
    PersonalLaborCreateView,
    PersonalUpdateView,
    PersonalDeleteView,
    get_cargos,
    toggle_personal_status,
    personal_documentation,
    add_license,
    add_exam,
    delete_license,
    delete_exam,
    add_internal_license,
    delete_internal_license,
    upload_personal_document,
    upload_carnet_document,
    delete_personal_document,
    documentation_view,
    save_certification,
    delete_certification,
    LicenciaMedicaPorPersonalCreateView,
    LicenciaMedicaPorPersonalUpdateView,
    delete_licencia_medica,
    delete_archivo_licencia_medica,
    listar_licencias_medicas_personal,
    buscar_personal_licencia_medica,
    buscar_personal_ausentismo,
    listar_ausentismos_personal,
    crear_ausentismo,
    actualizar_ausentismo,
    eliminar_ausentismo,
)

urlpatterns = [
    # Vista principal de la tabla
    path('personal/', PersonalListView.as_view(), name='table_personal'),
    path('personal/create/', PersonalCreateView.as_view(), name='personal_create'),
    path('personal/create/documents/', PersonalDocumentCreateView.as_view(), name='personal_document_create'),
    path('personal/create/info_laboral/', PersonalLaborCreateView.as_view(), name='personal_labor_create'),
    path('personal/get_cargos/', get_cargos, name='get_cargos'),
    path('personal/<int:pk>/update/', PersonalUpdateView.as_view(), name='personal_update'),
    path('personal/<int:pk>/delete/', PersonalDeleteView.as_view(), name='personal_delete'),
    path('personal/<int:pk>/toggle-status/', toggle_personal_status, name='toggle_personal_status'),
    
    # Documentación
    path('personal/<int:pk>/documentation/', documentation_view, name='documentation'),
    # Documentos personales individuales
    path('personal/<int:personal_id>/upload_document/', upload_personal_document, name='upload_personal_document'),
    path('personal/<int:personal_id>/upload_carnet/', upload_carnet_document, name='upload_carnet_document'),
    path('personal/<int:personal_id>/delete_document/', delete_personal_document, name='delete_personal_document'),
    # Licencias de conducir
    path('personal/<int:personal_id>/add_license/', add_license, name='add_license'),
    path('personal/<int:personal_id>/add_internal_license/', add_internal_license, name='add_internal_license'),
    path('personal/<int:license_id>/delete_license/', delete_license, name='delete_license'),
    path('personal/<int:license_id>/delete_internal_license/', delete_internal_license, name='delete_internal_license'),
    # Exámenes
    path('personal/<int:personal_id>/add_exam/', add_exam, name='add_exam'),
    path('personal/<int:exam_id>/delete_exam/', delete_exam, name='delete_exam'),
    # Certificaciones
    path('personal/<int:pk>/save_certification/', save_certification, name='save_certification'),
    path('personal/<int:pk>/delete_certification/<int:certification_id>/', delete_certification, name='delete_certification'),
    # Licencia médica
    path('personal/<int:personal_id>/add_licencia_medica/', LicenciaMedicaPorPersonalCreateView.as_view(), name='add_licencia_medica'),
    path('personal/<int:personal_id>/licencias_medicas/', listar_licencias_medicas_personal, name='listar_licencias_medicas_personal'),
    path('licencia_medica/<int:pk>/edit/', LicenciaMedicaPorPersonalUpdateView.as_view(), name='edit_licencia_medica'),
    path('licencia_medica/<int:licencia_id>/delete/', delete_licencia_medica, name='delete_licencia_medica'),
    path('licencia_medica/<int:licencia_id>/delete_archivo/', delete_archivo_licencia_medica, name='delete_archivo_licencia_medica'),
    # Búsqueda de personal para licencias médicas
    path('licencias_medicas/buscar/', buscar_personal_licencia_medica, name='buscar_personal_licencia_medica'),
    # Ausentismos y permisos
    path('ausentismos/buscar/', buscar_personal_ausentismo, name='buscar_personal_ausentismo'),
    path('personal/<int:personal_id>/ausentismos/', listar_ausentismos_personal, name='listar_ausentismos_personal'),
    path('personal/<int:personal_id>/ausentismos/create/', crear_ausentismo, name='crear_ausentismo'),
    path('personal/<int:personal_id>/ausentismos/<int:ausentismo_id>/update/', actualizar_ausentismo, name='actualizar_ausentismo'),
    path('personal/ausentismos/<int:ausentismo_id>/delete/', eliminar_ausentismo, name='eliminar_ausentismo'),
]