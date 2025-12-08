// Variables globales
let paginaActual = 1;
let tamanoPagina = 25;
let tabActual = 'activas'; // 'activas' o 'finalizadas'

// Cargar ordenes al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarOrdenes();
    
    // Event listeners para filtros de activas
    const searchInput = document.getElementById('searchInput');
    const empresaFilter = document.getElementById('empresaFilter');
    const tipoEquipoFilter = document.getElementById('tipoEquipoFilter');
    const estadoOTFilter = document.getElementById('estadoOTFilter');
    const tipoMantenimientoFilter = document.getElementById('tipoMantenimientoFilter');
    
    if (searchInput) searchInput.addEventListener('input', debounce(() => { tabActual = 'activas'; cargarOrdenes(); }, 500));
    if (empresaFilter) empresaFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (tipoEquipoFilter) tipoEquipoFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (estadoOTFilter) estadoOTFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (tipoMantenimientoFilter) tipoMantenimientoFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    
    // Event listeners para filtros de finalizadas
    const searchInputFinalizadas = document.getElementById('searchInputFinalizadas');
    const empresaFilterFinalizadas = document.getElementById('empresaFilterFinalizadas');
    const tipoEquipoFilterFinalizadas = document.getElementById('tipoEquipoFilterFinalizadas');
    const tipoMantenimientoFilterFinalizadas = document.getElementById('tipoMantenimientoFilterFinalizadas');
    
    if (searchInputFinalizadas) searchInputFinalizadas.addEventListener('input', debounce(() => { tabActual = 'finalizadas'; cargarOrdenes(); }, 500));
    if (empresaFilterFinalizadas) empresaFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    if (tipoEquipoFilterFinalizadas) tipoEquipoFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    if (tipoMantenimientoFilterFinalizadas) tipoMantenimientoFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    
    // Event listeners para tabs
    const tabActivas = document.getElementById('tab-activas');
    const tabFinalizadas = document.getElementById('tab-finalizadas');
    
    if (tabActivas) {
        tabActivas.addEventListener('shown.bs.tab', () => {
            tabActual = 'activas';
            paginaActual = 1;
            cargarOrdenes();
        });
    }
    
    if (tabFinalizadas) {
        tabFinalizadas.addEventListener('shown.bs.tab', () => {
            tabActual = 'finalizadas';
            paginaActual = 1;
            cargarOrdenes();
        });
    }
    
    // Event listeners para botones de limpiar filtros
    const btnLimpiarFiltros = document.getElementById('btnLimpiarFiltros');
    if (btnLimpiarFiltros) {
        btnLimpiarFiltros.addEventListener('click', limpiarFiltros);
    }
    
    const btnLimpiarFiltrosFinalizadas = document.getElementById('btnLimpiarFiltrosFinalizadas');
    if (btnLimpiarFiltrosFinalizadas) {
        btnLimpiarFiltrosFinalizadas.addEventListener('click', limpiarFiltrosFinalizadas);
    }
    
    // Event listener para cambiar tamaño de página
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', cambiarTamanoPagina);
    }
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

