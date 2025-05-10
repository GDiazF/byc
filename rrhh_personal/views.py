from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PersonalCreationForm, InfoLaboralPersonalForm, LicenciasPersonal, CertificacionPersonal, ExamenPersonal
from django.shortcuts import redirect
from .models import Personal, InfoLaboral, Ausentismo, TipoAusentismo, LicenciaPorPersonal, Certificacion, Examen, Comuna, Cargo
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.db.models import Max
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.base import ContentFile
import base64
import json

# Create your views here.

#vista para tabla de personal
class PersonalListView(ListView, LoginRequiredMixin):
    model = Personal
    template_name = 'personal/table_personal.html'
    context_object_name = 'personal'
    paginate_by = 10

class PersonalCreateView(LoginRequiredMixin, CreateView):
    model = Personal
    form_class = PersonalCreationForm
    template_name = 'personal/create_personal.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Excluir campos de documentación en el primer paso
        document_fields = [
            'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
            'foto_carnet', 'certificado_afp', 'certificado_salud',
            'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
            'fotocopia_finiquito', 'comprobante_banco'
        ]
        for field in document_fields:
            if field in form.fields:
                del form.fields[field]
        return form
    
    def form_valid(self, form):
        # Almacenar datos básicos en la sesión
        personal_data = form.cleaned_data
        self.request.session['personal_data'] = {
            'rut': personal_data['rut'],
            'dvrut': personal_data['dvrut'],
            'nombre': personal_data['nombre'],
            'apepat': personal_data['apepat'],
            'apemat': personal_data['apemat'],
            'sexo_id': personal_data['sexo_id'].pk if personal_data['sexo_id'] else None,
            'fechanac': personal_data['fechanac'].strftime('%Y-%m-%d') if personal_data['fechanac'] else None,
            'estcivil_id': personal_data['estcivil_id'].pk if personal_data['estcivil_id'] else None,
            'correo': personal_data['correo'],
            'region_id': personal_data['region_id'].pk if personal_data['region_id'] else None,
            'comuna_id': personal_data['comuna_id'].pk if personal_data['comuna_id'] else None,
            'direccion': personal_data['direccion'],
        }
        
        messages.success(self.request, 'Información personal validada. Por favor complete la documentación.')
        return redirect('personal_document_create')

    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario personal. Por favor revise los datos ingresados.')
        return super().form_invalid(form)

class PersonalDocumentCreateView(LoginRequiredMixin, CreateView):
    model = Personal
    form_class = PersonalCreationForm
    template_name = 'personal/create_personal_documents.html'
    
    def dispatch(self, request, *args, **kwargs):
        if 'personal_data' not in request.session:
            messages.error(request, 'Por favor complete primero la información personal.')
            return redirect('personal_create')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Mantener solo los campos de documentación
        basic_fields = [
            'rut', 'dvrut', 'nombre', 'apepat', 'apemat', 'sexo_id',
            'fechanac', 'estcivil_id', 'correo', 'region_id', 'comuna_id', 'direccion'
        ]
        for field in basic_fields:
            if field in form.fields:
                del form.fields[field]
        return form

    def form_valid(self, form):
        # Procesar los archivos
        files_data = {}
        for field_name, field in form.files.items():
            file_content = field.read()
            files_data[field_name] = {
                'name': field.name,
                'content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': field.content_type
            }
            field.seek(0)

        # Almacenar datos de documentos en la sesión
        self.request.session['document_data'] = files_data
        
        messages.success(self.request, 'Documentación validada. Por favor complete la información laboral.')
        return redirect('personal_labor_create')

    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario de documentación. Por favor revise los archivos subidos.')
        return super().form_invalid(form)

