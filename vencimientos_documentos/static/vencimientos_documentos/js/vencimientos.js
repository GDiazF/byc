/**
 * JavaScript para el panel de vencimientos de documentos.
 */

const API_PERSONAL = '/vencimientos/api/personal/';
const API_MAQUINARIAS = '/vencimientos/api/maquinarias/';
const API_EXPORTAR_PERSONAL = '/vencimientos/api/exportar/personal/';
const API_EXPORTAR_MAQUINARIAS = '/vencimientos/api/exportar/maquinarias/';

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
    const filtrosPersonal = ['filtroBuscarPersonal', 'filtroEstadoPersonal', 'filtroDiasPersonal'];
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
    
    const filtrosMaquinarias = ['filtroBuscarMaquinarias', 'filtroEstadoMaquinarias', 'filtroDiasMaquinarias'];
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
            <td colspan="8" class="text-center">
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
    if (filtros.estado !== 'todos') params.append('estado', filtros.estado);
    if (filtros.dias) params.append('dias', filtros.dias);
    params.append('solo_activos', filtros.solo_activos);
    
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
            actualizarEstadisticasPersonal(documentosPersonal);
        } else {
            const errorMsg = data.error || 'Error al cargar documentos de personal';
            console.error('Error en respuesta:', errorMsg);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger">
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
            <td colspan="8" class="text-center">
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
    if (filtros.estado !== 'todos') params.append('estado', filtros.estado);
    if (filtros.dias) params.append('dias', filtros.dias);
    params.append('solo_activos', filtros.solo_activos);
    
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
            actualizarEstadisticasMaquinarias(documentosMaquinarias);
        } else {
            const errorMsg = data.error || 'Error al cargar documentos de maquinarias';
            console.error('Error en respuesta:', errorMsg);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger">
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
        estado: document.getElementById('filtroEstadoPersonal')?.value || 'todos',
        dias: document.getElementById('filtroDiasPersonal')?.value || '',
        solo_activos: document.getElementById('filtroSoloActivosPersonal')?.checked !== false
    };
}

/**
 * Obtiene los valores de los filtros de maquinarias.
 */
