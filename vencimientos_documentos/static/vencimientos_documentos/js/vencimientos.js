/**
 * JavaScript para el panel de vencimientos de documentos.
 */

const API_PERSONAL = '/vencimientos/api/personal/';
const API_MAQUINARIAS = '/vencimientos/api/maquinarias/';
const API_EXPORTAR_PERSONAL = '/vencimientos/api/exportar/personal/';
const API_EXPORTAR_MAQUINARIAS = '/vencimientos/api/exportar/maquinarias/';
const API_EJECUTAR_PROCESAMIENTO = '/vencimientos/api/ejecutar-procesamiento/';

let documentosPersonal = [];
let documentosMaquinarias = [];

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Cargar datos iniciales
    cargarDocumentosPersonal();
    
    // Event listeners para tabs
    const personalTab = document.getElementById('personal-tab');
    const maquinariasTab = document.getElementById('maquinarias-tab');
    
    if (personalTab) {
        personalTab.addEventListener('shown.bs.tab', function() {
            if (documentosPersonal.length === 0) {
                cargarDocumentosPersonal();
            }
        });
    }
    
    if (maquinariasTab) {
        maquinariasTab.addEventListener('shown.bs.tab', function() {
            if (documentosMaquinarias.length === 0) {
                cargarDocumentosMaquinarias();
            }
        });
    }
    
    // Event listeners para Enter en filtros
    const filtrosPersonal = ['filtroBuscarPersonal'];
    filtrosPersonal.forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    cargarDocumentosPersonal();
                }
            });
        }
    });
    
    const filtrosMaquinarias = ['filtroBuscarMaquinarias'];
    filtrosMaquinarias.forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    cargarDocumentosMaquinarias();
                }
            });
        }
    });
});

/**
 * Carga los documentos de personal desde la API.
 */
function cargarDocumentosPersonal() {
    const tbody = document.getElementById('tbodyPersonal');
    if (!tbody) return;
    
    // Mostrar loading
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </td>
        </tr>
    `;
    
    // Obtener filtros
    const filtros = obtenerFiltrosPersonal();
    
    // Construir URL con parámetros
    const params = new URLSearchParams();
    if (filtros.buscar) params.append('buscar', filtros.buscar);
    params.append('solo_activos', 'true');  // Siempre solo activos
    
    const url = API_PERSONAL + (params.toString() ? '?' + params.toString() : '');
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            documentosPersonal = data.documentos;
            renderizarTablaPersonal(documentosPersonal);
        } else {
            const errorMsg = data.error || 'Error al cargar documentos de personal';
            console.error('Error en respuesta:', errorMsg);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>${escapeHtml(errorMsg)}
                    </td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>Error al cargar los datos: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    });
}

/**
 * Carga los documentos de maquinarias desde la API.
 */
function cargarDocumentosMaquinarias() {
    const tbody = document.getElementById('tbodyMaquinarias');
    if (!tbody) return;
    
    // Mostrar loading
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </td>
        </tr>
    `;
    
    // Obtener filtros
    const filtros = obtenerFiltrosMaquinarias();
    
    // Construir URL con parámetros
    const params = new URLSearchParams();
    if (filtros.buscar) params.append('buscar', filtros.buscar);
    params.append('solo_activos', 'true');  // Siempre solo activos
    
    const url = API_MAQUINARIAS + (params.toString() ? '?' + params.toString() : '');
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            documentosMaquinarias = data.documentos;
            renderizarTablaMaquinarias(documentosMaquinarias);
        } else {
            const errorMsg = data.error || 'Error al cargar documentos de maquinarias';
            console.error('Error en respuesta:', errorMsg);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>${escapeHtml(errorMsg)}
                    </td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>Error al cargar los datos: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    });
}

/**
 * Obtiene los valores de los filtros de personal.
 */
function obtenerFiltrosPersonal() {
    return {
        buscar: document.getElementById('filtroBuscarPersonal')?.value.trim() || '',
        solo_activos: true  // Siempre solo activos
    };
}

/**
 * Obtiene los valores de los filtros de maquinarias.
 */
function obtenerFiltrosMaquinarias() {
    return {
        buscar: document.getElementById('filtroBuscarMaquinarias')?.value.trim() || '',
        solo_activos: true  // Siempre solo activos
    };
}

/**
 * Renderiza la tabla de documentos de personal.
 */
