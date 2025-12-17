"""
Formularios Django para la gestión de personal y documentos relacionados.

Este módulo contiene todos los formularios utilizados para crear, editar y validar
información de personal, licencias, certificaciones, exámenes, ausentismos, etc.
"""
from django import forms
from .models import *
from datetime import date
from gen_settings.widgets import DateInputChileno


# ============================================================================
# FORMULARIO PRINCIPAL: CREACIÓN Y EDICIÓN DE PERSONAL
# ============================================================================

class PersonalCreationForm(forms.ModelForm):
    """
    Formulario para crear y editar información de personal.
    
    Incluye campos personales básicos (nombre, RUT, fecha de nacimiento, etc.),
    información de contacto, y todos los documentos personales requeridos.
    """

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
        """
        Inicializa el formulario y configura validaciones de fecha.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre, puede incluir 'instance_id' para edición
        """
        # Extraer instance_id si se proporciona (para edición)
        self.instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)
        
        # Establecer fecha máxima (hoy) para fecha de nacimiento en el widget HTML
        if 'fechanac' in self.fields:
            self.fields['fechanac'].widget.attrs['max'] = date.today().isoformat()

    def clean_fechanac(self):
        """
        Valida que la fecha de nacimiento no sea posterior a la fecha actual.
        
        Returns:
            date: La fecha de nacimiento validada
            
        Raises:
            forms.ValidationError: Si la fecha es posterior a hoy
        """
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
            'fechanac' : DateInputChileno(),
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

    

# ============================================================================
# FORMULARIO DE INFORMACIÓN LABORAL
# ============================================================================

class InfoLaboralPersonalForm(forms.ModelForm):
    """
    Formulario para ingresar la información laboral de las personas.
    
    Permite asociar un personal con una empresa, departamento, cargo y fecha de contratación.
    """

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
            'fechacontrata' : DateInputChileno(),
        }

        labels = {'fechacontrata' : 'Fecha Contrata'}

# ============================================================================
# FORMULARIOS DE LICENCIAS DE CONDUCIR
# ============================================================================

class LicenciasPersonal(forms.ModelForm):
    """
    Formulario para crear y editar licencias de conducir del personal.
    
    Permite seleccionar múltiples tipos de licencia (A, B, C, D, E, etc.)
    y asociar un documento PDF con las fechas de emisión y vencimiento.
    """
    # Campo para seleccionar múltiples tipos de licencia
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
            'fechaEmision': DateInputChileno(),
            'fechaVencimiento': DateInputChileno(),
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


# ============================================================================
# FORMULARIOS DE LICENCIAS INTERNAS
# ============================================================================

class LicenciasInternasPersonal(forms.ModelForm):
    """
    Formulario para crear y editar licencias internas de conducir del personal.
    
    Las licencias internas son emitidas por la empresa/faena, no por el estado.
    Incluye número de licencia, empresa emisora, y documento asociado.
    """
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
        """
        Inicializa el formulario y establece el queryset del campo tipoLicenciaInterna_id.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        """
        super().__init__(*args, **kwargs)
        # Cargar los tipos de licencia interna disponibles, ordenados alfabéticamente
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
            'fechaEmision': DateInputChileno(),
            'fechaVencimiento': DateInputChileno(),
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
        """
        Valida que la fecha de vencimiento no sea anterior a la fecha de emisión.
        
        Returns:
            dict: Datos del formulario validados
            
        Raises:
            forms.ValidationError: Si la fecha de vencimiento es anterior a la de emisión
        """
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        # Validar que la fecha de vencimiento sea posterior o igual a la de emisión
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


# ============================================================================
# FORMULARIO DE CERTIFICACIONES
# ============================================================================

class CertificacionPersonal(forms.ModelForm):
    """
    Formulario para crear y editar certificaciones del personal.
    
    Las certificaciones son documentos que acreditan habilidades o competencias
    específicas (ej: Operador de Grúa, Trabajo en Altura, etc.).
    Incluye proveedor, tipo de certificación, fechas y documento asociado.
    """
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
            'fechaEmision': DateInputChileno(),
            'fechaVencimiento': DateInputChileno(),
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
        """
        Valida que la fecha de vencimiento no sea anterior a la fecha de emisión.
        
        Returns:
            dict: Datos del formulario validados
            
        Raises:
            forms.ValidationError: Si la fecha de vencimiento es anterior a la de emisión
        """
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        # Validar que la fecha de vencimiento sea posterior o igual a la de emisión
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


# ============================================================================
# FORMULARIO DE EXÁMENES
# ============================================================================

