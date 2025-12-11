"""
============================================================================
VISTAS PARA GEN_SETTINGS
============================================================================
Este módulo contiene las vistas para gestionar configuraciones generales
del sistema: Regiones, Comunas, Unidades de Medida y Empresas.
Todas las vistas usan class-based views de Django y retornan JSON para
interacción AJAX.
============================================================================
"""

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Region, Comuna, UnidadMedida, Empresa
from .forms import RegionForm, ComunaForm, UnidadMedidaForm, EmpresaForm


class RegionListView(ListView):
    """
    Vista para listar todas las regiones.
    
    Renderiza la página HTML con la lista de regiones disponibles.
    """
    model = Region
    template_name = 'region.html'
    context_object_name = 'regiones'

class RegionCreateView(CreateView):
    """
    Vista para crear una nueva región.
    
    Retorna JSON para interacción AJAX. Si el formulario es válido,
    crea la región y retorna success=True. Si es inválido, retorna
    los errores del formulario.
    """
    model = Region
    form_class = RegionForm
    success_url = reverse_lazy('region_list')

    def form_valid(self, form):
        """
        Procesa un formulario válido y retorna respuesta JSON.
        
        Args:
            form: Formulario válido de región.
            
        Returns:
            JsonResponse: Respuesta JSON con success=True.
        """
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        """
        Procesa un formulario inválido y retorna errores en JSON.
        
        Args:
            form: Formulario inválido de región.
            
        Returns:
            JsonResponse: Respuesta JSON con success=False y errores del formulario.
        """
        return JsonResponse({'success': False, 'errors': form.errors})

class RegionUpdateView(UpdateView):
    """
    Vista para actualizar una región existente.
    
    GET: Retorna los datos de la región en JSON.
    POST: Actualiza la región y retorna success=True o errores.
    """
    model = Region
    form_class = RegionForm
    success_url = reverse_lazy('region_list')

    def get(self, request, *args, **kwargs):
        """
        Retorna los datos de la región en formato JSON.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: Datos de la región (id, nombre).
        """
        region = get_object_or_404(Region, pk=kwargs['pk'])
        return JsonResponse({
            'id': region.id,
            'nombre': region.nombre
        })

    def post(self, request, *args, **kwargs):
        """
        Actualiza una región existente.
        
        Args:
            request: Objeto HttpRequest con datos POST.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se actualizó correctamente,
                         success=False con errores si falló.
        """
        region = get_object_or_404(Region, pk=kwargs['pk'])
        nombre = request.POST.get('nombre')
        
        if nombre:
            region.nombre = nombre
            region.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': 'El nombre es requerido'})

