// ============================================================================
// GESTIONAR AUSENCIAS - Licencias Médicas y Ausentismos en Tabs
// ============================================================================

// Estado global para LICENCIAS
let paginaActualLicencias = 1;
let registrosPorPaginaLicencias = 10;
let personalFiltradoLicencias = [];
let ordenLicencias = { columna: null, direccion: 'asc' };

// Estado global para AUSENTISMOS
let paginaActualAusentismos = 1;
let registrosPorPaginaAusentismos = 10;
let personalFiltradoAusentismos = [];
let ordenAusentismos = { columna: null, direccion: 'asc' };

// ============================================================================
// FUNCIONES PARA LICENCIAS MÉDICAS
// ============================================================================

function renderizarTablaLicencias() {
    const searchTerm = document.getElementById('searchInputLicencias').value.toLowerCase();
    const empresaFiltro = document.getElementById('filtroEmpresaLicencias').value;
    
    // Filtrar
    personalFiltradoLicencias = window.personalDataLicencias.filter(p => {
        const matchSearch = p.nombre.toLowerCase().includes(searchTerm) ||
                          p.rut.toLowerCase().includes(searchTerm) ||
                          p.cargo.toLowerCase().includes(searchTerm);
        const matchEmpresa = !empresaFiltro || p.empresa === empresaFiltro;
        return matchSearch && matchEmpresa;
    });
    
    // Ordenar
    if (ordenLicencias.columna) {
        personalFiltradoLicencias.sort((a, b) => {
            let valA = a[ordenLicencias.columna];
            let valB = b[ordenLicencias.columna];
            
            if (typeof valA === 'string') {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }
            
            if (valA < valB) return ordenLicencias.direccion === 'asc' ? -1 : 1;
            if (valA > valB) return ordenLicencias.direccion === 'asc' ? 1 : -1;
            return 0;
        });
    }
    
    // Paginar
    const inicio = (paginaActualLicencias - 1) * registrosPorPaginaLicencias;
    const fin = registrosPorPaginaLicencias === 9999 ? personalFiltradoLicencias.length : inicio + registrosPorPaginaLicencias;
    const personalPagina = personalFiltradoLicencias.slice(inicio, fin);
    
    // Renderizar
    const tbody = document.getElementById('personalTableBodyLicencias');
    if (personalPagina.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No se encontraron trabajadores</td></tr>';
    } else {
        tbody.innerHTML = personalPagina.map(p => `
            <tr>
                <td>${p.rut}</td>
                <td><strong>${p.nombre}</strong></td>
                <td>${p.cargo}</td>
                <td>${p.empresa}</td>
                <td class="text-center">
                    <span class="badge ${p.licenciasActivas > 0 ? 'bg-warning text-dark' : 'bg-secondary'}">
                        ${p.licenciasActivas}
                    </span>
                </td>
                <td class="text-center">
                    <a href="/users/personal/${p.id}/licencias_medicas/" 
                       class="btn btn-primary btn-sm" title="Ver Licencias">
                        <i class="bi bi-clipboard-pulse me-1"></i>Ver
                    </a>
                </td>
            </tr>
        `).join('');
    }
    
    // Actualizar contadores y paginación
    document.getElementById('totalRegistrosLicencias').textContent = personalFiltradoLicencias.length;
    document.getElementById('registroInicioLicencias').textContent = personalFiltradoLicencias.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinLicencias').textContent = Math.min(fin, personalFiltradoLicencias.length);
    document.getElementById('totalRegistrosPaginacionLicencias').textContent = personalFiltradoLicencias.length;
    
    renderizarPaginacionLicencias();
}

