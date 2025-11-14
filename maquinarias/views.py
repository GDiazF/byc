from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
import json

from .models import (
    Equipo, TipoEquipo, MarcaEquipo, ModeloEquipo, Seccion, TipoReparacion, 
    PautaMantenimientoPreventivo, ItemPauta, TipoDocumentoMaquinaria, 
    DocumentoMaquinaria, HistorialDocumentoMaquinaria,
    TipoMantenimiento, EstadoOT, EstadoEquipo,
    OrdenTrabajo, ItemSeccionOT, HistorialObservacionesOT, HistorialOT
)
from gen_settings.models import Empresa
from rrhh_personal.models import Personal, InfoLaboral, Cargo
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, date


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
        
        return JsonResponse({
            'status': 'success',
            'activo': equipo.activo
        })
    
    except Equipo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Equipo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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


@login_required
def documentacion_equipo(request, equipo_id):
    """Vista para mostrar la documentación del equipo"""
    try:
        equipo = Equipo.objects.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        ).get(equipo_id=equipo_id)
        
        # Obtener tipos de documentos activos
        tipos_documentos = TipoDocumentoMaquinaria.objects.filter(activo=True).order_by('nombre')
        
        context = {
            'equipo': equipo,
            'tipos_documentos': tipos_documentos,
        }
        
        return render(request, 'maquinarias/documentacion.html', context)
    
    except Equipo.DoesNotExist:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Equipo no encontrado')
        return redirect('maquinarias:lista_equipos')


# ============================================================================
# APIs PARA DOCUMENTACIÓN DE MAQUINARIAS
# ============================================================================

@login_required
@csrf_exempt
def api_tipos_documentos_maquinaria(request):
    """API para listar tipos de documentos de maquinaria activos"""
    try:
        tipos = TipoDocumentoMaquinaria.objects.filter(activo=True).order_by('nombre')
        tipos_data = [{
            'id': tipo.tipoDocumento_id,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'requiere_fecha_vencimiento': tipo.requiere_fecha_vencimiento
        } for tipo in tipos]
        
        return JsonResponse({'success': True, 'tipos': tipos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_documentos_equipo(request, equipo_id):
    """API para listar documentos de un equipo"""
    try:
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        documentos = DocumentoMaquinaria.objects.filter(
            equipo_id=equipo
        ).select_related('tipo_documento_id').order_by('tipo_documento_id__nombre')
        
        documentos_data = []
        for doc in documentos:
            estado = 'vigente'
            dias_restantes = None
            if doc.fecha_vencimiento:
                dias_restantes = (doc.fecha_vencimiento - date.today()).days
                if dias_restantes < 0:
                    estado = 'vencido'
                elif dias_restantes <= 30:
                    estado = 'por_vencer'
            
            documentos_data.append({
                'id': doc.documento_id,
                'tipo_documento_id': doc.tipo_documento_id.tipoDocumento_id,
                'tipo_documento_nombre': doc.tipo_documento_id.nombre,
                'archivo_url': doc.archivo.url if doc.archivo else None,
                'archivo_nombre': doc.archivo.name.split('/')[-1] if doc.archivo else None,
                'fecha_vencimiento': doc.fecha_vencimiento.isoformat() if doc.fecha_vencimiento else None,
                'fecha_subida': doc.fecha_subida.isoformat(),
                'observaciones': doc.observaciones or '',
                'estado': estado,
                'dias_restantes': dias_restantes
            })
        
        return JsonResponse({'success': True, 'documentos': documentos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_subir_documento_maquinaria(request, equipo_id):
    """API para subir/actualizar un documento de maquinaria con lógica de reemplazo automático"""
    try:
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        tipo_documento_id = request.POST.get('tipo_documento_id')
        archivo = request.FILES.get('archivo')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '').strip()
        
        if not tipo_documento_id or not archivo:
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos requeridos (tipo_documento_id, archivo)'
            }, status=400)
        
        # Validar que solo sea PDF
        if not archivo.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'Solo se aceptan archivos PDF'
            }, status=400)
        
        tipo_documento = get_object_or_404(TipoDocumentoMaquinaria, tipoDocumento_id=tipo_documento_id, activo=True)
        
        # Validar fecha de vencimiento si es requerida
        if tipo_documento.requiere_fecha_vencimiento and not fecha_vencimiento:
            return JsonResponse({
                'success': False,
                'error': f'El documento "{tipo_documento.nombre}" requiere una fecha de vencimiento'
            }, status=400)
        
        # Convertir fecha_vencimiento si existe
        fecha_vencimiento_obj = None
        if fecha_vencimiento:
            try:
                fecha_vencimiento_obj = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Formato de fecha inválido'
                }, status=400)
        
        # Verificar si ya existe un documento de este tipo para este equipo
        documento_existente = DocumentoMaquinaria.objects.filter(
            equipo_id=equipo,
            tipo_documento_id=tipo_documento
        ).first()
        
        # Si existe, moverlo al historial
        if documento_existente:
            # Crear registro en historial
            historial = HistorialDocumentoMaquinaria(
                equipo_id=equipo,
                tipo_documento_id=tipo_documento,
                tipo_documento_nombre=tipo_documento.nombre,
                fecha_vencimiento=documento_existente.fecha_vencimiento,
                fecha_subida_original=documento_existente.fecha_subida,
                observaciones=documento_existente.observaciones
            )
            
            # Guardar el historial primero para tener la instancia
            historial.save()
            
            # Copiar el archivo al historial
            if documento_existente.archivo:
                try:
                    # Copiar el archivo usando el método del FileField
                    historial.archivo.save(
                        documento_existente.archivo.name.split('/')[-1],
                        documento_existente.archivo,
                        save=True
                    )
                except Exception as e:
                    # Si falla la copia, eliminar el historial creado
                    historial.delete()
                    return JsonResponse({
                        'success': False,
                        'error': f'Error al copiar archivo al historial: {str(e)}'
                    }, status=500)
            
            # Eliminar el documento existente (esto también eliminará el archivo original)
            documento_existente.delete()
        
        # Crear nuevo documento
        nuevo_documento = DocumentoMaquinaria(
            equipo_id=equipo,
            tipo_documento_id=tipo_documento,
            fecha_vencimiento=fecha_vencimiento_obj,
            observaciones=observaciones
        )
        nuevo_documento.archivo = archivo
        nuevo_documento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Documento subido correctamente',
            'documento_id': nuevo_documento.documento_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def api_eliminar_documento_maquinaria(request, documento_id):
    """API para eliminar un documento de maquinaria (lo mueve al historial)"""
    try:
        documento = get_object_or_404(DocumentoMaquinaria, documento_id=documento_id)
        
        # Crear registro en historial
        historial = HistorialDocumentoMaquinaria(
            equipo_id=documento.equipo_id,
            tipo_documento_id=documento.tipo_documento_id,
            tipo_documento_nombre=documento.tipo_documento_id.nombre,
            fecha_vencimiento=documento.fecha_vencimiento,
            fecha_subida_original=documento.fecha_subida,
            observaciones=documento.observaciones
        )
        historial.save()
        
        # Copiar el archivo al historial
        if documento.archivo:
            try:
                # Guardar el historial primero para tener la instancia
                historial.save()
                
                # Copiar el archivo usando el método del FileField
                historial.archivo.save(
                    documento.archivo.name.split('/')[-1],
                    documento.archivo,
                    save=True
                )
            except Exception as e:
                historial.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Error al copiar archivo al historial: {str(e)}'
                }, status=500)
        
        # Eliminar el documento
        documento.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Documento eliminado y movido al historial'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