// Cargar ordenes con filtros
function cargarOrdenes() {
    const esFinalizadas = tabActual === 'finalizadas';
    
    let search, empresa, tipoEquipo, estadoOT, tipoMantenimiento;
    
    if (esFinalizadas) {
        search = document.getElementById('searchInputFinalizadas')?.value || '';
        empresa = document.getElementById('empresaFilterFinalizadas')?.value || '';
        tipoEquipo = document.getElementById('tipoEquipoFilterFinalizadas')?.value || '';
        estadoOT = '';
        tipoMantenimiento = document.getElementById('tipoMantenimientoFilterFinalizadas')?.value || '';
    } else {
        search = document.getElementById('searchInput')?.value || '';
        empresa = document.getElementById('empresaFilter')?.value || '';
        tipoEquipo = document.getElementById('tipoEquipoFilter')?.value || '';
        estadoOT = document.getElementById('estadoOTFilter')?.value || '';
        tipoMantenimiento = document.getElementById('tipoMantenimientoFilter')?.value || '';
    }
    
    const params = new URLSearchParams({
        search: search,
        empresa_id: empresa,
        tipo_equipo_id: tipoEquipo,
        estado_ot: estadoOT,
        tipo_mantenimiento: tipoMantenimiento,
        solo_finalizadas: esFinalizadas ? 'true' : 'false',
        page: paginaActual,
        per_page: tamanoPagina
    });
    
    fetch(`${window.apiListarOrdenes}?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (esFinalizadas) {
                    renderizarOrdenesFinalizadas(data.ordenes);
                } else {
                    renderizarOrdenes(data.ordenes);
                }
                renderizarPaginacion(data.pagination);
                actualizarEstadisticas(data.pagination);
            } else {
                mostrarError('Error al cargar ordenes de trabajo: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar ordenes de trabajo');
        });
}

// Función helper para obtener color de tipo de mantenimiento
function getColorTipoMantenimiento(tipo) {
    if (!tipo) return 'secondary';
    const tipoLower = tipo.toLowerCase();
    if (tipoLower.includes('preventivo')) return 'success'; // Verde
    if (tipoLower.includes('correctivo')) return 'danger'; // Rojo
    return 'secondary';
}

// Función helper para obtener color de estado OT
function getColorEstadoOT(estado) {
    if (!estado) return 'secondary';
    const estadoLower = estado.toLowerCase();
    if (estadoLower.includes('pendiente')) return 'secondary'; // Gris
    if (estadoLower.includes('proceso') || estadoLower.includes('en proceso')) return 'success'; // Verde
    if (estadoLower.includes('finalizada') || estadoLower.includes('terminada')) return 'dark'; // Negro
    if (estadoLower.includes('cancelada')) return 'danger'; // Rojo
    return 'secondary';
}

// Función helper para obtener color de estado equipo
function getColorEstadoEquipo(estado) {
    if (!estado) return 'secondary';
    const estadoLower = estado.toLowerCase();
    if (estadoLower.includes('shutdown')) return 'danger'; // Rojo
    if (estadoLower.includes('disponible') && !estadoLower.includes('reparación')) return 'success'; // Verde
    if (estadoLower.includes('reparación disponible') || estadoLower.includes('en reparación disponible')) return 'warning'; // Amarillo
    if (estadoLower.includes('reparación') || estadoLower.includes('en reparación')) return 'dark'; // Negro
    return 'secondary';
}

// Renderizar tabla de ordenes activas
function renderizarOrdenes(ordenes) {
    const tbody = document.getElementById('ordenesTableBody');
    if (!tbody) return;
    
    if (ordenes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron ordenes de trabajo</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = ordenes.map(ot => {
        // Badge para estado OT con colores definidos
        const estadoOTColor = getColorEstadoOT(ot.estado_ot);
        const estadoOTBadge = `<span class="badge bg-${estadoOTColor}">${ot.estado_ot || 'No disponible'}</span>`;
        
        // Badge para estado equipo con colores definidos
        const estadoEquipoColor = getColorEstadoEquipo(ot.estado_equipo);
        const estadoEquipoBadge = `<span class="badge bg-${estadoEquipoColor}">${ot.estado_equipo || 'No disponible'}</span>`;
        
        // Badge para tipo mantenimiento con colores definidos
        const tipoMantenimientoColor = getColorTipoMantenimiento(ot.tipo_mantenimiento);
        const tipoMantenimientoBadge = ot.tipo_mantenimiento 
            ? `<span class="badge bg-${tipoMantenimientoColor}">${ot.tipo_mantenimiento}</span>`
            : '<span class="badge bg-secondary">N/A</span>';
        
        // Fecha fin
        const fechaFin = ot.fecha_fin 
            ? new Date(ot.fecha_fin).toLocaleDateString('es-CL')
            : '<span class="text-muted">Sin fecha</span>';
        
        return `
            <tr>
                <td>
                    <a href="#" class="text-primary text-decoration-none fw-bold" onclick="verDetalleOT(${ot.ot_id}); return false;" title="Ver detalle">
                        ${ot.folio}
                    </a>
                </td>
                <td>
                    <strong>${ot.equipo.nombreEquipo}</strong>
                </td>
                <td>${ot.empresa.nomFantasia}</td>
                <td>${tipoMantenimientoBadge}</td>
                <td>${estadoOTBadge}</td>
                <td>${estadoEquipoBadge}</td>
                <td>${fechaFin}</td>
                <td class="text-center">
                    ${ot.estado_ot && (ot.estado_ot.toUpperCase().includes('FINALIZADA') || ot.estado_ot.toUpperCase().includes('CANCELADA')) 
                        ? (window.userPermissions && window.userPermissions.canView ? `
                        <button type="button" 
                            class="btn btn-info btn-sm" 
                            onclick="verDetalleOT(${ot.ot_id})"
                            title="Ver Detalle">
                            <i class="bi bi-eye"></i> Ver
                        </button>` : '')
                        : (window.userPermissions && window.userPermissions.canChange ? `
                        <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/editar/" 
                            class="btn btn-primary btn-sm" 
                            title="Actualizar">
                            <i class="bi bi-pencil"></i> Actualizar
                        </a>` : (window.userPermissions && window.userPermissions.canView ? `
                        <button type="button" 
                            class="btn btn-info btn-sm" 
                            onclick="verDetalleOT(${ot.ot_id})"
                            title="Ver Detalle">
                            <i class="bi bi-eye"></i> Ver
                        </button>` : ''))
                    }
                </td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canGenerarPDF ? `
                    <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/pdf/" 
                       class="btn btn-danger btn-sm" 
                       title="Descargar PDF"
                       target="_blank">
                        <i class="bi bi-file-pdf"></i> PDF
                    </a>
                    ` : `
                    <button class="btn btn-danger btn-sm" disabled title="No tiene permiso para descargar PDF">
                        <i class="bi bi-file-pdf"></i> PDF
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

// Renderizar tabla de ordenes finalizadas
function renderizarOrdenesFinalizadas(ordenes) {
    const tbody = document.getElementById('ordenesTableBodyFinalizadas');
    if (!tbody) return;
    
    if (ordenes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron ordenes finalizadas</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = ordenes.map(ot => {
        // Badge para estado OT con colores definidos
        const estadoOTColor = getColorEstadoOT(ot.estado_ot);
        const estadoOTBadge = `<span class="badge bg-${estadoOTColor}">${ot.estado_ot || 'No disponible'}</span>`;
        
        // Badge para estado equipo con colores definidos
        const estadoEquipoColor = getColorEstadoEquipo(ot.estado_equipo);
        const estadoEquipoBadge = `<span class="badge bg-${estadoEquipoColor}">${ot.estado_equipo || 'No disponible'}</span>`;
        
        // Badge para tipo mantenimiento con colores definidos
        const tipoMantenimientoColor = getColorTipoMantenimiento(ot.tipo_mantenimiento);
        const tipoMantenimientoBadge = ot.tipo_mantenimiento 
            ? `<span class="badge bg-${tipoMantenimientoColor}">${ot.tipo_mantenimiento}</span>`
            : '<span class="badge bg-secondary">N/A</span>';
        
        // Fecha fin
        const fechaFin = ot.fecha_fin 
            ? new Date(ot.fecha_fin).toLocaleDateString('es-CL')
            : '<span class="text-muted">Sin fecha</span>';
        
        return `
            <tr>
                <td>
                    <a href="#" class="text-primary text-decoration-none fw-bold" onclick="verDetalleOT(${ot.ot_id}); return false;" title="Ver detalle">
                        ${ot.folio}
                    </a>
                </td>
                <td>
                    <strong>${ot.equipo.nombreEquipo}</strong>
                </td>
                <td>${ot.empresa.nomFantasia}</td>
                <td>${tipoMantenimientoBadge}</td>
                <td>${estadoOTBadge}</td>
                <td>${estadoEquipoBadge}</td>
                <td>${fechaFin}</td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canView ? `
                    <button type="button" 
                        class="btn btn-info btn-sm" 
                        onclick="verDetalleOT(${ot.ot_id})"
                        title="Ver Detalle">
                        <i class="bi bi-eye"></i> Ver
                    </button>
                    ` : ''}
                </td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canGenerarPDF ? `
                    <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/pdf/" 
                       class="btn btn-danger btn-sm" 
                       title="Descargar PDF"
                       target="_blank">
                        <i class="bi bi-file-pdf"></i> PDF
                    </a>
                    ` : `
                    <button class="btn btn-danger btn-sm" disabled title="No tiene permiso para descargar PDF">
                        <i class="bi bi-file-pdf"></i> PDF
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

// Renderizar paginación
function renderizarPaginacion(pagination) {
    const paginacionEl = document.getElementById('paginacion');
    if (!paginacionEl) return;
    
    if (!pagination || pagination.pages <= 1) {
        paginacionEl.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${!pagination.has_prev ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="irAPagina(${pagination.page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Números de página
    const inicio = Math.max(1, pagination.page - 2);
    const fin = Math.min(pagination.pages, pagination.page + 2);
    
    if (inicio > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="irAPagina(1); return false;">1</a></li>`;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="irAPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (fin < pagination.pages) {
        if (fin < pagination.pages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="irAPagina(${pagination.pages}); return false;">${pagination.pages}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="irAPagina(${pagination.page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionEl.innerHTML = html;
}

// Ir a página específica
function irAPagina(pagina) {
    if (pagina < 1) return;
    paginaActual = pagina;
    cargarOrdenes();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Cambiar tamaño de página
function cambiarTamanoPagina() {
    tamanoPagina = parseInt(document.getElementById('pageSizeSelect').value);
    paginaActual = 1;
    cargarOrdenes();
}

// Actualizar estadísticas
function actualizarEstadisticas(pagination) {
    const totalOrdenes = document.getElementById('totalOrdenes');
    const registroInicio = document.getElementById('registroInicio');
    const registroFin = document.getElementById('registroFin');
    const totalRegistros = document.getElementById('totalRegistros');
    
    if (totalOrdenes) totalOrdenes.textContent = pagination.total;
    if (registroInicio) registroInicio.textContent = pagination.total > 0 
        ? ((pagination.page - 1) * pagination.per_page + 1) 
        : 0;
    if (registroFin) registroFin.textContent = Math.min(
        pagination.page * pagination.per_page,
        pagination.total
    );
    if (totalRegistros) totalRegistros.textContent = pagination.total;
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('empresaFilter').value = '';
    document.getElementById('tipoEquipoFilter').value = '';
    document.getElementById('estadoOTFilter').value = '';
    document.getElementById('tipoMantenimientoFilter').value = '';
    paginaActual = 1;
    tabActual = 'activas';
    cargarOrdenes();
}

// Limpiar filtros finalizadas
function limpiarFiltrosFinalizadas() {
    document.getElementById('searchInputFinalizadas').value = '';
    document.getElementById('empresaFilterFinalizadas').value = '';
    document.getElementById('tipoEquipoFilterFinalizadas').value = '';
    document.getElementById('tipoMantenimientoFilterFinalizadas').value = '';
    paginaActual = 1;
    tabActual = 'finalizadas';
    cargarOrdenes();
}

// Ver detalle de OT (modal)
function verDetalleOT(ot_id) {
    const modal = new bootstrap.Modal(document.getElementById('modalDetalleOT'));
    const modalTitle = document.getElementById('modalDetalleOTLabel');
    const panelInformacion = document.getElementById('panel-informacion');
    const panelObservaciones = document.getElementById('panel-observaciones');
    const panelHistorial = document.getElementById('panel-historial');
    
    // Mostrar loading en todas las pestañas
    panelInformacion.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando detalles...</p>
        </div>
    `;
    panelObservaciones.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando observaciones...</p>
        </div>
    `;
    panelHistorial.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando historial...</p>
        </div>
    `;
    
    // Activar primera pestaña
    const tabInformacion = document.getElementById('tab-informacion');
    if (tabInformacion) {
        const bsTab = new bootstrap.Tab(tabInformacion);
        bsTab.show();
    }
    
    modal.show();
    
    // Obtener detalles de la OT
    const urlDetalle = window.apiDetalleOT.replace('0', ot_id);
    fetch(urlDetalle)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar título del modal
                modalTitle.innerHTML = `<i class="bi bi-clipboard-data me-2"></i>Detalle - ${data.ot.folio}`;
                
                // Renderizar información general (sin observaciones ni historial)
                renderizarDetalleOT(data.ot, panelInformacion);
                
                // Renderizar observaciones
                renderizarObservacionesOT(data.ot, panelObservaciones);
            } else {
                panelInformacion.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar detalles: ${data.message}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            panelInformacion.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar detalles
                </div>
            `;
        });
    
    // Obtener historial de la OT
    const urlHistorial = window.apiHistorialOT.replace('0', ot_id);
    fetch(urlHistorial)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarHistorialOT(data, panelHistorial, null);
            } else {
                panelHistorial.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar historial: ${data.message}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            panelHistorial.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar historial
                </div>
            `;
        });
}

// Renderizar observaciones de OT
function renderizarObservacionesOT(ot, container) {
    let html = '';
    
    // Mostrar observación inicial si existe
    if (ot.observaciones) {
        html += `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary">
                                <i class="bi bi-file-text me-1"></i>Observación Inicial
                            </strong>
                        </div>
                        <small class="text-muted">
                            <i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(ot.fecha_creacion)}
                        </small>
                    </div>
                    <p class="mb-0">${ot.observaciones}</p>
                </div>
            </div>
        `;
    }
    
    // Mostrar historial de observaciones
    if (ot.historial_observaciones && ot.historial_observaciones.length > 0) {
        html += ot.historial_observaciones.map(obs => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary"><i class="bi bi-person-circle me-1"></i>${obs.usuario}</strong>
                        </div>
                        <small class="text-muted"><i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(obs.fecha)}</small>
                    </div>
                    <p class="mb-0">${obs.observacion}</p>
                </div>
            </div>
        `).join('');
    } else if (!ot.observaciones) {
        html = '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay observaciones registradas</div>';
    }
    
    container.innerHTML = `
        <div class="card border">
            <div class="card-body">
                ${html}
            </div>
        </div>
    `;
}

