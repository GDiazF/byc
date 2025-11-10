from django import forms
from .models import *
from datetime import date


#formulario para la creacion de personas
class PersonalCreationForm(forms.ModelForm):

    sexo_id = forms.ModelChoiceField(
        queryset=Sexo.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})  # Aquí se aplica el widget
    )
    
    region_id = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})  # Aquí también
    )

    comuna_id = forms.ModelChoiceField(
        queryset=Comuna.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    estcivil_id = forms.ModelChoiceField(
        queryset=EstadoCivil.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)
        
        # Establecer fecha máxima (hoy) para fecha de nacimiento
        if 'fechanac' in self.fields:
            self.fields['fechanac'].widget.attrs['max'] = date.today().isoformat()

    def clean_fechanac(self):
        fechanac = self.cleaned_data.get('fechanac')
        if fechanac and fechanac > date.today():
            raise forms.ValidationError('La fecha de nacimiento no puede ser posterior a la fecha actual.')
        return fechanac
    
    class Meta:
        model = Personal
        fields = [
            'rut', 'dvrut', 'nombre', 'apepat', 'apemat', 
            'sexo_id', 'fechanac', 'estcivil_id', 'correo', 
            'region_id', 'comuna_id', 'direccion',
            'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
            'foto_carnet', 'certificado_afp', 'certificado_salud',
            'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
            'fotocopia_finiquito', 'comprobante_banco'
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'type': 'text', 'class': 'form-control'}),
            'dvrut': forms.TextInput(attrs={'type': 'text', 'class': 'form-control', 'id': 'id_dvrut', 'readonly': 'readonly'}),
            'nombre': forms.TextInput(attrs={'type': 'text', 'class': 'form-control'}),
            'apepat': forms.TextInput(attrs={'type': 'text', 'class': 'form-control'}),
            'apemat': forms.TextInput(attrs={'type': 'text', 'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'type': 'text', 'class': 'form-control'}),
            'fechanac' : forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'type': 'email', 'class': 'form-control'}),
            'curriculum': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'certificado_antecedentes': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'hoja_vida_conductor': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'foto_carnet': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png'
            }),
            'certificado_afp': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'certificado_salud': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'certificado_estudios': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'certificado_residencia': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fotocopia_carnet': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fotocopia_finiquito': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'comprobante_banco': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'apepat': 'Apellido paterno',
            'apemat': 'Apellido Materno',
            'rut': 'Rut',
            'dvrut': 'Dígito verificador',
            'fechanac': 'Fecha de nacimiento',
            'estcivil_id': 'Estado civil',
            'correo': 'Correo electrónico',
            'region_id': 'Región',
            'comuna_id': 'Comuna',
            'direccion': 'Dirección',
            'sexo_id':'Sexo',
            'curriculum': 'Curriculum Vitae',
            'certificado_antecedentes': 'Certificado de Antecedentes',
            'hoja_vida_conductor': 'Hoja de Vida del Conductor',
            'foto_carnet': 'Foto tipo Carnet',
            'certificado_afp': 'Certificado de Afiliación AFP',
            'certificado_salud': 'Certificado de Afiliación de Salud',
            'certificado_estudios': 'Certificado de Estudios',
            'certificado_residencia': 'Certificado de Residencia',
            'fotocopia_carnet': 'Fotocopia de Carnet',
            'fotocopia_finiquito': 'Fotocopia de Último Finiquito',
            'comprobante_banco': 'Comprobante de Cuenta Bancaria',
        }

    

