from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import Equipo, TipoEquipo, MarcaEquipo, ModeloEquipo
from gen_settings.models import Empresa


def lista_equipos(request):
    """Vista principal para mostrar la tabla de equipos activos"""
    # Obtener datos para los filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    modelos = ModeloEquipo.objects.all().order_by('modeloEquipo')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
        'modelos': modelos,
    }
    
    return render(request, 'maquinarias/lista_equipos.html', context)


def equipos_desactivados(request):
    """Vista para mostrar equipos desactivados"""
    # Obtener datos para los filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
    }
    
    return render(request, 'maquinarias/equipos_desactivados.html', context)


def crear_equipo(request):
    """Vista para mostrar el formulario de crear equipo"""
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'es_edicion': False
    }
    
    return render(request, 'maquinarias/form_equipo.html', context)


def editar_equipo(request, equipo_id):
    """Vista para mostrar el formulario de editar equipo"""
    try:
        equipo = Equipo.objects.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).get(equipo_id=equipo_id)
        
        empresas = Empresa.objects.all().order_by('nomFantasia')
        tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
        
        context = {
            'empresas': empresas,
            'tipos_equipo': tipos_equipo,
            'equipo': equipo,
            'es_edicion': True
        }
        
        return render(request, 'maquinarias/form_equipo.html', context)
    
    except Equipo.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Equipo no encontrado')
        from django.shortcuts import redirect
        return redirect('maquinarias:lista_equipos')