// Renderizar historial de OT en el modal
function renderizarHistorialOT(data, modalBody, modalTitle) {
    const historial = data.historial || [];
    
    // Actualizar título del modal solo si se proporciona
    if (modalTitle && data.ot) {
        modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${data.ot.folio}`;
    }
    
    let infoHTML = '';
    
    if (historial.length > 0) {
        // Tabla simple con filas expandibles (acordeón)
        infoHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">
                    <i class="bi bi-list-ul me-1"></i>Historial de Cambios
                </h6>
                <span class="badge bg-secondary">${historial.length} registro(s)</span>
            </div>
            <div class="table-responsive">
                <table class="table table-sm table-hover table-bordered">
                    <thead class="table-dark">
                        <tr>
                            <th style="width: 5%;"></th>
                            <th style="width: 15%;">Fecha y Hora</th>
                            <th style="width: 15%;">Usuario</th>
                            <th style="width: 20%;">Acción</th>
                            <th style="width: 45%;">Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        historial.forEach((evento, index) => {
            const badgeColor = getBadgeColorAccion(evento.accion);
            const rowId = `historial-row-${index}`;
            const detailsId = `historial-details-${index}`;
            
            // Generar detalles expandibles solo si hay información adicional que no esté en la descripción
            let detallesHTML = '';
            let tieneDetalles = false;
            
            // Solo mostrar detalles si hay información adicional relevante que no esté en la descripción
            // La descripción ya contiene los cambios principales, así que solo mostramos:
            // 1. Personal asignado (lista completa de nombres)
            // 2. Información adicional que no esté en la descripción
            
            if (evento.personal && Array.isArray(evento.personal) && evento.personal.length > 0) {
                // Personal asignado - mostrar lista completa si hay múltiples personas
                const nombres = evento.personal.map(p => p.nombre_completo).join(', ');
                detallesHTML = '<div class="small">';
                detallesHTML += `<div class="mb-2"><strong>Personal asignado:</strong><ul class="mb-0 mt-1">`;
                evento.personal.forEach(p => {
                    detallesHTML += `<li>${p.nombre_completo}${p.rut ? ` (RUT: ${p.rut})` : ''}</li>`;
                });
                detallesHTML += '</ul></div>';
                tieneDetalles = true;
            }
            
            // Información adicional que no esté en la descripción (solo campos realmente útiles)
            if (evento.datos_nuevos) {
                const camposTecnicos = [
                    'estado_ot_nombre', 'estado_equipo_nombre', 'estado_seccion_nombre',
                    'seccion_nombre', 'fecha_fin', 'personal_ids',
                    'estado_ot_id', 'estado_equipo_id', 'estado_seccion_id',
                    'seccion_id', 'equipo_id', 'equipo_nombre', 'folio',
                    'tipo_mantenimiento', 'estado_ot', 'estado_equipo'
                ];
                
                const keys = Object.keys(evento.datos_nuevos).filter(k => 
                    !camposTecnicos.includes(k) && 
                    !k.endsWith('_id') &&
                    evento.datos_nuevos[k] !== null && 
                    evento.datos_nuevos[k] !== undefined &&
                    evento.datos_nuevos[k] !== '' &&
                    // Excluir información que ya está en la descripción
                    !evento.descripcion.includes(k)
                );
                
                if (keys.length > 0) {
                    if (!tieneDetalles) {
                        detallesHTML = '<div class="small">';
                    }
                    detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información adicional:</strong><ul class="mb-0 mt-1">';
                    keys.forEach(key => {
                        const valor = evento.datos_nuevos[key];
                        const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                    });
                    detallesHTML += '</ul></div>';
                    tieneDetalles = true;
                }
            }
            
            if (tieneDetalles) {
                detallesHTML += '</div>';
            }
            
            infoHTML += `
                <tr id="${rowId}" class="${tieneDetalles ? 'historial-row-clickable' : ''}" ${tieneDetalles ? `onclick="toggleHistorialDetails('${detailsId}')" style="cursor: pointer;"` : ''}>
                    <td class="text-center" style="width: 5%;">
                        ${tieneDetalles ? `<i class="bi bi-info-circle text-muted" style="font-size: 0.9rem;" title="Click para ver más detalles"></i>` : ''}
                    </td>
                    <td>
                        <small class="text-muted">${evento.fecha_hora_formateada || evento.fecha_hora}</small>
                    </td>
                    <td>
                        <small><i class="bi bi-person me-1"></i>${obtenerNombreUsuario(evento)}</small>
                    </td>
                    <td>
                        <span class="badge ${badgeColor}">${evento.accion_display}</span>
                    </td>
                    <td>
                        <small>${evento.descripcion || '-'}</small>
                        ${tieneDetalles ? ' <span class="text-muted small">(click para más detalles)</span>' : ''}
                    </td>
                </tr>
                ${tieneDetalles ? `
                <tr id="${detailsId}" class="historial-details-row" style="display: none;">
                    <td colspan="5" class="bg-light">
                        <div class="p-3">
                            ${detallesHTML}
                        </div>
                    </td>
                </tr>
                ` : ''}
            `;
        });
        
        infoHTML += `
                    </tbody>
                </table>
            </div>
            <style>
                .historial-row-clickable {
                    transition: background-color 0.2s;
                }
                .historial-row-clickable:hover {
                    background-color: #f8f9fa !important;
                }
                .historial-row-clickable:hover td {
                    background-color: #f8f9fa !important;
                }
                .historial-details-row {
                    background-color: #f8f9fa;
                }
                .historial-details-row td {
                    border-top: none !important;
                }
            </style>
        `;
    } else {
        infoHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta orden de trabajo.
            </div>
        `;
    }
    
    modalBody.innerHTML = infoHTML;
}