#formulario para ingresar la informacion laboral de las personas
class InfoLaboralPersonalForm(forms.ModelForm):

    empresa_id = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    depto_id = forms.ModelChoiceField(
        queryset=DeptoEmpresa.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    cargo_id = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        empty_label='elija una opción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = InfoLaboral
        fields = ['empresa_id', 'depto_id', 'cargo_id', 'fechacontrata']
        widgets = {
            'fechacontrata' : forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

        labels = {'fechacontrata' : 'Fecha Contrata'}

#formularios de licencias --------------------------------------------------------------
class LicenciasPersonal(forms.ModelForm):
    tipos = forms.ModelMultipleChoiceField(
        queryset=TipoLicencia.objects.all().order_by('tipoLicencia'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'list-unstyled'
        }),
        required=True,
        label='Tipos de Licencia'
    )

    class Meta:
        model = LicenciaPorPersonal
        fields = ['tipos', 'fechaEmision', 'fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'fechaEmision': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'fechaVencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'rutaDoc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'fechaEmision': 'Fecha de Emisión',
            'fechaVencimiento': 'Fecha de Vencimiento',
            'rutaDoc': 'Documento',
            'observacion': 'Observación'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


#formularios de licencias internas ------------------------------------------------------
class LicenciasInternasPersonal(forms.ModelForm):
    tipoLicenciaInterna_id = forms.ModelChoiceField(
        queryset=None,  # Se establecerá en __init__
        empty_label='Seleccione un tipo de licencia',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label='Tipo de Licencia Interna'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import TipoLicenciaInterna
        self.fields['tipoLicenciaInterna_id'].queryset = TipoLicenciaInterna.objects.all().order_by('tipoLicenciaInterna')

    class Meta:
        from .models import LicenciaInternaPorPersonal
        model = LicenciaInternaPorPersonal
        fields = ['tipoLicenciaInterna_id', 'numero_licencia', 'empresa_emisora', 'fechaEmision', 'fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'numero_licencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LI-2024-001'
            }),
            'empresa_emisora': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Faena Los Bronces'
            }),
            'fechaEmision': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'fechaVencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'rutaDoc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'numero_licencia': 'N° de Licencia Interna',
            'empresa_emisora': 'Empresa/Faena Emisora',
            'fechaEmision': 'Fecha de Emisión',
            'fechaVencimiento': 'Fecha de Vencimiento',
            'rutaDoc': 'Documento',
            'observacion': 'Observaciones'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


