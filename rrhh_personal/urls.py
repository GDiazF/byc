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
    documentation_view,
    save_certification,
    delete_certification
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
    path('personal/<int:personal_id>/add_license/', add_license, name='add_license'),
    path('personal/<int:personal_id>/add_exam/', add_exam, name='add_exam'),
    path('personal/<int:license_id>/delete_license/', delete_license, name='delete_license'),
    path('personal/<int:exam_id>/delete_exam/', delete_exam, name='delete_exam'),
    path('personal/<int:pk>/save_certification/', save_certification, name='save_certification'),
    path('personal/<int:pk>/delete_certification/<int:certification_id>/', delete_certification, name='delete_certification'),
]