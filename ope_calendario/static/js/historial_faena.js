// ============================================================================
// HISTORIAL DE FAENA
// ============================================================================
// Este archivo maneja la visualización del historial de cambios de faenas.
// Permite ver todos los eventos y cambios registrados en una faena específica,
// incluyendo asignaciones de personal, modificaciones y eliminaciones.

// Función para obtener el color del badge según el tipo de acción
// Retorna la clase CSS de Bootstrap correspondiente al color del badge
// Parámetros:
//   accion: String - Tipo de acción realizada (ej: 'FAENA_CREADA', 'PERSONAL_ASIGNADO')
// Retorna:
//   String - Clase CSS de Bootstrap para el badge (ej: 'bg-success', 'bg-danger')
function getBadgeColorAccion(accion) {
    // Mapeo de acciones a colores de badges
    const colores = {
        'FAENA_CREADA': 'bg-success',  // Verde para creación
        'FAENA_MODIFICADA': 'bg-primary',  // Azul para modificaciones
        'PERSONAL_ASIGNADO': 'bg-info',  // Azul claro para asignaciones
        'PERSONAL_ELIMINADO': 'bg-danger',  // Rojo para eliminaciones
        'ASIGNACION_MODIFICADA': 'bg-warning text-dark',  // Amarillo para modificaciones de asignación
        'TURNO_MODIFICADO': 'bg-warning text-dark',  // Amarillo para cambios de turno
        'FECHA_MODIFICADA': 'bg-warning text-dark'  // Amarillo para cambios de fecha
    };
    // Retornar color correspondiente o color por defecto si no se encuentra
    return colores[accion] || 'bg-secondary';
}

// Función para mostrar el historial de una faena en un modal
// Abre un modal de Bootstrap y carga el historial desde la API
// Parámetros:
//   faenaId: Number - ID de la faena para la cual mostrar el historial
//   codigoFaena: String - Código de la faena para mostrar en el título del modal
function verHistorialFaena(faenaId, codigoFaena) {
    // Paso 1: Verificar permisos antes de abrir el modal
    // Solo usuarios con permiso pueden ver el historial
    const canVerHistorial = permisos && (permisos.can_ver_historial_faena === true || permisos.can_ver_historial_faena === 'true');
    if (!canVerHistorial) {
        console.log('Debug: No tiene permiso para ver historial. permisos:', permisos);
        alert('No tiene permiso para ver el historial de faenas. Por favor, contacte al administrador si necesita acceso.');
        return;  // Salir sin abrir el modal
    }
    
    // Paso 2: Obtener referencias a los elementos del modal
    const modal = new bootstrap.Modal(document.getElementById('modalHistorialFaena'));
    const modalBody = document.getElementById('modalHistorialFaenaBody');
    const modalTitle = document.getElementById('modalHistorialFaenaLabel');
    
    // Paso 3: Actualizar título del modal con el código de la faena
    modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${codigoFaena}`;
    
    // Paso 4: Mostrar indicador de carga mientras se obtienen los datos
    modalBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando historial...</p>
        </div>
    `;
    
    // Paso 5: Mostrar el modal
    modal.show();
    
    // Paso 6: Obtener historial desde la API
    // apiHistorialFaenaBase se define en el template HTML con la URL base
    const url = apiHistorialFaenaBase.replace('0', faenaId);  // Reemplazar '0' con el ID de la faena
    fetch(url)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Renderizar el historial en el modal
                renderizarHistorialFaenaModal(data, modalBody);
            } else {
                // CASO ERROR: Mostrar mensaje de error
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar historial: ${data.message || 'Error desconocido'}
                    </div>
                `;
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar historial
                </div>
            `;
        });
}

// Función para obtener el nombre completo del usuario que realizó la acción
// Prioriza el nombre completo sobre el username, y usa 'Sistema' como fallback
// Parámetros:
//   evento: Object - Objeto del evento del historial con información del usuario
// Retorna:
//   String - Nombre del usuario o 'Sistema' si no hay información
function obtenerNombreUsuario(evento) {
    // Paso 1: Priorizar usuario_nombre (nombre completo) si está disponible
    // Verificar que exista, no esté vacío y sea diferente del username
    if (evento.usuario_nombre && evento.usuario_nombre.trim() && evento.usuario_nombre !== evento.usuario) {
        return evento.usuario_nombre.trim();
    }
    
    // Paso 2: Si no hay nombre completo, usar username si está disponible
    // Verificar que exista, no esté vacío y no sea 'Sistema'
    if (evento.usuario && evento.usuario.trim() && evento.usuario !== 'Sistema') {
        return evento.usuario.trim();
    }
    
    // Paso 3: Si no hay información de usuario, retornar 'Sistema' como fallback
    // Esto ocurre cuando la acción fue realizada automáticamente por el sistema
    return 'Sistema';
}