function renderizarPaginacionLicencias() {
    const totalPaginas = Math.ceil(personalFiltradoLicencias.length / registrosPorPaginaLicencias);
    const paginacion = document.getElementById('paginacionLicencias');
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = `
        <li class="page-item ${paginaActualLicencias === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaLicencias(${paginaActualLicencias - 1}); return false;">Anterior</a>
        </li>
    `;
    
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActualLicencias - 1 && i <= paginaActualLicencias + 1)) {
            html += `
                <li class="page-item ${i === paginaActualLicencias ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPaginaLicencias(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActualLicencias - 2 || i === paginaActualLicencias + 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    html += `
        <li class="page-item ${paginaActualLicencias === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaLicencias(${paginaActualLicencias + 1}); return false;">Siguiente</a>
        </li>
    `;
    
    paginacion.innerHTML = html;
}

function cambiarPaginaLicencias(nuevaPagina) {
    const totalPaginas = Math.ceil(personalFiltradoLicencias.length / registrosPorPaginaLicencias);
    if (nuevaPagina < 1 || nuevaPagina > totalPaginas) return;
    paginaActualLicencias = nuevaPagina;
    renderizarTablaLicencias();
}

function cambiarRegistrosPorPaginaLicencias() {
    registrosPorPaginaLicencias = parseInt(document.getElementById('registrosPorPaginaLicencias').value);
    paginaActualLicencias = 1;
    renderizarTablaLicencias();
}

function ordenarPorLicencias(columna) {
    if (ordenLicencias.columna === columna) {
        ordenLicencias.direccion = ordenLicencias.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenLicencias.columna = columna;
        ordenLicencias.direccion = 'asc';
    }
    actualizarIconosOrdenamientoLicencias();
    renderizarTablaLicencias();
}

function actualizarIconosOrdenamientoLicencias() {
    document.querySelectorAll('#personalTableLicencias .sortable[data-tipo="licencias"]').forEach(th => {
        const icon = th.querySelector('i');
        if (th.dataset.column === ordenLicencias.columna) {
            icon.className = ordenLicencias.direccion === 'asc' ? 'bi bi-arrow-up ms-1' : 'bi bi-arrow-down ms-1';
        } else {
            icon.className = 'bi bi-arrow-down-up ms-1';
        }
    });
}

function limpiarFiltrosLicencias() {
    document.getElementById('searchInputLicencias').value = '';
    document.getElementById('filtroEmpresaLicencias').value = '';
    paginaActualLicencias = 1;
    renderizarTablaLicencias();
}

// ============================================================================
// FUNCIONES PARA AUSENTISMOS
// ============================================================================

function renderizarTablaAusentismos() {
    const searchTerm = document.getElementById('searchInputAusentismos').value.toLowerCase();
    const empresaFiltro = document.getElementById('filtroEmpresaAusentismos').value;
    
    // Filtrar
    personalFiltradoAusentismos = window.personalDataAusentismos.filter(p => {
        const matchSearch = p.nombre.toLowerCase().includes(searchTerm) ||
                          p.rut.toLowerCase().includes(searchTerm) ||
                          p.cargo.toLowerCase().includes(searchTerm);
        const matchEmpresa = !empresaFiltro || p.empresa === empresaFiltro;
        return matchSearch && matchEmpresa;
    });
    
    // Ordenar
    if (ordenAusentismos.columna) {
        personalFiltradoAusentismos.sort((a, b) => {
            let valA = a[ordenAusentismos.columna];
            let valB = b[ordenAusentismos.columna];
            
            if (typeof valA === 'string') {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }
            
            if (valA < valB) return ordenAusentismos.direccion === 'asc' ? -1 : 1;
            if (valA > valB) return ordenAusentismos.direccion === 'asc' ? 1 : -1;
            return 0;
        });
    }
    
    // Paginar
    const inicio = (paginaActualAusentismos - 1) * registrosPorPaginaAusentismos;
    const fin = registrosPorPaginaAusentismos === 9999 ? personalFiltradoAusentismos.length : inicio + registrosPorPaginaAusentismos;
    const personalPagina = personalFiltradoAusentismos.slice(inicio, fin);
    
    // Renderizar
    const tbody = document.getElementById('personalTableBodyAusentismos');
    if (personalPagina.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No se encontraron trabajadores</td></tr>';
    } else {
        tbody.innerHTML = personalPagina.map(p => `
            <tr>
                <td>${p.rut}</td>
                <td><strong>${p.nombre}</strong></td>
                <td>${p.cargo}</td>
                <td>${p.empresa}</td>
                <td class="text-center">
                    <span class="badge ${p.ausentismosActivos > 0 ? 'bg-info text-dark' : 'bg-secondary'}">
                        ${p.ausentismosActivos}
                    </span>
                </td>
                <td class="text-center">
                    <a href="/users/personal/${p.id}/ausentismos/" 
                       class="btn btn-primary btn-sm" title="Ver Ausentismos">
                        <i class="bi bi-calendar-x me-1"></i>Ver
                    </a>
                </td>
            </tr>
        `).join('');
    }
    
    // Actualizar contadores y paginación
    document.getElementById('totalRegistrosAusentismos').textContent = personalFiltradoAusentismos.length;
    document.getElementById('registroInicioAusentismos').textContent = personalFiltradoAusentismos.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinAusentismos').textContent = Math.min(fin, personalFiltradoAusentismos.length);
    document.getElementById('totalRegistrosPaginacionAusentismos').textContent = personalFiltradoAusentismos.length;
    
    renderizarPaginacionAusentismos();
}

function renderizarPaginacionAusentismos() {
    const totalPaginas = Math.ceil(personalFiltradoAusentismos.length / registrosPorPaginaAusentismos);
    const paginacion = document.getElementById('paginacionAusentismos');
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = `
        <li class="page-item ${paginaActualAusentismos === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaAusentismos(${paginaActualAusentismos - 1}); return false;">Anterior</a>
        </li>
    `;
    
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActualAusentismos - 1 && i <= paginaActualAusentismos + 1)) {
            html += `
                <li class="page-item ${i === paginaActualAusentismos ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPaginaAusentismos(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActualAusentismos - 2 || i === paginaActualAusentismos + 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    html += `
        <li class="page-item ${paginaActualAusentismos === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaAusentismos(${paginaActualAusentismos + 1}); return false;">Siguiente</a>
        </li>
    `;
    
    paginacion.innerHTML = html;
}

function cambiarPaginaAusentismos(nuevaPagina) {
    const totalPaginas = Math.ceil(personalFiltradoAusentismos.length / registrosPorPaginaAusentismos);
    if (nuevaPagina < 1 || nuevaPagina > totalPaginas) return;
    paginaActualAusentismos = nuevaPagina;
    renderizarTablaAusentismos();
}

function cambiarRegistrosPorPaginaAusentismos() {
    registrosPorPaginaAusentismos = parseInt(document.getElementById('registrosPorPaginaAusentismos').value);
    paginaActualAusentismos = 1;
    renderizarTablaAusentismos();
}

function ordenarPorAusentismos(columna) {
    if (ordenAusentismos.columna === columna) {
        ordenAusentismos.direccion = ordenAusentismos.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenAusentismos.columna = columna;
        ordenAusentismos.direccion = 'asc';
    }
    actualizarIconosOrdenamientoAusentismos();
    renderizarTablaAusentismos();
}

function actualizarIconosOrdenamientoAusentismos() {
    document.querySelectorAll('#personalTableAusentismos .sortable[data-tipo="ausentismos"]').forEach(th => {
        const icon = th.querySelector('i');
        if (th.dataset.column === ordenAusentismos.columna) {
            icon.className = ordenAusentismos.direccion === 'asc' ? 'bi bi-arrow-up ms-1' : 'bi bi-arrow-down ms-1';
        } else {
            icon.className = 'bi bi-arrow-down-up ms-1';
        }
    });
}

function limpiarFiltrosAusentismos() {
    document.getElementById('searchInputAusentismos').value = '';
    document.getElementById('filtroEmpresaAusentismos').value = '';
    paginaActualAusentismos = 1;
    renderizarTablaAusentismos();
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Verificar si hay un tab especificado en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    if (tabParam === 'ausentismos') {
        // Activar el tab de ausentismos
        const ausentismosTab = document.getElementById('ausentismos-tab');
        const ausentismosPane = document.getElementById('ausentismos');
        const licenciasTab = document.getElementById('licencias-tab');
        const licenciasPane = document.getElementById('licencias');
        
        licenciasTab.classList.remove('active');
        licenciasPane.classList.remove('show', 'active');
        ausentismosTab.classList.add('active');
        ausentismosPane.classList.add('show', 'active');
    }
    // Si es 'licencias' o no hay parámetro, el tab de licencias ya está activo por defecto
    
    // Renderizar ambas tablas inicialmente
    renderizarTablaLicencias();
    renderizarTablaAusentismos();
    
    // Event listeners para LICENCIAS
    document.getElementById('searchInputLicencias').addEventListener('input', () => {
        paginaActualLicencias = 1;
        renderizarTablaLicencias();
    });
    
    document.getElementById('filtroEmpresaLicencias').addEventListener('change', () => {
        paginaActualLicencias = 1;
        renderizarTablaLicencias();
    });
    
    document.getElementById('registrosPorPaginaLicencias').addEventListener('change', cambiarRegistrosPorPaginaLicencias);
    
    document.getElementById('limpiarFiltrosLicencias').addEventListener('click', limpiarFiltrosLicencias);
    
    document.querySelectorAll('#personalTableLicencias .sortable[data-tipo="licencias"]').forEach(th => {
        th.addEventListener('click', () => ordenarPorLicencias(th.dataset.column));
    });
    
    // Event listeners para AUSENTISMOS
    document.getElementById('searchInputAusentismos').addEventListener('input', () => {
        paginaActualAusentismos = 1;
        renderizarTablaAusentismos();
    });
    
    document.getElementById('filtroEmpresaAusentismos').addEventListener('change', () => {
        paginaActualAusentismos = 1;
        renderizarTablaAusentismos();
    });
    
    document.getElementById('registrosPorPaginaAusentismos').addEventListener('change', cambiarRegistrosPorPaginaAusentismos);
    
    document.getElementById('limpiarFiltrosAusentismos').addEventListener('click', limpiarFiltrosAusentismos);
    
    document.querySelectorAll('#personalTableAusentismos .sortable[data-tipo="ausentismos"]').forEach(th => {
        th.addEventListener('click', () => ordenarPorAusentismos(th.dataset.column));
    });
});

