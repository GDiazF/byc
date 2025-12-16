/**
 * Gestión de tabla de ausentismos con JavaScript vanilla (sin DataTables/jQuery).
 * 
 * Maneja el renderizado, ordenamiento, paginación y eliminación de ausentismos.
 */

// Variables globales
let ausentismos = [];
let ausentismosFiltrados = [];
let paginaActual = 1;
let registrosPorPagina = 10;
let ordenActual = { columna: 'fechaInicioSort', direccion: 'desc' };
let ausentismoIdToDelete = null;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando tabla de ausentismos...');
    
    // Cargar datos
    ausentismos = window.ausentismosData || [];
    console.log(`Cargados ${ausentismos.length} ausentismos`);
    
    // Inicializar event listeners
    inicializarEventListeners();
    
    // Renderizar tabla inicial
    renderizarTabla();
});

// ============================================================================
// EVENT LISTENERS
// ============================================================================

/**
 * Inicializa todos los event listeners de la página.
 * Configura listeners para ordenamiento, modales y eliminación.
 */
function inicializarEventListeners() {
    // Ordenamiento por columnas
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const columna = this.dataset.column;
            ordenarPor(columna);
        });
    });
    
    // Modales
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmarEliminacion);
    
    // Limpiar al cerrar modal
    document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
        ausentismoIdToDelete = null;
    });
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

/**
 * Renderiza la tabla de ausentismos con ordenamiento y paginación aplicados.
 * 
 * Filtra, ordena y pagina los ausentismos según la configuración actual,
 * y actualiza los contadores y controles de paginación.
 */
function renderizarTabla() {
    const tbody = document.getElementById('ausentismosTableBody');
    
    // Filtrar (preparado para filtros futuros)
    ausentismosFiltrados = [...ausentismos];
    
    // Ordenar
    ausentismosFiltrados.sort((a, b) => {
        let valorA = a[ordenActual.columna] || '';
        let valorB = b[ordenActual.columna] || '';
        
        // Para números
        if (ordenActual.columna === 'dias') {
            return ordenActual.direccion === 'asc' ? 
                valorA - valorB : valorB - valorA;
        }
        
        // Para strings
        valorA = valorA.toString().toLowerCase();
        valorB = valorB.toString().toLowerCase();
        
        if (valorA < valorB) return ordenActual.direccion === 'asc' ? -1 : 1;
        if (valorA > valorB) return ordenActual.direccion === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Actualizar contador
    document.getElementById('totalRegistros').textContent = ausentismosFiltrados.length;
    
    // Si no hay resultados
    if (ausentismosFiltrados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No hay ausentismos registrados</p>
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
    const totalPaginas = Math.ceil(ausentismosFiltrados.length / registrosPorPagina);
    paginaActual = Math.min(paginaActual, totalPaginas);
    paginaActual = Math.max(1, paginaActual);
    
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, ausentismosFiltrados.length);
    const ausentismosPagina = ausentismosFiltrados.slice(inicio, fin);
    
    // Renderizar filas
    tbody.innerHTML = ausentismosPagina.map(aus => `
        <tr>
            <td>
                <i class="bi bi-calendar-event me-1"></i>${aus.tipo}
            </td>
            <td>${aus.fechaInicio}</td>
            <td>${aus.fechaFin}</td>
            <td class="text-center">
                <span class="badge bg-primary">${aus.dias} días</span>
            </td>
            <td class="text-center">
                ${aus.activo ? 
                    '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Activo</span>' : 
                    '<span class="badge bg-secondary">Vencido</span>'}
            </td>
            <td class="small">${aus.observacion}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/users/personal/${window.personalId}/ausentismos/${aus.id}/update/" 
                       class="btn btn-warning btn-sm" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-danger btn-sm" 
                            onclick="abrirModalEliminar(${aus.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Actualizar información de paginación
    document.getElementById('registroInicio').textContent = ausentismosFiltrados.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistrosPaginacion').textContent = ausentismosFiltrados.length;
    
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
    
    // Páginas numeradas
    for (let i = 1; i <= totalPaginas; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPagina(${i})">${i}</a>
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
        ordenActual.direccion = ordenActual.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenActual.columna = columna;
        ordenActual.direccion = 'asc';
    }
    renderizarTabla();
}

function actualizarIconosOrdenamiento() {
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up ms-1';
    });
    
    const thActual = document.querySelector(`.sortable[data-column="${ordenActual.columna}"]`);
    if (thActual) {
        const icon = thActual.querySelector('i');
        icon.className = ordenActual.direccion === 'asc' ? 
            'bi bi-arrow-up ms-1' : 
            'bi bi-arrow-down ms-1';
    }
}

// ============================================================================
// ELIMINACIÓN
// ============================================================================

function abrirModalEliminar(ausentismoId) {
    ausentismoIdToDelete = ausentismoId;
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

function confirmarEliminacion() {
    if (!ausentismoIdToDelete) return;
    
    // Crear formulario para el POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/users/personal/ausentismos/${ausentismoIdToDelete}/delete/`;
    
    // Agregar CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = window.csrfToken;
    form.appendChild(csrfInput);
    
    // Agregar al DOM y enviar
    document.body.appendChild(form);
    form.submit();
}

