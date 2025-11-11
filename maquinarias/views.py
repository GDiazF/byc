from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import Equipo, TipoEquipo, MarcaEquipo, ModeloEquipo, Seccion, TipoReparacion, PautaMantenimientoPreventivo, ItemPauta
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
                equipo.codigoInterno = data['codigoInterno'].strip().upper()
                equipo.patente = data.get('patente', '').strip().upper() if data.get('patente') else None
                equipo.horometro = data.get('horometro')
                equipo.odometro = data.get('odometro')
                equipo.horometroSuperEstructural = data.get('horometroSuperEstructural')
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
                codigoInterno=data['codigoInterno'].strip().upper(),
                patente=data.get('patente', '').strip().upper() if data.get('patente') else None,
                horometro=data.get('horometro'),
                odometro=data.get('odometro'),
                horometroSuperEstructural=data.get('horometroSuperEstructural'),
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


# ==================== VISTAS PARA SECCIONES ====================

def lista_secciones(request):
    """Vista principal para mostrar la tabla de secciones"""
    return render(request, 'maquinarias/lista_secciones.html')


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_secciones(request):
    """API para listar secciones con paginación y búsqueda"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        search = request.GET.get('search', '').strip()
        
        # Query base
        query = Seccion.objects.all()
        
        # Búsqueda
        if search:
            query = query.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Ordenar
        query = query.order_by('nombre')
        
        # Contar total
        total = query.count()
        
        # Paginar
        paginator = Paginator(query, per_page)
        secciones_page = paginator.get_page(page)
        
        # Serializar
        secciones_data = []
        for seccion in secciones_page:
            secciones_data.append({
                'seccion_id': seccion.seccion_id,
                'nombre': seccion.nombre,
                'descripcion': seccion.descripcion or '',
                'total_tipos_reparacion': seccion.tipos_reparacion.count(),
            })
        
        return JsonResponse({
            'success': True,
            'secciones': secciones_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar secciones: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_seccion(request):
    """API para crear o actualizar una sección"""
    try:
        data = json.loads(request.body)
        seccion_id = data.get('seccion_id')
        nombre = data.get('nombre', '').strip().upper()
        descripcion = data.get('descripcion', '').strip()
        
        # Validaciones
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Verificar si ya existe otra sección con el mismo nombre
        existing = Seccion.objects.filter(nombre=nombre).exclude(seccion_id=seccion_id).first()
        if existing:
            return JsonResponse({
                'success': False,
                'message': f'Ya existe una sección con el nombre "{nombre}"'
            }, status=400)
        
        # Crear o actualizar
        if seccion_id:
            # Actualizar
            seccion = Seccion.objects.get(seccion_id=seccion_id)
            seccion.nombre = nombre
            seccion.descripcion = descripcion
            seccion.save()
            message = 'Sección actualizada exitosamente'
        else:
            # Crear
            seccion = Seccion.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            message = 'Sección creada exitosamente'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'seccion': {
                'seccion_id': seccion.seccion_id,
                'nombre': seccion.nombre,
                'descripcion': seccion.descripcion or '',
            }
        })
        
    except Seccion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sección no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar sección: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_seccion(request, seccion_id):
    """API para eliminar una sección"""
    try:
        seccion = Seccion.objects.get(seccion_id=seccion_id)
        
        # Verificar si tiene tipos de reparación asociados
        if seccion.tipos_reparacion.exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la sección "{seccion.nombre}" porque tiene tipos de reparación asociados'
            }, status=400)
        
        # Verificar si está en uso en pautas
        if ItemPauta.objects.filter(seccion_id=seccion).exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la sección "{seccion.nombre}" porque está siendo utilizada en pautas de mantenimiento'
            }, status=400)
        
        nombre = seccion.nombre
        seccion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Sección "{nombre}" eliminada exitosamente'
        })
        
    except Seccion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sección no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar sección: {str(e)}'
        }, status=500)


# ==================== VISTAS PARA TIPOS DE REPARACIÓN ====================

def lista_tipos_reparacion(request):
    """Vista principal para mostrar la tabla de tipos de reparación"""
    secciones = Seccion.objects.all().order_by('nombre')
    
    context = {
        'secciones': secciones,
    }
    
    return render(request, 'maquinarias/lista_tipos_reparacion.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_tipos_reparacion(request):
    """API para listar tipos de reparación con paginación y búsqueda"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        search = request.GET.get('search', '').strip()
        seccion_id = request.GET.get('seccion_id', '').strip()
        
        # Query base con select_related para optimizar
        query = TipoReparacion.objects.select_related('seccion_id')
        
        # Filtro por sección
        if seccion_id:
            query = query.filter(seccion_id=seccion_id)
        
        # Búsqueda
        if search:
            query = query.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(seccion_id__nombre__icontains=search)
            )
        
        # Ordenar
        query = query.order_by('seccion_id__nombre', 'nombre')
        
        # Contar total
        total = query.count()
        
        # Paginar
        paginator = Paginator(query, per_page)
        tipos_page = paginator.get_page(page)
        
        # Serializar
        tipos_data = []
        for tipo in tipos_page:
            tipos_data.append({
                'tipoReparacion_id': tipo.tipoReparacion_id,
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion or '',
                'seccion_id': tipo.seccion_id.seccion_id,
                'seccion_nombre': tipo.seccion_id.nombre,
            })
        
        return JsonResponse({
            'success': True,
            'tipos_reparacion': tipos_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar tipos de reparación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_tipo_reparacion(request):
    """API para crear o actualizar un tipo de reparación"""
    try:
        data = json.loads(request.body)
        tipo_id = data.get('tipoReparacion_id')
        seccion_id = data.get('seccion_id')
        nombre = data.get('nombre', '').strip().upper()
        descripcion = data.get('descripcion', '').strip()
        
        # Validaciones
        if not seccion_id:
            return JsonResponse({
                'success': False,
                'message': 'La sección es requerida'
            }, status=400)
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Verificar que la sección existe
        try:
            seccion = Seccion.objects.get(seccion_id=seccion_id)
        except Seccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'La sección seleccionada no existe'
            }, status=400)
        
        # Verificar si ya existe otro tipo de reparación con el mismo nombre en la misma sección
        existing = TipoReparacion.objects.filter(
            seccion_id=seccion_id,
            nombre=nombre
        ).exclude(tipoReparacion_id=tipo_id).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': f'Ya existe un tipo de reparación "{nombre}" para la sección "{seccion.nombre}"'
            }, status=400)
        
        # Crear o actualizar
        if tipo_id:
            # Actualizar
            tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
            tipo.seccion_id = seccion
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.save()
            message = 'Tipo de reparación actualizado exitosamente'
        else:
            # Crear
            tipo = TipoReparacion.objects.create(
                seccion_id=seccion,
                nombre=nombre,
                descripcion=descripcion
            )
            message = 'Tipo de reparación creado exitosamente'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'tipo_reparacion': {
                'tipoReparacion_id': tipo.tipoReparacion_id,
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion or '',
                'seccion_id': tipo.seccion_id.seccion_id,
                'seccion_nombre': tipo.seccion_id.nombre,
            }
        })
        
    except TipoReparacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Tipo de reparación no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar tipo de reparación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_tipo_reparacion(request, tipo_id):
    """API para eliminar un tipo de reparación"""
    try:
        tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
        
        # Verificar si está en uso en pautas
        if tipo.items_pauta.exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar el tipo de reparación "{tipo.nombre}" porque está siendo utilizado en pautas de mantenimiento'
            }, status=400)
        
        nombre = tipo.nombre
        tipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Tipo de reparación "{nombre}" eliminado exitosamente'
        })
        
    except TipoReparacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Tipo de reparación no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar tipo de reparación: {str(e)}'
        }, status=500)