class RegionDeleteView(DeleteView):
    """
    Vista para eliminar una región.
    
    Retorna JSON para interacción AJAX. Maneja errores y retorna
    success=True si se eliminó correctamente.
    """
    model = Region
    success_url = reverse_lazy('region_list')

    def post(self, request, *args, **kwargs):
        """
        Elimina una región existente.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se eliminó correctamente,
                         success=False con error si falló.
        """
        try:
            region = self.get_object()
            region.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class ComunaListView(ListView):
    """
    Vista para listar todas las comunas.
    
    Renderiza la página HTML con la lista de comunas disponibles.
    Incluye el formulario vacío en el contexto para crear nuevas comunas.
    """
    model = Comuna
    template_name = 'comuna.html'
    context_object_name = 'comunas'

    def get_context_data(self, **kwargs):
        """
        Agrega el formulario de comuna al contexto.
        
        Args:
            **kwargs: Argumentos adicionales del contexto.
            
        Returns:
            dict: Contexto con la lista de comunas y el formulario.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = ComunaForm()
        return context

class ComunaCreateView(CreateView):
    """
    Vista para crear una nueva comuna.
    
    Retorna JSON para interacción AJAX. Si el formulario es válido,
    crea la comuna y retorna success=True. Si es inválido, retorna
    los errores del formulario.
    """
    model = Comuna
    form_class = ComunaForm
    success_url = reverse_lazy('comuna_list')

    def form_valid(self, form):
        """
        Procesa un formulario válido y retorna respuesta JSON.
        
        Args:
            form: Formulario válido de comuna.
            
        Returns:
            JsonResponse: Respuesta JSON con success=True.
        """
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        """
        Procesa un formulario inválido y retorna errores en JSON.
        
        Args:
            form: Formulario inválido de comuna.
            
        Returns:
            JsonResponse: Respuesta JSON con success=False y errores del formulario.
        """
        return JsonResponse({'success': False, 'errors': form.errors})

class ComunaUpdateView(UpdateView):
    """
    Vista para actualizar una comuna existente.
    
    GET: Retorna los datos de la comuna en JSON.
    POST: Actualiza la comuna y retorna success=True o errores.
    """
    model = Comuna
    form_class = ComunaForm
    success_url = reverse_lazy('comuna_list')

    def get(self, request, *args, **kwargs):
        """
        Retorna los datos de la comuna en formato JSON.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: Datos de la comuna (id, nombre, region).
        """
        comuna = get_object_or_404(Comuna, pk=kwargs['pk'])
        return JsonResponse({
            'id': comuna.id,
            'nombre': comuna.nombre,
            'region': comuna.region.id
        })

    def post(self, request, *args, **kwargs):
        """
        Actualiza una comuna existente.
        
        Args:
            request: Objeto HttpRequest con datos POST.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se actualizó correctamente,
                         success=False con errores si falló.
        """
        comuna = get_object_or_404(Comuna, pk=kwargs['pk'])
        nombre = request.POST.get('nombre')
        region_id = request.POST.get('region')
        
        if nombre and region_id:
            comuna.nombre = nombre
            comuna.region_id = region_id
            comuna.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': 'Todos los campos son requeridos'})

class ComunaDeleteView(DeleteView):
    """
    Vista para eliminar una comuna.
    
    Retorna JSON para interacción AJAX. Maneja errores y retorna
    success=True si se eliminó correctamente.
    """
    model = Comuna
    success_url = reverse_lazy('comuna_list')

    def post(self, request, *args, **kwargs):
        """
        Elimina una comuna existente.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se eliminó correctamente,
                         success=False con error si falló.
        """
        try:
            comuna = self.get_object()
            comuna.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class UnidadMedidaListView(ListView):
    """
    Vista para listar todas las unidades de medida.
    
    Renderiza la página HTML con la lista de unidades de medida disponibles.
    Incluye el formulario vacío en el contexto para crear nuevas unidades.
    """
    model = UnidadMedida
    template_name = 'unidad_medida.html'
    context_object_name = 'unidades_medida'

    def get_context_data(self, **kwargs):
        """
        Agrega el formulario de unidad de medida al contexto.
        
        Args:
            **kwargs: Argumentos adicionales del contexto.
            
        Returns:
            dict: Contexto con la lista de unidades y el formulario.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = UnidadMedidaForm()
        return context

class UnidadMedidaCreateView(CreateView):
    """
    Vista para crear una nueva unidad de medida.
    
    Retorna JSON para interacción AJAX. Si el formulario es válido,
    crea la unidad de medida y retorna success=True. Si es inválido,
    retorna los errores del formulario.
    """
    model = UnidadMedida
    form_class = UnidadMedidaForm
    success_url = reverse_lazy('unidad_medida_list')

    def form_valid(self, form):
        """
        Procesa un formulario válido y retorna respuesta JSON.
        
        Args:
            form: Formulario válido de unidad de medida.
            
        Returns:
            JsonResponse: Respuesta JSON con success=True.
        """
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        """
        Procesa un formulario inválido y retorna errores en JSON.
        
        Args:
            form: Formulario inválido de unidad de medida.
            
        Returns:
            JsonResponse: Respuesta JSON con success=False y errores del formulario.
        """
        return JsonResponse({'success': False, 'errors': form.errors})

class UnidadMedidaUpdateView(UpdateView):
    """
    Vista para actualizar una unidad de medida existente.
    
    GET: Retorna los datos de la unidad de medida en JSON.
    POST: Actualiza la unidad de medida y retorna success=True o errores.
    """
    model = UnidadMedida
    form_class = UnidadMedidaForm
    success_url = reverse_lazy('unidad_medida_list')

    def get(self, request, *args, **kwargs):
        """
        Retorna los datos de la unidad de medida en formato JSON.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: Datos de la unidad de medida (id, codigo, descripcion).
        """
        unidad = get_object_or_404(UnidadMedida, pk=kwargs['pk'])
        return JsonResponse({
            'id': unidad.id,
            'codigo': unidad.codigo,
            'descripcion': unidad.descripcion
        })

    def post(self, request, *args, **kwargs):
        """
        Actualiza una unidad de medida existente.
        
        Args:
            request: Objeto HttpRequest con datos POST.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se actualizó correctamente,
                         success=False con errores si falló.
        """
        unidad = get_object_or_404(UnidadMedida, pk=kwargs['pk'])
        codigo = request.POST.get('codigo')
        descripcion = request.POST.get('descripcion')
        
        if codigo and descripcion:
            unidad.codigo = codigo
            unidad.descripcion = descripcion
            unidad.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': 'Todos los campos son requeridos'})

