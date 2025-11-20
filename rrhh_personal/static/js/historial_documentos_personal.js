// ============================================================================
// HISTORIAL DE DOCUMENTOS PERSONAL
// ============================================================================

let historialCompleto = [];

// Mapeo de tipos de documentos a sus contenedores
const historialConfig = {
    'personal-docs': {
        tipo: 'DOCUMENTO_PERSONAL',
        containerId: 'historialPersonalContainer',
        tbodyId: 'historialPersonalTbody',
        btnId: 'btnToggleHistorialPersonal'
    },
    'licenses': {
        tipo: 'LICENCIA_CONDUCIR',
        containerId: 'historialLicenciasContainer',
        tbodyId: 'historialLicenciasTbody',
        btnId: 'btnToggleHistorialLicencias'
    },
    'internal-licenses': {
        tipo: 'LICENCIA_INTERNA',
        containerId: 'historialLicenciasInternasContainer',
        tbodyId: 'historialLicenciasInternasTbody',
        btnId: 'btnToggleHistorialLicenciasInternas'
    },
    'certifications': {
        tipo: 'CERTIFICACION',
        containerId: 'historialCertificacionesContainer',
        tbodyId: 'historialCertificacionesTbody',
        btnId: 'btnToggleHistorialCertificaciones'
    },
    'exams': {
        tipo: 'EXAMEN',
        containerId: 'historialExamenesContainer',
        tbodyId: 'historialExamenesTbody',
        btnId: 'btnToggleHistorialExamenes'
    }
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventosHistorial();
    cargarHistorialCompleto();
});

function inicializarEventosHistorial() {
    // Configurar eventos para cada botón de toggle
    Object.keys(historialConfig).forEach(tabId => {
        const config = historialConfig[tabId];
        const btn = document.getElementById(config.btnId);
        if (btn) {
            btn.addEventListener('click', function() {
                toggleHistorial(config.containerId, config.btnId, config.tipo);
            });
        }
    });
}

// ============================================================================
// FUNCIONES PARA CARGAR HISTORIAL
// ============================================================================

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

// Función pública para recargar el historial desde otros scripts
function recargarHistorialDocumentos() {
    cargarHistorialCompleto();
}

// Hacer la función disponible globalmente
window.recargarHistorialDocumentos = recargarHistorialDocumentos;

function toggleHistorial(containerId, btnId, tipoDocumento) {
    const container = document.getElementById(containerId);
    const btn = document.getElementById(btnId);
    
    if (!container || !btn) return;
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        btn.innerHTML = '<i class="bi bi-chevron-up me-1"></i>Ocultar Historial';
        renderizarHistorialPorTipo(tipoDocumento, containerId);
    } else {
        container.style.display = 'none';
        btn.innerHTML = '<i class="bi bi-chevron-down me-1"></i>Mostrar Historial';
    }
}

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

function obtenerBadgeAccion(accion) {
    const badges = {
        'DOCUMENTO_AGREGADO': '<span class="badge bg-success">Agregado</span>',
        'DOCUMENTO_ELIMINADO': '<span class="badge bg-danger">Eliminado</span>',
        'DOCUMENTO_MODIFICADO': '<span class="badge bg-warning text-dark">Modificado</span>',
        'DOCUMENTO_REEMPLAZADO': '<span class="badge bg-info">Reemplazado</span>'
    };
    
    return badges[accion] || `<span class="badge bg-secondary">${accion}</span>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
                <i class="bi bi-eye"></i>
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
                <i class="bi bi-eye"></i>
            </a>
        `;
    }
    
    return '<span class="text-muted">-</span>';
}