function renderizarTablaPersonal(documentos) {
    const tbody = document.getElementById('tbodyPersonal');
    if (!tbody) return;
    
    if (documentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="bi bi-inbox me-2"></i>No se encontraron documentos
                </td>
            </tr>
        `;
        return;
    }
    
        tbody.innerHTML = documentos.map(doc => {
        const colorFila = obtenerColorFila(doc.dias_restantes);
        return `
            <tr class="${colorFila}">
                <td>${escapeHtml(doc.personal_nombre)}</td>
                <td>${escapeHtml(doc.personal_rut)}</td>
                <td>${escapeHtml(doc.tipo_nombre)}</td>
                <td>${escapeHtml(doc.nombre)}</td>
                <td>${doc.fecha_vencimiento || 'N/A'}</td>
                <td>${doc.dias_restantes !== null ? doc.dias_restantes : 'N/A'}</td>
                <td>
                    <span class="badge ${doc.badge_class} ${doc.estado === 'amarillo' ? 'amarillo' : doc.estado === 'naranja' ? 'naranja' : ''} badge-estado">
                        ${doc.icono} ${doc.texto_estado}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Renderiza la tabla de documentos de maquinarias.
 */
function renderizarTablaMaquinarias(documentos) {
    const tbody = document.getElementById('tbodyMaquinarias');
    if (!tbody) return;
    
    if (documentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="bi bi-inbox me-2"></i>No se encontraron documentos
                </td>
            </tr>
        `;
        return;
    }
    
        tbody.innerHTML = documentos.map(doc => {
        const colorFila = obtenerColorFila(doc.dias_restantes);
        return `
            <tr class="${colorFila}">
                <td>${escapeHtml(doc.equipo_nombre)}</td>
                <td>${escapeHtml(doc.equipo_codigo)}</td>
                <td>${escapeHtml(doc.equipo_patente || '')}</td>
                <td>${escapeHtml(doc.nombre)}</td>
                <td>${doc.fecha_vencimiento || 'N/A'}</td>
                <td>${doc.dias_restantes !== null ? doc.dias_restantes : 'N/A'}</td>
                <td>
                    <span class="badge ${doc.badge_class} ${doc.estado === 'amarillo' ? 'amarillo' : doc.estado === 'naranja' ? 'naranja' : ''} badge-estado">
                        ${doc.icono} ${doc.texto_estado}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Obtiene la clase CSS para el color de la fila según los días restantes.
 */
function obtenerColorFila(diasRestantes) {
    if (diasRestantes === null) return '';
    if (diasRestantes < 0) return 'table-danger';  // Vencido
    if (diasRestantes <= 14) return 'table-danger';  // Crítico (rojo) - 14 hacia abajo
    if (diasRestantes <= 29) return 'table-warning naranja';  // Naranja (29-15 días)
    if (diasRestantes <= 44) return 'table-warning amarillo';  // Amarillo (44-30 días)
    return '';  // Más de 45 días (no se muestran)
}

/**
 * Exporta los documentos de personal a Excel.
 */
function exportarExcelPersonal() {
    const filtros = obtenerFiltrosPersonal();
    const params = new URLSearchParams();
    if (filtros.buscar) params.append('buscar', filtros.buscar);
    params.append('solo_activos', 'true');  // Siempre solo activos
    
    const url = API_EXPORTAR_PERSONAL + (params.toString() ? '?' + params.toString() : '');
    window.location.href = url;
}

/**
 * Exporta los documentos de maquinarias a Excel.
 */
function exportarExcelMaquinarias() {
    const filtros = obtenerFiltrosMaquinarias();
    const params = new URLSearchParams();
    if (filtros.buscar) params.append('buscar', filtros.buscar);
    params.append('solo_activos', 'true');  // Siempre solo activos
    
    const url = API_EXPORTAR_MAQUINARIAS + (params.toString() ? '?' + params.toString() : '');
    window.location.href = url;
}

/**
 * Obtiene el valor de una cookie.
 */
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

/**
 * Escapa HTML para prevenir XSS.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Muestra un mensaje de error.
 */
function mostrarError(mensaje) {
    // Puedes implementar un sistema de notificaciones aquí
    console.error(mensaje);
    alert(mensaje);
}

/**
 * Ejecuta el procesamiento de vencimientos manualmente (solo para pruebas).
 */
function ejecutarProcesamientoVencimientos() {
    if (!confirm('¿Está seguro de ejecutar el procesamiento de vencimientos? Esto creará notificaciones para todos los documentos próximos a vencer.')) {
        return;
    }
    
    // Deshabilitar el botón mientras se procesa
    const boton = event.target.closest('button');
    const textoOriginal = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Procesando...';
    
    fetch(API_EJECUTAR_PROCESAMIENTO, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        boton.disabled = false;
        boton.innerHTML = textoOriginal;
        
        if (data.success) {
            alert('✓ ' + data.message);
        } else {
            alert('✗ Error: ' + (data.error || 'Error desconocido'));
        }
    })
    .catch(error => {
        boton.disabled = false;
        boton.innerHTML = textoOriginal;
        console.error('Error:', error);
        alert('✗ Error al ejecutar el procesamiento: ' + error.message);
    });
}