// Función para obtener el nombre completo del usuario
function obtenerNombreUsuario(evento) {
    // Priorizar usuario_nombre (nombre completo), luego usuario (username), finalmente 'Sistema'
    if (evento.usuario_nombre && evento.usuario_nombre.trim() && evento.usuario_nombre !== evento.usuario) {
        return evento.usuario_nombre.trim();
    }
    if (evento.usuario && evento.usuario.trim() && evento.usuario !== 'Sistema') {
        return evento.usuario.trim();
    }
    return 'Sistema';
}

// Función para expandir/colapsar detalles del historial
function toggleHistorialDetails(detailsId) {
    const detailsRow = document.getElementById(detailsId);
    
    if (detailsRow) {
        if (detailsRow.style.display === 'none') {
            detailsRow.style.display = '';
        } else {
            detailsRow.style.display = 'none';
        }
    }
}

// Funciones helper para iconos y colores según acción
function getIconoAccion(accion) {
    const iconos = {
        'OT_CREADA': '<i class="bi bi-plus-circle-fill text-success fs-5"></i>',
        'OT_MODIFICADA': '<i class="bi bi-pencil-fill text-primary fs-5"></i>',
        'ESTADO_OT_CAMBIADO': '<i class="bi bi-arrow-repeat text-info fs-5"></i>',
        'ESTADO_EQUIPO_CAMBIADO': '<i class="bi bi-gear-fill text-warning fs-5"></i>',
        'ESTADO_SECCION_CAMBIADO': '<i class="bi bi-diagram-3-fill text-secondary fs-5"></i>',
        'FECHA_INICIO_CAMBIADA': '<i class="bi bi-calendar-event-fill text-primary fs-5"></i>',
        'FECHA_FIN_CAMBIADA': '<i class="bi bi-calendar-event-fill text-primary fs-5"></i>',
        'PERSONAL_ASIGNADO': '<i class="bi bi-person-plus-fill text-success fs-5"></i>',
        'PERSONAL_ELIMINADO': '<i class="bi bi-person-dash-fill text-danger fs-5"></i>',
        'OBSERVACION_AGREGADA': '<i class="bi bi-chat-left-text-fill text-info fs-5"></i>'
    };
    return iconos[accion] || '<i class="bi bi-info-circle-fill text-secondary fs-5"></i>';
}

