from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Region, Comuna, UnidadMedida, Empresa
from .forms import RegionForm, ComunaForm, UnidadMedidaForm, EmpresaForm

# Create your views here.

class RegionListView(ListView):
    model = Region
    template_name = 'region.html'
    context_object_name = 'regiones'

class RegionCreateView(CreateView):
    model = Region
    form_class = RegionForm
    success_url = reverse_lazy('region_list')

    def form_valid(self, form):
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})

class RegionUpdateView(UpdateView):
    model = Region
    form_class = RegionForm
    success_url = reverse_lazy('region_list')

    def get(self, request, *args, **kwargs):
        region = get_object_or_404(Region, pk=kwargs['pk'])
        return JsonResponse({
            'id': region.id,
            'nombre': region.nombre
        })

    def post(self, request, *args, **kwargs):
        region = get_object_or_404(Region, pk=kwargs['pk'])
        nombre = request.POST.get('nombre')
        
        if nombre:
            region.nombre = nombre
            region.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': 'El nombre es requerido'})

class RegionDeleteView(DeleteView):
    model = Region
    success_url = reverse_lazy('region_list')

    def post(self, request, *args, **kwargs):
        try:
            region = self.get_object()
            region.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class ComunaListView(ListView):
    model = Comuna
    template_name = 'comuna.html'
    context_object_name = 'comunas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ComunaForm()
        return context

class ComunaCreateView(CreateView):
    model = Comuna
    form_class = ComunaForm
    success_url = reverse_lazy('comuna_list')

    def form_valid(self, form):
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})

class ComunaUpdateView(UpdateView):
    model = Comuna
    form_class = ComunaForm
    success_url = reverse_lazy('comuna_list')

    def get(self, request, *args, **kwargs):
        comuna = get_object_or_404(Comuna, pk=kwargs['pk'])
        return JsonResponse({
            'id': comuna.id,
            'nombre': comuna.nombre,
            'region': comuna.region.id
        })

    def post(self, request, *args, **kwargs):
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
    model = Comuna
    success_url = reverse_lazy('comuna_list')

    def post(self, request, *args, **kwargs):
        try:
            comuna = self.get_object()
            comuna.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class UnidadMedidaListView(ListView):
    model = UnidadMedida
    template_name = 'unidad_medida.html'
    context_object_name = 'unidades_medida'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UnidadMedidaForm()
        return context

class UnidadMedidaCreateView(CreateView):
    model = UnidadMedida
    form_class = UnidadMedidaForm
    success_url = reverse_lazy('unidad_medida_list')

    def form_valid(self, form):
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})

class UnidadMedidaUpdateView(UpdateView):
    model = UnidadMedida
    form_class = UnidadMedidaForm
    success_url = reverse_lazy('unidad_medida_list')

    def get(self, request, *args, **kwargs):
        unidad = get_object_or_404(UnidadMedida, pk=kwargs['pk'])
        return JsonResponse({
            'id': unidad.id,
            'codigo': unidad.codigo,
            'descripcion': unidad.descripcion
        })

    def post(self, request, *args, **kwargs):
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
    model = UnidadMedida
    success_url = reverse_lazy('unidad_medida_list')

    def post(self, request, *args, **kwargs):
        try:
            unidad = self.get_object()
            unidad.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def load_comunas(request):
    region_id = request.GET.get('region_id')
    comunas = Comuna.objects.filter(region_id=region_id).order_by('nombre')
    return JsonResponse(list(comunas.values('id', 'nombre')), safe=False)

class EmpresaListView(ListView):
    model = Empresa
    template_name = 'empresa.html'
    context_object_name = 'empresas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EmpresaForm()
        return context

class EmpresaCreateView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})

class EmpresaUpdateView(UpdateView):
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy('empresa_list')

    def get(self, request, *args, **kwargs):
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
        empresa = get_object_or_404(Empresa, pk=kwargs['pk'])
        form = self.form_class(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})

class EmpresaDeleteView(DeleteView):
    model = Empresa
    success_url = reverse_lazy('empresa_list')

    def post(self, request, *args, **kwargs):
        try:
            empresa = self.get_object()
            empresa.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
