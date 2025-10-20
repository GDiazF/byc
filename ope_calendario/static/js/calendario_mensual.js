// Calendario de Planificación - JavaScript

// Obtener datos inyectados desde el template
const calendarioData = window.calendarioData;
const currentYear = window.currentYear;
const currentMonth = window.currentMonth;
const currentMonthName = window.currentMonthName;
const filtros = window.filtros;
const mesAnterior = window.mesAnterior;
const mesSiguiente = window.mesSiguiente;

// Nombres de meses y días en español
const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
 const dayNames = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];

// Variables globales
let currentDate = new Date(currentYear, currentMonth - 1, 1);
let filteredPersonal = [];

// Función para formatear fechas al formato chileno (DD-MM-YYYY)
function formatFechaChilena(fechaISO) {
    if (!fechaISO) return 'Sin fecha';
    const [year, month, day] = fechaISO.split('-');
    return `${day}-${month}-${year}`;
}

// Funciones helper para modales
function showAlert(message, type = 'info') {
    const modal = new bootstrap.Modal(document.getElementById('alertModal'));
    const header = document.getElementById('alertModalHeader');
    const title = document.getElementById('alertModalTitle');
    const body = document.getElementById('alertModalBody');
    
    // Configurar colores según el tipo
    if (type === 'success') {
        header.className = 'modal-header bg-success text-white';
        title.textContent = 'Éxito';
    } else if (type === 'error') {
        header.className = 'modal-header bg-danger text-white';
        title.textContent = 'Error';
    } else {
        header.className = 'modal-header bg-dark text-white';
        title.textContent = 'Información';
    }
    
    body.textContent = message;
    modal.show();
}

function showConfirm(message, title = 'Confirmar') {
    return new Promise((resolve) => {
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const titleEl = document.getElementById('confirmModalTitle');
        const bodyEl = document.getElementById('confirmModalBody');
        const btnConfirm = document.getElementById('confirmModalBtn');
        
        titleEl.textContent = title;
        bodyEl.textContent = message;
        
        // Remover event listeners anteriores
        const newBtn = btnConfirm.cloneNode(true);
        btnConfirm.parentNode.replaceChild(newBtn, btnConfirm);
        
        // Agregar nuevo event listener
        newBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });
        
        // Si se cierra sin confirmar
        document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
            resolve(false);
        }, { once: true });
        
        modal.show();
    });
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('📅 Inicializando calendario...');
    console.log('Datos recibidos:', calendarioData);
    
    // Generar leyenda de estados
    generateStatusLegend();
    
    // Generar calendario
    generateCalendar();
    
    // Configurar filtros
    setupFilters();
    
    // Llenar opciones de modales
    populateFaenaOptions();
    populateTurnoOptions();
    
    // Configurar eventos de modales
    setupModalEvents();
    
    console.log('✅ Calendario inicializado');
});

// Generar leyenda de estados
function generateStatusLegend() {
    const legendContainer = document.getElementById('statusLegend');
    const estados = calendarioData.todos_estados_disponibles || [];
    
    let html = '<small class="me-2 fw-bold">Estados:</small>';
    
    estados.forEach(estado => {
        html += `
            <div class="status-legend-item">
                <div class="status-legend-color" style="background-color: ${estado.background_color}; color: ${estado.color}; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 600;">
                    ${estado.nombre_corto}
                 </div>
                <small>${estado.nombre}</small>
             </div>
         `;
    });
    
    legendContainer.innerHTML = html;
}

