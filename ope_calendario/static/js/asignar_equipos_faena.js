// ============================================================================
// ASIGNAR EQUIPOS A FAENA
// ============================================================================

// Variables globales (se inicializan desde el template con datos de Django)
let equipos = [];
let faena = {};
let equiposSeleccionados = [];
let faenaFechaInicio = null;
let faenaFechaFin = null;

// Variables de paginación
let paginaActual = 1;
let registrosPorPagina = 10;
let equiposFiltrados = [];

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

function initDataEquipos(equiposData, faenaData, fechaInicio, fechaFin) {
    equipos = equiposData || [];
    faena = faenaData || {};
    faenaFechaInicio = fechaInicio;
    faenaFechaFin = fechaFin;
    
    // Establecer fechas por defecto si están disponibles
    if (faenaFechaInicio) {
        document.getElementById('fecha_inicio').value = formatearFechaChilena(faenaFechaInicio);
    }
    if (faenaFechaFin) {
        document.getElementById('fecha_fin').value = formatearFechaChilena(faenaFechaFin);
    }
    
    // Renderizar tabla inicial
    renderizarTablaEquipos();
    renderizarEquiposAsignados();
    
    // Event listeners
    document.getElementById('searchInput').addEventListener('input', renderizarTablaEquipos);
    document.getElementById('filtroEstado').addEventListener('change', renderizarTablaEquipos);
    document.getElementById('filtroTipo').addEventListener('change', renderizarTablaEquipos);
    document.getElementById('filtroEmpresa').addEventListener('change', renderizarTablaEquipos);
}

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
        const date = new Date(fecha + 'T00:00:00');
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const anio = date.getFullYear();
        return `${dia}-${mes}-${anio}`;
    } catch (error) {
        console.error('Error formateando fecha:', error);
        return fecha;
    }
}

