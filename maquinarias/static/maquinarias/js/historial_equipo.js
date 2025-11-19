// ============================================================================
// HISTORIAL DE EQUIPOS
// ============================================================================

// Función para obtener el color del badge según la acción
function getBadgeColorAccionEquipo(accion) {
    const colores = {
        'EQUIPO_CREADO': 'bg-success',
        'EQUIPO_MODIFICADO': 'bg-primary',
        'EQUIPO_ACTIVADO': 'bg-success',
        'EQUIPO_DESACTIVADO': 'bg-danger',
        'EQUIPO_ELIMINADO': 'bg-danger',
        'ESTADO_MANUAL_ASIGNADO': 'bg-info',
        'ESTADO_MANUAL_MODIFICADO': 'bg-warning text-dark',
        'ESTADO_MANUAL_ELIMINADO': 'bg-danger',
        'ASIGNACION_FAENA_CREADA': 'bg-success',
        'ASIGNACION_FAENA_MODIFICADA': 'bg-warning text-dark',
        'ASIGNACION_FAENA_ELIMINADA': 'bg-danger'
    };
    return colores[accion] || 'bg-secondary';
}

// Función para mostrar el historial de un equipo en un modal
function verHistorialEquipo(equipoId, nombreEquipo) {
    const modal = new bootstrap.Modal(document.getElementById('modalHistorialEquipo'));
    const modalBody = document.getElementById('modalHistorialEquipoBody');
    const modalTitle = document.getElementById('modalHistorialEquipoLabel');
    
    // Actualizar título
    modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${nombreEquipo}`;
    
    // Mostrar loading
    modalBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando historial...</p>
        </div>
    `;
    
    // Mostrar modal
    modal.show();
    
    // Obtener historial desde la API
    const url = apiHistorialEquipoBase.replace('0', equipoId);
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarHistorialEquipoModal(data, modalBody);
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar historial: ${data.message || 'Error desconocido'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar historial
                </div>
            `;
        });
}

// Función para obtener el nombre completo del usuario
function obtenerNombreUsuario(evento) {
    // Priorizar usuario_nombre (nombre completo), luego usuario (username), finalmente 'Sistema'
    if (evento.usuario_nombre && evento.usuario_nombre.trim() && evento.usuario_nombre !== evento.usuario) {
        return evento.usuario_nombre.trim();
    }
    if (evento.usuario && evento.usuario.trim() && evento.usuario !== 'Sistema') {
        return evento.usuario.trim();
    }
    return 'Sistema';
}

// Función para expandir/colapsar detalles del historial
function toggleHistorialDetails(detailsId) {
    const detailsRow = document.getElementById(detailsId);
    
    if (detailsRow) {
        if (detailsRow.style.display === 'none') {
            detailsRow.style.display = '';
        } else {
            detailsRow.style.display = 'none';
        }
    }
}

// Renderizar historial de equipo en modal
function renderizarHistorialEquipoModal(data, container) {
    const historial = data.historial || [];
    
    if (historial.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de este equipo.
            </div>
        `;
        return;
    }
    
    let infoHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">
                <i class="bi bi-list-ul me-1"></i>Historial de Cambios
            </h6>
            <span class="badge bg-secondary">${historial.length} registro(s)</span>
        </div>
        <div class="table-responsive">
            <table class="table table-sm table-hover table-bordered">
                <thead class="table-dark">
                    <tr>
                        <th style="width: 5%;"></th>
                        <th style="width: 15%;">Fecha y Hora</th>
                        <th style="width: 15%;">Usuario</th>
                        <th style="width: 20%;">Acción</th>
                        <th style="width: 45%;">Descripción</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    historial.forEach((evento, index) => {
        const badgeColor = getBadgeColorAccionEquipo(evento.accion);
        const rowId = `historial-row-${index}`;
        const detailsId = `historial-details-${index}`;
        
        // Generar detalles expandibles solo si hay información adicional
        let detallesHTML = '';
        let tieneDetalles = false;
        
        // Información adicional de datos_nuevos que no esté en la descripción
        if (evento.datos_nuevos || evento.datos_previos) {
            const camposTecnicos = [
                'equipo_id', 'activo', 'faena_id', 'estado_id'
            ];
            
            // Datos nuevos
            if (evento.datos_nuevos) {
                const keys = Object.keys(evento.datos_nuevos).filter(k => 
                    !camposTecnicos.includes(k) && 
                    !k.endsWith('_id') &&
                    evento.datos_nuevos[k] !== null && 
                    evento.datos_nuevos[k] !== undefined &&
                    evento.datos_nuevos[k] !== '' &&
                    !evento.descripcion.includes(k)
                );
                
                if (keys.length > 0) {
                    detallesHTML = '<div class="small">';
                    detallesHTML += '<div class="mb-2"><strong>Información nueva:</strong><ul class="mb-0 mt-1">';
                    keys.forEach(key => {
                        const valor = evento.datos_nuevos[key];
                        const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                    });
                    detallesHTML += '</ul></div>';
                    tieneDetalles = true;
                }
            }
            
            // Datos previos
            if (evento.datos_previos) {
                const keys = Object.keys(evento.datos_previos).filter(k => 
                    !camposTecnicos.includes(k) && 
                    !k.endsWith('_id') &&
                    evento.datos_previos[k] !== null && 
                    evento.datos_previos[k] !== undefined &&
                    evento.datos_previos[k] !== ''
                );
                
                if (keys.length > 0) {
                    if (!tieneDetalles) {
                        detallesHTML = '<div class="small">';
                    }
                    detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información anterior:</strong><ul class="mb-0 mt-1">';
                    keys.forEach(key => {
                        const valor = evento.datos_previos[key];
                        const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                    });
                    detallesHTML += '</ul></div>';
                    tieneDetalles = true;
                }
            }
            
            if (tieneDetalles) {
                detallesHTML += '</div>';
            }
        }
        
        infoHTML += `
            <tr id="${rowId}" class="${tieneDetalles ? 'historial-row-clickable' : ''}" ${tieneDetalles ? `onclick="toggleHistorialDetails('${detailsId}')" style="cursor: pointer;"` : ''}>
                <td class="text-center" style="width: 5%;">
                    ${tieneDetalles ? `<i class="bi bi-info-circle text-muted" style="font-size: 0.9rem;" title="Click para ver más detalles"></i>` : ''}
                </td>
                <td>
                    <small class="text-muted">${evento.fecha_hora_formateada || evento.fecha_hora}</small>
                </td>
                <td>
                    <small><i class="bi bi-person me-1"></i>${obtenerNombreUsuario(evento)}</small>
                </td>
                <td>
                    <span class="badge ${badgeColor}">${evento.accion_display}</span>
                </td>
                <td>
                    <small>${evento.descripcion || '-'}</small>
                    ${tieneDetalles ? ' <span class="text-muted small">(click para más detalles)</span>' : ''}
                </td>
            </tr>
            ${tieneDetalles ? `
            <tr id="${detailsId}" class="historial-details-row" style="display: none;">
                <td colspan="5" class="bg-light">
                    <div class="p-3">
                        ${detallesHTML}
                    </div>
                </td>
            </tr>
            ` : ''}
        `;
    });
    
    infoHTML += `
                </tbody>
            </table>
        </div>
        <style>
            .historial-row-clickable {
                transition: background-color 0.2s;
            }
            .historial-row-clickable:hover {
                background-color: #f8f9fa !important;
            }
            .historial-row-clickable:hover td {
                background-color: #f8f9fa !important;
            }
            .historial-details-row {
                background-color: #f8f9fa;
            }
            .historial-details-row td {
                border-top: none !important;
            }
        </style>
    `;
    
    container.innerHTML = infoHTML;
}

