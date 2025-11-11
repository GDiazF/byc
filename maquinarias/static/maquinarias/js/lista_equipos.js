// Variables globales
let paginaActual = 1;
let tamanoPagina = 25;
let equipoIdEliminar = null;

// Cargar equipos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarEquipos();
    
    // Event listeners para filtros
    document.getElementById('searchInput').addEventListener('input', debounce(cargarEquipos, 500));
    document.getElementById('empresaFilter').addEventListener('change', cargarEquipos);
    document.getElementById('tipoFilter').addEventListener('change', cargarEquipos);
    document.getElementById('marcaFilter').addEventListener('change', cargarEquipos);
});

// Función debounce para búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Cargar equipos con filtros
function cargarEquipos() {
    const search = document.getElementById('searchInput').value;
    const empresa = document.getElementById('empresaFilter').value;
    const tipo = document.getElementById('tipoFilter').value;
    const marca = document.getElementById('marcaFilter').value;
    
    const params = new URLSearchParams({
        search: search,
        empresa: empresa,
        tipo: tipo,
        marca: marca,
        estado: 'activos', // Siempre mostrar solo activos
        page: paginaActual,
        page_size: tamanoPagina
    });
    
    fetch(`/maquinarias/api/equipos/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarEquipos(data.equipos);
                renderizarPaginacion(data.pagination);
                actualizarEstadisticas(data.pagination);
            } else {
                mostrarError('Error al cargar equipos: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar equipos');
        });
}

// Renderizar tabla de equipos
function renderizarEquipos(equipos) {
    const tbody = document.getElementById('equiposTableBody');
    
    if (equipos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron equipos activos</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = equipos.map(equipo => `
        <tr>
            <td><strong>${equipo.nombreEquipo}</strong></td>
            <td>
                <span class="badge bg-secondary">${equipo.tipoEquipo.sigla}</span>
                <span class="ms-1">${equipo.tipoEquipo.nombre}</span>
            </td>
            <td>${equipo.marcaEquipo.nombre}</td>
            <td>${equipo.modeloEquipo.nombre}</td>
            <td>${equipo.empresa.nombre}</td>
            <td class="text-center">
                <a href="/maquinarias/equipos/${equipo.equipo_id}/documentacion/" 
                   class="btn btn-sm btn-primary" 
                   title="Ver Documentación">
                    <i class="bi bi-folder"></i>
                </a>
            </td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    <a href="/maquinarias/equipos/${equipo.equipo_id}/editar/" 
                       class="btn btn-sm btn-secondary" 
                       title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button class="btn btn-sm btn-danger" 
                            onclick="mostrarModalEliminar(${equipo.equipo_id}, '${equipo.nombreEquipo}')"
                            title="Eliminar">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-switch d-inline-block">
                    <input class="form-check-input" type="checkbox" 
                           style="cursor: pointer;"
                           ${equipo.activo ? 'checked' : ''} 
                           onchange="toggleActivo(${equipo.equipo_id}, '${equipo.nombreEquipo}', ${equipo.activo})"
                           title="${equipo.activo ? 'Desactivar equipo' : 'Activar equipo'}">
                </div>
            </td>
        </tr>
    `).join('');
}

// Renderizar paginación
function renderizarPaginacion(pagination) {
    const paginacionDiv = document.getElementById('paginacion');
    
    if (pagination.total_pages <= 1) {
        paginacionDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${!pagination.has_previous ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    const startPage = Math.max(1, pagination.current_page - 2);
    const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === pagination.current_page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${pagination.total_pages}); return false;">${pagination.total_pages}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionDiv.innerHTML = html;
}

// Actualizar estadísticas
function actualizarEstadisticas(pagination) {
    document.getElementById('totalEquipos').textContent = pagination.total_count;
    
    const inicio = (pagination.current_page - 1) * pagination.page_size + 1;
    const fin = Math.min(pagination.current_page * pagination.page_size, pagination.total_count);
    
    document.getElementById('registroInicio').textContent = pagination.total_count > 0 ? inicio : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistros').textContent = pagination.total_count;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    cargarEquipos();
}

// Cambiar tamaño de página
function cambiarTamanoPagina() {
    tamanoPagina = parseInt(document.getElementById('pageSizeSelect').value);
    paginaActual = 1;
    cargarEquipos();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('empresaFilter').value = '';
    document.getElementById('tipoFilter').value = '';
    document.getElementById('marcaFilter').value = '';
    paginaActual = 1;
    cargarEquipos();
}

// Mostrar modal eliminar
function mostrarModalEliminar(equipoId, nombreEquipo) {
    equipoIdEliminar = equipoId;
    document.getElementById('equipoEliminarNombre').textContent = nombreEquipo;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmarEliminarModal'));
    modal.show();
    
    document.getElementById('btnConfirmarEliminar').onclick = function() {
        eliminarEquipo(equipoId);
    };
}

// Eliminar equipo
function eliminarEquipo(equipoId) {
    fetch(`/maquinarias/api/equipos/${equipoId}/eliminar/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            bootstrap.Modal.getInstance(document.getElementById('confirmarEliminarModal')).hide();
            cargarEquipos();
        } else {
            mostrarError(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error de conexión al eliminar el equipo');
    });
}

// Toggle activo/inactivo
function toggleActivo(equipoId, nombreEquipo, estadoActual) {
    if (estadoActual) {
        // Si está activo, mostrar modal de desactivación
        document.getElementById('equipoDesactivarNombre').textContent = nombreEquipo;
        const modal = new bootstrap.Modal(document.getElementById('confirmDesactivarModal'));
        modal.show();
        
        // Configurar botón de confirmación
        document.getElementById('btnConfirmarDesactivar').onclick = function() {
            ejecutarToggleActivo(equipoId, modal);
        };
    } else {
        // Si está inactivo, activar directamente (esto no debería pasar en lista activos)
        ejecutarToggleActivo(equipoId, null);
    }
}

// Ejecutar toggle de estado
function ejecutarToggleActivo(equipoId, modal) {
    fetch(`/maquinarias/api/equipos/${equipoId}/toggle-activo/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (modal) {
                modal.hide();
            }
            mostrarExito(data.message);
            cargarEquipos();
        } else {
            mostrarError(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error de conexión al cambiar el estado del equipo');
    });
}

// Mostrar notificación estilo alert
function showNotification(message, type = 'success') {
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 3000);
}

// Mostrar mensaje de éxito
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}