// Convertir fecha chilena a formato ISO (YYYY-MM-DD)
function fechaChilenaToISO(fechaChilena) {
    if (!fechaChilena) return null;
    const partes = fechaChilena.split('-');
    if (partes.length === 3) {
        return `${partes[2]}-${partes[1]}-${partes[0]}`;
    }
    return null;
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

// Renderizar tabla de equipos con paginación
function renderizarTablaEquipos() {
    const tbody = document.getElementById('equiposTableBody');
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    const filtroEstado = document.getElementById('filtroEstado').value;
    const filtroTipo = document.getElementById('filtroTipo').value;
    const filtroEmpresa = document.getElementById('filtroEmpresa').value;
    
    // Obtener IDs de equipos ya asignados a ESTA faena
    const idsAsignadosEstaFaena = faena.asignaciones ? faena.asignaciones.map(a => a.equipo.id) : [];
    
    // Filtrar equipos
    equiposFiltrados = equipos.filter(eq => {
        // NO mostrar equipos ya asignados a ESTA faena
        if (idsAsignadosEstaFaena.includes(eq.id)) {
            return false;
        }
        
        // Búsqueda
        const codigo = eq.codigo_interno.toLowerCase();
        const nombre = eq.nombre.toLowerCase();
        const patente = (eq.patente || '').toLowerCase();
        const matchBusqueda = !busqueda || codigo.includes(busqueda) || nombre.includes(busqueda) || patente.includes(busqueda);
        
        // Filtro de estado
        let matchEstado = true;
        if (filtroEstado === 'disponible') {
            matchEstado = !eq.tiene_asignacion;
        } else if (filtroEstado === 'asignado') {
            matchEstado = eq.tiene_asignacion;
        }
        
        // Filtro de tipo
        const matchTipo = !filtroTipo || eq.tipo === filtroTipo;
        
        // Filtro de empresa
        const matchEmpresa = !filtroEmpresa || eq.empresa === filtroEmpresa;
        
        return matchBusqueda && matchEstado && matchTipo && matchEmpresa;
    });
    
    // Actualizar contador total
    document.getElementById('totalEquipos').textContent = equiposFiltrados.length;
    
    // Calcular paginación
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, equiposFiltrados.length);
    const equiposPagina = equiposFiltrados.slice(inicio, fin);
    
    // Actualizar contadores
    document.getElementById('registroInicio').textContent = equiposFiltrados.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistros').textContent = equiposFiltrados.length;
    
    // Renderizar tabla
    if (equiposPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="bi bi-inbox me-2"></i>No se encontraron equipos
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = equiposPagina.map(eq => {
            const estaSeleccionado = equiposSeleccionados.includes(eq.id);
            const tieneAsignacion = eq.tiene_asignacion;
            const asignacionInfo = eq.asignacion_actual;
            
            // Estado: Disponible o Asignado
            const estadoClass = tieneAsignacion ? 'bg-warning' : 'bg-success';
            const estadoText = tieneAsignacion ? 'Asignado' : 'Disponible';
            
            // Asignación Actual: solo el nombre de la faena o OT
            let asignacionActualHTML = '-';
            if (tieneAsignacion && asignacionInfo) {
                if (asignacionInfo.tipo === 'ot') {
                    asignacionActualHTML = `OT: ${asignacionInfo.folio}`;
                } else {
                    asignacionActualHTML = asignacionInfo.faena || '-';
                }
            }
            
            // Fecha Asignación: las fechas de la asignación actual
            let fechaAsignacionHTML = '-';
            if (asignacionInfo && asignacionInfo.fecha_inicio) {
                const fechaInicio = formatearFechaChilena(asignacionInfo.fecha_inicio);
                const fechaFin = asignacionInfo.fecha_fin ? formatearFechaChilena(asignacionInfo.fecha_fin) : 'Indefinida';
                fechaAsignacionHTML = `${fechaInicio} → ${fechaFin}`;
            }
            
            return `
                <tr class="${tieneAsignacion ? 'table-secondary' : ''}">
                    <td class="text-center">
                        <input class="form-check-input" type="checkbox" 
                               ${tieneAsignacion ? 'disabled title="No se puede asignar: Tiene asignación conflictiva"' : ''}
                               ${estaSeleccionado ? 'checked' : ''}
                               onchange="toggleEquipoSeleccionado(${eq.id})"
                               id="equipo_${eq.id}">
                    </td>
                    <td>${eq.nombre}</td>
                    <td>${eq.patente || '-'}</td>
                    <td>${eq.tipo}</td>
                    <td>${eq.empresa}</td>
                    <td>
                        <span class="badge ${estadoClass}">${estadoText}</span>
                    </td>
                    <td>${asignacionActualHTML}</td>
                    <td class="small">${fechaAsignacionHTML}</td>
                </tr>
            `;
        }).join('');
    }
    
    // Renderizar paginación
    renderizarPaginacionEquipos(totalPaginas);
    
    // Actualizar contador de seleccionados
    actualizarContadorSeleccionados();
    
    // Actualizar estado del botón
    actualizarBotonAsignar();
}

