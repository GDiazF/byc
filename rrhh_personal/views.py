from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PersonalCreationForm, InfoLaboralPersonalForm, LicenciasPersonal, CertificacionPersonal, ExamenPersonal, LicenciaMedicaPorPersonalForm
from django.shortcuts import redirect
from .models import Personal, InfoLaboral, Ausentismo, TipoAusentismo, LicenciaPorPersonal, Certificacion, Examen, Comuna, Cargo, LicenciaMedicaPorPersonal
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
from django.db.models import Q

# Create your views here.

#vista para tabla de personal
class PersonalListView(ListView, LoginRequiredMixin):
    model = Personal
    template_name = 'personal/table_personal.html'
    context_object_name = 'personal'
    # Removido paginate_by para permitir que DataTables maneje la paginación

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
        # Solo mostrar personal ACTIVO
        queryset = Personal.objects.filter(activo=True).prefetch_related(
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
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context
    
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
        
        messages.success(self.request, 'Información personal validada. Por favor complete la información laboral.')
        return redirect('personal_labor_create')

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
        if 'personal_data' not in request.session:
            messages.error(request, 'Por favor complete primero la información personal.')
            return redirect('personal_create')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Recuperar los datos personales de la sesión
                personal_data = self.request.session['personal_data']
                
                # Crear el objeto Personal (sin documentos por ahora)
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

                # Asignar el personal al formulario laboral y guardar
                form.instance.personal_id = personal
                self.object = form.save()

                # Limpiar los datos de la sesión
                if 'personal_data' in self.request.session:
                    del self.request.session['personal_data']
                if 'document_data' in self.request.session:
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
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        if 'labor_form' not in context:
            info_laboral, created = InfoLaboral.objects.get_or_create(personal_id=self.object)
            context['labor_form'] = InfoLaboralPersonalForm(instance=info_laboral)
        
        context['now'] = timezone.now()
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
        messages.error(self.request, 'Error al actualizar el personal. Por favor revise los datos ingresados.')
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
            
            # Validar que solo sea PDF
            if 'rutaDoc' in request.FILES:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
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
                
                # Obtener las clases de licencia
                clase = ', '.join([tipo.tipoLicencia for tipo in licencia.tipos.all()])
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Licencia guardada exitosamente',
                    'data': {
                        'id': licencia.licenciaPorPersonal_id,
                        'numero': '',  # Este modelo no tiene número
                        'municipalidad': '',  # Este modelo no tiene municipalidad
                        'clase': clase,
                        'fecha_emision': licencia.fechaEmision.strftime('%d/%m/%Y'),
                        'fecha_vencimiento': licencia.fechaVencimiento.strftime('%d/%m/%Y'),
                        'documento': True if licencia.rutaDoc else False,
                        'documento_url': licencia.rutaDoc.url if licencia.rutaDoc else None
                    }
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
            
            # Validar que solo sea PDF
            if 'rutaDoc' in request.FILES:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
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
                    'message': 'Examen guardado exitosamente',
                    'data': {
                        'id': examen.examen_id,
                        'tipo': examen.tipoEx_id.tipoExamen if examen.tipoEx_id else '',
                        'resultado': str(examen.resultadoEx_id) if examen.resultadoEx_id else '-',
                        'proveedor': str(examen.proveedor_id) if examen.proveedor_id else '',
                        'fecha_emision': examen.fechaEmision.strftime('%d/%m/%Y'),
                        'fecha_vencimiento': examen.fechaVencimiento.strftime('%d/%m/%Y'),
                        'observacion': examen.observacion or '',
                        'documento': True if examen.rutaDoc else False,
                        'documento_url': examen.rutaDoc.url if examen.rutaDoc else None
                    }
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


# ============================================================================
# VISTAS PARA LICENCIAS INTERNAS DE CONDUCIR
# ============================================================================

@login_required
def add_internal_license(request, personal_id):
    """Vista para agregar licencia interna de conducir"""
    if request.method == 'POST':
        try:
            personal = get_object_or_404(Personal, personal_id=personal_id)
            
            # Validar que solo sea PDF
            if 'rutaDoc' in request.FILES:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
            from .forms import LicenciasInternasPersonal
            form = LicenciasInternasPersonal(request.POST, request.FILES)
            
            if form.is_valid():
                licencia = form.save(commit=False)
                licencia.personal_id = personal
                licencia.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Licencia interna guardada exitosamente',
                    'data': {
                        'id': licencia.licenciaInterna_id,
                        'tipo': licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else '',
                        'numero': licencia.numero_licencia or '-',
                        'empresa': licencia.empresa_emisora or '-',
                        'fecha_emision': licencia.fechaEmision.strftime('%d/%m/%Y'),
                        'fecha_vencimiento': licencia.fechaVencimiento.strftime('%d/%m/%Y'),
                        'activo': licencia.esta_activa,
                        'observacion': licencia.observacion or '',
                        'documento': True if licencia.rutaDoc else False,
                        'documento_url': licencia.rutaDoc.url if licencia.rutaDoc else None
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al procesar la solicitud: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


@login_required
def edit_internal_license(request, license_id):
    """Vista para editar licencia interna de conducir"""
    if request.method == 'GET':
        try:
            from .models import LicenciaInternaPorPersonal
            from .forms import LicenciasInternasPersonal
            license = get_object_or_404(LicenciaInternaPorPersonal, licenciaInterna_id=license_id)
            form = LicenciasInternasPersonal(instance=license)
            
            # Convertir el formulario a HTML
            form_html = form.as_p()
            
            return JsonResponse({
                'status': 'success',
                'form_html': form_html,
                'license_data': {
                    'id': license.licenciaInterna_id,
                    'tipo_id': license.tipoLicenciaInterna_id.tipoLicenciaInterna_id,
                    'tipo_nombre': license.tipoLicenciaInterna_id.tipoLicenciaInterna,
                    'numero': license.numero_licencia,
                    'empresa': license.empresa_emisora,
                    'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                    'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
                    'observacion': license.observacion,
                    'documento_url': license.rutaDoc.url if license.rutaDoc else None,
                    'documento_nombre': license.rutaDoc.name if license.rutaDoc else None
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            from .models import LicenciaInternaPorPersonal
            from .forms import LicenciasInternasPersonal
            license = get_object_or_404(LicenciaInternaPorPersonal, licenciaInterna_id=license_id)
            
            # Validar que solo sea PDF si se sube un nuevo archivo
            if 'rutaDoc' in request.FILES and request.FILES['rutaDoc']:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
            # Crear un formulario personalizado para la edición
            form_data = request.POST.copy()
            form_files = request.FILES
            
            # Si no se subió un nuevo archivo, mantener el existente
            if 'rutaDoc' not in form_files or not form_files['rutaDoc']:
                # Crear un formulario sin el campo de archivo para validar otros campos
                form = LicenciasInternasPersonal(form_data, instance=license)
                # Remover la validación del campo de archivo
                form.fields['rutaDoc'].required = False
                
                if form.is_valid():
                    # Guardar sin tocar el archivo existente
                    license.tipoLicenciaInterna_id = form.cleaned_data['tipoLicenciaInterna_id']
                    license.numero_licencia = form.cleaned_data['numero_licencia']
                    license.empresa_emisora = form.cleaned_data['empresa_emisora']
                    license.fechaEmision = form.cleaned_data['fechaEmision']
                    license.fechaVencimiento = form.cleaned_data['fechaVencimiento']
                    license.observacion = form.cleaned_data['observacion']
                    license.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia interna actualizada exitosamente',
                        'data': {
                            'id': license.licenciaInterna_id,
                            'tipo': license.tipoLicenciaInterna_id.tipoLicenciaInterna if license.tipoLicenciaInterna_id else '',
                            'numero': license.numero_licencia or '-',
                            'empresa': license.empresa_emisora or '-',
                            'fecha_emision': license.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%d/%m/%Y'),
                            'activo': license.esta_activa,
                            'observacion': license.observacion or '',
                            'documento': True if license.rutaDoc else False,
                            'documento_url': license.rutaDoc.url if license.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
            else:
                # Si se subió un nuevo archivo, usar el formulario normal
                form = LicenciasInternasPersonal(form_data, form_files, instance=license)
                
                if form.is_valid():
                    license = form.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia interna actualizada exitosamente',
                        'data': {
                            'id': license.licenciaInterna_id,
                            'tipo': license.tipoLicenciaInterna_id.tipoLicenciaInterna if license.tipoLicenciaInterna_id else '',
                            'numero': license.numero_licencia or '-',
                            'empresa': license.empresa_emisora or '-',
                            'fecha_emision': license.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%d/%m/%Y'),
                            'activo': license.esta_activa,
                            'observacion': license.observacion or '',
                            'documento': True if license.rutaDoc else False,
                            'documento_url': license.rutaDoc.url if license.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al actualizar la licencia: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
def delete_internal_license(request, license_id):
    """Vista para eliminar licencia interna de conducir"""
    if request.method == 'DELETE':
        try:
            from .models import LicenciaInternaPorPersonal
            license = get_object_or_404(LicenciaInternaPorPersonal, licenciaInterna_id=license_id)
            license.delete()
            return JsonResponse({'status': 'success', 'message': 'Licencia interna eliminada exitosamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


# ============================================================================
# VISTAS PARA DOCUMENTOS PERSONALES
# ============================================================================

@login_required
def upload_personal_document(request, personal_id):
    """Vista para subir/actualizar un documento personal individual"""
    if request.method == 'POST':
        try:
            personal = get_object_or_404(Personal, personal_id=personal_id)
            document_field = request.POST.get('document_field')
            document_file = request.FILES.get('document_file')
            
            if not document_field or not document_file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Faltan datos requeridos'
                }, status=400)
            
            # Validar que solo sea PDF
            if not document_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Solo se aceptan archivos PDF'
                }, status=400)
            
            # Validar que el campo exista en el modelo
            valid_fields = [
                'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                'foto_carnet', 'certificado_afp', 'certificado_salud',
                'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                'fotocopia_finiquito', 'comprobante_banco'
            ]
            
            if document_field not in valid_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Campo de documento inválido'
                }, status=400)
            
            # Guardar el documento
            setattr(personal, document_field, document_file)
            personal.save()
            
            # Obtener la URL del documento guardado
            document_url = getattr(personal, document_field).url if getattr(personal, document_field) else None
            
            return JsonResponse({
                'status': 'success',
                'message': 'Documento subido exitosamente',
                'document_url': document_url
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al subir el documento: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


@login_required
def upload_carnet_document(request, personal_id):
    """Vista específica para subir carnet con fecha de vencimiento"""
    if request.method == 'POST':
        try:
            personal = get_object_or_404(Personal, personal_id=personal_id)
            carnet_file = request.FILES.get('carnet_file')
            fecha_vencimiento = request.POST.get('fecha_vencimiento')
            
            if not carnet_file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Debe seleccionar un archivo'
                }, status=400)
            
            # Validar que solo sea PDF
            if not carnet_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Solo se aceptan archivos PDF'
                }, status=400)
            
            if not fecha_vencimiento:
                return JsonResponse({
                    'status': 'error',
                    'message': 'La fecha de vencimiento es obligatoria'
                }, status=400)
            
            # Guardar el archivo del carnet
            personal.fotocopia_carnet = carnet_file
            
            # Guardar la fecha de vencimiento
            from datetime import datetime
            try:
                personal.fecha_vencimiento_carnet = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato de fecha inválido'
                }, status=400)
            
            personal.save()
            
            # Obtener la URL del documento guardado
            document_url = personal.fotocopia_carnet.url if personal.fotocopia_carnet else None
            
            return JsonResponse({
                'status': 'success',
                'message': 'Carnet subido exitosamente',
                'document_url': document_url
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al subir el carnet: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


@login_required
def delete_personal_document(request, personal_id):
    """Vista para eliminar un documento personal individual"""
    if request.method == 'POST':
        try:
            import json
            personal = get_object_or_404(Personal, personal_id=personal_id)
            data = json.loads(request.body)
            document_field = data.get('document_field')
            
            if not document_field:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Falta especificar el documento a eliminar'
                }, status=400)
            
            # Validar que el campo exista
            valid_fields = [
                'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                'foto_carnet', 'certificado_afp', 'certificado_salud',
                'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                'fotocopia_finiquito', 'comprobante_banco'
            ]
            
            if document_field not in valid_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Campo de documento inválido'
                }, status=400)
            
            # Eliminar el archivo físico y limpiar el campo
            field = getattr(personal, document_field)
            if field:
                field.delete(save=False)
                setattr(personal, document_field, None)
                
                # Si es el carnet, también eliminar la fecha de vencimiento
                if document_field == 'fotocopia_carnet':
                    personal.fecha_vencimiento_carnet = None
                
                personal.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Documento eliminado exitosamente'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El documento no existe'
                }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al eliminar el documento: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


