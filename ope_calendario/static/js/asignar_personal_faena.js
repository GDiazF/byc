// ============================================================================
// ASIGNAR PERSONAL A FAENA
// ============================================================================

// Variables globales (se inicializan desde el template con datos de Django)
let personal = [];
let turnos = [];
let faena = {};
let personalSeleccionados = [];
let faenaFechaInicio = null;
let faenaFechaFin = null;

// Variables de paginación
let paginaActual = 1;
let registrosPorPagina = 10;
let personalFiltrado = [];

// ============================================================================
// UTILIDADES
// ============================================================================

// Get CSRF token
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

// Formatear fecha a formato chileno (DD-MM-YYYY)
function formatearFechaChilena(fecha) {
    if (!fecha) return '';
    
    try {
        const date = new Date(fecha + 'T00:00:00'); // Agregar hora para evitar problemas de timezone
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const anio = date.getFullYear();
        return `${dia}-${mes}-${anio}`;
    } catch (error) {
        console.error('Error formateando fecha:', error);
        return fecha;
    }
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

// Renderizar tabla de personal con paginación
function renderizarTablaPersonal() {
    const tbody = document.getElementById('personalTableBody');
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    const filtroEstado = document.getElementById('filtroEstado').value;
    const filtroCargo = document.getElementById('filtroCargo').value;
    const filtroEmpresa = document.getElementById('filtroEmpresa').value;
    
    // Obtener IDs de personal ya asignado a ESTA faena
    const idsAsignadosEstaFaena = faena.asignaciones ? faena.asignaciones.map(a => a.personal.id) : [];
    
    // Filtrar personal
    personalFiltrado = personal.filter(p => {
        // NO mostrar personal ya asignado a ESTA faena
        if (idsAsignadosEstaFaena.includes(p.id)) {
            return false;
        }
        
        // Búsqueda
        const nombreCompleto = p.nombre_completo.toLowerCase();
        const rut = p.rut.toLowerCase();
        const matchBusqueda = !busqueda || nombreCompleto.includes(busqueda) || rut.includes(busqueda);
        
        // Filtro de estado
        let matchEstado = true;
        if (filtroEstado === 'disponible') {
            matchEstado = !p.tiene_asignacion;
        } else if (filtroEstado === 'asignado') {
            matchEstado = p.tiene_asignacion;
        }
        
        // Filtro de cargo
        const matchCargo = !filtroCargo || p.cargo === filtroCargo;
        
        // Filtro de empresa
        const matchEmpresa = !filtroEmpresa || p.empresa === filtroEmpresa;
        
        return matchBusqueda && matchEstado && matchCargo && matchEmpresa;
    });
    
    if (personalFiltrado.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron trabajadores con los filtros aplicados</p>
                </td>
            </tr>
        `;
        document.getElementById('paginacion').innerHTML = '';
        document.getElementById('totalRegistros').textContent = '0';
        document.getElementById('registroInicio').textContent = '0';
        document.getElementById('registroFin').textContent = '0';
        actualizarContador();
        return;
    }
    
    // Aplicar ordenamiento si existe
    if (typeof ordenAsignar !== 'undefined' && ordenAsignar.columna) {
        personalFiltrado.sort((a, b) => {
            let valorA, valorB;
            
            switch(ordenAsignar.columna) {
                case 'rut':
                    valorA = a.rut || '';
                    valorB = b.rut || '';
                    break;
                case 'cargo':
                    valorA = a.cargo || '';
                    valorB = b.cargo || '';
                    break;
                case 'empresa':
                    valorA = a.empresa || '';
                    valorB = b.empresa || '';
                    break;
                case 'nombre':
                default:
                    valorA = a.nombre_completo || '';
                    valorB = b.nombre_completo || '';
                    break;
            }
            
            const comparacion = valorA.localeCompare(valorB);
            return ordenAsignar.direccion === 'asc' ? comparacion : -comparacion;
        });
    }
    
    // Calcular paginación
    const totalPaginas = Math.ceil(personalFiltrado.length / registrosPorPagina);
    paginaActual = Math.min(paginaActual, totalPaginas); // Ajustar si estamos fuera de rango
    paginaActual = Math.max(1, paginaActual); // Mínimo página 1
    
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, personalFiltrado.length);
    const personalPagina = personalFiltrado.slice(inicio, fin);
    
    // Renderizar solo la página actual
    tbody.innerHTML = personalPagina.map(p => {
        const isChecked = personalSeleccionados.includes(p.id);
        const estadoClass = p.tiene_asignacion ? 'bg-warning' : 'bg-success';
        const estadoText = p.tiene_asignacion ? 'Asignado' : 'Disponible';
        
        // Determinar qué mostrar según el tipo de asignación
        let asignacionTexto = '-';
        let fechaAsignacion = '-';
        
        if (p.asignacion_actual) {
            if (p.asignacion_actual.tipo === 'ot') {
                // Es una OT
                asignacionTexto = `OT: ${p.asignacion_actual.folio} - ${p.asignacion_actual.equipo || 'N/A'}`;
                fechaAsignacion = `${formatearFechaChilena(p.asignacion_actual.fecha_inicio) || ''} ${p.asignacion_actual.fecha_fin ? '→ ' + formatearFechaChilena(p.asignacion_actual.fecha_fin) : '→ Indefinido'}`;
            } else {
                // Es una faena
                asignacionTexto = p.asignacion_actual.faena || '-';
                fechaAsignacion = `${formatearFechaChilena(p.asignacion_actual.fecha_inicio) || ''} ${p.asignacion_actual.fecha_fin ? '→ ' + formatearFechaChilena(p.asignacion_actual.fecha_fin) : '→ Indefinido'}`;
            }
        }
        
        // Deshabilitar checkbox si tiene asignación conflictiva
        const tieneConflicto = p.tiene_asignacion;
        const disabledAttr = tieneConflicto ? 'disabled' : '';
        const titleAttr = tieneConflicto ? 
            (p.asignacion_actual && p.asignacion_actual.tipo === 'ot' ? 
                `No se puede asignar: Tiene OT asignada` : 
                `No se puede asignar: Ya asignado a otra faena`) : 
            '';
        
        return `
            <tr class="${isChecked ? 'table-primary' : ''} ${tieneConflicto ? 'table-secondary' : ''}">
                <td class="text-center">
                    <input class="form-check-input personal-checkbox" type="checkbox" 
                           value="${p.id}" ${isChecked ? 'checked' : ''} ${disabledAttr}
                           title="${titleAttr}">
                </td>
                <td>
                    <a href="#" onclick="event.preventDefault(); showPersonalInfo(${p.id});" 
                       class="text-decoration-none text-primary fw-semibold" 
                       style="cursor: pointer;"
                       title="Ver información completa">
                        ${p.nombre_completo}
                    </a>
                </td>
                <td>${p.rut}</td>
                <td>${p.cargo}</td>
                <td>${p.empresa}</td>
                <td>
                    <span class="badge ${estadoClass}">${estadoText}</span>
                </td>
                <td>${asignacionTexto}</td>
                <td class="small">${fechaAsignacion}</td>
            </tr>
        `;
    }).join('');
    
    // Actualizar información de paginación
    document.getElementById('totalRegistros').textContent = personalFiltrado.length;
    document.getElementById('registroInicio').textContent = personalFiltrado.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    
    // Renderizar controles de paginación
    renderizarPaginacion(totalPaginas);
    
    actualizarContador();
}

// Renderizar controles de paginación
function renderizarPaginacion(totalPaginas) {
    const paginacionContainer = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacionContainer.innerHTML = '';
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
    const maxBotones = 5;
    let inicio = Math.max(1, paginaActual - Math.floor(maxBotones / 2));
    let fin = Math.min(totalPaginas, inicio + maxBotones - 1);
    
    if (fin - inicio < maxBotones - 1) {
        inicio = Math.max(1, fin - maxBotones + 1);
    }
    
    if (inicio > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a></li>`;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (fin < totalPaginas) {
        if (fin < totalPaginas - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${totalPaginas}); return false;">${totalPaginas}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionContainer.innerHTML = html;
}

// Cambiar de página
function cambiarPagina(nuevaPagina) {
    paginaActual = nuevaPagina;
    renderizarTablaPersonal();
}

// Cambiar registros por página
function cambiarRegistrosPorPagina() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1; // Volver a la primera página
    renderizarTablaPersonal();
}

// ============================================================================
// GESTIÓN DE SELECCIÓN
// ============================================================================

// Actualizar contador
function actualizarContador() {
    const total = document.querySelectorAll('.personal-checkbox:not(:disabled)').length;
    // Solo contar checkboxes seleccionados que NO estén deshabilitados
    const seleccionados = document.querySelectorAll('.personal-checkbox:checked:not(:disabled)').length;
    
    document.getElementById('totalPersonal').textContent = total;
    document.getElementById('totalSeleccionados').textContent = seleccionados;
    
    const btnAsignar = document.getElementById('btnAsignarMasivo');
    if (seleccionados > 0) {
        btnAsignar.disabled = false;
        btnAsignar.innerHTML = `<i class="bi bi-check-circle me-1"></i>Asignar ${seleccionados} Trabajador${seleccionados > 1 ? 'es' : ''}`;
    } else {
        btnAsignar.disabled = true;
        btnAsignar.innerHTML = '<i class="bi bi-check-circle me-1"></i>Asignar Personal';
    }
}

// Manejar checkbox
function onCheckboxChange(checkbox) {
    // Ignorar checkboxes deshabilitados
    if (checkbox.disabled) {
        checkbox.checked = false;
        return;
    }
    
    const id = parseInt(checkbox.value);
    if (checkbox.checked) {
        if (!personalSeleccionados.includes(id)) {
            personalSeleccionados.push(id);
        }
    } else {
        personalSeleccionados = personalSeleccionados.filter(pid => pid !== id);
    }
    renderizarTablaPersonal();
}

// Seleccionar/deseleccionar todos visibles
function toggleSeleccionarTodos() {
    // Solo considerar checkboxes que NO estén deshabilitados
    const checkboxes = document.querySelectorAll('.personal-checkbox:not(:disabled)');
    const todosSeleccionados = Array.from(checkboxes).every(cb => cb.checked);
    
    personalSeleccionados = [];
    
    if (!todosSeleccionados) {
        checkboxes.forEach(cb => {
            if (!cb.disabled) {
                const id = parseInt(cb.value);
                if (!personalSeleccionados.includes(id)) {
                    personalSeleccionados.push(id);
                }
            }
        });
    }
    
    renderizarTablaPersonal();
}

// Limpiar selección
function limpiarSeleccion() {
    personalSeleccionados = [];
    renderizarTablaPersonal();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filtroEstado').value = '';
    document.getElementById('filtroCargo').value = '';
    document.getElementById('filtroEmpresa').value = '';
    paginaActual = 1; // Resetear a página 1
    cerrarAdvertencia(); // Limpiar advertencias al cambiar filtros
    renderizarTablaPersonal();
}

// ============================================================================
// GESTIÓN DE TURNOS
// ============================================================================

// Renderizar selector de turnos
function renderizarTurnos() {
    const select = document.getElementById('turno_id');
    select.innerHTML = '<option value="">Seleccione un turno...</option>' +
        turnos.map(t => `
            <option value="${t.id}">${t.nombre} (${t.longitud_ciclo} días ciclo)</option>
        `).join('');
}

// Al seleccionar turno, mostrar bloques
function onTurnoChange() {
    const turnoId = parseInt(document.getElementById('turno_id').value);
    const container = document.getElementById('bloqueContainer');
    const select = document.getElementById('bloque_inicio_id');
    const btnInfoTurno = document.getElementById('btnInfoTurno');
    
    const iconInfoTurno = document.getElementById('iconInfoTurno');
    
    if (!turnoId) {
        container.style.display = 'none';
        btnInfoTurno.setAttribute('data-bs-content', 'Seleccione un turno para ver su información');
        iconInfoTurno.classList.remove('text-primary');
        iconInfoTurno.classList.add('text-muted');
        btnInfoTurno.style.cursor = 'not-allowed';
        // Reinicializar popover
        const popoverInstance = bootstrap.Popover.getInstance(btnInfoTurno);
        if (popoverInstance) {
            popoverInstance.dispose();
        }
        new bootstrap.Popover(btnInfoTurno, {
            html: true,
            placement: 'top',
            trigger: 'click'
        });
        return;
    }
    
    const turno = turnos.find(t => t.id === turnoId);
    if (!turno || !turno.bloques || turno.bloques.length === 0) {
        container.style.display = 'none';
        btnInfoTurno.setAttribute('data-bs-content', 'Turno sin información disponible');
        iconInfoTurno.classList.remove('text-primary');
        iconInfoTurno.classList.add('text-muted');
        btnInfoTurno.style.cursor = 'not-allowed';
        // Reinicializar popover
        const popoverInstance = bootstrap.Popover.getInstance(btnInfoTurno);
        if (popoverInstance) {
            popoverInstance.dispose();
        }
        new bootstrap.Popover(btnInfoTurno, {
            html: true,
            placement: 'top',
            trigger: 'click'
        });
        return;
    }
    
    // Construir información del turno para el popover
    let infoTurno = '<strong>Ciclo del turno:</strong><br>';
    turno.bloques.forEach(b => {
        infoTurno += `Bloque ${b.orden}: ${b.estado.nombre} (${b.duracion_dias} días) → `;
    });
    infoTurno = infoTurno.slice(0, -4); // Quitar última flecha
    infoTurno += `<br><strong>Total: ${turno.longitud_ciclo} días</strong>`;
    
    // Habilitar visualmente y actualizar popover
    btnInfoTurno.setAttribute('data-bs-content', infoTurno);
    iconInfoTurno.classList.remove('text-muted');
    iconInfoTurno.classList.add('text-primary');
    btnInfoTurno.style.cursor = 'pointer';
    
    // Reinicializar popover con HTML
    const popoverInstance = bootstrap.Popover.getInstance(btnInfoTurno);
    if (popoverInstance) {
        popoverInstance.dispose();
    }
    new bootstrap.Popover(btnInfoTurno, {
        html: true,
        placement: 'top',
        trigger: 'click'
    });
    
    container.style.display = 'block';
    select.innerHTML = '<option value="">Desde el inicio del ciclo</option>' +
        turno.bloques.map(b => `
            <option value="${b.id}">
                Iniciar en Bloque ${b.orden}: ${b.estado.nombre} (${b.duracion_dias} días)
            </option>
        `).join('');
}

// Al seleccionar estado manual, mostrar información
function onEstadoManualChange() {
    const estadoId = parseInt(document.getElementById('estadoManualSelect').value);
    const btnInfoEstadoManual = document.getElementById('btnInfoEstadoManual');
    const iconInfoEstadoManual = document.getElementById('iconInfoEstadoManual');
    
    if (!estadoId) {
        btnInfoEstadoManual.setAttribute('data-bs-content', 'Seleccione un estado para ver su información');
        iconInfoEstadoManual.classList.remove('text-primary');
        iconInfoEstadoManual.classList.add('text-muted');
        btnInfoEstadoManual.style.cursor = 'not-allowed';
        // Reinicializar popover
        const popoverInstance = bootstrap.Popover.getInstance(btnInfoEstadoManual);
        if (popoverInstance) {
            popoverInstance.dispose();
        }
        new bootstrap.Popover(btnInfoEstadoManual, {
            html: true,
            placement: 'top',
            trigger: 'click'
        });
        return;
    }
    
    // Obtener información del estado desde el option seleccionado
    const selectEstado = document.getElementById('estadoManualSelect');
    const optionSeleccionado = selectEstado.options[selectEstado.selectedIndex];
    
    const nombre = optionSeleccionado.getAttribute('data-nombre') || 'N/A';
    const nombreCorto = optionSeleccionado.getAttribute('data-nombre-corto') || 'N/A';
    const color = optionSeleccionado.getAttribute('data-color') || '#000000';
    const backgroundColor = optionSeleccionado.getAttribute('data-background-color') || '#FFFFFF';
    const prioridad = optionSeleccionado.getAttribute('data-prioridad') || '10';
    const bloqueante = optionSeleccionado.getAttribute('data-bloqueante') || 'No';
    const predeterminado = optionSeleccionado.getAttribute('data-predeterminado') || 'No';
    
    // Construir información del estado para el popover
    let infoEstado = `<strong>Información del Estado:</strong><br>`;
    infoEstado += `<strong>Nombre:</strong> ${nombre}<br>`;
    if (nombreCorto && nombreCorto !== 'N/A') {
        infoEstado += `<strong>Nombre corto:</strong> ${nombreCorto}<br>`;
    }
    infoEstado += `<strong>Prioridad:</strong> ${prioridad}<br>`;
    infoEstado += `<strong>Es bloqueante:</strong> ${bloqueante}<br>`;
    infoEstado += `<strong>Es predeterminado:</strong> ${predeterminado}<br>`;
    infoEstado += `<strong>Color texto:</strong> <span style="color: ${color};">●</span> ${color}<br>`;
    infoEstado += `<strong>Color fondo:</strong> <span style="background-color: ${backgroundColor}; padding: 2px 8px; border-radius: 3px;">&nbsp;&nbsp;</span> ${backgroundColor}`;
    
    // Habilitar visualmente y actualizar popover
    btnInfoEstadoManual.setAttribute('data-bs-content', infoEstado);
    iconInfoEstadoManual.classList.remove('text-muted');
    iconInfoEstadoManual.classList.add('text-primary');
    btnInfoEstadoManual.style.cursor = 'pointer';
    
    // Reinicializar popover con HTML
    const popoverInstance = bootstrap.Popover.getInstance(btnInfoEstadoManual);
    if (popoverInstance) {
        popoverInstance.dispose();
    }
    new bootstrap.Popover(btnInfoEstadoManual, {
        html: true,
        placement: 'top',
        trigger: 'click'
    });
}

// ============================================================================
// ASIGNACIÓN MASIVA
// ============================================================================

// Asignar masivamente
async function asignarMasivo() {
    const turnoId = document.getElementById('turno_id').value;
    const fechaInicio = document.getElementById('fecha_inicio').value;
    const fechaFin = document.getElementById('fecha_fin').value;
    const bloqueInicioId = document.getElementById('bloque_inicio_id').value;
    const observaciones = document.getElementById('observaciones').value.trim();
    
    // Validaciones básicas
    if (personalSeleccionados.length === 0) {
        mostrarModal('Error de Validación', 'Debe seleccionar al menos un trabajador para asignar.', 'error');
        return;
    }
    
    if (!turnoId) {
        mostrarModal('Error de Validación', 'Debe seleccionar un turno.', 'error');
        return;
    }
    
    if (!fechaInicio) {
        mostrarModal('Error de Validación', 'Debe indicar una fecha de inicio.', 'error');
        return;
    }
    
    // Validar que la fecha de inicio no sea anterior al inicio de la faena
    if (faenaFechaInicio && fechaInicio < faenaFechaInicio) {
        mostrarModal(
            'Error de Validación',
            `La fecha de inicio de asignación (${formatearFechaChilena(fechaInicio)}) no puede ser anterior al inicio de la faena (${formatearFechaChilena(faenaFechaInicio)}).`,
            'error'
        );
        return;
    }
    
    // Validar que la fecha de fin no sea posterior al fin de la faena
    if (faenaFechaFin && fechaFin && fechaFin > faenaFechaFin) {
        mostrarModal(
            'Error de Validación',
            `La fecha de fin de asignación (${formatearFechaChilena(fechaFin)}) no puede ser posterior al fin de la faena (${formatearFechaChilena(faenaFechaFin)}).`,
            'error'
        );
        return;
    }
    
    // Validar que la fecha de fin sea posterior a la fecha de inicio
    if (fechaFin && fechaFin < fechaInicio) {
        mostrarModal(
            'Error de Validación',
            `La fecha de fin (${formatearFechaChilena(fechaFin)}) debe ser posterior a la fecha de inicio (${formatearFechaChilena(fechaInicio)}).`,
            'error'
        );
        return;
    }
    
    const data = {
        personal_ids: personalSeleccionados,
        faena_id: faena.id,
        turno_id: parseInt(turnoId),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin || null,
        bloque_inicio_id: bloqueInicioId ? parseInt(bloqueInicioId) : null,
        observaciones: observaciones
    };
    
    try {
        const response = await fetch('/calendario/api/crear-asignacion-masiva/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Si hay errores parciales, mostrar advertencia persistente
            if (result.warning && result.errores && result.errores.length > 0) {
                mostrarAdvertenciaPersistente(result.total_asignados, result.total_errores, result.errores);
                
                // También mostrar alerta flotante de éxito parcial
                if (result.total_asignados > 0) {
            mostrarAlerta(result.message, 'success');
                }
                
                // NO recargar completamente, pero actualizar datos
                // Limpiar selección
                personalSeleccionados = [];
                
                // Recargar página para obtener datos actualizados pero mantener la advertencia visible
                // Usar sessionStorage para mostrar la advertencia después de recargar
                sessionStorage.setItem('advertenciaAsignacion', JSON.stringify({
                    totalAsignados: result.total_asignados,
                    totalErrores: result.total_errores,
                    errores: result.errores
                }));
                
                // Recargar en el tab de asignar (no gestionar) para que vean la advertencia
            setTimeout(() => {
                    window.location.reload();
                }, 1500);
                
            } else {
                // Asignación completamente exitosa
                mostrarAlerta(result.message, 'success');
                
                // Recargar la página con el hash para activar el tab de gestión
                setTimeout(() => {
                    window.location.hash = '#gestionar';
                    window.location.reload();
                }, 1500);
            }
        } else {
            // Error total
            if (result.errores && result.errores.length > 0) {
                mostrarAdvertenciaPersistente(0, result.total_errores, result.errores);
        } else {
            mostrarAlerta(result.error || 'Error al asignar personal', 'error');
            }
        }
    } catch (error) {
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}

// ============================================================================
// NOTIFICACIONES
// ============================================================================

// Mostrar notificación flotante estilo RRHH
function mostrarAlerta(mensaje, tipo) {
    // Crear contenedor de alertas flotantes si no existe
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
            // Si no hay más alertas, remover el contenedor
            if (container.children.length === 0) {
                container.remove();
            }
        }, 150);
    }, 5000);
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

