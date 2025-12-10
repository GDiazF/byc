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

// Asegurar que permisos esté definido (por si acaso no se carga desde el template)
if (typeof permisos === 'undefined') {
    var permisos = {};
    console.warn('permisos no está definido, usando objeto vacío');
}

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

/**
 * Inicializa todos los event listeners de la página.
 * Configura listeners para búsqueda, filtros, ordenamiento, modales y botones.
 */
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
    
    // Inicializar modal de selección de personal para descarga
    const btnSeleccionarPersonal = document.getElementById('btnSeleccionarPersonal');
    if (btnSeleccionarPersonal) {
        btnSeleccionarPersonal.addEventListener('click', function() {
            const modalElement = document.getElementById('modalSeleccionarPersonal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                personalSeleccionado = [];
                actualizarVistaSeleccionados();
            }
        });
    }
    
    // Búsqueda en modal
    const buscarPersonalModal = document.getElementById('buscarPersonalModal');
    if (buscarPersonalModal) {
        buscarPersonalModal.addEventListener('input', function() {
            buscarPersonalEnModal(this.value);
        });
    }
    
    // Botón limpiar selección
    const btnLimpiarSeleccion = document.getElementById('btnLimpiarSeleccion');
    if (btnLimpiarSeleccion) {
        btnLimpiarSeleccion.addEventListener('click', function() {
            personalSeleccionado = [];
            actualizarVistaSeleccionados();
            const resultadosDiv = document.getElementById('resultadosBusquedaPersonal');
            if (resultadosDiv) {
                resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
            }
        });
    }
    
    // Botón descargar ZIP
    const btnDescargarZip = document.getElementById('btnDescargarZip');
    if (btnDescargarZip) {
        btnDescargarZip.addEventListener('click', function() {
            descargarDocumentacionZip();
        });
    }
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

/**
 * Renderiza la tabla de personal con filtros, ordenamiento y paginación aplicados.
 * 
 * Filtra el personal según la búsqueda y el filtro de empresa,
 * ordena según la columna seleccionada, y muestra solo los registros
 * de la página actual. También actualiza los contadores y la paginación.
 */