@login_required
def documentation_view(request, pk):
    personal = get_object_or_404(Personal, personal_id=pk)
    from .forms import LicenciasInternasPersonal
    from .models import LicenciaInternaPorPersonal
    
    license_form = LicenciasPersonal()
    internal_license_form = LicenciasInternasPersonal()
    exam_form = ExamenPersonal()
    certification_form = CertificacionPersonal()
    
    licencias = LicenciaPorPersonal.objects.filter(personal_id=personal)
    licencias_internas = LicenciaInternaPorPersonal.objects.filter(personal_id=personal)
    examenes = Examen.objects.filter(personal_id=personal)
    certificaciones = Certificacion.objects.filter(personal_id=personal)
    
    context = {
        'personal': personal,
        'license_form': license_form,
        'internal_license_form': internal_license_form,
        'exam_form': exam_form,
        'certification_form': certification_form,
        'licencias': licencias,
        'licencias_internas': licencias_internas,
        'examenes': examenes,
        'certificaciones': certificaciones,
    }
    
    return render(request, 'personal/documentation.html', context)

@login_required
@require_POST
def save_certification(request, pk):
    try:
        personal = get_object_or_404(Personal, personal_id=pk)
        
        # Validar que solo sea PDF
        if 'rutaDoc' in request.FILES:
            document_file = request.FILES['rutaDoc']
            if not document_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Solo se aceptan archivos PDF'
                }, status=400)
        
        form = CertificacionPersonal(request.POST, request.FILES)
        
        if form.is_valid():
            certification = form.save(commit=False)
            certification.personal_id = personal
            certification.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificación guardada exitosamente',
                'data': {
                    'id': certification.certif_id,
                    'tipo': certification.tipoCertificacion_id.tipoCertificacion if certification.tipoCertificacion_id else '',
                    'proveedor': str(certification.proveedor_id) if certification.proveedor_id else '',
                    'fecha_emision': certification.fechaEmision.strftime('%d/%m/%Y'),
                    'fecha_vencimiento': certification.fechaVencimiento.strftime('%d/%m/%Y'),
                    'observacion': certification.observacion or '',
                    'documento': True if certification.rutaDoc else False,
                    'documento_url': certification.rutaDoc.url if certification.rutaDoc else None
                }
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

