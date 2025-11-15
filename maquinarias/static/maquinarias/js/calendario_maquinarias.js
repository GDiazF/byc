// Variables globales para calendario de maquinarias
let equiposFiltrados = [];
let ordenesFiltradas = [];

// Función wrapper para inicializar calendario de operaciones con IDs correctos
function inicializarCalendarioOperaciones() {
    if (typeof generateCalendar !== 'function') {
        console.warn('generateCalendar no está disponible');
        return;
    }
    
    // Guardar referencias a los elementos del tab de operaciones
    const headerOperaciones = document.getElementById('calendarHeaderOperaciones');
    const bodyOperaciones = document.getElementById('calendarBodyOperaciones');
    
    if (!headerOperaciones || !bodyOperaciones) {
        console.warn('Elementos del calendario de operaciones no encontrados');
        return;
    }
    
    // Cambiar temporalmente los IDs para que el script del calendario funcione
    const originalHeaderId = headerOperaciones.id;
    const originalBodyId = bodyOperaciones.id;
    
    headerOperaciones.id = 'calendarHeader';
    bodyOperaciones.id = 'calendarBody';
    
    // Llamar a la función de generación del calendario
    try {
        generateCalendar();
        
        // Configurar filtros si la función existe
        if (typeof setupFilters === 'function') {
            setupFilters();
        }
        
        // Limpiar y generar leyenda de estados si la función existe
        if (typeof generateStatusLegend === 'function') {
            // Limpiar la leyenda antes de regenerarla para evitar duplicados
            const legendContainer = document.getElementById('statusLegend');
            if (legendContainer) {
                // Guardar solo el texto base "Estados:"
                legendContainer.innerHTML = '<small class="me-2 fw-bold">Estados:</small>';
            }
            generateStatusLegend();
        }
    } catch (error) {
        console.error('Error al generar calendario de operaciones:', error);
    }
    
    // Restaurar los IDs originales
    headerOperaciones.id = originalHeaderId;
    bodyOperaciones.id = originalBodyId;
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar calendario de maquinarias directamente
    inicializarCalendarioMaquinarias();
    
    // Event listeners para filtros de maquinarias
    const searchInputMaquinarias = document.getElementById('searchInputMaquinarias');
    const empresaFilterMaquinarias = document.getElementById('empresaFilterMaquinarias');
    const estadoFilterMaquinarias = document.getElementById('estadoFilterMaquinarias');
    
    if (searchInputMaquinarias) {
        searchInputMaquinarias.addEventListener('input', aplicarFiltrosMaquinarias);
    }
    if (empresaFilterMaquinarias) {
        empresaFilterMaquinarias.addEventListener('change', aplicarFiltrosMaquinarias);
    }
    if (estadoFilterMaquinarias) {
        estadoFilterMaquinarias.addEventListener('change', aplicarFiltrosMaquinarias);
    }
    
    // Cargar estados OT para el filtro
    cargarEstadosOT();
});

// Cargar estados OT para el filtro
function cargarEstadosOT() {
    const estadoFilter = document.getElementById('estadoFilterMaquinarias');
    if (!estadoFilter) return;
    
    // Obtener estados únicos de las órdenes de trabajo
    const estados = new Set();
    window.ordenesTrabajo.forEach(ot => {
        if (ot.estado_ot) {
            estados.add(ot.estado_ot);
        }
    });
    
    // Agregar opciones al select
    estados.forEach(estado => {
        const option = document.createElement('option');
        option.value = estado;
        option.textContent = estado;
        estadoFilter.appendChild(option);
    });
}

// Inicializar calendario de maquinarias
function inicializarCalendarioMaquinarias() {
    equiposFiltrados = [...window.equipos];
    ordenesFiltradas = [...window.ordenesTrabajo];
    generarCalendarioMaquinarias();
}