function obtenerFiltrosMaquinarias() {
    return {
        buscar: document.getElementById('filtroBuscarMaquinarias')?.value.trim() || '',
        estado: document.getElementById('filtroEstadoMaquinarias')?.value || 'todos',
        dias: document.getElementById('filtroDiasMaquinarias')?.value || '',
        solo_activos: document.getElementById('filtroSoloActivosMaquinarias')?.checked !== false
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
                <td colspan="8" class="text-center text-muted">
                    <i class="bi bi-inbox me-2"></i>No se encontraron documentos
                </td>
            </tr>
        `;
        return;
    }
    
        const canEdit = window.userPermissions && window.userPermissions.canEditPersonal;
        tbody.innerHTML = documentos.map(doc => {
        const colorFila = obtenerColorFila(doc.dias_restantes);
        const botonEditar = canEdit 
            ? `<a href="${doc.url_editar}" class="btn btn-sm btn-outline-primary btn-editar" title="Editar documentación">
                    <i class="bi bi-pencil-square"></i>
                </a>`
            : `<button class="btn btn-sm btn-outline-secondary btn-editar" disabled title="No tiene permiso para editar documentación">
                    <i class="bi bi-pencil-square"></i>
                </button>`;
        return `
            <tr class="${colorFila}">
                <td>${escapeHtml(doc.personal_nombre)}</td>
                <td>${escapeHtml(doc.personal_rut)}</td>
                <td>${escapeHtml(doc.tipo_nombre)}</td>
                <td>${escapeHtml(doc.nombre)}</td>
                <td>${doc.fecha_vencimiento || 'N/A'}</td>
                <td>${doc.dias_restantes !== null ? doc.dias_restantes : 'N/A'}</td>
                <td>
                    <span class="badge ${doc.badge_class} badge-estado">
                        ${doc.icono} ${doc.texto_estado}
                    </span>
                </td>
                <td>
                    ${botonEditar}
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
                <td colspan="8" class="text-center text-muted">
                    <i class="bi bi-inbox me-2"></i>No se encontraron documentos
                </td>
            </tr>
        `;
        return;
    }
    
        const canEdit = window.userPermissions && window.userPermissions.canEditMaquinarias;
        tbody.innerHTML = documentos.map(doc => {
        const colorFila = obtenerColorFila(doc.dias_restantes);
        const botonEditar = canEdit 
            ? `<a href="${doc.url_editar}" class="btn btn-sm btn-outline-primary btn-editar" title="Editar documentación">
                    <i class="bi bi-pencil-square"></i>
                </a>`
            : `<button class="btn btn-sm btn-outline-secondary btn-editar" disabled title="No tiene permiso para editar documentación">
                    <i class="bi bi-pencil-square"></i>
                </button>`;
        return `
            <tr class="${colorFila}">
                <td>${escapeHtml(doc.equipo_nombre)}</td>
                <td>${escapeHtml(doc.equipo_codigo)}</td>
                <td>${escapeHtml(doc.equipo_patente || '')}</td>
                <td>${escapeHtml(doc.nombre)}</td>
                <td>${doc.fecha_vencimiento || 'N/A'}</td>
                <td>${doc.dias_restantes !== null ? doc.dias_restantes : 'N/A'}</td>
                <td>
                    <span class="badge ${doc.badge_class} badge-estado">
                        ${doc.icono} ${doc.texto_estado}
                    </span>
                </td>
                <td>
                    ${botonEditar}
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
    if (diasRestantes < 15) return 'table-danger';  // Crítico
    if (diasRestantes < 30) return 'table-warning';  // Naranja
    if (diasRestantes < 45) return 'table-info';  // Amarillo
    return '';  // Verde (sin color)
}

/**
 * Actualiza las estadísticas de documentos de personal.
 */
function actualizarEstadisticasPersonal(documentos) {
    const container = document.getElementById('estadisticasPersonal');
    if (!container) return;
    
    const estadisticas = calcularEstadisticas(documentos);
    
    container.innerHTML = `
        <div class="col-md-3">
            <div class="card estadisticas-card verde">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Vigentes (45+ días)</h6>
                    <h3 class="card-title text-success">${estadisticas.verde}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card amarillo">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Amarillo (30-44 días)</h6>
                    <h3 class="card-title text-info">${estadisticas.amarillo}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card naranja">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Naranja (15-29 días)</h6>
                    <h3 class="card-title text-warning">${estadisticas.naranja}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card rojo">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Crítico/Vencido (&lt;15 días)</h6>
                    <h3 class="card-title text-danger">${estadisticas.rojo}</h3>
                </div>
            </div>
        </div>
    `;
}

/**
 * Actualiza las estadísticas de documentos de maquinarias.
 */
function actualizarEstadisticasMaquinarias(documentos) {
    const container = document.getElementById('estadisticasMaquinarias');
    if (!container) return;
    
    const estadisticas = calcularEstadisticas(documentos);
    
    container.innerHTML = `
        <div class="col-md-3">
            <div class="card estadisticas-card verde">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Vigentes (45+ días)</h6>
                    <h3 class="card-title text-success">${estadisticas.verde}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card amarillo">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Amarillo (30-44 días)</h6>
                    <h3 class="card-title text-info">${estadisticas.amarillo}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card naranja">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Naranja (15-29 días)</h6>
                    <h3 class="card-title text-warning">${estadisticas.naranja}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card estadisticas-card rojo">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Crítico/Vencido (&lt;15 días)</h6>
                    <h3 class="card-title text-danger">${estadisticas.rojo}</h3>
                </div>
            </div>
        </div>
    `;
}

/**
 * Calcula las estadísticas de documentos.
 */
function calcularEstadisticas(documentos) {
    let verde = 0;
    let amarillo = 0;
    let naranja = 0;
    let rojo = 0;
    
    documentos.forEach(doc => {
        const dias = doc.dias_restantes;
        if (dias === null) return;
        
        if (dias < 0 || dias < 15) {
            rojo++;
        } else if (dias < 30) {
            naranja++;
        } else if (dias < 45) {
            amarillo++;
        } else {
            verde++;
        }
    });
    
    return { verde, amarillo, naranja, rojo };
}

/**
 * Exporta los documentos de personal a Excel.
 */
function exportarExcelPersonal() {
    const filtros = obtenerFiltrosPersonal();
    const params = new URLSearchParams();
    if (filtros.buscar) params.append('buscar', filtros.buscar);
    if (filtros.estado !== 'todos') params.append('estado', filtros.estado);
    if (filtros.dias) params.append('dias', filtros.dias);
    params.append('solo_activos', filtros.solo_activos);
    
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
    if (filtros.estado !== 'todos') params.append('estado', filtros.estado);
    if (filtros.dias) params.append('dias', filtros.dias);
    params.append('solo_activos', filtros.solo_activos);
    
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