# ==================== VISTAS PARA PAUTAS DE MANTENIMIENTO ====================

def lista_pautas_mantenimiento(request):
    """Vista principal para mostrar la tabla de pautas de mantenimiento"""
    # Obtener datos para filtros
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
        'modelos': modelos,
    }
    
    return render(request, 'maquinarias/lista_pautas_mantenimiento.html', context)


def ver_pautas_modelo(request, modelo_id):
    """Vista para ver todas las pautas de un modelo específico"""
    try:
        modelo = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',
            'marcaEquipo_id'
        ).get(modeloEquipo_id=modelo_id)
        
        # Obtener todas las pautas del modelo con sus items
        pautas = PautaMantenimientoPreventivo.objects.filter(
            modeloEquipo_id=modelo
        ).prefetch_related('items__seccion_id', 'items__tipos_reparacion').order_by('-activo', 'nombre')
        
        context = {
            'modelo': modelo,
            'pautas': pautas,
        }
        
        return render(request, 'maquinarias/ver_pautas_modelo.html', context)
        
    except ModeloEquipo.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Modelo de equipo no encontrado')
        return redirect('maquinarias:lista_pautas_mantenimiento')


def crear_pauta_mantenimiento(request):
    """Vista para crear una nueva pauta de mantenimiento"""
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')
    secciones = Seccion.objects.all().order_by('nombre')
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')
    
    # Capturar modelo_id de la URL si existe (para pre-selección)
    modelo_id_param = request.GET.get('modelo', None)
    modelo_preseleccionado = None
    
    if modelo_id_param:
        try:
            modelo_preseleccionado = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').get(modeloEquipo_id=modelo_id_param)
        except ModeloEquipo.DoesNotExist:
            pass
    
    context = {
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
        'modelos': modelos,
        'secciones': secciones,
        'tipos_reparacion': tipos_reparacion,
        'es_edicion': False,
        'modelo_preseleccionado': modelo_preseleccionado,
    }
    
    return render(request, 'maquinarias/form_pauta_mantenimiento.html', context)


