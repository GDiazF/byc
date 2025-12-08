// Variables globales
let paginaActual = 1;
let tamanoPagina = 25;
let currentToggle = null;
let originalState = false;
let changeConfirmed = false;
let equiposSeleccionados = []; // Array de objetos {equipo_id, nombreEquipo, codigoInterno, tipoEquipo, marcaEquipo}
let todosLosEquipos = []; // Almacenar todos los equipos para búsqueda en modal

// Cargar equipos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarEquipos();
    
    // Event listeners para filtros
    document.getElementById('searchInput').addEventListener('input', debounce(cargarEquipos, 500));
    document.getElementById('empresaFilter').addEventListener('change', cargarEquipos);
    document.getElementById('tipoFilter').addEventListener('change', cargarEquipos);
    document.getElementById('marcaFilter').addEventListener('change', cargarEquipos);
    
    // Configurar botón de confirmación del modal
    document.getElementById('btnConfirmarDesactivar').addEventListener('click', confirmarDesactivacion);
    
    // Limpiar al cerrar modal de confirmación
    document.getElementById('confirmDesactivarModal').addEventListener('hidden.bs.modal', function() {
        if (currentToggle && !changeConfirmed) {
            currentToggle.checked = originalState;
        }
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
    
    // Inicializar modal de selección de equipos para descarga
    const btnSeleccionarEquipos = document.getElementById('btnSeleccionarEquipos');
    if (btnSeleccionarEquipos) {
        btnSeleccionarEquipos.addEventListener('click', function(e) {
            e.preventDefault();
            const modalElement = document.getElementById('modalSeleccionarEquipos');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                equiposSeleccionados = [];
                actualizarVistaSeleccionadosEquipos();
                // Cargar todos los equipos activos para búsqueda
                cargarTodosLosEquipos();
            }
        });
    }
    
    // Configurar búsqueda cuando el modal se muestra
    const modalSeleccionarEquipos = document.getElementById('modalSeleccionarEquipos');
    if (modalSeleccionarEquipos) {
        modalSeleccionarEquipos.addEventListener('shown.bs.modal', function() {
            console.log('Modal mostrado, configurando buscador...');
            // Configurar el event listener del buscador cuando el modal se muestra
            const buscarEquiposModal = document.getElementById('buscarEquiposModal');
            if (buscarEquiposModal) {
                console.log('Campo de búsqueda encontrado');
                // Remover listener anterior si existe
                if (buscarEquiposModal._buscarHandler) {
                    buscarEquiposModal.removeEventListener('input', buscarEquiposModal._buscarHandler);
                }
                // Crear nuevo handler - capturar el valor del input correctamente
                let timeoutBusqueda = null;
                buscarEquiposModal._buscarHandler = function(e) {
                    const inputElement = e.target || buscarEquiposModal;
                    const valor = inputElement.value;
                    console.log('Buscando:', valor);
                    
                    // Limpiar timeout anterior
                    if (timeoutBusqueda) {
                        clearTimeout(timeoutBusqueda);
                    }
                    
                    // Crear nuevo timeout para debounce
                    timeoutBusqueda = setTimeout(function() {
                        buscarEquiposEnModal(valor);
                    }, 300);
                };
                buscarEquiposModal.addEventListener('input', buscarEquiposModal._buscarHandler);
                // Limpiar el campo de búsqueda
                buscarEquiposModal.value = '';
                // Limpiar resultados
                const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
                if (resultadosDiv) {
                    resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
                }
            } else {
                console.error('No se encontró el campo buscarEquiposModal');
            }
        });
    }
    
    // Botón limpiar selección
    const btnLimpiarSeleccionEquipos = document.getElementById('btnLimpiarSeleccionEquipos');
    if (btnLimpiarSeleccionEquipos) {
        btnLimpiarSeleccionEquipos.addEventListener('click', function() {
            equiposSeleccionados = [];
            actualizarVistaSeleccionadosEquipos();
            const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
            if (resultadosDiv) {
                resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
            }
        });
    }
    
    // Botón descargar ZIP - usar delegación de eventos ya que el botón está dentro del modal
    // Manejar clics tanto en el botón como en sus elementos hijos (íconos, texto)
    document.addEventListener('click', function(e) {
        const btnDescargarZip = e.target.closest('#btnDescargarZipEquipos');
        if (btnDescargarZip && !btnDescargarZip.disabled) {
            e.preventDefault();
            e.stopPropagation();
            descargarDocumentacionZipEquipos();
        }
    });
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

// Cargar equipos con filtros
function cargarEquipos() {
    const search = document.getElementById('searchInput').value;
    const empresa = document.getElementById('empresaFilter').value;
    const tipo = document.getElementById('tipoFilter').value;
    const marca = document.getElementById('marcaFilter').value;
    
    const params = new URLSearchParams({
        search: search,
        empresa: empresa,
        tipo: tipo,
        marca: marca,
        estado: 'activos', // Siempre mostrar solo activos
        page: paginaActual,
        page_size: tamanoPagina
    });
    
    fetch(`/maquinarias/api/equipos/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarEquipos(data.equipos);
                renderizarPaginacion(data.pagination);
                actualizarEstadisticas(data.pagination);
            } else {
                mostrarError('Error al cargar equipos: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar equipos');
        });
}

// Renderizar tabla de equipos
function renderizarEquipos(equipos) {
    const tbody = document.getElementById('equiposTableBody');
    
    if (equipos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron equipos activos</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = equipos.map(equipo => `
        <tr>
            <td><strong>${equipo.nombreEquipo}</strong></td>
            <td>
                <span class="badge bg-secondary">${equipo.tipoEquipo.sigla}</span>
                <span class="ms-1">${equipo.tipoEquipo.nombre}</span>
            </td>
            <td>${equipo.marcaEquipo.nombre}</td>
            <td>${equipo.modeloEquipo.nombre}</td>
            <td>${equipo.empresa.nombre}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${window.userPermissions.canViewDocumentacion ? `
                    <a href="/maquinarias/equipos/${equipo.equipo_id}/documentacion/" 
                       class="btn btn-sm btn-primary" 
                       title="Ver Documentación">
                        <i class="bi bi-folder"></i>
                    </a>
                    ` : ''}
                    ${window.userPermissions.canEdit ? `
                    <a href="/maquinarias/equipos/${equipo.equipo_id}/editar/" 
                       class="btn btn-sm btn-secondary" 
                       title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    ` : ''}
                    ${window.userPermissions.canViewHistorial ? `
                    <button type="button" class="btn btn-sm btn-info" onclick="verHistorialEquipo(${equipo.equipo_id}, '${equipo.nombreEquipo.replace(/'/g, "\\'")}')" title="Ver Historial">
                        <i class="bi bi-clock-history"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-switch d-inline-block">
                    <input class="form-check-input" type="checkbox" 
                           style="cursor: ${window.userPermissions.canDesactivar || window.userPermissions.canActivar ? 'pointer' : 'not-allowed'};"
                           data-equipo-id="${equipo.equipo_id}"
                           data-nombre-equipo="${equipo.nombreEquipo.replace(/'/g, "\\'")}"
                           ${equipo.activo ? 'checked' : ''} 
                           ${(equipo.activo && !window.userPermissions.canDesactivar) || (!equipo.activo && !window.userPermissions.canActivar) ? 'disabled' : ''}
                           onchange="toggleEstadoEquipo(this)"
                           title="${equipo.activo ? (window.userPermissions.canDesactivar ? 'Desactivar equipo' : 'No tiene permiso para desactivar') : (window.userPermissions.canActivar ? 'Activar equipo' : 'No tiene permiso para activar')}">
                </div>
            </td>
        </tr>
    `).join('');
}

// Renderizar paginación
function renderizarPaginacion(pagination) {
    const paginacionDiv = document.getElementById('paginacion');
    
    if (pagination.total_pages <= 1) {
        paginacionDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${!pagination.has_previous ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    const startPage = Math.max(1, pagination.current_page - 2);
    const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === pagination.current_page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${pagination.total_pages}); return false;">${pagination.total_pages}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionDiv.innerHTML = html;
}

// Actualizar estadísticas
function actualizarEstadisticas(pagination) {
    document.getElementById('totalEquipos').textContent = pagination.total_count;
    
    const inicio = (pagination.current_page - 1) * pagination.page_size + 1;
    const fin = Math.min(pagination.current_page * pagination.page_size, pagination.total_count);
    
    document.getElementById('registroInicio').textContent = pagination.total_count > 0 ? inicio : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistros').textContent = pagination.total_count;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    cargarEquipos();
}

// Cambiar tamaño de página
function cambiarTamanoPagina() {
    tamanoPagina = parseInt(document.getElementById('pageSizeSelect').value);
    paginaActual = 1;
    cargarEquipos();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('empresaFilter').value = '';
    document.getElementById('tipoFilter').value = '';
    document.getElementById('marcaFilter').value = '';
    paginaActual = 1;
    cargarEquipos();
}

// ============================================================================
// TOGGLE DE ESTADO
// ============================================================================

function toggleEstadoEquipo(checkbox) {
    currentToggle = checkbox;
    originalState = !checkbox.checked;
    changeConfirmed = false;
    
    // Revertir el cambio hasta que se confirme
    checkbox.checked = originalState;
    
    // Actualizar nombre del equipo en el modal
    const nombreEquipo = checkbox.dataset.nombreEquipo;
    const nombreElement = document.getElementById('equipoDesactivarNombre');
    if (nombreElement) {
        nombreElement.textContent = nombreEquipo;
    }
    
    // Cerrar cualquier instancia existente del modal primero
    const modalElement = document.getElementById('confirmDesactivarModal');
    if (!modalElement) {
        console.error('Modal element not found');
        return;
    }
    
    const existingModal = bootstrap.Modal.getInstance(modalElement);
    if (existingModal) {
        existingModal.dispose();
    }
    
    // Mostrar modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

function confirmarDesactivacion() {
    if (!currentToggle) return;
    
    const equipoId = parseInt(currentToggle.dataset.equipoId);
    const nuevoEstado = !originalState;
    
    // Llamada AJAX para actualizar el estado
    fetch(`/maquinarias/api/equipos/${equipoId}/toggle-activo/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            changeConfirmed = true;
            
            // Cerrar modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
            confirmModal.hide();
            
            // Mostrar mensaje de éxito
            const accion = data.activo ? 'activado' : 'desactivado';
            mostrarExito(`Equipo ${accion} correctamente`);
            
            // Recargar equipos
            cargarEquipos();
        } else {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
            confirmModal.hide();
            alert('Error: ' + (data.message || 'Error al cambiar el estado del equipo'));
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
        confirmModal.hide();
        alert('Error al cambiar el estado del equipo');
        currentToggle.checked = originalState;
    });
}


// Mostrar notificación estilo alert
function showNotification(message, type = 'success') {
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 3000);
}

// Mostrar mensaje de éxito
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

// ============================================================================
// MODAL DE SELECCIÓN DE EQUIPOS PARA DESCARGA
// ============================================================================

// Cargar todos los equipos activos para búsqueda en modal
function cargarTodosLosEquipos() {
    console.log('Cargando todos los equipos...');
    fetch('/maquinarias/api/equipos/?estado=activos&page_size=9999')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                todosLosEquipos = data.equipos;
                console.log(`Cargados ${todosLosEquipos.length} equipos para búsqueda`);
            } else {
                console.error('Error al cargar equipos:', data.error);
            }
        })
        .catch(error => {
            console.error('Error al cargar equipos:', error);
        });
}

// Buscar equipos en el modal
function buscarEquiposEnModal(termino) {
    console.log('buscarEquiposEnModal llamada con término:', termino);
    const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
    
    if (!resultadosDiv) {
        console.error('No se encontró el div de resultados');
        return;
    }
    
    if (!termino || termino.trim() === '') {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
        return;
    }
    
    // Verificar que los equipos estén cargados
    if (!todosLosEquipos || todosLosEquipos.length === 0) {
        console.log('Equipos no cargados aún, esperando...');
        resultadosDiv.innerHTML = '<p class="text-warning text-center mb-0"><i class="bi bi-hourglass-split me-1"></i>Cargando equipos...</p>';
        // Intentar cargar nuevamente
        cargarTodosLosEquipos();
        // Reintentar después de un segundo
        setTimeout(() => {
            if (todosLosEquipos && todosLosEquipos.length > 0) {
                buscarEquiposEnModal(termino);
            } else {
                resultadosDiv.innerHTML = '<p class="text-danger text-center mb-0">Error al cargar equipos. Por favor recargue la página.</p>';
            }
        }, 1000);
        return;
    }
    
    console.log(`Buscando en ${todosLosEquipos.length} equipos`);
    const terminoLower = termino.toLowerCase().trim();
    console.log('Término de búsqueda (lowercase):', terminoLower);
    
    const resultados = todosLosEquipos.filter(e => {
        const nombreMatch = e.nombreEquipo && e.nombreEquipo.toLowerCase().includes(terminoLower);
        const codigoMatch = e.codigoInterno && e.codigoInterno.toLowerCase().includes(terminoLower);
        const patenteMatch = e.patente && e.patente !== '-' && e.patente.toLowerCase().includes(terminoLower);
        const marcaMatch = e.marcaEquipo && e.marcaEquipo.nombre && e.marcaEquipo.nombre.toLowerCase().includes(terminoLower);
        const modeloMatch = e.modeloEquipo && e.modeloEquipo.nombre && e.modeloEquipo.nombre.toLowerCase().includes(terminoLower);
        const tipoMatch = e.tipoEquipo && e.tipoEquipo.nombre && e.tipoEquipo.nombre.toLowerCase().includes(terminoLower);
        
        return nombreMatch || codigoMatch || patenteMatch || marcaMatch || modeloMatch || tipoMatch;
    });
    
    console.log(`Resultados encontrados: ${resultados.length}`);
    
    if (resultados.length === 0) {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">No se encontraron resultados</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    resultados.forEach(e => {
        const yaSeleccionado = equiposSeleccionados.some(es => es.equipo_id === e.equipo_id);
        html += `
            <div class="list-group-item list-group-item-action ${yaSeleccionado ? 'bg-light' : ''}" 
                 style="cursor: pointer;" 
                 data-equipo-id="${e.equipo_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${e.nombreEquipo}</h6>
                        <small class="text-muted">Código: ${e.codigoInterno} | ${e.tipoEquipo.nombre} | ${e.marcaEquipo.nombre} ${e.modeloEquipo.nombre}</small>
                    </div>
                    ${yaSeleccionado 
                        ? '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Seleccionado</span>'
                        : '<button class="btn btn-sm btn-primary btn-agregar-equipo" data-equipo-id="' + e.equipo_id + '"><i class="bi bi-plus-circle me-1"></i>Agregar</button>'
                    }
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultadosDiv.innerHTML = html;
    
    // Agregar event listeners a los botones y items
    resultadosDiv.querySelectorAll('.btn-agregar-equipo').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const equipoId = parseInt(this.dataset.equipoId);
            agregarEquipoSeleccionado(equipoId);
        });
    });
    
    resultadosDiv.querySelectorAll('.list-group-item').forEach(item => {
        item.addEventListener('click', function() {
            const equipoId = parseInt(this.dataset.equipoId);
            if (!equiposSeleccionados.some(es => es.equipo_id === equipoId)) {
                agregarEquipoSeleccionado(equipoId);
            }
        });
    });
}

// Agregar equipo a la lista de seleccionados
function agregarEquipoSeleccionado(equipoId) {
    const equipo = todosLosEquipos.find(e => e.equipo_id === equipoId);
    if (!equipo) return;
    
    // Verificar si ya está seleccionado
    if (equiposSeleccionados.some(es => es.equipo_id === equipoId)) {
        return;
    }
    
    equiposSeleccionados.push({
        equipo_id: equipo.equipo_id,
        nombreEquipo: equipo.nombreEquipo,
        codigoInterno: equipo.codigoInterno,
        tipoEquipo: equipo.tipoEquipo.nombre,
        marcaEquipo: equipo.marcaEquipo.nombre,
        modeloEquipo: equipo.modeloEquipo.nombre
    });
    
    actualizarVistaSeleccionadosEquipos();
    
    // Actualizar la vista de resultados para mostrar que está seleccionado
    const termino = document.getElementById('buscarEquiposModal').value;
    if (termino) {
        buscarEquiposEnModal(termino);
    }
}

// Remover equipo de la lista de seleccionados
function removerEquipoSeleccionado(equipoId) {
    equiposSeleccionados = equiposSeleccionados.filter(es => es.equipo_id !== equipoId);
    actualizarVistaSeleccionadosEquipos();
    
    // Actualizar la vista de resultados
    const termino = document.getElementById('buscarEquiposModal').value;
    if (termino) {
        buscarEquiposEnModal(termino);
    }
}

// Actualizar la vista de equipos seleccionados
function actualizarVistaSeleccionadosEquipos() {
    const contador = document.getElementById('contadorSeleccionadosEquipos');
    const vistaSeleccionados = document.getElementById('equiposSeleccionados');
    const btnDescargarZipEquipos = document.getElementById('btnDescargarZipEquipos');
    
    if (!vistaSeleccionados) return; // Si el modal no está abierto, no hacer nada
    
    if (contador) {
        contador.textContent = equiposSeleccionados.length;
    }
    
    if (btnDescargarZipEquipos) {
        btnDescargarZipEquipos.disabled = equiposSeleccionados.length === 0;
    }
    
    if (equiposSeleccionados.length === 0) {
        vistaSeleccionados.innerHTML = '<p class="text-muted text-center mb-0">No hay equipos seleccionados</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    equiposSeleccionados.forEach(e => {
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${e.nombreEquipo}</h6>
                        <small class="text-muted">Código: ${e.codigoInterno} | ${e.tipoEquipo}</small>
                    </div>
                    <button class="btn btn-sm btn-danger btn-remover-equipo" data-equipo-id="${e.equipo_id}">
                        <i class="bi bi-x-circle me-1"></i>Quitar
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    vistaSeleccionados.innerHTML = html;
    
    // Agregar event listeners a los botones de quitar
    vistaSeleccionados.querySelectorAll('.btn-remover-equipo').forEach(btn => {
        btn.addEventListener('click', function() {
            const equipoId = parseInt(this.dataset.equipoId);
            removerEquipoSeleccionado(equipoId);
        });
    });
}

// Descargar documentación en ZIP
function descargarDocumentacionZipEquipos() {
    console.log('descargarDocumentacionZipEquipos llamada');
    console.log('Equipos seleccionados:', equiposSeleccionados);
    
    if (equiposSeleccionados.length === 0) {
        alert('Por favor seleccione al menos un equipo');
        return;
    }
    
    const equipoIds = equiposSeleccionados.map(e => e.equipo_id);
    console.log('IDs de equipos:', equipoIds);
    
    // Obtener URL
    const url = window.descargarDocumentacionZipEquiposUrl || '/maquinarias/equipos/descargar-documentacion-zip/';
    console.log('URL de descarga:', url);
    
    // Crear formulario para enviar POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    
    // Agregar CSRF token
    const csrfToken = window.csrfToken || getCookie('csrftoken');
    console.log('CSRF Token:', csrfToken ? 'Encontrado' : 'No encontrado');
    
    if (!csrfToken) {
        alert('Error: No se pudo obtener el token CSRF. Por favor recargue la página.');
        return;
    }
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    // Agregar IDs de los equipos
    equipoIds.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'equipo_ids';
        input.value = id;
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    console.log('Enviando formulario...');
    form.submit();
    document.body.removeChild(form);
    
    // Cerrar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalSeleccionarEquipos'));
    if (modal) {
        modal.hide();
    }
    
    // Limpiar selección
    equiposSeleccionados = [];
    actualizarVistaSeleccionadosEquipos();
}

// Función helper para obtener cookie
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

