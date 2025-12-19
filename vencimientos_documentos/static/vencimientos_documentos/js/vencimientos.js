/**
 * ============================================================================
 * JAVASCRIPT PARA EL PANEL DE VENCIMIENTOS DE DOCUMENTOS
 * ============================================================================
 * Este módulo maneja la lógica JavaScript para el panel de vencimientos,
 * incluyendo carga de datos desde APIs, renderizado de tablas, filtros,
 * exportación a Excel y ejecución manual del procesamiento de vencimientos.
 * ============================================================================
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
 * Carga los documentos de personal próximos a vencer desde la API.
 * 
 * Hace una petición GET a la API de vencimientos de personal, aplica los filtros
 * configurados y renderiza los resultados en la tabla correspondiente.
 * Muestra un spinner de carga mientras se obtienen los datos.
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
 * Carga los documentos de maquinarias próximos a vencer desde la API.
 * 
 * Hace una petición GET a la API de vencimientos de maquinarias, aplica los filtros
 * configurados y renderiza los resultados en la tabla correspondiente.
 * Muestra un spinner de carga mientras se obtienen los datos.
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
 * Obtiene los valores actuales de los filtros de personal.
 * 
 * @returns {Object} Objeto con los valores de los filtros:
 *                   - buscar (string): Texto de búsqueda
 *                   - solo_activos (boolean): Siempre true
 */
function obtenerFiltrosPersonal() {
    return {
        buscar: document.getElementById('filtroBuscarPersonal')?.value.trim() || '',
        solo_activos: true  // Siempre solo activos
    };
}

/**
 * Obtiene los valores actuales de los filtros de maquinarias.
 * 
 * @returns {Object} Objeto con los valores de los filtros:
 *                   - buscar (string): Texto de búsqueda
 *                   - solo_activos (boolean): Siempre true
 */
function obtenerFiltrosMaquinarias() {
    return {
        buscar: document.getElementById('filtroBuscarMaquinarias')?.value.trim() || '',
        solo_activos: true  // Siempre solo activos
    };
}

/**
 * Renderiza la tabla de documentos de personal con los datos proporcionados.
 * 
 * Genera las filas HTML de la tabla con la información de cada documento,
 * aplicando colores según el estado de vencimiento. Si no hay documentos,
 * muestra un mensaje indicando que no se encontraron resultados.
 * 
 * @param {Array} documentos - Array de objetos con información de documentos próximos a vencer.
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
 * Renderiza la tabla de documentos de maquinarias con los datos proporcionados.
 * 
 * Genera las filas HTML de la tabla con la información de cada documento,
 * aplicando colores según el estado de vencimiento. Si no hay documentos,
 * muestra un mensaje indicando que no se encontraron resultados.
 * 
 * @param {Array} documentos - Array de objetos con información de documentos próximos a vencer.
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
 * Obtiene la clase CSS para el color de fondo de la fila según los días restantes.
 * 
 * Determina el color de fondo de una fila de tabla según el estado de vencimiento:
 * - table-danger: Vencido o crítico (< 15 días)
 * - table-warning: Por vencer (15-44 días)
 * - Sin clase: Más de 45 días o sin fecha
 * 
 * @param {number|null} diasRestantes - Días restantes hasta el vencimiento.
 *                                      null si no hay fecha de vencimiento.
 * @returns {string} Clase CSS de Bootstrap para el color de fondo de la fila.
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
 * Exporta los documentos de personal a un archivo Excel.
 * 
 * Construye la URL de exportación con los filtros actuales y redirige al navegador
 * para descargar el archivo Excel generado por el servidor.
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
 * Exporta los documentos de maquinarias a un archivo Excel.
 * 
 * Construye la URL de exportación con los filtros actuales y redirige al navegador
 * para descargar el archivo Excel generado por el servidor.
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
 * Obtiene el valor de una cookie por su nombre.
 * 
 * @param {string} name - Nombre de la cookie.
 * @returns {string|null} Valor de la cookie o null si no existe.
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
 * Escapa caracteres HTML especiales para prevenir ataques XSS.
 * 
 * @param {string} text - Texto a escapar.
 * @returns {string} Texto escapado seguro para insertar en HTML.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Muestra un mensaje de error al usuario.
 * 
 * Por ahora usa alert() y console.error(). En el futuro se puede implementar
 * un sistema de notificaciones más sofisticado.
 * 
 * @param {string} mensaje - Mensaje de error a mostrar.
 */
function mostrarError(mensaje) {
    // Puedes implementar un sistema de notificaciones aquí
    console.error(mensaje);
    alert(mensaje);
}

/**
 * Ejecuta el procesamiento de vencimientos manualmente (solo para pruebas).
 * 
 * Hace una petición POST al servidor para ejecutar el procesamiento de vencimientos
 * y crear notificaciones automáticamente. Muestra un diálogo de confirmación antes
 * de ejecutar y deshabilita el botón durante el procesamiento.
 */
function ejecutarProcesamientoVencimientos(event) {
    if (!confirm('¿Está seguro de ejecutar el procesamiento de vencimientos? Esto creará notificaciones para todos los documentos próximos a vencer.')) {
        return;
    }
    
    // Obtener el botón desde el evento o buscarlo directamente
    let boton;
    if (event && event.target) {
        boton = event.target.closest('button');
    } else {
        // Si no hay evento, buscar el botón por su contenido
        const botones = document.querySelectorAll('button');
        boton = Array.from(botones).find(btn => btn.textContent.includes('Ejecutar Procesamiento'));
    }
    
    if (!boton) {
        alert('✗ Error: No se pudo encontrar el botón');
        return;
    }
    
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
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        boton.disabled = false;
        boton.innerHTML = textoOriginal;
        
        if (data.success) {
            alert('✓ ' + data.message);
            // Recargar la página para mostrar las nuevas notificaciones
            setTimeout(() => {
                location.reload();
            }, 1000);
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

