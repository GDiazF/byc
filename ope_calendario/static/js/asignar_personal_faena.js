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
let registrosPorPagina = 25;
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
    const filtroFaena = document.getElementById('filtroFaena').value;
    
    // Filtrar personal
    personalFiltrado = personal.filter(p => {
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
        
        // Filtro de faena
        let matchFaena = true;
        if (filtroFaena && p.asignacion_actual) {
            matchFaena = p.asignacion_actual.faena === filtroFaena;
        } else if (filtroFaena === 'sin_asignar') {
            matchFaena = !p.tiene_asignacion;
        }
        
        return matchBusqueda && matchEstado && matchCargo && matchFaena;
    });
    
    if (personalFiltrado.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
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
        const fechaAsignacion = p.asignacion_actual ? 
            `${formatearFechaChilena(p.asignacion_actual.fecha_inicio) || ''} ${p.asignacion_actual.fecha_fin ? '→ ' + formatearFechaChilena(p.asignacion_actual.fecha_fin) : '→ Indefinido'}` : 
            '-';
        
        return `
            <tr class="${isChecked ? 'table-primary' : ''}">
                <td class="text-center">
                    <input class="form-check-input personal-checkbox" type="checkbox" 
                           value="${p.id}" ${isChecked ? 'checked' : ''}>
                </td>
                <td>${p.nombre_completo}</td>
                <td>${p.rut}</td>
                <td>${p.cargo}</td>
                <td>
                    <span class="badge ${estadoClass}">${estadoText}</span>
                </td>
                <td>${p.asignacion_actual ? p.asignacion_actual.faena : '-'}</td>
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
    const total = document.querySelectorAll('.personal-checkbox').length;
    const seleccionados = document.querySelectorAll('.personal-checkbox:checked').length;
    
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
    const checkboxes = document.querySelectorAll('.personal-checkbox');
    const todosSeleccionados = Array.from(checkboxes).every(cb => cb.checked);
    
    personalSeleccionados = [];
    
    if (!todosSeleccionados) {
        checkboxes.forEach(cb => {
            const id = parseInt(cb.value);
            if (!personalSeleccionados.includes(id)) {
                personalSeleccionados.push(id);
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
    document.getElementById('filtroFaena').value = '';
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
    
    if (!turnoId) {
        container.style.display = 'none';
        return;
    }
    
    const turno = turnos.find(t => t.id === turnoId);
    if (!turno || !turno.bloques || turno.bloques.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    // Mostrar descripción del turno
    const descripcionDiv = document.getElementById('turnoDescripcion');
    let descripcionHTML = '<div class="alert alert-info small py-2 mb-3"><strong>Ciclo del turno:</strong><br>';
    turno.bloques.forEach(b => {
        descripcionHTML += `Bloque ${b.orden}: ${b.estado.nombre} (${b.duracion_dias} días) → `;
    });
    descripcionHTML = descripcionHTML.slice(0, -4); // Quitar última flecha
    descripcionHTML += `<br><strong>Total: ${turno.longitud_ciclo} días</strong></div>`;
    descripcionDiv.innerHTML = descripcionHTML;
    
    container.style.display = 'block';
    select.innerHTML = '<option value="">Desde el inicio del ciclo</option>' +
        turno.bloques.map(b => `
            <option value="${b.id}">
                Iniciar en Bloque ${b.orden}: ${b.estado.nombre} (${b.duracion_dias} días)
            </option>
        `).join('');
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

// Renderizar tabla de personal asignado
function renderizarPersonalAsignado() {
    const tbody = document.getElementById('tablaPersonalAsignadoBody');
    
    if (!faena.asignaciones || faena.asignaciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
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
    
    tbody.innerHTML = faena.asignaciones.map(asig => {
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
                <td><strong>${asig.personal.nombre}</strong></td>
                <td class="text-muted small">${asig.personal.rut}</td>
                <td>${asig.personal.cargo}</td>
                <td><span class="badge bg-primary" style="font-size: 0.75rem;">${asig.turno.nombre}</span></td>
                <td>${asig.bloque_inicio ? `Bloque ${asig.bloque_inicio.orden}` : '-'}</td>
                <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : '<span class="badge bg-info">Indefinida</span>'}</td>
                <td class="text-center">${estadoBadge}</td>
                <td class="text-center">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-sm btn-primary" onclick="editarAsignacionDirecta(${asig.id})" title="Editar">
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
    document.getElementById('editAsig_fechaInicio').value = asignacion.fecha_inicio;
    document.getElementById('editAsig_fechaFin').value = asignacion.fecha_fin || '';
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
    
    // Pre-llenar fechas de la faena si existen
    if (faenaFechaInicio) {
        document.getElementById('fecha_inicio').value = faenaFechaInicio;
    }
    if (faenaFechaFin) {
        document.getElementById('fecha_fin').value = faenaFechaFin;
    }
    
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
    document.getElementById('filtroFaena').addEventListener('change', function() {
        paginaActual = 1;
        renderizarTablaPersonal();
    });
    document.getElementById('turno_id').addEventListener('change', onTurnoChange);
    
    // Checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('personal-checkbox')) {
            onCheckboxChange(e.target);
        }
    });
    
    // Event listener para cambio de tab
    document.getElementById('gestionar-tab').addEventListener('shown.bs.tab', function() {
        renderizarPersonalAsignado();
    });
    
    // Si la URL tiene #gestionar, activar ese tab automáticamente
    if (window.location.hash === '#gestionar') {
        const tabElement = document.getElementById('gestionar-tab');
        const tab = new bootstrap.Tab(tabElement);
        tab.show();
    }
    
});

// ============================================================================
// ADVERTENCIAS Y MENSAJES
// ============================================================================

// Mostrar advertencia persistente en el cuerpo de la página
function mostrarAdvertenciaPersistente(totalAsignados, totalErrores, errores) {
    const container = document.getElementById('areaAdvertencias');
    
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
    const container = document.getElementById('areaAdvertencias');
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
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

