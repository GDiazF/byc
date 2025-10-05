from django.urls import path
from .views import (
    RegionListView, RegionCreateView, RegionUpdateView, RegionDeleteView,
    ComunaListView, ComunaCreateView, ComunaUpdateView, ComunaDeleteView,
    UnidadMedidaListView, UnidadMedidaCreateView, UnidadMedidaUpdateView, UnidadMedidaDeleteView,
    EmpresaListView, EmpresaCreateView, EmpresaUpdateView, EmpresaDeleteView, load_comunas
)

urlpatterns = [
    path('regiones/', RegionListView.as_view(), name='region_list'),
    path('regiones/crear/', RegionCreateView.as_view(), name='region_create'),
    path('regiones/<int:pk>/editar/', RegionUpdateView.as_view(), name='region_update'),
    path('regiones/<int:pk>/eliminar/', RegionDeleteView.as_view(), name='region_delete'),
    
    path('comunas/', ComunaListView.as_view(), name='comuna_list'),
    path('comunas/crear/', ComunaCreateView.as_view(), name='comuna_create'),
    path('comunas/<int:pk>/editar/', ComunaUpdateView.as_view(), name='comuna_update'),
    path('comunas/<int:pk>/eliminar/', ComunaDeleteView.as_view(), name='comuna_delete'),
    
    path('unidades-medida/', UnidadMedidaListView.as_view(), name='unidad_medida_list'),
    path('unidades-medida/crear/', UnidadMedidaCreateView.as_view(), name='unidad_medida_create'),
    path('unidades-medida/<int:pk>/editar/', UnidadMedidaUpdateView.as_view(), name='unidad_medida_update'),
    path('unidades-medida/<int:pk>/eliminar/', UnidadMedidaDeleteView.as_view(), name='unidad_medida_delete'),
    
    path('empresas/', EmpresaListView.as_view(), name='empresa_list'),
    path('empresas/crear/', EmpresaCreateView.as_view(), name='empresa_create'),
    path('empresas/<int:pk>/editar/', EmpresaUpdateView.as_view(), name='empresa_update'),
    path('empresas/<int:pk>/eliminar/', EmpresaDeleteView.as_view(), name='empresa_delete'),
    path('ajax/load-comunas/', load_comunas, name='ajax_load_comunas'),
]