# Vista para crear una licencia médica por personal
class LicenciaMedicaPorPersonalCreateView(LoginRequiredMixin, CreateView):
    model = LicenciaMedicaPorPersonal
    form_class = LicenciaMedicaPorPersonalForm
    template_name = 'personal/create_licencia_medica.html'

    def get_success_url(self):
        return reverse_lazy('listar_licencias_medicas_personal', kwargs={'personal_id': self.object.personal_id.personal_id})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Quitar el campo personal_id del formulario
        if 'personal_id' in form.fields:
            del form.fields['personal_id']
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el objeto personal al contexto
        personal_id = self.kwargs.get('personal_id')
        context['personal'] = Personal.objects.get(pk=personal_id)
        return context

    def form_valid(self, form):
        personal_id = self.kwargs.get('personal_id')
        form.instance.personal_id = Personal.objects.get(pk=personal_id)
        messages.success(self.request, 'Licencia médica registrada correctamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario. Por favor revise los datos ingresados.')
        return super().form_invalid(form)

# Vista para listar y editar licencias médicas de un personal
@login_required
def listar_licencias_medicas_personal(request, personal_id):
    """Vista mejorada para listar licencias médicas de un personal"""
    personal = get_object_or_404(Personal, personal_id=personal_id)
    licencias_medicas = LicenciaMedicaPorPersonal.objects.filter(
        personal_id=personal
    ).select_related('tipoLicenciaMedica_id').order_by('-fechaEmision')
    
    context = {
        'personal': personal,
        'licencias_medicas': licencias_medicas,
    }
    return render(request, 'personal/listar_licencias_medicas_new.html', context)