// Generar calendario de maquinarias
function generarCalendarioMaquinarias() {
    const year = window.currentYear;
    const month = window.currentMonth - 1; // JavaScript usa 0-11 para meses
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    
    const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    
    // Generar encabezado (días)
    const headerRow = document.getElementById('calendarHeaderMaquinarias');
    if (!headerRow) return;
    
    let headerHTML = '<th class="sticky-col">Equipo</th>';
    
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dayOfWeek = date.getDay();
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
        const isToday = date.toDateString() === today.toDateString();
        
        let classes = [];
        if (isWeekend) classes.push('weekend');
        if (isToday) classes.push('today');
        
        headerHTML += `<th class="${classes.join(' ')}" title="${dayNames[dayOfWeek]} ${day}">
            <div>${day}</div>
            <small style="font-size: 0.7rem;">${dayNames[dayOfWeek]}</small>
        </th>`;
    }
    
    headerRow.innerHTML = headerHTML;
    
    // Generar filas (equipos)
    const tbody = document.getElementById('calendarBodyMaquinarias');
    if (!tbody) return;
    
    let bodyHTML = '';
    
    equiposFiltrados.forEach(equipo => {
        bodyHTML += '<tr>';
        
        // Columna de nombre del equipo (sticky) con click para mostrar info
        bodyHTML += `<td class="sticky-col">
            <div class="equipo-name-container">
                <div class="equipo-info" onclick="mostrarDetalleEquipo(${equipo.equipo_id})" 
                     style="cursor: pointer;" 
                     title="Click para ver información del equipo">
                    <div style="font-size: 0.75rem; font-weight: 600;">${equipo.nombreEquipo}</div>
                    <small style="color: #6c757d; font-size: 0.65rem;">${equipo.empresa}</small>
                </div>
            </div>
        </td>`;
        
        // Celdas de días con estados calculados
        for (let day = 1; day <= daysInMonth; day++) {
            // Obtener estado calculado del backend
            let estado = null;
            if (window.estadosCalculados && 
                window.estadosCalculados[equipo.equipo_id] && 
                window.estadosCalculados[equipo.equipo_id][day]) {
                const estadosDelDia = window.estadosCalculados[equipo.equipo_id][day];
                if (estadosDelDia && estadosDelDia.length > 0) {
                    estado = estadosDelDia[0]; // Tomar el primer estado (mayor prioridad)
                }
            }
            
            // Buscar OT para mostrar información adicional al hacer clic
            const fechaActual = new Date(year, month, day);
            const fechaISO = fechaActual.toISOString().split('T')[0];
            const otsDelDia = ordenesFiltradas.filter(ot => {
                if (ot.equipo_id !== equipo.equipo_id) return false;
                if (ot.fecha_inicio && ot.fecha_fin) {
                    return fechaISO >= ot.fecha_inicio.split('T')[0] && fechaISO <= ot.fecha_fin.split('T')[0];
                } else if (ot.fecha_inicio) {
                    return fechaISO === ot.fecha_inicio.split('T')[0];
                } else if (ot.fecha_fin) {
                    return fechaISO === ot.fecha_fin.split('T')[0];
                }
                return false;
            });
            
            if (estado) {
                // Hay estado calculado
                const otId = otsDelDia.length > 0 ? otsDelDia[0].ot_id : null;
                const onclickAttr = otId ? `onclick="mostrarDetalleOT(${otId})"` : '';
                const cursorStyle = otId ? 'cursor: pointer;' : '';
                
                bodyHTML += `<td ${onclickAttr}
                                style="background-color: ${estado.background_color}; color: ${estado.color}; ${cursorStyle}"
                                title="${estado.nombre}${otsDelDia.length > 0 ? ' - OT: ' + otsDelDia[0].folio : ''}">
                    <div class="estado-cell">
                        <div style="font-size: 0.65rem; font-weight: 600;">${estado.nombre_corto}</div>
                    </div>
                </td>`;
            } else {
                // Sin estado - mostrar estado predeterminado si existe
                const estadoPred = window.estadoPredeterminado;
                if (estadoPred) {
                    bodyHTML += `<td style="background-color: ${estadoPred.background_color}; color: ${estadoPred.color};"
                                    title="${estadoPred.nombre}">
                        <div class="estado-cell">${estadoPred.nombre_corto}</div>
                    </td>`;
                } else {
                    bodyHTML += `<td class="empty-cell"></td>`;
                }
            }
        }
        
        bodyHTML += '</tr>';
    });
    
    tbody.innerHTML = bodyHTML;
}

