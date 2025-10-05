from django import forms
from .models import Region, Comuna, UnidadMedida, Empresa

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }

class ComunaForm(forms.ModelForm):
    class Meta:
        model = Comuna
        fields = ['nombre', 'region']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'})
        }

class UnidadMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = ['codigo', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'})
        }

class EmpresaForm(forms.ModelForm):
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
