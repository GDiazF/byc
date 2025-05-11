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
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import os
from django.db import models

# Create your views here.

#vista para tabla de personal
class PersonalListView(ListView, LoginRequiredMixin):
    model = Personal
    template_name = 'personal/table_personal.html'
    context_object_name = 'personal'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from gen_settings.models import Empresa
        context['empresas'] = Empresa.objects.all()
        
        # Obtener y procesar empresa_id
        empresa_id = self.request.GET.get('empresa')
        if empresa_id and empresa_id.strip():
            try:
                context['empresa_seleccionada'] = int(empresa_id)
            except (ValueError, TypeError):
                context['empresa_seleccionada'] = None
        else:
            context['empresa_seleccionada'] = None
        
        return context

    def get_queryset(self):
        queryset = Personal.objects.prefetch_related(
            'infolaboral_set__cargo_id',
            'infolaboral_set__depto_id',
            'infolaboral_set__empresa_id'
        )
        
        empresa_id = self.request.GET.get('empresa')
        if empresa_id and empresa_id.strip():
            try:
                empresa_id = int(empresa_id)
                queryset = queryset.filter(infolaboral_set__empresa_id=empresa_id)
            except (ValueError, TypeError):
                pass
        
        return queryset.distinct()

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

@login_required
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
            info_laboral, created = InfoLaboral.objects.get_or_create(personal_id=self.object)
            context['labor_form'] = InfoLaboralPersonalForm(instance=info_laboral)
        
        # Agregar documentos del personal al contexto
        personal_docs = {
            'curriculum': self.object.curriculum if self.object.curriculum else None,
            'certificado_antecedentes': self.object.certificado_antecedentes if self.object.certificado_antecedentes else None,
            'hoja_vida_conductor': self.object.hoja_vida_conductor if self.object.hoja_vida_conductor else None,
            'foto_carnet': self.object.foto_carnet if self.object.foto_carnet else None,
            'certificado_afp': self.object.certificado_afp if self.object.certificado_afp else None,
            'certificado_salud': self.object.certificado_salud if self.object.certificado_salud else None,
            'certificado_estudios': self.object.certificado_estudios if self.object.certificado_estudios else None,
            'certificado_residencia': self.object.certificado_residencia if self.object.certificado_residencia else None,
            'fotocopia_carnet': self.object.fotocopia_carnet if self.object.fotocopia_carnet else None,
            'fotocopia_finiquito': self.object.fotocopia_finiquito if self.object.fotocopia_finiquito else None,
            'comprobante_banco': self.object.comprobante_banco if self.object.comprobante_banco else None,
        }
        context['personal_docs'] = personal_docs
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_type = request.POST.get('form_type', 'personal')
        
        if form_type == 'personal':
            form = self.get_form()
            if form.is_valid():
                response = self.form_valid(form)
                messages.success(request, 'Información personal actualizada exitosamente.')
                return redirect(f"{request.path}?tab=personal")
            else:
                return self.form_invalid(form)
        
        elif form_type == 'documents':
            try:
                personal = self.object
                document_fields = [
                    'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                    'foto_carnet', 'certificado_afp', 'certificado_salud',
                    'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                    'fotocopia_finiquito', 'comprobante_banco'
                ]
                
                # Guardar cada archivo subido
                for field in document_fields:
                    if field in request.FILES:
                        # Eliminar archivo anterior si existe
                        old_file = getattr(personal, field)
                        if old_file:
                            try:
                                if os.path.isfile(old_file.path):
                                    os.remove(old_file.path)
                            except Exception as e:
                                print(f"Error al eliminar archivo anterior: {e}")

                        # Guardar nuevo archivo
                        file_obj = request.FILES[field]
                        setattr(personal, field, file_obj)
                
                personal.save()
                messages.success(request, 'Documentación actualizada exitosamente.')
                return redirect(f"{request.path}?tab=documents")
            except Exception as e:
                messages.error(request, f'Error al guardar documentos: {str(e)}')
                return self.render_to_response(self.get_context_data(form=self.get_form()))

        elif form_type == 'delete_document':
            try:
                personal = self.object
                field = request.POST.get('field')
                
                if field in [f.name for f in personal._meta.fields if isinstance(f, (models.FileField, models.ImageField))]:
                    # Obtener el archivo actual
                    current_file = getattr(personal, field)
                    if current_file:
                        # Eliminar el archivo físico
                        try:
                            if os.path.isfile(current_file.path):
                                os.remove(current_file.path)
                        except Exception as e:
                            print(f"Error al eliminar archivo físico: {e}")
                        
                        # Limpiar el campo en la base de datos
                        setattr(personal, field, None)
                        personal.save()
                        
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Documento eliminado exitosamente'
                        })
                    
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se encontró el documento'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        elif form_type == 'labor':
            info_laboral = InfoLaboral.objects.get(personal_id=self.object)
            labor_form = InfoLaboralPersonalForm(request.POST, instance=info_laboral)
            if labor_form.is_valid():
                labor_form.save()
                messages.success(request, 'Información laboral actualizada exitosamente.')
                return redirect(f"{request.path}?tab=labor")
            else:
                return self.form_invalid(labor_form)

    def form_valid(self, form):
        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
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