// Esta función ya no se usa, los colores vienen de los estados calculados

// Aplicar filtros al calendario de maquinarias
function aplicarFiltrosMaquinarias() {
    const search = document.getElementById('searchInputMaquinarias')?.value || '';
    const empresa = document.getElementById('empresaFilterMaquinarias')?.value || '';
    const estado = document.getElementById('estadoFilterMaquinarias')?.value || '';
    
    // Construir URL con filtros y recargar página
    const url = new URL(window.location.href);
    
    // Mantener parámetros de fecha y paginación
    const year = url.searchParams.get('year') || window.currentYear;
    const month = url.searchParams.get('month') || window.currentMonth;
    const page = url.searchParams.get('page') || '1';
    const pageSize = url.searchParams.get('page_size') || window.pageSize || '25';
    
    // Actualizar parámetros
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    url.searchParams.set('page', '1'); // Resetear a página 1 al filtrar
    url.searchParams.set('page_size', pageSize);
    
    // Agregar filtros
    if (search) {
        url.searchParams.set('search', search);
    } else {
        url.searchParams.delete('search');
    }
    
    if (empresa) {
        url.searchParams.set('empresa', empresa);
    } else {
        url.searchParams.delete('empresa');
    }
    
    if (estado) {
        url.searchParams.set('estado', estado);
    } else {
        url.searchParams.delete('estado');
    }
    
    // Recargar página con filtros
    window.location.href = url.toString();
}

// Limpiar filtros de maquinarias
function clearFiltersMaquinarias() {
    // Construir URL sin filtros
    const url = new URL(window.location.href);
    
    // Mantener solo fecha y paginación
    const year = url.searchParams.get('year') || window.currentYear;
    const month = url.searchParams.get('month') || window.currentMonth;
    const pageSize = url.searchParams.get('page_size') || window.pageSize || '25';
    
    // Limpiar todos los parámetros y reconstruir URL
    url.search = '';
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    url.searchParams.set('page', '1');
    url.searchParams.set('page_size', pageSize);
    
    window.location.href = url.toString();
}

// Cambiar tamaño de página para maquinarias
function cambiarTamanioPaginaMaquinarias(newSize) {
    const url = new URL(window.location.href);
    
    // Mantener parámetros actuales
    const year = url.searchParams.get('year') || window.currentYear;
    const month = url.searchParams.get('month') || window.currentMonth;
    const search = url.searchParams.get('search') || '';
    const empresa = url.searchParams.get('empresa') || '';
    const estado = url.searchParams.get('estado') || '';
    
    // Actualizar tamaño de página y resetear a página 1
    url.search = '';
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    url.searchParams.set('page', '1');
    url.searchParams.set('page_size', newSize);
    
    if (search) url.searchParams.set('search', search);
    if (empresa) url.searchParams.set('empresa', empresa);
    if (estado) url.searchParams.set('estado', estado);
    
    window.location.href = url.toString();
}

