// ============================================================================
// GESTIÓN DE PERSONAL - TABLA PERSONALIZADA (Sin DataTables/jQuery)
// Reemplazo completo de DataTables con JavaScript vanilla
// ============================================================================

// Variables globales
let personal = [];
let personalFiltrado = [];
let paginaActual = 1;
let registrosPorPagina = 10;
let ordenActual = { columna: 'nombre', direccion: 'asc' };
let currentToggle = null;
let originalState = false;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando tabla personalizada de gestión de personal...');
    
    // Cargar datos del personal
    personal = window.personalData || [];
    console.log(`Cargados ${personal.length} registros de personal`);
    
    // Inicializar event listeners
    inicializarEventListeners();
    
    // Renderizar tabla inicial
    renderizarTabla();
});

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function inicializarEventListeners() {
    // Búsqueda
    document.getElementById('searchInput').addEventListener('input', function() {
        paginaActual = 1;
        renderizarTabla();
    });
    
    // Filtro de empresa
    document.getElementById('filtroEmpresa').addEventListener('change', function() {
        paginaActual = 1;
        renderizarTabla();
    });
    
    // Ordenamiento por columnas
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const columna = this.dataset.column;
            ordenarPor(columna);
        });
    });
    
    // Modales
    document.getElementById('confirmButton').addEventListener('click', confirmarDesactivacion);
    
    // Limpiar al cerrar modal de confirmación
    document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
        if (currentToggle && !changeConfirmed) {
            currentToggle.checked = originalState;
        }
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

function renderizarTabla() {
    const tbody = document.getElementById('personalTableBody');
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    const filtroEmpresa = document.getElementById('filtroEmpresa').value;
    
    // Filtrar personal
    personalFiltrado = personal.filter(p => {
        // Búsqueda global
        const matchBusqueda = !busqueda || 
            p.rut.toLowerCase().includes(busqueda) ||
            p.nombre.toLowerCase().includes(busqueda) ||
            p.cargo.toLowerCase().includes(busqueda) ||
            p.departamento.toLowerCase().includes(busqueda) ||
            p.empresa.toLowerCase().includes(busqueda);
        
        // Filtro de empresa
        const matchEmpresa = !filtroEmpresa || p.empresa === filtroEmpresa;
        
        return matchBusqueda && matchEmpresa;
    });
    
    // Ordenar
    personalFiltrado.sort((a, b) => {
        let valorA = a[ordenActual.columna] || '';
        let valorB = b[ordenActual.columna] || '';
        
        // Normalizar para comparación
        valorA = valorA.toString().toLowerCase();
        valorB = valorB.toString().toLowerCase();
        
        if (valorA < valorB) return ordenActual.direccion === 'asc' ? -1 : 1;
        if (valorA > valorB) return ordenActual.direccion === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Actualizar contador
    document.getElementById('totalRegistros').textContent = personalFiltrado.length;
    
    // Si no hay resultados
    if (personalFiltrado.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron registros con los filtros aplicados</p>
                </td>
            </tr>
        `;
        document.getElementById('paginacion').innerHTML = '';
        document.getElementById('registroInicio').textContent = '0';
        document.getElementById('registroFin').textContent = '0';
        document.getElementById('totalRegistrosPaginacion').textContent = '0';
        return;
    }
    
    // Calcular paginación
    const totalPaginas = Math.ceil(personalFiltrado.length / registrosPorPagina);
    paginaActual = Math.min(paginaActual, totalPaginas);
    paginaActual = Math.max(1, paginaActual);
    
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, personalFiltrado.length);
    const personalPagina = personalFiltrado.slice(inicio, fin);
    
    // Renderizar filas
    tbody.innerHTML = personalPagina.map(p => `
        <tr>
            <td>${p.rut}</td>
            <td>${p.nombre}</td>
            <td>${p.cargo}</td>
            <td>${p.departamento}</td>
            <td>${p.empresa}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    <a href="/users/personal/${p.id}/documentation/" class="btn btn-sm btn-primary" title="Ver Documentación">
                        <i class="bi bi-folder"></i>
                    </a>
                    <a href="/users/personal/${p.id}/update/" class="btn btn-sm btn-secondary" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-switch d-flex justify-content-center">
                    <input class="form-check-input" type="checkbox" 
                           data-id="${p.id}"
                           ${p.activo ? 'checked' : ''}
                           onchange="toggleEstado(this)">
                </div>
            </td>
        </tr>
    `).join('');
    
    // Actualizar información de paginación
    document.getElementById('registroInicio').textContent = personalFiltrado.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistrosPaginacion').textContent = personalFiltrado.length;
    
    // Renderizar controles de paginación
    renderizarPaginacion(totalPaginas);
    
    // Actualizar iconos de ordenamiento
    actualizarIconosOrdenamiento();
}

// ============================================================================
// PAGINACIÓN
// ============================================================================

function renderizarPaginacion(totalPaginas) {
    const paginacion = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(${paginaActual - 1})">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    const maxPaginas = 5;
    let inicio = Math.max(1, paginaActual - Math.floor(maxPaginas / 2));
    let fin = Math.min(totalPaginas, inicio + maxPaginas - 1);
    
    // Ajustar inicio si estamos cerca del final
    if (fin - inicio < maxPaginas - 1) {
        inicio = Math.max(1, fin - maxPaginas + 1);
    }
    
    // Primera página
    if (inicio > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(1)">1</a>
            </li>
        `;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Páginas numeradas
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(${i})">${i}</a>
            </li>
        `;
    }
    
    // Última página
    if (fin < totalPaginas) {
        if (fin < totalPaginas - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(${totalPaginas})">${totalPaginas}</a>
            </li>
        `;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(${paginaActual + 1})">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacion.innerHTML = html;
}

function cambiarPagina(nuevaPagina) {
    paginaActual = nuevaPagina;
    renderizarTabla();
}

function cambiarRegistrosPorPagina() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1;
    renderizarTabla();
}

// ============================================================================
// ORDENAMIENTO
// ============================================================================

function ordenarPor(columna) {
    if (ordenActual.columna === columna) {
        // Cambiar dirección
        ordenActual.direccion = ordenActual.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        // Nueva columna, orden ascendente
        ordenActual.columna = columna;
        ordenActual.direccion = 'asc';
    }
    renderizarTabla();
}

function actualizarIconosOrdenamiento() {
    // Limpiar todos los iconos
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up ms-1';
    });
    
    // Actualizar el icono de la columna ordenada
    const thActual = document.querySelector(`.sortable[data-column="${ordenActual.columna}"]`);
    if (thActual) {
        const icon = thActual.querySelector('i');
        icon.className = ordenActual.direccion === 'asc' ? 
            'bi bi-arrow-up ms-1' : 
            'bi bi-arrow-down ms-1';
    }
}