// Generar calendario
function generateCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    
    // Generar encabezado (días)
    const headerRow = document.getElementById('calendarHeader');
    let headerHTML = '<th class="sticky-col">Personal</th>';
    
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
    
    // Generar filas (personal)
    const tbody = document.getElementById('calendarBody');
    filteredPersonal = calendarioData.personal || [];
    
    let bodyHTML = '';
    
    filteredPersonal.forEach(persona => {
        bodyHTML += '<tr>';
        
        // Columna de nombre (sticky) con botones de acción
        const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
        const cargo = persona.infolaboral_set?.[0]?.cargo_id?.cargo || 'Sin cargo';
        
        bodyHTML += `<td class="sticky-col">
            <div class="personal-name-container">
                <div class="personal-info" onclick="showPersonalInfo(${persona.personal_id})" title="${nombreCompleto}\n${cargo}">
                    <div style="font-size: 0.75rem;">${nombreCompleto}</div>
                    <small style="color: #fd7e14; font-style: italic; font-size: 0.65rem;">${cargo}</small>
                </div>
                <div class="personal-actions">
                    <button class="btn-action btn-assign" onclick="event.stopPropagation(); openFaenaModal(${persona.personal_id})" title="Nueva asignación">
                        <i class="bi bi-plus-circle"></i>
                    </button>
                    <button class="btn-action btn-edit" onclick="event.stopPropagation(); showAsignaciones(${persona.personal_id})" title="Editar asignaciones">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
            </div>
        </td>`;
        
        // Celdas de días
        for (let day = 1; day <= daysInMonth; day++) {
            const estados = calendarioData.estados[persona.personal_id]?.[day];
            
            if (estados) {
                if (estados.multiple) {
         // Múltiples estados
                    const primerEstado = estados.estados[0];
                    bodyHTML += `<td onclick="showEstadoInfo(${persona.personal_id}, ${day})" 
                                    style="background-color: ${primerEstado.background_color}; color: ${primerEstado.color};"
                                    title="Múltiples estados">
                        <div class="estado-cell">M</div>
                    </td>`;
                } else {
         // Estado único
                    bodyHTML += `<td onclick="showEstadoInfo(${persona.personal_id}, ${day})" 
                                    style="background-color: ${estados.background_color}; color: ${estados.color};"
                                    title="${estados.nombre}">
                        <div class="estado-cell">${estados.nombre_corto}</div>
                    </td>`;
         }
     } else {
                // Sin estado
                bodyHTML += `<td class="empty-cell" onclick="showEstadoInfo(${persona.personal_id}, ${day})"></td>`;
            }
        }
        
        bodyHTML += '</tr>';
    });
    
    tbody.innerHTML = bodyHTML;
}

// Mostrar información de estado
function showEstadoInfo(personalId, day) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    const cargo = persona.infolaboral_set?.[0]?.cargo_id?.cargo || 'Sin cargo';
    const fecha = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const estados = calendarioData.estados[personalId]?.[day];
    
    // Buscar faena activa
    let faenaActual = 'Sin asignar';
    if (persona.asignaciones_faena && persona.asignaciones_faena.length > 0) {
        const asignacion = persona.asignaciones_faena[0];
        faenaActual = asignacion.faena?.nombre || 'Sin asignar';
    }
    
    // Llenar modal
    document.getElementById('modalPersonal').textContent = nombreCompleto;
    document.getElementById('modalFecha').textContent = fecha.toLocaleDateString('es-ES', { 
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    });
    
    if (estados) {
        if (estados.multiple) {
            const nombresEstados = estados.estados.map(e => e.nombre).join(', ');
            document.getElementById('modalEstado').textContent = nombresEstados;
                 } else {
            document.getElementById('modalEstado').textContent = estados.nombre;
             }
         } else {
        document.getElementById('modalEstado').textContent = 'Sin estado';
    }
    
    document.getElementById('modalFaena').textContent = faenaActual;
     document.getElementById('modalCargo').textContent = cargo;
     
     // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('estadoModal'));
    modal.show();
}

// Mostrar información personal
function showPersonalInfo(personalId) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    const cargo = persona.infolaboral_set?.[0]?.cargo_id?.cargo || 'Sin cargo';
    const rut = `${persona.rut}-${persona.dvrut}`;
    
    let html = `
        <div class="mb-2"><strong>Nombre:</strong> ${nombreCompleto}</div>
        <div class="mb-2"><strong>RUT:</strong> ${rut}</div>
        <div class="mb-2"><strong>Cargo:</strong> ${cargo}</div>
        <div class="mb-2"><strong>Correo:</strong> ${persona.correo || 'No disponible'}</div>
        <div class="mb-2"><strong>Dirección:</strong> ${persona.direccion || 'No disponible'}</div>
    `;
    
    if (persona.asignaciones_faena && persona.asignaciones_faena.length > 0) {
        html += '<hr><h6>Asignaciones Activas:</h6>';
        persona.asignaciones_faena.forEach(asig => {
            const fechaInicio = formatFechaChilena(asig.fecha_inicio);
            const fechaFin = asig.fecha_fin ? formatFechaChilena(asig.fecha_fin) : 'Sin fecha fin';
            html += `
                <div class="alert alert-info mb-2 p-2">
                    <strong>${asig.faena.nombre}</strong><br>
                    <small>
                        Desde: ${fechaInicio}<br>
                        Hasta: ${fechaFin}
                    </small>
                </div>
            `;
        });
    }
    
    html += `
        <hr>
        <button class="btn btn-success btn-sm w-100" onclick="openFaenaModal(${personalId})">
            <i class="bi bi-plus-circle me-1"></i>Gestionar Asignaciones
        </button>
    `;
    
    document.getElementById('personalModalBody').innerHTML = html;
    
    const modal = new bootstrap.Modal(document.getElementById('personalModal'));
    modal.show();
}

