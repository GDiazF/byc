// ============================================================================
// GESTIÓN DE FAENAS Y SERVICIOS
// ============================================================================

// Variables globales (se inicializan desde el template con datos de Django)
let faenas = [];
let personal = [];
let turnos = [];
let faenaActual = null;
let asignacionEditando = null;

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

// Renderizar faenas
function renderizarFaenas() {
    const container = document.getElementById('faenasContainer');
    
    if (faenas.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay faenas registradas. Crea una nueva faena para comenzar.
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = faenas.map(faena => `
        <div class="col-md-6 col-lg-4">
            <div class="card faena-card" data-faena-id="${faena.id}">
                <div class="card-header bg-dark text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-geo-alt me-2"></i>${faena.nombre}
                        </h6>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-sm btn-outline-light" onclick="editarFaena(${faena.id})" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-light" onclick="confirmarEliminarFaena(${faena.id})" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    ${faena.descripcion ? `
                        <p class="small text-muted mb-2">${faena.descripcion}</p>
                    ` : '<p class="small text-muted mb-2">Sin descripción</p>'}
                    ${faena.fecha_inicio || faena.fecha_fin ? `
                        <p class="small mb-2">
                            <i class="bi bi-calendar-range me-1"></i>
                            <strong>${formatearFechaChilena(faena.fecha_inicio) || 'Sin inicio'}</strong> → <strong>${formatearFechaChilena(faena.fecha_fin) || 'Sin fin'}</strong>
                        </p>
                    ` : ''}
                    <div class="mb-3">
                        <span class="badge bg-info">
                            <i class="bi bi-people-fill me-1"></i>${faena.total_personal} Trabajador${faena.total_personal !== 1 ? 'es' : ''}
                        </span>
                    </div>
                    <div class="d-grid gap-2">
                        <a href="/calendario/faenas/${faena.id}/asignar/" class="btn btn-sm btn-success">
                            <i class="bi bi-person-plus me-1"></i>Asignar Personal
                        </a>
                        <button class="btn btn-sm btn-outline-dark" onclick="verDetallesFaena(${faena.id})">
                            <i class="bi bi-eye me-1"></i>Ver Detalle
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Crear nueva faena
function mostrarModalNuevaFaena() {
    document.getElementById('faenaModalTitle').textContent = 'Nueva Faena';
    document.getElementById('faenaForm').reset();
    document.getElementById('faena_id').value = '';
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Editar faena
function editarFaena(faenaId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    document.getElementById('faenaModalTitle').textContent = 'Editar Faena';
    document.getElementById('faena_id').value = faena.id;
    document.getElementById('nombre_faena').value = faena.nombre;
    document.getElementById('fecha_inicio_faena').value = faena.fecha_inicio || '';
    document.getElementById('fecha_fin_faena').value = faena.fecha_fin || '';
    document.getElementById('descripcion_faena').value = faena.descripcion;
    
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Guardar faena
async function guardarFaena(event) {
    event.preventDefault();
    
    const faenaId = document.getElementById('faena_id').value;
    const nombre = document.getElementById('nombre_faena').value.trim();
    const fechaInicio = document.getElementById('fecha_inicio_faena').value;
    const fechaFin = document.getElementById('fecha_fin_faena').value;
    const descripcion = document.getElementById('descripcion_faena').value.trim();
    
    if (!nombre) {
        mostrarAlerta('El nombre de la faena es requerido', 'error');
        return;
    }
    
    // Validar que fecha_fin sea posterior a fecha_inicio
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
        mostrarAlerta('La fecha de fin debe ser posterior a la fecha de inicio', 'error');
        return;
    }
    
    const url = faenaId ? '/calendario/api/actualizar-faena/' : '/calendario/api/crear-faena/';
    const data = faenaId ? 
        { faena_id: parseInt(faenaId), nombre, ubicacion: '', descripcion, fecha_inicio: fechaInicio || null, fecha_fin: fechaFin || null } :
        { nombre, ubicacion: '', descripcion, fecha_inicio: fechaInicio || null, fecha_fin: fechaFin || null };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Cerrar modal correctamente
            const modalElement = document.getElementById('faenaModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar mensaje y recargar
            mostrarAlerta(result.message, 'success');
            setTimeout(() => {
                location.reload();
            }, 500);
        } else {
            mostrarAlerta(result.error || 'Error al guardar la faena', 'error');
        }
    } catch (error) {
        console.error('Error al guardar faena:', error);
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}

// Confirmar eliminación de faena
function confirmarEliminarFaena(faenaId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    if (confirm(`¿Está seguro que desea eliminar la faena "${faena.nombre}"?\n\n` +
                `Esto solo será posible si no tiene personal asignado.`)) {
        eliminarFaena(faenaId);
    }
}

// Eliminar faena
async function eliminarFaena(faenaId) {
    try {
        const response = await fetch('/calendario/api/eliminar-faena/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ faena_id: faenaId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarAlerta(result.message, 'success');
            location.reload();
        } else {
            mostrarAlerta(result.error || 'Error al eliminar la faena', 'error');
        }
    } catch (error) {
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}


// Ver detalles de faena
function verDetallesFaena(faenaId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    faenaActual = faena;
    
    document.getElementById('detalleFaenaNombre').textContent = faena.nombre;
    
    const tbody = document.getElementById('detalleAsignacionesBody');
    
    if (faena.asignaciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No hay personal asignado a esta faena</p>
                    <button class="btn btn-sm btn-success" onclick="mostrarModalAsignarPersonal(${faena.id})">
                        <i class="bi bi-person-plus-fill me-1"></i>Asignar Personal
                    </button>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = faena.asignaciones.map(asig => `
            <tr>
                <td>${asig.personal.nombre}</td>
                <td>${asig.personal.rut}</td>
                <td>${asig.personal.cargo}</td>
                <td>${asig.turno.nombre}</td>
                <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : '<span class="badge bg-success">Activo</span>'}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-sm btn-outline-primary" onclick="editarAsignacion(${faena.id}, ${asig.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="confirmarEliminarAsignacion(${asig.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    const modal = new bootstrap.Modal(document.getElementById('detalleFaenaModal'));
    modal.show();
}

// Editar asignación
function editarAsignacion(faenaId, asignacionId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) return;
    
    faenaActual = faena;
    asignacionEditando = asignacion;
    
    // Cerrar modal de detalles
    bootstrap.Modal.getInstance(document.getElementById('detalleFaenaModal')).hide();
    
    // Mostrar modo edición individual
    document.getElementById('modoSeleccionMultiple').style.display = 'none';
    document.getElementById('modoEdicionIndividual').style.display = 'block';
    
    // Llenar formulario
    document.getElementById('asignacionModalTitle').textContent = `Editar Asignación - ${faena.nombre}`;
    document.getElementById('asignacion_id').value = asignacion.id;
    document.getElementById('personalIdEdit').value = asignacion.personal.id;
    document.getElementById('nombrePersonalEdit').textContent = asignacion.personal.nombre;
    document.getElementById('turno_id').value = asignacion.turno.id;
    document.getElementById('fecha_inicio').value = asignacion.fecha_inicio;
    document.getElementById('fecha_fin').value = asignacion.fecha_fin || '';
    document.getElementById('observaciones').value = asignacion.observaciones;
    
    // Cargar bloques de turno
    onTurnoChange();
    
    // Seleccionar bloque de inicio si existe
    if (asignacion.bloque_inicio) {
        setTimeout(() => {
            document.getElementById('bloque_inicio_id').value = asignacion.bloque_inicio.id;
        }, 100);
    }
    
    // Renderizar turnos
    renderizarTurnos();
    
    const modal = new bootstrap.Modal(document.getElementById('asignacionModal'));
    modal.show();
}

// Confirmar eliminación de asignación
function confirmarEliminarAsignacion(asignacionId) {
    if (confirm('¿Está seguro que desea eliminar esta asignación?\n\nEl trabajador ya no estará asignado a esta faena.')) {
        eliminarAsignacion(asignacionId);
    }
}

// Eliminar asignación
async function eliminarAsignacion(asignacionId) {
    try {
        const response = await fetch('/calendario/api/eliminar-asignacion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ asignacion_id: asignacionId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarAlerta(result.message, 'success');
            location.reload();
        } else {
            mostrarAlerta(result.error || 'Error al eliminar la asignación', 'error');
        }
    } catch (error) {
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}

// Mostrar alerta
function mostrarAlerta(mensaje, tipo) {
    const alertContainer = document.getElementById('alertContainer');
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    renderizarFaenas();
    
    // Event listeners
    document.getElementById('buscarPersonal').addEventListener('input', renderizarPersonalDisponible);
    document.getElementById('turno_id').addEventListener('change', onTurnoChange);
    
    // Event listener para checkboxes de personal
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('personal-checkbox')) {
            actualizarContadorSeleccionados();
        }
    });
});
