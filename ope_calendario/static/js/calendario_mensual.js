// Calendario de Planificación - JavaScript

// Obtener datos inyectados desde el template
const calendarioData = window.calendarioData;
const currentYear = window.currentYear;
const currentMonth = window.currentMonth;
const currentMonthName = window.currentMonthName;
const filtros = window.filtros;
const mesAnterior = window.mesAnterior;
const mesSiguiente = window.mesSiguiente;

// Crear mapa de asignaciones por personal para acceso rápido
const asignacionesPorPersonal = {};
if (calendarioData.asignaciones) {
    calendarioData.asignaciones.forEach(asig => {
        if (!asignacionesPorPersonal[asig.personal_id]) {
            asignacionesPorPersonal[asig.personal_id] = [];
        }
        asignacionesPorPersonal[asig.personal_id].push(asig);
    });
}

// Crear mapa de turnos para acceso rápido
const turnosMap = {};
if (calendarioData.turnos) {
    calendarioData.turnos.forEach(turno => {
        turnosMap[turno.id] = turno;
    });
}

// Crear mapa de estados para acceso rápido
const estadosMap = {};
if (calendarioData.todos_estados_disponibles) {
    calendarioData.todos_estados_disponibles.forEach(estado => {
        estadosMap[estado.nombre] = estado;
    });
}

// Nombres de meses y días en español
const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
 const dayNames = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];

/**
 * Formatea una fecha al formato chileno (DD-MM-YYYY)
 * @param {Date|string} fecha - Fecha a formatear
 * @returns {string} Fecha formateada
 */
function formatearFechaChilena(fecha) {
    if (!fecha) return '';
    
    try {
        const date = fecha instanceof Date ? fecha : new Date(fecha + 'T00:00:00');
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const anio = date.getFullYear();
        return `${dia}-${mes}-${anio}`;
    } catch (error) {
        console.error('Error formateando fecha:', error);
        return fecha;
    }
}

/**
 * Formatea una fecha al formato chileno con día de la semana completo
 * @param {Date} fecha - Fecha a formatear
 * @returns {string} Fecha formateada con día de semana
 */
function formatearFechaChilenaLarga(fecha) {
    const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                   'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    
    const diaSemana = diasSemana[fecha.getDay()];
    const dia = fecha.getDate();
    const mes = meses[fecha.getMonth()];
    const anio = fecha.getFullYear();
    
    return `${diaSemana}, ${dia} de ${mes} de ${anio}`;
}

// Variables globales
let currentDate = new Date(currentYear, currentMonth - 1, 1);
let filteredPersonal = [];

/**
 * Calcula el estado de un trabajador en una fecha específica
 */
function calcularEstadoPersonalFecha(personalId, fecha) {
    // 1. Buscar estado manual
    if (calendarioData.estados_manuales) {
        const estadoManual = calendarioData.estados_manuales.find(em => {
            if (em.personal_id !== personalId) return false;
            const fechaIni = new Date(em.fecha_inicio);
            const fechaFin = new Date(em.fecha_fin);
            return fecha >= fechaIni && fecha <= fechaFin;
        });
        
        if (estadoManual) {
            const estado = calendarioData.todos_estados_disponibles.find(e => e.id === estadoManual.estado_id);
            return estado || calendarioData.estado_predeterminado;
        }
    }
    
    // 2. Buscar asignación de faena activa
    // Normalizar la fecha para comparación (solo año, mes, día, sin hora)
    const fechaNormalizada = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
    
    const asignaciones = asignacionesPorPersonal[personalId] || [];
    const asignacionActiva = asignaciones.find(asig => {
        if (!asig.activo) return false;
        
        // Normalizar fechas para comparación (solo fecha, sin hora)
        const fechaIniStr = asig.fecha_inicio.split('T')[0]; // Obtener solo la parte de fecha
        const fechaIniParts = fechaIniStr.split('-');
        const fechaIni = new Date(parseInt(fechaIniParts[0]), parseInt(fechaIniParts[1]) - 1, parseInt(fechaIniParts[2]));
        
        if (fechaNormalizada < fechaIni) return false;
        
        if (asig.fecha_fin) {
            const fechaFinStr = asig.fecha_fin.split('T')[0]; // Obtener solo la parte de fecha
            const fechaFinParts = fechaFinStr.split('-');
            const fechaFin = new Date(parseInt(fechaFinParts[0]), parseInt(fechaFinParts[1]) - 1, parseInt(fechaFinParts[2]));
            if (fechaNormalizada > fechaFin) return false;
        }
        
        return true;
    });
    
    if (asignacionActiva) {
        const turno = turnosMap[asignacionActiva.turno_id];
        if (turno && turno.bloques && turno.bloques.length > 0) {
            const fechaInicio = new Date(asignacionActiva.fecha_inicio);
            const diasTranscurridos = Math.floor((fecha - fechaInicio) / (1000 * 60 * 60 * 24));
            
            const longitudCiclo = turno.bloques.reduce((sum, b) => sum + b.duracion_dias, 0);
            if (longitudCiclo === 0) return calendarioData.estado_predeterminado;
            
            let posicionCiclo = diasTranscurridos % longitudCiclo;
            
            if (asignacionActiva.bloque_inicio_orden && asignacionActiva.bloque_inicio_orden > 1) {
                let offsetInicio = 0;
                for (let i = 0; i < asignacionActiva.bloque_inicio_orden - 1; i++) {
                    if (i < turno.bloques.length) {
                        offsetInicio += turno.bloques[i].duracion_dias;
                    }
                }
                posicionCiclo = (posicionCiclo + offsetInicio) % longitudCiclo;
            }
            
            let diasAcumulados = 0;
            for (const bloque of turno.bloques) {
                if (posicionCiclo < diasAcumulados + bloque.duracion_dias) {
                    return bloque.estado;
                }
                diasAcumulados += bloque.duracion_dias;
            }
        }
    }
    
    // 3. Retornar estado predeterminado
    return calendarioData.estado_predeterminado;
}

/**
 * Formatea una fecha ISO (YYYY-MM-DD) al formato chileno (DD-MM-YYYY).
 * Versión simplificada para fechas en formato string ISO.
 * @param {string} fechaISO - Fecha en formato ISO (YYYY-MM-DD)
 * @returns {string} Fecha formateada en formato chileno (DD-MM-YYYY) o 'Sin fecha' si no hay fecha
 */
function formatearFechaChilena(fechaISO) {
    if (!fechaISO) return 'Sin fecha';
    const [year, month, day] = fechaISO.split('-');
    return `${day}-${month}-${year}`;
}

/**
 * Muestra un modal de alerta con mensaje y tipo específico.
 * Configura el color del header según el tipo (success, error, info).
 * @param {string} message - Mensaje a mostrar en el modal
 * @param {string} type - Tipo de alerta: 'success', 'error' o 'info' (por defecto: 'info')
 */
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

/**
 * Muestra un modal de confirmación y retorna una Promise que se resuelve con true/false.
 * El usuario puede confirmar o cancelar la acción.
 * @param {string} message - Mensaje de confirmación a mostrar
 * @param {string} title - Título del modal (por defecto: 'Confirmar')
 * @returns {Promise<boolean>} Promise que se resuelve con true si se confirma, false si se cancela
 */
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
    
    // Inicializar filteredPersonal con todos los datos al cargar la página
    if (calendarioData && calendarioData.personal) {
        filteredPersonal = [...calendarioData.personal];
    }
    
    // NO tocar la leyenda de estados - dejar que el template HTML lo maneje
    
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

/**
 * Genera la leyenda de estados visual en el contenedor especificado.
 * Muestra todos los estados disponibles con sus colores y nombres cortos.
 * Evita duplicados verificando si el estado ya existe en la leyenda.
 */