class ExamenPersonal(forms.ModelForm):
    """
    Formulario para crear y editar exámenes médicos del personal.
    
    Los exámenes pueden ser de diferentes tipos (vista, audición, psicológico, etc.)
    y tienen un resultado (Apto, No Apto, etc.). Incluye proveedor, fechas y documento asociado.
    """
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
            'fechaEmision' : DateInputChileno(),
            'fechaVencimiento' : DateInputChileno(),
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
        """
        Valida que la fecha de vencimiento no sea anterior a la fecha de emisión.
        
        Returns:
            dict: Datos del formulario validados
            
        Raises:
            forms.ValidationError: Si la fecha de vencimiento es anterior a la de emisión
        """
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        fecha_vencimiento = cleaned_data.get('fechaVencimiento')
        
        # Validar que la fecha de vencimiento sea posterior o igual a la de emisión
        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento < fecha_emision:
                raise forms.ValidationError('La fecha de vencimiento no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


# ============================================================================
# FORMULARIO DE AUSENTISMOS
# ============================================================================

class AusentismoForm(forms.ModelForm):
    """
    Formulario para crear y editar ausentismos del personal.
    
    Los ausentismos pueden ser de diferentes tipos (vacaciones, permiso sin goce, etc.).
    La fecha de fin se calcula automáticamente basándose en la fecha de inicio y los días.
    Valida que no haya solapamientos con otros ausentismos del mismo personal.
    """
    tipoausen_id = forms.ModelChoiceField(
        queryset=TipoAusentismo.objects.all().order_by('tipo'),
        empty_label='Seleccione un tipo',
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
        label='Tipo de Ausentismo',
        required=True
    )
    
    # Campo adicional solo para mostrar la fecha de fin (no se guardará)
    # Este campo NO se incluye en el POST, solo es para mostrar
    fechafin_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'id_fechafin'}),
        label='Fecha de Fin (Calculada)'
    )
    
    class Meta:
        model = Ausentismo
        fields = ['tipoausen_id', 'fechaini', 'dias_ausentismo', 'observacion']
        widgets = {
            'fechaini': DateInputChileno(attrs={'required': 'required'}),
            'dias_ausentismo': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': 'required'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fechaini': 'Fecha de Inicio',
            'dias_ausentismo': 'Días de Ausentismo',
            'observacion': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y configura el campo de fecha de fin calculada.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre, puede incluir 'personal_id' para validación
        """
        super().__init__(*args, **kwargs)
        
        # Si es CREACIÓN (no edición), limpiar el valor por defecto del modelo
        if not self.instance.pk:
            self.fields['dias_ausentismo'].initial = None
        
        # Si es edición, calcular y mostrar la fecha de fin en formato chileno
        if self.instance and self.instance.pk:
            if self.instance.fechafin:
                # Formatear fecha en formato chileno DD/MM/YYYY para mostrar al usuario
                self.fields['fechafin_display'].initial = self.instance.fechafin.strftime('%d/%m/%Y')
        
        # Excluir fechafin_display del procesamiento del formulario (solo es visual)
        # Esto evita que Django intente procesarlo como campo de fecha
        if 'fechafin_display' in self.fields:
            self.fields['fechafin_display'].widget.attrs['name'] = ''  # Sin name, no se envía en POST
    
    def clean_dias_ausentismo(self):
        """
        Valida que los días de ausentismo sean al menos 1.
        
        Returns:
            int: Los días de ausentismo validados
            
        Raises:
            forms.ValidationError: Si los días son menores a 1
        """
        dias = self.cleaned_data.get('dias_ausentismo')
        if dias and dias < 1:
            raise forms.ValidationError('Los días de ausentismo deben ser al menos 1.')
        return dias
    
    def clean(self):
        """
        Valida que no haya solapamiento de fechas con otros ausentismos del mismo personal.
        
        Calcula la fecha de fin basándose en la fecha de inicio y los días.
        Luego verifica si hay otros ausentismos del mismo personal que se solapen
        con el rango de fechas del ausentismo actual.
        
        Returns:
            dict: Datos del formulario validados
            
        Raises:
            forms.ValidationError: Si hay solapamiento con otro ausentismo existente
        """
        cleaned_data = super().clean()
        fechaini = cleaned_data.get('fechaini')
        dias_ausentismo = cleaned_data.get('dias_ausentismo')
        
        if fechaini and dias_ausentismo:
            from datetime import timedelta
            # Calcular fecha de fin: fecha_inicio + (días - 1)
            # Ejemplo: Si inicia el 1 de enero y son 3 días, termina el 3 de enero
            fechafin = fechaini + timedelta(days=dias_ausentismo - 1)
            
            # Obtener el personal_id desde la vista (se pasa en el constructor)
            if hasattr(self, 'personal_id'):
                # Verificar solapamiento con otros ausentismos del mismo personal
                # Excluir el ausentismo actual si es una edición
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

        
# ============================================================================
# FORMULARIO DE LICENCIAS MÉDICAS
# ============================================================================

class LicenciaMedicaPorPersonalForm(forms.ModelForm):
    """
    Formulario para crear y editar licencias médicas del personal.
    
    Las licencias médicas no tienen archivo asociado, solo registran fechas.
    La fecha de fin se calcula automáticamente basándose en la fecha de emisión y los días.
    Valida que no haya solapamientos con otras licencias médicas del mismo personal.
    """
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
            'fechaEmision': DateInputChileno(attrs={'required': 'required'}),
            'dias_licencia': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': 'required'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fechaEmision': 'Fecha de Emisión',
            'dias_licencia': 'Días de Licencia',
            'observacion': 'Observaciones'
        }
    
    def clean(self):
        """
        Valida que no haya solapamiento de fechas con otras licencias médicas del mismo personal.
        
        Calcula la fecha de fin basándose en la fecha de emisión y los días.
        Luego verifica si hay otras licencias médicas del mismo personal que se solapen
        con el rango de fechas de la licencia actual.
        
        Returns:
            dict: Datos del formulario validados
            
        Raises:
            forms.ValidationError: Si hay solapamiento con otra licencia médica existente
        """
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fechaEmision')
        dias_licencia = cleaned_data.get('dias_licencia')
        
        if fecha_emision and dias_licencia:
            from datetime import timedelta
            # Calcular fecha de fin: fecha_emision + (días - 1)
            # Ejemplo: Si se emite el 1 de enero y son 3 días, termina el 3 de enero
            fecha_fin = fecha_emision + timedelta(days=dias_licencia - 1)
            
            # Obtener el personal_id desde la vista (se pasa en el constructor)
            if hasattr(self, 'personal_id'):
                # Verificar solapamiento con otras licencias médicas del mismo personal
                # Excluir la licencia actual si es una edición
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

        