// Inicializar variables desde el template (se llama desde el HTML)
function initData(personalData, turnosData, faenaData, fechaInicio, fechaFin) {
    personal = personalData;
    turnos = turnosData;
    faena = faenaData;
    faenaFechaInicio = fechaInicio;
    faenaFechaFin = fechaFin;
}

// ============================================================================
// GESTIÓN DE PERSONAL ASIGNADO
// ============================================================================

// Variables globales para filtrado de personal asignado
let asignacionesFiltradas = [];

// Renderizar tabla de personal asignado
function renderizarPersonalAsignado() {
    const tbody = document.getElementById('tablaPersonalAsignadoBody');
    
    if (!faena.asignaciones || faena.asignaciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No hay personal asignado a esta faena</p>
                    <button class="btn btn-primary" onclick="document.getElementById('asignar-tab').click()">
                        <i class="bi bi-person-plus me-1"></i>Asignar Personal
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    // Aplicar filtros si existen
    asignacionesFiltradas = filtrarPersonalAsignado(false);
    
    if (asignacionesFiltradas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron trabajadores con los filtros aplicados</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = asignacionesFiltradas.map(asig => {
        // Determinar estado
        let estadoBadge = '';
        if (asig.fecha_fin) {
            const hoy = new Date();
            hoy.setHours(0, 0, 0, 0);
            const fechaFin = new Date(asig.fecha_fin + 'T00:00:00');
            if (fechaFin < hoy) {
                estadoBadge = '<span class="badge bg-secondary">Finalizado</span>';
            } else {
                estadoBadge = '<span class="badge bg-success">Activo</span>';
            }
        } else {
            estadoBadge = '<span class="badge bg-success">Activo</span>';
        }
        
        return `
            <tr>
                <td>
                    <a href="#" onclick="event.preventDefault(); showPersonalInfo(${asig.personal.id});" 
                       class="text-decoration-none text-primary fw-semibold" 
                       style="cursor: pointer;"
                       title="Ver información completa">
                        ${asig.personal.nombre}
                    </a>
                </td>
                <td class="text-muted small">${asig.personal.rut}</td>
                <td>${asig.personal.cargo}</td>
                <td>${asig.personal.empresa}</td>
                <td><span class="badge bg-primary" style="font-size: 0.75rem;">${asig.turno.nombre}</span></td>
                <td>${asig.bloque_inicio ? `Bloque ${asig.bloque_inicio.orden}` : '-'}</td>
                <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : '<span class="badge bg-info">Indefinida</span>'}</td>
                <td class="text-center">${estadoBadge}</td>
                <td class="text-center">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-sm btn-secondary" onclick="editarAsignacionDirecta(${asig.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarAsignacionDirecta(${asig.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Filtrar personal asignado
function filtrarPersonalAsignado(rerender = true) {
    if (!faena.asignaciones || faena.asignaciones.length === 0) {
        return [];
    }
    
    const busqueda = document.getElementById('searchAsignadosInput')?.value.toLowerCase() || '';
    const filtroCargo = document.getElementById('filtroCargoAsignados')?.value || '';
    const filtroEmpresa = document.getElementById('filtroEmpresaAsignados')?.value || '';
    
    const filtradas = faena.asignaciones.filter(asig => {
        // Búsqueda por nombre o RUT
        const nombreCompleto = asig.personal.nombre.toLowerCase();
        const rut = asig.personal.rut.toLowerCase();
        const matchBusqueda = !busqueda || nombreCompleto.includes(busqueda) || rut.includes(busqueda);
        
        // Filtro de cargo
        const matchCargo = !filtroCargo || asig.personal.cargo === filtroCargo;
        
        // Filtro de empresa
        const matchEmpresa = !filtroEmpresa || asig.personal.empresa === filtroEmpresa;
        
        return matchBusqueda && matchCargo && matchEmpresa;
    });
    
    if (rerender) {
        renderizarPersonalAsignado();
    }
    
    return filtradas;
}

// Limpiar filtros de personal asignado
function limpiarFiltrosAsignados() {
    document.getElementById('searchAsignadosInput').value = '';
    document.getElementById('filtroCargoAsignados').value = '';
    document.getElementById('filtroEmpresaAsignados').value = '';
    renderizarPersonalAsignado();
}

// Editar asignación individual
function editarAsignacionDirecta(asignacionId) {
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) {
        console.error('Asignación no encontrada:', asignacionId);
        mostrarAlerta('Error: Asignación no encontrada', 'error');
        return;
    }
    
    // Limpiar alertas
    const alertContainer = document.getElementById('alertEditAsignacion');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    // Llenar datos
    document.getElementById('editAsig_id').value = asignacion.id;
    document.getElementById('editAsig_nombreTrabajador').textContent = asignacion.personal.nombre;
    
    // Llenar turnos
    const selectTurno = document.getElementById('editAsig_turno');
    selectTurno.innerHTML = '<option value="">Seleccione un turno...</option>';
    turnos.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.nombre;
        if (t.id === asignacion.turno.id) opt.selected = true;
        selectTurno.appendChild(opt);
    });
    
    // Cargar bloques
    cargarBloquesEdicion();
    
    // Seleccionar bloque si existe
    if (asignacion.bloque_inicio) {
        setTimeout(() => {
            document.getElementById('editAsig_bloque').value = asignacion.bloque_inicio.id;
        }, 100);
    }
    
    // Llenar fechas y observaciones
    if (window.DatePickerChile) {
        DatePickerChile.setValor('editAsig_fechaInicio', asignacion.fecha_inicio);
        if (asignacion.fecha_fin) {
            DatePickerChile.setValor('editAsig_fechaFin', asignacion.fecha_fin);
        } else {
            DatePickerChile.limpiar('editAsig_fechaFin');
        }
    }
    document.getElementById('editAsig_obs').value = asignacion.observaciones || '';
    
    // Abrir modal
    const modalElement = document.getElementById('modalEditarAsignacionIndividual');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Cargar bloques del turno en edición
function cargarBloquesEdicion() {
    const turnoId = parseInt(document.getElementById('editAsig_turno').value);
    const selectBloque = document.getElementById('editAsig_bloque');
    const bloqueContainer = document.getElementById('editAsig_bloqueContainer');
    
    if (!turnoId) {
        bloqueContainer.style.display = 'none';
        return;
    }
    
    const turno = turnos.find(t => t.id === turnoId);
    if (!turno || !turno.bloques || turno.bloques.length === 0) {
        bloqueContainer.style.display = 'none';
        return;
    }
    
    bloqueContainer.style.display = 'block';
    selectBloque.innerHTML = '<option value="">Desde el inicio del ciclo</option>';
    
    turno.bloques.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.id;
        opt.textContent = `Bloque ${b.orden} - ${b.estado.nombre} (${b.duracion_dias} días)`;
        selectBloque.appendChild(opt);
    });
}

// Guardar edición de asignación
async function guardarEdicionAsignacion(event) {
    event.preventDefault();
    
    const id = document.getElementById('editAsig_id').value;
    const turnoId = document.getElementById('editAsig_turno').value;
    const bloqueId = document.getElementById('editAsig_bloque').value;
    const fechaInicio = document.getElementById('editAsig_fechaInicio').value;
    const fechaFin = document.getElementById('editAsig_fechaFin').value;
    const obs = document.getElementById('editAsig_obs').value;
    
    // Validación 1: Fecha fin debe ser posterior a fecha inicio
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
        mostrarAlertaEnModal('La fecha de fin debe ser posterior a la fecha de inicio', 'error', 'alertEditAsignacion');
        return;
    }
    
    // Validación 2: Fecha inicio de asignación no puede ser antes del inicio de la faena
    if (faenaFechaInicio && fechaInicio && fechaInicio < faenaFechaInicio) {
        mostrarAlertaEnModal(`La fecha de inicio no puede ser anterior al inicio de la faena (${formatearFechaChilena(faenaFechaInicio)})`, 'error', 'alertEditAsignacion');
        return;
    }
    
    // Validación 3: Fecha fin de asignación no puede ser posterior al fin de la faena (si la faena tiene fin)
    if (faenaFechaFin && fechaFin && fechaFin > faenaFechaFin) {
        mostrarAlertaEnModal(`La fecha de fin no puede ser posterior al fin de la faena (${formatearFechaChilena(faenaFechaFin)})`, 'error', 'alertEditAsignacion');
        return;
    }
    
    try {
        const response = await fetch('/calendario/api/actualizar-asignacion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                asignacion_id: parseInt(id),
                faena_id: faena.id,
                turno_id: parseInt(turnoId),
                bloque_inicio_id: bloqueId ? parseInt(bloqueId) : null,
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin || null,
                observaciones: obs,
                activo: true
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Cerrar modal
            const modalElement = document.getElementById('modalEditarAsignacionIndividual');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar mensaje de éxito flotante
            mostrarAlerta(result.message, 'success');
            
            // Actualizar los datos localmente
            const asignacion = faena.asignaciones.find(a => a.id === parseInt(id));
            if (asignacion) {
                const turnoObj = turnos.find(t => t.id === parseInt(turnoId));
                const bloqueObj = bloqueId && turnoObj ? turnoObj.bloques.find(b => b.id === parseInt(bloqueId)) : null;
                
                asignacion.turno = { id: parseInt(turnoId), nombre: turnoObj.nombre };
                asignacion.bloque_inicio = bloqueObj;
                asignacion.fecha_inicio = fechaInicio;
                asignacion.fecha_fin = fechaFin || null;
                asignacion.observaciones = obs;
            }
            
            // Re-renderizar la tabla dinámicamente
            renderizarPersonalAsignado();
        } else {
            mostrarAlertaEnModal(result.error || 'Error al actualizar', 'error', 'alertEditAsignacion');
        }
    } catch (error) {
        mostrarAlertaEnModal('Error de conexión: ' + error.message, 'error', 'alertEditAsignacion');
    }
}

// Mostrar alerta en modal específico
function mostrarAlertaEnModal(mensaje, tipo, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Contenedor de alerta no encontrado:', containerId);
        return;
    }
    
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    
    container.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show">
            <i class="bi ${iconClass} me-2"></i>${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// Variable para guardar el ID de la asignación a eliminar
let asignacionAEliminar = null;

// Mostrar modal de confirmación para eliminar
function eliminarAsignacionDirecta(asignacionId) {
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) return;
    
    // Guardar ID para usar en la confirmación
    asignacionAEliminar = asignacionId;
    
    // Mostrar nombre del trabajador en el modal
    document.getElementById('confirmarEliminar_nombreTrabajador').textContent = asignacion.personal.nombre;
    
    // Configurar botón de confirmar
    document.getElementById('btnConfirmarEliminar').onclick = confirmarEliminacion;
    
    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminar'));
    modal.show();
}

// Confirmar y ejecutar eliminación
async function confirmarEliminacion() {
    if (!asignacionAEliminar) return;
    
    // Cerrar modal de confirmación
    const modalElement = document.getElementById('modalConfirmarEliminar');
    const modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) {
        modalInstance.hide();
    }
    
    try {
        const response = await fetch('/calendario/api/eliminar-asignacion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ asignacion_id: asignacionAEliminar })
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarAlerta(result.message, 'success');
            
            // Eliminar de los datos locales
            const index = faena.asignaciones.findIndex(a => a.id === asignacionAEliminar);
            if (index !== -1) {
                faena.asignaciones.splice(index, 1);
            }
            
            // Re-renderizar la tabla dinámicamente
            renderizarPersonalAsignado();
            
            // Limpiar variable
            asignacionAEliminar = null;
        } else {
            mostrarAlerta(result.error || 'Error al eliminar la asignación', 'error');
        }
    } catch (error) {
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
    renderizarTablaPersonal();
    renderizarTurnos();
    renderizarPersonalAsignado();
    
    // Verificar si hay una advertencia guardada en sessionStorage
    const advertenciaGuardada = sessionStorage.getItem('advertenciaAsignacion');
    if (advertenciaGuardada) {
        try {
            const datos = JSON.parse(advertenciaGuardada);
            mostrarAdvertenciaPersistente(datos.totalAsignados, datos.totalErrores, datos.errores);
            sessionStorage.removeItem('advertenciaAsignacion'); // Limpiar después de mostrar
        } catch (e) {
            console.error('Error al restaurar advertencia:', e);
        }
    }
    
    // Pre-llenar fechas de la faena usando el componente DatePickerChile
    // Esperar a que los date pickers estén completamente inicializados
    setTimeout(() => {
        if (window.DatePickerChile) {
            if (faenaFechaInicio) {
                // Asignar Personal
                DatePickerChile.setValor('fecha_inicio', faenaFechaInicio);
                
                // Asignar Turno Manual
                DatePickerChile.setValor('fechaInicioManual', faenaFechaInicio);
            }
            
            if (faenaFechaFin) {
                // Asignar Personal
                DatePickerChile.setValor('fecha_fin', faenaFechaFin);
                
                // Asignar Turno Manual
                DatePickerChile.setValor('fechaFinManual', faenaFechaFin);
            }
        }
    }, 500);
    
    // Event listeners - resetear paginación cuando se filtran datos
    document.getElementById('searchInput').addEventListener('input', function() {
        paginaActual = 1;
        renderizarTablaPersonal();
    });
    document.getElementById('filtroEstado').addEventListener('change', function() {
        paginaActual = 1;
        renderizarTablaPersonal();
    });
    document.getElementById('filtroCargo').addEventListener('change', function() {
        paginaActual = 1;
        renderizarTablaPersonal();
    });
    document.getElementById('filtroEmpresa').addEventListener('change', function() {
        paginaActual = 1;
        renderizarTablaPersonal();
    });
    document.getElementById('turno_id').addEventListener('change', onTurnoChange);
    
    // Inicializar popover del botón de información del turno
    const btnInfoTurno = document.getElementById('btnInfoTurno');
    if (btnInfoTurno) {
        new bootstrap.Popover(btnInfoTurno, {
            html: true,
            placement: 'top',
            trigger: 'click'
        });
    }
    
    // Inicializar popover del botón de información del estado manual
    const btnInfoEstadoManual = document.getElementById('btnInfoEstadoManual');
    if (btnInfoEstadoManual) {
        new bootstrap.Popover(btnInfoEstadoManual, {
            html: true,
            placement: 'top',
            trigger: 'click'
        });
        
        // Event listener para cuando cambie el select de estado
        document.getElementById('estadoManualSelect').addEventListener('change', onEstadoManualChange);
    }
    
    // Checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('personal-checkbox')) {
            // No permitir cambiar checkboxes deshabilitados (con conflictos)
            if (e.target.disabled) {
                e.target.checked = false;
                return;
            }
            onCheckboxChange(e.target);
        }
    });
    
    // Event listener para cambio de tab
    document.getElementById('gestionar-tab').addEventListener('shown.bs.tab', function() {
        renderizarPersonalAsignado();
    });
    
    // Si la URL tiene un hash, activar el tab correspondiente
    const hash = window.location.hash;
    if (hash === '#gestionar') {
        const tabElement = document.getElementById('gestionar-tab');
        const tab = new bootstrap.Tab(tabElement);
        tab.show();
    } else if (hash === '#asignar-manual') {
        const tabElement = document.getElementById('asignar-manual-tab');
        const tab = new bootstrap.Tab(tabElement);
        tab.show();
    } else if (hash === '#estados-manuales') {
        const tabElement = document.getElementById('estados-manuales-tab');
        const tab = new bootstrap.Tab(tabElement);
        tab.show();
    }
    
});

// ============================================================================
// ADVERTENCIAS Y MENSAJES
// ============================================================================

// Mostrar advertencia persistente en el cuerpo de la página
function mostrarAdvertenciaPersistente(totalAsignados, totalErrores, errores) {
    // Detectar el contenedor correcto según el tab activo
    const hash = window.location.hash;
    let container;
    
    if (hash === '#asignar-manual') {
        container = document.getElementById('areaAdvertenciasManual');
    } else {
        container = document.getElementById('areaAdvertencias');
    }
    
    if (!container) {
        console.error('No se encontró el contenedor de advertencias');
        return;
    }
    
    let cardClass = 'border-warning';
    let headerClass = 'bg-warning text-dark';
    let icon = 'bi-exclamation-triangle-fill';
    let titulo = 'Asignación Parcial - Conflictos Detectados';
    let btnCloseClass = '';
    
    if (totalAsignados === 0) {
        cardClass = 'border-danger';
        headerClass = 'bg-danger text-white';
        icon = 'bi-x-circle-fill';
        titulo = 'Error en Asignación';
        btnCloseClass = 'btn-close-white';
    }
    
    let html = `
        <div class="card ${cardClass}">
            <div class="card-header ${headerClass}">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="bi ${icon} me-2"></i>${titulo}
                    </h6>
                    <button type="button" class="btn-close ${btnCloseClass}" onclick="cerrarAdvertencia()"></button>
                </div>
            </div>
            <div class="card-body">
                ${totalAsignados > 0 ? `
                    <div class="card border-success mb-3">
                        <div class="card-body bg-success bg-opacity-10">
                            <i class="bi bi-check-circle me-2 text-success"></i>
                            <strong>${totalAsignados}</strong> trabajador${totalAsignados > 1 ? 'es fueron asignados' : ' fue asignado'} correctamente.
                        </div>
                    </div>
                ` : ''}
                
                <div class="card border-danger mb-0">
                    <div class="card-body bg-danger bg-opacity-10">
                        <h6 class="mb-2">
                            <i class="bi bi-exclamation-triangle me-2 text-danger"></i>
                            ${totalErrores} trabajador${totalErrores > 1 ? 'es NO pudieron' : ' NO pudo'} ser asignado${totalErrores > 1 ? 's' : ''} debido a conflictos:
                        </h6>
                        <ul class="mb-2 small">
                            ${errores.map(error => `<li>${error}</li>`).join('')}
                        </ul>
                        ${totalAsignados > 0 ? `
                            <hr>
                            <p class="mb-0 small">
                                <strong>Sugerencia:</strong> Para asignar estos trabajadores, primero debe eliminar o ajustar las fechas de sus asignaciones conflictivas visitando la pestaña "Gestionar Personal Asignado" de las faenas correspondientes.
                            </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    container.style.display = 'block';
    
    // Scroll al inicio de la página para ver la advertencia
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Cerrar advertencia persistente
function cerrarAdvertencia() {
    // Cerrar ambos contenedores de advertencias
    const container1 = document.getElementById('areaAdvertencias');
    const container2 = document.getElementById('areaAdvertenciasManual');
    
    if (container1) {
        container1.style.display = 'none';
        container1.innerHTML = '';
    }
    
    if (container2) {
        container2.style.display = 'none';
        container2.innerHTML = '';
    }
}

// ============================================================================
// UTILIDADES DE MODAL
// ============================================================================

// Mostrar modal de mensaje/validación
function mostrarModal(titulo, mensaje, tipo = 'info') {
    const modal = document.getElementById('modalMensaje');
    const header = document.getElementById('modalMensajeHeader');
    const tituloEl = document.getElementById('modalMensajeTitulo');
    const contenidoEl = document.getElementById('modalMensajeContenido');
    
    // Configurar colores según tipo
    let bgClass = 'bg-primary';
    let icon = 'bi-info-circle';
    
    if (tipo === 'error') {
        bgClass = 'bg-danger';
        icon = 'bi-exclamation-triangle';
    } else if (tipo === 'warning') {
        bgClass = 'bg-warning';
        icon = 'bi-exclamation-circle';
    } else if (tipo === 'success') {
        bgClass = 'bg-success';
        icon = 'bi-check-circle';
    }
    
    // Actualizar modal
    header.className = `modal-header ${bgClass} text-white`;
    tituloEl.innerHTML = `<i class="bi ${icon} me-2"></i>${titulo}`;
    contenidoEl.innerHTML = mensaje;
    
    // Mostrar modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// ============================================================================
// MODAL DE INFORMACIÓN PERSONAL
// ============================================================================

/**
 * Muestra el modal con información completa del personal
 * @param {number} personalId - ID del personal
 */
async function showPersonalInfo(personalId) {
    // Mostrar modal con spinner
    const modal = new bootstrap.Modal(document.getElementById('personalModal'));
    modal.show();
    
    try {
        // Llamar a la API para obtener información completa
        const response = await fetch(`/calendario/api/personal/${personalId}/info/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
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
        
        // Construir HTML del modal (igual que en calendario_mensual.js)
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
        
        // Tabs para documentación (igual que en calendario_mensual.js)
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
 * Genera tabla de licencias de conducir
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
 * Genera tabla de licencias internas
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
 * Genera tabla de certificaciones
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
 * Genera tabla de exámenes médicos
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

// ============================================================================
// CALENDARIO DE FAENA - VISTA GANTT/TIMELINE
// ============================================================================

let ganttPersonalData = [];
let ganttPersonalFiltrado = [];
let ganttTurnos = {};
let ganttColoresTurno = [
    '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
    '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0'
];

// Inicializar el calendario cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // Detectar cuando se cambia al tab de calendario
    const calendarioTab = document.getElementById('calendario-tab');
    if (calendarioTab) {
        calendarioTab.addEventListener('shown.bs.tab', async function () {
            await cargarDatosGantt();
        });
    }
});

// Cargar datos para el Gantt
async function cargarDatosGantt() {
    try {
        // Cargar personal de la faena
        const personalResponse = await fetch(`/calendario/api/personal-faena/${faena.id}/`);
        if (personalResponse.ok) {
            const personalData = await personalResponse.json();
            procesarDatosGantt(personalData.personal || []);
            renderizarGantt();
        }
    } catch (error) {
        console.error('Error al cargar datos del Gantt:', error);
        mostrarAlerta('Error al cargar el calendario', 'error');
    }
}

// Procesar datos para el Gantt
function procesarDatosGantt(personalArray) {
    ganttPersonalData = [];
    ganttTurnos = {};
    let turnoIndex = 0;
    
    personalArray.forEach(persona => {
        persona.asignaciones.forEach(asig => {
            const turnoId = asig.turno.id;
            const turnoNombre = asig.turno.nombre;
            
            // Asignar color al turno si no existe
            if (!ganttTurnos[turnoId]) {
                ganttTurnos[turnoId] = {
                    id: turnoId,
                    nombre: turnoNombre,
                    color: ganttColoresTurno[turnoIndex % ganttColoresTurno.length]
                };
                turnoIndex++;
            }
            
            ganttPersonalData.push({
                personal_id: persona.personal_id,
                nombre: persona.nombre,
                apepat: persona.apepat,
                apemat: persona.apemat,
                rut: persona.rut,
                dvrut: persona.dvrut,
                cargo: persona.cargo,
                turno_id: turnoId,
                turno_nombre: turnoNombre,
                turno_color: ganttTurnos[turnoId].color,
                fecha_inicio: asig.fecha_inicio,
                fecha_fin: asig.fecha_fin,
                asignacion_id: asig.id
            });
        });
    });
    
    ganttPersonalFiltrado = [...ganttPersonalData];
    
    // Llenar selector de turnos
    llenarFiltroTurnos();
    
    // Renderizar leyenda de turnos
    renderizarLeyendaTurnos();
    
    // Actualizar badges
    const totalTurnos = Object.keys(ganttTurnos).length;
    const totalPersonalUnico = new Set(ganttPersonalData.map(p => p.personal_id)).size;
    
    document.getElementById('totalTurnosGantt').textContent = totalTurnos;
    document.getElementById('totalPersonalGantt').textContent = totalPersonalUnico;
}

// Llenar filtro de turnos
function llenarFiltroTurnos() {
    const selectTurno = document.getElementById('filtroTurnoGantt');
    if (!selectTurno) return;
    
    let html = '<option value="">Todos los turnos</option>';
    Object.values(ganttTurnos).forEach(turno => {
        html += `<option value="${turno.id}">${turno.nombre}</option>`;
    });
    
    selectTurno.innerHTML = html;
}

// Renderizar leyenda de turnos
function renderizarLeyendaTurnos() {
    const legendContainer = document.getElementById('leyendaTurnosGantt');
    if (!legendContainer) return;
    
    let html = '<small class="me-2 fw-bold">Turnos:</small>';
    
    Object.values(ganttTurnos).forEach(turno => {
        html += `
            <div style="display: inline-flex; align-items: center; margin-right: 15px; margin-bottom: 5px;">
                <div style="
                    background-color: ${turno.color};
                    width: 20px;
                    height: 20px;
                    border-radius: 3px;
                    margin-right: 5px;
                "></div>
                <small>${turno.nombre}</small>
            </div>
        `;
    });
    
    legendContainer.innerHTML = html;
}

// Aplicar filtros
function aplicarFiltrosGantt() {
    const filtroTurno = document.getElementById('filtroTurnoGantt').value;
    const busqueda = document.getElementById('buscarPersonalGantt').value.toLowerCase();
    const orden = document.getElementById('ordenGantt').value;
    
    // Filtrar
    ganttPersonalFiltrado = ganttPersonalData.filter(p => {
        const matchTurno = !filtroTurno || p.turno_id == filtroTurno;
        const nombreCompleto = `${p.nombre} ${p.apepat} ${p.apemat}`.toLowerCase();
        const rutCompleto = `${p.rut}-${p.dvrut}`.toLowerCase();
        const matchBusqueda = !busqueda || nombreCompleto.includes(busqueda) || rutCompleto.includes(busqueda);
        
        return matchTurno && matchBusqueda;
    });
    
    // Ordenar
    ganttPersonalFiltrado.sort((a, b) => {
        if (orden === 'nombre') {
            return `${a.apepat} ${a.apemat} ${a.nombre}`.localeCompare(`${b.apepat} ${b.apemat} ${b.nombre}`);
        } else if (orden === 'turno') {
            return a.turno_nombre.localeCompare(b.turno_nombre);
        } else if (orden === 'fecha_inicio') {
            return new Date(a.fecha_inicio) - new Date(b.fecha_inicio);
        }
        return 0;
    });
    
    renderizarGantt();
}

// Limpiar filtros
function limpiarFiltrosGantt() {
    document.getElementById('filtroTurnoGantt').value = '';
    document.getElementById('buscarPersonalGantt').value = '';
    document.getElementById('ordenGantt').value = 'nombre';
    aplicarFiltrosGantt();
}

// Renderizar Gantt
function renderizarGantt() {
    const container = document.getElementById('ganttContainer');
    const mensajeSinPersonal = document.getElementById('mensajeSinPersonalGantt');
    
    if (!container) return;
    
    if (ganttPersonalFiltrado.length === 0) {
        container.innerHTML = '';
        mensajeSinPersonal.style.display = 'block';
        return;
    }
    
    mensajeSinPersonal.style.display = 'none';
    
    // Calcular rango de fechas
    const rangoFechas = calcularRangoFechasGantt();
    
    // Generar tabla Gantt
    let html = '<table class="gantt-table">';
    
    // Header con dos filas si es por días
    html += '<thead class="gantt-header">';
    
    if (!rangoFechas.usar_semanas) {
        // Primera fila: meses
        html += '<tr>';
        html += '<th class="gantt-name-col" rowspan="2">Personal</th>';
        
        let mesActual = -1;
        let colspan = 0;
        rangoFechas.periodos.forEach((periodo, idx) => {
            const mes = periodo.fecha_inicio.getMonth();
            if (mes !== mesActual) {
                if (colspan > 0) {
                    const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
                    html += `<th colspan="${colspan}" style="border: 1px solid #495057; background: #212529;">${meses[mesActual]} ${rangoFechas.periodos[idx - 1].fecha_inicio.getFullYear()}</th>`;
                }
                mesActual = mes;
                colspan = 1;
            } else {
                colspan++;
            }
        });
        // Último mes
        if (colspan > 0) {
            const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
            html += `<th colspan="${colspan}" style="border: 1px solid #495057; background: #212529;">${meses[mesActual]} ${rangoFechas.periodos[rangoFechas.periodos.length - 1].fecha_inicio.getFullYear()}</th>`;
        }
        html += '</tr>';
        
        // Segunda fila: días
        html += '<tr>';
        rangoFechas.periodos.forEach(periodo => {
            const esHoy = periodo.incluye_hoy;
            const esDomingo = periodo.fecha_inicio.getDay() === 0;
            html += `<th class="gantt-cell ${esHoy ? 'gantt-today' : ''}" style="${esDomingo ? 'background: #495057;' : ''}">${periodo.label}</th>`;
        });
        html += '</tr>';
    } else {
        // Una sola fila para semanas
        html += '<tr>';
        html += '<th class="gantt-name-col">Personal</th>';
        
        rangoFechas.periodos.forEach(periodo => {
            const esHoy = periodo.incluye_hoy;
            html += `<th class="gantt-cell ${esHoy ? 'gantt-today' : ''}">${periodo.label}</th>`;
        });
        
        html += '</tr>';
    }
    
    html += '</thead>';
    
    // Body
    html += '<tbody>';
    
    ganttPersonalFiltrado.forEach(persona => {
        html += '<tr class="gantt-row">';
        
        // Columna de nombre
        const nombreCompleto = `${persona.nombre} ${persona.apepat} ${persona.apemat}`;
        const rutCompleto = `${persona.rut}-${persona.dvrut}`;
        html += `
            <td class="gantt-name-col">
                <div class="gantt-worker-name">${nombreCompleto}</div>
                <div class="gantt-worker-info">${rutCompleto}</div>
                <div class="gantt-worker-info">
                    <span class="badge" style="background-color: ${persona.turno_color}; font-size: 0.65rem;">
                        ${persona.turno_nombre}
                    </span>
                </div>
            </td>
        `;
        
        // Celdas de timeline
        const asignacion = {
            inicio: new Date(persona.fecha_inicio + 'T00:00:00'),
            fin: persona.fecha_fin ? new Date(persona.fecha_fin + 'T00:00:00') : null
        };
        asignacion.inicio.setHours(0, 0, 0, 0);
        if (asignacion.fin) asignacion.fin.setHours(0, 0, 0, 0);
        
        const fechaInicioStr = formatearFechaChilena(persona.fecha_inicio);
        const fechaFinStr = persona.fecha_fin ? formatearFechaChilena(persona.fecha_fin) : 'Indefinido';
        
        // Determinar qué períodos cubre la asignación
        const periodosActivos = [];
        rangoFechas.periodos.forEach((periodo, idx) => {
            const periodoInicio = periodo.fecha_inicio;
            const periodoFin = periodo.fecha_fin;
            
            // Verificar si la asignación está activa en este período
            const activo = asignacion.inicio <= periodoFin && 
                          (!asignacion.fin || asignacion.fin >= periodoInicio);
            
            periodosActivos.push({
                activo: activo,
                incluye_hoy: periodo.incluye_hoy,
                idx: idx
            });
        });
        
        // Renderizar las celdas
        let i = 0;
        while (i < periodosActivos.length) {
            if (periodosActivos[i].activo) {
                // Contar cuántos períodos consecutivos están activos
                let colspan = 0;
                let j = i;
                while (j < periodosActivos.length && periodosActivos[j].activo) {
                    colspan++;
                    j++;
                }
                
                // Renderizar la barra
                html += `
                    <td colspan="${colspan}" class="gantt-cell">
                        <div class="gantt-bar" style="background-color: ${persona.turno_color};" 
                             title="${nombreCompleto}\n${persona.turno_nombre}\n${fechaInicioStr} → ${fechaFinStr}">
                            ${persona.turno_nombre}
                        </div>
                    </td>
                `;
                
                i = j;
            } else {
                // Celda vacía
                html += `<td class="gantt-cell ${periodosActivos[i].incluye_hoy ? 'gantt-today' : ''}"></td>`;
                i++;
            }
        }
        
        html += '</tr>';
    });
    
    html += '</tbody>';
    html += '</table>';
    
    container.innerHTML = html;
}

// Calcular rango de fechas para el Gantt (días individuales)
function calcularRangoFechasGantt() {
    // Usar las fechas de la faena o calcular del personal
    let fechaMin = faenaFechaInicio ? new Date(faenaFechaInicio + 'T00:00:00') : null;
    let fechaMax = faenaFechaFin ? new Date(faenaFechaFin + 'T00:00:00') : null;
    
    // Si no hay fechas de faena, calcular del personal
    if (!fechaMin || !fechaMax) {
        ganttPersonalFiltrado.forEach(p => {
            const inicio = new Date(p.fecha_inicio + 'T00:00:00');
            if (!fechaMin || inicio < fechaMin) fechaMin = inicio;
            
            if (p.fecha_fin) {
                const fin = new Date(p.fecha_fin + 'T00:00:00');
                if (!fechaMax || fin > fechaMax) fechaMax = fin;
            }
        });
    }
    
    // Si aún no hay fechas, usar mes actual
    if (!fechaMin) fechaMin = new Date();
    if (!fechaMax) {
        fechaMax = new Date(fechaMin);
        fechaMax.setMonth(fechaMax.getMonth() + 3);
    }
    
    fechaMin.setHours(0, 0, 0, 0);
    fechaMax.setHours(0, 0, 0, 0);
    
    // Agregar margen
    fechaMin.setDate(1); // Inicio del mes
    fechaMax = new Date(fechaMax.getFullYear(), fechaMax.getMonth() + 1, 0); // Fin del mes
    
    // Calcular total de días
    const totalDias = Math.ceil((fechaMax - fechaMin) / (1000 * 60 * 60 * 24)) + 1;
    
    // Si hay muchos días (más de 90), agrupar por semanas
    const usarSemanas = totalDias > 90;
    
    const periodos = [];
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    
    if (usarSemanas) {
        // Vista por semanas
        let fechaActual = new Date(fechaMin);
        // Ajustar al lunes más cercano
        const diaSemana = fechaActual.getDay();
        const diasHastaLunes = diaSemana === 0 ? -6 : 1 - diaSemana;
        fechaActual.setDate(fechaActual.getDate() + diasHastaLunes);
        
        while (fechaActual <= fechaMax) {
            const inicioSemana = new Date(fechaActual);
            const finSemana = new Date(fechaActual);
            finSemana.setDate(finSemana.getDate() + 6);
            
            const incluyeHoy = hoy >= inicioSemana && hoy <= finSemana;
            
            periodos.push({
                fecha_inicio: inicioSemana,
                fecha_fin: finSemana,
                label: `${inicioSemana.getDate()}/${inicioSemana.getMonth() + 1}`,
                tipo: 'semana',
                incluye_hoy: incluyeHoy
            });
            
            fechaActual.setDate(fechaActual.getDate() + 7);
        }
    } else {
        // Vista por días
        let fechaActual = new Date(fechaMin);
        let mesActual = fechaActual.getMonth();
        
        while (fechaActual <= fechaMax) {
            const dia = fechaActual.getDate();
            const mes = fechaActual.getMonth();
            const esPrimerDiaMes = dia === 1 || mes !== mesActual;
            
            const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
            const label = esPrimerDiaMes ? `${dia} ${meses[mes]}` : `${dia}`;
            
            const incluyeHoy = fechaActual.toDateString() === hoy.toDateString();
            
            periodos.push({
                fecha_inicio: new Date(fechaActual),
                fecha_fin: new Date(fechaActual),
                label: label,
                tipo: 'dia',
                incluye_hoy: incluyeHoy,
                es_primer_dia_mes: esPrimerDiaMes
            });
            
            mesActual = mes;
            fechaActual.setDate(fechaActual.getDate() + 1);
        }
    }
    
    return {
        fecha_min: fechaMin,
        fecha_max: fechaMax,
        periodos: periodos,
        usar_semanas: usarSemanas
    };
}

// ============================================================================
// VARIABLES DE ORDENAMIENTO Y PAGINACIÓN ADICIONALES
// ============================================================================

let ordenAsignar = { columna: 'nombre', direccion: 'asc' };
let ordenManual = { columna: 'nombre', direccion: 'asc' };
let ordenGestionar = { columna: 'nombre', direccion: 'asc' };
let ordenEstadosManuales = { columna: 'nombre', direccion: 'asc' };

let paginaActualManual = 1;
let registrosPorPaginaManual = 25;
let paginaActualGestionar = 1;
let registrosPorPaginaGestionar = 25;
let paginaActualEstadosManuales = 1;
let registrosPorPaginaEstadosManuales = 25;

// ============================================================================
// FUNCIONES DE SELECCIÓN
// ============================================================================

// Toggle select all en Asignar Personal
function toggleSelectAllAsignar() {
    const selectAll = document.getElementById('selectAllAsignar');
    const checkboxes = document.querySelectorAll('.personal-checkbox');
    
    checkboxes.forEach(checkbox => {
        // Solo seleccionar checkboxes que no estén deshabilitados (sin conflictos)
        if (!checkbox.disabled) {
            checkbox.checked = selectAll.checked;
            const personalId = parseInt(checkbox.value);
            
            if (selectAll.checked) {
                if (!personalSeleccionados.includes(personalId)) {
                    personalSeleccionados.push(personalId);
                }
            } else {
                const index = personalSeleccionados.indexOf(personalId);
                if (index > -1) {
                    personalSeleccionados.splice(index, 1);
                }
            }
        }
    });
    
    actualizarContador();
    renderizarTablaPersonal();
}

// ============================================================================
// FUNCIONES DE ORDENAMIENTO CON FLECHAS
// ============================================================================

// Ordenar tabla de Asignar Personal
function ordenarTablaAsignar(columna) {
    if (ordenAsignar.columna === columna) {
        ordenAsignar.direccion = ordenAsignar.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenAsignar.columna = columna;
        ordenAsignar.direccion = 'asc';
    }
    actualizarIconosOrdenamiento('#asignar', ordenAsignar);
    renderizarTablaPersonal();
}

// Ordenar tabla de Asignar Turno Manual
function ordenarTablaManual(columna) {
    if (ordenManual.columna === columna) {
        ordenManual.direccion = ordenManual.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenManual.columna = columna;
        ordenManual.direccion = 'asc';
    }
    actualizarIconosOrdenamiento('#asignar-manual', ordenManual);
    ordenarYRenderizarManual();
}

// Ordenar tabla de Personal Asignado
function ordenarTablaGestionar(columna) {
    if (ordenGestionar.columna === columna) {
        ordenGestionar.direccion = ordenGestionar.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenGestionar.columna = columna;
        ordenGestionar.direccion = 'asc';
    }
    actualizarIconosOrdenamiento('#gestionar', ordenGestionar);
    ordenarYRenderizarGestionar();
}

// Ordenar tabla de Estados Manuales
function ordenarTablaEstadosManuales(columna) {
    if (ordenEstadosManuales.columna === columna) {
        ordenEstadosManuales.direccion = ordenEstadosManuales.direccion === 'asc' ? 'desc' : 'asc';
    } else {
        ordenEstadosManuales.columna = columna;
        ordenEstadosManuales.direccion = 'asc';
    }
    actualizarIconosOrdenamiento('#estados-manuales', ordenEstadosManuales);
    filtrarEstadosManuales();
}

// Actualizar iconos de ordenamiento
function actualizarIconosOrdenamiento(tabId, ordenActual) {
    // Limpiar todos los iconos de esa tabla
    document.querySelectorAll(`${tabId} .sortable i`).forEach(icon => {
        icon.className = 'bi bi-arrow-down-up ms-1';
    });
    
    // Actualizar el icono de la columna ordenada
    const thActual = document.querySelector(`${tabId} .sortable[data-column="${ordenActual.columna}"]`);
    if (thActual) {
        const icon = thActual.querySelector('i');
        icon.className = ordenActual.direccion === 'asc' ? 
            'bi bi-arrow-up ms-1' : 
            'bi bi-arrow-down ms-1';
    }
}

// Ordenar y re-renderizar tabla manual
function ordenarYRenderizarManual() {
    filtrarPersonalManual();
}

// ============================================================================
// PAGINACIÓN PARA TABLA GESTIONAR (Personal Asignado con Turnos)
// ============================================================================

function ordenarYRenderizarGestionar() {
    if (!faena.asignaciones) return;
    
    // Aplicar filtros si existen
    let asignacionesFiltradas = filtrarPersonalAsignado(false);
    
    // Ordenar
    asignacionesFiltradas.sort((a, b) => {
        let valorA, valorB;
        
        switch(ordenGestionar.columna) {
            case 'rut':
                valorA = a.personal.rut || '';
                valorB = b.personal.rut || '';
                break;
            case 'cargo':
                valorA = a.personal.cargo || '';
                valorB = b.personal.cargo || '';
                break;
            case 'empresa':
                valorA = a.personal.empresa || '';
                valorB = b.personal.empresa || '';
                break;
            case 'fecha_inicio':
                valorA = a.fecha_inicio || '';
                valorB = b.fecha_inicio || '';
                break;
            case 'nombre':
            default:
                valorA = a.personal.nombre || '';
                valorB = b.personal.nombre || '';
                break;
        }
        
        const comparacion = valorA.toString().localeCompare(valorB.toString());
        return ordenGestionar.direccion === 'asc' ? comparacion : -comparacion;
    });
    
    // Calcular paginación
    const totalPaginas = Math.ceil(asignacionesFiltradas.length / registrosPorPaginaGestionar);
    paginaActualGestionar = Math.min(paginaActualGestionar, Math.max(1, totalPaginas));
    
    const inicio = (paginaActualGestionar - 1) * registrosPorPaginaGestionar;
    const fin = Math.min(inicio + registrosPorPaginaGestionar, asignacionesFiltradas.length);
    const asignacionesPagina = asignacionesFiltradas.slice(inicio, fin);
    
    // Renderizar
    const tbody = document.getElementById('tablaPersonalAsignadoBody');
    if (asignacionesPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron trabajadores con los filtros aplicados</p>
                </td>
            </tr>
        `;
        document.getElementById('totalRegistrosGestionar').textContent = '0';
        document.getElementById('registroInicioGestionar').textContent = '0';
        document.getElementById('registroFinGestionar').textContent = '0';
        document.getElementById('paginacionGestionar').innerHTML = '';
        return;
    }
    
    tbody.innerHTML = asignacionesPagina.map(asig => {
        // Determinar estado
        let estadoBadge = '';
        if (asig.fecha_fin) {
            const hoy = new Date();
            hoy.setHours(0, 0, 0, 0);
            const fechaFin = new Date(asig.fecha_fin + 'T00:00:00');
            if (fechaFin < hoy) {
                estadoBadge = '<span class="badge bg-secondary">Finalizado</span>';
            } else {
                estadoBadge = '<span class="badge bg-success">Activo</span>';
            }
        } else {
            estadoBadge = '<span class="badge bg-success">Activo</span>';
        }
        
        return `
            <tr>
                <td class="small">
                    <a href="#" onclick="event.preventDefault(); showPersonalInfo(${asig.personal.id});" 
                       class="text-decoration-none text-primary fw-semibold" 
                       style="cursor: pointer;"
                       title="Ver información completa">
                        ${asig.personal.nombre}
                    </a>
                </td>
                <td class="text-muted small">${asig.personal.rut}</td>
                <td class="small">${asig.personal.cargo}</td>
                <td class="small">${asig.personal.empresa}</td>
                <td><span class="badge bg-primary" style="font-size: 0.75rem;">${asig.turno.nombre}</span></td>
                <td class="small">${asig.bloque_inicio ? `Bloque ${asig.bloque_inicio.orden}` : '-'}</td>
                <td class="small">${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td class="small">${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : '<span class="badge bg-info">Indefinida</span>'}</td>
                <td class="text-center">${estadoBadge}</td>
                <td class="text-center">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-sm btn-secondary" onclick="editarAsignacionDirecta(${asig.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarAsignacionDirecta(${asig.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Actualizar información de paginación
    document.getElementById('totalRegistrosGestionar').textContent = asignacionesFiltradas.length;
    document.getElementById('registroInicioGestionar').textContent = asignacionesFiltradas.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinGestionar').textContent = fin;
    
    // Generar paginación
    generarPaginacionGestionar(totalPaginas);
}

// Generar paginación para tabla gestionar
function generarPaginacionGestionar(totalPaginas) {
    const paginacion = document.getElementById('paginacionGestionar');
    if (!paginacion) return;
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Anterior
    html += `<li class="page-item ${paginaActualGestionar === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaGestionar(${paginaActualGestionar - 1})">«</a>
    </li>`;
    
    // Páginas
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActualGestionar - 2 && i <= paginaActualGestionar + 2)) {
            html += `<li class="page-item ${i === paginaActualGestionar ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaGestionar(${i})">${i}</a>
            </li>`;
        } else if (i === paginaActualGestionar - 3 || i === paginaActualGestionar + 3) {
            html += `<li class="page-item disabled"><a class="page-link" href="#">...</a></li>`;
        }
    }
    
    // Siguiente
    html += `<li class="page-item ${paginaActualGestionar === totalPaginas ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaGestionar(${paginaActualGestionar + 1})">»</a>
    </li>`;
    
    paginacion.innerHTML = html;
}

function cambiarPaginaGestionar(pagina) {
    paginaActualGestionar = pagina;
    ordenarYRenderizarGestionar();
}

function cambiarRegistrosPorPaginaGestionar() {
    registrosPorPaginaGestionar = parseInt(document.getElementById('registrosPorPaginaGestionar').value);
    paginaActualGestionar = 1;
    ordenarYRenderizarGestionar();
}

// ============================================================================
// PAGINACIÓN Y FUNCIONES PARA TABLA MANUAL
// ============================================================================

// Llenar tabla manual al cargar
document.addEventListener('DOMContentLoaded', function() {
    llenarTablaManual();
});

function llenarTablaManual() {
    const tbody = document.getElementById('personalManualTableBody');
    if (!tbody || !personal) return;
    
    // NO filtrar personal asignado - en turno manual SÍ pueden asignar múltiples veces
    let personalFiltrado = personal;
    
    // Aplicar ordenamiento
    if (ordenManual.columna) {
        personalFiltrado = [...personalFiltrado].sort((a, b) => {
            let valorA, valorB;
            
            switch(ordenManual.columna) {
                case 'rut':
                    valorA = a.rut || '';
                    valorB = b.rut || '';
                    break;
                case 'cargo':
                    valorA = a.cargo || '';
                    valorB = b.cargo || '';
                    break;
                case 'empresa':
                    valorA = a.empresa || '';
                    valorB = b.empresa || '';
                    break;
                case 'nombre':
                default:
                    valorA = a.nombre_completo || '';
                    valorB = b.nombre_completo || '';
                    break;
            }
            
            const comparacion = valorA.localeCompare(valorB);
            return ordenManual.direccion === 'asc' ? comparacion : -comparacion;
        });
    }
    
    // Calcular paginación
    const totalPaginas = Math.ceil(personalFiltrado.length / registrosPorPaginaManual);
    paginaActualManual = Math.min(paginaActualManual, Math.max(1, totalPaginas));
    
    const inicio = (paginaActualManual - 1) * registrosPorPaginaManual;
    const fin = Math.min(inicio + registrosPorPaginaManual, personalFiltrado.length);
    const personalPagina = personalFiltrado.slice(inicio, fin);
    
    // Renderizar página actual
    tbody.innerHTML = personalPagina.map(p => {
        const isAsignado = p.tiene_asignacion;
        const estadoBadge = isAsignado ? 
            '<span class="badge bg-warning">Asignado</span>' : 
            '<span class="badge bg-success">Disponible</span>';
        const faenaActual = p.asignacion_actual ? p.asignacion_actual.faena : '-';
        const periodo = p.asignacion_actual ?
            `${formatearFechaChilena(p.asignacion_actual.fecha_inicio)} → ${p.asignacion_actual.fecha_fin ? formatearFechaChilena(p.asignacion_actual.fecha_fin) : 'Indefinido'}` :
            '-';
            
        return `
            <tr data-personal-id="${p.id}"
                data-nombre="${p.nombre_completo}"
                data-rut="${p.rut}"
                data-cargo="${p.cargo}"
                data-empresa="${p.empresa}"
                data-tiene-asignacion="${isAsignado}">
                <td class="text-center">
                    <input class="form-check-input personal-manual-checkbox" type="checkbox" value="${p.id}">
                </td>
                <td class="small">${p.nombre_completo}</td>
                <td class="text-muted small">${p.rut}</td>
                <td class="small">${p.cargo}</td>
                <td class="small">${p.empresa}</td>
                <td>${estadoBadge}</td>
                <td class="small">${faenaActual}</td>
                <td class="small">${periodo}</td>
            </tr>
        `;
    }).join('');
    
    // Actualizar información de paginación
    document.getElementById('totalRegistrosManual').textContent = personalFiltrado.length;
    document.getElementById('registroInicioManual').textContent = personalFiltrado.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinManual').textContent = fin;
    
    // Generar paginación
    generarPaginacionManual(totalPaginas);
    
    // Agregar event listeners
    document.querySelectorAll('.personal-manual-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', actualizarResumenManual);
    });
}

// Generar paginación para tabla manual
function generarPaginacionManual(totalPaginas) {
    const paginacion = document.getElementById('paginacionManual');
    if (!paginacion) return;
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Anterior
    html += `<li class="page-item ${paginaActualManual === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaManual(${paginaActualManual - 1})">«</a>
    </li>`;
    
    // Páginas
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActualManual - 2 && i <= paginaActualManual + 2)) {
            html += `<li class="page-item ${i === paginaActualManual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaManual(${i})">${i}</a>
            </li>`;
        } else if (i === paginaActualManual - 3 || i === paginaActualManual + 3) {
            html += `<li class="page-item disabled"><a class="page-link" href="#">...</a></li>`;
        }
    }
    
    // Siguiente
    html += `<li class="page-item ${paginaActualManual === totalPaginas ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaManual(${paginaActualManual + 1})">»</a>
    </li>`;
    
    paginacion.innerHTML = html;
}

function cambiarPaginaManual(pagina) {
    paginaActualManual = pagina;
    llenarTablaManual();
}

function cambiarRegistrosPorPaginaManual() {
    registrosPorPaginaManual = parseInt(document.getElementById('registrosPorPaginaManual').value);
    paginaActualManual = 1;
    filtrarPersonalManual();
}

// Toggle select all manual
function toggleSelectAllManual() {
    const selectAll = document.getElementById('selectAllManual');
    // Solo seleccionar checkboxes que NO estén deshabilitados
    const checkboxes = document.querySelectorAll('.personal-manual-checkbox:not(:disabled)');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });
    
    actualizarResumenManual();
}

