from django.urls import path
# Importar vistas individualmente para claridad
from .views import (
    PersonalListView,
    PersonalCreateView,
    PersonalDocumentCreateView,
    PersonalLaborCreateView,
    PersonalUpdateView,
    PersonalDeleteView,
    get_cargos
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
]