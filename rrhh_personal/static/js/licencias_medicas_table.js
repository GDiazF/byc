// ============================================================================
// LICENCIAS MÉDICAS - TABLA PERSONALIZADA
// Sin DataTables/jQuery - JavaScript vanilla
// ============================================================================

// Variables globales
let licencias = [];
let licenciasFiltradas = [];
let paginaActual = 1;
let registrosPorPagina = 10;
let ordenActual = { columna: 'fechaEmisionSort', direccion: 'desc' };
let licenciaIdToDelete = null;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando tabla de licencias médicas...');
    
    // Cargar datos
    licencias = window.licenciasData || [];
    console.log(`Cargadas ${licencias.length} licencias médicas`);
    
    // Inicializar event listeners
    inicializarEventListeners();
    
    // Renderizar tabla inicial
    renderizarTabla();
});

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function inicializarEventListeners() {
    // Ordenamiento por columnas
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const columna = this.dataset.column;
            ordenarPor(columna);
        });
    });
    
    // Modales
    document.getElementById('confirmButton').addEventListener('click', confirmarEliminacion);
    
    // Limpiar al cerrar modal
    document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
        licenciaIdToDelete = null;
    });
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

function renderizarTabla() {
    const tbody = document.getElementById('licenciasTableBody');
    
    // Filtrar (por ahora sin filtros, pero preparado para el futuro)
    licenciasFiltradas = [...licencias];
    
    // Ordenar
    licenciasFiltradas.sort((a, b) => {
        let valorA = a[ordenActual.columna] || '';
        let valorB = b[ordenActual.columna] || '';
        
        // Para fechas, usar la versión sort (Y-m-d)
        if (ordenActual.columna === 'fechaEmision') {
            valorA = a.fechaEmisionSort;
            valorB = b.fechaEmisionSort;
        } else if (ordenActual.columna === 'fechaFin') {
            valorA = a.fechaFinSort;
            valorB = b.fechaFinSort;
        }
        
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
    document.getElementById('totalRegistros').textContent = licenciasFiltradas.length;
    
    // Si no hay resultados
    if (licenciasFiltradas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No hay licencias médicas</p>
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
    const totalPaginas = Math.ceil(licenciasFiltradas.length / registrosPorPagina);
    paginaActual = Math.min(paginaActual, totalPaginas);
    paginaActual = Math.max(1, paginaActual);
    
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, licenciasFiltradas.length);
    const licenciasPagina = licenciasFiltradas.slice(inicio, fin);
    
    // Renderizar filas
    tbody.innerHTML = licenciasPagina.map(lic => `
        <tr>
            <td>${lic.tipo}</td>
            <td>${lic.fechaEmision}</td>
            <td class="text-center"><strong>${lic.dias}</strong></td>
            <td>${lic.fechaFin}</td>
            <td class="text-center">
                ${lic.activa ? 
                    '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Activa</span>' : 
                    '<span class="badge bg-secondary">Vencida</span>'}
            </td>
            <td class="small">${lic.observacion}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/users/licencia_medica/${lic.id}/edit/" class="btn btn-warning btn-sm" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-danger btn-sm" 
                            onclick="abrirModalEliminar(${lic.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Actualizar información de paginación
    document.getElementById('registroInicio').textContent = licenciasFiltradas.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistrosPaginacion').textContent = licenciasFiltradas.length;
    
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

function abrirModalEliminar(licenciaId) {
    licenciaIdToDelete = licenciaId;
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

function confirmarEliminacion() {
    if (!licenciaIdToDelete) return;
    
    // Crear formulario para el POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/users/licencia_medica/${licenciaIdToDelete}/delete/`;
    
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