function renderizarTabla() {
    const tbody = document.getElementById('personalTableBody');
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    const filtroEmpresa = document.getElementById('filtroEmpresa').value;
    
    // Filtrar personal según búsqueda y filtro de empresa
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
    
    // Verificar permisos (usar permisos global si está disponible)
    const canView = permisos && (permisos.can_view_personal === true || permisos.can_view_personal === 'true');
    const canChange = permisos && (permisos.can_change_personal === true || permisos.can_change_personal === 'true');
    const canDesactivar = permisos && (permisos.can_desactivar_personal === true || permisos.can_desactivar_personal === 'true');
    const canActivar = permisos && (permisos.can_activar_personal === true || permisos.can_activar_personal === 'true');
    const canVerHistorial = permisos && (permisos.can_ver_historial_personal === true || permisos.can_ver_historial_personal === 'true');
    // Permiso para ver documentación (puede tener view_personal o permisos de documentación)
    const canViewDocumentation = permisos && (
        permisos.can_view_documentation === true || 
        permisos.can_view_documentation === 'true' ||
        permisos.can_view_personal === true || 
        permisos.can_view_personal === 'true' ||
        permisos.can_change_personal === true ||
        permisos.can_change_personal === 'true'
    );
    
    // Debug: verificar permisos de documentación
    if (personalPagina.length > 0) {
        console.log('Debug permisos documentación:', {
            can_view_documentation: permisos?.can_view_documentation,
            can_view_personal: permisos?.can_view_personal,
            can_change_personal: permisos?.can_change_personal,
            canViewDocumentation: canViewDocumentation
        });
    }
    
    // Renderizar filas
    tbody.innerHTML = personalPagina.map(p => {
        // Determinar si puede activar/desactivar según el estado actual
        const puedeToggle = p.activo ? canDesactivar : canActivar;
        
        return `
        <tr>
            <td>${p.rut}</td>
            <td>
                <span class="text-primary" style="cursor: pointer; text-decoration: underline;" 
                      onclick="mostrarInfoPersonal(${p.id})" 
                      title="Click para ver información completa">
                    ${p.nombre}
                </span>
            </td>
            <td>${p.cargo}</td>
            <td>${p.departamento}</td>
            <td>${p.empresa}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${canViewDocumentation ? `
                        <a href="/users/personal/${p.id}/documentation/" class="btn btn-sm btn-primary" title="Ver Documentación">
                            <i class="bi bi-folder"></i>
                        </a>
                    ` : `
                        <button type="button" class="btn btn-sm btn-primary" disabled title="No tiene permiso para ver documentación" onclick="event.preventDefault(); alert('No tiene permiso para ver documentación. Por favor, contacte al administrador si necesita acceso.'); return false;">
                            <i class="bi bi-folder"></i>
                        </button>
                    `}
                    ${canChange ? `
                        <a href="/users/personal/${p.id}/update/" class="btn btn-sm btn-secondary" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </a>
                    ` : `
                        <button type="button" class="btn btn-sm btn-secondary" disabled title="No tiene permiso para editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                    `}
                    ${canVerHistorial ? `
                        <button type="button" class="btn btn-sm btn-info" onclick="verHistorialPersonal(${p.id}, '${p.nombre.replace(/'/g, "\\'")}')" title="Ver Historial">
                            <i class="bi bi-clock-history"></i>
                        </button>
                    ` : `
                        <button type="button" class="btn btn-sm btn-info" disabled title="No tiene permiso para ver historial">
                            <i class="bi bi-clock-history"></i>
                        </button>
                    `}
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-switch d-flex justify-content-center">
                    <input class="form-check-input" type="checkbox" 
                           data-id="${p.id}"
                           ${p.activo ? 'checked' : ''}
                           ${puedeToggle ? '' : 'disabled'}
                           ${puedeToggle ? `onchange="toggleEstado(this)"` : ''}
                           ${!puedeToggle ? `title="No tiene permiso para ${p.activo ? 'desactivar' : 'activar'} personal"` : ''}>
                </div>
            </td>
        </tr>
        `;
    }).join('');
    
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

/**
 * Renderiza los controles de paginación.
 * 
 * @param {number} totalPaginas - Número total de páginas
 */
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

/**
 * Actualiza los iconos de ordenamiento en los encabezados de columna.
 * Muestra flecha arriba/abajo según la dirección del ordenamiento actual.
 */
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

/**
 * Limpia todos los filtros y restablece la búsqueda.
 * Reinicia la tabla a su estado inicial.
 */
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

/**
 * Maneja el cambio de estado activo/inactivo del personal.
 * 
 * Muestra un modal de confirmación antes de cambiar el estado.
 * Si el usuario confirma, envía una petición AJAX para actualizar el estado.
 * 
 * @param {HTMLInputElement} checkbox - Checkbox que disparó el evento
 */
function toggleEstado(checkbox) {
    // Verificar si el checkbox está deshabilitado
    if (checkbox.disabled) {
        const personalId = parseInt(checkbox.dataset.id);
        const persona = personal.find(p => p.id === personalId);
        const accion = persona && persona.activo ? 'desactivar' : 'activar';
        alert(`No tiene permiso para ${accion} personal. Por favor, contacte al administrador si necesita acceso.`);
        return;
    }
    
    // Verificar permisos antes de continuar
    const personalId = parseInt(checkbox.dataset.id);
    const persona = personal.find(p => p.id === personalId);
    if (persona) {
        const necesitaDesactivar = persona.activo;
        const tienePermiso = necesitaDesactivar ? 
            (permisos && permisos.can_desactivar_personal === true) : 
            (permisos && permisos.can_activar_personal === true);
        
        if (!tienePermiso) {
            const accion = necesitaDesactivar ? 'desactivar' : 'activar';
            alert(`No tiene permiso para ${accion} personal. Por favor, contacte al administrador si necesita acceso.`);
            checkbox.checked = !checkbox.checked; // Revertir el cambio
            return;
        }
    }
    
    currentToggle = checkbox;
    originalState = !checkbox.checked;
    changeConfirmed = false;
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
    
    // Revertir el cambio hasta que se confirme
    checkbox.checked = originalState;
}

/**
 * Confirma el cambio de estado del personal.
 * 
 * Envía una petición AJAX para cambiar el estado activo/inactivo
 * del personal seleccionado. Muestra mensajes de éxito o error.
 */
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
    .then(async response => {
        // Usar handleAjaxResponse para manejar errores automáticamente
        const data = await handleAjaxResponse(response);
        
        if (data.status === 'success') {
            changeConfirmed = true;
            
            // Cerrar modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
            if (confirmModal) {
                confirmModal.hide();
            }
            
            // Mostrar mensaje de éxito
            const accion = data.activo ? 'activado' : 'desactivado';
            if (typeof showNotification === 'function') {
                showNotification(`Personal ${accion} correctamente`, 'success');
            } else {
                // Fallback si showNotification no está disponible
                document.getElementById('successModalBody').innerHTML = `
                    <i class="bi bi-check-circle me-2"></i>Personal ${accion} correctamente
                `;
                const successModal = new bootstrap.Modal(document.getElementById('successModal'));
                successModal.show();
            }
            
            // Redirigir después de mostrar el mensaje
            setTimeout(() => {
                window.location.replace(window.location.pathname + '?updated=' + Date.now());
            }, 1500);
        } else {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
            if (confirmModal) {
                confirmModal.hide();
            }
            // El error ya fue mostrado por handleAjaxResponse
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
        if (confirmModal) {
            confirmModal.hide();
        }
        // El error ya fue mostrado por handleAjaxResponse, solo restaurar el estado
        currentToggle.checked = originalState;
    });
}

// ============================================================================
// MODAL DE INFORMACIÓN DEL PERSONAL
// ============================================================================

/**
 * Muestra un modal con toda la información personal y laboral del personal
 * @param {number} personalId - ID del personal
 */
/**
 * Muestra información completa del personal en un modal.
 * 
 * Carga los datos del personal mediante AJAX y los muestra
 * en un modal de Bootstrap con toda la información disponible.
 * 
 * @param {number} personalId - ID del personal a mostrar
 */
function mostrarInfoPersonal(personalId) {
    const modal = new bootstrap.Modal(document.getElementById('infoPersonalModal'));
    const modalBody = document.getElementById('infoPersonalModalBody');
    const modalTitle = document.getElementById('infoPersonalModalLabel');
    
    // Mostrar loading
    modalBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando información...</p>
        </div>
    `;
    
    // Mostrar modal
    modal.show();
    
    // Cargar datos del personal
    fetch(`/users/api/personal/${personalId}/info/`)
        .then(async response => {
            const data = await handleAjaxResponse(response);
            
            if (data.success) {
                const personal = data.data.personal;
                const laboral = data.data.laboral_actual;
                const historial = data.data.historial_laboral || [];
                
                // Construir HTML con pestañas
                let html = `
                    <!-- Nav tabs -->
                    <ul class="nav nav-tabs mb-3" id="infoPersonalTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="personal-tab" data-bs-toggle="tab" data-bs-target="#personal-pane" type="button" role="tab" aria-controls="personal-pane" aria-selected="true">
                                <i class="bi bi-person me-1"></i>Información Personal
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="laboral-tab" data-bs-toggle="tab" data-bs-target="#laboral-pane" type="button" role="tab" aria-controls="laboral-pane" aria-selected="false">
                                <i class="bi bi-briefcase me-1"></i>Información Laboral
                            </button>
                        </li>
                    </ul>
                    
                    <!-- Tab content -->
                    <div class="tab-content" id="infoPersonalTabContent">
                        <!-- Tab: Información Personal -->
                        <div class="tab-pane fade show active" id="personal-pane" role="tabpanel" aria-labelledby="personal-tab">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-primary mb-3">
                                                <i class="bi bi-person-badge me-2"></i>Datos Personales
                                            </h6>
                                            <table class="table table-sm table-borderless mb-0">
                                                <tbody>
                                                    <tr>
                                                        <td class="fw-bold text-muted" style="width: 45%;">RUT:</td>
                                                        <td><strong>${personal.rut}</strong></td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Nombre Completo:</td>
                                                        <td><strong>${personal.nombre_completo}</strong></td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Fecha de Nacimiento:</td>
                                                        <td>${personal.fecha_nacimiento}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Sexo:</td>
                                                        <td>${personal.sexo}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Estado Civil:</td>
                                                        <td>${personal.estado_civil}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Estado:</td>
                                                        <td>
                                                            <span class="badge ${personal.activo ? 'bg-success' : 'bg-danger'}">
                                                                ${personal.estado_texto}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-primary mb-3">
                                                <i class="bi bi-geo-alt me-2"></i>Contacto y Ubicación
                                            </h6>
                                            <table class="table table-sm table-borderless mb-0">
                                                <tbody>
                                                    <tr>
                                                        <td class="fw-bold text-muted" style="width: 45%;">Correo:</td>
                                                        <td>${personal.correo}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Dirección:</td>
                                                        <td>${personal.direccion}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Región:</td>
                                                        <td>${personal.region}</td>
                                                    </tr>
                                                    <tr>
                                                        <td class="fw-bold text-muted">Comuna:</td>
                                                        <td>${personal.comuna}</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tab: Información Laboral -->
                        <div class="tab-pane fade" id="laboral-pane" role="tabpanel" aria-labelledby="laboral-tab">
                `;
                
                if (laboral) {
                    html += `
                            <div class="row">
                                <div class="col-md-12 mb-3">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-primary mb-3">
                                                <i class="bi bi-briefcase me-2"></i>Información Laboral Actual
                                            </h6>
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <table class="table table-sm table-borderless mb-0">
                                                        <tbody>
                                                            <tr>
                                                                <td class="fw-bold text-muted" style="width: 45%;">Empresa:</td>
                                                                <td><strong>${laboral.empresa}</strong></td>
                                                            </tr>
                                                            <tr>
                                                                <td class="fw-bold text-muted">Departamento:</td>
                                                                <td>${laboral.departamento}</td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </div>
                                                <div class="col-md-6">
                                                    <table class="table table-sm table-borderless mb-0">
                                                        <tbody>
                                                            <tr>
                                                                <td class="fw-bold text-muted" style="width: 45%;">Cargo:</td>
                                                                <td><strong>${laboral.cargo}</strong></td>
                                                            </tr>
                                                            <tr>
                                                                <td class="fw-bold text-muted">Fecha de Contratación:</td>
                                                                <td>${laboral.fecha_contratacion}</td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                    `;
                } else {
                    html += `
                            <div class="alert alert-warning border-0 shadow-sm">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                No hay información laboral registrada.
                            </div>
                    `;
                }
                
                // Historial laboral (si hay más de un registro)
                if (historial.length > 1) {
                    html += `
                            <div class="row mt-3">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-primary mb-3">
                                                <i class="bi bi-clock-history me-2"></i>Historial Laboral
                                            </h6>
                                            <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                                                <table class="table table-sm table-hover mb-0">
                                                    <thead class="table-dark sticky-top">
                                                        <tr>
                                                            <th>Empresa</th>
                                                            <th>Departamento</th>
                                                            <th>Cargo</th>
                                                            <th>Fecha Contratación</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                    `;
                    
                    historial.forEach((hist, index) => {
                        html += `
                                                        <tr ${index === 0 ? 'class="table-success"' : ''}>
                                                            <td>${hist.empresa}</td>
                                                            <td>${hist.departamento}</td>
                                                            <td>${hist.cargo}</td>
                                                            <td>${hist.fecha_contratacion}</td>
                                                        </tr>
                        `;
                    });
                    
                    html += `
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                    `;
                }
                
                html += `
                        </div>
                    </div>
                `;
                
                modalBody.innerHTML = html;
                modalTitle.innerHTML = `<i class="bi bi-person-circle me-2"></i>${personal.nombre_completo}`;
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar la información: ${data.error || 'Error desconocido'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error al cargar la información del personal.
                </div>
            `;
        });
}

// ============================================================================
// UTILIDADES
// ============================================================================

/**
 * Obtiene el valor de una cookie por su nombre.
 * 
 * @param {string} name - Nombre de la cookie
 * @returns {string|null} Valor de la cookie o null si no existe
 */
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

// ============================================================================
// MODAL DE SELECCIÓN DE PERSONAL PARA DESCARGA
// ============================================================================

let personalSeleccionado = []; // Array de objetos {id, nombre, rut, cargo}

// Buscar personal en el modal
/**
 * Busca personal en el modal de selección para descarga ZIP.
 * 
 * Filtra el personal según el término de búsqueda y muestra
 * los resultados en el modal.
 * 
 * @param {string} termino - Término de búsqueda
 */
function buscarPersonalEnModal(termino) {
    const resultadosDiv = document.getElementById('resultadosBusquedaPersonal');
    
    if (!termino || termino.trim() === '') {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
        return;
    }
    
    const terminoLower = termino.toLowerCase();
    const resultados = personal.filter(p => {
        return p.nombre.toLowerCase().includes(terminoLower) ||
               p.rut.toLowerCase().includes(terminoLower) ||
               p.cargo.toLowerCase().includes(terminoLower) ||
               p.empresa.toLowerCase().includes(terminoLower);
    });
    
    if (resultados.length === 0) {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">No se encontraron resultados</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    resultados.forEach(p => {
        const yaSeleccionado = personalSeleccionado.some(ps => ps.id === p.id);
        html += `
            <div class="list-group-item list-group-item-action ${yaSeleccionado ? 'bg-light' : ''}" 
                 style="cursor: pointer;" 
                 data-personal-id="${p.id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${p.nombre}</h6>
                        <small class="text-muted">RUT: ${p.rut} | ${p.cargo} | ${p.empresa}</small>
                    </div>
                    ${yaSeleccionado 
                        ? '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Seleccionado</span>'
                        : '<button class="btn btn-sm btn-primary btn-agregar-personal" data-personal-id="' + p.id + '"><i class="bi bi-plus-circle me-1"></i>Agregar</button>'
                    }
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultadosDiv.innerHTML = html;
    
    // Agregar event listeners a los botones y items
    resultadosDiv.querySelectorAll('.btn-agregar-personal').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const personalId = parseInt(this.dataset.personalId);
            agregarPersonalSeleccionado(personalId);
        });
    });
    
    resultadosDiv.querySelectorAll('.list-group-item').forEach(item => {
        item.addEventListener('click', function() {
            const personalId = parseInt(this.dataset.personalId);
            if (!personalSeleccionado.some(ps => ps.id === personalId)) {
                agregarPersonalSeleccionado(personalId);
            }
        });
    });
}

// Agregar personal a la lista de seleccionados
/**
 * Agrega un personal a la lista de seleccionados para descarga ZIP.
 * 
 * @param {number} personalId - ID del personal a agregar
 */
function agregarPersonalSeleccionado(personalId) {
    const persona = personal.find(p => p.id === personalId);
    if (!persona) return;
    
    // Verificar si ya está seleccionado
    if (personalSeleccionado.some(ps => ps.id === personalId)) {
        return;
    }
    
    personalSeleccionado.push({
        id: persona.id,
        nombre: persona.nombre,
        rut: persona.rut,
        cargo: persona.cargo,
        empresa: persona.empresa
    });
    
    actualizarVistaSeleccionados();
    
    // Actualizar la vista de resultados para mostrar que está seleccionado
    const termino = document.getElementById('buscarPersonalModal').value;
    if (termino) {
        buscarPersonalEnModal(termino);
    }
}

// Remover personal de la lista de seleccionados
/**
 * Remueve un personal de la lista de seleccionados para descarga ZIP.
 * 
 * @param {number} personalId - ID del personal a remover
 */
function removerPersonalSeleccionado(personalId) {
    personalSeleccionado = personalSeleccionado.filter(ps => ps.id !== personalId);
    actualizarVistaSeleccionados();
    
    // Actualizar la vista de resultados
    const termino = document.getElementById('buscarPersonalModal').value;
    if (termino) {
        buscarPersonalEnModal(termino);
    }
}

// Actualizar la vista de personal seleccionado
/**
 * Actualiza la vista de personal seleccionado en el modal.
 * 
 * Muestra la lista de personal seleccionado y actualiza
 * el contador de seleccionados.
 */
function actualizarVistaSeleccionados() {
    const contador = document.getElementById('contadorSeleccionados');
    const vistaSeleccionados = document.getElementById('personalSeleccionado');
    const btnDescargarZip = document.getElementById('btnDescargarZip');
    
    if (!vistaSeleccionados) return; // Si el modal no está abierto, no hacer nada
    
    if (contador) {
        contador.textContent = personalSeleccionado.length;
    }
    
    if (btnDescargarZip) {
        btnDescargarZip.disabled = personalSeleccionado.length === 0;
    }
    
    if (personalSeleccionado.length === 0) {
        vistaSeleccionados.innerHTML = '<p class="text-muted text-center mb-0">No hay personal seleccionado</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    personalSeleccionado.forEach(p => {
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${p.nombre}</h6>
                        <small class="text-muted">RUT: ${p.rut} | ${p.cargo}</small>
                    </div>
                    <button class="btn btn-sm btn-danger btn-remover-personal" data-personal-id="${p.id}">
                        <i class="bi bi-x-circle me-1"></i>Quitar
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    vistaSeleccionados.innerHTML = html;
    
    // Agregar event listeners a los botones de quitar
    vistaSeleccionados.querySelectorAll('.btn-remover-personal').forEach(btn => {
        btn.addEventListener('click', function() {
            const personalId = parseInt(this.dataset.personalId);
            removerPersonalSeleccionado(personalId);
        });
    });
}

// Descargar documentación en ZIP
/**
 * Descarga la documentación de los personal seleccionados en un archivo ZIP.
 * 
 * Envía una petición POST con los IDs del personal seleccionado
 * y descarga el archivo ZIP generado por el servidor.
 */
function descargarDocumentacionZip() {
    if (personalSeleccionado.length === 0) {
        alert('Por favor seleccione al menos un personal');
        return;
    }
    
    const personalIds = personalSeleccionado.map(p => p.id);
    
    // Crear formulario para enviar POST
    const form = document.createElement('form');
    form.method = 'POST';
    // Usar la URL desde el template o la ruta correcta
    form.action = window.descargarDocumentacionZipUrl || '/users/personal/descargar-documentacion-zip/';
    
    // Agregar CSRF token
    const csrfToken = getCookie('csrftoken');
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    // Agregar IDs del personal
    personalIds.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'personal_ids';
        input.value = id;
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    // Cerrar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalSeleccionarPersonal'));
    if (modal) {
        modal.hide();
    }
    
    // Limpiar selección
    personalSeleccionado = [];
    actualizarVistaSeleccionados();
}