class UnidadMedidaDeleteView(DeleteView):
    """
    Vista para eliminar una unidad de medida.
    
    Retorna JSON para interacción AJAX. Maneja errores y retorna
    success=True si se eliminó correctamente.
    """
    model = UnidadMedida
    success_url = reverse_lazy('unidad_medida_list')

    def post(self, request, *args, **kwargs):
        """
        Elimina una unidad de medida existente.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se eliminó correctamente,
                         success=False con error si falló.
        """
        try:
            unidad = self.get_object()
            unidad.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def load_comunas(request):
    """
    Vista AJAX para cargar comunas según la región seleccionada.
    
    Endpoint utilizado por formularios que necesitan cargar comunas
    dinámicamente cuando se selecciona una región.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con parámetro GET 'region_id'.
        
    Returns:
        JsonResponse: Lista de comunas de la región especificada en formato JSON.
                     Cada comuna contiene 'id' y 'nombre'.
    """
    region_id = request.GET.get('region_id')
    comunas = Comuna.objects.filter(region_id=region_id).order_by('nombre')
    return JsonResponse({'comunas': list(comunas.values('id', 'nombre'))}, safe=False)

class EmpresaListView(ListView):
    """
    Vista para listar todas las empresas.
    
    Renderiza la página HTML con la lista de empresas disponibles.
    Incluye el formulario vacío en el contexto para crear nuevas empresas.
    """
    model = Empresa
    template_name = 'empresa.html'
    context_object_name = 'empresas'

    def get_context_data(self, **kwargs):
        """
        Agrega el formulario de empresa al contexto.
        
        Args:
            **kwargs: Argumentos adicionales del contexto.
            
        Returns:
            dict: Contexto con la lista de empresas y el formulario.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = EmpresaForm()
        return context

class EmpresaCreateView(CreateView):
    """
    Vista para crear una nueva empresa.
    
    Retorna JSON para interacción AJAX. Si el formulario es válido,
    crea la empresa y retorna success=True. Si es inválido, retorna
    los errores del formulario.
    """
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        """
        Procesa un formulario válido y retorna respuesta JSON.
        
        Args:
            form: Formulario válido de empresa.
            
        Returns:
            JsonResponse: Respuesta JSON con success=True.
        """
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        """
        Procesa un formulario inválido y retorna errores en JSON.
        
        Args:
            form: Formulario inválido de empresa.
            
        Returns:
            JsonResponse: Respuesta JSON con success=False y errores del formulario.
        """
        return JsonResponse({'success': False, 'errors': form.errors})

class EmpresaUpdateView(UpdateView):
    """
    Vista para actualizar una empresa existente.
    
    GET: Retorna los datos de la empresa en JSON.
    POST: Actualiza la empresa usando el formulario y retorna success=True o errores.
    """
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy('empresa_list')

    def get(self, request, *args, **kwargs):
        """
        Retorna los datos de la empresa en formato JSON.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: Datos completos de la empresa en formato JSON.
        """
        empresa = get_object_or_404(Empresa, pk=kwargs['pk'])
        return JsonResponse({
            'id': empresa.id,
            'rut': empresa.rut,
            'dv': empresa.dv,
            'razonSocial': empresa.razonSocial,
            'nomFantasia': empresa.nomFantasia,
            'giro': empresa.giro,
            'direccion': empresa.direccion,
            'telefono': empresa.telefono,
            'email': empresa.email,
            'region': empresa.region.id,
            'comuna': empresa.comuna.id
        })

    def post(self, request, *args, **kwargs):
        """
        Actualiza una empresa existente usando el formulario.
        
        Args:
            request: Objeto HttpRequest con datos POST.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se actualizó correctamente,
                         success=False con errores del formulario si falló.
        """
        empresa = get_object_or_404(Empresa, pk=kwargs['pk'])
        form = self.form_class(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})

class EmpresaDeleteView(DeleteView):
    """
    Vista para eliminar una empresa.
    
    Retorna JSON para interacción AJAX. Maneja errores y retorna
    success=True si se eliminó correctamente.
    """
    model = Empresa
    success_url = reverse_lazy('empresa_list')

    def post(self, request, *args, **kwargs):
        """
        Elimina una empresa existente.
        
        Args:
            request: Objeto HttpRequest.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave, debe contener 'pk'.
            
        Returns:
            JsonResponse: success=True si se eliminó correctamente,
                         success=False con error si falló.
        """
        try:
            empresa = self.get_object()
            empresa.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