def api_historial_documentos_equipo(request, equipo_id):
    """API para listar el historial de documentos de un equipo"""
    try:
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        historial = HistorialDocumentoMaquinaria.objects.filter(
            equipo_id=equipo
        ).order_by('-fecha_reemplazo')
        
        historial_data = []
        for item in historial:
            historial_data.append({
                'id': item.historial_id,
                'tipo_documento_nombre': item.tipo_documento_nombre,
                'archivo_url': item.archivo.url if item.archivo else None,
                'archivo_nombre': item.archivo.name.split('/')[-1] if item.archivo else None,
                'fecha_vencimiento': item.fecha_vencimiento.isoformat() if item.fecha_vencimiento else None,
                'fecha_subida_original': item.fecha_subida_original.isoformat() if item.fecha_subida_original else None,
                'fecha_reemplazo': item.fecha_reemplazo.isoformat(),
                'observaciones': item.observaciones or ''
            })
        
        return JsonResponse({'success': True, 'historial': historial_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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


# ============================================================================
# VISTAS PARA ORDEN DE TRABAJO (OT)
# ============================================================================

@login_required
def lista_ordenes_trabajo(request):
    """Vista principal para mostrar la lista de ordenes de trabajo"""
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'tipos_mantenimiento': tipos_mantenimiento,
        'estados_ot': estados_ot,
    }
    
    return render(request, 'maquinarias/lista_ordenes_trabajo.html', context)


@login_required
def crear_orden_trabajo(request):
    """Vista para crear una nueva orden de trabajo"""
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')
    secciones = Seccion.objects.all().order_by('nombre')
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')
    
    # Obtener tipos de mantenimiento, estados OT y estados equipo
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')
    estados_equipo = EstadoEquipo.objects.filter(activo=True).order_by('orden', 'nombre')
    
    context = {
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
        'modelos': modelos,
        'secciones': secciones,
        'tipos_reparacion': tipos_reparacion,
        'tipos_mantenimiento': tipos_mantenimiento,
        'estados_ot': estados_ot,
        'estados_equipo': estados_equipo,
        'es_edicion': False,
    }
    
    return render(request, 'maquinarias/form_orden_trabajo.html', context)


@login_required
def editar_orden_trabajo(request, ot_id):
    """Vista para editar una orden de trabajo existente"""
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
    
    # Verificar si la OT está finalizada o cancelada
    estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
    estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
    if (estado_finalizada and ot.estado_ot_id == estado_finalizada) or (estado_cancelada and ot.estado_ot_id == estado_cancelada):
        messages.error(request, 'No se puede editar una orden de trabajo finalizada o cancelada.')
        return redirect('maquinarias:lista_ordenes_trabajo')
    
    empresas = Empresa.objects.all().order_by('nomFantasia')
    tipos_equipo = TipoEquipo.objects.all().order_by('tipoEquipo')
    marcas = MarcaEquipo.objects.all().order_by('marcaEquipo')
    modelos = ModeloEquipo.objects.select_related('tipoEquipo_id', 'marcaEquipo_id').all().order_by('modeloEquipo')
    secciones = Seccion.objects.all().order_by('nombre')
    tipos_reparacion = TipoReparacion.objects.select_related('seccion_id').all().order_by('seccion_id__nombre', 'nombre')
    
    # Obtener tipos de mantenimiento, estados OT y estados equipo
    tipos_mantenimiento = TipoMantenimiento.objects.filter(activo=True).order_by('nombre')
    estados_ot = EstadoOT.objects.filter(activo=True).order_by('orden', 'nombre')
    estados_equipo = EstadoEquipo.objects.filter(activo=True).order_by('orden', 'nombre')
    
    # Obtener items de secciones de la OT
    items_secciones = ItemSeccionOT.objects.filter(ot_id=ot).prefetch_related('tipos_reparacion', 'estado_seccion_id', 'seccion_id')
    
    # Obtener historial de observaciones
    historial_observaciones = HistorialObservacionesOT.objects.filter(ot_id=ot).order_by('-fecha')
    
    context = {
        'ot': ot,
        'empresas': empresas,
        'tipos_equipo': tipos_equipo,
        'marcas': marcas,
        'modelos': modelos,
        'secciones': secciones,
        'tipos_reparacion': tipos_reparacion,
        'tipos_mantenimiento': tipos_mantenimiento,
        'estados_ot': estados_ot,
        'estados_equipo': estados_equipo,
        'items_secciones': items_secciones,
        'historial_observaciones': historial_observaciones,
        'es_edicion': True,
    }
    
    return render(request, 'maquinarias/form_orden_trabajo.html', context)


# ============================================================================
# APIs PARA ORDEN DE TRABAJO
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_listar_ordenes_trabajo(request):
    """API para listar ordenes de trabajo con filtros y paginación"""
    try:
        # Verificar y actualizar OTs con fecha de fin vencida
        estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
        estado_disponible = EstadoEquipo.objects.filter(nombre__iexact='Disponible').first()
        
        if estado_finalizada and estado_disponible:
            hoy = date.today()
            # Buscar OTs activas con fecha de fin vencida
            ots_vencidas = OrdenTrabajo.objects.filter(
                fecha_fin__lt=hoy,
                estado_ot_id__isnull=False
            ).exclude(
                estado_ot_id=estado_finalizada
            ).select_related('estado_ot_id', 'estado_equipo_id')
            
            for ot in ots_vencidas:
                estado_ot_anterior = ot.estado_ot_id
                estado_equipo_anterior = ot.estado_equipo_id
                
                # Cambiar estado OT a FINALIZADA
                ot.estado_ot_id = estado_finalizada
                
                # Cambiar estado equipo a DISPONIBLE
                ot.estado_equipo_id = estado_disponible
                ot.save()
                
                # Registrar en historial
                HistorialOT.registrar(
                    ot=ot,
                    accion='ESTADO_OT_CAMBIADO',
                    descripcion=f"OT finalizada automáticamente por vencimiento de fecha de fin (fecha fin: {ot.fecha_fin.strftime('%d/%m/%Y')}). Estado cambiado de '{estado_ot_anterior.nombre if estado_ot_anterior else 'N/A'}' a '{estado_finalizada.nombre}'",
                    usuario=None,  # Sistema automático
                    datos_previos={'estado_ot_id': estado_ot_anterior.estadoOT_id if estado_ot_anterior else None, 'estado_ot_nombre': estado_ot_anterior.nombre if estado_ot_anterior else None},
                    datos_nuevos={'estado_ot_id': estado_finalizada.estadoOT_id, 'estado_ot_nombre': estado_finalizada.nombre}
                )
                
                if estado_equipo_anterior != estado_disponible:
                    HistorialOT.registrar(
                        ot=ot,
                        accion='ESTADO_EQUIPO_CAMBIADO',
                        descripcion=f"Estado de equipo cambiado automáticamente a DISPONIBLE al finalizar la OT. Estado cambiado de '{estado_equipo_anterior.nombre if estado_equipo_anterior else 'N/A'}' a '{estado_disponible.nombre}'",
                        usuario=None,  # Sistema automático
                        datos_previos={'estado_equipo_id': estado_equipo_anterior.estadoEquipo_id if estado_equipo_anterior else None, 'estado_equipo_nombre': estado_equipo_anterior.nombre if estado_equipo_anterior else None},
                        datos_nuevos={'estado_equipo_id': estado_disponible.estadoEquipo_id, 'estado_equipo_nombre': estado_disponible.nombre}
                    )
        
        # Parámetros de filtro
        empresa_id = request.GET.get('empresa_id', None)
        tipo_equipo_id = request.GET.get('tipo_equipo_id', None)
        estado_ot = request.GET.get('estado_ot', None)
        estado_equipo = request.GET.get('estado_equipo', None)
        tipo_mantenimiento = request.GET.get('tipo_mantenimiento', None)
        solo_finalizadas = request.GET.get('solo_finalizadas', 'false').lower() == 'true'
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        # Query base
        queryset = OrdenTrabajo.objects.select_related(
            'equipo_id', 'equipo_id__modeloEquipo_id', 'equipo_id__modeloEquipo_id__tipoEquipo_id',
            'equipo_id__modeloEquipo_id__marcaEquipo_id', 'empresa_id', 'pauta_id',
            'tipo_mantenimiento_id', 'estado_ot_id', 'estado_equipo_id'
        ).prefetch_related('personal_asignado').all()
        
        # Filtrar por finalizadas o activas
        if solo_finalizadas:
            # Obtener los estados "FINALIZADA" y "CANCELADA"
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
            estados_finalizados = []
            if estado_finalizada:
                estados_finalizados.append(estado_finalizada.estadoOT_id)
            if estado_cancelada:
                estados_finalizados.append(estado_cancelada.estadoOT_id)
            if estados_finalizados:
                queryset = queryset.filter(estado_ot_id__in=estados_finalizados)
        else:
            # Excluir las finalizadas y canceladas
            estado_finalizada = EstadoOT.objects.filter(nombre__iexact='FINALIZADA').first()
            estado_cancelada = EstadoOT.objects.filter(nombre__iexact='CANCELADA').first()
            estados_finalizados = []
            if estado_finalizada:
                estados_finalizados.append(estado_finalizada.estadoOT_id)
            if estado_cancelada:
                estados_finalizados.append(estado_cancelada.estadoOT_id)
            if estados_finalizados:
                queryset = queryset.exclude(estado_ot_id__in=estados_finalizados)
        
        # Aplicar filtros
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        if tipo_equipo_id:
            queryset = queryset.filter(equipo_id__modeloEquipo_id__tipoEquipo_id=tipo_equipo_id)
        
        if estado_ot:
            queryset = queryset.filter(estado_ot_id=estado_ot)
        
        if estado_equipo:
            queryset = queryset.filter(estado_equipo_id=estado_equipo)
        
        if tipo_mantenimiento:
            queryset = queryset.filter(tipo_mantenimiento_id=tipo_mantenimiento)
        
        if search:
            queryset = queryset.filter(
                Q(folio__icontains=search) |
                Q(equipo_id__nombreEquipo__icontains=search) |
                Q(equipo_id__codigoInterno__icontains=search) |
                Q(observaciones__icontains=search)
            )
        
        # Ordenar por fecha de creación descendente
        queryset = queryset.order_by('-fecha_creacion')
        
        # Paginación
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        # Serializar datos
        ordenes = []
        for ot in page_obj:
            personal_asignado = []
            for p in ot.personal_asignado.all():
                info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
                cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
                personal_asignado.append({
                    'personal_id': p.personal_id,
                    'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
                    'cargo': cargo_nombre
                })
            
            ordenes.append({
                'ot_id': ot.ot_id,
                'folio': ot.folio,
                'equipo': {
                    'equipo_id': ot.equipo_id.equipo_id,
                    'nombreEquipo': ot.equipo_id.nombreEquipo,
                    'codigoInterno': ot.equipo_id.codigoInterno,
                    'tipoEquipo': ot.equipo_id.modeloEquipo_id.tipoEquipo_id.tipoEquipo if ot.equipo_id.modeloEquipo_id.tipoEquipo_id else '',
                },
                'empresa': {
                    'empresa_id': ot.empresa_id.id if hasattr(ot.empresa_id, 'id') else None,
                    'nomFantasia': ot.empresa_id.nomFantasia,
                },
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else '',
                'tipo_mantenimiento_id': ot.tipo_mantenimiento_id.tipoMantenimiento_id if ot.tipo_mantenimiento_id else None,
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else 'No disponible',
                'estado_ot_id': ot.estado_ot_id.estadoOT_id if ot.estado_ot_id else None,
                'estado_ot_color': ot.estado_ot_id.color if ot.estado_ot_id else 'secondary',
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else 'No disponible',
                'estado_equipo_id': ot.estado_equipo_id.estadoEquipo_id if ot.estado_equipo_id else None,
                'estado_equipo_color': ot.estado_equipo_id.color if ot.estado_equipo_id else 'secondary',
                'fecha_creacion': ot.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if ot.fecha_creacion else None,
                'fecha_inicio': ot.fecha_inicio.strftime('%Y-%m-%d') if ot.fecha_inicio else None,
                'fecha_fin': ot.fecha_fin.strftime('%Y-%m-%d') if ot.fecha_fin else None,
                'personal_asignado': personal_asignado,
            })
        
        return JsonResponse({
            'success': True,
            'ordenes': ordenes,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_prev': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al listar ordenes de trabajo: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_equipos_filtrados(request):
    """API para obtener equipos filtrados por empresa, tipo, marca y modelo"""
    try:
        empresa_id = request.GET.get('empresa_id', None)
        tipo_equipo_id = request.GET.get('tipo_equipo_id', None)
        marca_equipo_id = request.GET.get('marca_equipo_id', None)
        modelo_equipo_id = request.GET.get('modelo_equipo_id', None)
        
        queryset = Equipo.objects.filter(activo=True).select_related(
            'modeloEquipo_id', 'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id', 'empresa_id'
        )
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        if tipo_equipo_id:
            queryset = queryset.filter(modeloEquipo_id__tipoEquipo_id=tipo_equipo_id)
        
        if marca_equipo_id:
            queryset = queryset.filter(modeloEquipo_id__marcaEquipo_id=marca_equipo_id)
        
        if modelo_equipo_id:
            queryset = queryset.filter(modeloEquipo_id=modelo_equipo_id)
        
        equipos = []
        for equipo in queryset.order_by('nombreEquipo'):
            equipos.append({
                'equipo_id': equipo.equipo_id,
                'nombreEquipo': equipo.nombreEquipo,
                'codigoInterno': equipo.codigoInterno,
                'patente': equipo.patente or '',
                'horometro': equipo.horometro,
                'odometro': equipo.odometro,
                'horometroSuperEstructural': equipo.horometroSuperEstructural,
                'modeloEquipo_id': equipo.modeloEquipo_id.modeloEquipo_id if equipo.modeloEquipo_id else None,
                'tipoEquipo': equipo.modeloEquipo_id.tipoEquipo_id.tipoEquipo if equipo.modeloEquipo_id.tipoEquipo_id else '',
                'marcaEquipo': equipo.modeloEquipo_id.marcaEquipo_id.marcaEquipo if equipo.modeloEquipo_id.marcaEquipo_id else '',
                'modeloEquipo': equipo.modeloEquipo_id.modeloEquipo if equipo.modeloEquipo_id else '',
            })
        
        return JsonResponse({
            'success': True,
            'equipos': equipos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener equipos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_personal_maquinarias(request):
    """API para obtener personal activo con su cargo, empresa y departamento (con filtros)"""
    try:
        # Filtros
        search = request.GET.get('search', '').strip()
        empresa_id = request.GET.get('empresa_id', None)
        cargo_id = request.GET.get('cargo_id', None)
        depto_id = request.GET.get('depto_id', None)
        
        # Query base
        queryset = Personal.objects.filter(activo=True).prefetch_related('infolaboral_set__cargo_id', 'infolaboral_set__depto_id', 'infolaboral_set__empresa_id')
        
        # Aplicar filtros
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(apepat__icontains=search) |
                Q(apemat__icontains=search) |
                Q(rut__icontains=search)
            )
        
        personal = []
        for p in queryset:
            info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
            cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
            cargo_id_val = info_laboral.cargo_id.cargo_id if info_laboral and info_laboral.cargo_id else None
            depto_nombre = info_laboral.depto_id.depto if info_laboral and info_laboral.depto_id else 'Sin departamento'
            depto_id_val = info_laboral.depto_id.depto_id if info_laboral and info_laboral.depto_id else None
            empresa_nombre = info_laboral.empresa_id.nomFantasia if info_laboral and info_laboral.empresa_id else 'Sin empresa'
            empresa_id_val = info_laboral.empresa_id.id if info_laboral and info_laboral.empresa_id else None
            
            # Aplicar filtros adicionales
            if empresa_id and empresa_id_val != int(empresa_id):
                continue
            if cargo_id and cargo_id_val != int(cargo_id):
                continue
            if depto_id and depto_id_val != int(depto_id):
                continue
            
            personal.append({
                'personal_id': p.personal_id,
                'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
                'rut': f"{p.rut}-{p.dvrut}",
                'cargo': cargo_nombre,
                'cargo_id': cargo_id_val,
                'departamento': depto_nombre,
                'depto_id': depto_id_val,
                'empresa': empresa_nombre,
                'empresa_id': empresa_id_val,
            })
        
        return JsonResponse({
            'success': True,
            'personal': personal
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener personal: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_marcas_por_tipo(request):
    """API para obtener marcas filtradas por tipo de equipo (para filtros en cascada)"""
    try:
        tipo_id = request.GET.get('tipo_id', None)
        
        if not tipo_id:
            return JsonResponse({
                'success': True,
                'marcas': []
            })
        
        # Obtener modelos del tipo seleccionado
        modelos = ModeloEquipo.objects.filter(tipoEquipo_id=tipo_id).select_related('marcaEquipo_id')
        
        # Obtener marcas únicas
        marcas_ids = modelos.values_list('marcaEquipo_id', flat=True).distinct()
        marcas = MarcaEquipo.objects.filter(marcaEquipo_id__in=marcas_ids).order_by('marcaEquipo')
        
        marcas_list = [{
            'marcaEquipo_id': m.marcaEquipo_id,
            'marcaEquipo': m.marcaEquipo
        } for m in marcas]
        
        return JsonResponse({
            'success': True,
            'marcas': marcas_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener marcas: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_modelos_por_tipo_marca(request):
    """API para obtener modelos filtrados por tipo y marca (para filtros en cascada)"""
    try:
        tipo_id = request.GET.get('tipo_id', None)
        marca_id = request.GET.get('marca_id', None)
        
        if not tipo_id or not marca_id:
            return JsonResponse({
                'success': True,
                'modelos': []
            })
        
        modelos = ModeloEquipo.objects.filter(
            tipoEquipo_id=tipo_id,
            marcaEquipo_id=marca_id
        ).select_related('tipoEquipo_id', 'marcaEquipo_id').order_by('modeloEquipo')
        
        modelos_list = [{
            'modeloEquipo_id': m.modeloEquipo_id,
            'modeloEquipo': m.modeloEquipo
        } for m in modelos]
        
        return JsonResponse({
            'success': True,
            'modelos': modelos_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener modelos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_cargos_por_depto(request):
    """API para obtener cargos filtrados por departamento"""
    try:
        depto_id = request.GET.get('depto_id', None)
        
        if not depto_id:
            return JsonResponse({
                'success': True,
                'cargos': []
            })
        
        from rrhh_personal.models import Cargo
        cargos = Cargo.objects.filter(depto_id=depto_id).order_by('cargo')
        
        cargos_list = [{
            'cargo_id': c.cargo_id,
            'cargo': c.cargo
        } for c in cargos]
        
        return JsonResponse({
            'success': True,
            'cargos': cargos_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener cargos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_departamentos(request):
    """API para obtener todos los departamentos"""
    try:
        from rrhh_personal.models import DeptoEmpresa
        departamentos = DeptoEmpresa.objects.all().order_by('depto')
        
        deptos_list = [{
            'depto_id': d.depto_id,
            'depto': d.depto
        } for d in departamentos]
        
        return JsonResponse({
            'success': True,
            'departamentos': deptos_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener departamentos: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_pauta_ot(request, pauta_id):
    """API para obtener detalle de una pauta con sus secciones y estados (para mostrar en OT)"""
    try:
        pauta = get_object_or_404(PautaMantenimientoPreventivo, pauta_id=pauta_id)
        
        # Si se proporciona ot_id, usar los estados de ItemSeccionOT de esa OT
        ot_id = request.GET.get('ot_id', None)
        items_ot = None
        if ot_id:
            try:
                ot = OrdenTrabajo.objects.get(ot_id=ot_id, pauta_id=pauta)
                items_ot = ItemSeccionOT.objects.filter(ot_id=ot).select_related('estado_seccion_id', 'seccion_id')
                # Crear un diccionario para acceso rápido por seccion_id
                estados_ot_dict = {item.seccion_id.seccion_id: item.estado_seccion_id for item in items_ot if item.estado_seccion_id}
            except OrdenTrabajo.DoesNotExist:
                items_ot = None
        
        items_pauta = ItemPauta.objects.filter(pauta_id=pauta).prefetch_related(
            'seccion_id', 'tipos_reparacion', 'estado_seccion_id'
        )
        
        items = []
        for item in items_pauta:
            # Si hay OT, usar el estado de ItemSeccionOT, sino el de ItemPauta
            estado_seccion = None
            if items_ot:
                estado_seccion = estados_ot_dict.get(item.seccion_id.seccion_id)
            else:
                estado_seccion = item.estado_seccion_id
            
            items.append({
                'itemPauta_id': item.itemPauta_id,
                'seccion_id': item.seccion_id.seccion_id,
                'seccion_nombre': item.seccion_id.nombre,
                'tipos_reparacion': [{
                    'tipoReparacion_id': tr.tipoReparacion_id,
                    'nombre': tr.nombre
                } for tr in item.tipos_reparacion.all()],
                'estado_seccion_id': estado_seccion.estadoOT_id if estado_seccion else None,
                'estado_seccion_nombre': estado_seccion.nombre if estado_seccion else None,
            })
        
        return JsonResponse({
            'success': True,
            'pauta': {
                'pauta_id': pauta.pauta_id,
                'nombre': pauta.nombre,
                'descripcion': pauta.descripcion,
                'modeloEquipo_id': pauta.modeloEquipo_id.modeloEquipo_id,
            },
            'items': items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de pauta: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_orden_trabajo(request):
    """API para crear o actualizar una orden de trabajo"""
    try:
        data = json.loads(request.body)
        ot_id = data.get('ot_id')
        
        if ot_id:
            # Modo edición - solo actualizar estados
            ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
            
            # Guardar estados anteriores para historial
            estado_ot_anterior = ot.estado_ot_id
            estado_equipo_anterior = ot.estado_equipo_id
            fecha_fin_anterior = ot.fecha_fin
            
            # Obtener estados
            estado_ot_id = data.get('estado_ot_id')
            if not estado_ot_id:
                estado_ot = EstadoOT.objects.filter(nombre='Pendiente').first()
                if not estado_ot:
                    estado_ot = EstadoOT.objects.filter(activo=True).first()
            else:
                estado_ot = get_object_or_404(EstadoOT, estadoOT_id=estado_ot_id)
            
            estado_equipo_id = data.get('estado_equipo_id')
            if not estado_equipo_id:
                estado_equipo = EstadoEquipo.objects.filter(nombre='Disponible').first()
                if not estado_equipo:
                    estado_equipo = EstadoEquipo.objects.filter(activo=True).first()
            else:
                estado_equipo = get_object_or_404(EstadoEquipo, estadoEquipo_id=estado_equipo_id)
            
            # Registrar cambios en historial
            cambios_registrados = []
            
            # Cambio de estado OT
            if estado_ot_anterior != estado_ot:
                HistorialOT.registrar(
                    ot=ot,
                    accion='ESTADO_OT_CAMBIADO',
                    descripcion=f"Estado de OT cambiado de '{estado_ot_anterior.nombre if estado_ot_anterior else "N/A"}' a '{estado_ot.nombre}'",
                    usuario=request.user if request.user.is_authenticated else None,
                    datos_previos={'estado_ot_id': estado_ot_anterior.estadoOT_id if estado_ot_anterior else None, 'estado_ot_nombre': estado_ot_anterior.nombre if estado_ot_anterior else None},
                    datos_nuevos={'estado_ot_id': estado_ot.estadoOT_id, 'estado_ot_nombre': estado_ot.nombre}
                )
                cambios_registrados.append('estado_ot')
                
                # Si la OT se marca como FINALIZADA o CANCELADA, cambiar automáticamente el estado del equipo a DISPONIBLE
                estado_ot_nombre_upper = estado_ot.nombre.upper()
                if estado_ot_nombre_upper == 'FINALIZADA' or estado_ot_nombre_upper == 'CANCELADA':
                    estado_disponible = EstadoEquipo.objects.filter(nombre__iexact='Disponible').first()
                    if estado_disponible and estado_equipo != estado_disponible:
                        estado_equipo_anterior = estado_equipo  # Actualizar para registrar el cambio
                        estado_equipo = estado_disponible
            
            # Cambio de estado equipo
            if estado_equipo_anterior != estado_equipo:
                HistorialOT.registrar(
                    ot=ot,
                    accion='ESTADO_EQUIPO_CAMBIADO',
                    descripcion=f"Estado de equipo cambiado de '{estado_equipo_anterior.nombre if estado_equipo_anterior else "N/A"}' a '{estado_equipo.nombre}'",
                    usuario=request.user if request.user.is_authenticated else None,
                    datos_previos={'estado_equipo_id': estado_equipo_anterior.estadoEquipo_id if estado_equipo_anterior else None, 'estado_equipo_nombre': estado_equipo_anterior.nombre if estado_equipo_anterior else None},
                    datos_nuevos={'estado_equipo_id': estado_equipo.estadoEquipo_id, 'estado_equipo_nombre': estado_equipo.nombre}
                )
                cambios_registrados.append('estado_equipo')
            
            # Cambio de fecha fin
            fecha_fin_nueva = data.get('fecha_fin')
            if fecha_fin_nueva:
                try:
                    fecha_fin_parsed = datetime.strptime(fecha_fin_nueva, '%Y-%m-%d').date()
                    if fecha_fin_anterior != fecha_fin_parsed:
                        HistorialOT.registrar(
                            ot=ot,
                            accion='FECHA_FIN_CAMBIADA',
                            descripcion=f"Fecha de fin cambiada de '{fecha_fin_anterior.strftime('%d/%m/%Y') if fecha_fin_anterior else 'No definida'}' a '{fecha_fin_parsed.strftime('%d/%m/%Y')}'",
                            usuario=request.user if request.user.is_authenticated else None,
                            datos_previos={'fecha_fin': fecha_fin_anterior.strftime('%Y-%m-%d') if fecha_fin_anterior else None},
                            datos_nuevos={'fecha_fin': fecha_fin_nueva}
                        )
                        cambios_registrados.append('fecha_fin')
                        ot.fecha_fin = fecha_fin_parsed
                except (ValueError, TypeError):
                    pass  # Si hay error en el formato, ignorar
            elif fecha_fin_anterior:  # Si se eliminó la fecha fin
                HistorialOT.registrar(
                    ot=ot,
                    accion='FECHA_FIN_CAMBIADA',
                    descripcion=f"Fecha de fin eliminada (anteriormente era '{fecha_fin_anterior.strftime('%d/%m/%Y')}')",
                    usuario=request.user if request.user.is_authenticated else None,
                    datos_previos={'fecha_fin': fecha_fin_anterior.strftime('%Y-%m-%d')},
                    datos_nuevos={'fecha_fin': None}
                )
                cambios_registrados.append('fecha_fin')
                ot.fecha_fin = None
            
            # Actualizar estados y fecha fin
            ot.estado_ot_id = estado_ot
            ot.estado_equipo_id = estado_equipo
            ot.save()
            
            # Actualizar estados de secciones si se enviaron
            estados_pauta = data.get('estados_pauta', [])
            estados_secciones = data.get('estados_secciones', [])
            
            # Actualizar estados de pauta
            if estados_pauta:
                for estado_data in estados_pauta:
                    item_pauta_id = estado_data.get('itemPauta_id')
                    estado_seccion_id = estado_data.get('estado_seccion_id')
                    if item_pauta_id and estado_seccion_id:
                        try:
                            item_pauta = ItemPauta.objects.get(itemPauta_id=item_pauta_id, pauta_id=ot.pauta_id)
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                            
                            # Obtener estado anterior para comparar
                            estado_seccion_anterior = item_pauta.estado_seccion_id
                            
                            # Actualizar estado en ItemPauta
                            item_pauta.estado_seccion_id = estado_seccion
                            item_pauta.save()
                            
                            # Actualizar también en ItemSeccionOT
                            item_seccion_ot = ItemSeccionOT.objects.filter(
                                ot_id=ot,
                                seccion_id=item_pauta.seccion_id
                            ).first()
                            
                            if item_seccion_ot:
                                # Registrar cambio si el estado cambió
                                if estado_seccion_anterior != estado_seccion:
                                    HistorialOT.registrar(
                                        ot=ot,
                                        accion='ESTADO_SECCION_CAMBIADO',
                                        descripcion=f"Estado de sección '{item_pauta.seccion_id.nombre}' cambiado de '{estado_seccion_anterior.nombre if estado_seccion_anterior else 'Sin estado'}' a '{estado_seccion.nombre}'",
                                        usuario=request.user if request.user.is_authenticated else None,
                                        datos_previos={
                                            'seccion_id': item_pauta.seccion_id.seccion_id,
                                            'seccion_nombre': item_pauta.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion_anterior.estadoOT_id if estado_seccion_anterior else None,
                                            'estado_seccion_nombre': estado_seccion_anterior.nombre if estado_seccion_anterior else None
                                        },
                                        datos_nuevos={
                                            'seccion_id': item_pauta.seccion_id.seccion_id,
                                            'seccion_nombre': item_pauta.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion.estadoOT_id,
                                            'estado_seccion_nombre': estado_seccion.nombre
                                        }
                                    )
                                
                                item_seccion_ot.estado_seccion_id = estado_seccion
                                item_seccion_ot.save()
                        except (ItemPauta.DoesNotExist, EstadoOT.DoesNotExist):
                            pass
            
            # Actualizar estados de secciones manuales (items de secciones de la OT)
            if estados_secciones:
                # Obtener todos los items de secciones de la OT
                items_secciones_ot = ItemSeccionOT.objects.filter(ot_id=ot).select_related('seccion_id', 'estado_seccion_id')
                
                # Mapear estados por sección_id
                for estado_data in estados_secciones:
                    seccion_id = estado_data.get('seccion_id')
                    estado_seccion_id = estado_data.get('estado_seccion_id')
                    if seccion_id and estado_seccion_id:
                        try:
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                            # Actualizar el item de sección específico
                            item_ot = items_secciones_ot.filter(seccion_id=seccion_id).first()
                            if item_ot:
                                # Obtener estado anterior para comparar
                                estado_seccion_anterior = item_ot.estado_seccion_id
                                
                                # Registrar cambio si el estado cambió
                                if estado_seccion_anterior != estado_seccion:
                                    HistorialOT.registrar(
                                        ot=ot,
                                        accion='ESTADO_SECCION_CAMBIADO',
                                        descripcion=f"Estado de sección '{item_ot.seccion_id.nombre}' cambiado de '{estado_seccion_anterior.nombre if estado_seccion_anterior else 'Sin estado'}' a '{estado_seccion.nombre}'",
                                        usuario=request.user if request.user.is_authenticated else None,
                                        datos_previos={
                                            'seccion_id': item_ot.seccion_id.seccion_id,
                                            'seccion_nombre': item_ot.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion_anterior.estadoOT_id if estado_seccion_anterior else None,
                                            'estado_seccion_nombre': estado_seccion_anterior.nombre if estado_seccion_anterior else None
                                        },
                                        datos_nuevos={
                                            'seccion_id': item_ot.seccion_id.seccion_id,
                                            'seccion_nombre': item_ot.seccion_id.nombre,
                                            'estado_seccion_id': estado_seccion.estadoOT_id,
                                            'estado_seccion_nombre': estado_seccion.nombre
                                        }
                                    )
                                
                                item_ot.estado_seccion_id = estado_seccion
                                item_ot.save()
                        except EstadoOT.DoesNotExist:
                            pass
            
            return JsonResponse({
                'success': True,
                'message': 'Estados actualizados exitosamente',
                'ot_id': ot.ot_id,
                'folio': ot.folio
            })
        
        # Modo creación - validaciones básicas
        equipo_id = data.get('equipo_id')
        if not equipo_id:
            return JsonResponse({
                'success': False,
                'message': 'El equipo es requerido'
            }, status=400)
        
        equipo = get_object_or_404(Equipo, equipo_id=equipo_id)
        
        # Obtener tipo de mantenimiento
        tipo_mantenimiento_id = data.get('tipo_mantenimiento_id')
        if not tipo_mantenimiento_id:
            return JsonResponse({
                'success': False,
                'message': 'Tipo de mantenimiento es requerido'
            }, status=400)
        
        tipo_mantenimiento = get_object_or_404(TipoMantenimiento, tipoMantenimiento_id=tipo_mantenimiento_id)
        
        # En creación, SIEMPRE usar PENDIENTE para la OT
        estado_ot = EstadoOT.objects.filter(nombre='Pendiente').first()
        if not estado_ot:
            estado_ot = EstadoOT.objects.filter(activo=True).first()
        
        estado_equipo_id = data.get('estado_equipo_id')
        if not estado_equipo_id:
            estado_equipo = EstadoEquipo.objects.filter(nombre='Disponible').first()
            if not estado_equipo:
                estado_equipo = EstadoEquipo.objects.filter(activo=True).first()
        else:
            estado_equipo = get_object_or_404(EstadoEquipo, estadoEquipo_id=estado_equipo_id)
        
        # Crear nueva OT
        ot = OrdenTrabajo()
        
        # Campos básicos (solo en creación)
        ot.equipo_id = equipo
        ot.empresa_id = equipo.empresa_id
        ot.tipo_mantenimiento_id = tipo_mantenimiento
        ot.estado_ot_id = estado_ot
        ot.estado_equipo_id = estado_equipo
        
        # Campos automáticos del equipo
        ot.horometro = equipo.horometro
        ot.odometro = equipo.odometro
        ot.horometro_superestructura = equipo.horometroSuperEstructural
        
        # Fechas
        fecha_inicio = data.get('fecha_inicio')
        if fecha_inicio:
            ot.fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        
        fecha_fin = data.get('fecha_fin')
        if fecha_fin:
            ot.fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Si es preventivo
        if tipo_mantenimiento.nombre.lower() == 'preventivo':
            corresponde_pauta = data.get('corresponde_pauta', False)
            ot.corresponde_pauta = corresponde_pauta
            
            if corresponde_pauta:
                pauta_id = data.get('pauta_id')
                if pauta_id:
                    ot.pauta_id = get_object_or_404(PautaMantenimientoPreventivo, pauta_id=pauta_id)
                else:
                    ot.pauta_id = None
            else:
                ot.pauta_id = None
        else:
            ot.corresponde_pauta = False
            ot.pauta_id = None
        
        # Observaciones
        ot.observaciones = data.get('observaciones', '')
        
        ot.save()
        
        # Registrar creación en historial
        HistorialOT.registrar(
            ot=ot,
            accion='OT_CREADA',
            descripcion=f"Orden de Trabajo creada. Equipo: {ot.equipo_id.nombreEquipo}, Tipo: {ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else 'N/A'}",
            usuario=request.user if request.user.is_authenticated else None,
            datos_nuevos={
                'folio': ot.folio,
                'equipo_id': ot.equipo_id.equipo_id,
                'equipo_nombre': ot.equipo_id.nombreEquipo,
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else None,
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else None,
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else None,
            }
        )
        
        # Personal asignado (ManyToMany)
        personal_ids = data.get('personal_asignado', [])
        ot.personal_asignado.set(personal_ids)
        
        # Registrar asignación de personal en historial
        if personal_ids:
            personal_list = Personal.objects.filter(personal_id__in=personal_ids)
            nombres_personal = [f"{p.nombre} {p.apepat}" for p in personal_list]
            HistorialOT.registrar(
                ot=ot,
                accion='PERSONAL_ASIGNADO',
                descripcion=f"Personal asignado: {', '.join(nombres_personal)}",
                usuario=request.user if request.user.is_authenticated else None,
                datos_nuevos={'personal_ids': list(personal_ids)}
            )
        
        # Si es preventivo con pauta, crear items de secciones desde la pauta
        if tipo_mantenimiento.nombre.lower() == 'preventivo' and ot.corresponde_pauta and ot.pauta_id:
            # Eliminar items existentes
            ItemSeccionOT.objects.filter(ot_id=ot).delete()
            
            # Obtener items de la pauta
            items_pauta = ItemPauta.objects.filter(pauta_id=ot.pauta_id).prefetch_related('tipos_reparacion', 'estado_seccion_id')
            
            # Obtener estados de pauta desde el formulario (si se enviaron)
            estados_pauta = data.get('estados_pauta', [])
            estados_pauta_dict = {item['seccion_id']: item['estado_seccion_id'] for item in estados_pauta if item.get('estado_seccion_id')}
            
            # Obtener estado por defecto (Pendiente)
            estado_pendiente = EstadoOT.objects.filter(nombre='Pendiente').first()
            if not estado_pendiente:
                estado_pendiente = EstadoOT.objects.filter(activo=True).first()
            
            # Crear items de secciones desde la pauta
            # En creación, SIEMPRE usar PENDIENTE para las secciones
            for item_pauta in items_pauta:
                # Siempre usar PENDIENTE en creación, ignorar estados del formulario
                estado_seccion = estado_pendiente
                
                item_seccion = ItemSeccionOT.objects.create(
                    ot_id=ot,
                    seccion_id=item_pauta.seccion_id,
                    estado_seccion_id=estado_seccion
                )
                item_seccion.tipos_reparacion.set(item_pauta.tipos_reparacion.all())
            
            # Actualizar estados de las secciones en la pauta si se enviaron
            if estados_pauta:
                for estado_data in estados_pauta:
                    item_pauta_id = estado_data.get('itemPauta_id')
                    estado_seccion_id = estado_data.get('estado_seccion_id')
                    if item_pauta_id and estado_seccion_id:
                        try:
                            item_pauta = ItemPauta.objects.get(itemPauta_id=item_pauta_id, pauta_id=ot.pauta_id)
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                            item_pauta.estado_seccion_id = estado_seccion
                            item_pauta.save()
                        except (ItemPauta.DoesNotExist, EstadoOT.DoesNotExist):
                            pass
        
        # Si NO es pauta o es correctivo, guardar items de secciones manuales
        elif (tipo_mantenimiento.nombre.lower() == 'preventivo' and not ot.corresponde_pauta) or tipo_mantenimiento.nombre.lower() == 'correctivo':
            items_secciones = data.get('items_secciones', [])
            # Eliminar items existentes
            ItemSeccionOT.objects.filter(ot_id=ot).delete()
            
            # Obtener estado por defecto (Pendiente)
            estado_pendiente = EstadoOT.objects.filter(nombre='Pendiente').first()
            if not estado_pendiente:
                estado_pendiente = EstadoOT.objects.filter(activo=True).first()
            
            # Crear nuevos items
            for item in items_secciones:
                seccion_id = item.get('seccion_id')
                tipos_reparacion_ids = item.get('tipos_reparacion_ids', [])
                estado_seccion_id = item.get('estado_seccion_id')
                
                if seccion_id and tipos_reparacion_ids:
                    estado_seccion = None
                    # En creación, siempre usar PENDIENTE por defecto para las secciones
                    if estado_seccion_id:
                        try:
                            estado_seccion = EstadoOT.objects.get(estadoOT_id=estado_seccion_id)
                        except EstadoOT.DoesNotExist:
                            estado_seccion = estado_pendiente
                    else:
                        # Siempre PENDIENTE en creación
                        estado_seccion = estado_pendiente
                    
                    item_seccion = ItemSeccionOT.objects.create(
                        ot_id=ot,
                        seccion_id_id=seccion_id,
                        estado_seccion_id=estado_seccion
                    )
                    item_seccion.tipos_reparacion.set(tipos_reparacion_ids)
        
        return JsonResponse({
            'success': True,
            'message': 'Orden de trabajo guardada exitosamente',
            'ot_id': ot.ot_id,
            'folio': ot.folio
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar orden de trabajo: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_agregar_observacion_ot(request, ot_id):
    """API para agregar una observación al historial de una OT"""
    try:
        ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
        data = json.loads(request.body)
        
        observacion = data.get('observacion', '').strip()
        if not observacion:
            return JsonResponse({
                'success': False,
                'message': 'La observación es requerida'
            }, status=400)
        
        historial = HistorialObservacionesOT.objects.create(
            ot_id=ot,
            observacion=observacion,
            usuario=request.user if request.user.is_authenticated else None
        )
        
        # Registrar en historial de cambios
        HistorialOT.registrar(
            ot=ot,
            accion='OBSERVACION_AGREGADA',
            descripcion=f"Observación agregada: {observacion[:100]}...",
            usuario=request.user if request.user.is_authenticated else None,
            datos_nuevos={'observacion': observacion}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Observación agregada exitosamente',
            'historial': {
                'historial_id': historial.historial_id,
                'observacion': historial.observacion,
                'usuario': historial.usuario.username if historial.usuario else None,
                'fecha': historial.fecha.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar observación: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detalle_ot(request, ot_id):
    """API para obtener detalles completos de una OT"""
    try:
        ot = get_object_or_404(OrdenTrabajo.objects.select_related(
            'equipo_id', 'equipo_id__modeloEquipo_id', 'equipo_id__modeloEquipo_id__tipoEquipo_id',
            'equipo_id__modeloEquipo_id__marcaEquipo_id', 'empresa_id', 'pauta_id',
            'tipo_mantenimiento_id', 'estado_ot_id', 'estado_equipo_id'
        ).prefetch_related('personal_asignado', 'items_secciones__seccion_id', 'items_secciones__tipos_reparacion', 'items_secciones__estado_seccion_id'), ot_id=ot_id)
        
        # Personal asignado
        personal_asignado = []
        for p in ot.personal_asignado.all():
            info_laboral = InfoLaboral.objects.filter(personal_id=p).first()
            cargo_nombre = info_laboral.cargo_id.cargo if info_laboral and info_laboral.cargo_id else 'Sin cargo'
            personal_asignado.append({
                'personal_id': p.personal_id,
                'nombre_completo': f"{p.nombre} {p.apepat} {p.apemat}",
                'rut': f"{p.rut}-{p.dvrut}",
                'cargo': cargo_nombre
            })
        
        # Secciones (si es pauta)
        secciones_pauta = []
        if ot.corresponde_pauta and ot.pauta_id:
            items_pauta = ItemPauta.objects.filter(pauta_id=ot.pauta_id).select_related('seccion_id', 'estado_seccion_id').prefetch_related('tipos_reparacion')
            for item in items_pauta:
                # Buscar el estado en ItemSeccionOT si existe
                item_seccion_ot = ItemSeccionOT.objects.filter(ot_id=ot, seccion_id=item.seccion_id).first()
                estado_actual = item_seccion_ot.estado_seccion_id if item_seccion_ot and item_seccion_ot.estado_seccion_id else item.estado_seccion_id
                
                secciones_pauta.append({
                    'seccion_id': item.seccion_id.seccion_id,
                    'seccion_nombre': item.seccion_id.nombre,
                    'tipos_reparacion': [tr.nombre for tr in item.tipos_reparacion.all()],
                    'estado_seccion': estado_actual.nombre if estado_actual else 'Pendiente',
                    'estado_seccion_id': estado_actual.estadoOT_id if estado_actual else None,
                    'estado_seccion_color': estado_actual.color if estado_actual else 'secondary'
                })
        
        # Secciones manuales (si no es pauta)
        secciones_manuales = []
        if not ot.corresponde_pauta or not ot.pauta_id:
            items_secciones = ItemSeccionOT.objects.filter(ot_id=ot).select_related('seccion_id', 'estado_seccion_id').prefetch_related('tipos_reparacion')
            for item in items_secciones:
                secciones_manuales.append({
                    'seccion_id': item.seccion_id.seccion_id,
                    'seccion_nombre': item.seccion_id.nombre,
                    'tipos_reparacion': [tr.nombre for tr in item.tipos_reparacion.all()],
                    'estado_seccion': item.estado_seccion_id.nombre if item.estado_seccion_id else 'Pendiente',
                    'estado_seccion_id': item.estado_seccion_id.estadoOT_id if item.estado_seccion_id else None,
                    'estado_seccion_color': item.estado_seccion_id.color if item.estado_seccion_id else 'secondary'
                })
        
        # Historial de observaciones
        historial_observaciones = []
        for obs in HistorialObservacionesOT.objects.filter(ot_id=ot).select_related('usuario').order_by('-fecha'):
            historial_observaciones.append({
                'fecha': obs.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'usuario': obs.usuario.username if obs.usuario else 'Sistema',
                'observacion': obs.observacion
            })
        
        # Historial de cambios
        historial_cambios = []
        for cambio in HistorialOT.objects.filter(ot=ot).select_related('usuario').order_by('-fecha_hora'):
            historial_cambios.append({
                'fecha_hora': cambio.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
                'usuario': cambio.usuario.username if cambio.usuario else 'Sistema',
                'accion': cambio.get_accion_display(),
                'descripcion': cambio.descripcion
            })
        
        return JsonResponse({
            'success': True,
            'ot': {
                'ot_id': ot.ot_id,
                'folio': ot.folio,
                'equipo': {
                    'equipo_id': ot.equipo_id.equipo_id,
                    'nombreEquipo': ot.equipo_id.nombreEquipo,
                    'codigoInterno': ot.equipo_id.codigoInterno,
                    'tipoEquipo': ot.equipo_id.modeloEquipo_id.tipoEquipo_id.tipoEquipo if ot.equipo_id.modeloEquipo_id.tipoEquipo_id else '',
                    'marcaEquipo': ot.equipo_id.modeloEquipo_id.marcaEquipo_id.marcaEquipo if ot.equipo_id.modeloEquipo_id.marcaEquipo_id else '',
                    'modeloEquipo': ot.equipo_id.modeloEquipo_id.modeloEquipo if ot.equipo_id.modeloEquipo_id else '',
                },
                'empresa': {
                    'empresa_id': ot.empresa_id.id if hasattr(ot.empresa_id, 'id') else None,
                    'nomFantasia': ot.empresa_id.nomFantasia,
                },
                'tipo_mantenimiento': ot.tipo_mantenimiento_id.nombre if ot.tipo_mantenimiento_id else '',
                'estado_ot': ot.estado_ot_id.nombre if ot.estado_ot_id else '',
                'estado_ot_color': ot.estado_ot_id.color if ot.estado_ot_id else 'secondary',
                'estado_equipo': ot.estado_equipo_id.nombre if ot.estado_equipo_id else '',
                'estado_equipo_color': ot.estado_equipo_id.color if ot.estado_equipo_id else 'secondary',
                'fecha_creacion': ot.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if ot.fecha_creacion else None,
                'fecha_inicio': ot.fecha_inicio.strftime('%Y-%m-%d') if ot.fecha_inicio else None,
                'fecha_fin': ot.fecha_fin.strftime('%Y-%m-%d') if ot.fecha_fin else None,
                'horometro': ot.horometro,
                'odometro': ot.odometro,
                'horometro_superestructura': ot.horometro_superestructura,
                'corresponde_pauta': ot.corresponde_pauta,
                'pauta_nombre': ot.pauta_id.nombre if ot.pauta_id else None,
                'observaciones': ot.observaciones,
                'personal_asignado': personal_asignado,
                'secciones_pauta': secciones_pauta,
                'secciones_manuales': secciones_manuales,
                'historial_observaciones': historial_observaciones,
                'historial_cambios': historial_cambios
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener detalle de OT: {str(e)}'
        }, status=500)
