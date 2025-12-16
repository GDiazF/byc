// ============================================================================
// HISTORIAL DE EQUIPOS
// ============================================================================
// Este archivo maneja la visualización del historial de cambios de equipos.
// Incluye funciones para mostrar el historial en un modal con detalles expandibles.

// Función helper para obtener el color del badge según el tipo de acción realizada
// Asigna colores visuales para facilitar la identificación rápida del tipo de acción
// Parámetros:
//   accion: Código de la acción realizada (ej: 'EQUIPO_CREADO', 'EQUIPO_MODIFICADO')
// Retorna:
//   String con el nombre de la clase de color de Bootstrap para el badge
function getBadgeColorAccionEquipo(accion) {
    // Mapeo de acciones a colores de Bootstrap
    // Verde (success): acciones positivas (crear, activar)
    // Azul (primary): modificaciones normales
    // Rojo (danger): eliminaciones y desactivaciones
    // Amarillo (warning): modificaciones de estados manuales
    // Azul claro (info): asignaciones de estados manuales
    const colores = {
        'EQUIPO_CREADO': 'bg-success',  // Verde para creación
        'EQUIPO_MODIFICADO': 'bg-primary',  // Azul para modificación
        'EQUIPO_ACTIVADO': 'bg-success',  // Verde para activación
        'EQUIPO_DESACTIVADO': 'bg-danger',  // Rojo para desactivación
        'EQUIPO_ELIMINADO': 'bg-danger',  // Rojo para eliminación
        'ESTADO_MANUAL_ASIGNADO': 'bg-info',  // Azul claro para asignación de estado manual
        'ESTADO_MANUAL_MODIFICADO': 'bg-warning text-dark',  // Amarillo para modificación de estado manual
        'ESTADO_MANUAL_ELIMINADO': 'bg-danger',  // Rojo para eliminación de estado manual
        'ASIGNACION_FAENA_CREADA': 'bg-success',  // Verde para creación de asignación a faena
        'ASIGNACION_FAENA_MODIFICADA': 'bg-warning text-dark',  // Amarillo para modificación de asignación
        'ASIGNACION_FAENA_ELIMINADA': 'bg-danger'  // Rojo para eliminación de asignación
    };
    return colores[accion] || 'bg-secondary';  // Color por defecto (gris) si la acción no está en el mapeo
}

