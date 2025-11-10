from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date, timedelta
from .models import AsignacionFaena, EstadoManual, Faena, Turno, TurnoBloque, Estado
from rrhh_personal.models import Personal


class IncorporacionTardiaForm(forms.Form):
    """
    Formulario simplificado para asignar estados manuales a personal en una faena.
    Útil para asignar días específicos de trabajo o descanso sin un turno completo.
    """
    personal = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    faena = forms.ModelChoiceField(
        queryset=Faena.objects.filter(activo=True).order_by('nombre'),
        label='Faena',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=True
    )
    
    estado = forms.ModelChoiceField(
        queryset=None,  # Se configurará en __init__
        label='Estado',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=True,
        help_text='Tipo de estado a asignar'
    )
    
    fecha_inicio = forms.DateField(
        label='Fecha de Inicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        required=True
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de Fin',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        required=True
    )
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        required=False,
        label='Observaciones'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener solo los estados relevantes para asignación manual
        self.fields['estado'].queryset = Estado.objects.filter(
            nombre__in=['Trabajo Día', 'Trabajo Noche', 'Descanso']
        ).order_by('nombre')
    
    def clean_personal(self):
        """Convertir personal_id a objeto Personal"""
        personal_id = self.cleaned_data.get('personal')
        if personal_id:
            try:
                return Personal.objects.get(personal_id=personal_id)
            except Personal.DoesNotExist:
                raise ValidationError('Personal no encontrado.')
        return None
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar que fecha de fin no sea anterior a fecha de inicio
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError(
                    'La fecha de fin no puede ser anterior a la fecha de inicio.'
                )
        
        return cleaned_data