// Configurar filtros
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const faenaFilter = document.getElementById('faenaFilter');
    const cargoFilter = document.getElementById('cargoFilter');
    
    searchInput.addEventListener('input', applyFilters);
    faenaFilter.addEventListener('change', applyFilters);
    cargoFilter.addEventListener('change', applyFilters);
}

// Aplicar filtros
function applyFilters() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const faenaValue = document.getElementById('faenaFilter').value;
    const cargoValue = document.getElementById('cargoFilter').value;
    
    const rows = document.querySelectorAll('#calendarBody tr');
    
    calendarioData.personal.forEach((persona, index) => {
        const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.toLowerCase();
        const rut = `${persona.rut}${persona.dvrut}`.toLowerCase();
        const cargo = persona.infolaboral_set?.[0]?.cargo_id?.cargo || 'Sin cargo';
        
        let faena = 'Sin asignar';
        if (persona.asignaciones_faena && persona.asignaciones_faena.length > 0) {
            faena = persona.asignaciones_faena[0].faena?.nombre || 'Sin asignar';
        }
        
        // Filtrar por búsqueda
        const matchesSearch = searchValue === '' || 
                             nombreCompleto.includes(searchValue) || 
                             rut.includes(searchValue);
        
        // Filtrar por faena
        const matchesFaena = faenaValue === '' || faena === faenaValue;
        
        // Filtrar por cargo
        const matchesCargo = cargoValue === '' || cargo === cargoValue;
        
        // Mostrar/ocultar fila
        if (matchesSearch && matchesFaena && matchesCargo) {
            rows[index].classList.remove('filtered-out');
         } else {
            rows[index].classList.add('filtered-out');
        }
    });
}

// Limpiar filtros
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('faenaFilter').value = '';
    document.getElementById('cargoFilter').value = '';
    applyFilters();
}

// Navegación del calendario
function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    navigateToDate();
}

function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    navigateToDate();
}

function previousYear() {
    currentDate.setFullYear(currentDate.getFullYear() - 1);
    navigateToDate();
}

function nextYear() {
    currentDate.setFullYear(currentDate.getFullYear() + 1);
    navigateToDate();
}

function goToToday() {
    const today = new Date();
    currentDate = new Date(today.getFullYear(), today.getMonth(), 1);
    navigateToDate();
}

function navigateToDate() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    window.location.href = `?year=${year}&month=${month}`;
}

// Llenar opciones de faenas
function populateFaenaOptions() {
    const select = document.getElementById('faenaSelect');
    const faenas = calendarioData.faenas || [];
    
    faenas.forEach(faena => {
                     const option = document.createElement('option');
                     option.value = faena.id;
                     option.textContent = faena.nombre;
        select.appendChild(option);
    });
}

// Llenar opciones de turnos
function populateTurnoOptions() {
    const select = document.getElementById('turnoSelect');
    const turnos = calendarioData.turnos || [];
    
    turnos.forEach(turno => {
                 const option = document.createElement('option');
                 option.value = turno.id;
                 option.textContent = turno.nombre;
        select.appendChild(option);
    });
    
    // Al cambiar turno, actualizar bloques
    select.addEventListener('change', function() {
        const turnoId = parseInt(this.value);
        updateBloqueOptions(turnoId);
    });
}