// Función principal para mostrar el historial de un equipo en un modal
// Carga el historial desde el servidor mediante AJAX y lo muestra en un modal de Bootstrap
// Parámetros:
//   equipoId: ID del equipo cuyo historial se va a mostrar
//   nombreEquipo: Nombre del equipo (se muestra en el título del modal)
function verHistorialEquipo(equipoId, nombreEquipo) {
    // Paso 1: Obtener referencias a los elementos del modal
    const modal = new bootstrap.Modal(document.getElementById('modalHistorialEquipo'));  // Instancia del modal
    const modalBody = document.getElementById('modalHistorialEquipoBody');  // Cuerpo del modal donde se mostrará el historial
    const modalTitle = document.getElementById('modalHistorialEquipoLabel');  // Título del modal
    
    // Paso 2: Actualizar título del modal con el nombre del equipo
    modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${nombreEquipo}`;
    
    // Paso 3: Mostrar indicador de carga mientras se obtienen los datos
    // Esto mejora la experiencia del usuario mostrando que algo está pasando
    modalBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando historial...</p>
        </div>
    `;
    
    // Paso 4: Mostrar el modal (los datos se cargarán después mediante AJAX)
    modal.show();
    
    // Paso 5: Obtener historial desde la API mediante petición AJAX
    // apiHistorialEquipoBase se define en el template HTML con la URL base (contiene '0' como placeholder)
    const url = apiHistorialEquipoBase.replace('0', equipoId);  // Reemplazar '0' con el ID real del equipo
    fetch(url)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: El historial se cargó correctamente
                // Renderizar el historial en el modal
                renderizarHistorialEquipoModal(data, modalBody);
            } else {
                // CASO ERROR: El servidor retornó un error
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
            console.error('Error:', error);  // Registrar error en consola para debugging
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar historial
                </div>
            `;
        });
}

// Función helper para obtener el nombre completo del usuario desde un evento del historial
// Prioriza el nombre completo sobre el username, y usa 'Sistema' como valor por defecto
// Parámetros:
//   evento: Objeto del historial que contiene información del usuario
// Retorna:
//   String con el nombre del usuario (nombre completo, username o 'Sistema')
function obtenerNombreUsuario(evento) {
    // Priorizar usuario_nombre (nombre completo), luego usuario (username), finalmente 'Sistema'
    if (evento.usuario_nombre && evento.usuario_nombre.trim() && evento.usuario_nombre !== evento.usuario) {
        return evento.usuario_nombre.trim();  // Usar nombre completo si está disponible y es diferente del username
    }
    if (evento.usuario && evento.usuario.trim() && evento.usuario !== 'Sistema') {
        return evento.usuario.trim();  // Usar username si está disponible y no es 'Sistema'
    }
    return 'Sistema';  // Valor por defecto si no hay información de usuario
}

// Función para expandir/colapsar los detalles adicionales de una fila del historial
// Se ejecuta cuando el usuario hace clic en una fila que tiene detalles expandibles
// Parámetros:
//   detailsId: ID del elemento que contiene los detalles a mostrar/ocultar
function toggleHistorialDetails(detailsId) {
    const detailsRow = document.getElementById(detailsId);
    
    if (detailsRow) {
        // Alternar visibilidad: si está oculto, mostrarlo; si está visible, ocultarlo
        if (detailsRow.style.display === 'none') {
            detailsRow.style.display = '';  // Mostrar detalles
        } else {
            detailsRow.style.display = 'none';  // Ocultar detalles
        }
    }
}

// Función para renderizar el historial de un equipo en el modal
// Genera una tabla HTML con todos los eventos del historial, incluyendo detalles expandibles
// Parámetros:
//   data: Objeto con los datos del historial (contiene array 'historial')
//   container: Elemento DOM donde se insertará el HTML generado
function renderizarHistorialEquipoModal(data, container) {
    // Paso 1: Obtener el array de eventos del historial (o array vacío si no existe)
    const historial = data.historial || [];
    
    // Paso 2: Si no hay eventos en el historial, mostrar mensaje informativo
    if (historial.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de este equipo.
            </div>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar encabezado de la tabla con contador de registros
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
    
    // Paso 4: Generar filas de la tabla para cada evento del historial
    historial.forEach((evento, index) => {
        // Paso 4.1: Obtener color del badge según el tipo de acción
        const badgeColor = getBadgeColorAccionEquipo(evento.accion);
        
        // Paso 4.2: Generar IDs únicos para la fila y sus detalles expandibles
        const rowId = `historial-row-${index}`;  // ID de la fila principal
        const detailsId = `historial-details-${index}`;  // ID de la fila de detalles
        
        // Paso 4.3: Generar detalles expandibles solo si hay información adicional relevante
        // Los detalles muestran datos nuevos y previos que no están en la descripción principal
        let detallesHTML = '';  // HTML para los detalles expandibles
        let tieneDetalles = false;  // Flag para indicar si hay detalles que mostrar
        
        // Verificar si hay datos nuevos o previos que mostrar
        if (evento.datos_nuevos || evento.datos_previos) {
            // Lista de campos técnicos que no deben mostrarse (IDs internos, flags, etc.)
            const camposTecnicos = [
                'equipo_id', 'activo', 'faena_id', 'estado_id'
            ];
            
            // Paso 4.3.1: Procesar datos nuevos (valores después del cambio)
            if (evento.datos_nuevos) {
                // Filtrar campos que:
                // - No están en la lista de campos técnicos
                // - No terminan en '_id' (son IDs internos)
                // - Tienen valores válidos (no null, undefined o vacío)
                // - No están ya incluidos en la descripción principal
                const keys = Object.keys(evento.datos_nuevos).filter(k => 
                    !camposTecnicos.includes(k) && 
                    !k.endsWith('_id') &&
                    evento.datos_nuevos[k] !== null && 
                    evento.datos_nuevos[k] !== undefined &&
                    evento.datos_nuevos[k] !== '' &&
                    !evento.descripcion.includes(k)  // No mostrar si ya está en la descripción
                );
                
                // Si hay campos nuevos relevantes, generar HTML para mostrarlos
                if (keys.length > 0) {
                    detallesHTML = '<div class="small">';
                    detallesHTML += '<div class="mb-2"><strong>Información nueva:</strong><ul class="mb-0 mt-1">';
                    keys.forEach(key => {
                        const valor = evento.datos_nuevos[key];
                        // Convertir nombre de campo de snake_case a formato legible (ej: 'nombre_equipo' -> 'Nombre Equipo')
                        const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                    });
                    detallesHTML += '</ul></div>';
                    tieneDetalles = true;  // Marcar que hay detalles para mostrar
                }
            }
            
            // Paso 4.3.2: Procesar datos previos (valores antes del cambio)
            if (evento.datos_previos) {
                // Filtrar campos similares a los datos nuevos, pero sin verificar si están en la descripción
                // (los datos previos siempre son útiles para comparar)
                const keys = Object.keys(evento.datos_previos).filter(k => 
                    !camposTecnicos.includes(k) && 
                    !k.endsWith('_id') &&
                    evento.datos_previos[k] !== null && 
                    evento.datos_previos[k] !== undefined &&
                    evento.datos_previos[k] !== ''
                );
                
                // Si hay campos previos relevantes, generar HTML para mostrarlos
                if (keys.length > 0) {
                    if (!tieneDetalles) {
                        detallesHTML = '<div class="small">';  // Iniciar contenedor si no existe
                    }
                    detallesHTML += '<div class="mt-2 pt-2 border-top"><strong>Información anterior:</strong><ul class="mb-0 mt-1">';
                    keys.forEach(key => {
                        const valor = evento.datos_previos[key];
                        // Convertir nombre de campo a formato legible
                        const nombreCampo = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detallesHTML += `<li><strong>${nombreCampo}:</strong> ${valor}</li>`;
                    });
                    detallesHTML += '</ul></div>';
                    tieneDetalles = true;  // Marcar que hay detalles para mostrar
                }
            }
            
            // Cerrar contenedor de detalles si se abrió
            if (tieneDetalles) {
                detallesHTML += '</div>';
            }
        }
        
        // Paso 4.4: Generar HTML de la fila principal del evento
        // Si tiene detalles, la fila es clickeable para expandir/colapsar
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
    
    // Paso 5: Cerrar la tabla y agregar estilos CSS para las filas clickeables
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
    
    // Paso 6: Insertar el HTML generado en el contenedor del modal
    container.innerHTML = infoHTML;
}

