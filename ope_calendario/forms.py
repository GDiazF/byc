# ============================================================================
# FORMULARIOS DE CALENDARIO DE OPERACIONES
# ============================================================================
# Este módulo define los formularios utilizados en el sistema de calendario de operaciones.

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
    Permite incorporar personal a una faena con un estado manual en un rango de fechas específico.
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
        """
        Inicializar el formulario y configurar el queryset de estados.
        Filtra solo los estados relevantes para asignación manual (Trabajo Día, Trabajo Noche, Descanso).
        """
        super().__init__(*args, **kwargs)
        
        # Paso 1: Obtener solo los estados relevantes para asignación manual
        # Estos estados son los más comunes para incorporaciones tardías
        self.fields['estado'].queryset = Estado.objects.filter(
            nombre__in=['Trabajo Día', 'Trabajo Noche', 'Descanso']
        ).order_by('nombre')
    
    def clean_personal(self):
        """
        Validar y convertir el ID de personal a un objeto Personal.
        Este método se ejecuta automáticamente durante la validación del formulario.
        
        Retorna:
            Personal: Objeto Personal si existe, None si no se proporcionó ID
        
        Lanza:
            ValidationError: Si el ID de personal no existe en la base de datos
        """
        personal_id = self.cleaned_data.get('personal')
        if personal_id:
            try:
                # Buscar el personal por su ID
                return Personal.objects.get(personal_id=personal_id)
            except Personal.DoesNotExist:
                # Si no existe, lanzar error de validación
                raise ValidationError('Personal no encontrado.')
        return None
    
    def clean(self):
        """
        Validación general del formulario.
        Valida que la fecha de fin no sea anterior a la fecha de inicio.
        Este método se ejecuta después de que todos los campos individuales han sido validados.
        
        Retorna:
            dict: Datos limpios y validados del formulario
        
        Lanza:
            ValidationError: Si la fecha de fin es anterior a la fecha de inicio
        """
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Paso 1: Validar que fecha de fin no sea anterior a fecha de inicio
        # Esta validación asegura la integridad de los rangos de fechas
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError(
                    'La fecha de fin no puede ser anterior a la fecha de inicio.'
                )
        
        return cleaned_data