// Actualizar resumen manual
function actualizarResumenManual() {
    // Solo contar checkboxes seleccionados que NO estén deshabilitados
    const checkboxes = document.querySelectorAll('.personal-manual-checkbox:checked:not(:disabled)');
    const cantidad = checkboxes.length;
    
    const cantidadElement = document.getElementById('cantidadSeleccionadosManual');
    const resumenElement = document.getElementById('resumenSeleccionManual');
    const btnAsignarManual = document.getElementById('btnAsignarManual');
    
    // Validar que los elementos existan
    if (!cantidadElement || !resumenElement) {
        console.warn('Elementos de resumen manual no encontrados');
        return;
    }
    
    if (cantidad > 0) {
        cantidadElement.textContent = cantidad;
        resumenElement.style.display = 'block';
        // Habilitar botón solo si hay personal sin conflictos seleccionado
        if (btnAsignarManual) {
            btnAsignarManual.disabled = false;
        }
    } else {
        resumenElement.style.display = 'none';
        // Deshabilitar botón si no hay personal sin conflictos seleccionado
        if (btnAsignarManual) {
            btnAsignarManual.disabled = true;
        }
    }
}

// Filtrar personal manual
function filtrarPersonalManual() {
    const search = document.getElementById('searchManualInput').value.toLowerCase();
    const filtroCargo = document.getElementById('filtroCargoManual').value;
    const filtroEmpresa = document.getElementById('filtroEmpresaManual').value;
    
    // NO excluir personal asignado - en turno manual pueden tener múltiples asignaciones
    
    // Filtrar el array de personal
    const personalFiltrado = personal.filter(p => {
        const nombre = p.nombre_completo.toLowerCase();
        const rut = p.rut.toLowerCase();
        const cargo = p.cargo;
        const empresa = p.empresa;
        
        const matchSearch = nombre.includes(search) || rut.includes(search);
        const matchCargo = !filtroCargo || cargo === filtroCargo;
        const matchEmpresa = !filtroEmpresa || empresa === filtroEmpresa;
        
        return matchSearch && matchCargo && matchEmpresa;
    });
    
    // Resetear paginación y re-renderizar
    paginaActualManual = 1;
    renderizarTablaManualFiltrada(personalFiltrado);
}