// Renderizar paginación
function renderizarPaginacionEquipos(totalPaginas) {
    const paginacion = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${paginaActual - 1}); return false;">Anterior</a>
        </li>
    `;
    
    // Números de página
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActual - 2 && i <= paginaActual + 2)) {
            html += `
                <li class="page-item ${i === paginaActual ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActual - 3 || i === paginaActual + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${paginaActual + 1}); return false;">Siguiente</a>
        </li>
    `;
    
    paginacion.innerHTML = html;
}

// Cambiar página
function cambiarPaginaEquipos(nuevaPagina) {
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas) {
        paginaActual = nuevaPagina;
        renderizarTablaEquipos();
    }
}

// Cambiar registros por página
function cambiarRegistrosPorPaginaEquipos() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1;
    renderizarTablaEquipos();
}

// ============================================================================
// SELECCIÓN DE EQUIPOS
// ============================================================================

// Toggle selección de un equipo
function toggleEquipoSeleccionado(equipoId) {
    const checkbox = document.getElementById(`equipo_${equipoId}`);
    if (checkbox.disabled) return;
    
    if (checkbox.checked) {
        if (!equiposSeleccionados.includes(equipoId)) {
            equiposSeleccionados.push(equipoId);
        }
    } else {
        equiposSeleccionados = equiposSeleccionados.filter(id => id !== equipoId);
    }
    
    actualizarContadorSeleccionados();
    actualizarBotonAsignar();
}

// Toggle seleccionar todos
function toggleSelectAllEquipos() {
    const selectAll = document.getElementById('selectAllEquipos');
    const checkboxes = document.querySelectorAll('#equiposTableBody input[type="checkbox"]:not(:disabled)');
    
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
        const equipoId = parseInt(cb.id.replace('equipo_', ''));
        if (selectAll.checked) {
            if (!equiposSeleccionados.includes(equipoId)) {
                equiposSeleccionados.push(equipoId);
            }
        } else {
            equiposSeleccionados = equiposSeleccionados.filter(id => id !== equipoId);
        }
    });
    
    actualizarContadorSeleccionados();
    actualizarBotonAsignar();
}

// Actualizar contador de seleccionados
function actualizarContadorSeleccionados() {
    document.getElementById('totalSeleccionados').textContent = equiposSeleccionados.length;
}

// Actualizar estado del botón
function actualizarBotonAsignar() {
    const btn = document.getElementById('btnAsignarEquiposMasivo');
    btn.disabled = equiposSeleccionados.length === 0;
}

// ============================================================================
// FILTROS
// ============================================================================

function limpiarFiltrosEquipos() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filtroEstado').value = '';
    document.getElementById('filtroTipo').value = '';
    document.getElementById('filtroEmpresa').value = '';
    paginaActual = 1;
    renderizarTablaEquipos();
}

// ============================================================================
// ASIGNACIÓN MASIVA
// ============================================================================

async function asignarEquiposMasivo() {
    // Obtener valores de fecha del date picker chileno en formato ISO
    let fechaInicio = null;
    let fechaFin = null;
    
    // Usar DatePickerChile.getValor() si está disponible (devuelve formato ISO)
    if (window.DatePickerChile && typeof window.DatePickerChile.getValor === 'function') {
        fechaInicio = window.DatePickerChile.getValor('fecha_inicio');
        fechaFin = window.DatePickerChile.getValor('fecha_fin');
    } else {
        // Fallback: intentar obtener del input hidden (formato ISO)
        const fechaInicioHidden = document.getElementById('fecha_inicio_hidden');
        const fechaFinHidden = document.getElementById('fecha_fin_hidden');
        
        if (fechaInicioHidden && fechaInicioHidden.value) {
            fechaInicio = fechaInicioHidden.value;
        } else {
            // Último recurso: obtener del input original y convertir
            const fechaInicioValue = document.getElementById('fecha_inicio').value;
            if (fechaInicioValue) {
                // Verificar si ya está en formato ISO
                if (fechaInicioValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaInicio = fechaInicioValue;
                } else {
                    // Convertir de formato chileno (DD-MM-YYYY) a ISO (YYYY-MM-DD)
                    fechaInicio = fechaChilenaToISO(fechaInicioValue);
                }
            }
        }
        
        if (fechaFinHidden && fechaFinHidden.value) {
            fechaFin = fechaFinHidden.value;
        } else {
            const fechaFinValue = document.getElementById('fecha_fin').value;
            if (fechaFinValue) {
                // Verificar si ya está en formato ISO
                if (fechaFinValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaFin = fechaFinValue;
                } else {
                    // Convertir de formato chileno (DD-MM-YYYY) a ISO (YYYY-MM-DD)
                    fechaFin = fechaChilenaToISO(fechaFinValue);
                }
            }
        }
    }
    
    const observaciones = document.getElementById('observaciones').value.trim();
    
    if (!fechaInicio) {
        mostrarAlerta('La fecha de inicio es requerida', 'error');
        return;
    }
    
    if (equiposSeleccionados.length === 0) {
        mostrarAlerta('Debe seleccionar al menos un equipo', 'error');
        return;
    }
    
    const data = {
        faena_id: faena.id,
        equipos_ids: equiposSeleccionados,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin || null,
        observaciones: observaciones
    };
    
    try {
        const response = await fetch('/calendario/api/crear-asignacion-equipos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            mostrarAlerta(result.message || 'Equipos asignados correctamente', 'success');
            
            // Limpiar selección
            equiposSeleccionados = [];
            document.getElementById('selectAllEquipos').checked = false;
            
            // Recargar página para actualizar datos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostrarAlerta(result.error || 'Error al asignar equipos', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error de conexión al asignar equipos', 'error');
    }
}

// ============================================================================
// GESTIÓN DE EQUIPOS ASIGNADOS
// ============================================================================

function renderizarEquiposAsignados() {
    const tbody = document.getElementById('equiposAsignadosBody');
    
    if (!faena.asignaciones || faena.asignaciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="bi bi-inbox me-2"></i>No hay equipos asignados
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = faena.asignaciones.map(asig => {
        return `
            <tr>
                <td>${asig.equipo.nombre}</td>
                <td>${asig.equipo.patente || '-'}</td>
                <td>${asig.equipo.tipo}</td>
                <td>${asig.equipo.empresa}</td>
                <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : 'Indefinida'}</td>
                <td class="text-center">
                    <div class="btn-group btn-group-sm">
                        ${window.userPermissions && window.userPermissions.canModificarAsignacion ? `
                        <button class="btn btn-sm btn-primary" onclick="editarAsignacionEquipo(${asig.id})" title="Editar asignación">
                            <i class="bi bi-pencil"></i>
                        </button>
                        ` : ''}
                        ${window.userPermissions && window.userPermissions.canDelete ? `
                        <button class="btn btn-sm btn-danger" onclick="eliminarAsignacionEquipo(${asig.id})" title="Eliminar asignación">
                            <i class="bi bi-trash"></i>
                        </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function editarAsignacionEquipo(asignacionId) {
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) {
        console.error('Asignación no encontrada:', asignacionId);
        mostrarAlerta('Error: Asignación no encontrada', 'error');
        return;
    }
    
    // Limpiar alertas
    const alertContainer = document.getElementById('alertEditAsignacionEquipo');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    // Llenar datos
    document.getElementById('editEquipoAsig_id').value = asignacion.id;
    document.getElementById('editEquipoAsig_faena_id').value = faena.id;
    document.getElementById('editEquipoAsig_nombreEquipo').textContent = asignacion.equipo.nombre;
    
    // Llenar fechas y observaciones
    if (window.DatePickerChile) {
        DatePickerChile.setValor('editEquipoAsig_fechaInicio', asignacion.fecha_inicio);
        if (asignacion.fecha_fin) {
            DatePickerChile.setValor('editEquipoAsig_fechaFin', asignacion.fecha_fin);
        } else {
            DatePickerChile.limpiar('editEquipoAsig_fechaFin');
        }
    }
    document.getElementById('editEquipoAsig_obs').value = asignacion.observaciones || '';
    
    // Abrir modal
    const modalElement = document.getElementById('modalEditarAsignacionEquipo');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Guardar edición de asignación de equipo
async function guardarEdicionAsignacionEquipo(event) {
    event.preventDefault();
    
    const id = document.getElementById('editEquipoAsig_id').value;
    const faenaId = document.getElementById('editEquipoAsig_faena_id').value;
    
    // Obtener fechas en formato ISO
    let fechaInicio = null;
    let fechaFin = null;
    
    if (window.DatePickerChile && typeof window.DatePickerChile.getValor === 'function') {
        fechaInicio = window.DatePickerChile.getValor('editEquipoAsig_fechaInicio');
        fechaFin = window.DatePickerChile.getValor('editEquipoAsig_fechaFin');
    } else {
        // Fallback: intentar obtener del input hidden
        const fechaInicioHidden = document.getElementById('editEquipoAsig_fechaInicio_hidden');
        const fechaFinHidden = document.getElementById('editEquipoAsig_fechaFin_hidden');
        
        if (fechaInicioHidden && fechaInicioHidden.value) {
            fechaInicio = fechaInicioHidden.value;
        } else {
            const fechaInicioValue = document.getElementById('editEquipoAsig_fechaInicio').value;
            if (fechaInicioValue) {
                if (fechaInicioValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaInicio = fechaInicioValue;
                } else {
                    fechaInicio = fechaChilenaToISO(fechaInicioValue);
                }
            }
        }
        
        if (fechaFinHidden && fechaFinHidden.value) {
            fechaFin = fechaFinHidden.value;
        } else {
            const fechaFinValue = document.getElementById('editEquipoAsig_fechaFin').value;
            if (fechaFinValue) {
                if (fechaFinValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaFin = fechaFinValue;
                } else {
                    fechaFin = fechaChilenaToISO(fechaFinValue);
                }
            }
        }
    }
    
    const obs = document.getElementById('editEquipoAsig_obs').value.trim();
    
    // Validación 1: Fecha fin debe ser posterior a fecha inicio
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
        mostrarAlertaEnModal('La fecha de fin debe ser posterior a la fecha de inicio', 'error', 'alertEditAsignacionEquipo');
        return;
    }
    
    // Validación 2: Fecha inicio de asignación no puede ser antes del inicio de la faena
    if (faenaFechaInicio && fechaInicio && fechaInicio < faenaFechaInicio) {
        mostrarAlertaEnModal(`La fecha de inicio no puede ser anterior al inicio de la faena (${formatearFechaChilena(faenaFechaInicio)})`, 'error', 'alertEditAsignacionEquipo');
        return;
    }
    
    // Validación 3: Fecha fin de asignación no puede ser posterior al fin de la faena (si la faena tiene fin)
    if (faenaFechaFin && fechaFin && fechaFin > faenaFechaFin) {
        mostrarAlertaEnModal(`La fecha de fin no puede ser posterior al fin de la faena (${formatearFechaChilena(faenaFechaFin)})`, 'error', 'alertEditAsignacionEquipo');
        return;
    }
    
    try {
        const response = await fetch('/calendario/api/actualizar-asignacion-equipo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                asignacion_id: parseInt(id),
                faena_id: parseInt(faenaId),
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin || null,
                observaciones: obs
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Cerrar modal
            const modalElement = document.getElementById('modalEditarAsignacionEquipo');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar mensaje de éxito
            mostrarAlerta(result.message || 'Asignación actualizada correctamente', 'success');
            
            // Actualizar los datos localmente
            const asignacion = faena.asignaciones.find(a => a.id === parseInt(id));
            if (asignacion) {
                asignacion.fecha_inicio = fechaInicio;
                asignacion.fecha_fin = fechaFin || null;
                asignacion.observaciones = obs;
            }
            
            // Recargar página para actualizar datos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostrarAlertaEnModal(result.error || 'Error al actualizar la asignación', 'error', 'alertEditAsignacionEquipo');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarAlertaEnModal('Error de conexión al actualizar la asignación', 'error', 'alertEditAsignacionEquipo');
    }
}

// Función auxiliar para mostrar alertas en el modal
function mostrarAlertaEnModal(mensaje, tipo, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertClass = tipo === 'error' ? 'danger' : tipo;
    const icon = tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle';
    
    container.innerHTML = `
        <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi bi-${icon} me-2"></i>${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
}

async function eliminarAsignacionEquipo(asignacionId) {
    if (!confirm('¿Está seguro de eliminar esta asignación?')) {
        return;
    }
    
    try {
        const response = await fetch('/calendario/api/eliminar-asignacion-equipo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ asignacion_id: asignacionId })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            mostrarAlerta('Asignación eliminada correctamente', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostrarAlerta(result.error || 'Error al eliminar asignación', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error de conexión', 'error');
    }
}

// ============================================================================
// ALERTAS
// ============================================================================

function mostrarAlerta(mensaje, tipo) {
    const alertContainer = document.getElementById('alertContainer');
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const icon = tipo === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';
    
    alertContainer.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi ${icon} me-2"></i>${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