#formulario para certificacion------------------------------------------------------------  
class CertificacionPersonal(forms.ModelForm):
    proveedor_id = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Proveedor'
    )
    tipoCertificacion_id = forms.ModelChoiceField(
        queryset=TipoCertificacion.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de certificación'
    )

    class Meta:
        model = Certificacion
        fields = ['proveedor_id', 'tipoCertificacion_id', 'fechaEmision', 'fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'fechaEmision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fechaVencimiento': forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'rutaDoc': forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'fechaEmision': 'Fecha de emisión',
            'fechaVencimiento': 'Fecha de vencimiento',
            'rutaDoc': 'Documento',
            'observacion': 'Observación'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


#formulario para examenes
class ExamenPersonal(forms.ModelForm):
    tipoEx_id = forms.ModelChoiceField(
        queryset=TipoExamen.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de examen'
    )
    resultadoEx_id = forms.ModelChoiceField(
        queryset=ResultadoExamen.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Resultado'
    )
    proveedor_id = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Proveedor'
    )
    
    class Meta:
        model = Examen
        fields = ['tipoEx_id','resultadoEx_id', 'proveedor_id','fechaEmision','fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'fechaEmision' : forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'fechaVencimiento' : forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rutaDoc' : forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'fechaEmision': 'Fecha de emisión',
            'fechaVencimiento': 'Fecha de vencimiento',
            'rutaDoc': 'Documento',
            'observacion': 'Observación'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


# Formulario para ausentismos
class AusentismoForm(forms.ModelForm):
    tipoausen_id = forms.ModelChoiceField(
        queryset=TipoAusentismo.objects.all().order_by('tipo'),
        empty_label='Seleccione un tipo',
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
        label='Tipo de Ausentismo',
        required=True
    )
    
    # Campo adicional solo para mostrar la fecha de fin (no se guardará)
    fechafin_display = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'id_fechafin'}),
        label='Fecha de Fin (Calculada)'
    )
    
    class Meta:
        model = Ausentismo
        fields = ['tipoausen_id', 'fechaini', 'dias_ausentismo', 'observacion']
        widgets = {
            'fechaini': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'dias_ausentismo': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': 'required'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fechaini': 'Fecha de Inicio',
            'dias_ausentismo': 'Días de Ausentismo',
            'observacion': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si es CREACIÓN (no edición), limpiar el valor por defecto del modelo
        if not self.instance.pk:
            self.fields['dias_ausentismo'].initial = None
        
        # Si es edición, calcular y mostrar la fecha de fin en formato chileno
        if self.instance and self.instance.pk:
            if self.instance.fechafin:
                # Formatear fecha en formato chileno DD/MM/YYYY
                self.fields['fechafin_display'].initial = self.instance.fechafin.strftime('%d/%m/%Y')
    
    def clean_dias_ausentismo(self):
        dias = self.cleaned_data.get('dias_ausentismo')
        if dias and dias < 1:
            raise forms.ValidationError('Los días de ausentismo deben ser al menos 1.')
        return dias
    
    def clean(self):
        cleaned_data = super().clean()
        fechaini = cleaned_data.get('fechaini')
        dias_ausentismo = cleaned_data.get('dias_ausentismo')
        
        if fechaini and dias_ausentismo:
            from datetime import timedelta
            # Calcular fecha de fin
            fechafin = fechaini + timedelta(days=dias_ausentismo - 1)
            
            # Obtener el personal_id desde la vista (se pasa en el constructor)
            if hasattr(self, 'personal_id'):
                # Verificar solapamiento con otros ausentismos del mismo personal
                solapamientos = Ausentismo.objects.filter(
                    personal_id=self.personal_id
                ).exclude(
                    pk=self.instance.pk if self.instance.pk else None
                ).filter(
                    # Condición de solapamiento: 
                    # (fecha_inicio_nueva <= fecha_fin_existente) AND (fecha_fin_nueva >= fecha_inicio_existente)
                    fechaini__lte=fechafin,
                    fechafin__gte=fechaini
                )
                
                if solapamientos.exists():
                    primer_solapamiento = solapamientos.first()
                    raise forms.ValidationError(
                        f'Las fechas se solapan con un ausentismo existente: '
                        f'{primer_solapamiento.tipoausen_id} del {primer_solapamiento.fechaini.strftime("%d/%m/%Y")} '
                        f'al {primer_solapamiento.fechafin.strftime("%d/%m/%Y")}.'
                    )
        
        return cleaned_data

        
# Formulario para ingresar licencias médicas
class LicenciaMedicaPorPersonalForm(forms.ModelForm):
    tipoLicenciaMedica_id = forms.ModelChoiceField(
        queryset=TipoLicenciaMedica.objects.all().order_by('tipoLicenciaMedica'),
        empty_label='Seleccione un tipo',
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
        label='Tipo de Licencia Médica',
        required=True
    )
    fecha_fin_licencia = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label='Fecha de Fin (Calculada)'
    )

    class Meta:
        model = LicenciaMedicaPorPersonal
        fields = ['tipoLicenciaMedica_id', 'fechaEmision', 'dias_licencia', 'observacion']
        widgets = {
            'fechaEmision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'dias_licencia': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': 'required'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fechaEmision': 'Fecha de Emisión',
            'dias_licencia': 'Días de Licencia',
            'observacion': 'Observaciones'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        dias_licencia = cleaned_data.get('dias_licencia')
        
        if fecha_emision and dias_licencia:
            from datetime import timedelta
            # Calcular fecha de fin
            fecha_fin = fecha_emision + timedelta(days=dias_licencia - 1)
            
            # Obtener el personal_id desde la vista (se pasa en el constructor)
            if hasattr(self, 'personal_id'):
                # Verificar solapamiento con otras licencias médicas del mismo personal
                solapamientos = LicenciaMedicaPorPersonal.objects.filter(
                    personal_id=self.personal_id
                ).exclude(
                    pk=self.instance.pk if self.instance.pk else None
                ).filter(
                    # Condición de solapamiento: 
                    # (fecha_inicio_nueva <= fecha_fin_existente) AND (fecha_fin_nueva >= fecha_inicio_existente)
                    fechaEmision__lte=fecha_fin,
                    fecha_fin_licencia__gte=fecha_emision
                )
                
                if solapamientos.exists():
                    primer_solapamiento = solapamientos.first()
                    raise forms.ValidationError(
                        f'Las fechas se solapan con una licencia médica existente: '
                        f'{primer_solapamiento.tipoLicenciaMedica_id} del {primer_solapamiento.fechaEmision.strftime("%d/%m/%Y")} '
                        f'al {primer_solapamiento.fecha_fin_licencia.strftime("%d/%m/%Y")}.'
                    )
        
        return cleaned_data

        