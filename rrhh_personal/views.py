"""
Vistas Django para la gestión de personal y documentos relacionados.

Este módulo contiene todas las vistas (clases y funciones) para:
- Listar, crear, editar y eliminar personal
- Gestionar documentos personales (licencias, certificaciones, exámenes)
- Gestionar ausentismos y licencias médicas
- APIs para historial y consultas
- Descarga de documentación en ZIP
"""
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
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
import base64
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import os
from django.db import models
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import HistorialPersonal, HistorialDocumentoPersonal
# Importar decoradores de permisos desde gen_permissions
from gen_permissions.decorators import permission_required_custom, permission_required_multiple
from gen_permissions.mixins import PermissionRequiredMixin
import zipfile
import tempfile
from django.conf import settings
from datetime import datetime

# Create your views here.

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def obtener_nombre_completo_usuario(usuario):
    """
    Obtiene el nombre completo de un usuario o retorna el username como fallback.
    
    Intenta obtener el nombre completo desde first_name y last_name del modelo User.
    Si no está disponible, usa el username. Si no hay usuario, retorna 'Sistema'.
    
    Args:
        usuario: Instancia del modelo User de Django
        
    Returns:
        str: Nombre completo del usuario, username, o 'Sistema' si no hay usuario
    """
    if not usuario:
        return 'Sistema'
    
    # Intentar obtener nombre completo desde el modelo User
    if hasattr(usuario, 'first_name') and hasattr(usuario, 'last_name'):
        nombre_completo = f"{usuario.first_name} {usuario.last_name}".strip()
        if nombre_completo:
            return nombre_completo
    
    # Fallback: usar username si está disponible
    return usuario.username if usuario.username else 'Sistema'

def obtener_url_archivo_historial(evento, personal):
    """
    Obtiene la URL del archivo del historial si existe.
    
    Busca el archivo en diferentes ubicaciones según el tipo de documento:
    - Archivos eliminados: en la carpeta Documentacion_Eliminada
    - Documentos personales: en los campos del modelo Personal
    - Licencias, certificaciones, exámenes: en los modelos correspondientes
    
    Args:
        evento: Instancia de HistorialDocumentoPersonal
        personal: Instancia del modelo Personal
        
    Returns:
        str: URL del archivo si existe, None si no se encuentra
    """
    if not evento.archivo_ruta:
        return None
    
    try:
        from django.conf import settings
        
        # Si el archivo está en la carpeta de eliminados, construir URL directamente
        if evento.archivo_ruta.startswith('Documentacion_Eliminada/'):
            ruta_completa = os.path.join(settings.MEDIA_ROOT, evento.archivo_ruta)
            if os.path.exists(ruta_completa):
                # Construir URL relativa desde MEDIA_URL
                url_relativa = evento.archivo_ruta.replace('\\', '/')
                return os.path.join(settings.MEDIA_URL.rstrip('/'), url_relativa).replace('\\', '/')
        
        # Para documentos personales, verificar si está en el campo actual del modelo Personal
        if evento.campo_documento:
            campo_actual = getattr(personal, evento.campo_documento, None)
            if campo_actual and campo_actual.name == evento.archivo_ruta:
                return campo_actual.url
        
        # Para otros tipos de documentos (licencias, certificaciones, exámenes)
        # Buscar en los modelos correspondientes usando archivo_ruta
        if evento.tipo_documento == 'LICENCIA_CONDUCIR':
            from .models import LicenciaPorPersonal
            licencia = LicenciaPorPersonal.objects.filter(
                personal_id=personal,
                rutaDoc__isnull=False
            ).exclude(rutaDoc='').first()
            if licencia and licencia.rutaDoc.name == evento.archivo_ruta:
                return licencia.rutaDoc.url
        
        elif evento.tipo_documento == 'LICENCIA_INTERNA':
            from .models import LicenciaInternaPorPersonal
            licencia = LicenciaInternaPorPersonal.objects.filter(
                personal_id=personal,
                rutaDoc__isnull=False
            ).exclude(rutaDoc='').first()
            if licencia and licencia.rutaDoc.name == evento.archivo_ruta:
                return licencia.rutaDoc.url
        
        elif evento.tipo_documento == 'CERTIFICACION':
            from .models import Certificacion
            cert = Certificacion.objects.filter(
                personal_id=personal,
                rutaDoc__isnull=False
            ).exclude(rutaDoc='').first()
            if cert and cert.rutaDoc.name == evento.archivo_ruta:
                return cert.rutaDoc.url
        
        elif evento.tipo_documento == 'EXAMEN':
            from .models import Examen
            examen = Examen.objects.filter(
                personal_id=personal,
                rutaDoc__isnull=False
            ).exclude(rutaDoc='').first()
            if examen and examen.rutaDoc.name == evento.archivo_ruta:
                return examen.rutaDoc.url
        
        # Si no se encuentra, el archivo fue eliminado o reemplazado
        return None
    except Exception as e:
        print(f"Error en obtener_url_archivo_historial: {str(e)}")
        return None

# ============================================================================
# VISTAS PRINCIPALES DE PERSONAL
# ============================================================================