@login_required
@require_POST
def toggle_personal_status(request, pk):
    try:
        personal = get_object_or_404(Personal, pk=pk)
        personal.activo = request.POST.get('activo') == 'true'
        personal.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def personal_documentation(request, personal_id):
    personal = get_object_or_404(Personal, personal_id=personal_id)
    licencias = LicenciaPorPersonal.objects.filter(personal_id=personal)
    examenes = Examen.objects.filter(personal_id=personal)
    
    license_form = LicenciasPersonal()
    exam_form = ExamenPersonal()
    
    context = {
        'personal': personal,
        'licencias': licencias,
        'examenes': examenes,
        'license_form': license_form,
        'exam_form': exam_form,
    }
    
    return render(request, 'personal/documentation.html', context)

@login_required
def add_license(request, personal_id):
    if request.method == 'POST':
        try:
            personal = get_object_or_404(Personal, personal_id=personal_id)
            form = LicenciasPersonal(request.POST, request.FILES)
            print("Form data:", request.POST)  # Debug print
            print("Files:", request.FILES)     # Debug print
            
            if form.is_valid():
                print("Form is valid")         # Debug print
                print("Cleaned data:", form.cleaned_data)  # Debug print
                
                licencia = form.save(commit=False)
                licencia.personal_id = personal
                licencia.save()
                form.save_m2m()  # Importante: guardar las relaciones many-to-many
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Licencia guardada exitosamente'
                })
            else:
                print("Form errors:", form.errors)  # Debug print
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            print("Exception:", str(e))  # Debug print
            return JsonResponse({
                'status': 'error',
                'message': f'Error al procesar la solicitud: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)

@login_required
def add_exam(request, personal_id):
    if request.method == 'POST':
        try:
            personal = get_object_or_404(Personal, personal_id=personal_id)
            form = ExamenPersonal(request.POST, request.FILES)
            print("Form data:", request.POST)  # Debug print
            print("Files:", request.FILES)     # Debug print
            
            if form.is_valid():
                print("Form is valid")         # Debug print
                print("Cleaned data:", form.cleaned_data)  # Debug print
                
                examen = form.save(commit=False)
                examen.personal_id = personal
                examen.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Examen guardado exitosamente'
                })
            else:
                print("Form errors:", form.errors)  # Debug print
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            print("Exception:", str(e))  # Debug print
            return JsonResponse({
                'status': 'error',
                'message': f'Error al procesar la solicitud: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)

@login_required
def delete_exam(request, exam_id):
    if request.method == 'DELETE':
        try:
            exam = get_object_or_404(Examen, examen_id=exam_id)
            exam.delete()
            return JsonResponse({'status': 'success', 'message': 'Examen eliminado exitosamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def delete_license(request, license_id):
    if request.method == 'DELETE':
        try:
            license = get_object_or_404(LicenciaPorPersonal, licenciaPorPersonal_id=license_id)
            license.delete()
            return JsonResponse({'status': 'success', 'message': 'Licencia eliminada exitosamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def documentation_view(request, pk):
    personal = get_object_or_404(Personal, personal_id=pk)
    license_form = LicenciasPersonal()
    exam_form = ExamenPersonal()
    certification_form = CertificacionPersonal()
    
    licencias = LicenciaPorPersonal.objects.filter(personal_id=personal)
    examenes = Examen.objects.filter(personal_id=personal)
    certificaciones = Certificacion.objects.filter(personal_id=personal)
    
    context = {
        'personal': personal,
        'license_form': license_form,
        'exam_form': exam_form,
        'certification_form': certification_form,
        'licencias': licencias,
        'examenes': examenes,
        'certificaciones': certificaciones,
    }
    
    return render(request, 'personal/documentation.html', context)

@login_required
@require_POST
def save_certification(request, pk):
    try:
        personal = get_object_or_404(Personal, personal_id=pk)
        form = CertificacionPersonal(request.POST, request.FILES)
        
        if form.is_valid():
            certification = form.save(commit=False)
            certification.personal_id = personal
            certification.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificación guardada exitosamente'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formulario',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def delete_certification(request, pk, certification_id):
    try:
        certification = get_object_or_404(Certificacion, certif_id=certification_id, personal_id__personal_id=pk)
        certification.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Certificación eliminada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


