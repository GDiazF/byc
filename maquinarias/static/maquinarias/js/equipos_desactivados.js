// Variables globales
let paginaActual = 1;
let registrosPorPagina = 10;
let equiposDesactivados = [];
let equiposFiltrados = [];
let currentToggle = null;
let originalState = false;
let changeConfirmed = false;

// Cargar al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarEquiposDesactivados();
    
    // Event listeners
    document.getElementById('searchInput').addEventListener('input', debounce(filtrarEquipos, 300));
    document.getElementById('filtroTipo').addEventListener('change', filtrarEquipos);
    document.getElementById('filtroEmpresa').addEventListener('change', filtrarEquipos);
    
    // Configurar botón de confirmación del modal
    document.getElementById('btnConfirmarActivar').addEventListener('click', confirmarActivacion);
    
    // Limpiar al cerrar modal de confirmación
    document.getElementById('confirmActivarModal').addEventListener('hidden.bs.modal', function() {
        if (currentToggle && !changeConfirmed) {
            currentToggle.checked = originalState;
        }
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
});

// Debounce
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

// Cargar equipos desactivados
function cargarEquiposDesactivados() {
    const params = new URLSearchParams({
        estado: 'inactivos',
        page: 1,
        page_size: 9999  // Traer todos para manejar paginación en frontend
    });
    
    fetch(`/maquinarias/api/equipos/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                equiposDesactivados = data.equipos;
                filtrarEquipos();
            }
        })
        .catch(error => console.error('Error:', error));
}

// Filtrar equipos
function filtrarEquipos() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const tipoFiltro = document.getElementById('filtroTipo').value;
    const empresaFiltro = document.getElementById('filtroEmpresa').value;
    
    equiposFiltrados = equiposDesactivados.filter(equipo => {
        const matchSearch = !searchTerm || 
            equipo.nombreEquipo.toLowerCase().includes(searchTerm) ||
            equipo.codigoInterno.toLowerCase().includes(searchTerm);
        
        const matchTipo = !tipoFiltro || equipo.tipoEquipo.nombre === tipoFiltro;
        const matchEmpresa = !empresaFiltro || equipo.empresa.nombre === empresaFiltro;
        
        return matchSearch && matchTipo && matchEmpresa;
    });
    
    paginaActual = 1;
    renderizarTabla();
}

// Renderizar tabla
function renderizarTabla() {
    const tbody = document.getElementById('equiposTableBody');
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const equiposPagina = equiposFiltrados.slice(inicio, fin);
    
    if (equiposPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5">
                    <i class="bi bi-check-circle text-success" style="font-size: 4rem;"></i>
                    <h5 class="mt-3 text-success">¡Excelente!</h5>
                    <p class="text-muted">No hay equipos desactivados en este momento.</p>
                    <p class="text-muted small">Todos los equipos se encuentran activos y disponibles.</p>
                </td>
            </tr>
        `;
        document.getElementById('totalRegistros').textContent = '0';
        document.getElementById('registroInicio').textContent = '0';
        document.getElementById('registroFin').textContent = '0';
        document.getElementById('totalRegistrosPaginacion').textContent = '0';
        return;
    }
    
    tbody.innerHTML = equiposPagina.map(equipo => `
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
                <div class="form-check form-switch d-inline-block">
                    <input class="form-check-input" type="checkbox" 
                           style="cursor: pointer;"
                           data-equipo-id="${equipo.equipo_id}"
                           data-nombre-equipo="${equipo.nombreEquipo.replace(/'/g, "\\'")}"
                           ${equipo.activo ? 'checked' : ''} 
                           onchange="toggleEstadoEquipo(this)"
                           title="Activar equipo">
                </div>
            </td>
        </tr>
    `).join('');
    
    // Actualizar contadores
    document.getElementById('totalRegistros').textContent = equiposFiltrados.length;
    document.getElementById('registroInicio').textContent = equiposFiltrados.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = Math.min(fin, equiposFiltrados.length);
    document.getElementById('totalRegistrosPaginacion').textContent = equiposFiltrados.length;
    
    renderizarPaginacion();
}

// Renderizar paginación
function renderizarPaginacion() {
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    const paginacionDiv = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacionDiv.innerHTML = '';
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
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActual - 2 && i <= paginaActual + 2)) {
            html += `
                <li class="page-item ${i === paginaActual ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActual - 3 || i === paginaActual + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionDiv.innerHTML = html;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    renderizarTabla();
}

// Cambiar registros por página
function cambiarRegistrosPorPagina() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1;
    renderizarTabla();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filtroTipo').value = '';
    document.getElementById('filtroEmpresa').value = '';
    filtrarEquipos();
}

// ============================================================================
// TOGGLE DE ESTADO (ACTIVAR)
// ============================================================================

function toggleEstadoEquipo(checkbox) {
    currentToggle = checkbox;
    originalState = !checkbox.checked;
    changeConfirmed = false;
    
    // Revertir el cambio hasta que se confirme
    checkbox.checked = originalState;
    
    // Actualizar nombre del equipo en el modal
    const nombreEquipo = checkbox.dataset.nombreEquipo;
    const nombreElement = document.getElementById('equipoActivarNombre');
    if (nombreElement) {
        nombreElement.textContent = nombreEquipo;
    }
    
    // Cerrar cualquier instancia existente del modal primero
    const modalElement = document.getElementById('confirmActivarModal');
    if (!modalElement) {
        console.error('Modal element not found');
        return;
    }
    
    const existingModal = bootstrap.Modal.getInstance(modalElement);
    if (existingModal) {
        existingModal.dispose();
    }
    
    // Mostrar modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

function confirmarActivacion() {
    if (!currentToggle) return;
    
    const equipoId = parseInt(currentToggle.dataset.equipoId);
    
    // Llamada AJAX para actualizar el estado
    fetch(`/maquinarias/api/equipos/${equipoId}/toggle-activo/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            changeConfirmed = true;
            
            // Cerrar modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
            confirmModal.hide();
            
            // Mostrar mensaje de éxito
            showNotification('Equipo activado correctamente', 'success');
            
            // Recargar lista
            cargarEquiposDesactivados();
        } else {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
            confirmModal.hide();
            alert('Error: ' + (data.message || 'Error al cambiar el estado del equipo'));
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
        confirmModal.hide();
        alert('Error al cambiar el estado del equipo');
        currentToggle.checked = originalState;
    });
}

// Sistema de notificaciones
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