def api_listar_equipos(request):
    """API para listar equipos con filtros y paginación"""
    try:
        # Parámetros de búsqueda y filtros
        search = request.GET.get('search', '').strip()
        empresa_id = request.GET.get('empresa', '')
        tipo_id = request.GET.get('tipo', '')
        marca_id = request.GET.get('marca', '')
        modelo_id = request.GET.get('modelo', '')
        estado = request.GET.get('estado', 'activos')  # activos, inactivos, todos
        
        # Paginación
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        
        # Consulta base
        equipos = Equipo.objects.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).all()
        
        # Filtros
        if estado == 'activos':
            equipos = equipos.filter(activo=True)
        elif estado == 'inactivos':
            equipos = equipos.filter(activo=False)
        
        if empresa_id:
            equipos = equipos.filter(empresa_id=empresa_id)
        
        if tipo_id:
            equipos = equipos.filter(modeloEquipo_id__tipoEquipo_id=tipo_id)
        
        if marca_id:
            equipos = equipos.filter(modeloEquipo_id__marcaEquipo_id=marca_id)
        
        if modelo_id:
            equipos = equipos.filter(modeloEquipo_id=modelo_id)
        
        if search:
            equipos = equipos.filter(
                Q(nombreEquipo__icontains=search) |
                Q(codigoInterno__icontains=search) |
                Q(patente__icontains=search) |
                Q(modeloEquipo_id__marcaEquipo_id__marcaEquipo__icontains=search) |
                Q(modeloEquipo_id__modeloEquipo__icontains=search)
            )
        
        # Ordenar
        equipos = equipos.order_by('-activo', 'modeloEquipo_id__tipoEquipo_id__tipoEquipo', 'codigoInterno')
        
        # Paginación
        paginator = Paginator(equipos, page_size)
        page_obj = paginator.get_page(page)
        
        # Serializar datos
        equipos_data = []
        for equipo in page_obj:
            modelo = equipo.modeloEquipo_id
            equipos_data.append({
                'equipo_id': equipo.equipo_id,
                'nombreEquipo': equipo.nombreEquipo,
                'codigoInterno': equipo.codigoInterno,
                'patente': equipo.patente or '-',
                'empresa': {
                    'id': equipo.empresa_id.id,
                    'nombre': equipo.empresa_id.nomFantasia
                },
                'tipoEquipo': {
                    'id': modelo.tipoEquipo_id.tipoEquipo_id,
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,
                    'sigla': modelo.tipoEquipo_id.siglaEquipo
                },
                'marcaEquipo': {
                    'id': modelo.marcaEquipo_id.marcaEquipo_id,
                    'nombre': modelo.marcaEquipo_id.marcaEquipo
                },
                'modeloEquipo': {
                    'id': modelo.modeloEquipo_id,
                    'nombre': modelo.modeloEquipo
                },
                'horometro': equipo.horometro,
                'odometro': equipo.odometro,
                'horometroSuperEstructural': equipo.horometroSuperEstructural,
                'activo': equipo.activo
            })
        
        return JsonResponse({
            'success': True,
            'equipos': equipos_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'page_size': page_size
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_equipo(request):
    """API unificada para crear o editar un equipo"""
    try:
        data = json.loads(request.body)
        equipo_id = data.get('equipo_id')
        
        # Validar datos requeridos
        required_fields = ['empresa_id', 'modeloEquipo_id', 'codigoInterno']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'El campo {field} es requerido'
                }, status=400)
        
        # Si es edición
        if equipo_id:
            try:
                equipo = Equipo.objects.get(equipo_id=equipo_id)
                
                # Verificar unicidad de código interno por modelo (excluyendo el equipo actual)
                if Equipo.objects.filter(
                    modeloEquipo_id=data['modeloEquipo_id'],
                    codigoInterno=data['codigoInterno']
                ).exclude(equipo_id=equipo_id).exists():
                    modelo = ModeloEquipo.objects.get(modeloEquipo_id=data['modeloEquipo_id'])
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe otro equipo del modelo {modelo.modeloEquipo} con el código interno {data["codigoInterno"]}'
                    }, status=400)
                
                # Actualizar campos
                equipo.empresa_id_id = data['empresa_id']
                equipo.modeloEquipo_id_id = data['modeloEquipo_id']
                equipo.codigoInterno = data['codigoInterno']
                equipo.patente = data.get('patente', '').strip() or None
                equipo.horometro = data.get('horometro', 0)
                equipo.odometro = data.get('odometro', 0)
                equipo.horometroSuperEstructural = data.get('horometroSuperEstructural', 0)
                equipo.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Equipo {equipo.nombreEquipo} actualizado exitosamente',
                    'equipo_id': equipo.equipo_id
                })
            
            except Equipo.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Equipo no encontrado'}, status=404)
        
        # Si es creación
        else:
            # Verificar unicidad de código interno por modelo
            if Equipo.objects.filter(
                modeloEquipo_id=data['modeloEquipo_id'],
                codigoInterno=data['codigoInterno']
            ).exists():
                modelo = ModeloEquipo.objects.get(modeloEquipo_id=data['modeloEquipo_id'])
                return JsonResponse({
                    'success': False,
                    'error': f'Ya existe un equipo del modelo {modelo.modeloEquipo} con el código interno {data["codigoInterno"]}'
                }, status=400)
            
            # Crear equipo
            equipo = Equipo.objects.create(
                empresa_id_id=data['empresa_id'],
                modeloEquipo_id_id=data['modeloEquipo_id'],
                codigoInterno=data['codigoInterno'],
                patente=data.get('patente', '').strip() or None,
                horometro=data.get('horometro', 0),
                odometro=data.get('odometro', 0),
                horometroSuperEstructural=data.get('horometroSuperEstructural', 0),
                activo=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Equipo {equipo.nombreEquipo} creado exitosamente',
                'equipo_id': equipo.equipo_id
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_eliminar_equipo(request, equipo_id):
    """API para eliminar un equipo"""
    try:
        equipo = Equipo.objects.get(equipo_id=equipo_id)
        nombre = equipo.nombreEquipo
        equipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Equipo {nombre} eliminado exitosamente'
        })
    
    except Equipo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Equipo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_toggle_activo_equipo(request, equipo_id):
    """API para activar/desactivar un equipo"""
    try:
        equipo = Equipo.objects.get(equipo_id=equipo_id)
        equipo.activo = not equipo.activo
        equipo.save()
        
        estado = 'activado' if equipo.activo else 'desactivado'
        return JsonResponse({
            'success': True,
            'message': f'Equipo {equipo.nombreEquipo} {estado} exitosamente',
            'activo': equipo.activo
        })
    
    except Equipo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Equipo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_tipos_equipo(request):
    """API para obtener tipos de equipo"""
    try:
        tipos = TipoEquipo.objects.all().order_by('tipoEquipo')
        tipos_data = [{
            'id': tipo.tipoEquipo_id,
            'nombre': tipo.tipoEquipo,
            'sigla': tipo.siglaEquipo
        } for tipo in tipos]
        
        return JsonResponse({'success': True, 'tipos': tipos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_marcas_equipo(request):
    """API para obtener marcas de equipo"""
    try:
        marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
        marcas_data = [{
            'id': marca.marcaEquipo_id,
            'nombre': marca.marcaEquipo
        } for marca in marcas]
        
        return JsonResponse({'success': True, 'marcas': marcas_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_modelos_equipo(request):
    """API para obtener modelos de equipo filtrados por tipo y marca"""
    try:
        tipo_id = request.GET.get('tipo_id')
        marca_id = request.GET.get('marca_id')
        
        modelos = ModeloEquipo.objects.all()
        
        # Filtrar por tipo si se proporciona
        if tipo_id:
            modelos = modelos.filter(tipoEquipo_id=tipo_id)
        
        # Filtrar por marca si se proporciona
        if marca_id:
            modelos = modelos.filter(marcaEquipo_id=marca_id)
        
        modelos = modelos.select_related('tipoEquipo_id', 'marcaEquipo_id').order_by('modeloEquipo')
        
        modelos_data = [{
            'id': modelo.modeloEquipo_id,
            'nombre': modelo.modeloEquipo,
            'tipo_id': modelo.tipoEquipo_id.tipoEquipo_id,
            'tipo_nombre': modelo.tipoEquipo_id.tipoEquipo,
            'tipo_sigla': modelo.tipoEquipo_id.siglaEquipo,
            'marca_id': modelo.marcaEquipo_id.marcaEquipo_id,
            'marca_nombre': modelo.marcaEquipo_id.marcaEquipo
        } for modelo in modelos]
        
        return JsonResponse({'success': True, 'modelos': modelos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ficha_tecnica_equipo(request, equipo_id):
    """Vista para mostrar la ficha técnica del equipo"""
    try:
        equipo = Equipo.objects.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).get(equipo_id=equipo_id)
        
        context = {
            'equipo': equipo,
        }
        
        return render(request, 'maquinarias/ficha_tecnica.html', context)
    
    except Equipo.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Equipo no encontrado')
        return redirect('maquinarias:lista_equipos')


def documentacion_equipo(request, equipo_id):
    """Vista para mostrar la documentación del equipo"""
    try:
        equipo = Equipo.objects.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).get(equipo_id=equipo_id)
        
        context = {
            'equipo': equipo,
        }
        
        return render(request, 'maquinarias/documentacion.html', context)
    
    except Equipo.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Equipo no encontrado')
        return redirect('maquinarias:lista_equipos')