def editar_pauta_mantenimiento(request, pauta_id):
    """Vista para editar una pauta de mantenimiento existente"""
    try:
        pauta = PautaMantenimientoPreventivo.objects.select_related('modeloEquipo_id').get(pauta_id=pauta_id)
        
        tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
        marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
        modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')
        secciones = Seccion.objects.all().order_by('nombre')
        tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')
        
        # Obtener los items actuales de la pauta con sus tipos de reparación
        items = ItemPauta.objects.filter(pauta_id=pauta).select_related('seccion_id').prefetch_related('tipos_reparacion')
        
        context = {
            'pauta': pauta,
            'tipos_equipo': tipos_equipo,
            'marcas': marcas,
            'modelos': modelos,
            'secciones': secciones,
            'tipos_reparacion': tipos_reparacion,
            'items': items,
            'es_edicion': True,
        }
        
        return render(request, 'maquinarias/form_pauta_mantenimiento.html', context)
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Pauta de mantenimiento no encontrada')
        return redirect('maquinarias:lista_pautas_mantenimiento')


@csrf_exempt
@require_http_methods(["GET"])
def api_listar_pautas_mantenimiento(request):
    """API para listar TODOS los modelos de equipo con sus pautas (o sin pautas)"""
    try:
        from django.db.models import Count
        
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        search = request.GET.get('search', '').strip()
        tipo_equipo_id = request.GET.get('tipo_equipo_id', '').strip()
        marca_id = request.GET.get('marca_id', '').strip()
        modelo_id = request.GET.get('modelo_id', '').strip()
        order_by = request.GET.get('order_by', '').strip()
        direction = request.GET.get('direction', 'asc').strip()
        
        # Query para TODOS los modelos (tengan o no pautas)
        modelos_query = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',
            'marcaEquipo_id'
        ).annotate(
            total_pautas=Count('pautas_mantenimiento')
        )
        
        # Filtros
        if tipo_equipo_id:
            modelos_query = modelos_query.filter(tipoEquipo_id=tipo_equipo_id)
        
        if marca_id:
            modelos_query = modelos_query.filter(marcaEquipo_id=marca_id)
        
        if modelo_id:
            modelos_query = modelos_query.filter(modeloEquipo_id=modelo_id)
        
        # Búsqueda
        if search:
            modelos_query = modelos_query.filter(
                Q(modeloEquipo__icontains=search) |
                Q(tipoEquipo_id__tipoEquipo__icontains=search) |
                Q(marcaEquipo_id__marcaEquipo__icontains=search)
            )
        
        # Ordenamiento
        order_field = 'modeloEquipo'  # Por defecto
        if order_by == 'tipo':
            order_field = 'tipoEquipo_id__tipoEquipo'
        elif order_by == 'marca':
            order_field = 'marcaEquipo_id__marcaEquipo'
        elif order_by == 'modelo':
            order_field = 'modeloEquipo'
        elif order_by == 'pautas':
            order_field = 'total_pautas'
        
        if direction == 'desc':
            order_field = '-' + order_field
        
        modelos_query = modelos_query.order_by(order_field)
        
        # Contar total de modelos
        total = modelos_query.count()
        
        # Paginar modelos
        paginator = Paginator(modelos_query, per_page)
        modelos_page = paginator.get_page(page)
        
        # Serializar modelos con sus pautas
        modelos_data = []
        for modelo in modelos_page:
            modelos_data.append({
                'modeloEquipo': {
                    'modeloEquipo_id': modelo.modeloEquipo_id,
                    'nombre': modelo.modeloEquipo,
                },
                'tipoEquipo': {
                    'tipoEquipo_id': modelo.tipoEquipo_id.tipoEquipo_id,
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,
                    'sigla': modelo.tipoEquipo_id.siglaEquipo,
                },
                'marcaEquipo': {
                    'marcaEquipo_id': modelo.marcaEquipo_id.marcaEquipo_id,
                    'nombre': modelo.marcaEquipo_id.marcaEquipo,
                },
                'total_pautas': modelo.total_pautas,  # Usamos el annotate
            })
        
        return JsonResponse({
            'success': True,
            'modelos': modelos_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar modelos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_pautas_por_modelo(request, modelo_id):
    """API para obtener todas las pautas de un modelo específico con detalles completos"""
    try:
        modelo = ModeloEquipo.objects.select_related(
            'tipoEquipo_id',
            'marcaEquipo_id'
        ).get(modeloEquipo_id=modelo_id)
        
        # Obtener todas las pautas del modelo con sus items
        pautas = PautaMantenimientoPreventivo.objects.filter(
            modeloEquipo_id=modelo
        ).prefetch_related('items__seccion_id', 'items__tipos_reparacion').order_by('-activo', 'nombre')
        
        pautas_data = []
        for pauta in pautas:
            # Obtener items con tipos de reparación
            items_data = []
            for item in pauta.items.all():
                tipos_reparacion = []
                for tipo in item.tipos_reparacion.all():
                    tipos_reparacion.append({
                        'tipoReparacion_id': tipo.tipoReparacion_id,
                        'nombre': tipo.nombre,
                        'descripcion': tipo.descripcion or '',
                    })
                
                items_data.append({
                    'seccion': {
                        'seccion_id': item.seccion_id.seccion_id,
                        'nombre': item.seccion_id.nombre,
                    },
                    'tipos_reparacion': tipos_reparacion
                })
            
            pautas_data.append({
                'pauta_id': pauta.pauta_id,
                'nombre': pauta.nombre,
                'descripcion': pauta.descripcion or '',
                'activo': pauta.activo,
                'items': items_data,
                'total_items': len(items_data),
                'fecha_creacion': pauta.fecha_creacion.strftime('%Y-%m-%d'),
                'fecha_modificacion': pauta.fecha_modificacion.strftime('%Y-%m-%d %H:%M'),
            })
        
        return JsonResponse({
            'success': True,
            'modelo': {
                'modeloEquipo_id': modelo.modeloEquipo_id,
                'nombre': modelo.modeloEquipo,
                'tipoEquipo': {
                    'tipoEquipo_id': modelo.tipoEquipo_id.tipoEquipo_id,
                    'nombre': modelo.tipoEquipo_id.tipoEquipo,
                    'sigla': modelo.tipoEquipo_id.siglaEquipo,
                },
                'marcaEquipo': {
                    'marcaEquipo_id': modelo.marcaEquipo_id.marcaEquipo_id,
                    'nombre': modelo.marcaEquipo_id.marcaEquipo,
                },
            },
            'pautas': pautas_data
        })
        
    except ModeloEquipo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Modelo de equipo no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cargar pautas del modelo: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_pauta_mantenimiento(request):
    """API para crear o actualizar una pauta de mantenimiento"""
    try:
        from django.db import transaction
        
        data = json.loads(request.body)
        pauta_id = data.get('pauta_id')
        modelo_equipo_id = data.get('modeloEquipo_id')
        nombre = data.get('nombre', '').strip().upper()
        descripcion = data.get('descripcion', '').strip()
        items_data = data.get('items', [])  # Lista de {seccion_id, tipos_reparacion_ids[]}
        
        # Validaciones
        if not modelo_equipo_id:
            return JsonResponse({
                'success': False,
                'message': 'El modelo de equipo es requerido'
            }, status=400)
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'message': 'El nombre es requerido'
            }, status=400)
        
        # Verificar que el modelo existe
        try:
            modelo = ModeloEquipo.objects.get(modeloEquipo_id=modelo_equipo_id)
        except ModeloEquipo.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'El modelo de equipo seleccionado no existe'
            }, status=400)
        
        with transaction.atomic():
            # Crear o actualizar la pauta
            if pauta_id:
                # Actualizar
                pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
                pauta.modeloEquipo_id = modelo
                pauta.nombre = nombre
                pauta.descripcion = descripcion
                pauta.save()
                
                # Eliminar items antiguos
                ItemPauta.objects.filter(pauta_id=pauta).delete()
                
                message = 'Pauta de mantenimiento actualizada exitosamente'
            else:
                # Crear
                pauta = PautaMantenimientoPreventivo.objects.create(
                    modeloEquipo_id=modelo,
                    nombre=nombre,
                    descripcion=descripcion
                )
                message = 'Pauta de mantenimiento creada exitosamente'
            
            # Crear los nuevos items
            for item_data in items_data:
                seccion_id = item_data.get('seccion_id')
                tipos_ids = item_data.get('tipos_reparacion_ids', [])
                
                if not seccion_id or not tipos_ids:
                    continue
                
                try:
                    seccion = Seccion.objects.get(seccion_id=seccion_id)
                    
                    # Crear el ItemPauta
                    item = ItemPauta.objects.create(
                        pauta_id=pauta,
                        seccion_id=seccion
                    )
                    
                    # Agregar los tipos de reparación
                    for tipo_id in tipos_ids:
                        try:
                            tipo = TipoReparacion.objects.get(tipoReparacion_id=tipo_id)
                            item.tipos_reparacion.add(tipo)
                        except TipoReparacion.DoesNotExist:
                            pass
                    
                except Seccion.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'message': message,
            'pauta_id': pauta.pauta_id
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar pauta de mantenimiento: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_toggle_activo_pauta(request, pauta_id):
    """API para activar/desactivar una pauta de mantenimiento"""
    try:
        pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
        pauta.activo = not pauta.activo
        pauta.save()
        
        estado = "activada" if pauta.activo else "desactivada"
        
        return JsonResponse({
            'success': True,
            'message': f'Pauta "{pauta.nombre}" {estado} exitosamente',
            'activo': pauta.activo
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar estado: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_pauta(request, pauta_id):
    """API para eliminar una pauta de mantenimiento"""
    try:
        pauta = PautaMantenimientoPreventivo.objects.get(pauta_id=pauta_id)
        nombre = pauta.nombre
        pauta.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Pauta "{nombre}" eliminada exitosamente'
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar pauta: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_pauta(request, pauta_id):
    """API para obtener el detalle completo de una pauta con sus items"""
    try:
        pauta = PautaMantenimientoPreventivo.objects.select_related(
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).get(pauta_id=pauta_id)
        
        # Obtener items con sus tipos de reparación
        items = ItemPauta.objects.filter(pauta_id=pauta).select_related('seccion_id').prefetch_related('tipos_reparacion')
        
        items_data = []
        for item in items:
            tipos_reparacion = []
            for tipo in item.tipos_reparacion.all():
                tipos_reparacion.append({
                    'tipoReparacion_id': tipo.tipoReparacion_id,
                    'nombre': tipo.nombre,
                    'descripcion': tipo.descripcion or '',
                })
            
            items_data.append({
                'itemPauta_id': item.itemPauta_id,
                'seccion': {
                    'seccion_id': item.seccion_id.seccion_id,
                    'nombre': item.seccion_id.nombre,
                },
                'tipos_reparacion': tipos_reparacion
            })
        
        pauta_data = {
            'pauta_id': pauta.pauta_id,
            'nombre': pauta.nombre,
            'descripcion': pauta.descripcion or '',
            'activo': pauta.activo,
            'modeloEquipo': {
                'modeloEquipo_id': pauta.modeloEquipo_id.modeloEquipo_id,
                'nombre': pauta.modeloEquipo_id.modeloEquipo,
                'tipoEquipo_id': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo_id,
                'marcaEquipo_id': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo_id,
            },
            'tipoEquipo': {
                'tipoEquipo_id': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo_id,
                'nombre': pauta.modeloEquipo_id.tipoEquipo_id.tipoEquipo,
                'sigla': pauta.modeloEquipo_id.tipoEquipo_id.siglaEquipo,
            },
            'marcaEquipo': {
                'marcaEquipo_id': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo_id,
                'nombre': pauta.modeloEquipo_id.marcaEquipo_id.marcaEquipo,
            },
            'items': items_data,
            'fecha_creacion': pauta.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            'fecha_modificacion': pauta.fecha_modificacion.strftime('%Y-%m-%d %H:%M'),
        }
        
        return JsonResponse({
            'success': True,
            'pauta': pauta_data
        })
        
    except PautaMantenimientoPreventivo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pauta de mantenimiento no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de pauta: {str(e)}'
        }, status=500)