// Mostrar detalle de Equipo
function mostrarDetalleEquipo(equipoId) {
    const equipo = window.equipos.find(e => e.equipo_id === equipoId);
    if (!equipo) return;
    
    const modalBody = document.getElementById('equipoModalBody');
    if (!modalBody) return;
    
    // Crear estructura con tabs
    modalBody.innerHTML = `
        <!-- Nav tabs -->
        <ul class="nav nav-tabs mb-3" id="equipoTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="info-tab" data-bs-toggle="tab" data-bs-target="#info-pane" type="button" role="tab" aria-controls="info-pane" aria-selected="true">
                    <i class="bi bi-info-circle me-1"></i>Información
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="documentacion-tab" data-bs-toggle="tab" data-bs-target="#documentacion-pane" type="button" role="tab" aria-controls="documentacion-pane" aria-selected="false" data-equipo-id="${equipoId}">
                    <i class="bi bi-folder me-1"></i>Documentación
                </button>
            </li>
        </ul>
        
        <!-- Tab panes -->
        <div class="tab-content" id="equipoTabContent">
            <!-- Tab: Información -->
            <div class="tab-pane fade show active" id="info-pane" role="tabpanel" aria-labelledby="info-tab">
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-info-circle me-2 text-primary"></i>Información General</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Nombre:</th>
                                            <td><strong>${equipo.nombreEquipo}</strong></td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Código Interno:</th>
                                            <td>${equipo.codigoInterno}</td>
                                        </tr>
                                        ${equipo.patente ? `
                                        <tr>
                                            <th class="bg-light">Patente:</th>
                                            <td>${equipo.patente}</td>
                                        </tr>
                                        ` : ''}
                                        <tr>
                                            <th class="bg-light">Empresa:</th>
                                            <td>${equipo.empresa}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Tipo:</th>
                                            <td>${equipo.tipoEquipo || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Marca:</th>
                                            <td>${equipo.marcaEquipo || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Modelo:</th>
                                            <td>${equipo.modeloEquipo || 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-speedometer2 me-2 text-success"></i>Horómetros y Odómetro</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Horómetro:</th>
                                            <td>${equipo.horometro ? equipo.horometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Odómetro:</th>
                                            <td>${equipo.odometro ? equipo.odometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Horómetro Superestructura:</th>
                                            <td>${equipo.horometroSuperEstructural ? equipo.horometroSuperEstructural.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tab: Documentación -->
            <div class="tab-pane fade" id="documentacion-pane" role="tabpanel" aria-labelledby="documentacion-tab">
                <div id="documentosContainer">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando documentación...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('equipoModal'));
    modal.show();
    
    // Agregar listener para cuando se active el tab de documentación
    const documentacionTab = document.getElementById('documentacion-tab');
    if (documentacionTab) {
        documentacionTab.addEventListener('shown.bs.tab', function (e) {
            const equipoId = e.target.getAttribute('data-equipo-id');
            if (equipoId) {
                cargarDocumentosEquipo(parseInt(equipoId));
            }
        });
    }
}

// Cargar documentos del equipo
async function cargarDocumentosEquipo(equipoId) {
    const container = document.getElementById('documentosContainer');
    if (!container) return;
    
    try {
        const response = await fetch(`/maquinarias/api/equipos/${equipoId}/documentos/`);
        const data = await response.json();
        
        if (data.success && data.documentos) {
            renderizarDocumentosEquipo(data.documentos, container);
        } else {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay documentación disponible para este equipo.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error al cargar documentos:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error al cargar la documentación. Por favor, intente nuevamente.
            </div>
        `;
    }
}

