/**
 * Gestión del historial de documentos del personal.
 * 
 * Maneja la carga, renderizado y visualización del historial de cambios
 * de documentos personales, licencias, certificaciones y exámenes.
 */

let historialCompleto = [];

/**
 * Mapeo de tipos de documentos a sus contenedores y configuraciones.
 * Define qué tipo de documento corresponde a cada sección de la interfaz.
 */
const historialConfig = {
    'personal-docs': {
        tipo: 'DOCUMENTO_PERSONAL',
        containerId: 'historialPersonalContainer',
        tbodyId: 'historialPersonalTbody',
        btnId: 'btnToggleHistorialPersonal',
        permisoKey: 'can_ver_historial_documentos_personales'
    },
    'licenses': {
        tipo: 'LICENCIA_CONDUCIR',
        containerId: 'historialLicenciasContainer',
        tbodyId: 'historialLicenciasTbody',
        btnId: 'btnToggleHistorialLicencias',
        permisoKey: 'can_ver_historial_licencias'
    },
    'internal-licenses': {
        tipo: 'LICENCIA_INTERNA',
        containerId: 'historialLicenciasInternasContainer',
        tbodyId: 'historialLicenciasInternasTbody',
        btnId: 'btnToggleHistorialLicenciasInternas',
        permisoKey: 'can_ver_historial_licencias_internas'
    },
    'certifications': {
        tipo: 'CERTIFICACION',
        containerId: 'historialCertificacionesContainer',
        tbodyId: 'historialCertificacionesTbody',
        btnId: 'btnToggleHistorialCertificaciones',
        permisoKey: 'can_ver_historial_certificaciones'
    },
    'exams': {
        tipo: 'EXAMEN',
        containerId: 'historialExamenesContainer',
        tbodyId: 'historialExamenesTbody',
        btnId: 'btnToggleHistorialExamenes',
        permisoKey: 'can_ver_historial_examenes'
    }
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventosHistorial();
    cargarHistorialCompleto();
});

/**
 * Inicializa los eventos para los botones de toggle del historial.
 * 
 * Configura los event listeners para cada sección de historial,
 * verificando permisos antes de habilitar los botones.
 */
function inicializarEventosHistorial() {
    // Asegurar que permisosHistorial esté definido
    const permisos = window.permisosHistorial || {};
    
    // Configurar eventos para cada botón de toggle
    Object.keys(historialConfig).forEach(tabId => {
        const config = historialConfig[tabId];
        const btn = document.getElementById(config.btnId);
        if (btn) {
            // Verificar si el usuario tiene permiso para este historial
            const tienePermiso = permisos[config.permisoKey] === true || permisos[config.permisoKey] === 'true';
            
            if (!tienePermiso) {
                // Deshabilitar el botón si no tiene permiso
                btn.disabled = true;
                btn.classList.add('disabled');
                btn.title = 'No tiene permiso para ver este historial';
                return;
            }
            
            btn.addEventListener('click', function() {
                toggleHistorial(config.containerId, config.btnId, config.tipo);
            });
        }
    });
}

// ============================================================================
// FUNCIONES PARA CARGAR HISTORIAL
// ============================================================================

/**
 * Carga el historial completo de documentos desde la API.
 * 
 * Obtiene todos los eventos del historial y actualiza las secciones
 * que estén visibles en ese momento.
 */
function cargarHistorialCompleto() {
    if (!window.HISTORIAL_DOCUMENTOS_URL) {
        console.error('URL de historial no configurada');
        return;
    }
    
    fetch(window.HISTORIAL_DOCUMENTOS_URL)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                historialCompleto = data.historial || [];
                // Si algún historial está visible, actualizarlo también
                Object.values(historialConfig).forEach(config => {
                    const container = document.getElementById(config.containerId);
                    if (container && container.style.display !== 'none') {
                        renderizarHistorialPorTipo(config.tipo, config.containerId);
                    }
                });
            } else {
                console.error('Error al cargar historial:', data.message);
            }
        })
        .catch(error => {
            console.error('Error al cargar historial:', error);
        });
}

/**
 * Función pública para recargar el historial desde otros scripts.
 * 
 * Útil cuando se agrega, modifica o elimina un documento y se necesita
 * actualizar el historial sin recargar toda la página.
 */
function recargarHistorialDocumentos() {
    cargarHistorialCompleto();
}

// Hacer la función disponible globalmente
window.recargarHistorialDocumentos = recargarHistorialDocumentos;

/**
 * Muestra u oculta el historial de un tipo de documento específico.
 * 
 * Verifica permisos antes de permitir el toggle y renderiza el historial
 * si se está mostrando por primera vez.
 * 
 * @param {string} containerId - ID del contenedor del historial
 * @param {string} btnId - ID del botón de toggle
 * @param {string} tipoDocumento - Tipo de documento (DOCUMENTO_PERSONAL, LICENCIA_CONDUCIR, etc.)
 */
function toggleHistorial(containerId, btnId, tipoDocumento) {
    const container = document.getElementById(containerId);
    const btn = document.getElementById(btnId);
    
    if (!container || !btn) return;
    
    // Verificar permisos antes de permitir el toggle
    const config = Object.values(historialConfig).find(c => c.containerId === containerId);
    if (config) {
        const permisos = window.permisosHistorial || {};
        const tienePermiso = permisos[config.permisoKey] === true || permisos[config.permisoKey] === 'true';
        
        if (!tienePermiso) {
            alert('No tiene permiso para ver este historial. Por favor, contacte al administrador si necesita acceso.');
            return;
        }
    }
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        btn.innerHTML = '<i class="bi bi-chevron-up me-1"></i>Ocultar Historial';
        renderizarHistorialPorTipo(tipoDocumento, containerId);
    } else {
        container.style.display = 'none';
        btn.innerHTML = '<i class="bi bi-chevron-down me-1"></i>Mostrar Historial';
    }
}