class PersonalListView(PermissionRequiredMixin, ListView, LoginRequiredMixin):
    """
    Vista para listar el personal activo en formato de tabla.
    
    Requiere permiso 'rrhh_personal.view_personal'.
    Optimiza las consultas usando prefetch_related para evitar N+1 queries.
    Proporciona datos en JSON para DataTables y permisos del usuario.
    """
    model = Personal
    template_name = 'personal/table_personal.html'
    context_object_name = 'personal'
    # Permiso requerido: ver personal
    permission_required = 'rrhh_personal.view_personal'
    # Removido paginate_by para permitir que DataTables maneje la paginación

    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto de la vista.
        
        Incluye:
        - Lista de empresas para filtros
        - Datos del personal en formato JSON para DataTables
        - Permisos del usuario en formato JSON
        - Empresa seleccionada desde parámetros GET
        
        Returns:
            dict: Contexto con todos los datos necesarios para el template
        """
        context = super().get_context_data(**kwargs)
        from gen_settings.models import Empresa
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        # Obtener todas las empresas para el filtro
        context['empresas'] = Empresa.objects.all()
        
        # Preparar datos del personal para JSON - optimizado para evitar N+1 queries
        # El queryset ya tiene prefetch_related, así que las relaciones están en memoria
        personal_data = []
        for persona in context['personal']:
            # Acceder a la primera info laboral desde el prefetch (ya está en memoria)
            info_laboral = next(iter(persona.infolaboral_set.all()), None)
            personal_data.append({
                'id': persona.personal_id,
                'rut': f"{persona.rut}-{persona.dvrut}",
                'nombre': f"{persona.nombre} {persona.apepat} {persona.apemat}",
                'cargo': info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'No disponible',
                'departamento': info_laboral.depto_id.depto if info_laboral and info_laboral.depto_id else 'No disponible',
                'empresa': info_laboral.empresa_id.nomFantasia if info_laboral and info_laboral.empresa_id else 'No disponible',
                'activo': persona.activo
            })
        
        # Convertir a JSON para usar en JavaScript (DataTables)
        context['personal_json'] = json.dumps(personal_data, cls=DjangoJSONEncoder)
        
        # Verificar permisos del usuario para pasar al template
        # Esto permite mostrar/ocultar botones según los permisos del usuario
        user = self.request.user
        permisos = {
            'can_add_personal': user.has_perm('rrhh_personal.add_personal'),
            'can_change_personal': user.has_perm('rrhh_personal.change_personal'),
            'can_view_personal': user.has_perm('rrhh_personal.view_personal'),
            'can_desactivar_personal': user.has_perm('rrhh_personal.desactivar_personal'),
            'can_activar_personal': user.has_perm('rrhh_personal.activar_personal'),
            'can_ver_historial_personal': user.has_perm('rrhh_personal.ver_historial_personal'),
            # Permisos para documentación (si tiene alguno de estos, puede ver documentación)
            'can_view_documentation': (
                user.has_perm('rrhh_personal.view_personal') or
                user.has_perm('rrhh_personal.change_personal') or
                user.has_perm('rrhh_personal.add_licenciaporpersonal') or
                user.has_perm('rrhh_personal.change_licenciaporpersonal') or
                user.has_perm('rrhh_personal.add_examen') or
                user.has_perm('rrhh_personal.change_examen')
            ),
        }
        context['permisos_json'] = json.dumps(permisos)
        
        # Obtener y procesar empresa_id desde parámetros GET (para filtros)
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
        """
        Obtiene el queryset de personal activo con optimizaciones.
        
        Filtra solo personal activo y usa prefetch_related para cargar
        relaciones de información laboral en una sola consulta adicional.
        Opcionalmente filtra por empresa si se proporciona en GET.
        
        Returns:
            QuerySet: QuerySet optimizado de Personal activo
        """
        # Solo mostrar personal ACTIVO
        # Usar prefetch_related para evitar N+1 queries al acceder a info laboral
        queryset = Personal.objects.filter(activo=True).prefetch_related(
            'infolaboral_set__cargo_id',
            'infolaboral_set__depto_id',
            'infolaboral_set__empresa_id'
        )
        
        # Filtrar por empresa si se proporciona en los parámetros GET
        empresa_id = self.request.GET.get('empresa')
        if empresa_id and empresa_id.strip():
            try:
                empresa_id = int(empresa_id)
                queryset = queryset.filter(infolaboral_set__empresa_id=empresa_id)
            except (ValueError, TypeError):
                pass
        
        return queryset.distinct()

class PersonalCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """
    Vista para crear nuevo personal.
    
    Requiere permiso 'rrhh_personal.add_personal'.
    Crea el personal y su información laboral en una transacción atómica.
    Los documentos personales se pueden agregar después de la creación.
    """
    # Permiso requerido: agregar personal
    permission_required = 'rrhh_personal.add_personal'
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
        # Agregar formulario de información laboral
        if 'labor_form' not in context:
            context['labor_form'] = InfoLaboralPersonalForm()
        return context
    
    def form_valid(self, form):
        """
        Valida y guarda el personal junto con su información laboral.
        
        Primero valida el formulario de información laboral.
        Si ambos formularios son válidos, guarda todo en una transacción atómica.
        Establece el usuario actual para las señales de historial.
        
        Args:
            form: Formulario de creación de personal validado
            
        Returns:
            HttpResponseRedirect: Redirección a la lista de personal si es exitoso
            HttpResponse: Renderizado del formulario con errores si falla
        """
        # PRIMERO validar el formulario laboral ANTES de guardar nada
        labor_form = InfoLaboralPersonalForm(self.request.POST)
        
        if not labor_form.is_valid():
            # Si la info laboral no es válida, NO crear el personal
            # Mostrar errores específicos del formulario laboral
            errores_labor = []
            for field, errors in labor_form.errors.items():
                field_label = labor_form.fields[field].label if field in labor_form.fields else field
                for error in errors:
                    errores_labor.append(f"{field_label}: {error}")
            
            error_msg = 'Error en la información laboral: ' + '; '.join(errores_labor)
            messages.error(self.request, error_msg)
            
            context = self.get_context_data(form=form)
            context['labor_form'] = labor_form  # Pasar el formulario con errores
            return self.render_to_response(context)
        
        # Si ambos formularios son válidos, guardar en transacción atómica
        # Esto asegura que si falla algo, no se guarde nada
        try:
            with transaction.atomic():
                # Guardar el personal primero
                self.object = form.save(commit=False)
                # Pasar usuario a la señal para registrar en historial
                self.object._current_user = self.request.user
                self.object.save()
                
                # Guardar información laboral asociada
                info_laboral = labor_form.save(commit=False)
                info_laboral.personal_id = self.object
                info_laboral.save()
                
                messages.success(
                    self.request, 
                    f'Personal {self.object.nombre} {self.object.apepat} creado exitosamente con su información laboral.'
                )
                
                return redirect('table_personal')
        except Exception as e:
            messages.error(self.request, f'Error al crear el personal: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Mostrar errores específicos del formulario principal
        errores = []
        for field, errors in form.errors.items():
            field_label = form.fields[field].label if field in form.fields else field
            for error in errors:
                errores.append(f"{field_label}: {error}")
        
        if errores:
            error_msg = 'Errores en el formulario: ' + '; '.join(errores)
        else:
            error_msg = 'Error en el formulario. Por favor revise los datos ingresados.'
        
        messages.error(self.request, error_msg)
        context = self.get_context_data(form=form)
        context['labor_form'] = InfoLaboralPersonalForm(self.request.POST)
        return self.render_to_response(context)

@login_required
def get_cargos(request):
    """
    Vista AJAX para obtener cargos por departamento.
    
    Utilizada para poblar dinámicamente el campo de cargos
    cuando se selecciona un departamento en el formulario.
    
    Args:
        request: HttpRequest con parámetro GET 'depto_id'
        
    Returns:
        JsonResponse: Diccionario con cargo_id como clave y cargo como valor
    """
    depto_id = request.GET.get('depto_id')
    cargos = Cargo.objects.filter(depto_id=depto_id).values_list('cargo_id', 'cargo')
    return JsonResponse(dict(cargos))

class PersonalUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Vista para editar personal existente.
    
    Requiere permiso 'rrhh_personal.change_personal'.
    Permite editar información personal y laboral.
    Establece el usuario actual para las señales de historial.
    """
    # Permiso requerido: cambiar personal
    permission_required = 'rrhh_personal.change_personal'
    model = Personal
    form_class = PersonalCreationForm
    template_name = 'personal/edit_personal.html'
    success_url = reverse_lazy('table_personal')

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        if 'labor_form' not in context:
            try:
                info_laboral = InfoLaboral.objects.get(personal_id=self.object)
                context['labor_form'] = InfoLaboralPersonalForm(instance=info_laboral)
            except InfoLaboral.DoesNotExist:
                # Si no existe info laboral, crear formulario vacío
                context['labor_form'] = InfoLaboralPersonalForm()
        
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
            # Obtener o crear InfoLaboral
            info_laboral, created = InfoLaboral.objects.get_or_create(personal_id=self.object)
            labor_form = InfoLaboralPersonalForm(request.POST, instance=info_laboral)
            
            if labor_form.is_valid():
                info_laboral = labor_form.save(commit=False)
                info_laboral.personal_id = self.object
                info_laboral.save()
                messages.success(request, 'Información laboral actualizada exitosamente.')
                return redirect(f"{request.path}?tab=labor")
            else:
                messages.error(request, 'Error en la información laboral. Por favor revise los datos.')
                context = self.get_context_data()
                context['labor_form'] = labor_form
                return self.render_to_response(context)

    def form_valid(self, form):
        # Pasar usuario a la señal
        self.object = form.save(commit=False)
        self.object._current_user = self.request.user
        self.object.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el personal. Por favor revise los datos ingresados.')
        return self.render_to_response(self.get_context_data(form=form))

