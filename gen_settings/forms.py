"""
============================================================================
FORMULARIOS PARA GEN_SETTINGS
============================================================================
Este módulo contiene los formularios Django para gestionar las configuraciones
generales: Region, Comuna, UnidadMedida y Empresa.
Todos los formularios incluyen widgets personalizados con clases CSS de Bootstrap.
============================================================================
"""

from django import forms
from .models import Region, Comuna, UnidadMedida, Empresa


class RegionForm(forms.ModelForm):
    """
    Formulario para crear y editar regiones.
    
    Formulario simple con un solo campo (nombre) y widget de texto
    con estilo Bootstrap.
    """
    class Meta:
        model = Region
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }

class ComunaForm(forms.ModelForm):
    """
    Formulario para crear y editar comunas.
    
    Incluye campos para nombre y región asociada. La región se selecciona
    mediante un dropdown.
    """
    class Meta:
        model = Comuna
        fields = ['nombre', 'region']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'})
        }

class UnidadMedidaForm(forms.ModelForm):
    """
    Formulario para crear y editar unidades de medida.
    
    Incluye campos para código (máximo 3 caracteres) y descripción.
    El código debe ser único en el sistema.
    """
    class Meta:
        model = UnidadMedida
        fields = ['codigo', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'})
        }

class EmpresaForm(forms.ModelForm):
    """
    Formulario para crear y editar empresas.
    
    Incluye todos los campos de información de la empresa: datos fiscales,
    contacto, ubicación. El campo de comuna se carga dinámicamente según
    la región seleccionada mediante JavaScript.
    """
    class Meta:
        model = Empresa
        fields = ['rut', 'dv', 'razonSocial', 'nomFantasia', 'giro', 'direccion', 'telefono', 'email', 'region', 'comuna']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'dv': forms.TextInput(attrs={'class': 'form-control'}),
            'razonSocial': forms.TextInput(attrs={'class': 'form-control'}),
            'nomFantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control', 'id': 'id_region'}),
            'comuna': forms.Select(attrs={'class': 'form-control', 'id': 'id_comuna'})
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con el queryset de comunas filtrado por región.
        
        Si hay datos POST con región seleccionada, filtra las comunas de esa región.
        Si es una edición (instance.pk existe), muestra las comunas de la región actual.
        Si es creación nueva, no muestra comunas hasta que se seleccione una región.
        
        Args:
            *args: Argumentos posicionales del formulario.
            **kwargs: Argumentos de palabra clave del formulario.
        """
        super().__init__(*args, **kwargs)
        # Inicialmente, solo mostramos las comunas de la región seleccionada
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['comuna'].queryset = Comuna.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['comuna'].queryset = self.instance.region.comuna_set
        else:
            self.fields['comuna'].queryset = Comuna.objects.none()