function generateStatusLegend() {
    const legendContainer = document.getElementById('statusLegend');
    if (!legendContainer) {
        console.error('Container statusLegend no encontrado');
        return;
    }
    
    const estados = calendarioData.todos_estados_disponibles || [];
    console.log('Generando leyenda con', estados.length, 'estados');
    
    // Limpiar todos los elementos de estado existentes, pero mantener el texto base
    const itemsExistentes = legendContainer.querySelectorAll('.status-legend-item');
    itemsExistentes.forEach(item => item.remove());
    
    // Verificar si ya tiene el texto base
    const tieneTextoBase = legendContainer.innerHTML.includes('Estados:');
    
    // Si no tiene el texto base, agregarlo
    if (!tieneTextoBase) {
        legendContainer.innerHTML = '<small class="me-2 fw-bold">Estados:</small>';
    }
    
    // Si hay estados, agregarlos
    if (estados.length > 0) {
        estados.forEach(estado => {
            if (!estado || !estado.nombre) return;
            
            // Verificar si este estado ya existe para evitar duplicados
            const estadoExiste = Array.from(legendContainer.querySelectorAll('.status-legend-item')).some(item => {
                const small = item.querySelector('small');
                return small && small.textContent.trim() === estado.nombre;
            });
            
            if (estadoExiste) {
                return; // Saltar si ya existe
            }
            
            const nombre_corto = estado.nombre_corto || estado.nombre.substring(0, 2).toUpperCase();
            const background_color = estado.background_color || '#cccccc';
            const color = estado.color || '#000000';
            
            const item = document.createElement('div');
            item.className = 'status-legend-item';
            item.innerHTML = `
                <div class="status-legend-color" style="background-color: ${background_color}; color: ${color}; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 600;">
                    ${nombre_corto}
                </div>
                <small>${estado.nombre}</small>
            `;
            legendContainer.appendChild(item);
        });
    }
    
    console.log('Leyenda generada. HTML final:', legendContainer.innerHTML.substring(0, 100));
}

/**
 * Genera la tabla del calendario mensual con encabezados de días y filas de personal.
 * Usa los estados calculados del backend cuando están disponibles, o calcula estados localmente como fallback.
 * Marca días de fin de semana y el día actual con clases CSS especiales.
 * Cada celda es clickeable para mostrar información detallada del estado.
 */
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
    // Usar filteredPersonal que ya fue filtrado por filtrarPersonalLocalmente()
    // Solo inicializar si está vacío o no está definido (primera vez o después de recargar)
    if (!filteredPersonal || filteredPersonal.length === 0) {
        filteredPersonal = calendarioData.personal ? [...calendarioData.personal] : [];
    }
    
    const tbody = document.getElementById('calendarBody');
    let bodyHTML = '';
    
    filteredPersonal.forEach(persona => {
        bodyHTML += '<tr>';
        
        // Columna de nombre (sticky) con botones de acción
        const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
        const cargo = persona.cargo || 'Sin cargo';
        
        bodyHTML += `<td class="sticky-col">
            <div class="personal-name-container">
                <div class="personal-info" onclick="showPersonalInfo(${persona.personal_id})" title="${nombreCompleto}\n${cargo}">
                    <div style="font-size: 0.75rem;">${nombreCompleto}</div>
                    <small style="color: #fd7e14; font-style: italic; font-size: 0.65rem;">${cargo}</small>
                </div>
                <div class="personal-actions">
                    <button class="btn-action btn-view" onclick="event.stopPropagation(); showAsignaciones(${persona.personal_id})" title="Ver asignaciones">
                        <i class="bi bi-eye"></i>
                    </button>
                </div>
            </div>
        </td>`;
        
        // Celdas de días - USAR ESTADOS CALCULADOS DEL BACKEND
        for (let day = 1; day <= daysInMonth; day++) {
            let estado = null;
            
            // Primero intentar obtener del backend (estados_calculados)
            if (calendarioData.estados_calculados && 
                calendarioData.estados_calculados[persona.personal_id] && 
                calendarioData.estados_calculados[persona.personal_id][day]) {
                
                const estadosDelDia = calendarioData.estados_calculados[persona.personal_id][day];
                if (estadosDelDia && estadosDelDia.length > 0) {
                    estado = estadosDelDia[0]; // Tomar el primer estado (mayor prioridad)
                }
            }
            
            // Si no hay estados calculados, usar el cálculo del cliente (fallback)
            if (!estado) {
                const fecha = new Date(year, month, day);
                estado = calcularEstadoPersonalFecha(persona.personal_id, fecha);
            }
            
            if (estado) {
                bodyHTML += `<td onclick="showEstadoInfo(${persona.personal_id}, ${day})" 
                                style="background-color: ${estado.background_color}; color: ${estado.color};"
                                title="${estado.nombre}">
                    <div class="estado-cell">${estado.nombre_corto}</div>
                </td>`;
            } else {
                // Sin estado - mostrar estado predeterminado
                const estadoPred = calendarioData.estado_predeterminado;
                if (estadoPred) {
                    bodyHTML += `<td onclick="showEstadoInfo(${persona.personal_id}, ${day})" 
                                    style="background-color: ${estadoPred.background_color}; color: ${estadoPred.color};"
                                    title="${estadoPred.nombre}">
                        <div class="estado-cell">${estadoPred.nombre_corto}</div>
                    </td>`;
                } else {
                    bodyHTML += `<td class="empty-cell" onclick="showEstadoInfo(${persona.personal_id}, ${day})"></td>`;
                }
            }
        }
        
        bodyHTML += '</tr>';
    });
    
    tbody.innerHTML = bodyHTML;
}

/**
 * Muestra información detallada del estado de un personal en un día específico.
 * Abre un modal con información del estado, faena, turno y detalles adicionales.
 * Prioriza estados calculados del backend sobre cálculos locales.
 * @param {number} personalId - ID del personal
 * @param {number} day - Día del mes (1-31)
 */
function showEstadoInfo(personalId, day) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    const cargo = persona.cargo || 'Sin cargo';
    const fecha = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    
    // USAR ESTADOS CALCULADOS DEL BACKEND (incluye fuentes de estado)
    let estado = null;
    
    // Primero intentar obtener del backend (estados_calculados)
    if (calendarioData.estados_calculados && 
        calendarioData.estados_calculados[personalId] && 
        calendarioData.estados_calculados[personalId][day]) {
        
        const estadosDelDia = calendarioData.estados_calculados[personalId][day];
        if (estadosDelDia && estadosDelDia.length > 0) {
            estado = estadosDelDia[0]; // Tomar el primer estado (mayor prioridad)
        }
    }
    
    // Si no hay estados calculados, usar el cálculo del cliente (fallback)
    if (!estado) {
        estado = calcularEstadoPersonalFecha(personalId, fecha);
    }
    
    // Si aún no hay estado, usar el predeterminado
    if (!estado && calendarioData.estado_predeterminado) {
        estado = calendarioData.estado_predeterminado;
    }
    
    // Normalizar la fecha para comparación (solo año, mes, día, sin hora)
    const fechaNormalizada = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
    
    // Buscar asignación activa (turno normal)
    const asignaciones = asignacionesPorPersonal[personalId] || [];
    const asignacionActiva = asignaciones.find(asig => {
        if (!asig.activo) return false;
        
        // Normalizar fechas para comparación (solo fecha, sin hora)
        const fechaIniStr = asig.fecha_inicio.split('T')[0]; // Obtener solo la parte de fecha
        const fechaIniParts = fechaIniStr.split('-');
        const fechaIni = new Date(parseInt(fechaIniParts[0]), parseInt(fechaIniParts[1]) - 1, parseInt(fechaIniParts[2]));
        
        if (fechaNormalizada < fechaIni) return false;
        
        if (asig.fecha_fin) {
            const fechaFinStr = asig.fecha_fin.split('T')[0]; // Obtener solo la parte de fecha
            const fechaFinParts = fechaFinStr.split('-');
            const fechaFin = new Date(parseInt(fechaFinParts[0]), parseInt(fechaFinParts[1]) - 1, parseInt(fechaFinParts[2]));
            if (fechaNormalizada > fechaFin) return false;
        }
        
        return true;
    });
    
    let faenaActual = 'Sin asignar';
    let turnoNombre = '-';
    
    // Primero verificar si el estado tiene información de faena (estados manuales)
    if (estado && estado.faena_nombre) {
        faenaActual = estado.faena_nombre;
        turnoNombre = 'Estado Manual';
    } else if (asignacionActiva) {
        // Si no es estado manual, usar la asignación de turno normal
        faenaActual = asignacionActiva.faena.nombre;
        const turno = turnosMap[asignacionActiva.turno_id];
        turnoNombre = turno ? turno.nombre : '-';
    }
    
    // Llenar modal
    document.getElementById('modalPersonal').textContent = nombreCompleto;
    document.getElementById('modalFecha').textContent = formatearFechaChilenaLarga(fecha);
    document.getElementById('modalEstado').textContent = estado ? estado.nombre : 'Sin estado';
    document.getElementById('modalFaena').textContent = faenaActual;
    document.getElementById('modalCargo').textContent = cargo;
    
    // Mostrar detalles adicionales si existen
    const detallesDiv = document.getElementById('modalDetallesEstado');
    if (estado && estado.detalles) {
        let detallesHTML = '<div class="alert alert-info mt-2 mb-2" style="font-size: 0.9rem;">';
        
        if (estado.detalles.tipo_detalle) {
            detallesHTML += `<div class="mb-1"><strong>Tipo:</strong> ${estado.detalles.tipo_detalle}</div>`;
        }
        
        if (estado.detalles.fecha_inicio && estado.detalles.fecha_fin) {
            detallesHTML += `<div class="mb-1"><strong>Período:</strong> ${estado.detalles.fecha_inicio} - ${estado.detalles.fecha_fin}</div>`;
        }
        
        if (estado.detalles.dias) {
            detallesHTML += `<div class="mb-1"><strong>Días:</strong> ${estado.detalles.dias}</div>`;
        }
        
        if (estado.detalles.observacion) {
            detallesHTML += `<div class="mb-0"><strong>Observación:</strong> ${estado.detalles.observacion}</div>`;
        }
        
        detallesHTML += '</div>';
        detallesDiv.innerHTML = detallesHTML;
    } else {
        detallesDiv.innerHTML = '';
    }
     
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('estadoModal'));
    modal.show();
}

