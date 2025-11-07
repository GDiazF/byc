// ============================================================================
// GESTIÓN DE FAENAS Y SERVICIOS
// ============================================================================

// Variables globales (se inicializan desde el template con datos de Django)
// faenas, personal y turnos se definen en el template HTML
let faenaActual = null;
let asignacionEditando = null;
let vistaActual = 'tabla'; // 'cards' o 'tabla'

// ============================================================================
// RECARGA DINÁMICA DE DATOS
// ============================================================================

// Recargar faenas desde la API
async function recargarFaenasDinamicamente() {
    try {
        const response = await fetch('/calendario/api/listar-faenas/', {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.faenas) {
                faenas = data.faenas;
                renderizarFaenas();
                return true;
            }
        }
        return false;
    } catch (error) {
        console.error('Error al recargar faenas:', error);
        return false;
    }
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

// Verificar si una faena está activa o finalizada
function esFaenaActiva(faena) {
    if (!faena.fecha_fin) {
        return true; // Sin fecha de fin = activa
    }
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const fechaFin = new Date(faena.fecha_fin + 'T00:00:00');
    return fechaFin >= hoy;
}

// Calcular duración de una faena en días
function calcularDuracionFaena(faena) {
    if (!faena.fecha_inicio || !faena.fecha_fin) {
        return 'N/A';
    }
    const inicio = new Date(faena.fecha_inicio + 'T00:00:00');
    const fin = new Date(faena.fecha_fin + 'T00:00:00');
    const dias = Math.ceil((fin - inicio) / (1000 * 60 * 60 * 24));
    
    if (dias < 30) {
        return `${dias} día${dias !== 1 ? 's' : ''}`;
    } else if (dias < 365) {
        const meses = Math.floor(dias / 30);
        return `${meses} mes${meses !== 1 ? 'es' : ''}`;
    } else {
        const años = Math.floor(dias / 365);
        const meses = Math.floor((dias % 365) / 30);
        return `${años} año${años !== 1 ? 's' : ''}${meses > 0 ? ` ${meses} mes${meses !== 1 ? 'es' : ''}` : ''}`;
    }
}

// Obtener estado de la faena
function obtenerEstadoFaena(faena) {
    if (!faena.fecha_fin) {
        return '<span class="badge bg-success" style="font-size: 0.7rem;">Activa</span>';
    }
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const fechaFin = new Date(faena.fecha_fin + 'T00:00:00');
    const diasRestantes = Math.ceil((fechaFin - hoy) / (1000 * 60 * 60 * 24));
    
    if (diasRestantes < 0) {
        return '<span class="badge bg-secondary" style="font-size: 0.7rem;">Finalizada</span>';
    } else if (diasRestantes >= 1 && diasRestantes <= 3) {
        // Rojo: 1-3 días (CRÍTICO)
        return `<span class="badge bg-success" style="font-size: 0.7rem;">Activa</span> <span class="badge bg-danger" style="font-size: 0.7rem;" title="¡URGENTE! Finaliza en ${diasRestantes} día${diasRestantes !== 1 ? 's' : ''}">${diasRestantes}d</span>`;
    } else if (diasRestantes >= 4 && diasRestantes <= 14) {
        // Amarillo: 4-14 días (ALERTA)
        return `<span class="badge bg-success" style="font-size: 0.7rem;">Activa</span> <span class="badge bg-warning text-dark" style="font-size: 0.7rem;" title="Finaliza en ${diasRestantes} días">${diasRestantes}d</span>`;
    } else if (diasRestantes >= 15 && diasRestantes <= 29) {
        // Azul: 15-29 días (PLANIFICAR)
        return `<span class="badge bg-success" style="font-size: 0.7rem;">Activa</span> <span class="badge bg-primary" style="font-size: 0.7rem;" title="Finaliza en ${diasRestantes} días">${diasRestantes}d</span>`;
    } else {
        // Gris: 30+ días (SIN URGENCIA)
        return `<span class="badge bg-success" style="font-size: 0.7rem;">Activa</span> <span class="badge bg-secondary" style="font-size: 0.7rem;" title="Finaliza en ${diasRestantes} días">${diasRestantes}d</span>`;
    }
}

// Renderizar faenas en formato de cards compactas
function renderizarFaenaCard(faena, esActiva = true) {
    return `
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="card faena-card ${!esActiva ? 'faena-finalizada' : ''}" 
                 data-faena-id="${faena.id}"
                 data-faena-codigo="${faena.codigo || ''}"
                 data-faena-nombre="${faena.nombre}">
                <div class="card-header ${esActiva ? 'bg-dark' : 'bg-secondary'} text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0" title="${faena.codigo}">
                            <i class="bi bi-geo-alt me-1"></i><strong>${faena.codigo}</strong>
                        </h6>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-sm btn-secondary" onclick="editarFaena(${faena.id})" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="confirmarEliminarFaena(${faena.id})" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <h6 class="mb-2 text-truncate" title="${faena.nombre}">
                        ${faena.nombre}
                    </h6>
                    ${faena.fecha_inicio || faena.fecha_fin ? `
                        <div class="small mb-2">
                            <i class="bi bi-calendar-range me-1"></i>
                            <div class="text-truncate">
                                ${formatearFechaChilena(faena.fecha_inicio) || '-'} → ${formatearFechaChilena(faena.fecha_fin) || 'Indef.'}
                            </div>
                        </div>
                    ` : ''}
                    <div class="mb-2">
                        <span class="badge bg-dark me-1" style="font-size: 0.7rem;">
                            <i class="bi bi-people-fill me-1"></i>${faena.total_personal}
                        </span>
                        ${obtenerEstadoFaena(faena)}
                    </div>
                    <div class="d-grid gap-1">
                        ${esActiva ? `
                            <a href="/calendario/faenas/${faena.id}/asignar/" class="btn btn-sm btn-success">
                                <i class="bi bi-person-plus me-1"></i>Asignar
                            </a>
                        ` : ''}
                        <button class="btn btn-sm btn-dark" onclick="verDetallesFaena(${faena.id})">
                            <i class="bi bi-eye me-1"></i>Detalle
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Renderizar fila de tabla
function renderizarFaenaFila(faena, esActiva = true) {
    return `
        <tr data-faena-id="${faena.id}"
            data-faena-codigo="${faena.codigo || ''}"
            data-faena-nombre="${faena.nombre}">
            <td><span class="badge bg-dark">${faena.codigo}</span></td>
            <td><strong>${faena.nombre}</strong></td>
            <td class="text-muted small">${faena.descripcion || 'Sin descripción'}</td>
            <td>${formatearFechaChilena(faena.fecha_inicio) || '-'}</td>
            <td>${formatearFechaChilena(faena.fecha_fin) || 'Indefinida'}</td>
            <td class="text-center">
                <span class="badge bg-dark">${faena.total_personal}</span>
            </td>
            <td>${esActiva ? obtenerEstadoFaena(faena) : '<span class="badge bg-secondary">Finalizada</span>'}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm">
                    ${esActiva ? `
                        <a href="/calendario/faenas/${faena.id}/asignar/" class="btn btn-sm btn-success" title="Asignar Personal">
                            <i class="bi bi-person-plus"></i>
                        </a>
                    ` : ''}
                    <button class="btn btn-sm btn-primary" onclick="verDetallesFaena(${faena.id})" title="Ver Detalle">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editarFaena(${faena.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmarEliminarFaena(${faena.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// Renderizar faenas principales
function renderizarFaenas() {
    // Asegurarse de que faenas está definido
    if (!faenas) {
        faenas = [];
    }
    
    // Separar faenas activas y finalizadas
    const faenasActivas = faenas.filter(f => esFaenaActiva(f));
    const faenasFinalizadas = faenas.filter(f => !esFaenaActiva(f));
    
    console.log('Total faenas:', faenas.length);
    console.log('Faenas activas:', faenasActivas.length);
    console.log('Faenas finalizadas:', faenasFinalizadas.length);
    
    // Actualizar badges de tabs
    document.getElementById('badgeActivas').textContent = faenasActivas.length;
    document.getElementById('badgeFinalizadas').textContent = faenasFinalizadas.length;
    
    // Actualizar cards de estadísticas
    document.getElementById('totalFaenas').textContent = faenas.length;
    document.getElementById('faenasActivas').textContent = faenasActivas.length;
    
    // Renderizar faenas activas
    renderizarSeccion(faenasActivas, 'Activas', true);
    
    // Renderizar faenas finalizadas
    renderizarSeccion(faenasFinalizadas, 'Finalizadas', false);
}

// Renderizar una sección (activas o finalizadas)
function renderizarSeccion(faenasLista, tipo, esActiva) {
    const cardsContainer = document.getElementById(`faenas${tipo}Cards`);
    const tablaBody = document.getElementById(`faenas${tipo}TablaBody`);
    
    if (faenasLista.length === 0) {
        const mensajeVacio = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay faenas ${esActiva ? 'activas' : 'finalizadas'}.
                    ${esActiva ? 'Crea una nueva faena para comenzar.' : ''}
                </div>
            </div>
        `;
        cardsContainer.innerHTML = mensajeVacio;
        tablaBody.innerHTML = `
            <tr>
                <td colspan="${esActiva ? '7' : '7'}" class="text-center text-muted py-4">
                    <i class="bi bi-inbox fs-1"></i>
                    <p class="mt-2">No hay faenas ${esActiva ? 'activas' : 'finalizadas'}</p>
                </td>
            </tr>
        `;
        return;
    }
    
    // Renderizar cards
    cardsContainer.innerHTML = faenasLista.map(f => renderizarFaenaCard(f, esActiva)).join('');
    
    // Renderizar tabla
    tablaBody.innerHTML = faenasLista.map(f => renderizarFaenaFila(f, esActiva)).join('');
}

// Cambiar entre vista de cards y tabla
function cambiarVisualizacion(vista) {
    vistaActual = vista;
    
    // Actualizar botones
    document.getElementById('btnVistaTabla').classList.toggle('active', vista === 'tabla');
    document.getElementById('btnVistaCards').classList.toggle('active', vista === 'cards');
    
    // Mostrar/ocultar vistas usando clases de Bootstrap
    const vistasCards = document.querySelectorAll('.vista-cards');
    const vistasTabla = document.querySelectorAll('.vista-tabla');
    
    if (vista === 'cards') {
        vistasCards.forEach(v => v.classList.remove('d-none'));
        vistasTabla.forEach(v => v.classList.add('d-none'));
    } else {
        vistasCards.forEach(v => v.classList.add('d-none'));
        vistasTabla.forEach(v => v.classList.remove('d-none'));
    }
}

// Crear nueva faena
function mostrarModalNuevaFaena() {
    document.getElementById('faenaModalTitle').textContent = 'Nueva Faena';
    document.getElementById('faenaForm').reset();
    document.getElementById('faena_id').value = '';
    document.getElementById('codigo_faena').value = '';
    
    // Limpiar alertas del modal
    document.getElementById('alertContainerModal').innerHTML = '';
    
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Editar faena
function editarFaena(faenaId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    document.getElementById('faenaModalTitle').textContent = 'Editar Faena';
    document.getElementById('faena_id').value = faena.id;
    document.getElementById('codigo_faena').value = faena.codigo || '';
    document.getElementById('nombre_faena').value = faena.nombre;
    document.getElementById('fecha_inicio_faena').value = faena.fecha_inicio || '';
    document.getElementById('fecha_fin_faena').value = faena.fecha_fin || '';
    document.getElementById('descripcion_faena').value = faena.descripcion;
    
    // Limpiar alertas del modal
    document.getElementById('alertContainerModal').innerHTML = '';
    
    const modal = new bootstrap.Modal(document.getElementById('faenaModal'));
    modal.show();
}

// Guardar faena
async function guardarFaena(event) {
    event.preventDefault();
    
    const faenaId = document.getElementById('faena_id').value;
    const codigo = document.getElementById('codigo_faena').value.trim().toUpperCase();
    const nombre = document.getElementById('nombre_faena').value.trim();
    const fechaInicio = document.getElementById('fecha_inicio_faena').value;
    const fechaFin = document.getElementById('fecha_fin_faena').value;
    const descripcion = document.getElementById('descripcion_faena').value.trim();
    
    if (!codigo) {
        mostrarAlertaModal('El código de la faena es requerido', 'error');
        return;
    }
    
    if (!nombre) {
        mostrarAlertaModal('El nombre de la faena es requerido', 'error');
        return;
    }
    
    if (!fechaInicio) {
        mostrarAlertaModal('La fecha de inicio es requerida', 'error');
        return;
    }
    
    if (!fechaFin) {
        mostrarAlertaModal('La fecha de fin es requerida', 'error');
        return;
    }
    
    // Validar que fecha_fin sea posterior a fecha_inicio
    if (fechaFin < fechaInicio) {
        mostrarAlertaModal('La fecha de fin debe ser posterior a la fecha de inicio', 'error');
        return;
    }
    
    const url = faenaId ? '/calendario/api/actualizar-faena/' : '/calendario/api/crear-faena/';
    const data = faenaId ? 
        { faena_id: parseInt(faenaId), codigo, nombre, ubicacion: '', descripcion, fecha_inicio: fechaInicio || null, fecha_fin: fechaFin || null } :
        { codigo, nombre, ubicacion: '', descripcion, fecha_inicio: fechaInicio || null, fecha_fin: fechaFin || null };
    
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
            // Cerrar modal de edición
            const modalElement = document.getElementById('faenaModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar mensaje de éxito
            mostrarAlerta(result.message, 'success');
            
            // Recargar datos dinámicamente
            await recargarFaenasDinamicamente();
            
            // Si hay conflictos (asignaciones desactivadas), mostrar modal de advertencia
            if (result.conflictos && result.conflictos.length > 0) {
                setTimeout(() => {
                    mostrarModalAdvertenciaConflictos(result.asignaciones_actualizadas, result.asignaciones_desactivadas, result.conflictos);
                }, 500);
            }
        } else {
            mostrarAlertaModal(result.error || 'Error al guardar la faena', 'error');
        }
    } catch (error) {
        console.error('Error al guardar faena:', error);
        mostrarAlertaModal('Error de conexión: ' + error.message, 'error');
    }
}

// Variable para guardar el ID de la faena a eliminar
let faenaAEliminar = null;

// Mostrar modal de confirmación para eliminar faena
function confirmarEliminarFaena(faenaId) {
    const faena = faenas.find(f => f.id === faenaId);
    if (!faena) return;
    
    // Guardar ID
    faenaAEliminar = faenaId;
    
    // Mostrar nombre de la faena
    document.getElementById('confirmarEliminarFaena_nombre').textContent = faena.nombre;
    
    // Mostrar advertencia según si tiene personal o no
    const tienePersonal = faena.total_personal > 0;
    const advertenciaDiv = document.getElementById('advertenciaPersonalAsignado');
    const sinPersonalDiv = document.getElementById('sinPersonalAsignado');
    
    if (tienePersonal) {
        document.getElementById('totalPersonalAsignado').textContent = faena.total_personal;
        advertenciaDiv.style.display = 'block';
        sinPersonalDiv.style.display = 'none';
    } else {
        advertenciaDiv.style.display = 'none';
        sinPersonalDiv.style.display = 'block';
    }
    
    // Configurar botón de confirmar
    document.getElementById('btnConfirmarEliminarFaena').onclick = ejecutarEliminarFaena;
    
    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminarFaena'));
    modal.show();
}

// Ejecutar eliminación de faena
function ejecutarEliminarFaena() {
    if (!faenaAEliminar) return;
    
    // Cerrar modal
    const modalElement = document.getElementById('modalConfirmarEliminarFaena');
    const modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) {
        modalInstance.hide();
    }
    
    // Ejecutar eliminación
    eliminarFaena(faenaAEliminar);
    faenaAEliminar = null;
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
            // Recargar datos dinámicamente en lugar de recargar la página
            await recargarFaenasDinamicamente();
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
    
    // Actualizar título y datos de la faena
    document.getElementById('detalleFaenaNombre').textContent = faena.nombre;
    document.getElementById('detalleFechaInicio').textContent = formatearFechaChilena(faena.fecha_inicio) || 'Sin definir';
    document.getElementById('detalleFechaFin').textContent = formatearFechaChilena(faena.fecha_fin) || 'Indefinida';
    document.getElementById('detalleTotalPersonal').textContent = faena.total_personal || 0;
    
    // Mostrar u ocultar botón de gestionar según si la faena está activa
    const btnGestionar = document.getElementById('btnGestionarAsignaciones');
    const faenaActiva = esFaenaActiva(faena);
    
    if (faenaActiva) {
        btnGestionar.style.display = 'inline-block';
        btnGestionar.href = `/calendario/faenas/${faena.id}/asignar/#gestionar`;
    } else {
        btnGestionar.style.display = 'none';
    }
    
    const tbody = document.getElementById('detalleAsignacionesBody');
    
    if (faena.asignaciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2 mb-3">No hay personal asignado a esta faena</p>
                    <a href="/calendario/faenas/${faena.id}/asignar/" class="btn btn-success">
                        <i class="bi bi-person-plus-fill me-1"></i>Asignar Personal
                    </a>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = faena.asignaciones.map(asig => {
            // Verificar si hay inconsistencias con las fechas de la faena
            let warningIcon = '';
            let rowClass = '';
            let estadoBadge = '';
            
            // Verifica si la asignación empieza antes de la faena
            if (faena.fecha_inicio && asig.fecha_inicio && asig.fecha_inicio < faena.fecha_inicio) {
                warningIcon = ' <i class="bi bi-exclamation-triangle-fill text-warning" title="Empieza antes del inicio de la faena"></i>';
                rowClass = 'table-warning';
            }
            
            // Verifica si la asignación termina después de la faena
            if (faena.fecha_fin && asig.fecha_fin && asig.fecha_fin > faena.fecha_fin) {
                warningIcon = ' <i class="bi bi-exclamation-triangle-fill text-warning" title="Termina después del fin de la faena"></i>';
                rowClass = 'table-warning';
            }
            
            // Verifica si la asignación no tiene fin pero la faena sí
            if (faena.fecha_fin && !asig.fecha_fin) {
                warningIcon = ' <i class="bi bi-info-circle-fill text-info" title="Asignación indefinida"></i>';
                rowClass = 'table-info';
            }
            
            // Determinar estado
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
                <tr class="${rowClass}">
                    <td><strong>${asig.personal.nombre}</strong>${warningIcon}</td>
                    <td class="text-muted small">${asig.personal.rut}</td>
                    <td>${asig.personal.cargo}</td>
                    <td><span class="badge bg-primary" style="font-size: 0.75rem;">${asig.turno.nombre}</span></td>
                    <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                    <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : '-'}</td>
                    <td class="text-center">${estadoBadge}</td>
                </tr>
            `;
        }).join('');
    }
    
    const modal = new bootstrap.Modal(document.getElementById('detalleFaenaModal'));
    modal.show();
}


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
    
    let alertClass, iconClass;
    if (tipo === 'success') {
        alertClass = 'alert-success';
        iconClass = 'bi-check-circle-fill';
    } else if (tipo === 'warning') {
        alertClass = 'alert-warning';
        iconClass = 'bi-exclamation-triangle-fill';
    } else {
        alertClass = 'alert-danger';
        iconClass = 'bi-exclamation-triangle-fill';
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    // Preservar saltos de línea en el mensaje
    const mensajeFormateado = mensaje.replace(/\n/g, '<br>');
    alertDiv.innerHTML = `
        <i class="bi ${iconClass} me-2"></i><span>${mensajeFormateado}</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de 8 segundos (más tiempo para warnings largos)
    const tiempoAutoCierre = tipo === 'warning' ? 8000 : 5000;
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

// Mostrar alerta dentro del modal
function mostrarAlertaModal(mensaje, tipo) {
    const alertContainer = document.getElementById('alertContainerModal');
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    
    // Limpiar alertas anteriores
    alertContainer.innerHTML = '';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Scroll al inicio del modal para ver la alerta
    document.querySelector('#faenaModal .modal-body').scrollTop = 0;
    
    // NO SE AUTO-ELIMINA - el usuario debe cerrarla manualmente
}

// Filtrar faenas por código o nombre
function filtrarFaenas() {
    const busqueda = document.getElementById('buscadorFaenas').value.trim().toUpperCase();
    
    // Si no hay búsqueda, mostrar todas las faenas
    if (!busqueda) {
        document.querySelectorAll('.faena-card, tr[data-faena-id]').forEach(el => {
            el.style.display = '';
        });
        return;
    }
    
    // Filtrar en vista de cards
    document.querySelectorAll('.faena-card').forEach(card => {
        const codigo = card.dataset.faenaCodigo || '';
        const nombre = card.dataset.faenaNombre || '';
        
        const coincide = codigo.toUpperCase().includes(busqueda) || 
                         nombre.toUpperCase().includes(busqueda);
        
        card.style.display = coincide ? '' : 'none';
    });
    
    // Filtrar en vista de tabla
    document.querySelectorAll('tr[data-faena-id]').forEach(row => {
        const codigo = row.dataset.faenaCodigo || '';
        const nombre = row.dataset.faenaNombre || '';
        
        const coincide = codigo.toUpperCase().includes(busqueda) || 
                         nombre.toUpperCase().includes(busqueda);
        
        row.style.display = coincide ? '' : 'none';
    });
}

// Limpiar buscador
function limpiarBuscador() {
    document.getElementById('buscadorFaenas').value = '';
    filtrarFaenas();
}

// Mostrar modal de advertencia de conflictos al actualizar fechas de faena
function mostrarModalAdvertenciaConflictos(asignacionesActualizadas, asignacionesDesactivadas, conflictos) {
    const contenido = document.getElementById('modalAdvertenciaContenido');
    
    let html = `
        <div class="card border-success mb-3">
            <div class="card-body bg-success bg-opacity-10">
                <i class="bi bi-check-circle me-2 text-success"></i>
                <strong>Actualización Exitosa:</strong> ${asignacionesActualizadas} asignación(es) fueron ajustadas correctamente.
            </div>
        </div>
        
        <div class="card border-warning mb-3">
            <div class="card-body bg-warning bg-opacity-10">
                <h6 class="mb-2">
                    <i class="bi bi-exclamation-triangle me-2 text-warning"></i>
                    <strong>Asignaciones Desactivadas:</strong> ${asignacionesDesactivadas} asignación(es) se desactivaron automáticamente por conflictos de fechas:
                </h6>
                <ul class="mb-0">
    `;
    
    conflictos.forEach(conf => {
        html += `
            <li>
                <strong>${conf.personal}</strong> tiene conflicto con faena 
                <span class="badge bg-dark">${conf.codigo_conflicto}</span> 
                <strong>${conf.faena_conflicto}</strong>
                <br>
                <small class="text-muted">Período conflictivo: ${formatearFechaChilena(conf.fecha_inicio_conflicto)} → ${conf.fecha_fin_conflicto === 'Indefinido' ? 'Indefinido' : formatearFechaChilena(conf.fecha_fin_conflicto)}</small>
            </li>
        `;
    });
    
    html += `
                </ul>
            </div>
        </div>
        
        <div class="card border-info mb-0">
            <div class="card-body bg-info bg-opacity-10">
                <h6><i class="bi bi-info-circle me-2 text-info"></i>¿Qué hacer ahora?</h6>
                <p class="mb-2">Las asignaciones desactivadas ya no aparecerán en el calendario ni en las listas de personal asignado activo.</p>
                <p class="mb-0">Para reasignar estos trabajadores a esta faena, debe:</p>
                <ol class="mb-0">
                    <li>Eliminar o ajustar las fechas de sus asignaciones conflictivas en las otras faenas</li>
                    <li>Luego, asignarlos nuevamente a esta faena con las fechas deseadas</li>
                </ol>
            </div>
        </div>
    `;
    
    contenido.innerHTML = html;
    
    const modal = new bootstrap.Modal(document.getElementById('modalAdvertenciaConflictos'));
    modal.show();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando gestión de faenas...');
    console.log('Faenas cargadas:', faenas ? faenas.length : 0);
    
    // Renderizar faenas
    renderizarFaenas();
});