class PersonalLaborCreateView(LoginRequiredMixin, CreateView):
    model = InfoLaboral
    form_class = InfoLaboralPersonalForm
    template_name = 'personal/create_personal_labor.html'
    success_url = reverse_lazy('table_personal')

    def dispatch(self, request, *args, **kwargs):
        if 'personal_data' not in request.session or 'document_data' not in request.session:
            messages.error(request, 'Por favor complete primero la información personal y documentación.')
            return redirect('personal_create')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Recuperar los datos personales y de documentos de la sesión
                personal_data = self.request.session['personal_data']
                files_data = self.request.session['document_data']
                
                # Crear el objeto Personal
                personal = Personal(
                    rut=personal_data['rut'],
                    dvrut=personal_data['dvrut'],
                    nombre=personal_data['nombre'],
                    apepat=personal_data['apepat'],
                    apemat=personal_data['apemat'],
                    sexo_id_id=personal_data['sexo_id'],
                    fechanac=personal_data['fechanac'],
                    estcivil_id_id=personal_data['estcivil_id'],
                    correo=personal_data['correo'],
                    region_id_id=personal_data['region_id'],
                    comuna_id_id=personal_data['comuna_id'],
                    direccion=personal_data['direccion']
                )
                personal.save()

                # Procesar y guardar los archivos
                for field_name, file_data in files_data.items():
                    if file_data:
                        file_content = base64.b64decode(file_data['content'])
                        content_file = ContentFile(file_content, name=file_data['name'])
                        setattr(personal, field_name, content_file)
                
                personal.save()

                # Asignar el personal al formulario laboral y guardar
                form.instance.personal_id = personal
                self.object = form.save()

                # Limpiar los datos de la sesión
                del self.request.session['personal_data']
                del self.request.session['document_data']
                
                messages.success(self.request, 'Personal creado exitosamente con toda su información.')
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error al guardar la información: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario laboral. Por favor revise los datos ingresados.')
        return super().form_invalid(form)

def get_cargos(request):
    depto_id = request.GET.get('depto_id')
    cargos = Cargo.objects.filter(depto_id=depto_id).values_list('cargo_id', 'cargo')
    return JsonResponse(dict(cargos))

class PersonalUpdateView(LoginRequiredMixin, UpdateView):
    model = Personal
    form_class = PersonalCreationForm
    template_name = 'personal/edit_personal.html'
    success_url = reverse_lazy('table_personal')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'labor_form' not in context:
            # Get or create InfoLaboral instance
            info_laboral, created = InfoLaboral.objects.get_or_create(personal_id=self.object)
            context['labor_form'] = InfoLaboralPersonalForm(instance=info_laboral)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_type = request.POST.get('form_type', 'personal')
        
        if form_type == 'personal':
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        
        elif form_type == 'documents':
            form = self.get_form()
            if form.is_valid():
                # Only save document fields
                personal = form.save(commit=False)
                document_fields = [
                    'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                    'foto_carnet', 'certificado_afp', 'certificado_salud',
                    'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                    'fotocopia_finiquito', 'comprobante_banco'
                ]
                for field in document_fields:
                    if field in request.FILES:
                        setattr(personal, field, request.FILES[field])
                personal.save()
                messages.success(request, 'Documentación actualizada exitosamente.')
                return redirect(f"{self.success_url}?tab=documents")
            else:
                return self.form_invalid(form)
        
        elif form_type == 'labor':
            info_laboral = InfoLaboral.objects.get(personal_id=self.object)
            labor_form = InfoLaboralPersonalForm(request.POST, instance=info_laboral)
            if labor_form.is_valid():
                labor_form.save()
                messages.success(request, 'Información laboral actualizada exitosamente.')
                return redirect(f"{self.success_url}?tab=labor")
            else:
                return self.form_invalid(labor_form)

    def form_valid(self, form):
        messages.success(self.request, 'Información personal actualizada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar. Por favor revise los datos ingresados.')
        return self.render_to_response(self.get_context_data(form=form))

class PersonalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        personal = get_object_or_404(Personal, pk=pk)
        try:
            personal.delete()
            messages.success(request, 'Personal eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el personal: {str(e)}')
        return redirect('table_personal')