// Renderizar documentos del equipo
function renderizarDocumentosEquipo(documentos, container) {
    if (!documentos || documentos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay documentación disponible para este equipo.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-sm table-bordered table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Tipo de Documento</th>
                        <th>Archivo</th>
                        <th>Fecha Subida</th>
                        <th>Fecha Vencimiento</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    documentos.forEach(doc => {
        const fechaVencimiento = doc.fecha_vencimiento 
            ? new Date(doc.fecha_vencimiento).toLocaleDateString('es-CL')
            : 'N/A';
        const fechaSubida = new Date(doc.fecha_subida).toLocaleDateString('es-CL');
        
        let badgeEstado = '';
        if (doc.estado === 'vencido') {
            badgeEstado = '<span class="badge bg-danger">Vencido</span>';
        } else if (doc.estado === 'por_vencer') {
            badgeEstado = `<span class="badge bg-warning">Por vencer (${doc.dias_restantes} días)</span>`;
        } else {
            badgeEstado = '<span class="badge bg-success text-white">Vigente</span>';
        }
        
        const archivoLink = doc.archivo_url 
            ? `<a href="${doc.archivo_url}" target="_blank" class="btn btn-sm btn-primary" title="${doc.archivo_nombre || 'Ver archivo'}">
                 <i class="bi bi-eye"></i>
               </a>`
            : 'N/A';
        
        html += `
            <tr>
                <td><strong>${doc.tipo_documento_nombre}</strong></td>
                <td>${archivoLink}</td>
                <td>${fechaSubida}</td>
                <td>${fechaVencimiento}</td>
                <td>${badgeEstado}</td>
            </tr>
        `;
        
        if (doc.observaciones) {
            html += `
                <tr>
                    <td colspan="5" class="small text-muted">
                        <strong>Observaciones:</strong> ${doc.observaciones}
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Mostrar detalle de OT
function mostrarDetalleOT(otId) {
    const ot = window.ordenesTrabajo.find(o => o.ot_id === otId);
    if (!ot) return;
    
    const modalBody = document.getElementById('otModalBody');
    if (!modalBody) return;
    
    const fechaInicio = ot.fecha_inicio ? new Date(ot.fecha_inicio).toLocaleDateString('es-CL') : 'No definida';
    const fechaFin = ot.fecha_fin ? new Date(ot.fecha_fin).toLocaleDateString('es-CL') : 'No definida';
    const fechaCreacion = new Date(ot.fecha_creacion).toLocaleDateString('es-CL');
    
    const personalHTML = ot.personal_asignado && ot.personal_asignado.length > 0
        ? ot.personal_asignado.map(p => `<li>${p.nombre}</li>`).join('')
        : '<li class="text-muted">Sin personal asignado</li>';
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <p><strong>Folio:</strong> ${ot.folio}</p>
                <p><strong>Equipo:</strong> ${ot.equipo_nombre}</p>
                <p><strong>Empresa:</strong> ${ot.empresa}</p>
                <p><strong>Tipo de Mantenimiento:</strong> ${ot.tipo_mantenimiento || 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Estado OT:</strong> <span class="badge bg-secondary">${ot.estado_ot || 'N/A'}</span></p>
                <p><strong>Estado Equipo:</strong> <span class="badge bg-info">${ot.estado_equipo || 'N/A'}</span></p>
                <p><strong>Fecha de Creación:</strong> ${fechaCreacion}</p>
                <p><strong>Fecha de Inicio:</strong> ${fechaInicio}</p>
                <p><strong>Fecha de Fin:</strong> ${fechaFin}</p>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <strong>Personal Asignado:</strong>
                <ul>
                    ${personalHTML}
                </ul>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12 text-end">
                <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/editar/" class="btn btn-primary btn-sm">
                    <i class="bi bi-pencil me-1"></i>Ver Detalle
                </a>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('otModal'));
    modal.show();
}

// Navegación del calendario actualizada para mantener filtros y paginación
function navigateCalendar(type, direction) {
    let newYear = window.currentYear;
    let newMonth = window.currentMonth;
    
    if (type === 'month') {
        newMonth += direction;
        if (newMonth < 1) {
            newMonth = 12;
            newYear -= 1;
        } else if (newMonth > 12) {
            newMonth = 1;
            newYear += 1;
        }
    } else if (type === 'year') {
        newYear += direction;
    }
    
    // Construir URL con parámetros actuales (mantener filtros y paginación)
    const url = new URL(window.location.href);
    url.searchParams.set('year', newYear);
    url.searchParams.set('month', newMonth);
    url.searchParams.set('page', '1'); // Resetear a página 1 al cambiar mes/año
    
    window.location.href = url.toString();
}

// Ir a hoy (mantener filtros y paginación)
function goToToday() {
    const today = new Date();
    const url = new URL(window.location.href);
    url.searchParams.set('year', today.getFullYear());
    url.searchParams.set('month', today.getMonth() + 1);
    url.searchParams.set('page', '1'); // Resetear a página 1
    
    window.location.href = url.toString();
}

