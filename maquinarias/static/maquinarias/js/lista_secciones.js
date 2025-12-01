// Variables globales
let paginaActual = 1;
let tamanoPagina = 10;
let seccionIdEliminar = null;

// Cargar secciones al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarSecciones();
    
    // Event listeners
    document.getElementById('searchInput').addEventListener('input', debounce(cargarSecciones, 500));
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);
        paginaActual = 1;
        cargarSecciones();
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

// Cargar secciones con paginación y búsqueda
function cargarSecciones() {
    const search = document.getElementById('searchInput').value;
    
    const params = new URLSearchParams({
        search: search,
        page: paginaActual,
        per_page: tamanoPagina
    });
    
    fetch(`/maquinarias/api/secciones/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarSecciones(data.secciones);
                renderizarPaginacion(data);
                actualizarEstadisticas(data.total);
            } else {
                mostrarError('Error al cargar secciones: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar secciones');
        });
}

// Renderizar tabla de secciones
function renderizarSecciones(secciones) {
    const tbody = document.getElementById('seccionesTableBody');
    
    if (secciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron secciones</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = secciones.map(seccion => `
        <tr>
            <td><strong>${seccion.nombre}</strong></td>
            <td>${seccion.descripcion || '<span class="text-muted">Sin descripción</span>'}</td>
            <td class="text-center">
                <span class="badge bg-info">${seccion.total_tipos_reparacion}</span>
            </td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${window.userPermissions.canChange ? `
                    <button class="btn btn-sm btn-secondary" 
                            onclick="mostrarModalEditar(${seccion.seccion_id})" 
                            title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ` : ''}
                    ${window.userPermissions.canDelete ? `
                    <button class="btn btn-sm btn-danger" 
                            onclick="mostrarModalEliminar(${seccion.seccion_id}, '${seccion.nombre}')" 
                            title="Eliminar">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                    ` : ''}
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
    document.getElementById('totalSecciones').textContent = total;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    cargarSecciones();
}

// Limpiar búsqueda
function limpiarBusqueda() {
    document.getElementById('searchInput').value = '';
    paginaActual = 1;
    cargarSecciones();
}

// Mostrar modal para crear
function mostrarModalCrear() {
    document.getElementById('seccion_id').value = '';
    document.getElementById('nombre').value = '';
    document.getElementById('descripcion').value = '';
    document.getElementById('modalTitulo').textContent = 'Nueva Sección';
    
    const modal = new bootstrap.Modal(document.getElementById('modalSeccion'));
    modal.show();
}

// Mostrar modal para editar
function mostrarModalEditar(seccionId) {
    fetch(`/maquinarias/api/secciones/?search=&page=1&per_page=1000`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const seccion = data.secciones.find(s => s.seccion_id === seccionId);
                if (seccion) {
                    document.getElementById('seccion_id').value = seccion.seccion_id;
                    document.getElementById('nombre').value = seccion.nombre;
                    document.getElementById('descripcion').value = seccion.descripcion || '';
                    document.getElementById('modalTitulo').textContent = 'Editar Sección';
                    
                    const modal = new bootstrap.Modal(document.getElementById('modalSeccion'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar datos de la sección');
        });
}

// Guardar sección
function guardarSeccion() {
    const seccionId = document.getElementById('seccion_id').value;
    const nombre = document.getElementById('nombre').value.trim();
    const descripcion = document.getElementById('descripcion').value.trim();
    
    // Validación
    if (!nombre) {
        mostrarError('El nombre es requerido');
        return;
    }
    
    const data = {
        seccion_id: seccionId || null,
        nombre: nombre,
        descripcion: descripcion
    };
    
    fetch('/maquinarias/api/secciones/guardar/', {
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
            bootstrap.Modal.getInstance(document.getElementById('modalSeccion')).hide();
            cargarSecciones();
        } else {
            mostrarError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al guardar sección');
    });
}

// Mostrar modal de confirmación para eliminar
function mostrarModalEliminar(seccionId, nombre) {
    seccionIdEliminar = seccionId;
    document.getElementById('seccionEliminarNombre').textContent = nombre;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmEliminarModal'));
    modal.show();
}

// Confirmar eliminación
function confirmarEliminar() {
    if (!seccionIdEliminar) return;
    
    fetch(`/maquinarias/api/secciones/${seccionIdEliminar}/eliminar/`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            bootstrap.Modal.getInstance(document.getElementById('confirmEliminarModal')).hide();
            cargarSecciones();
        } else {
            mostrarError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al eliminar sección');
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