// ============================================================================
// FILTROS
// ============================================================================

function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filtroEmpresa').value = '';
    paginaActual = 1;
    renderizarTabla();
}

// ============================================================================
// TOGGLE DE ESTADO
// ============================================================================

let changeConfirmed = false;

function toggleEstado(checkbox) {
    currentToggle = checkbox;
    originalState = !checkbox.checked;
    changeConfirmed = false;
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
    
    // Revertir el cambio hasta que se confirme
    checkbox.checked = originalState;
}

function confirmarDesactivacion() {
    if (!currentToggle) return;
    
    const personalId = parseInt(currentToggle.dataset.id);
    const nuevoEstado = !originalState;
    
    // Llamada AJAX para actualizar el estado
    fetch('/users/personal/toggle-activo/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify({ personal_id: personalId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            changeConfirmed = true;
            
            // Cerrar modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
            confirmModal.hide();
            
            // Mostrar mensaje de éxito
            const accion = data.activo ? 'activado' : 'desactivado';
            document.getElementById('successModalBody').innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Personal ${accion} correctamente
            `;
            const successModal = new bootstrap.Modal(document.getElementById('successModal'));
            successModal.show();
            
            // Redirigir después de mostrar el mensaje
            setTimeout(() => {
                window.location.replace(window.location.pathname + '?updated=' + Date.now());
            }, 1500);
        } else {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
            confirmModal.hide();
            alert('Error: ' + (data.message || 'Error al cambiar el estado del personal'));
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
        confirmModal.hide();
        alert('Error al cambiar el estado del personal');
        currentToggle.checked = originalState;
    });
}

// ============================================================================
// UTILIDADES
// ============================================================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