// Función para expandir/colapsar detalles del historial
// Alterna la visibilidad de una fila de detalles específica en la tabla del historial
// Parámetros:
//   detailsId: String - ID del elemento de detalles a mostrar/ocultar
function toggleHistorialDetails(detailsId) {
    // Paso 1: Obtener referencia a la fila de detalles
    const detailsRow = document.getElementById(detailsId);
    
    // Paso 2: Si existe la fila, alternar su visibilidad
    if (detailsRow) {
        if (detailsRow.style.display === 'none') {
            // CASO: Detalles ocultos -> Mostrarlos
            detailsRow.style.display = '';
        } else {
            // CASO: Detalles visibles -> Ocultarlos
            detailsRow.style.display = 'none';
        }
    }
}

// Función para renderizar el historial de faena en el modal
// Genera una tabla HTML con todos los eventos del historial, incluyendo detalles expandibles
// Parámetros:
//   data: Object - Objeto con los datos del historial desde la API (debe tener propiedad 'historial')
//   container: HTMLElement - Contenedor donde se insertará el HTML generado
function renderizarHistorialFaenaModal(data, container) {
    // Paso 1: Obtener array de eventos del historial
    const historial = data.historial || [];
    
    // Paso 2: Si no hay eventos, mostrar mensaje informativo
    if (historial.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta faena.
            </div>
        `;
        return;  // Salir de la función
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
    
    // Paso 3: Generar HTML para cada evento del historial
    historial.forEach((evento, index) => {
        // Paso 3.1: Obtener color del badge según el tipo de acción
        const badgeColor = getBadgeColorAccion(evento.accion);
        
        // Paso 3.2: Generar IDs únicos para la fila y sus detalles
        const rowId = `historial-row-${index}`;
        const detailsId = `historial-details-${index}`;
        
        // Paso 3.3: Generar detalles expandibles solo si hay información adicional
        let detallesHTML = '';
        let tieneDetalles = false;
        
        // Paso 3.3.1: Si hay información de personal asignado/eliminado, agregarla a los detalles
        if (evento.personal && evento.personal.nombre_completo) {
            detallesHTML = '<div class="small">';
            detallesHTML += `<div class="mb-2"><strong>Personal:</strong><ul class="mb-0 mt-1">`;
            detallesHTML += `<li>${evento.personal.nombre_completo}${evento.personal.rut ? ` (RUT: ${evento.personal.rut})` : ''}</li>`;
            detallesHTML += '</ul></div>';
            tieneDetalles = true;
        }
        
        // Paso 3.3.2: Agregar información adicional de datos_nuevos que no esté en la descripción
        // Esto incluye campos técnicos que pueden ser útiles para debugging o información detallada
        if (evento.datos_nuevos) {
            // Lista de campos técnicos que se excluyen porque ya están en la descripción o son muy técnicos
            const camposTecnicos = [
                'faena_id', 'personal_id', 'turno_id', 'fecha_inicio', 'fecha_fin',
                'codigo', 'nombre', 'descripcion', 'activo'
            ];
            
            // Filtrar campos que no sean técnicos y tengan valores válidos
            const keys = Object.keys(evento.datos_nuevos).filter(k => 
                !camposTecnicos.includes(k) &&  // Excluir campos técnicos conocidos
                !k.endsWith('_id') &&  // Excluir campos que terminan en '_id'
                evento.datos_nuevos[k] !== null &&  // Excluir valores null
                evento.datos_nuevos[k] !== undefined &&  // Excluir valores undefined
                evento.datos_nuevos[k] !== '' &&  // Excluir strings vacíos
                // Excluir información que ya está en la descripción
                !evento.descripcion.includes(k)
            );
            
            // Si hay campos adicionales válidos, agregarlos a los detalles
            if (keys.length > 0) {
                if (!tieneDetalles) {
                    detallesHTML = '<div class="small">';
                }
                detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información adicional:</strong><ul class="mb-0 mt-1">';
                keys.forEach(key => {
                    const valor = evento.datos_nuevos[key];
                    // Convertir nombre del campo de snake_case a Title Case para mejor legibilidad
                    const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                });
                detallesHTML += '</ul></div>';
                tieneDetalles = true;
            }
        }
        
        // Paso 3.3.3: Cerrar el div de detalles si se creó
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

// Función para renderizar historial de faena (versión para página completa)
// Esta función se mantiene por compatibilidad con páginas que muestran el historial directamente
// (no en modal). Usa historialData que se define en el template HTML.
function renderizarHistorialFaena() {
    // Paso 1: Obtener referencia al contenedor del historial
    const container = document.getElementById('historialContainer');
    
    // Paso 2: Verificar que existan datos de historial
    // historialData se define en el template HTML con los datos del historial
    if (!historialData || historialData.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta faena.
            </div>
        `;
        return;  // Salir de la función
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

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
// Solo se ejecuta si existe el contenedor de historial (página completa, no modal)
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si existe el contenedor de historial antes de renderizar
    if (document.getElementById('historialContainer')) {
        renderizarHistorialFaena();  // Renderizar historial en la página completa
    }
});