/**
 * Renderiza el historial filtrado por tipo de documento en el tbody correspondiente.
 * 
 * @param {string} tipoDocumento - Tipo de documento a filtrar
 * @param {string} containerId - ID del contenedor del historial
 */
function renderizarHistorialPorTipo(tipoDocumento, containerId) {
    // Encontrar el tbody correspondiente
    const config = Object.values(historialConfig).find(c => c.containerId === containerId);
    if (!config) return;
    
    const tbody = document.getElementById(config.tbodyId);
    if (!tbody) return;
    
    // Filtrar historial por tipo de documento
    const historialFiltrado = historialCompleto.filter(item => item.tipo_documento === tipoDocumento);
    
    if (historialFiltrado.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="bi bi-folder-x fs-1"></i>
                    <p class="mt-2">No hay registros en el historial</p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    historialFiltrado.forEach(item => {
        const fechaHora = formatearFechaHora(item.fecha_hora);
        const accionBadge = obtenerBadgeAccion(item.accion);
        const archivoHtml = obtenerHtmlArchivo(item);
        
        html += `
            <tr>
                <td>${escapeHtml(item.tipo_documento_display || item.tipo_documento)}</td>
                <td>${accionBadge}</td>
                <td>${fechaHora}</td>
                <td>${escapeHtml(item.usuario_nombre || item.usuario || 'Sistema')}</td>
                <td>${escapeHtml(item.descripcion || '-')}</td>
                <td class="text-center">${archivoHtml}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

/**
 * Formatea una fecha y hora en formato DD/MM/YYYY HH:MM.
 * 
 * @param {string} fechaHoraStr - Fecha y hora en formato "YYYY-MM-DD HH:MM:SS"
 * @returns {string} Fecha formateada o HTML con "N/A" si no hay fecha
 */
function formatearFechaHora(fechaHoraStr) {
    if (!fechaHoraStr) return '<span class="text-muted">N/A</span>';
    
    try {
        // Formato esperado: "YYYY-MM-DD HH:MM:SS"
        const fecha = new Date(fechaHoraStr.replace(' ', 'T'));
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const año = fecha.getFullYear();
        const horas = String(fecha.getHours()).padStart(2, '0');
        const minutos = String(fecha.getMinutes()).padStart(2, '0');
        
        return `${dia}/${mes}/${año} ${horas}:${minutos}`;
    } catch (e) {
        return fechaHoraStr;
    }
}

/**
 * Obtiene el HTML del badge según el tipo de acción del historial.
 * 
 * @param {string} accion - Tipo de acción (DOCUMENTO_AGREGADO, DOCUMENTO_ELIMINADO, etc.)
 * @returns {string} HTML del badge con el color correspondiente
 */
function obtenerBadgeAccion(accion) {
    const badges = {
        'DOCUMENTO_AGREGADO': '<span class="badge bg-success">Agregado</span>',
        'DOCUMENTO_ELIMINADO': '<span class="badge bg-danger">Eliminado</span>',
        'DOCUMENTO_MODIFICADO': '<span class="badge bg-warning text-dark">Modificado</span>',
        'DOCUMENTO_REEMPLAZADO': '<span class="badge bg-info">Reemplazado</span>'
    };
    
    return badges[accion] || `<span class="badge bg-secondary">${accion}</span>`;
}

/**
 * Escapa caracteres HTML para prevenir XSS.
 * 
 * @param {string} text - Texto a escapar
 * @returns {string} Texto escapado
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Obtiene el HTML para mostrar el archivo del historial.
 * 
 * Muestra botones para visualizar/descargar archivos eliminados.
 * 
 * @param {Object} item - Item del historial
 * @returns {string} HTML del botón para ver el archivo o "-" si no aplica
 */
function obtenerHtmlArchivo(item) {
    // Solo mostrar el archivo si el documento fue ELIMINADO
    // Si fue creado/agregado/modificado, el archivo está disponible en la tabla principal
    if (item.accion !== 'DOCUMENTO_ELIMINADO') {
        return '<span class="text-muted">-</span>';
    }
    
    // Si fue eliminado, mostrar botón para ver el archivo (si existe)
    if (item.archivo_url) {
        return `
            <a href="${escapeHtml(item.archivo_url)}" target="_blank" class="btn btn-sm btn-primary" title="Ver documento eliminado">
                <i class="bi bi-eye"></i> Ver
            </a>
        `;
    }
    
    // Si hay ruta de archivo pero no URL, intentar construir la URL
    if (item.archivo_ruta) {
        // Construir URL relativa desde la ruta del archivo
        // Normalizar las barras (Windows usa \, Unix usa /)
        const archivoUrl = '/' + item.archivo_ruta.replace(/\\/g, '/');
        const nombreArchivo = item.archivo_ruta.split(/[/\\]/).pop();
        return `
            <a href="${escapeHtml(archivoUrl)}" target="_blank" class="btn btn-sm btn-primary" title="Ver documento eliminado: ${escapeHtml(nombreArchivo)}">
                <i class="bi bi-eye"></i> Ver
            </a>
        `;
    }
    
    return '<span class="text-muted">-</span>';
}