// Renderizar tabla manual filtrada con paginación
function renderizarTablaManualFiltrada(personalFiltrado) {
    const tbody = document.getElementById('personalManualTableBody');
    
    // Aplicar ordenamiento
    if (ordenManual.columna) {
        personalFiltrado = [...personalFiltrado].sort((a, b) => {
            let valorA, valorB;
            
            switch(ordenManual.columna) {
                case 'rut':
                    valorA = a.rut || '';
                    valorB = b.rut || '';
                    break;
                case 'cargo':
                    valorA = a.cargo || '';
                    valorB = b.cargo || '';
                    break;
                case 'empresa':
                    valorA = a.empresa || '';
                    valorB = b.empresa || '';
                    break;
                case 'nombre':
                default:
                    valorA = a.nombre_completo || '';
                    valorB = b.nombre_completo || '';
                    break;
            }
            
            const comparacion = valorA.localeCompare(valorB);
            return ordenManual.direccion === 'asc' ? comparacion : -comparacion;
        });
    }
    
    // Calcular paginación
    const totalPaginas = Math.ceil(personalFiltrado.length / registrosPorPaginaManual);
    paginaActualManual = Math.min(paginaActualManual, Math.max(1, totalPaginas));
    
    const inicio = (paginaActualManual - 1) * registrosPorPaginaManual;
    const fin = Math.min(inicio + registrosPorPaginaManual, personalFiltrado.length);
    const personalPagina = personalFiltrado.slice(inicio, fin);
    
    // Renderizar
    tbody.innerHTML = personalPagina.map(p => {
        const isAsignado = p.tiene_asignacion;
        const estadoBadge = isAsignado ? 
            '<span class="badge bg-warning">Asignado</span>' : 
            '<span class="badge bg-success">Disponible</span>';
        const faenaActual = p.asignacion_actual ? p.asignacion_actual.faena : '-';
        const periodo = p.asignacion_actual ?
            `${formatearFechaChilena(p.asignacion_actual.fecha_inicio)} → ${p.asignacion_actual.fecha_fin ? formatearFechaChilena(p.asignacion_actual.fecha_fin) : 'Indefinido'}` :
            '-';
        
        // Deshabilitar checkbox si tiene asignación conflictiva
        const tieneConflicto = p.tiene_asignacion;
        const disabledAttr = tieneConflicto ? 'disabled' : '';
        const titleAttr = tieneConflicto ? 
            (p.asignacion_actual && p.asignacion_actual.tipo === 'ot' ? 
                `No se puede asignar: Tiene OT asignada` : 
                `No se puede asignar: Ya asignado a otra faena`) : 
            '';
            
        return `
            <tr data-personal-id="${p.id}"
                data-nombre="${p.nombre_completo}"
                data-rut="${p.rut}"
                data-cargo="${p.cargo}"
                data-empresa="${p.empresa}"
                data-tiene-asignacion="${isAsignado}"
                class="${tieneConflicto ? 'table-secondary' : ''}">
                <td class="text-center">
                    <input class="form-check-input personal-manual-checkbox" type="checkbox" value="${p.id}"
                           ${disabledAttr}
                           title="${titleAttr}">
                </td>
                <td class="small">${p.nombre_completo}</td>
                <td class="text-muted small">${p.rut}</td>
                <td class="small">${p.cargo}</td>
                <td class="small">${p.empresa}</td>
                <td>${estadoBadge}</td>
                <td class="small">${faenaActual}</td>
                <td class="small">${periodo}</td>
            </tr>
        `;
    }).join('');
    
    // Actualizar información de paginación
    document.getElementById('totalRegistrosManual').textContent = personalFiltrado.length;
    document.getElementById('registroInicioManual').textContent = personalFiltrado.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinManual').textContent = fin;
    
    // Generar paginación
    generarPaginacionManual(totalPaginas);
    
    // Agregar event listeners
    document.querySelectorAll('.personal-manual-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Si el checkbox está deshabilitado, no permitir seleccionarlo
            if (this.disabled && this.checked) {
                this.checked = false;
            }
            actualizarResumenManual();
        });
    });
    
    // Actualizar resumen y estado del botón después de renderizar
    actualizarResumenManual();
}