class PersonalDeleteView(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Vista para eliminar personal.
    
    Requiere permiso 'rrhh_personal.delete_personal'.
    Establece el usuario actual para las señales de historial.
    """
    # Permiso requerido: eliminar personal
    permission_required = 'rrhh_personal.delete_personal'
    
    def post(self, request, pk):
        """
        Elimina el personal especificado.
        
        Args:
            request: HttpRequest
            pk: ID del personal a eliminar
            
        Returns:
            HttpResponseRedirect: Redirección a la lista de personal
        """
        personal = get_object_or_404(Personal, pk=pk)
        try:
            # Pasar usuario a la señal para registrar en historial
            personal._current_user = request.user
            personal.delete()
            messages.success(request, 'Personal eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el personal: {str(e)}')
        return redirect('table_personal')

@login_required
@require_POST
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def toggle_personal_status(request, pk):
    """
    Vista AJAX para cambiar el estado activo/inactivo del personal.
    
    Args:
        request: HttpRequest con POST 'activo' ('true' o 'false')
        pk: ID del personal
        
    Returns:
        JsonResponse: {'success': True/False, 'error': mensaje si hay error}
    """
    try:
        personal = get_object_or_404(Personal, pk=pk)
        personal.activo = request.POST.get('activo') == 'true'
        personal.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required_custom('rrhh_personal.view_personal')
def personal_documentation(request, personal_id):
    """
    Vista para mostrar y gestionar la documentación del personal.
    
    Muestra todos los documentos, licencias, certificaciones y exámenes
    asociados al personal, y permite agregar nuevos.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del template de documentación
    """
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def add_license(request, personal_id):
    """
    Vista para agregar una licencia de conducir al personal.
    
    Args:
        request: HttpRequest con datos del formulario
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                licencia._current_user = request.user
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
                        'fecha_emision': licencia.fechaEmision.strftime('%Y-%m-%d'),
                        'fecha_vencimiento': licencia.fechaVencimiento.strftime('%Y-%m-%d'),
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def add_exam(request, personal_id):
    """
    Vista para agregar un examen médico al personal.
    
    Args:
        request: HttpRequest con datos del formulario
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                examen._current_user = request.user
                examen.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Examen guardado exitosamente',
                    'data': {
                        'id': examen.examen_id,
                        'tipo': examen.tipoEx_id.tipoExamen if examen.tipoEx_id else '',
                        'resultado': str(examen.resultadoEx_id) if examen.resultadoEx_id else '-',
                        'proveedor': str(examen.proveedor_id) if examen.proveedor_id else '',
                        'fecha_emision': examen.fechaEmision.strftime('%Y-%m-%d'),
                        'fecha_vencimiento': examen.fechaVencimiento.strftime('%Y-%m-%d'),
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def delete_exam(request, exam_id):
    """
    Vista para eliminar un examen médico.
    
    Args:
        request: HttpRequest
        exam_id: ID del examen a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la documentación del personal
    """
    if request.method == 'DELETE':
        try:
            exam = get_object_or_404(Examen, examen_id=exam_id)
            exam._current_user = request.user
            exam.delete()
            return JsonResponse({'status': 'success', 'message': 'Examen eliminado exitosamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def delete_license(request, license_id):
    """
    Vista para eliminar una licencia de conducir.
    
    Args:
        request: HttpRequest
        license_id: ID de la licencia a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la documentación del personal
    """
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def add_internal_license(request, personal_id):
    """
    Vista para agregar una licencia interna de conducir al personal.
    
    Args:
        request: HttpRequest con datos del formulario
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                licencia._current_user = request.user
                licencia.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Licencia interna guardada exitosamente',
                    'data': {
                        'id': licencia.licenciaInterna_id,
                        'tipo': licencia.tipoLicenciaInterna_id.tipoLicenciaInterna if licencia.tipoLicenciaInterna_id else '',
                        'numero': licencia.numero_licencia or '-',
                        'empresa': licencia.empresa_emisora or '-',
                        'fecha_emision': licencia.fechaEmision.strftime('%Y-%m-%d'),
                        'fecha_vencimiento': licencia.fechaVencimiento.strftime('%Y-%m-%d'),
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def edit_internal_license(request, license_id):
    """
    Vista para editar una licencia interna de conducir existente.
    
    Args:
        request: HttpRequest con datos del formulario
        license_id: ID de la licencia interna a editar
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                    license._current_user = request.user
                    license.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia interna actualizada exitosamente',
                        'data': {
                            'id': license.licenciaInterna_id,
                            'tipo': license.tipoLicenciaInterna_id.tipoLicenciaInterna if license.tipoLicenciaInterna_id else '',
                            'numero': license.numero_licencia or '-',
                            'empresa': license.empresa_emisora or '-',
                            'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
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
                    license = form.save(commit=False)
                    license._current_user = request.user
                    license.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Licencia interna actualizada exitosamente',
                        'data': {
                            'id': license.licenciaInterna_id,
                            'tipo': license.tipoLicenciaInterna_id.tipoLicenciaInterna if license.tipoLicenciaInterna_id else '',
                            'numero': license.numero_licencia or '-',
                            'empresa': license.empresa_emisora or '-',
                            'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
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
    """
    Vista para eliminar una licencia interna de conducir.
    
    Args:
        request: HttpRequest
        license_id: ID de la licencia interna a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la documentación del personal
    """
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
    """
    Vista para subir un documento personal (AJAX).
    
    Permite subir documentos personales como curriculum, certificados, etc.
    Valida el tipo de archivo y mueve archivos antiguos a la carpeta de eliminados.
    
    Args:
        request: HttpRequest con archivo en POST
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Resultado de la operación
    """
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
            
            # Verificar si ya existe un documento (para saber si es nuevo o reemplazo)
            documento_anterior = getattr(personal, document_field)
            archivo_anterior_ruta = documento_anterior.name if documento_anterior else None
            
            # Guardar el documento
            setattr(personal, document_field, document_file)
            personal.save()
            
            # Obtener la URL del documento guardado
            document_url = getattr(personal, document_field).url if getattr(personal, document_field) else None
            
            # Registrar en historial
            nombres_documentos = {
                'curriculum': 'Curriculum Vitae',
                'certificado_antecedentes': 'Certificado de Antecedentes',
                'hoja_vida_conductor': 'Hoja de Vida del Conductor',
                'foto_carnet': 'Foto Carnet',
                'certificado_afp': 'Certificado AFP',
                'certificado_salud': 'Certificado de Salud',
                'certificado_estudios': 'Certificado de Estudios',
                'certificado_residencia': 'Certificado de Residencia',
                'fotocopia_carnet': 'Fotocopia Carnet',
                'fotocopia_finiquito': 'Fotocopia Finiquito',
                'comprobante_banco': 'Comprobante Banco'
            }
            nombre_doc = nombres_documentos.get(document_field, document_field)
            
            if archivo_anterior_ruta:
                # Es un reemplazo
                HistorialDocumentoPersonal.registrar(
                    personal=personal,
                    tipo_documento='DOCUMENTO_PERSONAL',
                    accion='DOCUMENTO_REEMPLAZADO',
                    nombre_documento=nombre_doc,
                    descripcion=f"Documento {nombre_doc} reemplazado",
                    usuario=request.user,
                    campo_documento=document_field,
                    archivo_ruta=document_file.name,
                    datos_previos={'archivo_anterior': archivo_anterior_ruta},
                    datos_nuevos={'archivo_nuevo': document_file.name}
                )
            else:
                # Es nuevo
                HistorialDocumentoPersonal.registrar(
                    personal=personal,
                    tipo_documento='DOCUMENTO_PERSONAL',
                    accion='DOCUMENTO_AGREGADO',
                    nombre_documento=nombre_doc,
                    descripcion=f"Documento {nombre_doc} agregado",
                    usuario=request.user,
                    campo_documento=document_field,
                    archivo_ruta=document_file.name,
                    datos_nuevos={'archivo': document_file.name}
                )
            
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
    """
    Vista para subir documento de carnet con validación especial.
    
    Valida que el archivo sea una imagen y actualiza la fecha de vencimiento
    del carnet si se proporciona.
    
    Args:
        request: HttpRequest con archivo y fecha de vencimiento en POST
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Resultado de la operación
    """
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
            
            # Verificar si ya existe un documento (para saber si es nuevo o reemplazo)
            archivo_anterior_ruta = personal.fotocopia_carnet.name if personal.fotocopia_carnet else None
            
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
            
            # Registrar en historial
            from .models import HistorialDocumentoPersonal
            if archivo_anterior_ruta:
                # Es un reemplazo
                HistorialDocumentoPersonal.registrar(
                    personal=personal,
                    tipo_documento='DOCUMENTO_PERSONAL',
                    accion='DOCUMENTO_REEMPLAZADO',
                    nombre_documento='Fotocopia Carnet',
                    descripcion=f"Fotocopia Carnet reemplazada. Fecha de vencimiento: {fecha_vencimiento}",
                    usuario=request.user,
                    campo_documento='fotocopia_carnet',
                    archivo_ruta=carnet_file.name,
                    datos_previos={'archivo_anterior': archivo_anterior_ruta},
                    datos_nuevos={'archivo_nuevo': carnet_file.name, 'fecha_vencimiento': fecha_vencimiento}
                )
            else:
                # Es nuevo
                HistorialDocumentoPersonal.registrar(
                    personal=personal,
                    tipo_documento='DOCUMENTO_PERSONAL',
                    accion='DOCUMENTO_AGREGADO',
                    nombre_documento='Fotocopia Carnet',
                    descripcion=f"Fotocopia Carnet agregada. Fecha de vencimiento: {fecha_vencimiento}",
                    usuario=request.user,
                    campo_documento='fotocopia_carnet',
                    archivo_ruta=carnet_file.name,
                    datos_nuevos={'archivo': carnet_file.name, 'fecha_vencimiento': fecha_vencimiento}
                )
            
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
    """
    Vista para eliminar un documento personal (AJAX).
    
    Mueve el archivo a la carpeta de eliminados en lugar de borrarlo físicamente,
    y registra la acción en el historial.
    
    Args:
        request: HttpRequest con nombre del campo del documento en POST
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Resultado de la operación
    """
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
            
            # Mover el archivo a carpeta de eliminados en lugar de eliminarlo
            field = getattr(personal, document_field)
            if field:
                archivo_ruta_original = field.name  # Guardar ruta original
                
                # Nombres de documentos para la carpeta de eliminados
                nombres_documentos = {
                    'curriculum': 'Curriculum Vitae',
                    'certificado_antecedentes': 'Certificado de Antecedentes',
                    'hoja_vida_conductor': 'Hoja de Vida del Conductor',
                    'foto_carnet': 'Foto Carnet',
                    'certificado_afp': 'Certificado AFP',
                    'certificado_salud': 'Certificado de Salud',
                    'certificado_estudios': 'Certificado de Estudios',
                    'certificado_residencia': 'Certificado de Residencia',
                    'fotocopia_carnet': 'Fotocopia Carnet',
                    'fotocopia_finiquito': 'Fotocopia Finiquito',
                    'comprobante_banco': 'Comprobante Banco'
                }
                nombre_doc = nombres_documentos.get(document_field, document_field)
                
                # Mover archivo a carpeta de eliminados
                from .models import mover_archivo_a_eliminados
                archivo_ruta_eliminado = mover_archivo_a_eliminados(
                    field, 
                    personal.rut, 
                    nombre_doc
                )
                
                # Limpiar el campo del modelo
                setattr(personal, document_field, None)
                
                # Si es el carnet, también eliminar la fecha de vencimiento
                if document_field == 'fotocopia_carnet':
                    personal.fecha_vencimiento_carnet = None
                
                personal.save()
                
                # Registrar en historial con la nueva ruta del archivo eliminado
                from .models import HistorialDocumentoPersonal
                archivo_ruta_historial = archivo_ruta_eliminado if archivo_ruta_eliminado else archivo_ruta_original
                
                HistorialDocumentoPersonal.registrar(
                    personal=personal,
                    tipo_documento='DOCUMENTO_PERSONAL',
                    accion='DOCUMENTO_ELIMINADO',
                    nombre_documento=nombre_doc,
                    descripcion=f"Documento {nombre_doc} eliminado",
                    usuario=request.user,
                    campo_documento=document_field,
                    archivo_ruta=archivo_ruta_historial,
                    datos_previos={'archivo': archivo_ruta_original, 'archivo_eliminado': archivo_ruta_historial}
                )
                
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
    """
    Vista principal para gestionar toda la documentación del personal.
    
    Muestra todos los documentos, licencias, certificaciones, exámenes,
    licencias médicas y ausentismos del personal en una vista unificada.
    
    Args:
        request: HttpRequest
        pk: ID del personal
        
    Returns:
        HttpResponse: Renderizado del template de documentación completa
    """
    # Verificar permisos: puede ver si tiene view_personal, change_personal, o permisos para agregar/editar documentación
    puede_ver = (
        request.user.has_perm('rrhh_personal.view_personal') or
        request.user.has_perm('rrhh_personal.change_personal') or
        request.user.has_perm('rrhh_personal.add_licenciaporpersonal') or
        request.user.has_perm('rrhh_personal.change_licenciaporpersonal') or
        request.user.has_perm('rrhh_personal.add_examen') or
        request.user.has_perm('rrhh_personal.change_examen')
    )
    
    if not puede_ver:
        from django.contrib import messages
        messages.error(
            request,
            'No tiene permiso para acceder a esta sección. Por favor, contacte al administrador si necesita acceso.'
        )
        from django.shortcuts import redirect
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('/home/')
    
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
    
    # Verificar permisos del usuario para pasar al template
    user = request.user
    permisos = {
        'can_view_personal': user.has_perm('rrhh_personal.view_personal'),
        'can_change_personal': user.has_perm('rrhh_personal.change_personal'),
        # Permisos para documentos personales
        'can_upload_document': user.has_perm('rrhh_personal.change_personal'),
        'can_delete_document': user.has_perm('rrhh_personal.change_personal'),
        # Permisos para licencias de conducir
        'can_add_license': user.has_perm('rrhh_personal.add_licenciaporpersonal'),
        'can_change_license': user.has_perm('rrhh_personal.change_licenciaporpersonal'),
        'can_delete_license': user.has_perm('rrhh_personal.delete_licenciaporpersonal'),
        # Permisos para licencias internas
        'can_add_internal_license': user.has_perm('rrhh_personal.add_licenciainternaporpersonal'),
        'can_change_internal_license': user.has_perm('rrhh_personal.change_licenciainternaporpersonal'),
        'can_delete_internal_license': user.has_perm('rrhh_personal.delete_licenciainternaporpersonal'),
        # Permisos para certificaciones
        'can_add_certification': user.has_perm('rrhh_personal.add_certificacion'),
        'can_change_certification': user.has_perm('rrhh_personal.change_certificacion'),
        'can_delete_certification': user.has_perm('rrhh_personal.delete_certificacion'),
        # Permisos para exámenes
        'can_add_exam': user.has_perm('rrhh_personal.add_examen'),
        'can_change_exam': user.has_perm('rrhh_personal.change_examen'),
        'can_delete_exam': user.has_perm('rrhh_personal.delete_examen'),
        # Historial de Documentos Personales - puede ver si tiene permisos de historial o de documentos personales
        'can_ver_historial_documentos_personales': (
            user.has_perm('rrhh_personal.view_historialdocumentopersonal') or
            user.has_perm('rrhh_personal.ver_historial_personal') or
            user.has_perm('rrhh_personal.view_personal') or
            user.has_perm('rrhh_personal.change_personal')
        ),
        # Historial de Licencias - puede ver si tiene permisos de licencias
        'can_ver_historial_licencias': (
            user.has_perm('rrhh_personal.view_licenciaporpersonal') or
            user.has_perm('rrhh_personal.add_licenciaporpersonal') or
            user.has_perm('rrhh_personal.change_licenciaporpersonal') or
            user.has_perm('rrhh_personal.ver_historial_personal') or
            user.has_perm('rrhh_personal.view_personal') or
            user.has_perm('rrhh_personal.change_personal')
        ),
        # Historial de Licencias Internas - puede ver si tiene permisos de licencias internas
        'can_ver_historial_licencias_internas': (
            user.has_perm('rrhh_personal.view_licenciainternaporpersonal') or
            user.has_perm('rrhh_personal.add_licenciainternaporpersonal') or
            user.has_perm('rrhh_personal.change_licenciainternaporpersonal') or
            user.has_perm('rrhh_personal.ver_historial_personal') or
            user.has_perm('rrhh_personal.view_personal') or
            user.has_perm('rrhh_personal.change_personal')
        ),
        # Historial de Certificaciones - puede ver si tiene permisos de certificaciones
        'can_ver_historial_certificaciones': (
            user.has_perm('rrhh_personal.view_certificacion') or
            user.has_perm('rrhh_personal.add_certificacion') or
            user.has_perm('rrhh_personal.change_certificacion') or
            user.has_perm('rrhh_personal.ver_historial_personal') or
            user.has_perm('rrhh_personal.view_personal') or
            user.has_perm('rrhh_personal.change_personal')
        ),
        # Historial de Exámenes - puede ver si tiene permisos de exámenes
        'can_ver_historial_examenes': (
            user.has_perm('rrhh_personal.view_examen') or
            user.has_perm('rrhh_personal.add_examen') or
            user.has_perm('rrhh_personal.change_examen') or
            user.has_perm('rrhh_personal.ver_historial_personal') or
            user.has_perm('rrhh_personal.view_personal') or
            user.has_perm('rrhh_personal.change_personal')
        ),
    }
    
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
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
        'permisos': permisos,
        'permisos_json': json.dumps(permisos, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'personal/documentation.html', context)

@login_required
@require_POST
def save_certification(request, pk):
    """
    Vista para guardar una certificación nueva (AJAX).
    
    Args:
        request: HttpRequest con datos del formulario
        pk: ID del personal
        
    Returns:
        JsonResponse: Resultado de la operación
    """
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
            certification._current_user = request.user
            certification.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificación guardada exitosamente',
                'data': {
                    'id': certification.certif_id,
                    'tipo': certification.tipoCertificacion_id.tipoCertificacion if certification.tipoCertificacion_id else '',
                    'proveedor': str(certification.proveedor_id) if certification.proveedor_id else '',
                    'fecha_emision': certification.fechaEmision.strftime('%Y-%m-%d'),
                    'fecha_vencimiento': certification.fechaVencimiento.strftime('%Y-%m-%d'),
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
    """
    Vista para eliminar una certificación.
    
    Args:
        request: HttpRequest
        pk: ID del personal
        certification_id: ID de la certificación a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la documentación del personal
    """
    try:
        certification = get_object_or_404(Certificacion, certif_id=certification_id, personal_id__personal_id=pk)
        certification._current_user = request.user
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
    """
    Vista para crear una nueva licencia médica.
    
    Valida que no haya solapamiento con otras licencias médicas del mismo personal.
    Calcula automáticamente la fecha de fin basándose en la fecha de emisión y los días.
    """
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
        # Pasar el personal_id al formulario para validación de solapamiento
        personal_id = self.kwargs.get('personal_id')
        form.personal_id = Personal.objects.get(pk=personal_id)
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
        # No mostrar mensaje genérico, los errores específicos se muestran con form.non_field_errors
        return super().form_invalid(form)

# Vista para listar y editar licencias médicas de un personal
@login_required
def listar_licencias_medicas_personal(request, personal_id):
    """
    Vista para listar las licencias médicas de un personal.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del template con lista de licencias médicas
    """
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
class LicenciaMedicaPorPersonalUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Vista para editar una licencia médica existente.
    
    Requiere permiso 'rrhh_personal.change_licenciamedicaporpersonal'.
    Valida que no haya solapamiento con otras licencias médicas del mismo personal.
    """
    permission_required = 'rrhh_personal.change_personal'
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
        # Pasar el personal_id al formulario para validación de solapamiento
        form.personal_id = self.object.personal_id
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
        # No mostrar mensaje genérico, los errores específicos se muestran con form.non_field_errors
        return super().form_invalid(form)

@login_required
def delete_licencia_medica(request, licencia_id):
    """
    Vista para eliminar una licencia médica.
    
    Args:
        request: HttpRequest
        licencia_id: ID de la licencia médica a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la lista de licencias médicas
    """
    if request.method == 'POST':
        try:
            licencia = get_object_or_404(LicenciaMedicaPorPersonal, licenciaMedicaPorPersonal_id=licencia_id)
            personal_id = licencia.personal_id.personal_id
            licencia.delete()
            
            messages.success(request, 'Licencia médica eliminada exitosamente')
            return redirect('listar_licencias_medicas_personal', personal_id=personal_id)
            
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
            return redirect('listar_licencias_medicas_personal', personal_id=licencia.personal_id.personal_id)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

# ============================================================================
# VISTAS PARA AUSENTISMOS Y PERMISOS
# ============================================================================

@login_required
def listar_ausentismos_personal(request, personal_id):
    """
    Vista para listar los ausentismos de un personal.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del template con lista de ausentismos
    """
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
@permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
def crear_ausentismo(request, personal_id):
    """
    Vista para crear un nuevo ausentismo.
    
    Valida que no haya solapamiento con otros ausentismos del mismo personal.
    
    Args:
        request: HttpRequest con datos del formulario
        personal_id: ID del personal
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
    """Vista para crear un ausentismo"""
    personal = get_object_or_404(Personal, personal_id=personal_id)
    
    if request.method == 'POST':
        from .forms import AusentismoForm
        form = AusentismoForm(request.POST)
        # Pasar el personal_id al formulario para validación de solapamiento
        form.personal_id = personal
        if form.is_valid():
            ausentismo = form.save(commit=False)
            ausentismo.personal_id = personal
            ausentismo.save()
            messages.success(request, 'Ausentismo registrado exitosamente')
            return redirect('listar_ausentismos_personal', personal_id=personal.personal_id)
        # No mostrar mensaje genérico, los errores específicos se muestran con form.non_field_errors
    else:
        from .forms import AusentismoForm
        form = AusentismoForm()
        # Pasar el personal_id al formulario para validación de solapamiento
        form.personal_id = personal
    
    context = {
        'form': form,
        'personal': personal,
    }
    
    return render(request, 'personal/create_ausentismo.html', context)


@login_required
def actualizar_ausentismo(request, personal_id, ausentismo_id):
    """
    Vista para actualizar un ausentismo existente.
    
    Valida que no haya solapamiento con otros ausentismos del mismo personal.
    
    Args:
        request: HttpRequest con datos del formulario
        personal_id: ID del personal
        ausentismo_id: ID del ausentismo a actualizar
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
    """Vista para actualizar un ausentismo"""
    ausentismo = get_object_or_404(Ausentismo, ausentismo_id=ausentismo_id)
    personal = ausentismo.personal_id
    
    if request.method == 'POST':
        from .forms import AusentismoForm
        form = AusentismoForm(request.POST, instance=ausentismo)
        # Pasar el personal_id al formulario para validación de solapamiento
        form.personal_id = personal
        if form.is_valid():
            form.save()
            messages.success(request, 'Ausentismo actualizado exitosamente')
            return redirect('listar_ausentismos_personal', personal_id=personal.personal_id)
        # No mostrar mensaje genérico, los errores específicos se muestran con form.non_field_errors
    else:
        from .forms import AusentismoForm
        form = AusentismoForm(instance=ausentismo)
        # Pasar el personal_id al formulario para validación de solapamiento
        form.personal_id = personal
    
    context = {
        'form': form,
        'personal': personal,
        'ausentismo': ausentismo,
    }
    
    return render(request, 'personal/edit_ausentismo.html', context)


@login_required
def eliminar_ausentismo(request, ausentismo_id):
    """
    Vista para eliminar un ausentismo.
    
    Args:
        request: HttpRequest
        ausentismo_id: ID del ausentismo a eliminar
        
    Returns:
        HttpResponseRedirect: Redirección a la lista de ausentismos
    """
    """Vista para eliminar un ausentismo"""
    if request.method == 'POST':
        try:
            ausentismo = get_object_or_404(Ausentismo, ausentismo_id=ausentismo_id)
            personal_id = ausentismo.personal_id.personal_id
            ausentismo.delete()
            
            messages.success(request, 'Ausentismo eliminado exitosamente')
            return redirect('listar_ausentismos_personal', personal_id=personal_id)
            
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
            return redirect('listar_ausentismos_personal', personal_id=ausentismo.personal_id.personal_id)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def gestionar_ausencias(request):
    """
    Vista unificada para gestionar ausencias (licencias médicas y ausentismos).
    
    Muestra una vista consolidada de todas las ausencias del personal,
    permitiendo filtrar y gestionar tanto licencias médicas como ausentismos.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Renderizado del template de gestión de ausencias
    """
    """Vista unificada para gestionar licencias médicas y ausentismos"""
    from gen_settings.models import Empresa
    from django.db.models import Count, Q
    from datetime import date
    
    # Obtener todo el personal activo con sus relaciones - optimizado
    # Precalcular conteos de licencias y ausentismos activos para evitar N+1 queries
    personal = Personal.objects.filter(activo=True).prefetch_related(
        'infolaboral_set__cargo_id',
        'infolaboral_set__depto_id',
        'infolaboral_set__empresa_id',
        'licenciamedicaporpersonal_set__tipoLicenciaMedica_id',
        'ausentismo_set__tipoausen_id'
    ).annotate(
        licencias_activas_count=Count(
            'licenciamedicaporpersonal',
            filter=Q(licenciamedicaporpersonal__fecha_fin_licencia__gte=date.today())
        ),
        ausentismos_activos_count=Count(
            'ausentismo',
            filter=Q(ausentismo__fechafin__gte=date.today())
        )
    ).order_by('apepat', 'apemat', 'nombre')
    
    # Preparar datos optimizados para el template
    personal_data = []
    for persona in personal:
        info_laboral = next(iter(persona.infolaboral_set.all()), None)
        personal_data.append({
            'persona': persona,
            'info_laboral': info_laboral,
            'licencias_activas': persona.licencias_activas_count,
            'ausentismos_activos': persona.ausentismos_activos_count,
        })
    
    # Obtener empresas para los filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')
    
    context = {
        'personal': personal,  # Mantener para compatibilidad
        'personal_data': personal_data,  # Datos optimizados
        'empresas': empresas,
    }
    
    return render(request, 'personal/gestionar_ausencias.html', context)


@login_required
def edit_license(request, license_id):
    """
    Vista para editar una licencia de conducir existente.
    
    Args:
        request: HttpRequest con datos del formulario
        license_id: ID de la licencia a editar
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                    license._current_user = request.user
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
                            'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
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
                    license = form.save(commit=False)
                    license._current_user = request.user
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
                            'fecha_emision': license.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': license.fechaVencimiento.strftime('%Y-%m-%d'),
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
    """
    Vista para editar una certificación existente.
    
    Args:
        request: HttpRequest con datos del formulario
        cert_id: ID de la certificación a editar
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                    cert._current_user = request.user
                    cert.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Certificación actualizada exitosamente',
                        'data': {
                            'id': cert.certif_id,
                            'tipo': cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else '',
                            'proveedor': str(cert.proveedor_id) if cert.proveedor_id else '',
                            'fecha_emision': cert.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': cert.fechaVencimiento.strftime('%Y-%m-%d'),
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
                    cert = form.save(commit=False)
                    cert._current_user = request.user
                    cert.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Certificación actualizada exitosamente',
                        'data': {
                            'id': cert.certif_id,
                            'tipo': cert.tipoCertificacion_id.tipoCertificacion if cert.tipoCertificacion_id else '',
                            'proveedor': str(cert.proveedor_id) if cert.proveedor_id else '',
                            'fecha_emision': cert.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': cert.fechaVencimiento.strftime('%Y-%m-%d'),
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
    """
    Vista para editar un examen médico existente.
    
    Args:
        request: HttpRequest con datos del formulario
        exam_id: ID del examen a editar
        
    Returns:
        HttpResponse: Renderizado del formulario o redirección si es exitoso
    """
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
                    exam._current_user = request.user
                    exam.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Examen actualizado exitosamente',
                        'data': {
                            'id': exam.examen_id,
                            'tipo': exam.tipoEx_id.tipoExamen if exam.tipoEx_id else '',
                            'resultado': str(exam.resultadoEx_id) if exam.resultadoEx_id else '-',
                            'proveedor': str(exam.proveedor_id) if exam.proveedor_id else '',
                            'fecha_emision': exam.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': exam.fechaVencimiento.strftime('%Y-%m-%d'),
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
                    exam = form.save(commit=False)
                    exam._current_user = request.user
                    exam.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Examen actualizado exitosamente',
                        'data': {
                            'id': exam.examen_id,
                            'tipo': exam.tipoEx_id.tipoExamen if exam.tipoEx_id else '',
                            'resultado': str(exam.resultadoEx_id) if exam.resultadoEx_id else '-',
                            'proveedor': str(exam.proveedor_id) if exam.proveedor_id else '',
                            'fecha_emision': exam.fechaEmision.strftime('%Y-%m-%d'),
                            'fecha_vencimiento': exam.fechaVencimiento.strftime('%Y-%m-%d'),
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

class PersonalDesactivadoListView(PermissionRequiredMixin, ListView, LoginRequiredMixin):
    """
    Vista para listar el personal desactivado.
    
    Requiere permiso 'rrhh_personal.view_personal'.
    Similar a PersonalListView pero muestra solo personal inactivo.
    """
    permission_required = 'rrhh_personal.view_personal'
    """Vista para listar personal desactivado"""
    model = Personal
    template_name = 'personal/personal_desactivado.html'
    context_object_name = 'personal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from gen_settings.models import Empresa
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        context['empresas'] = Empresa.objects.all()
        
        # Preparar datos del personal para JSON
        personal_data = []
        for persona in context['personal']:
            info_laboral = persona.infolaboral_set.first()
            personal_data.append({
                'id': persona.personal_id,
                'rut': f"{persona.rut}-{persona.dvrut}",
                'nombre': f"{persona.nombre} {persona.apepat} {persona.apemat}",
                'cargo': info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'No disponible',
                'departamento': info_laboral.depto_id.depto if info_laboral and info_laboral.depto_id else 'No disponible',
                'empresa': info_laboral.empresa_id.nomFantasia if info_laboral and info_laboral.empresa_id else 'No disponible',
                'activo': persona.activo
            })
        
        context['personal_json'] = json.dumps(personal_data, cls=DjangoJSONEncoder)
        
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


# ============================================================================
# APIs PARA HISTORIAL DE PERSONAL
# ============================================================================

@csrf_exempt
@login_required
@permission_required_multiple(
    'rrhh_personal.ver_historial_personal',
    'rrhh_personal.view_personal',
    'rrhh_personal.change_personal',
    require_all=False,
    is_ajax=True
)
@require_http_methods(["GET"])
def api_historial_personal(request, personal_id):
    """
    API endpoint para obtener el historial de cambios del personal (JSON).
    
    Retorna todos los eventos del historial (creación, modificación, activación, etc.)
    en formato JSON para ser consumido por JavaScript.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Lista de eventos del historial
    """
    """API para obtener el historial completo de un personal en formato JSON"""
    try:
        personal = get_object_or_404(Personal, personal_id=personal_id)
        historial = HistorialPersonal.objects.filter(personal=personal).select_related(
            'usuario'
        ).order_by('-fecha_hora')
        
        # Preparar historial con nombre completo de usuario
        historial_data = []
        for evento in historial:
            historial_data.append({
                'id': evento.id,
                'fecha_hora': evento.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_formateada': evento.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                'usuario_nombre': obtener_nombre_completo_usuario(evento.usuario),
                'accion': evento.accion,
                'accion_display': evento.get_accion_display(),
                'descripcion': evento.descripcion,
                'datos_previos': evento.datos_previos,
                'datos_nuevos': evento.datos_nuevos
            })
        
        return JsonResponse({
            'success': True,
            'personal': {
                'id': personal.personal_id,
                'rut': f"{personal.rut}-{personal.dvrut}",
                'nombre': f"{personal.nombre} {personal.apepat} {personal.apemat}"
            },
            'historial': historial_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener historial de personal: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@permission_required_multiple(
    'rrhh_personal.ver_historial_personal',
    'rrhh_personal.view_personal',
    'rrhh_personal.change_personal',
    require_all=False,
    is_ajax=True
)
@require_http_methods(["GET"])
def api_historial_documentos_personal(request, personal_id):
    """
    API endpoint para obtener el historial de documentos del personal (JSON).
    
    Retorna todos los eventos relacionados con documentos (agregado, modificado, eliminado)
    en formato JSON para ser consumido por JavaScript.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Lista de eventos del historial de documentos
    """
    """API para obtener el historial de documentos de un personal en formato JSON"""
    try:
        personal = get_object_or_404(Personal, personal_id=personal_id)
        historial = HistorialDocumentoPersonal.objects.filter(personal=personal).select_related(
            'usuario'
        ).order_by('-fecha_hora')
        
        # Preparar historial con nombre completo de usuario
        historial_data = []
        for evento in historial:
            historial_data.append({
                'id': evento.id,
                'fecha_hora': evento.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_formateada': evento.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'usuario': evento.usuario.username if evento.usuario else 'Sistema',
                'usuario_nombre': obtener_nombre_completo_usuario(evento.usuario),
                'tipo_documento': evento.tipo_documento,
                'tipo_documento_display': evento.get_tipo_documento_display() if hasattr(evento, 'get_tipo_documento_display') else evento.tipo_documento,
                'accion': evento.accion,
                'accion_display': evento.get_accion_display(),
                'nombre_documento': evento.nombre_documento,
                'campo_documento': evento.campo_documento,
                'archivo_ruta': evento.archivo_ruta,
                'archivo_url': obtener_url_archivo_historial(evento, personal),
                'descripcion': evento.descripcion,
                'datos_previos': evento.datos_previos,
                'datos_nuevos': evento.datos_nuevos
            })
        
        return JsonResponse({
            'success': True,
            'personal': {
                'id': personal.personal_id,
                'rut': f"{personal.rut}-{personal.dvrut}",
                'nombre': f"{personal.nombre} {personal.apepat} {personal.apemat}"
            },
            'historial': historial_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener historial de documentos: {str(e)}'
        }, status=500)


@login_required
@permission_required_custom('rrhh_personal.view_personal', is_ajax=True)
@require_http_methods(["GET"])
def api_obtener_info_personal(request, personal_id):
    """
    API endpoint para obtener información completa del personal (JSON).
    
    Retorna toda la información del personal incluyendo documentos, licencias,
    certificaciones, exámenes, etc. en formato JSON.
    
    Args:
        request: HttpRequest
        personal_id: ID del personal
        
    Returns:
        JsonResponse: Información completa del personal
    """
    """
    API para obtener información completa del personal (personal y laboral).
    Retorna toda la información en formato JSON para mostrar en un modal.
    """
    try:
        personal = get_object_or_404(Personal, personal_id=personal_id)
        
        # Obtener información laboral (puede haber múltiples registros históricos)
        info_laboral_list = personal.infolaboral_set.all().select_related(
            'empresa_id', 'depto_id', 'cargo_id'
        ).order_by('-fechacontrata')
        
        # Información laboral actual (la más reciente)
        info_laboral_actual = info_laboral_list.first() if info_laboral_list.exists() else None
        
        # Preparar datos personales
        datos_personales = {
            'personal_id': personal.personal_id,
            'rut': f"{personal.rut}-{personal.dvrut}",
            'nombre': personal.nombre,
            'apepat': personal.apepat,
            'apemat': personal.apemat or '',
            'nombre_completo': f"{personal.nombre} {personal.apepat} {personal.apemat}".strip(),
            'fecha_nacimiento': personal.fechanac.strftime('%d/%m/%Y') if personal.fechanac else 'No disponible',
            'correo': personal.correo,
            'direccion': personal.direccion or 'No disponible',
            'sexo': personal.sexo_id.sexo if personal.sexo_id else 'No disponible',
            'estado_civil': personal.estcivil_id.estadocivil if personal.estcivil_id else 'No disponible',
            'region': personal.region_id.nombre if personal.region_id else 'No disponible',
            'comuna': personal.comuna_id.nombre if personal.comuna_id else 'No disponible',
            'activo': personal.activo,
            'estado_texto': 'Activo' if personal.activo else 'Inactivo',
        }
        
        # Preparar información laboral actual
        info_laboral_data = None
        if info_laboral_actual:
            info_laboral_data = {
                'empresa': info_laboral_actual.empresa_id.nomFantasia if info_laboral_actual.empresa_id else 'No disponible',
                'departamento': info_laboral_actual.depto_id.depto if info_laboral_actual.depto_id else 'No disponible',
                'cargo': info_laboral_actual.cargo_id.cargo if info_laboral_actual.cargo_id else 'No disponible',
                'fecha_contratacion': info_laboral_actual.fechacontrata.strftime('%d/%m/%Y') if info_laboral_actual.fechacontrata else 'No disponible',
            }
        
        # Historial laboral (todas las asignaciones)
        historial_laboral = []
        for info_lab in info_laboral_list:
            historial_laboral.append({
                'empresa': info_lab.empresa_id.nomFantasia if info_lab.empresa_id else 'No disponible',
                'departamento': info_lab.depto_id.depto if info_lab.depto_id else 'No disponible',
                'cargo': info_lab.cargo_id.cargo if info_lab.cargo_id else 'No disponible',
                'fecha_contratacion': info_lab.fechacontrata.strftime('%d/%m/%Y') if info_lab.fechacontrata else 'No disponible',
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'personal': datos_personales,
                'laboral_actual': info_laboral_data,
                'historial_laboral': historial_laboral
            }
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc() if request.user.is_superuser else None
        }, status=500)


@login_required
@require_POST
def toggle_personal_activo(request):
    """
    Vista AJAX para cambiar el estado activo/inactivo del personal.
    
    Versión alternativa de toggle_personal_status que acepta múltiples IDs.
    
    Args:
        request: HttpRequest con POST 'personal_id' y 'activo'
        
    Returns:
        JsonResponse: Resultado de la operación
    """
    """
    Toggle estado activo/inactivo de personal.
    
    Requiere permisos específicos según la acción:
    - Desactivar: requiere 'rrhh_personal.desactivar_personal'
    - Activar: requiere 'rrhh_personal.activar_personal'
    """
    try:
        data = json.loads(request.body)
        personal_id = data.get('personal_id')
        
        personal = get_object_or_404(Personal, personal_id=personal_id)
        
        # Verificar permiso según la acción que se va a realizar
        if personal.activo:
            # Si está activo, se va a desactivar - requiere permiso de desactivar
            if not request.user.has_perm('rrhh_personal.desactivar_personal'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'No tiene permiso para desactivar personal'
                }, status=403)
        else:
            # Si está inactivo, se va a activar - requiere permiso de activar
            if not request.user.has_perm('rrhh_personal.activar_personal'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'No tiene permiso para activar personal'
                }, status=403)
        
        # Si tiene el permiso, realizar la acción
        personal.activo = not personal.activo
        # Pasar usuario a la señal
        personal._current_user = request.user
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


# ============================================================================
# VISTA PARA DESCARGAR DOCUMENTACIÓN EN ZIP
# ============================================================================

@login_required
@permission_required_custom('rrhh_personal.view_personal')
@require_POST
def descargar_documentacion_zip(request):
    """
    Vista para descargar toda la documentación del personal en un archivo ZIP.
    
    Incluye documentos personales, licencias, certificaciones y exámenes.
    Crea un archivo ZIP temporal y lo retorna como descarga.
    
    Args:
        request: HttpRequest con POST 'personal_ids' (lista de IDs)
        
    Returns:
        HttpResponse: Archivo ZIP con la documentación
    """
    """
    Genera un archivo ZIP con la documentación de los personal seleccionados.
    Estructura del ZIP:
    Documentacion_Personal/
        RUT1_Nombre/
            Documentos_Personales/
            Licencias/
            Certificaciones/
            Examenes/
            Licencias_Internas/
        RUT2_Nombre/
            ...
    
    Nota: Las licencias médicas y ausentismos no incluyen documentos adjuntos,
    solo información en la base de datos, por lo que no se descargan.
    """
    try:
        # Obtener IDs del personal desde POST
        personal_ids = request.POST.getlist('personal_ids')
        
        if not personal_ids:
            messages.error(request, 'No se seleccionó ningún personal')
            return redirect('table_personal')
        
        # Convertir a enteros
        personal_ids = [int(pid) for pid in personal_ids]
        
        # Obtener el personal
        personal_list = Personal.objects.filter(personal_id__in=personal_ids)
        
        if not personal_list.exists():
            messages.error(request, 'No se encontró el personal seleccionado')
            return redirect('table_personal')
        
        # Crear archivo ZIP temporal
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = temp_zip.name
        temp_zip.close()
        
        # Contador de archivos agregados
        archivos_agregados = 0
        
        # Crear ZIP
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for personal in personal_list:
                # Nombre de carpeta para este personal
                nombre_carpeta = f"{personal.rut}-{personal.dvrut}_{personal.nombre}_{personal.apepat}"
                nombre_carpeta = nombre_carpeta.replace('/', '_').replace('\\', '_')  # Limpiar caracteres especiales
                
                # Documentos personales (FileField e ImageField)
                campos_documentos = [
                    'curriculum', 'certificado_antecedentes', 'hoja_vida_conductor',
                    'foto_carnet', 'certificado_afp', 'certificado_salud',
                    'certificado_estudios', 'certificado_residencia', 'fotocopia_carnet',
                    'fotocopia_finiquito', 'comprobante_banco'
                ]
                
                for campo in campos_documentos:
                    archivo = getattr(personal, campo)
                    if archivo and archivo.name:
                        try:
                            # Leer contenido del archivo (funciona tanto con FileSystemStorage como con S3)
                            # Asegurarse de que el archivo esté abierto desde el principio
                            archivo.open('rb')
                            contenido_archivo = archivo.read()
                            archivo.close()
                            
                            if contenido_archivo and len(contenido_archivo) > 0:
                                # Nombre del archivo en el ZIP
                                nombre_archivo_zip = f"{nombre_carpeta}/Documentos_Personales/{os.path.basename(archivo.name)}"
                                zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                archivos_agregados += 1
                            else:
                                print(f"Archivo {campo} de {personal.nombre} está vacío o no se pudo leer")
                        except Exception as e:
                            print(f"Error al agregar {campo} de {personal.nombre}: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Licencias de conducir
                licencias = LicenciaPorPersonal.objects.filter(personal_id=personal)
                for licencia in licencias:
                    if licencia.rutaDoc and licencia.rutaDoc.name:
                        try:
                            licencia.rutaDoc.open('rb')
                            contenido_archivo = licencia.rutaDoc.read()
                            licencia.rutaDoc.close()
                            
                            if contenido_archivo and len(contenido_archivo) > 0:
                                nombre_archivo_zip = f"{nombre_carpeta}/Licencias/licencia_{licencia.licenciaPorPersonal_id}_{os.path.basename(licencia.rutaDoc.name)}"
                                zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                archivos_agregados += 1
                        except Exception as e:
                            print(f"Error al agregar licencia de {personal.nombre}: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Licencias internas
                try:
                    from .models import LicenciaInternaPorPersonal
                    licencias_internas = LicenciaInternaPorPersonal.objects.filter(personal_id=personal)
                    for licencia_int in licencias_internas:
                        if licencia_int.rutaDoc and licencia_int.rutaDoc.name:
                            try:
                                licencia_int.rutaDoc.open('rb')
                                contenido_archivo = licencia_int.rutaDoc.read()
                                licencia_int.rutaDoc.close()
                                
                                if contenido_archivo and len(contenido_archivo) > 0:
                                    nombre_archivo_zip = f"{nombre_carpeta}/Licencias_Internas/licencia_interna_{licencia_int.licenciaInterna_id}_{os.path.basename(licencia_int.rutaDoc.name)}"
                                    zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                    archivos_agregados += 1
                            except Exception as e:
                                print(f"Error al agregar licencia interna de {personal.nombre}: {e}")
                                import traceback
                                traceback.print_exc()
                except Exception as e:
                    print(f"Error al obtener licencias internas: {e}")
                
                # Licencias médicas y ausentismos no tienen documentos adjuntos
                # Solo se registra información en la base de datos, no se descargan archivos
                
                # Certificaciones
                certificaciones = Certificacion.objects.filter(personal_id=personal)
                for cert in certificaciones:
                    if cert.rutaDoc and cert.rutaDoc.name:
                        try:
                            cert.rutaDoc.open('rb')
                            contenido_archivo = cert.rutaDoc.read()
                            cert.rutaDoc.close()
                            
                            if contenido_archivo and len(contenido_archivo) > 0:
                                nombre_archivo_zip = f"{nombre_carpeta}/Certificaciones/certificacion_{cert.certif_id}_{os.path.basename(cert.rutaDoc.name)}"
                                zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                archivos_agregados += 1
                        except Exception as e:
                            print(f"Error al agregar certificación de {personal.nombre}: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Exámenes
                examenes = Examen.objects.filter(personal_id=personal)
                for examen in examenes:
                    if examen.rutaDoc and examen.rutaDoc.name:
                        try:
                            examen.rutaDoc.open('rb')
                            contenido_archivo = examen.rutaDoc.read()
                            examen.rutaDoc.close()
                            
                            if contenido_archivo and len(contenido_archivo) > 0:
                                nombre_archivo_zip = f"{nombre_carpeta}/Examenes/examen_{examen.examen_id}_{os.path.basename(examen.rutaDoc.name)}"
                                zip_file.writestr(nombre_archivo_zip, contenido_archivo)
                                archivos_agregados += 1
                        except Exception as e:
                            print(f"Error al agregar examen de {personal.nombre}: {e}")
                            import traceback
                            traceback.print_exc()
        
        # Verificar si se agregaron archivos
        if archivos_agregados == 0:
            messages.warning(request, f'No se encontraron documentos para descargar. Se generó un ZIP vacío.')
            os.unlink(temp_zip_path)
            return redirect('table_personal')
        
        # Leer el archivo ZIP
        with open(temp_zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Eliminar archivo temporal
        os.unlink(temp_zip_path)
        
        # Crear respuesta HTTP
        fecha_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"Documentacion_Personal_{fecha_hora}.zip"
        
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        response['Content-Length'] = len(zip_content)
        
        return response
        
    except Exception as e:
        # Eliminar archivo temporal si existe
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)
        
        messages.error(request, f'Error al generar el archivo ZIP: {str(e)}')
        return redirect('table_personal')