function getBadgeColorAccion(accion) {
    const colores = {
        'OT_CREADA': 'bg-success',
        'OT_MODIFICADA': 'bg-primary',
        'ESTADO_OT_CAMBIADO': 'bg-info',
        'ESTADO_EQUIPO_CAMBIADO': 'bg-warning text-dark',
        'ESTADO_SECCION_CAMBIADO': 'bg-secondary',
        'FECHA_INICIO_CAMBIADA': 'bg-primary',
        'FECHA_FIN_CAMBIADA': 'bg-primary',
        'PERSONAL_ASIGNADO': 'bg-success',
        'PERSONAL_ELIMINADO': 'bg-danger',
        'OBSERVACION_AGREGADA': 'bg-info'
    };
    return colores[accion] || 'bg-secondary';
}

function getBorderColorAccion(index) {
    const colores = ['border-primary', 'border-secondary', 'border-info', 'border-warning', 'border-success'];
    return colores[index % colores.length];
}

function getBackgroundColorAccion(accion) {
    const colores = {
        'OT_CREADA': 'bg-light',
        'OT_MODIFICADA': '',
        'ESTADO_OT_CAMBIADO': 'bg-light bg-opacity-50',
        'ESTADO_EQUIPO_CAMBIADO': 'bg-light bg-opacity-50',
        'ESTADO_SECCION_CAMBIADO': 'bg-light bg-opacity-50',
        'FECHA_INICIO_CAMBIADA': '',
        'FECHA_FIN_CAMBIADA': '',
        'PERSONAL_ASIGNADO': 'bg-light',
        'PERSONAL_ELIMINADO': 'bg-light bg-opacity-50',
        'OBSERVACION_AGREGADA': 'bg-light'
    };
    return colores[accion] || '';
}

