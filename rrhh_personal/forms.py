from django import forms
from .models import *


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
    # Clases: Mostrar todas, requerido
    clases = forms.ModelMultipleChoiceField(
        queryset=ClaseLicencia.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label='Clases Autorizadas'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agrupar las clases por tipo de licencia
        self.fields['clases'].queryset = ClaseLicencia.objects.select_related('tipoLicencia_id').order_by('tipoLicencia_id', 'claseLicencia')

    class Meta:
        model = LicenciaPorPersonal
        fields = ['clases', 'fechaEmision', 'fechaVencimiento', 'rutaDoc','observacion']
        widgets = {
            'fechaEmision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fechaVencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rutaDoc': forms.FileInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'fechaEmision': 'Fecha de Emisión', 
            'fechaVencimiento': 'Fecha de Vencimiento', 
            'rutaDoc': 'Documento', 
            'observacion': 'Observación'
        }


#formulario para certificacion------------------------------------------------------------  
class CertificacionPersonal(forms.ModelForm):
    proveedor_id = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipoCertificacion_id = forms.ModelChoiceField(
        queryset=TipoCertificacion.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Certificacion
        fields = ['proveedor_id', 'tipoCertificacion_id', 'fechaEmision', 'fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'fechaEmision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fechaVencimiento': forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'rutaDoc': forms.FileInput(attrs={'accept': 'application/pdf, image/jpg, image/png', 'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {'proveedor_id': 'Proveedor', 'tipoCertificacion_id': 'Tipo de certificación', 'fechaEmision': 'Fecha de emisión', 'fechaVencimiento': 'Fecha de vencimiento', 'rutaDoc': 'Documento', 'observacion': 'Observación'}


#formulario para examenes
class ExamenPersonal(forms.ModelForm):
    tipoEx_id = forms.ModelChoiceField(
        queryset=TipoExamen.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    resultadoEx_id = forms.ModelChoiceField(
        queryset=ResultadoExamen.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    proveedor_id = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), 
        empty_label='-----------',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Examen
        fields = ['tipoEx_id','resultadoEx_id', 'proveedor_id','fechaEmision','fechaVencimiento', 'rutaDoc', 'observacion']
        widgets = {
            'fechaEmision' : forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'fechaVencimiento' : forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rutaDoc' : forms.FileInput(attrs={'accept': 'application/pdf, image/jpg, image/png', 'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {'tipoEx_id': 'Tipo de examen', 'resultadoEx_id': 'Resultado', 'proveedor_id': 'Proveedor', 'fechaEmision': 'Fecha de emisión', 'fechaVencimiento': 'Fecha de vencimiento', 'rutaDoc': 'Documento', 'observacion': 'Observación'}

        