// Limpiar filtros manual
function limpiarFiltrosManual() {
    document.getElementById('searchManualInput').value = '';
    document.getElementById('filtroCargoManual').value = '';
    document.getElementById('filtroEmpresaManual').value = '';
    paginaActualManual = 1;
    llenarTablaManual();
}

// ============================================================================
// PAGINACIÓN Y FUNCIONES PARA TABLA ESTADOS MANUALES
// ============================================================================

// Filtrar estados manuales
function filtrarEstadosManuales() {
    const search = document.getElementById('searchEstadosManualesInput')?.value.toLowerCase() || '';
    const filtroCargo = document.getElementById('filtroCargoEstadosManuales')?.value || '';
    const filtroEmpresa = document.getElementById('filtroEmpresaEstadosManuales')?.value || '';
    
    // Obtener todas las filas sin filtrar
    const tbody = document.getElementById('tablaEstadosManualesBody');
    if (!tbody) return;
    
    const todasLasFilas = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
    
    // Filtrar filas
    const filasFiltradas = todasLasFilas.filter(row => {
        const nombre = (row.dataset.nombre || '').toLowerCase();
        const rut = (row.dataset.rut || '').toLowerCase();
        const cargo = row.dataset.cargo || '';
        const empresa = row.dataset.empresa || '';
        
        const matchSearch = nombre.includes(search) || rut.includes(search);
        const matchCargo = !filtroCargo || cargo === filtroCargo;
        const matchEmpresa = !filtroEmpresa || empresa === filtroEmpresa;
        
        return matchSearch && matchCargo && matchEmpresa;
    });
    
    // Resetear paginación y renderizar
    paginaActualEstadosManuales = 1;
    renderizarTablaEstadosManualesFiltrada(filasFiltradas);
}