function getBorderLeftColorAccion(accion) {
    const colores = {
        'OT_CREADA': '#198754',
        'OT_MODIFICADA': '#0d6efd',
        'ESTADO_OT_CAMBIADO': '#0dcaf0',
        'ESTADO_EQUIPO_CAMBIADO': '#ffc107',
        'ESTADO_SECCION_CAMBIADO': '#6c757d',
        'FECHA_INICIO_CAMBIADA': '#0d6efd',
        'FECHA_FIN_CAMBIADA': '#0d6efd',
        'PERSONAL_ASIGNADO': '#198754',
        'PERSONAL_ELIMINADO': '#dc3545',
        'OBSERVACION_AGREGADA': '#0dcaf0'
    };
    return colores[accion] || '#6c757d';
}

// Función helper para formatear fechas en formato chileno
function formatearFechaChilena(fechaString) {
    if (!fechaString) return 'N/A';
    
    try {
        // Intentar parsear diferentes formatos de fecha
        let fecha;
        
        // Si incluye hora (formato: YYYY-MM-DD HH:MM:SS)
        if (fechaString.includes(' ')) {
            fecha = new Date(fechaString.replace(' ', 'T'));
        } else {
            // Solo fecha (formato: YYYY-MM-DD)
            fecha = new Date(fechaString + 'T00:00:00');
        }
        
        if (isNaN(fecha.getTime())) {
            return fechaString; // Si no se puede parsear, devolver original
        }
        
        // Formatear en formato chileno DD/MM/YYYY o DD/MM/YYYY HH:MM si tiene hora
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const año = fecha.getFullYear();
        
        if (fechaString.includes(' ')) {
            const horas = String(fecha.getHours()).padStart(2, '0');
            const minutos = String(fecha.getMinutes()).padStart(2, '0');
            return `${dia}/${mes}/${año} ${horas}:${minutos}`;
        } else {
            return `${dia}/${mes}/${año}`;
        }
    } catch (e) {
        return fechaString; // Si hay error, devolver original
    }
}