/**
 * Muestra información completa del personal incluyendo documentación (licencias, certificaciones, exámenes).
 * Hace una petición AJAX al backend para obtener información detallada y la muestra en un modal con tabs.
 * @param {number} personalId - ID del personal a consultar
 */
async function showPersonalInfo(personalId) {
    // Cambiar título del modal
    document.getElementById('personalModalTitle').textContent = 'Información Personal y Documentación';
    
    // Mostrar modal con spinner
    const modal = new bootstrap.Modal(document.getElementById('personalModal'));
    modal.show();
    
    try {
        // Llamar a la API para obtener información completa
        const response = await fetch(`/calendario/api/personal/${personalId}/info/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        });
        
        const result = await response.json();
        
        if (result.status !== 'success') {
            document.getElementById('personalModalBody').innerHTML = `
                <div class="alert alert-danger">Error al cargar información: ${result.message}</div>
            `;
            return;
        }
        
        const data = result.data;
        const nombreCompleto = `${data.nombre} ${data.apepat} ${data.apemat}`.trim();
        const rut = `${data.rut}-${data.dvrut}`;
        
        // Construir HTML del modal
        let html = `
            <div class="mb-4">
                <h6 class="border-bottom pb-2 mb-3"><i class="bi bi-person-badge me-2"></i>Información Personal</h6>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold mb-1">RUT</label>
                        <input type="text" class="form-control form-control-sm" value="${rut}" readonly>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold mb-1">Cargo</label>
                        <input type="text" class="form-control form-control-sm" value="${data.cargo}" readonly>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold mb-1">Nombre Completo</label>
                        <input type="text" class="form-control form-control-sm" value="${nombreCompleto}" readonly>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold mb-1">Empresa</label>
                        <input type="text" class="form-control form-control-sm" value="${data.empresa}" readonly>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold mb-1">Correo Electrónico</label>
                        <input type="text" class="form-control form-control-sm" value="${data.correo}" readonly>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold mb-1">Dirección</label>
                        <input type="text" class="form-control form-control-sm" value="${data.direccion}" readonly>
                    </div>
                </div>
            </div>
        `;
        
        // Tabs para documentación
        html += `
            <ul class="nav nav-tabs mb-3" id="docModalTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="lic-conducir-tab" data-bs-toggle="tab" data-bs-target="#lic-conducir" type="button">
                        <i class="bi bi-card-text me-1"></i>Licencias Conducir
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="lic-internas-tab" data-bs-toggle="tab" data-bs-target="#lic-internas" type="button">
                        <i class="bi bi-award me-1"></i>Licencias Internas
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="certificaciones-tab" data-bs-toggle="tab" data-bs-target="#certificaciones" type="button">
                        <i class="bi bi-patch-check me-1"></i>Certificaciones
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="examenes-tab" data-bs-toggle="tab" data-bs-target="#examenes" type="button">
                        <i class="bi bi-clipboard2-pulse me-1"></i>Exámenes
                    </button>
                </li>
            </ul>
            
            <div class="tab-content">
                <!-- Licencias de Conducir -->
                <div class="tab-pane fade show active" id="lic-conducir">
                    ${generarTablaLicenciasConducir(data.licencias_conducir)}
                </div>
                
                <!-- Licencias Internas -->
                <div class="tab-pane fade" id="lic-internas">
                    ${generarTablaLicenciasInternas(data.licencias_internas)}
                </div>
                
                <!-- Certificaciones -->
                <div class="tab-pane fade" id="certificaciones">
                    ${generarTablaCertificaciones(data.certificaciones)}
                </div>
                
                <!-- Exámenes -->
                <div class="tab-pane fade" id="examenes">
                    ${generarTablaExamenes(data.examenes)}
                </div>
            </div>
        `;
        
        document.getElementById('personalModalBody').innerHTML = html;
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('personalModalBody').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error al cargar la información del personal
            </div>
        `;
    }
}

/**
 * Genera el HTML de una tabla con las licencias de conducir del personal.
 * Muestra clases, fecha de vencimiento y estado (vigente/vencida).
 * @param {Array} licencias - Array de objetos con información de licencias de conducir
 * @returns {string} HTML de la tabla o mensaje si no hay licencias
 */
function generarTablaLicenciasConducir(licencias) {
    if (licencias.length === 0) {
        return '<div class="alert alert-light text-center"><i class="bi bi-inbox me-2"></i>Sin licencias de conducir registradas</div>';
    }
    
    return `
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Clases</th>
                    <th class="text-center">Fecha Vencimiento</th>
                    <th class="text-center">Estado</th>
                </tr>
            </thead>
            <tbody>
                ${licencias.map(lic => `
                    <tr>
                        <td>${lic.clases || 'N/A'}</td>
                        <td class="text-center">${lic.fecha_vencimiento}</td>
                        <td class="text-center">
                            ${lic.vigente ? '<span class="badge bg-success text-white">Vigente</span>' : '<span class="badge bg-danger text-white">Vencida</span>'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

/**
 * Genera el HTML de una tabla con las licencias internas del personal.
 * Muestra tipo, número, empresa emisora, fecha de vencimiento y estado.
 * @param {Array} licencias - Array de objetos con información de licencias internas
 * @returns {string} HTML de la tabla o mensaje si no hay licencias
 */
function generarTablaLicenciasInternas(licencias) {
    if (licencias.length === 0) {
        return '<div class="alert alert-light text-center"><i class="bi bi-inbox me-2"></i>Sin licencias internas registradas</div>';
    }
    
    return `
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Tipo</th>
                    <th>N° Licencia</th>
                    <th>Empresa</th>
                    <th class="text-center">Fecha Vencimiento</th>
                    <th class="text-center">Estado</th>
                </tr>
            </thead>
            <tbody>
                ${licencias.map(lic => `
                    <tr>
                        <td>${lic.tipo}</td>
                        <td class="text-center">${lic.numero}</td>
                        <td>${lic.empresa}</td>
                        <td class="text-center">${lic.fecha_vencimiento}</td>
                        <td class="text-center">
                            ${lic.vigente ? '<span class="badge bg-success text-white">Vigente</span>' : '<span class="badge bg-danger text-white">Vencida</span>'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

/**
 * Genera el HTML de una tabla con las certificaciones del personal.
 * Muestra tipo, proveedor, fecha de vencimiento y estado (vigente/vencida).
 * @param {Array} certificaciones - Array de objetos con información de certificaciones
 * @returns {string} HTML de la tabla o mensaje si no hay certificaciones
 */
function generarTablaCertificaciones(certificaciones) {
    if (certificaciones.length === 0) {
        return '<div class="alert alert-light text-center"><i class="bi bi-inbox me-2"></i>Sin certificaciones registradas</div>';
    }
    
    return `
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Tipo</th>
                    <th>Proveedor</th>
                    <th class="text-center">Fecha Vencimiento</th>
                    <th class="text-center">Estado</th>
                </tr>
            </thead>
            <tbody>
                ${certificaciones.map(cert => `
                    <tr>
                        <td>${cert.tipo}</td>
                        <td>${cert.proveedor}</td>
                        <td class="text-center">${cert.fecha_vencimiento}</td>
                        <td class="text-center">
                            ${cert.vigente ? '<span class="badge bg-success text-white">Vigente</span>' : '<span class="badge bg-danger text-white">Vencida</span>'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

/**
 * Genera el HTML de una tabla con los exámenes del personal.
 * Muestra tipo, resultado (con badge de color según resultado), proveedor, fecha de vencimiento y estado.
 * @param {Array} examenes - Array de objetos con información de exámenes
 * @returns {string} HTML de la tabla o mensaje si no hay exámenes
 */
function generarTablaExamenes(examenes) {
    if (examenes.length === 0) {
        return '<div class="alert alert-light text-center"><i class="bi bi-inbox me-2"></i>Sin exámenes registrados</div>';
    }
    
    return `
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Tipo</th>
                    <th class="text-center">Resultado</th>
                    <th>Proveedor</th>
                    <th class="text-center">Fecha Vencimiento</th>
                    <th class="text-center">Estado</th>
                </tr>
            </thead>
            <tbody>
                ${examenes.map(exam => {
                    let resultadoBadge = 'bg-secondary';
                    if (exam.resultado.toLowerCase().includes('aprobado')) {
                        resultadoBadge = 'bg-success';
                    } else if (exam.resultado.toLowerCase().includes('reprobado')) {
                        resultadoBadge = 'bg-danger';
                    }
                    
                    return `
                        <tr>
                            <td>${exam.tipo}</td>
                            <td class="text-center">
                                ${exam.resultado !== '-' ? `<span class="badge ${resultadoBadge} text-white">${exam.resultado}</span>` : '-'}
                            </td>
                            <td>${exam.proveedor}</td>
                            <td class="text-center">${exam.fecha_vencimiento}</td>
                            <td class="text-center">
                                ${exam.vigente ? '<span class="badge bg-success text-white">Vigente</span>' : '<span class="badge bg-danger text-white">Vencida</span>'}
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
}

/**
 * Configura los event listeners para los filtros del calendario.
 * El filtro de búsqueda funciona localmente (sin recargar página).
 * Los filtros de faena, cargo y empresa recargan la página para usar caché del backend.
 */
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const faenaFilter = document.getElementById('faenaFilter');
    const cargoFilter = document.getElementById('cargoFilter');
    const empresaFilter = document.getElementById('empresaFilter');
    
    // Búsqueda - EXACTAMENTE igual que tabla de personal
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filtrarYRenderizarCalendario();
        });
    }
    
    // Filtros de faena, cargo y empresa: recargar página (requieren consulta al backend)
    if (faenaFilter) {
        faenaFilter.addEventListener('change', applyFiltersWithReload);
    }
    if (cargoFilter) {
        cargoFilter.addEventListener('change', applyFiltersWithReload);
    }
    if (empresaFilter) {
        empresaFilter.addEventListener('change', applyFiltersWithReload);
    }
}

/**
 * Filtra y renderiza el calendario - EXACTAMENTE igual que renderizarTabla() en personal_table.js
 */
function filtrarYRenderizarCalendario() {
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    const faena = document.getElementById('faenaFilter')?.value || '';
    const cargo = document.getElementById('cargoFilter')?.value || '';
    const empresa = document.getElementById('empresaFilter')?.value || '';
    
    // Validar que calendarioData.personal esté disponible
    if (!calendarioData || !calendarioData.personal || !Array.isArray(calendarioData.personal)) {
        console.error('calendarioData.personal no está disponible o no es un array');
        return;
    }
    
    // Filtrar personal según búsqueda y filtros - EXACTAMENTE igual que personal_table.js
    filteredPersonal = calendarioData.personal.filter(persona => {
        // Búsqueda global - EXACTAMENTE igual que personal_table.js
        const matchBusqueda = !busqueda || 
            (persona.nombre && persona.nombre.toLowerCase().includes(busqueda)) ||
            (persona.apepat && persona.apepat.toLowerCase().includes(busqueda)) ||
            (persona.apemat && persona.apemat.toLowerCase().includes(busqueda)) ||
            (persona.rut && `${persona.rut}${persona.dvrut || ''}`.toLowerCase().includes(busqueda));
        
        // Filtro de faena (si está seleccionado)
        let matchFaena = true;
        if (faena) {
            const asignaciones = asignacionesPorPersonal[persona.personal_id] || [];
            const asignacionActiva = asignaciones.find(asig => asig.activo);
            if (faena === 'Sin asignar') {
                matchFaena = !asignacionActiva;
            } else {
                matchFaena = asignacionActiva && asignacionActiva.faena.nombre === faena;
            }
        }
        
        // Filtro de cargo (si está seleccionado)
        const matchCargo = !cargo || (persona.cargo && persona.cargo === cargo);
        
        // Filtro de empresa (si está seleccionado)
        const matchEmpresa = !empresa || (persona.empresa && persona.empresa === empresa);
        
        return matchBusqueda && matchFaena && matchCargo && matchEmpresa;
    });
    
    // Re-renderizar calendario - igual que renderizarTabla() llama a actualizar el tbody
    generateCalendar();
}

/**
 * Aplica los filtros recargando la página para usar el caché del backend.
 * Mantiene los parámetros de año, mes y tamaño de página.
 * Resetea la página a 1 al aplicar nuevos filtros.
 * Construye la URL con todos los parámetros de filtro y recarga la página.
 */
function applyFiltersWithReload() {
    const searchValue = document.getElementById('searchInput').value.trim();
    const faenaValue = document.getElementById('faenaFilter').value;
    const cargoValue = document.getElementById('cargoFilter').value;
    const empresaValue = document.getElementById('empresaFilter').value;
    
    // Construir URL con parámetros
    const url = new URL(window.location.href);
    
    // Mantener year, month y page_size
    const currentYear = url.searchParams.get('year') || new Date().getFullYear();
    const currentMonth = url.searchParams.get('month') || (new Date().getMonth() + 1);
    const pageSize = url.searchParams.get('page_size') || '10';
    
    // Limpiar y reconstruir todos los parámetros
    url.search = '';
    url.searchParams.set('year', currentYear);
    url.searchParams.set('month', currentMonth);
    url.searchParams.set('page', '1'); // Resetear a página 1
    url.searchParams.set('page_size', pageSize);
    
    // Agregar nuevos parámetros de filtros solo si tienen valor
    if (searchValue) url.searchParams.set('search', searchValue);
    if (faenaValue) url.searchParams.set('faena', faenaValue);
    if (cargoValue) url.searchParams.set('cargo', cargoValue);
    if (empresaValue) url.searchParams.set('empresa', empresaValue);
    
    // Recargar página con nuevos parámetros
    window.location.href = url.toString();
}

/**
 * Aplica filtros en el frontend mostrando/ocultando filas del calendario.
 * Función LEGACY mantenida para compatibilidad.
 * Filtra por búsqueda, faena y cargo sin recargar la página.
 * @deprecated Se recomienda usar filtrarPersonalLocalmente() o applyFiltersWithReload()
 */
function applyFilters() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const faenaValue = document.getElementById('faenaFilter').value;
    const cargoValue = document.getElementById('cargoFilter').value;
    
    const rows = document.querySelectorAll('#calendarBody tr');
    
    calendarioData.personal.forEach((persona, index) => {
        const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.toLowerCase();
        const rut = `${persona.rut}${persona.dvrut}`.toLowerCase();
        const cargo = persona.cargo || 'Sin cargo';
        
        // Buscar asignación activa
        const asignaciones = asignacionesPorPersonal[persona.personal_id] || [];
        const asignacionActiva = asignaciones.find(asig => asig.activo);
        let faena = 'Sin asignar';
        if (asignacionActiva) {
            faena = asignacionActiva.faena.nombre;
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

/**
 * Limpia todos los filtros manteniendo solo los parámetros básicos (año, mes, tamaño de página).
 * Resetea la página a 1 y recarga la página con la URL limpia.
 */
function clearFilters() {
    // Limpiar filtros manteniendo year, month y page_size
    const url = new URL(window.location.href);
    const currentYear = url.searchParams.get('year') || new Date().getFullYear();
    const currentMonth = url.searchParams.get('month') || (new Date().getMonth() + 1);
    const pageSize = url.searchParams.get('page_size') || '25';
    
    // Reconstruir URL solo con parámetros básicos
    url.search = '';
    url.searchParams.set('year', currentYear);
    url.searchParams.set('month', currentMonth);
    url.searchParams.set('page', '1');
    url.searchParams.set('page_size', pageSize);
    
    window.location.href = url.toString();
}

/**
 * Cambia el tamaño de página (cantidad de registros por página) y recarga.
 * Mantiene todos los demás parámetros (filtros, año, mes).
 * Resetea la página a 1 al cambiar el tamaño.
 * @param {number|string} size - Nuevo tamaño de página (ej: 10, 25, 50)
 */
function cambiarTamanioPagina(size) {
    const url = new URL(window.location.href);
    
    // Mantener todos los parámetros existentes
    url.searchParams.set('page_size', size);
    url.searchParams.set('page', '1'); // Volver a página 1 al cambiar tamaño
    
    window.location.href = url.toString();
}

/**
 * Navega al mes anterior y recarga el calendario.
 */
function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    navigateToDate();
}

/**
 * Navega al mes siguiente y recarga el calendario.
 */
function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    navigateToDate();
}

/**
 * Navega al año anterior y recarga el calendario.
 */
function previousYear() {
    currentDate.setFullYear(currentDate.getFullYear() - 1);
    navigateToDate();
}

/**
 * Navega al año siguiente y recarga el calendario.
 */
function nextYear() {
    currentDate.setFullYear(currentDate.getFullYear() + 1);
    navigateToDate();
}

/**
 * Navega al mes actual (hoy) y recarga el calendario.
 */
function goToToday() {
    const today = new Date();
    currentDate = new Date(today.getFullYear(), today.getMonth(), 1);
    navigateToDate();
}

/**
 * Navega a la fecha configurada en currentDate y recarga el calendario.
 * Mantiene todos los parámetros de filtros y paginación.
 * Resetea la página a 1 al cambiar de mes/año.
 */
function navigateToDate() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    
    // Mantener parámetros actuales (filtros y paginación)
    const url = new URL(window.location.href);
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    url.searchParams.set('page', '1'); // Resetear a página 1 al cambiar de mes
    
    window.location.href = url.toString();
}

/**
 * Llena el select de faenas con las opciones disponibles.
 * Agrega información de fechas como data attributes para uso posterior.
 */
function populateFaenaOptions() {
    const select = document.getElementById('faenaSelect');
    const faenas = calendarioData.faenas || [];
    
    faenas.forEach(faena => {
        const option = document.createElement('option');
        option.value = faena.id;
        option.textContent = faena.nombre;
        
        // Agregar información de fechas como data attributes
        if (faena.fecha_inicio) {
            option.dataset.fechaInicio = faena.fecha_inicio;
        }
        if (faena.fecha_fin) {
            option.dataset.fechaFin = faena.fecha_fin;
        }
        
        select.appendChild(option);
    });
}

/**
 * Llena el select de turnos con las opciones disponibles.
 * Configura un event listener para actualizar los bloques cuando cambie el turno seleccionado.
 */
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

/**
 * Actualiza las opciones del select de bloques según el turno seleccionado.
 * Si no hay asignación en edición, selecciona automáticamente el primer bloque.
 * @param {number} turnoId - ID del turno para el cual cargar los bloques
 */
function updateBloqueOptions(turnoId) {
    const select = document.getElementById('bloqueInicioSelect');
    select.innerHTML = '<option value="">Seleccionar bloque de inicio...</option>';
    
    const turnos = calendarioData.turnos || [];
    const turno = turnos.find(t => t.id === turnoId);
     
     if (turno && turno.bloques) {
         let primerBloqueId = null;
         
         turno.bloques.forEach((bloque, index) => {
             const option = document.createElement('option');
             option.value = bloque.id;
             option.dataset.orden = bloque.orden; // Agregar data-orden para búsqueda
            option.textContent = `Bloque ${bloque.orden} - ${bloque.estado.nombre} (${bloque.duracion_dias} días)`;
            select.appendChild(option);
            
            // Guardar el ID del primer bloque
            if (index === 0) {
                primerBloqueId = bloque.id;
            }
        });
        
        // Seleccionar automáticamente el bloque 1 si no hay uno ya seleccionado
        // y NO estamos en modo edición
        const asignacionId = document.getElementById('asignacionId').value;
        if (!asignacionId && primerBloqueId) {
            select.value = primerBloqueId;
        }
    }
}

/**
 * Muestra las asignaciones y estados manuales de un personal para el mes actual.
 * Filtra solo las asignaciones y estados que están activos durante el mes mostrado.
 * Muestra información de faena, turno, fechas y estado (activa/finalizada).
 * @param {number} personalId - ID del personal del cual mostrar asignaciones
 */
function showAsignaciones(personalId) {
    // Cambiar título del modal
    document.getElementById('asignacionesModalTitle').textContent = 'Ver Asignaciones';
    
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    const todasAsignaciones = asignacionesPorPersonal[personalId] || [];
    
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
    
    // Buscar estados manuales de este personal en el mes actual
    const estadosManuales = (calendarioData.estados_manuales || []).filter(em => {
        if (em.personal_id !== personalId) return false;
        
        const fechaInicio = new Date(em.fecha_inicio);
        const fechaFin = new Date(em.fecha_fin);
        
        return fechaInicio <= ultimoDiaMes && fechaFin >= primerDiaMes;
    });
    
    let html = `
        <div class="mb-2 pb-2 border-bottom">
            <div class="fw-semibold small">${nombreCompleto}</div>
            <div class="text-muted" style="font-size: 0.7rem;">
                <i class="bi bi-calendar-month me-1"></i>${currentMonthName} ${currentYear}
            </div>
        </div>
    `;
    
    if (asignaciones.length === 0 && estadosManuales.length === 0) {
        html += `
            <div class="alert alert-info py-2 px-2 mb-0 small">
                <i class="bi bi-info-circle me-1"></i>No tiene asignaciones ni estados manuales activos en este mes.
            </div>
        `;
    } else {
        // Mostrar asignaciones de turno (solo visualización, sin botones de editar/eliminar)
        if (asignaciones.length > 0) {
            asignaciones.forEach((asig, index) => {
                const fechaInicio = formatearFechaChilena(asig.fecha_inicio);
                const fechaFin = asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : 'Sin fin';
                // Determinar estado basado en fechas, no en campo "activo"
                const hoy = new Date();
                hoy.setHours(0, 0, 0, 0);
                let estadoClass = 'success';
                let estadoText = 'Activa';
                
                if (asig.fecha_fin) {
                    const fechaFin = new Date(asig.fecha_fin + 'T00:00:00');
                    fechaFin.setHours(0, 0, 0, 0);
                    if (fechaFin < hoy) {
                        estadoClass = 'secondary';
                        estadoText = 'Finalizada';
                    }
                }
                
                html += `
                    <div class="mb-2 ${index < asignaciones.length - 1 ? 'pb-2 border-bottom' : ''}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="fw-semibold" style="font-size: 0.8rem;">${asig.faena.nombre}</div>
                                <div class="text-muted" style="font-size: 0.7rem;">
                                    ${fechaInicio} → ${fechaFin}
                                </div>
                            </div>
                            <span class="badge bg-${estadoClass} text-white ms-2" style="font-size: 0.65rem;">${estadoText}</span>
                        </div>
                    </div>
                `;
            });
        }
        
        // Mostrar estados manuales
        if (estadosManuales.length > 0) {
            if (asignaciones.length > 0) {
                html += '<hr class="my-2">';
            }
            
            estadosManuales.forEach((em, index) => {
                const fechaInicio = formatearFechaChilena(em.fecha_inicio);
                const fechaFin = formatearFechaChilena(em.fecha_fin);
                
                // Buscar el nombre del estado
                const estado = calendarioData.todos_estados_disponibles.find(e => e.id === em.estado_id);
                const estadoNombre = estado ? estado.nombre : 'Desconocido';
                
                html += `
                    <div class="mb-2 ${index < estadosManuales.length - 1 ? 'pb-2 border-bottom' : ''}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="fw-semibold" style="font-size: 0.8rem;">
                                    <i class="bi bi-wrench me-1 text-warning"></i>Estado Manual
                                </div>
                                <div class="text-muted" style="font-size: 0.7rem;">
                                    ${fechaInicio} → ${fechaFin}
                                </div>
                            </div>
                            <span class="badge ms-2" style="background-color: ${estado ? estado.background_color : '#666'}; color: ${estado ? estado.color : '#fff'}; font-size: 0.65rem;">
                                ${estadoNombre}
                            </span>
                        </div>
                    </div>
                `;
            });
        }
    }
    
    document.getElementById('asignacionesModalBody').innerHTML = html;
    
    const modal = new bootstrap.Modal(document.getElementById('asignacionesModal'));
    modal.show();
}

/**
 * Abre el modal de edición de asignación con los datos de la asignación existente.
 * Precarga todos los campos del formulario (faena, turno, fechas, bloque, observaciones).
 * Muestra el botón de eliminar y configura el modal en modo edición.
 * @param {number} personalId - ID del personal
 * @param {number} asignacionId - ID de la asignación a editar
 */
function editarAsignacion(personalId, asignacionId) {
    const persona = calendarioData.personal.find(p => p.personal_id === personalId);
    if (!persona) return;
    
    // Buscar la asignación en asignacionesPorPersonal (donde están cargadas)
    const asignaciones = asignacionesPorPersonal[personalId] || [];
    const asignacion = asignaciones.find(a => a.id === parseInt(asignacionId));
    
    if (!asignacion) {
        showAlert('Error', 'No se pudo cargar la asignación', 'error');
        return;
    }
    
    const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`.trim();
    
    // Cambiar título del modal
    document.querySelector('#faenaModal .modal-title').textContent = 'Editar Asignación de Faena';
    
    // Llenar formulario con datos de la asignación
    document.getElementById('personalId').value = personalId;
    document.getElementById('asignacionId').value = asignacionId;
    document.getElementById('faenaPersonalNombre').textContent = nombreCompleto;
    document.getElementById('faenaSelect').value = asignacion.faena.id;
    document.getElementById('turnoSelect').value = asignacion.turno_id;
    
    // Convertir fechas ISO a formato de input date (YYYY-MM-DD)
    const fechaInicio = asignacion.fecha_inicio.split('T')[0];
    const fechaFin = asignacion.fecha_fin ? asignacion.fecha_fin.split('T')[0] : '';
    
    // Establecer fechas usando el componente date picker chileno
    if (window.DatePickerChile) {
        DatePickerChile.setValor('fechaInicio', fechaInicio);
        if (fechaFin) {
            DatePickerChile.setValor('fechaFin', fechaFin);
        } else {
            DatePickerChile.limpiar('fechaFin');
        }
    } else {
        document.getElementById('fechaInicio').value = fechaInicio;
        document.getElementById('fechaFin').value = fechaFin;
    }
    document.getElementById('observaciones').value = asignacion.observaciones || '';
    // Campo "activo" eliminado - ya no es necesario
    
    // Precargar fechas de la faena y actualizar bloques
    precargarFechasFaena(asignacion.faena.id);
    updateBloqueOptions(asignacion.turno_id);
    
    // Seleccionar el bloque de inicio si existe
    if (asignacion.bloque_inicio_orden) {
        setTimeout(() => {
            const bloqueSelect = document.getElementById('bloqueInicioSelect');
            const bloqueOption = Array.from(bloqueSelect.options).find(opt => 
                opt.dataset && opt.dataset.orden === String(asignacion.bloque_inicio_orden)
            );
            
            if (bloqueOption) {
                bloqueSelect.value = bloqueOption.value;
            }
        }, 100);
    }
    
    // Mostrar botón eliminar
    document.getElementById('btnEliminar').style.display = 'inline-block';
    
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

/**
 * Muestra un modal de confirmación antes de eliminar una asignación.
 * Si se confirma, llama a eliminarAsignacionDirecta().
 * @param {number} asignacionId - ID de la asignación a eliminar
 */
async function confirmarEliminarAsignacion(asignacionId) {
    const confirmado = await showConfirm(
        '¿Está seguro de eliminar esta asignación? Esta acción no se puede deshacer.',
        'Eliminar Asignación'
    );
    
    if (confirmado) {
        eliminarAsignacionDirecta(asignacionId);
    }
}

/**
 * Abre el modal de faena para crear una nueva asignación.
 * Limpia el formulario y oculta el botón de eliminar.
 * Configura el modal en modo creación (no edición).
 * @param {number} personalId - ID del personal para el cual crear la asignación
 */
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

/**
 * Configura todos los event listeners para los modales de asignación.
 * Incluye: guardar asignación, eliminar asignación, precargar fechas al seleccionar faena,
 * y validar fechas cuando cambian los inputs de fecha.
 */
function setupModalEvents() {
    document.getElementById('btnGuardar').addEventListener('click', guardarAsignacion);
    document.getElementById('btnEliminar').addEventListener('click', eliminarAsignacion);
    
    // Evento para precargar fechas cuando se seleccione una faena
    const faenaSelect = document.getElementById('faenaSelect');
    if (faenaSelect) {
        faenaSelect.addEventListener('change', function() {
            precargarFechasFaena(this.value);
        });
    }
    
    // Validaciones de fechas
    const fechaInicioInput = document.getElementById('fechaInicio');
    const fechaFinInput = document.getElementById('fechaFin');
    
    if (fechaInicioInput) {
        fechaInicioInput.addEventListener('change', function() {
            validarFechasAsignacion();
        });
    }
    
    if (fechaFinInput) {
        fechaFinInput.addEventListener('change', function() {
            validarFechasAsignacion();
        });
    }
}

/**
 * Precarga las fechas de inicio y fin de la faena seleccionada en los inputs de fecha.
 * Solo precarga si NO estamos editando una asignación existente (modo creación).
 * Valida las fechas después de precargarlas.
 * @param {number|string} faenaId - ID de la faena de la cual precargar fechas
 */
function precargarFechasFaena(faenaId) {
    if (!faenaId) {
        // Si no hay faena seleccionada, limpiar fechas
        if (window.DatePickerChile) {
            DatePickerChile.limpiar('fechaInicio');
            DatePickerChile.limpiar('fechaFin');
        } else {
            document.getElementById('fechaInicio').value = '';
            document.getElementById('fechaFin').value = '';
        }
        return;
    }
    
    const faena = calendarioData.faenas.find(f => f.id === parseInt(faenaId));
    if (!faena) return;
    
    // Solo precargar si NO estamos editando una asignación existente
    const asignacionId = document.getElementById('asignacionId').value;
    const shouldPrecarga = !asignacionId; // Solo precargar en modo "nueva asignación"
    
    // Precargar fechas si corresponde
    if (shouldPrecarga) {
        if (faena.fecha_inicio && window.DatePickerChile) {
            DatePickerChile.setValor('fechaInicio', faena.fecha_inicio);
        }
        
        if (faena.fecha_fin && window.DatePickerChile) {
            DatePickerChile.setValor('fechaFin', faena.fecha_fin);
        }
    }
    
    // Validar después de precargar
    validarFechasAsignacion();
}

/**
 * Valida si el personal tiene una licencia médica activa que se solape con el período de asignación.
 * Retorna un objeto con información de la licencia si existe conflicto.
 * @returns {Object} Objeto con {existe: boolean, tipo?: string, fecha_inicio?: string, fecha_fin?: string, dias?: number}
 */
function validarLicenciaMedicaActiva() {
    const personalId = parseInt(document.getElementById('personalId').value);
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
    if (!personalId || !fechaInicio || !fechaFin) {
        return { existe: false };
    }
    
    const licenciasMedicas = calendarioData.licencias_medicas || [];
    
    const nuevaInicio = new Date(fechaInicio);
    const nuevaFin = new Date(fechaFin);
    
    // Buscar licencias que se solapen con el período
    for (const licencia of licenciasMedicas) {
        if (licencia.personal_id !== personalId) continue;
        
        const licInicio = new Date(licencia.fecha_inicio);
        const licFin = new Date(licencia.fecha_fin);
        
        // Verificar solapamiento
        if (nuevaInicio <= licFin && licInicio <= nuevaFin) {
            return {
                existe: true,
                tipo: licencia.tipo,
                fecha_inicio: licencia.fecha_inicio,
                fecha_fin: licencia.fecha_fin,
                dias: licencia.dias
            };
        }
    }
    
    return { existe: false };
}

/**
 * Valida si el personal tiene un ausentismo activo que se solape con el período de asignación.
 * Retorna un objeto con información del ausentismo si existe conflicto.
 * @returns {Object} Objeto con {existe: boolean, tipo?: string, fecha_inicio?: string, fecha_fin?: string}
 */
function validarAusentismoActivo() {
    const personalId = parseInt(document.getElementById('personalId').value);
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
    if (!personalId || !fechaInicio || !fechaFin) {
        return { existe: false };
    }
    
    const ausentismos = calendarioData.ausentismos || [];
    
    const nuevaInicio = new Date(fechaInicio);
    const nuevaFin = new Date(fechaFin);
    
    // Buscar ausentismos que se solapen con el período
    for (const ausentismo of ausentismos) {
        if (ausentismo.personal_id !== personalId) continue;
        
        const ausInicio = new Date(ausentismo.fecha_inicio);
        const ausFin = new Date(ausentismo.fecha_fin);
        
        // Verificar solapamiento
        if (nuevaInicio <= ausFin && ausInicio <= nuevaFin) {
            return {
                existe: true,
                tipo: ausentismo.tipo,
                fecha_inicio: ausentismo.fecha_inicio,
                fecha_fin: ausentismo.fecha_fin
            };
        }
    }
    
    return { existe: false };
}

/**
 * Valida si las fechas de la nueva asignación se solapan con asignaciones existentes en OTRAS faenas.
 * Ignora asignaciones a la misma faena (se permite tener múltiples asignaciones a la misma faena).
 * Retorna información del conflicto si existe solapamiento.
 * @returns {Object} Objeto con {existe: boolean, faena?: string, turno?: string, fecha_inicio?: string, fecha_fin?: string}
 */
function validarSolapamientoFechas() {
    const personalId = parseInt(document.getElementById('personalId').value);
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    const faenaIdNueva = parseInt(document.getElementById('faenaSelect').value);
    
    if (!personalId || !fechaInicio || !fechaFin || !faenaIdNueva) {
        return { existe: false };
    }
    
    const asignacionesPersona = asignacionesPorPersonal[personalId] || [];
    
    // Convertir fechas a Date para comparación
    const nuevaInicio = new Date(fechaInicio);
    const nuevaFin = new Date(fechaFin);
    
    // Buscar solapamientos (SOLO en OTRAS faenas diferentes)
    for (const asig of asignacionesPersona) {
        if (!asig.activo) continue;
        
        // IMPORTANTE: Ignorar asignaciones a la misma faena
        if (asig.faena.id === faenaIdNueva) continue;
        
        const asigInicio = new Date(asig.fecha_inicio);
        const asigFin = asig.fecha_fin ? new Date(asig.fecha_fin) : null;
        
        // Lógica de solapamiento:
        // Dos rangos se solapan si: inicio1 <= fin2 AND inicio2 <= fin1
        let seSolapan = false;
        
        if (asigFin) {
            // Asignación existente tiene fecha fin
            seSolapan = nuevaInicio <= asigFin && asigInicio <= nuevaFin;
        } else {
            // Asignación existente sin fin (indefinida) - solo revisar si la nueva empieza antes de que termine la existente
            seSolapan = asigInicio <= nuevaFin;
        }
        
        if (seSolapan) {
            const turno = calendarioData.turnos.find(t => t.id === asig.turno_id);
            return {
                existe: true,
                faena: asig.faena.nombre,
                turno: turno ? turno.nombre : 'Sin turno',
                fecha_inicio: asig.fecha_inicio.split('T')[0],
                fecha_fin: asig.fecha_fin ? asig.fecha_fin.split('T')[0] : 'Indefinida'
            };
        }
    }
    
    return { existe: false };
}

/**
 * Valida que las fechas de la asignación estén dentro del rango de fechas de la faena seleccionada.
 * Valida que la fecha de fin no sea anterior a la fecha de inicio.
 * Muestra mensajes de error en los inputs si hay problemas.
 * @returns {boolean} true si las fechas son válidas, false si hay errores
 */
function validarFechasAsignacion() {
    const faenaId = document.getElementById('faenaSelect').value;
    if (!faenaId) return true;
    
    const faena = calendarioData.faenas.find(f => f.id === parseInt(faenaId));
    if (!faena) return true;
    
    const fechaInicioInput = document.getElementById('fechaInicio');
    const fechaFinInput = document.getElementById('fechaFin');
    const fechaInicio = fechaInicioInput.value;
    const fechaFin = fechaFinInput.value;
    
    let isValid = true;
    
    // Limpiar mensajes de error previos
    fechaInicioInput.setCustomValidity('');
    fechaFinInput.setCustomValidity('');
    fechaInicioInput.classList.remove('is-invalid');
    fechaFinInput.classList.remove('is-invalid');
    
    // Validar fecha de inicio
    if (fechaInicio && faena.fecha_inicio) {
        if (fechaInicio < faena.fecha_inicio) {
            fechaInicioInput.setCustomValidity('La fecha de inicio no puede ser anterior al inicio de la faena');
            fechaInicioInput.classList.add('is-invalid');
            isValid = false;
        }
    }
    
    if (fechaInicio && faena.fecha_fin) {
        if (fechaInicio > faena.fecha_fin) {
            fechaInicioInput.setCustomValidity('La fecha de inicio no puede ser posterior al fin de la faena');
            fechaInicioInput.classList.add('is-invalid');
            isValid = false;
        }
    }
    
    // Validar fecha de fin
    if (fechaFin && faena.fecha_inicio) {
        if (fechaFin < faena.fecha_inicio) {
            fechaFinInput.setCustomValidity('La fecha de fin no puede ser anterior al inicio de la faena');
            fechaFinInput.classList.add('is-invalid');
            isValid = false;
        }
    }
    
    if (fechaFin && faena.fecha_fin) {
        if (fechaFin > faena.fecha_fin) {
            fechaFinInput.setCustomValidity('La fecha de fin no puede ser posterior al fin de la faena');
            fechaFinInput.classList.add('is-invalid');
            isValid = false;
        }
    }
    
    // Validar que fecha fin no sea menor que fecha inicio
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
        fechaFinInput.setCustomValidity('La fecha de fin no puede ser anterior a la fecha de inicio');
        fechaFinInput.classList.add('is-invalid');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Guarda una nueva asignación o actualiza una existente.
 * Valida fechas, turno con bloques, licencias médicas, ausentismos y solapamientos.
 * Muestra alertas detalladas si hay problemas de validación.
 * Envía los datos al backend y recarga la página si es exitoso.
 */
async function guardarAsignacion() {
    const form = document.getElementById('faenaForm');
    const btnGuardar = document.getElementById('btnGuardar');
    
    // Prevenir doble submit
    if (btnGuardar.disabled) return;
    
    // Validar fechas antes de enviar
    if (!validarFechasAsignacion()) {
        showAlert('Error de Validación', 'Por favor, corrija las fechas de la asignación. Las fechas deben estar dentro del período de la faena.', 'error');
        return;
    }
    
    // Validar que el formulario sea válido
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Validar que el turno tenga bloques configurados
    const turnoId = parseInt(document.getElementById('turnoSelect').value);
    const turno = calendarioData.turnos.find(t => t.id === turnoId);
    
    if (!turno) {
        showAlert('Error', 'Debe seleccionar un turno válido', 'error');
        return;
    }
    
    if (!turno.bloques || turno.bloques.length === 0) {
        const mensaje = `
            <div class="mb-3">
                <i class="bi bi-exclamation-circle-fill text-danger" style="font-size: 2rem;"></i>
                <h6 class="mt-2 mb-1">❌ Turno Sin Bloques Configurados</h6>
                <p class="text-muted mb-0">El turno "${turno.nombre}" no tiene bloques configurados.</p>
            </div>
            <div class="alert alert-warning mb-0">
                <small>
                    <strong><i class="bi bi-info-circle me-1"></i>¿Qué hacer?</strong>
                    <ul class="mb-0 mt-2">
                        <li>Contacte al administrador para que configure los bloques del turno "${turno.nombre}"</li>
                        <li>Los bloques definen la secuencia de trabajo (ej: Día → Descanso → Noche → Descanso)</li>
                        <li>O seleccione un turno diferente que sí tenga bloques configurados</li>
                    </ul>
                </small>
            </div>
        `;
        showAlert('Turno Incompleto', mensaje, 'error');
        return;
    }
    
    // Validar licencias médicas activas
    const licenciaActiva = validarLicenciaMedicaActiva();
    if (licenciaActiva.existe) {
        const mensaje = `
            <div class="mb-3">
                <i class="bi bi-heartbreak-fill text-danger" style="font-size: 2rem;"></i>
                <h6 class="mt-2 mb-1">🏥 Advertencia: Personal con Licencia Médica</h6>
                <p class="text-muted mb-0">Este personal tiene una licencia médica activa en el período seleccionado.</p>
            </div>
            <div class="alert alert-danger mb-3">
                <div class="mb-2"><strong>Licencia Médica Activa:</strong></div>
                <div><strong>Tipo:</strong> ${licenciaActiva.tipo}</div>
                <div><strong>Período:</strong> ${licenciaActiva.fecha_inicio} al ${licenciaActiva.fecha_fin}</div>
                <div><strong>Días:</strong> ${licenciaActiva.dias}</div>
            </div>
            <div class="alert alert-warning mb-0">
                <small>
                    <strong><i class="bi bi-exclamation-triangle me-1"></i>¿Continuar de todos modos?</strong>
                    <p class="mb-0 mt-1">Se recomienda NO asignar personal con licencia médica. Verifique que la licencia haya finalizado o ajuste las fechas de la asignación.</p>
                </small>
            </div>
        `;
        showAlert('Personal con Licencia Médica Activa', mensaje, 'error');
        return;
    }
    
    // Validar ausentismos activos
    const ausentismoActivo = validarAusentismoActivo();
    if (ausentismoActivo.existe) {
        const mensaje = `
            <div class="mb-3">
                <i class="bi bi-calendar-x-fill text-warning" style="font-size: 2rem;"></i>
                <h6 class="mt-2 mb-1">📅 Advertencia: Personal con Permiso</h6>
                <p class="text-muted mb-0">Este personal tiene un permiso/ausentismo en el período seleccionado.</p>
            </div>
            <div class="alert alert-warning mb-3">
                <div class="mb-2"><strong>Permiso Activo:</strong></div>
                <div><strong>Tipo:</strong> ${ausentismoActivo.tipo}</div>
                <div><strong>Período:</strong> ${ausentismoActivo.fecha_inicio} al ${ausentismoActivo.fecha_fin}</div>
            </div>
            <div class="alert alert-info mb-0">
                <small>
                    <strong><i class="bi bi-info-circle me-1"></i>Recomendación:</strong>
                    <p class="mb-0 mt-1">Verifique que el permiso no coincida con días laborales importantes, o ajuste las fechas de la asignación.</p>
                </small>
            </div>
        `;
        showAlert('Personal con Permiso Activo', mensaje, 'error');
        return;
    }
    
    // Validar solapamiento de fechas (solo al crear nueva asignación)
    const asignacionId = form.querySelector('[name="asignacion_id"]').value;
    if (!asignacionId) {
        const solapamiento = validarSolapamientoFechas();
        if (solapamiento.existe) {
            const fechaInicioNueva = document.getElementById('fechaInicio').value;
            const fechaFinNueva = document.getElementById('fechaFin').value;
            const faenaIdNueva = parseInt(document.getElementById('faenaSelect').value);
            const faenaNueva = calendarioData.faenas.find(f => f.id === faenaIdNueva);
            
            const mensaje = `
                <div class="mb-3">
                    <i class="bi bi-exclamation-triangle-fill text-warning" style="font-size: 2rem;"></i>
                    <h6 class="mt-2 mb-1">⚠️ No se puede asignar: Conflicto de Fechas</h6>
                    <p class="text-muted mb-0">Esta persona ya tiene una asignación en ese período de tiempo.</p>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <div class="card border-danger">
                            <div class="card-header bg-danger text-white py-1 px-2">
                                <small><strong>❌ Asignación que Intentas Crear</strong></small>
                            </div>
                            <div class="card-body p-2">
                                <small>
                                    <div><strong>Faena:</strong> ${faenaNueva ? faenaNueva.nombre : 'N/A'}</div>
                                    <div><strong>Período:</strong></div>
                                    <div class="ms-2">${fechaInicioNueva} al ${fechaFinNueva}</div>
                                </small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card border-warning">
                            <div class="card-header bg-warning py-1 px-2">
                                <small><strong>⚠️ Asignación Existente (Conflicto)</strong></small>
                            </div>
                            <div class="card-body p-2">
                                <small>
                                    <div><strong>Faena:</strong> ${solapamiento.faena}</div>
                                    <div><strong>Turno:</strong> ${solapamiento.turno}</div>
                                    <div><strong>Período:</strong></div>
                                    <div class="ms-2">${solapamiento.fecha_inicio} al ${solapamiento.fecha_fin}</div>
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-info mb-0">
                    <small>
                        <strong><i class="bi bi-lightbulb me-1"></i>¿Cómo solucionar este conflicto?</strong>
                        <ul class="mb-0 mt-2">
                            <li>Modifica las fechas para que NO se solapen con la asignación existente</li>
                            <li>O edita/elimina la asignación existente primero</li>
                        </ul>
                    </small>
                </div>
            `;
            showAlert('Conflicto de Períodos', mensaje, 'error');
            return;
        }
    }
    
    // Deshabilitar botón mientras se procesa
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Guardando...';
    
    try {
    
    const formData = new FormData(form);
    const asignacionId = formData.get('asignacion_id');
    
    // Si NO es edición, validar que no exista ya una asignación a la misma faena
    if (!asignacionId) {
        const personalId = parseInt(formData.get('personal_id'));
        const faenaId = parseInt(formData.get('faena_id'));
        
        const asignacionesPersona = asignacionesPorPersonal[personalId] || [];
        const asignacionExistente = asignacionesPersona.find(asig => 
            asig.faena.id === faenaId && asig.activo
        );
        
        if (asignacionExistente) {
            const faena = calendarioData.faenas.find(f => f.id === faenaId);
            const turno = calendarioData.turnos.find(t => t.id === asignacionExistente.turno_id);
            
            const fechaInicio = asignacionExistente.fecha_inicio.split('T')[0];
            const fechaFin = asignacionExistente.fecha_fin ? asignacionExistente.fecha_fin.split('T')[0] : 'Indefinida';
            
            const mensaje = `
                <div class="mb-3">
                    <strong>Este personal ya tiene una asignación activa a la faena "${faena.nombre}"</strong>
                </div>
                <div class="alert alert-warning mb-0">
                    <div class="mb-2"><strong>Detalles de la asignación existente:</strong></div>
                    <div><strong>Turno:</strong> ${turno ? turno.nombre : 'Sin turno'}</div>
                    <div><strong>Período:</strong> ${fechaInicio} al ${fechaFin}</div>
                </div>
                <div class="mt-3 text-muted">
                    <small><i class="bi bi-info-circle me-1"></i>Si desea modificar esta asignación, cierre este modal y edite la asignación existente.</small>
                </div>
            `;
            
            showAlert('No se Puede Crear Asignación Duplicada', mensaje, 'error');
            return;
        }
    }
    
    const data = {
        personal_id: formData.get('personal_id'),
        faena_id: formData.get('faena_id'),
        turno_id: formData.get('turno_id'),
        fecha_inicio: formData.get('fecha_inicio'),
        fecha_fin: formData.get('fecha_fin'), // Ahora es obligatoria
        bloque_inicio_id: formData.get('bloque_inicio_id'), // Si está vacío, el backend sabrá manejarlo
        observaciones: formData.get('observaciones') || '',
        activo: true  // Siempre activo - se controla con fechas
    };
    const url = asignacionId ? '/calendario/api/actualizar-asignacion/' : '/calendario/api/crear-asignacion/';
    
    if (asignacionId) {
        data.asignacion_id = asignacionId;
    }
    
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
    } finally {
        // Rehabilitar botón siempre (en caso de error)
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = '<i class="bi bi-save me-1"></i>Guardar';
    }
}

/**
 * Elimina una asignación desde el formulario de edición.
 * Muestra un modal de confirmación antes de eliminar.
 * Si se confirma, llama a eliminarAsignacionDirecta().
 */
async function eliminarAsignacion() {
    const confirmado = await showConfirm(
        '¿Está seguro de eliminar esta asignación? Esta acción no se puede deshacer.',
        'Eliminar Asignación'
    );
    
    if (!confirmado) return;
    
    const asignacionId = document.getElementById('asignacionId').value;
    await eliminarAsignacionDirecta(asignacionId);
}

/**
 * Elimina una asignación directamente haciendo una petición AJAX al backend.
 * Puede ser llamada desde cualquier lugar (formulario, botones, etc.).
 * Muestra mensaje de éxito/error y recarga la página si es exitoso.
 * @param {number|string} asignacionId - ID de la asignación a eliminar
 */
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

