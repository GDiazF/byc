// Variables globales
let paginaActual = 1;
let tamanoPagina = 10;
let tipoIdEliminar = null;

// Cargar tipos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarTiposReparacion();
    
    // Event listeners
    document.getElementById('searchInput').addEventListener('input', debounce(cargarTiposReparacion, 500));
    document.getElementById('seccionFilter').addEventListener('change', cargarTiposReparacion);
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);
        paginaActual = 1;
        cargarTiposReparacion();
    });
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

// Cargar tipos de reparación con paginación, búsqueda y filtros
function cargarTiposReparacion() {
    const search = document.getElementById('searchInput').value;
    const seccionId = document.getElementById('seccionFilter').value;
    
    const params = new URLSearchParams({
        search: search,
        seccion_id: seccionId,
        page: paginaActual,
        per_page: tamanoPagina
    });
    
    fetch(`/maquinarias/api/tipos-reparacion/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarTiposReparacion(data.tipos_reparacion);
                renderizarPaginacion(data);
                actualizarEstadisticas(data.total);
            } else {
                mostrarError('Error al cargar tipos de reparación: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar tipos de reparación');
        });
}

// Renderizar tabla de tipos de reparación
function renderizarTiposReparacion(tipos) {
    const tbody = document.getElementById('tiposTableBody');
    
    if (tipos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron tipos de reparación</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = tipos.map(tipo => `
        <tr>
            <td><strong>${tipo.nombre}</strong></td>
            <td>
                <span class="badge bg-primary">${tipo.seccion_nombre}</span>
            </td>
            <td>${tipo.descripcion || '<span class="text-muted">Sin descripción</span>'}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-secondary" 
                            onclick="mostrarModalEditar(${tipo.tipoReparacion_id})" 
                            title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" 
                            onclick="mostrarModalEliminar(${tipo.tipoReparacion_id}, '${tipo.nombre}')" 
                            title="Eliminar">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Renderizar paginación
function renderizarPaginacion(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.total_pages;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    const maxPaginas = 5;
    let inicio = Math.max(1, paginaActual - Math.floor(maxPaginas / 2));
    let fin = Math.min(totalPages, inicio + maxPaginas - 1);
    
    if (fin - inicio < maxPaginas - 1) {
        inicio = Math.max(1, fin - maxPaginas + 1);
    }
    
    if (inicio > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a>
            </li>
        `;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (fin < totalPages) {
        if (fin < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// Actualizar estadísticas
function actualizarEstadisticas(total) {
    document.getElementById('totalTipos').textContent = total;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    cargarTiposReparacion();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('seccionFilter').value = '';
    paginaActual = 1;
    cargarTiposReparacion();
}

// Mostrar modal para crear
function mostrarModalCrear() {
    document.getElementById('tipoReparacion_id').value = '';
    document.getElementById('seccion_id').value = '';
    document.getElementById('nombre').value = '';
    document.getElementById('descripcion').value = '';
    document.getElementById('modalTitulo').textContent = 'Nuevo Tipo de Reparación';
    
    const modal = new bootstrap.Modal(document.getElementById('modalTipoReparacion'));
    modal.show();
}

// Mostrar modal para editar
function mostrarModalEditar(tipoId) {
    fetch(`/maquinarias/api/tipos-reparacion/?search=&seccion_id=&page=1&per_page=1000`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tipo = data.tipos_reparacion.find(t => t.tipoReparacion_id === tipoId);
                if (tipo) {
                    document.getElementById('tipoReparacion_id').value = tipo.tipoReparacion_id;
                    document.getElementById('seccion_id').value = tipo.seccion_id;
                    document.getElementById('nombre').value = tipo.nombre;
                    document.getElementById('descripcion').value = tipo.descripcion || '';
                    document.getElementById('modalTitulo').textContent = 'Editar Tipo de Reparación';
                    
                    const modal = new bootstrap.Modal(document.getElementById('modalTipoReparacion'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar datos del tipo de reparación');
        });
}

// Guardar tipo de reparación
function guardarTipoReparacion() {
    const tipoId = document.getElementById('tipoReparacion_id').value;
    const seccionId = document.getElementById('seccion_id').value;
    const nombre = document.getElementById('nombre').value.trim();
    const descripcion = document.getElementById('descripcion').value.trim();
    
    // Validaciones
    if (!seccionId) {
        mostrarError('La sección es requerida');
        return;
    }
    
    if (!nombre) {
        mostrarError('El nombre es requerido');
        return;
    }
    
    const data = {
        tipoReparacion_id: tipoId || null,
        seccion_id: seccionId,
        nombre: nombre,
        descripcion: descripcion
    };
    
    fetch('/maquinarias/api/tipos-reparacion/guardar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            bootstrap.Modal.getInstance(document.getElementById('modalTipoReparacion')).hide();
            cargarTiposReparacion();
        } else {
            mostrarError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al guardar tipo de reparación');
    });
}

// Mostrar modal de confirmación para eliminar
function mostrarModalEliminar(tipoId, nombre) {
    tipoIdEliminar = tipoId;
    document.getElementById('tipoEliminarNombre').textContent = nombre;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmEliminarModal'));
    modal.show();
}

// Confirmar eliminación
function confirmarEliminar() {
    if (!tipoIdEliminar) return;
    
    fetch(`/maquinarias/api/tipos-reparacion/${tipoIdEliminar}/eliminar/`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            bootstrap.Modal.getInstance(document.getElementById('confirmEliminarModal')).hide();
            cargarTiposReparacion();
        } else {
            mostrarError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al eliminar tipo de reparación');
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

function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