# Vista para editar una licencia médica específica
class LicenciaMedicaPorPersonalUpdateView(LoginRequiredMixin, UpdateView):
    model = LicenciaMedicaPorPersonal
    form_class = LicenciaMedicaPorPersonalForm
    template_name = 'personal/edit_licencia_medica.html'

    def get_success_url(self):
        return reverse_lazy('listar_licencias_medicas_personal', kwargs={'personal_id': self.object.personal_id.personal_id})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Quitar el campo personal_id del formulario
        if 'personal_id' in form.fields:
            del form.fields['personal_id']
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el objeto personal al contexto
        context['personal'] = self.object.personal_id
        return context

    def form_valid(self, form):
        # Solo procesar el archivo si se subió uno nuevo
        if 'rutaDoc' in form.files:
            response = super().form_valid(form)
            messages.success(self.request, 'Licencia médica actualizada correctamente.')
        else:
            # Si no se subió archivo, solo guardar los otros campos
            self.object.save()
            messages.success(self.request, 'Licencia médica actualizada correctamente.')
            response = redirect(self.get_success_url())
        
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario. Por favor revise los datos ingresados.')
        return super().form_invalid(form)

@login_required
def delete_licencia_medica(request, licencia_id):
    if request.method == 'DELETE':
        try:
            licencia = get_object_or_404(LicenciaMedicaPorPersonal, licenciaMedicaPorPersonal_id=licencia_id)
            licencia.delete()
            return JsonResponse({'status': 'success', 'message': 'Licencia médica eliminada exitosamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

# ============================================================================
# VISTAS PARA AUSENTISMOS Y PERMISOS
# ============================================================================

@login_required
def buscar_personal_ausentismo(request):
    """Vista para buscar personal para gestionar ausentismos"""
    from gen_settings.models import Empresa
    
    personal_list = Personal.objects.filter(activo=True).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        'ausentismo_set'
    ).order_by('apepat', 'apemat', 'nombre')
    
    empresas = Empresa.objects.all().order_by('nomFantasia')
    
    context = {
        'personal_list': personal_list,
        'empresas': empresas,
    }
    
    return render(request, 'personal/buscar_personal_ausentismo.html', context)


@login_required
def listar_ausentismos_personal(request, personal_id):
    """Vista para listar ausentismos de un personal"""
    personal = get_object_or_404(Personal, personal_id=personal_id)
    ausentismos = Ausentismo.objects.filter(
        personal_id=personal
    ).select_related('tipoausen_id').order_by('-fechaini')
    
    context = {
        'personal': personal,
        'ausentismos': ausentismos,
    }
    
    return render(request, 'personal/listar_ausentismos.html', context)


@login_required
def crear_ausentismo(request, personal_id):
    """Vista para crear un ausentismo"""
    personal = get_object_or_404(Personal, personal_id=personal_id)
    
    if request.method == 'POST':
        from .forms import AusentismoForm
        form = AusentismoForm(request.POST)
        if form.is_valid():
            ausentismo = form.save(commit=False)
            ausentismo.personal_id = personal
            ausentismo.save()
            messages.success(request, 'Ausentismo registrado exitosamente')
            return redirect('listar_ausentismos_personal', personal_id=personal.personal_id)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        from .forms import AusentismoForm
        form = AusentismoForm()
    
    context = {
        'form': form,
        'personal': personal,
    }
    
    return render(request, 'personal/create_ausentismo.html', context)


@login_required
def actualizar_ausentismo(request, personal_id, ausentismo_id):
    """Vista para actualizar un ausentismo"""
    ausentismo = get_object_or_404(Ausentismo, ausentismo_id=ausentismo_id)
    personal = ausentismo.personal_id
    
    if request.method == 'POST':
        from .forms import AusentismoForm
        form = AusentismoForm(request.POST, instance=ausentismo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ausentismo actualizado exitosamente')
            return redirect('listar_ausentismos_personal', personal_id=personal.personal_id)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        from .forms import AusentismoForm
        form = AusentismoForm(instance=ausentismo)
    
    context = {
        'form': form,
        'personal': personal,
        'ausentismo': ausentismo,
    }
    
    return render(request, 'personal/edit_ausentismo.html', context)


@login_required
def eliminar_ausentismo(request, ausentismo_id):
    """Vista para eliminar un ausentismo"""
    if request.method == 'DELETE':
        try:
            ausentismo = get_object_or_404(Ausentismo, ausentismo_id=ausentismo_id)
            ausentismo.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Ausentismo eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def buscar_personal_licencia_medica(request):
    """Vista mejorada para buscar personal para licencias médicas"""
    from gen_settings.models import Empresa
    
    personal_list = Personal.objects.filter(activo=True).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__empresa_id',
        'licenciamedicaporpersonal_set'
    ).order_by('apepat', 'apemat', 'nombre')
    
    empresas = Empresa.objects.all().order_by('nomFantasia')
    
    context = {
        'personal_list': personal_list,
        'empresas': empresas,
    }
    
    return render(request, 'personal/buscar_personal_licencia_medica_new.html', context)


@login_required
def edit_license(request, license_id):
    """Vista para editar licencia de conducir"""
    if request.method == 'GET':
        try:
            from .models import LicenciaPorPersonal
            from .forms import LicenciasPersonal
            license = get_object_or_404(LicenciaPorPersonal, licenciaPorPersonal_id=license_id)
            form = LicenciasPersonal(instance=license)
            
            # Convertir el formulario a HTML
            form_html = form.as_p()
            
            return JsonResponse({
                'status': 'success',
                'form_html': form_html,
                'license_data': {
                    'id': license.licenciaPorPersonal_id,
                    'tipos': [tipo.tipoLicencia_id for tipo in license.tipos.all()],
                    'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                    'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
                    'documento_url': license.rutaDoc.url if license.rutaDoc else None,
                    'documento_nombre': license.rutaDoc.name if license.rutaDoc else None
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            from .models import LicenciaPorPersonal
            from .forms import LicenciasPersonal
            license = get_object_or_404(LicenciaPorPersonal, licenciaPorPersonal_id=license_id)
            
            # Validar que solo sea PDF si se sube un nuevo archivo
            if 'rutaDoc' in request.FILES and request.FILES['rutaDoc']:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
            # Crear un formulario personalizado para la edición
            form_data = request.POST.copy()
            form_files = request.FILES
            
            # Si no se subió un nuevo archivo, mantener el existente
            if 'rutaDoc' not in form_files or not form_files['rutaDoc']:
                # Crear un formulario sin el campo de archivo para validar otros campos
                form = LicenciasPersonal(form_data, instance=license)
                # Remover la validación del campo de archivo
                form.fields['rutaDoc'].required = False
                
                if form.is_valid():
                    # Guardar sin tocar el archivo existente
                    license.fechaEmision = form.cleaned_data['fechaEmision']
                    license.fechaVencimiento = form.cleaned_data['fechaVencimiento']
                    license.tipos.set(form.cleaned_data['tipos'])
                    license.save()
                    
                    # Obtener las clases de licencia
                    clase = ', '.join([tipo.tipoLicencia for tipo in license.tipos.all()])
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia actualizada exitosamente',
                        'data': {
                            'id': license.licenciaPorPersonal_id,
                            'numero': '',  # Este modelo no tiene número
                            'municipalidad': '',  # Este modelo no tiene municipalidad
                            'clase': clase,
                            'fecha_emision': license.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%d/%m/%Y'),
                            'documento': True if license.rutaDoc else False,
                            'documento_url': license.rutaDoc.url if license.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
            else:
                # Si se subió un nuevo archivo, usar el formulario normal
                form = LicenciasPersonal(form_data, form_files, instance=license)
                
                if form.is_valid():
                    license = form.save()
                    
                    # Obtener las clases de licencia
                    clase = ', '.join([tipo.tipoLicencia for tipo in license.tipos.all()])
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia actualizada exitosamente',
                        'data': {
                            'id': license.licenciaPorPersonal_id,
                            'numero': '',  # Este modelo no tiene número
                            'municipalidad': '',  # Este modelo no tiene municipalidad
                            'clase': clase,
                            'fecha_emision': license.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%d/%m/%Y'),
                            'documento': True if license.rutaDoc else False,
                            'documento_url': license.rutaDoc.url if license.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al actualizar la licencia: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
def edit_certification(request, cert_id):
    """Vista para editar certificación"""
    if request.method == 'GET':
        try:
            from .models import Certificacion
            from .forms import CertificacionPersonal
            cert = get_object_or_404(Certificacion, certif_id=cert_id)
            form = CertificacionPersonal(instance=cert)
            
            # Convertir el formulario a HTML
            form_html = form.as_p()
            
            return JsonResponse({
                'status': 'success',
                'form_html': form_html,
                'cert_data': {
                    'id': cert.certif_id,
                    'tipo_id': cert.tipoCertificacion_id.tipoCertificacion_id,
                    'proveedor_id': cert.proveedor_id.proveedor_id,
                    'fecha_emision': cert.fechaEmision.strftime('%Y-%m-%d'),
                    'fecha_vencimiento': cert.fechaVencimiento.strftime('%Y-%m-%d'),
                    'documento_url': cert.rutaDoc.url if cert.rutaDoc else None,
                    'documento_nombre': cert.rutaDoc.name if cert.rutaDoc else None
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            from .models import Certificacion
            from .forms import CertificacionPersonal
            cert = get_object_or_404(Certificacion, certif_id=cert_id)
            
            # Validar que solo sea PDF si se sube un nuevo archivo
            if 'rutaDoc' in request.FILES and request.FILES['rutaDoc']:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
            # Crear un formulario personalizado para la edición
            form_data = request.POST.copy()
            form_files = request.FILES
            
            # Si no se subió un nuevo archivo, mantener el existente
            if 'rutaDoc' not in form_files or not form_files['rutaDoc']:
                # Crear un formulario sin el campo de archivo para validar otros campos
                form = CertificacionPersonal(form_data, instance=cert)
                # Remover la validación del campo de archivo
                form.fields['rutaDoc'].required = False
                
                if form.is_valid():
                    # Guardar sin tocar el archivo existente
                    cert.tipoCertificacion_id = form.cleaned_data['tipoCertificacion_id']
                    cert.proveedor_id = form.cleaned_data['proveedor_id']
                    cert.fechaEmision = form.cleaned_data['fechaEmision']
                    cert.fechaVencimiento = form.cleaned_data['fechaVencimiento']
                    cert.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Certificación actualizada exitosamente',
                        'data': {
                            'id': cert.certif_id,
                            'tipo': cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else '',
                            'proveedor': str(cert.proveedor_id) if cert.proveedor_id else '',
                            'fecha_emision': cert.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
                            'observacion': cert.observacion or '',
                            'documento': True if cert.rutaDoc else False,
                            'documento_url': cert.rutaDoc.url if cert.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
            else:
                # Si se subió un nuevo archivo, usar el formulario normal
                form = CertificacionPersonal(form_data, form_files, instance=cert)
                
                if form.is_valid():
                    cert = form.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Certificación actualizada exitosamente',
                        'data': {
                            'id': cert.certif_id,
                            'tipo': cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else '',
                            'proveedor': str(cert.proveedor_id) if cert.proveedor_id else '',
                            'fecha_emision': cert.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': cert.fechaVencimiento.strftime('%d/%m/%Y'),
                            'observacion': cert.observacion or '',
                            'documento': True if cert.rutaDoc else False,
                            'documento_url': cert.rutaDoc.url if cert.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al actualizar la certificación: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
def edit_exam(request, exam_id):
    """Vista para editar examen"""
    if request.method == 'GET':
        try:
            from .models import Examen
            from .forms import ExamenPersonal
            exam = get_object_or_404(Examen, examen_id=exam_id)
            form = ExamenPersonal(instance=exam)
            
            # Convertir el formulario a HTML
            form_html = form.as_p()
            
            return JsonResponse({
                'status': 'success',
                'form_html': form_html,
                'exam_data': {
                    'id': exam.examen_id,
                    'tipo_id': exam.tipoEx_id.tipoEx_id,
                    'resultado_id': exam.resultadoEx_id.resultadoEx_id,
                    'proveedor_id': exam.proveedor_id.proveedor_id,
                    'fecha_emision': exam.fechaEmision.strftime('%Y-%m-%d'),
                    'fecha_vencimiento': exam.fechaVencimiento.strftime('%Y-%m-%d'),
                    'documento_url': exam.rutaDoc.url if exam.rutaDoc else None,
                    'documento_nombre': exam.rutaDoc.name if exam.rutaDoc else None
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            from .models import Examen
            from .forms import ExamenPersonal
            exam = get_object_or_404(Examen, examen_id=exam_id)
            
            # Validar que solo sea PDF si se sube un nuevo archivo
            if 'rutaDoc' in request.FILES and request.FILES['rutaDoc']:
                document_file = request.FILES['rutaDoc']
                if not document_file.name.lower().endswith('.pdf'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Solo se aceptan archivos PDF'
                    }, status=400)
            
            # Crear un formulario personalizado para la edición
            form_data = request.POST.copy()
            form_files = request.FILES
            
            # Si no se subió un nuevo archivo, mantener el existente
            if 'rutaDoc' not in form_files or not form_files['rutaDoc']:
                # Crear un formulario sin el campo de archivo para validar otros campos
                form = ExamenPersonal(form_data, instance=exam)
                # Remover la validación del campo de archivo
                form.fields['rutaDoc'].required = False
                
                if form.is_valid():
                    # Guardar sin tocar el archivo existente
                    exam.tipoEx_id = form.cleaned_data['tipoEx_id']
                    exam.resultadoEx_id = form.cleaned_data['resultadoEx_id']
                    exam.proveedor_id = form.cleaned_data['proveedor_id']
                    exam.fechaEmision = form.cleaned_data['fechaEmision']
                    exam.fechaVencimiento = form.cleaned_data['fechaVencimiento']
                    exam.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Examen actualizado exitosamente',
                        'data': {
                            'id': exam.examen_id,
                            'tipo': exam.tipoEx_id.tipoExamen if exam.tipoEx_id else '',
                            'resultado': str(exam.resultadoEx_id) if exam.resultadoEx_id else '-',
                            'proveedor': str(exam.proveedor_id) if exam.proveedor_id else '',
                            'fecha_emision': exam.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': exam.fechaVencimiento.strftime('%d/%m/%Y'),
                            'observacion': exam.observacion or '',
                            'documento': True if exam.rutaDoc else False,
                            'documento_url': exam.rutaDoc.url if exam.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
            else:
                # Si se subió un nuevo archivo, usar el formulario normal
                form = ExamenPersonal(form_data, form_files, instance=exam)
                
                if form.is_valid():
                    exam = form.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Examen actualizado exitosamente',
                        'data': {
                            'id': exam.examen_id,
                            'tipo': exam.tipoEx_id.tipoExamen if exam.tipoEx_id else '',
                            'resultado': str(exam.resultadoEx_id) if exam.resultadoEx_id else '-',
                            'proveedor': str(exam.proveedor_id) if exam.proveedor_id else '',
                            'fecha_emision': exam.fechaEmision.strftime('%d/%m/%Y'),
                            'fecha_vencimiento': exam.fechaVencimiento.strftime('%d/%m/%Y'),
                            'observacion': exam.observacion or '',
                            'documento': True if exam.rutaDoc else False,
                            'documento_url': exam.rutaDoc.url if exam.rutaDoc else None
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'errors': form.errors
                    }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al actualizar el examen: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)



# ============================================================================
# VISTA PARA PERSONAL DESACTIVADO
# ============================================================================

class PersonalDesactivadoListView(ListView, LoginRequiredMixin):
    """Vista para listar personal desactivado"""
    model = Personal
    template_name = 'personal/personal_desactivado.html'
    context_object_name = 'personal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from gen_settings.models import Empresa
        context['empresas'] = Empresa.objects.all()
        
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
        queryset = Personal.objects.filter(activo=False).prefetch_related(
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


@login_required
@require_POST
def toggle_personal_activo(request):
    """Toggle estado activo/inactivo de personal"""
    try:
        data = json.loads(request.body)
        personal_id = data.get('personal_id')
        
        personal = get_object_or_404(Personal, personal_id=personal_id)
        personal.activo = not personal.activo
        personal.save()
        
        estado_texto = "activado" if personal.activo else "desactivado"
        
        return JsonResponse({
            'status': 'success',
            'message': f'Personal {estado_texto} correctamente',
            'activo': personal.activo
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