// Actualizar opciones de bloques según turno
function updateBloqueOptions(turnoId) {
    const select = document.getElementById('bloqueInicioSelect');
    select.innerHTML = '<option value="">Seleccionar bloque de inicio...</option>';
    
    const turnos = calendarioData.turnos || [];
    const turno = turnos.find(t => t.id === turnoId);
     
     if (turno && turno.bloques) {
         turno.bloques.forEach(bloque => {
             const option = document.createElement('option');
             option.value = bloque.id;
            option.textContent = `Bloque ${bloque.orden} - ${bloque.estado.nombre} (${bloque.duracion_dias} días)`;
            select.appendChild(option);
        });
    }
}

// Mostrar asignaciones para editar/eliminar (solo las del mes actual)
function showAsignaciones(personalId) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    const todasAsignaciones = persona.asignaciones_faena || [];
    
    // Filtrar asignaciones que estén activas durante el mes actual
    const primerDiaMes = new Date(currentYear, currentMonth - 1, 1);
    const ultimoDiaMes = new Date(currentYear, currentMonth, 0);
    
    const asignaciones = todasAsignaciones.filter(asig => {
        if (!asig.fecha_inicio) return false;
        
        const fechaInicio = new Date(asig.fecha_inicio);
        const fechaFin = asig.fecha_fin ? new Date(asig.fecha_fin) : null;
        
        // La asignación está activa en el mes si:
        // - Comienza antes o durante el mes Y
        // - (No tiene fecha fin O la fecha fin es después o durante el mes)
        const iniciaAntesODuranteMes = fechaInicio <= ultimoDiaMes;
        const terminaDespuesODuranteMes = !fechaFin || fechaFin >= primerDiaMes;
        
        return iniciaAntesODuranteMes && terminaDespuesODuranteMes;
    });
    
    let html = `
        <h6 class="mb-3">Asignaciones de <strong>${nombreCompleto}</strong></h6>
        <p class="text-muted small mb-3">
            <i class="bi bi-calendar-month me-1"></i>Mostrando asignaciones activas en: ${currentMonthName} ${currentYear}
        </p>
    `;
    
    if (asignaciones.length === 0) {
        html += `
            <div class="alert alert-info">
                No tiene asignaciones activas en este mes.
            </div>
            <button class="btn btn-success w-100" onclick="openFaenaModal(${personalId})">
                <i class="bi bi-plus-circle me-1"></i>Nueva Asignación
            </button>
        `;
    } else {
        html += '<div class="list-group mb-3">';
        
        asignaciones.forEach(asig => {
            const fechaInicio = formatFechaChilena(asig.fecha_inicio);
            const fechaFin = asig.fecha_fin ? formatFechaChilena(asig.fecha_fin) : 'Sin fecha fin';
            const estadoClass = asig.activo ? 'success' : 'secondary';
            const estadoText = asig.activo ? 'Activa' : 'Inactiva';
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${asig.faena.nombre}</h6>
                            <p class="mb-1 small">
                                <strong>Desde:</strong> ${fechaInicio} 
                                <strong>Hasta:</strong> ${fechaFin}
                            </p>
                            <span class="badge bg-${estadoClass}">${estadoText}</span>
                        </div>
                        <div class="btn-group-vertical btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editarAsignacion(${personalId}, ${asig.id})" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="confirmarEliminarAsignacion(${asig.id})" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        html += `
            <button class="btn btn-success w-100" onclick="openFaenaModal(${personalId})">
                <i class="bi bi-plus-circle me-1"></i>Nueva Asignación
            </button>
        `;
    }
    
    document.getElementById('personalModalBody').innerHTML = html;
    
    const modal = new bootstrap.Modal(document.getElementById('personalModal'));
    modal.show();
}

// Editar asignación existente
function editarAsignacion(personalId, asignacionId) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const asignacion = persona.asignaciones_faena.find(a => a.id === asignacionId);
    if (!asignacion) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    
    // Cambiar título del modal
    document.querySelector('#faenaModal .modal-title').textContent = 'Editar Asignación de Faena';
    
    // Llenar formulario con datos de la asignación
    document.getElementById('personalId').value = personalId;
    document.getElementById('asignacionId').value = asignacionId;
    document.getElementById('faenaPersonalNombre').textContent = nombreCompleto;
    document.getElementById('faenaSelect').value = asignacion.faena.id;
    document.getElementById('turnoSelect').value = asignacion.turno_id;
    document.getElementById('fechaInicio').value = asignacion.fecha_inicio || '';
    document.getElementById('fechaFin').value = asignacion.fecha_fin || '';
    document.getElementById('observaciones').value = asignacion.observaciones || '';
    document.getElementById('activo').checked = asignacion.activo;
    
    // Actualizar bloques del turno
    updateBloqueOptions(asignacion.turno_id);
    if (asignacion.bloque_inicio_id) {
        document.getElementById('bloqueInicioSelect').value = asignacion.bloque_inicio_id;
    }
    
    // Mostrar botón eliminar
    document.getElementById('btnEliminar').style.display = 'inline-block';
    
    // Cerrar modal de personal
    const personalModalEl = document.getElementById('personalModal');
    const personalModal = bootstrap.Modal.getInstance(personalModalEl);
    if (personalModal) {
        personalModal.hide();
    }
    
    // Abrir modal de faena
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Confirmar eliminación de asignación
async function confirmarEliminarAsignacion(asignacionId) {
    const confirmado = await showConfirm(
        '¿Está seguro de eliminar esta asignación? Esta acción no se puede deshacer.',
        'Eliminar Asignación'
    );
    
    if (confirmado) {
        eliminarAsignacionDirecta(asignacionId);
    }
}

// Abrir modal de faena para nueva asignación
function openFaenaModal(personalId) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    
    // Cambiar título del modal
    document.querySelector('#faenaModal .modal-title').textContent = 'Nueva Asignación de Faena';
    
    document.getElementById('personalId').value = personalId;
    document.getElementById('asignacionId').value = '';
    document.getElementById('faenaPersonalNombre').textContent = nombreCompleto;
    
    // Limpiar formulario
    document.getElementById('faenaForm').reset();
    document.getElementById('btnEliminar').style.display = 'none';
    
    // Cerrar modal de personal si está abierto
    const personalModalEl = document.getElementById('personalModal');
    const personalModal = bootstrap.Modal.getInstance(personalModalEl);
    if (personalModal) {
        personalModal.hide();
    }
    
    // Abrir modal de faena
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Configurar eventos de modales
function setupModalEvents() {
    document.getElementById('btnGuardar').addEventListener('click', guardarAsignacion);
    document.getElementById('btnEliminar').addEventListener('click', eliminarAsignacion);
}

// Guardar asignación
async function guardarAsignacion() {
    const form = document.getElementById('faenaForm');
    const formData = new FormData(form);
    
    const data = {
        personal_id: formData.get('personal_id'),
        faena_id: formData.get('faena_id'),
        turno_id: formData.get('turno_id'),
        fecha_inicio: formData.get('fecha_inicio'),
        fecha_fin: formData.get('fecha_fin') || null,
        bloque_inicio_id: formData.get('bloque_inicio_id') || null,
        observaciones: formData.get('observaciones') || '',
        activo: document.getElementById('activo').checked
    };
    
    const asignacionId = formData.get('asignacion_id');
    const url = asignacionId ? '/calendario/api/actualizar-asignacion/' : '/calendario/api/crear-asignacion/';
    
    if (asignacionId) {
        data.asignacion_id = asignacionId;
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            setTimeout(() => location.reload(), 1500);
                 } else {
            showAlert('Error: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error al guardar la asignación', 'error');
    }
}

// Eliminar asignación desde el formulario
async function eliminarAsignacion() {
    const confirmado = await showConfirm(
        '¿Está seguro de eliminar esta asignación? Esta acción no se puede deshacer.',
        'Eliminar Asignación'
    );
    
    if (!confirmado) return;
    
    const asignacionId = document.getElementById('asignacionId').value;
    await eliminarAsignacionDirecta(asignacionId);
}

// Eliminar asignación directa (puede llamarse desde cualquier lugar)
async function eliminarAsignacionDirecta(asignacionId) {
    try {
        const response = await fetch('/calendario/api/eliminar-asignacion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ asignacion_id: asignacionId })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert('Error: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error al eliminar la asignación', 'error');
    }
}