// Renderizar detalle de OT en modal
function renderizarDetalleOT(ot, container) {
    const secciones = ot.corresponde_pauta && ot.secciones_pauta.length > 0 
        ? ot.secciones_pauta 
        : ot.secciones_manuales;
    
    const seccionesHTML = secciones && secciones.length > 0 ? secciones.map(sec => `
        <div class="card mb-2 border">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0 fw-bold">${sec.seccion_nombre}</h6>
                    <span class="badge bg-${getColorEstadoOT(sec.estado_seccion)}" style="font-size: 0.75rem;">${sec.estado_seccion || 'Pendiente'}</span>
                </div>
                ${sec.tipos_reparacion && sec.tipos_reparacion.length > 0 
                    ? `<div class="mt-2">
                        <small class="text-muted d-block mb-1">Tipos de Reparación:</small>
                        <ul class="mb-0 ps-3" style="font-size: 0.875rem;">
                            ${sec.tipos_reparacion.map(tr => `<li>${tr}</li>`).join('')}
                        </ul>
                    </div>`
                    : '<small class="text-muted">Sin tipos de reparación</small>'
                }
            </div>
        </div>
    `).join('') : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay secciones registradas</div>';
    
    const personalHTML = ot.personal_asignado && ot.personal_asignado.length > 0
        ? ot.personal_asignado.map(p => `
            <div class="card mb-2 border">
                <div class="card-body p-2">
                    <div class="d-flex justify-content-between align-items-center" style="font-size: 0.875rem;">
                        <div>
                            <strong class="d-block" style="font-size: 0.875rem;">${p.nombre_completo}</strong>
                            <small class="text-muted" style="font-size: 0.8rem;">${p.rut}</small>
                        </div>
                        <span class="badge bg-primary" style="font-size: 0.75rem;">${p.cargo}</span>
                    </div>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>Sin personal asignado</div>';
    
    const historialObservacionesHTML = ot.historial_observaciones && ot.historial_observaciones.length > 0
        ? ot.historial_observaciones.map(obs => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary"><i class="bi bi-person-circle me-1"></i>${obs.usuario}</strong>
                        </div>
                        <small class="text-muted"><i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(obs.fecha)}</small>
                    </div>
                    <p class="mb-0">${obs.observacion}</p>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay observaciones registradas</div>';
    
    const historialCambiosHTML = ot.historial_cambios && ot.historial_cambios.length > 0
        ? ot.historial_cambios.map(cambio => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong class="d-block mb-1"><i class="bi bi-arrow-repeat me-1"></i>${cambio.accion}</strong>
                            <small class="text-muted d-block mb-2">${cambio.descripcion}</small>
                        </div>
                        <div class="text-end ms-3">
                            <small class="text-muted d-block"><i class="bi bi-person me-1"></i>${cambio.usuario}</small>
                            <small class="text-muted d-block"><i class="bi bi-clock me-1"></i>${formatearFechaChilena(cambio.fecha_hora)}</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay cambios registrados</div>';
    
    container.innerHTML = `
        <div class="row g-3">
            <div class="col-md-6">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-info-circle me-2 text-primary"></i>Información General</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-sm table-bordered mb-0">
                            <tbody>
                                <tr>
                                    <th style="width: 40%;" class="bg-light">Folio:</th>
                                    <td><strong class="text-primary">${ot.folio}</strong></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Equipo:</th>
                                    <td>${ot.equipo.nombreEquipo} <small class="text-muted">(${ot.equipo.codigoInterno})</small></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Tipo:</th>
                                    <td>${ot.equipo.tipoEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Marca:</th>
                                    <td>${ot.equipo.marcaEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Modelo:</th>
                                    <td>${ot.equipo.modeloEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Empresa:</th>
                                    <td>${ot.empresa.nomFantasia}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Tipo Mantenimiento:</th>
                                    <td><span class="badge bg-${getColorTipoMantenimiento(ot.tipo_mantenimiento)}">${ot.tipo_mantenimiento}</span></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Estado OT:</th>
                                    <td><span class="badge bg-${getColorEstadoOT(ot.estado_ot)}">${ot.estado_ot}</span></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Estado Equipo:</th>
                                    <td><span class="badge bg-${getColorEstadoEquipo(ot.estado_equipo)}">${ot.estado_equipo}</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-calendar-event me-2 text-primary"></i>Fechas y Mediciones</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-sm table-bordered mb-0">
                            <tbody>
                                <tr>
                                    <th style="width: 40%;" class="bg-light">Fecha Creación:</th>
                                    <td>${formatearFechaChilena(ot.fecha_creacion)}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Fecha Inicio:</th>
                                    <td>${ot.fecha_inicio ? formatearFechaChilena(ot.fecha_inicio) : 'Sin fecha'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Fecha Fin:</th>
                                    <td>${ot.fecha_fin ? formatearFechaChilena(ot.fecha_fin) : 'Sin fecha'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Horómetro:</th>
                                    <td>${ot.horometro || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Odómetro:</th>
                                    <td>${ot.odometro || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Horómetro Superestructura:</th>
                                    <td>${ot.horometro_superestructura || 'N/A'}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        ${ot.corresponde_pauta && ot.pauta_nombre ? `
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-clipboard-check me-2 text-primary"></i>Pauta de Mantenimiento</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-0"><strong>${ot.pauta_nombre}</strong></p>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-list-check me-2 text-primary"></i>Secciones</h6>
                    </div>
                    <div class="card-body">
                        ${seccionesHTML}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-people me-2 text-primary"></i>Personal Asignado</h6>
                    </div>
                    <div class="card-body">
                        ${personalHTML}
                    </div>
                </div>
            </div>
        </div>
        
        ${ot.observaciones ? `
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-journal-text me-2 text-primary"></i>Observación Inicial</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <strong class="text-primary">
                                    <i class="bi bi-file-text me-1"></i>Observación Inicial
                                </strong>
                            </div>
                            <small class="text-muted">
                                <i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(ot.fecha_creacion)}
                            </small>
                        </div>
                        <p class="mb-0">${ot.observaciones}</p>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
    `;
}

// Mostrar error
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);
    console.error(mensaje);
}