// Renderizar tabla estados manuales filtrada con paginación
function renderizarTablaEstadosManualesFiltrada(filas) {
    const tbody = document.getElementById('tablaEstadosManualesBody');
    
    if (filas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron registros con los filtros aplicados</p>
                </td>
            </tr>
        `;
        document.getElementById('totalRegistrosEstadosManuales').textContent = '0';
        document.getElementById('registroInicioEstadosManuales').textContent = '0';
        document.getElementById('registroFinEstadosManuales').textContent = '0';
        document.getElementById('paginacionEstadosManuales').innerHTML = '';
        return;
    }
    
    // Ordenar
    filas.sort((a, b) => {
        let valorA, valorB;
        
        switch(ordenEstadosManuales.columna) {
            case 'rut':
                valorA = a.dataset.rut || '';
                valorB = b.dataset.rut || '';
                break;
            case 'cargo':
                valorA = a.dataset.cargo || '';
                valorB = b.dataset.cargo || '';
                break;
            case 'empresa':
                valorA = a.dataset.empresa || '';
                valorB = b.dataset.empresa || '';
                break;
            case 'fecha_inicio':
                valorA = a.dataset.fechaInicio || '';
                valorB = b.dataset.fechaInicio || '';
                break;
            case 'nombre':
            default:
                valorA = a.dataset.nombre || '';
                valorB = b.dataset.nombre || '';
                break;
        }
        
        const comparacion = valorA.localeCompare(valorB);
        return ordenEstadosManuales.direccion === 'asc' ? comparacion : -comparacion;
    });
    
    // Calcular paginación
    const totalPaginas = Math.ceil(filas.length / registrosPorPaginaEstadosManuales);
    paginaActualEstadosManuales = Math.min(paginaActualEstadosManuales, Math.max(1, totalPaginas));
    
    const inicio = (paginaActualEstadosManuales - 1) * registrosPorPaginaEstadosManuales;
    const fin = Math.min(inicio + registrosPorPaginaEstadosManuales, filas.length);
    const filasPagina = filas.slice(inicio, fin);
    
    // Renderizar
    tbody.innerHTML = '';
    filasPagina.forEach(row => tbody.appendChild(row));
    
    // Actualizar información de paginación
    document.getElementById('totalRegistrosEstadosManuales').textContent = filas.length;
    document.getElementById('registroInicioEstadosManuales').textContent = filas.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFinEstadosManuales').textContent = fin;
    
    // Generar paginación
    generarPaginacionEstadosManuales(totalPaginas);
}

// Generar paginación para tabla estados manuales
function generarPaginacionEstadosManuales(totalPaginas) {
    const paginacion = document.getElementById('paginacionEstadosManuales');
    if (!paginacion) return;
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Anterior
    html += `<li class="page-item ${paginaActualEstadosManuales === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaEstadosManuales(${paginaActualEstadosManuales - 1})">«</a>
    </li>`;
    
    // Páginas
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActualEstadosManuales - 2 && i <= paginaActualEstadosManuales + 2)) {
            html += `<li class="page-item ${i === paginaActualEstadosManuales ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaEstadosManuales(${i})">${i}</a>
            </li>`;
        } else if (i === paginaActualEstadosManuales - 3 || i === paginaActualEstadosManuales + 3) {
            html += `<li class="page-item disabled"><a class="page-link" href="#">...</a></li>`;
        }
    }
    
    // Siguiente
    html += `<li class="page-item ${paginaActualEstadosManuales === totalPaginas ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); cambiarPaginaEstadosManuales(${paginaActualEstadosManuales + 1})">»</a>
    </li>`;
    
    paginacion.innerHTML = html;
}

function cambiarPaginaEstadosManuales(pagina) {
    paginaActualEstadosManuales = pagina;
    filtrarEstadosManuales();
}

function cambiarRegistrosPorPaginaEstadosManuales() {
    registrosPorPaginaEstadosManuales = parseInt(document.getElementById('registrosPorPaginaEstadosManuales').value);
    paginaActualEstadosManuales = 1;
    filtrarEstadosManuales();
}

// Limpiar filtros estados manuales
function limpiarFiltrosEstadosManuales() {
    document.getElementById('searchEstadosManualesInput').value = '';
    document.getElementById('filtroCargoEstadosManuales').value = '';
    document.getElementById('filtroEmpresaEstadosManuales').value = '';
    paginaActualEstadosManuales = 1;
    ordenarYRenderizarEstadosManuales();
}

// Inicializar paginación de estados manuales al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const tbody = document.getElementById('tablaEstadosManualesBody');
    if (tbody) {
        filtrarEstadosManuales();
    }
});

// ============================================================================
// ELIMINAR ESTADO MANUAL
// ============================================================================

// Función para eliminar estado manual con modal de confirmación
function eliminarEstadoManual(estadoManualId, nombrePersonal) {
    // Crear modal de confirmación
    const modalHtml = `
        <div class="modal fade" id="modalEliminarEstadoManual" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Confirmar Eliminación
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-2">¿Está seguro que desea eliminar el estado manual de:</p>
                        <p class="mb-2"><strong>${nombrePersonal}</strong>?</p>
                        <div class="alert alert-warning mb-0">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Importante:</strong> Esta acción no se puede deshacer.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-circle me-1"></i>Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" id="btnConfirmarEliminarManual">
                            <i class="bi bi-trash me-1"></i>Eliminar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('modalEliminarEstadoManual'));
    
    // Event listener para el botón de confirmar
    document.getElementById('btnConfirmarEliminarManual').addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Eliminando...';
        
        try {
            const response = await fetch(`/calendario/estados-manuales/${estadoManualId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            modal.hide();
            
            if (data.status === 'success') {
                // Mostrar mensaje de éxito
                const exitoHtml = `
                    <div class="modal fade" id="modalExitoEliminar" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header bg-success text-white">
                                    <h5 class="modal-title">
                                        <i class="bi bi-check-circle me-2"></i>Eliminado Exitosamente
                                    </h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <p>${data.message}</p>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-primary" onclick="location.reload()">Aceptar</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', exitoHtml);
                const modalExito = new bootstrap.Modal(document.getElementById('modalExitoEliminar'));
                modalExito.show();
                
                document.getElementById('modalExitoEliminar').addEventListener('hidden.bs.modal', function() {
                    this.remove();
                    location.reload();
                });
            } else {
                // Mostrar mensaje de error
                const errorHtml = `
                    <div class="modal fade" id="modalErrorEliminar" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header bg-danger text-white">
                                    <h5 class="modal-title">
                                        <i class="bi bi-x-circle me-2"></i>Error
                                    </h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <p>Error: ${data.message}</p>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', errorHtml);
                const modalError = new bootstrap.Modal(document.getElementById('modalErrorEliminar'));
                modalError.show();
                
                document.getElementById('modalErrorEliminar').addEventListener('hidden.bs.modal', function() {
                    this.remove();
                });
            }
        } catch (error) {
            console.error('Error:', error);
            modal.hide();
            mostrarAlerta('Error de conexión al eliminar el estado manual', 'error');
        }
    });
    
    // Limpiar modal al cerrar
    document.getElementById('modalEliminarEstadoManual').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
    
    modal.show();
}

// ============================================================================
// ASIGNAR ESTADO MANUAL DESDE TAB
// ============================================================================

// Asignar estado manual desde el tab
async function asignarEstadoManualTab() {
    const estado = document.getElementById('estadoManualSelect').value;
    const fechaInicio = document.getElementById('fechaInicioManual').value;
    const fechaFin = document.getElementById('fechaFinManual').value;
    const observaciones = document.getElementById('observacionesManual').value;
    
    // Validaciones básicas
    if (!estado) {
        mostrarModal('Error de Validación', 'Debe seleccionar un estado.', 'error');
        return;
    }
    
    if (!fechaInicio || !fechaFin) {
        mostrarModal('Error de Validación', 'Debe ingresar las fechas de inicio y fin.', 'error');
        return;
    }
    
    // Validar que la fecha de inicio no sea anterior al inicio de la faena
    if (faenaFechaInicio && fechaInicio < faenaFechaInicio) {
        mostrarModal(
            'Error de Validación',
            `La fecha de inicio de asignación (${formatearFechaChilena(fechaInicio)}) no puede ser anterior al inicio de la faena (${formatearFechaChilena(faenaFechaInicio)}).`,
            'error'
        );
        return;
    }
    
    // Validar que la fecha de fin no sea posterior al fin de la faena
    if (faenaFechaFin && fechaFin > faenaFechaFin) {
        mostrarModal(
            'Error de Validación',
            `La fecha de fin de asignación (${formatearFechaChilena(fechaFin)}) no puede ser posterior al fin de la faena (${formatearFechaChilena(faenaFechaFin)}).`,
            'error'
        );
        return;
    }
    
    // Validar que la fecha de fin sea posterior a la fecha de inicio
    if (fechaFin && fechaFin < fechaInicio) {
        mostrarModal(
            'Error de Validación',
            `La fecha de fin (${formatearFechaChilena(fechaFin)}) debe ser posterior a la fecha de inicio (${formatearFechaChilena(fechaInicio)}).`,
            'error'
        );
        return;
    }
    
    // Obtener personal seleccionado (solo los que NO estén deshabilitados)
    const checkboxes = document.querySelectorAll('.personal-manual-checkbox:checked:not(:disabled)');
    if (checkboxes.length === 0) {
        mostrarModal('Error de Validación', 'Debe seleccionar al menos un trabajador disponible para asignar.', 'error');
        return;
    }
    
    const personalIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    const data = {
        personal_ids: personalIds,
        faena_id: faena.id,
        estado: parseInt(estado),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        observaciones: observaciones
    };
    
    try {
        const response = await fetch('/calendario/api/asignar-estado-manual/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Si hay errores parciales, mostrar advertencia persistente
            if (result.warning && result.errores && result.errores.length > 0) {
                mostrarAdvertenciaPersistente(result.total_asignados, result.total_errores, result.errores);
                
                // También mostrar alerta flotante de éxito parcial
                if (result.total_asignados > 0) {
                    mostrarAlerta(result.message, 'success');
                }
                
                // Guardar en sessionStorage para que aparezca después de recargar
                sessionStorage.setItem('advertenciaAsignacion', JSON.stringify({
                    totalAsignados: result.total_asignados,
                    totalErrores: result.total_errores,
                    errores: result.errores
                }));
                
                // Recargar en el tab actual
                setTimeout(() => {
                    window.location.hash = '#asignar-manual';
                    window.location.reload();
                }, 1500);
                
            } else {
                // Asignación completamente exitosa
                mostrarAlerta(result.message, 'success');
                
                // Recargar la página con el hash para activar el tab de estados manuales
                setTimeout(() => {
                    window.location.hash = '#estados-manuales';
                    window.location.reload();
                }, 1500);
            }
        } else {
            // Error total
            if (result.errores && result.errores.length > 0) {
                // Asegurar que el hash esté configurado ANTES de mostrar la advertencia
                window.location.hash = '#asignar-manual';
                
                // Pequeño delay para asegurar que el hash se aplique
                setTimeout(() => {
                    mostrarAdvertenciaPersistente(0, result.total_errores, result.errores);
                }, 100);
            } else {
                mostrarAlerta(result.error || 'Error al asignar estado manual', 'error');
            }
        }
    } catch (error) {
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}
