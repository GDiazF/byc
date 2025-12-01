// ============================================================================
// HISTORIAL DE FAENA
// ============================================================================

// Función para obtener el color del badge según la acción
function getBadgeColorAccion(accion) {
    const colores = {
        'FAENA_CREADA': 'bg-success',
        'FAENA_MODIFICADA': 'bg-primary',
        'PERSONAL_ASIGNADO': 'bg-info',
        'PERSONAL_ELIMINADO': 'bg-danger',
        'ASIGNACION_MODIFICADA': 'bg-warning text-dark',
        'TURNO_MODIFICADO': 'bg-warning text-dark',
        'FECHA_MODIFICADA': 'bg-warning text-dark'
    };
    return colores[accion] || 'bg-secondary';
}

// Función para mostrar el historial de una faena en un modal
function verHistorialFaena(faenaId, codigoFaena) {
    // Verificar permisos antes de abrir el modal
    const canVerHistorial = permisos && (permisos.can_ver_historial_faena === true || permisos.can_ver_historial_faena === 'true');
    if (!canVerHistorial) {
        console.log('Debug: No tiene permiso para ver historial. permisos:', permisos);
        alert('No tiene permiso para ver el historial de faenas. Por favor, contacte al administrador si necesita acceso.');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('modalHistorialFaena'));
    const modalBody = document.getElementById('modalHistorialFaenaBody');
    const modalTitle = document.getElementById('modalHistorialFaenaLabel');
    
    // Actualizar título
    modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${codigoFaena}`;
    
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
    const url = apiHistorialFaenaBase.replace('0', faenaId);
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarHistorialFaenaModal(data, modalBody);
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

// Renderizar historial de faena en modal
function renderizarHistorialFaenaModal(data, container) {
    const historial = data.historial || [];
    
    if (historial.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta faena.
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
        const badgeColor = getBadgeColorAccion(evento.accion);
        const rowId = `historial-row-${index}`;
        const detailsId = `historial-details-${index}`;
        
        // Generar detalles expandibles solo si hay información adicional
        let detallesHTML = '';
        let tieneDetalles = false;
        
        // Personal asignado/eliminado - mostrar información completa
        if (evento.personal && evento.personal.nombre_completo) {
            detallesHTML = '<div class="small">';
            detallesHTML += `<div class="mb-2"><strong>Personal:</strong><ul class="mb-0 mt-1">`;
            detallesHTML += `<li>${evento.personal.nombre_completo}${evento.personal.rut ? ` (RUT: ${evento.personal.rut})` : ''}</li>`;
            detallesHTML += '</ul></div>';
            tieneDetalles = true;
        }
        
        // Información adicional de datos_nuevos que no esté en la descripción
        if (evento.datos_nuevos) {
            const camposTecnicos = [
                'faena_id', 'personal_id', 'turno_id', 'fecha_inicio', 'fecha_fin',
                'codigo', 'nombre', 'descripcion', 'activo'
            ];
            
            const keys = Object.keys(evento.datos_nuevos).filter(k => 
                !camposTecnicos.includes(k) && 
                !k.endsWith('_id') &&
                evento.datos_nuevos[k] !== null && 
                evento.datos_nuevos[k] !== undefined &&
                evento.datos_nuevos[k] !== '' &&
                // Excluir información que ya está en la descripción
                !evento.descripcion.includes(k)
            );
            
            if (keys.length > 0) {
                if (!tieneDetalles) {
                    detallesHTML = '<div class="small">';
                }
                detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información adicional:</strong><ul class="mb-0 mt-1">';
                keys.forEach(key => {
                    const valor = evento.datos_nuevos[key];
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

// Renderizar historial de faena (versión para página completa - mantenida por compatibilidad)
function renderizarHistorialFaena() {
    const container = document.getElementById('historialContainer');
    
    if (!historialData || historialData.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta faena.
            </div>
        `;
        return;
    }
    
    let infoHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">
                <i class="bi bi-list-ul me-1"></i>Historial de Cambios
            </h6>
            <span class="badge bg-secondary">${historialData.length} registro(s)</span>
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
    
    historialData.forEach((evento, index) => {
        const badgeColor = getBadgeColorAccion(evento.accion);
        const rowId = `historial-row-${index}`;
        const detailsId = `historial-details-${index}`;
        
        // Generar detalles expandibles solo si hay información adicional
        let detallesHTML = '';
        let tieneDetalles = false;
        
        // Personal asignado/eliminado - mostrar información completa
        if (evento.personal && evento.personal.nombre_completo) {
            detallesHTML = '<div class="small">';
            detallesHTML += `<div class="mb-2"><strong>Personal:</strong><ul class="mb-0 mt-1">`;
            detallesHTML += `<li>${evento.personal.nombre_completo}${evento.personal.rut ? ` (RUT: ${evento.personal.rut})` : ''}</li>`;
            detallesHTML += '</ul></div>';
            tieneDetalles = true;
        }
        
        // Información adicional de datos_nuevos que no esté en la descripción
        if (evento.datos_nuevos) {
            const camposTecnicos = [
                'faena_id', 'personal_id', 'turno_id', 'fecha_inicio', 'fecha_fin',
                'codigo', 'nombre', 'descripcion', 'activo'
            ];
            
            const keys = Object.keys(evento.datos_nuevos).filter(k => 
                !camposTecnicos.includes(k) && 
                !k.endsWith('_id') &&
                evento.datos_nuevos[k] !== null && 
                evento.datos_nuevos[k] !== undefined &&
                evento.datos_nuevos[k] !== '' &&
                // Excluir información que ya está en la descripción
                !evento.descripcion.includes(k)
            );
            
            if (keys.length > 0) {
                if (!tieneDetalles) {
                    detallesHTML = '<div class="small">';
                }
                detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información adicional:</strong><ul class="mb-0 mt-1">';
                keys.forEach(key => {
                    const valor = evento.datos_nuevos[key];
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

// Inicializar cuando el DOM esté listo (solo para página completa)
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('historialContainer')) {
        renderizarHistorialFaena();
    }
});

