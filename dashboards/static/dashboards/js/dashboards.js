/* ============================================================================
   JAVASCRIPT PARA DASHBOARDS
   ============================================================================
   Este archivo contiene toda la logica JavaScript para la aplicacion de dashboards.
   Incluye funciones para cargar datos de las APIs, renderizar graficos con Chart.js,
   y manejar la interaccion del usuario con los diferentes dashboards.
   
   NOTA: Las URLs de las APIs se deben definir en el HTML como variables globales:
   - API_RRHH
   - API_OPERACIONES
   - API_MAQUINARIAS
   - API_GERENCIA
   ============================================================================ */

// Almacenar instancias de graficos
// NOTA: Las URLs de las APIs (API_RRHH, API_OPERACIONES, API_MAQUINARIAS, API_GERENCIA)
// se definen en el HTML como variables globales antes de cargar este script
const charts = {};

// Determinar que tab mostrar segun el rol (preparado para futuro)
// Por ahora, siempre mostrar todos los tabs
// TODO: Implementar logica de roles
// const userRole = '{{ request.user.groups.first.name|default:"gerencia" }}';
// const defaultTab = userRole === 'rrhh' ? 'rrhh' : userRole === 'operaciones' ? 'operaciones' : 'gerencia';

// Inicializar cuando el DOM este listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Dashboard] DOM cargado, iniciando dashboards...');
    
    // Determinar que tab esta activo y cargar su contenido
    // Buscar solo dentro del contenedor de tabs del dashboard (#dashboardTabs)
    const tabsContainer = document.getElementById('dashboardTabs');
    const activeTab = tabsContainer ? tabsContainer.querySelector('.nav-link.active') : null;
    console.log('[Dashboard] Tab activo encontrado:', activeTab);
    
    if (activeTab) {
        const targetId = activeTab.getAttribute('data-bs-target');
        console.log('[Dashboard] Target ID del tab activo:', targetId);
        
        if (targetId === '#rrhh') {
            console.log('[Dashboard] Cargando dashboard RRHH...');
            cargarDashboardRRHH();
        } else if (targetId === '#operaciones') {
            console.log('[Dashboard] Cargando dashboard Operaciones...');
            cargarDashboardOperaciones();
        } else if (targetId === '#maquinarias') {
            console.log('[Dashboard] Cargando dashboard Maquinarias...');
            cargarDashboardMaquinarias();
        } else if (targetId === '#gerencia') {
            console.log('[Dashboard] Cargando dashboard Gerencia...');
            cargarDashboardGerencia();
        } else {
            console.warn('[Dashboard] Tab activo desconocido:', targetId);
            // Si no se encuentra el target, intentar cargar RRHH por defecto
            const rrhhContent = document.getElementById('rrhh-content');
            if (rrhhContent) {
                console.log('[Dashboard] Contenedor RRHH encontrado, cargando por defecto...');
                cargarDashboardRRHH();
            }
        }
    } else {
        console.warn('[Dashboard] No se encontro tab activo, intentando cargar RRHH por defecto...');
        // Si no hay tab activo, intentar cargar RRHH por defecto
        const rrhhContent = document.getElementById('rrhh-content');
        if (rrhhContent) {
            console.log('[Dashboard] Contenedor RRHH encontrado, cargando...');
            cargarDashboardRRHH();
        } else {
            console.error('[Dashboard] Contenedor RRHH NO encontrado');
        }
    }
    
    // Event listeners para los tabs (solo si existen)
    const rrhhTab = document.getElementById('rrhh-tab');
    if (rrhhTab) {
        rrhhTab.addEventListener('shown.bs.tab', function() {
            cargarDashboardRRHH();
        });
    }
    
    const operacionesTab = document.getElementById('operaciones-tab');
    if (operacionesTab) {
        operacionesTab.addEventListener('shown.bs.tab', function() {
            cargarDashboardOperaciones();
        });
    }
    
    const maquinariasTab = document.getElementById('maquinarias-tab');
    if (maquinariasTab) {
        maquinariasTab.addEventListener('shown.bs.tab', function() {
            cargarDashboardMaquinarias();
        });
    }
    
    const gerenciaTab = document.getElementById('gerencia-tab');
    if (gerenciaTab) {
        gerenciaTab.addEventListener('shown.bs.tab', function() {
            cargarDashboardGerencia();
        });
    }
});

/**
 * Carga los datos del dashboard de RRHH desde la API y los renderiza.
 * 
 * Realiza una petición AJAX a la API de RRHH, procesa la respuesta y llama
 * a renderizarDashboardRRHH para mostrar los datos. Solo carga los datos una vez
 * por sesión usando el atributo dataset.loaded.
 */
function cargarDashboardRRHH() {
    console.log('[Dashboard RRHH] funcion cargarDashboardRRHH llamada');
    const container = document.getElementById('rrhh-content');
    if (!container) {
        console.error('[Dashboard RRHH] Contenedor no encontrado - El usuario puede no tener permiso para ver este dashboard');
        return;
    }
    console.log('[Dashboard RRHH] Contenedor encontrado:', container);
    
    if (container.dataset.loaded === 'true') {
        console.log('[Dashboard RRHH] Ya esta cargado, omitiendo...');
        return;
    }
    
    console.log('[Dashboard RRHH] Iniciando carga de datos desde:', API_RRHH);
    
    fetch(API_RRHH, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin'
    })
        .then(response => {
            console.log('[Dashboard RRHH] Respuesta recibida:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[Dashboard RRHH] Datos recibidos:', data);
            if (data.success) {
                console.log('[Dashboard RRHH] Renderizando dashboard...');
                renderizarDashboardRRHH(data.data, container);
                container.dataset.loaded = 'true';
                console.log('[Dashboard RRHH] Dashboard renderizado exitosamente');
            } else {
                console.error('[Dashboard RRHH] Error en respuesta:', data.error);
                if (data.traceback) {
                    console.error('[Dashboard RRHH] Traceback:', data.traceback);
                }
                container.innerHTML = '<div class="alert alert-danger">Error al cargar datos: ' + (data.error || 'Error desconocido') + '</div>';
            }
        })
        .catch(error => {
            console.error('[Dashboard RRHH] Error en fetch:', error);
            container.innerHTML = '<div class="alert alert-danger">Error al cargar datos de RRHH: ' + error.message + '</div>';
        });
}

/**
 * Carga los datos del dashboard de Operaciones desde la API y los renderiza.
 * 
 * Realiza una petición AJAX a la API de Operaciones, procesa la respuesta y llama
 * a renderizarDashboardOperaciones para mostrar los datos. Solo carga los datos una vez
 * por sesión usando el atributo dataset.loaded.
 */
function cargarDashboardOperaciones() {
    const container = document.getElementById('operaciones-content');
    if (container.dataset.loaded === 'true') return;
    
    fetch(API_OPERACIONES)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarDashboardOperaciones(data.data, container);
                container.dataset.loaded = 'true';
            } else {
                container.innerHTML = '<div class="alert alert-danger">Error al cargar datos: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = '<div class="alert alert-danger">Error al cargar datos de Operaciones</div>';
        });
}

/**
 * Carga los datos del dashboard de Maquinarias desde la API y los renderiza.
 * 
 * Realiza una petición AJAX a la API de Maquinarias, procesa la respuesta y llama
 * a renderizarDashboardMaquinarias para mostrar los datos. Solo carga los datos una vez
 * por sesión usando el atributo dataset.loaded.
 */
function cargarDashboardMaquinarias() {
    const container = document.getElementById('maquinarias-content');
    if (container.dataset.loaded === 'true') return;
    
    fetch(API_MAQUINARIAS)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarDashboardMaquinarias(data.data, container);
                container.dataset.loaded = 'true';
            } else {
                container.innerHTML = '<div class="alert alert-danger">Error al cargar datos: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = '<div class="alert alert-danger">Error al cargar datos de Maquinarias</div>';
        });
}

/**
 * Carga los datos del dashboard de Gerencia desde la API y los renderiza.
 * 
 * Realiza una petición AJAX a la API de Gerencia, procesa la respuesta y llama
 * a renderizarDashboardGerencia para mostrar los datos. Solo carga los datos una vez
 * por sesión usando el atributo dataset.loaded.
 */
function cargarDashboardGerencia() {
    const container = document.getElementById('gerencia-content');
    if (container.dataset.loaded === 'true') return;
    
    fetch(API_GERENCIA)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarDashboardGerencia(data.data, container);
                container.dataset.loaded = 'true';
            } else {
                container.innerHTML = '<div class="alert alert-danger">Error al cargar datos: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = '<div class="alert alert-danger">Error al cargar datos de Gerencia</div>';
        });
}

/**
 * Renderiza el dashboard de RRHH con los datos recibidos de la API.
 * 
 * Crea las tarjetas de estadísticas, gráficos con Chart.js y tablas con los datos
 * de personal, documentos por vencer, faenas activas, etc.
 * 
 * @param {Object} data - Datos del dashboard recibidos de la API
 * @param {HTMLElement} container - Contenedor donde se renderizará el dashboard
 */
function renderizarDashboardRRHH(data, container) {
    let html = `
        <div class="row mb-4">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Personal por Empresa</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-rrhh-empresas"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Distribucion del Personal</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-rrhh-distribucion"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            Documentos por Vencer (Proximos 30 dias)
                        </h6>
                        <span class="badge bg-warning">${data.total_documentos_por_vencer || 0}</span>
                    </div>
                    <div class="card-body">
                        ${data.documentos_por_vencer && data.documentos_por_vencer.length > 0 ? `
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Tipo</th>
                                            <th>Documento</th>
                                            <th>Personal</th>
                                            <th>RUT</th>
                                            <th>Fecha Vencimiento</th>
                                            <th>dias Restantes</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.documentos_por_vencer.map(doc => `
                                            <tr class="${doc.dias_restantes <= 5 ? 'table-warning' : ''}">
                                                <td><span class="badge bg-secondary">${doc.tipo}</span></td>
                                                <td>${doc.nombre}</td>
                                                <td>${doc.personal}</td>
                                                <td>${doc.personal_rut}</td>
                                                <td>${doc.fecha_vencimiento}</td>
                                                <td>
                                                    <span class="badge ${doc.dias_restantes <= 5 ? 'bg-danger' : doc.dias_restantes <= 10 ? 'bg-warning' : 'bg-info'}">
                                                        ${doc.dias_restantes} dia${doc.dias_restantes !== 1 ? 's' : ''}
                                                    </span>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : `
                            <div class="text-center py-3">
                                <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                                <p class="mt-2 text-muted mb-0">No hay documentos por vencer en los Proximos 30 dias</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Crear grafico de Distribucion del personal (doughnut, igual estilo que personal por empresa)
    const ctxDistribucion = document.getElementById('chart-rrhh-distribucion').getContext('2d');
    const distribucionData = {
        labels: ['Disponible', 'En Faena', 'Con Licencia Medica', 'Con Ausentismo'],
        datasets: [{
            data: [
                data.personal_disponible || 0,
                data.personal_en_faena || 0,
                data.personal_con_licencia || 0,
                data.personal_con_ausentismo || 0
            ],
            backgroundColor: [
                '#198754', // success - Disponible (verde, igual que la tarjeta success)
                '#0dcaf0', // info - En Faena (azul claro, igual que la tarjeta info)
                '#ffc107', // warning - Con Licencia Medica (amarillo, igual que la tarjeta warning)
                '#dc3545'  // danger - Con Ausentismo (rojo, igual que la tarjeta danger)
            ]
        }]
    };
    
    charts['rrhh-distribucion'] = new Chart(ctxDistribucion, {
        type: 'doughnut',
        data: distribucionData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            layout: {
                padding: {
                    left: 5,
                    right: 5,
                    top: 5,
                    bottom: 5
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: window.innerWidth < 768 ? 9 : 11
                        },
                        padding: window.innerWidth < 768 ? 8 : 12
                    },
                    onHover: function(e, legendItem) {
                        if (e.native && e.native.target) {
                            e.native.target.style.cursor = 'pointer';
                        }
                    },
                    onLeave: function(e, legendItem) {
                        if (e.native && e.native.target) {
                            e.native.target.style.cursor = 'default';
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = distribucionData.labels[index];
                    mostrarDetallesDistribucion(label, data);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
    
    // Crear grafico de personal por empresa
    if (data.personal_por_empresa && data.personal_por_empresa.length > 0) {
        const ctx = document.getElementById('chart-rrhh-empresas').getContext('2d');
        // Nueva paleta de colores Mas variada y atractiva
        const empresaColors = [
            '#667eea', // Morado azulado
            '#764ba2', // Morado oscuro
            '#f093fb', // Rosa
            '#4facfe', // Azul claro
            '#43e97b', // Verde claro
            '#fa709a', // Rosa coral
            '#fee140', // Amarillo claro
            '#30cfd0', // Turquesa
            '#a8edea', // Aqua claro
            '#fed6e3'  // Rosa pastel
        ];
        // Invertir el orden para que coincida con el orden visual del grafico
        const empresasReversed = [...data.personal_por_empresa].reverse();
        charts['rrhh-empresas'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: empresasReversed.map(e => e.empresa_id__nomFantasia || 'Sin empresa'),
                datasets: [{
                    data: empresasReversed.map(e => e.total),
                    backgroundColor: empresaColors.slice(0, empresasReversed.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Muestra un modal con los detalles de la distribución de personal.
 * 
 * @param {string} tipo - Tipo de distribución ('empresa', 'ausentismo', 'licencia_medica')
 * @param {Object} data - Datos completos del dashboard de RRHH
 */
function mostrarDetallesDistribucion(tipo, data) {
    let titulo = '';
    let modalHTML = '';
    
    if (tipo === 'Con Ausentismo') {
        const resumenTipos = data.tipos_ausentismo || [];
        const detallesPersonas = data.personal_con_ausentismo_detalle || [];
        
        if (resumenTipos.length === 0 && detallesPersonas.length === 0) {
            alert(`No hay detalles disponibles para ${tipo}`);
            return;
        }
        
        titulo = 'Detalles de Ausentismos';
        
        // Agrupar personas por tipo de ausentismo
        const personasPorTipo = {};
        detallesPersonas.forEach(persona => {
            const tipo = persona.tipo_ausentismo;
            if (!personasPorTipo[tipo]) {
                personasPorTipo[tipo] = [];
            }
            personasPorTipo[tipo].push(persona);
        });
        
        modalHTML = `
            <div class="modal fade" id="modalDetallesDistribucion" tabindex="-1" aria-labelledby="modalDetallesDistribucionLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesDistribucionLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="accordion" id="accordionAusentismos">
                                ${resumenTipos.map((tipo, index) => {
                                    const personas = personasPorTipo[tipo.tipo] || [];
                                    const tipoId = tipo.tipo.replace(/\s+/g, '_').toLowerCase();
                                    return `
                                        <div class="accordion-item">
                                            <h2 class="accordion-header" id="heading${tipoId}">
                                                <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${tipoId}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse${tipoId}">
                                                    <div class="d-flex justify-content-between align-items-center w-100 me-3">
                                                        <div>
                                                            <strong>${tipo.tipo}</strong>
                                                        </div>
                                                        <span class="badge bg-danger">${tipo.cantidad} persona${tipo.cantidad !== 1 ? 's' : ''}</span>
                                                    </div>
                                                </button>
                                            </h2>
                                            <div id="collapse${tipoId}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="heading${tipoId}" data-bs-parent="#accordionAusentismos">
                                                <div class="accordion-body">
                                                    <div class="table-responsive">
                                                        <table class="table table-sm table-hover">
                                                            <thead>
                                                                <tr>
                                                                    <th>Nombre</th>
                                                                    <th>RUT</th>
                                                                    <th>Fecha Inicio</th>
                                                                    <th>Fecha Fin</th>
                                                                    <th class="text-end">Días</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                ${personas.map(p => `
                                                                    <tr>
                                                                        <td>${p.nombre}</td>
                                                                        <td>${p.rut}</td>
                                                                        <td>${p.fecha_inicio}</td>
                                                                        <td>${p.fecha_fin}</td>
                                                                        <td class="text-end">${p.dias}</td>
                                                                    </tr>
                                                                `).join('')}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (tipo === 'Con Licencia Medica') {
        const detalles = data.tipos_licencia_medica || [];
        if (detalles.length === 0) {
            alert(`No hay detalles disponibles para ${tipo}`);
            return;
        }
        
        titulo = 'Detalles de Licencias Medicas';
        modalHTML = `
            <div class="modal fade" id="modalDetallesDistribucion" tabindex="-1" aria-labelledby="modalDetallesDistribucionLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesDistribucionLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Tipo</th>
                                            <th class="text-end">Cantidad de Personas</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(d => `
                                            <tr>
                                                <td>${d.tipo}</td>
                                                <td class="text-end"><strong>${d.cantidad}</strong></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                    <tfoot>
                                        <tr class="table-info">
                                            <th>Total</th>
                                            <th class="text-end">${detalles.reduce((sum, d) => sum + d.cantidad, 0)}</th>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (tipo === 'En Faena') {
        const faenas = data.faenas_con_personal || [];
        if (faenas.length === 0) {
            alert(`No hay faenas activas con personal asignado`);
            return;
        }
        
        titulo = 'Personal en Faenas';
        modalHTML = `
            <div class="modal fade" id="modalDetallesDistribucion" tabindex="-1" aria-labelledby="modalDetallesDistribucionLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesDistribucionLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="accordion" id="accordionFaenas">
                                ${faenas.map((faena, index) => `
                                    <div class="accordion-item">
                                        <h2 class="accordion-header" id="heading${faena.id}">
                                            <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${faena.id}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse${faena.id}">
                                                <div class="d-flex justify-content-between align-items-center w-100 me-3">
                                                    <div>
                                                        <strong>${faena.nombre}</strong>
                                                        ${faena.codigo ? `<span class="badge bg-secondary ms-2">${faena.codigo}</span>` : ''}
                                                    </div>
                                                    <span class="badge bg-primary">${faena.cantidad_personal} persona${faena.cantidad_personal !== 1 ? 's' : ''}</span>
                                                </div>
                                            </button>
                                        </h2>
                                        <div id="collapse${faena.id}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="heading${faena.id}" data-bs-parent="#accordionFaenas">
                                            <div class="accordion-body">
                                                ${faena.fecha_inicio || faena.fecha_fin ? `
                                                    <p class="mb-3">
                                                        <small class="text-muted">
                                                            ${faena.fecha_inicio ? `Desde: ${faena.fecha_inicio}` : ''}
                                                            ${faena.fecha_inicio && faena.fecha_fin ? ' | ' : ''}
                                                            ${faena.fecha_fin ? `Hasta: ${faena.fecha_fin}` : ''}
                                                        </small>
                                                    </p>
                                                ` : ''}
                                                <div class="table-responsive">
                                                    <table class="table table-sm table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Nombre</th>
                                                                <th>RUT</th>
                                                                <th>Cargo</th>
                                                                <th>Turno</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            ${faena.personal.map(p => `
                                                                <tr>
                                                                    <td>${p.nombre}</td>
                                                                    <td>${p.rut}</td>
                                                                    <td>${p.cargo}</td>
                                                                    <td>${p.turno}</td>
                                                                </tr>
                                                            `).join('')}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Para Disponible, no hay detalles por tipo
        return;
    }
    
    // Eliminar modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesDistribucion');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesDistribucion'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesDistribucion').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Renderiza el dashboard de Operaciones con los datos recibidos de la API.
 * 
 * Crea las tarjetas de estadísticas, gráficos con Chart.js y tablas con los datos
 * de personal, equipos, faenas y documentos por vencer.
 * 
 * @param {Object} data - Datos del dashboard recibidos de la API
 * @param {HTMLElement} container - Contenedor donde se renderizará el dashboard
 */
function renderizarDashboardOperaciones(data, container) {
    let html = `
        <div class="row mb-4">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Distribucion del Personal</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-operaciones-personal"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Estado de Equipos</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-operaciones-equipos"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            Documentos por Vencer (Proximos 30 dias)
                        </h6>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; height: 500px; padding: 1rem;">
                        <ul class="nav nav-tabs mb-3" id="tabsDocumentosOperaciones" role="tablist" style="flex-shrink: 0;">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="tab-personal-operaciones" data-bs-toggle="tab" data-bs-target="#content-personal-operaciones" type="button" role="tab">
                                    <i class="bi bi-people me-2"></i>Personal
                                    <span class="badge bg-warning ms-2">${data.total_documentos_personal_por_vencer || 0}</span>
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="tab-maquinarias-operaciones" data-bs-toggle="tab" data-bs-target="#content-maquinarias-operaciones" type="button" role="tab">
                                    <i class="bi bi-gear me-2"></i>Maquinarias
                                    <span class="badge bg-warning ms-2">${data.total_documentos_maquinarias_por_vencer || 0}</span>
                                </button>
                            </li>
                        </ul>
                        
                        <div class="tab-content" id="tabsContentDocumentosOperaciones" style="flex: 1; overflow: hidden; min-height: 0;">
                            <!-- Tab Personal -->
                            <div class="tab-pane fade show active" id="content-personal-operaciones" role="tabpanel" style="height: 100%; overflow: hidden;">
                                ${data.documentos_personal_por_vencer && data.documentos_personal_por_vencer.length > 0 ? `
                                    <div style="height: 100%; overflow-y: auto; overflow-x: auto; border: 1px solid #dee2e6; border-radius: 0.25rem;">
                                        <table class="table table-sm table-hover mb-0">
                                            <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                                <tr>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Tipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Documento</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Personal</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">RUT</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Fecha Vencimiento</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">dias Restantes</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.documentos_personal_por_vencer.map(doc => `
                                                    <tr class="${doc.dias_restantes <= 5 ? 'table-warning' : ''}">
                                                        <td><span class="badge bg-secondary">${doc.tipo}</span></td>
                                                        <td>${doc.nombre}</td>
                                                        <td>${doc.personal}</td>
                                                        <td>${doc.personal_rut}</td>
                                                        <td>${doc.fecha_vencimiento}</td>
                                                        <td>
                                                            <span class="badge ${doc.dias_restantes <= 5 ? 'bg-danger' : doc.dias_restantes <= 10 ? 'bg-warning' : 'bg-info'}">
                                                                ${doc.dias_restantes} dia${doc.dias_restantes !== 1 ? 's' : ''}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : `
                                    <div class="text-center py-3">
                                        <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                                        <p class="mt-2 text-muted mb-0">No hay documentos de personal por vencer en los Proximos 30 dias</p>
                                    </div>
                                `}
                            </div>
                            
                            <!-- Tab Maquinarias -->
                            <div class="tab-pane fade" id="content-maquinarias-operaciones" role="tabpanel" style="height: 100%; overflow: hidden;">
                                ${data.documentos_maquinarias_por_vencer && data.documentos_maquinarias_por_vencer.length > 0 ? `
                                    <div style="height: 100%; overflow-y: auto; overflow-x: auto; border: 1px solid #dee2e6; border-radius: 0.25rem;">
                                        <table class="table table-sm table-hover mb-0">
                                            <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                                <tr>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Tipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Equipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Codigo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Fecha Vencimiento</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">dias Restantes</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.documentos_maquinarias_por_vencer.map(doc => `
                                                    <tr class="${doc.dias_restantes <= 5 ? 'table-warning' : ''}">
                                                        <td><span class="badge bg-secondary">${doc.tipo}</span></td>
                                                        <td>${doc.equipo}</td>
                                                        <td>${doc.equipo_codigo}</td>
                                                        <td>${doc.fecha_vencimiento}</td>
                                                        <td>
                                                            <span class="badge ${doc.dias_restantes <= 5 ? 'bg-danger' : doc.dias_restantes <= 10 ? 'bg-warning' : 'bg-info'}">
                                                                ${doc.dias_restantes} dia${doc.dias_restantes !== 1 ? 's' : ''}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : `
                                    <div class="text-center py-3">
                                        <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                                        <p class="mt-2 text-muted mb-0">No hay documentos de maquinarias por vencer en los Proximos 30 dias</p>
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Crear grafico de Distribucion del personal (igual que RRHH)
    const ctxPersonal = document.getElementById('chart-operaciones-personal').getContext('2d');
    const distribucionPersonalData = {
        labels: ['Disponible', 'En Faena', 'Con Licencia Medica', 'Con Ausentismo'],
        datasets: [{
            data: [
                data.personal_disponible || 0,
                data.personal_en_faena || 0,
                data.personal_con_licencia || 0,
                data.personal_con_ausentismo || 0
            ],
            backgroundColor: [
                '#198754', // success - Disponible
                '#0dcaf0', // info - En Faena
                '#ffc107', // warning - Con Licencia Medica
                '#dc3545'  // danger - Con Ausentismo
            ]
        }]
    };
    
    charts['operaciones-personal'] = new Chart(ctxPersonal, {
        type: 'doughnut',
        data: distribucionPersonalData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            layout: {
                padding: {
                    left: 5,
                    right: 5,
                    top: 5,
                    bottom: 5
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: window.innerWidth < 768 ? 9 : 11
                        },
                        padding: window.innerWidth < 768 ? 8 : 12
                    },
                    onHover: function(e, legendItem) {
                        e.native.target.style.cursor = 'pointer';
                    },
                    onLeave: function(e, legendItem) {
                        e.native.target.style.cursor = 'default';
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = distribucionPersonalData.labels[index];
                    mostrarDetallesDistribucion(label, data);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
    
    // Crear grafico de Distribucion de equipos
    const ctxEquipos = document.getElementById('chart-operaciones-equipos').getContext('2d');
    
    // Preparar datos de Distribucion de equipos
    const distribucionEquipos = data.distribucion_equipos || {};
    const labelsEquipos = [];
    const valoresEquipos = [];
    const coloresEquipos = [];
    
    // Colores predefinidos para estados comunes
    const coloresEstados = {
        'Disponibles': '#198754', // success
        'En Uso': '#0dcaf0', // info
        'En Faena': '#ffc107', // warning
        'Inactivos': '#8b0000', // dark red - igual que maquinarias
        'Shutdown': '#dc3545', // danger
        'Operativo con anomalias': '#fd7e14', // warning variant
        'Operativo con anomalías': '#fd7e14', // warning variant (con tilde)
        'En Mantenimiento': '#fd7e14', // warning variant
        'En Reparacion': '#e83e8c', // pink
        'Fuera de Servicio': '#6610f2', // purple
        'Disponible': '#198754' // success (singular)
    };
    
    // funcion para obtener color de un estado
    function obtenerColorEstado(estado) {
        // Buscar coincidencia exacta primero
        if (coloresEstados[estado]) {
            return coloresEstados[estado];
        }
        // Buscar por coincidencia parcial (case insensitive)
        const estadoLower = estado.toLowerCase();
        for (const key in coloresEstados) {
            if (key.toLowerCase() === estadoLower) {
                return coloresEstados[key];
            }
        }
        // Si no se encuentra, usar un color por defecto basado en el nombre
        if (estadoLower.includes('inactivo') || estadoLower.includes('inactivos')) {
            return '#8b0000'; // dark red - igual que maquinarias
        }
        if (estadoLower.includes('shutdown') || estadoLower.includes('fuera')) {
            return '#dc3545'; // danger
        }
        if (estadoLower.includes('anomalia') || estadoLower.includes('anomalía') || estadoLower.includes('mantenimiento')) {
            return '#fd7e14'; // warning
        }
        if (estadoLower.includes('Reparacion') || estadoLower.includes('reparacion')) {
            return '#e83e8c'; // pink
        }
        // Color por defecto
        return '#6c757d'; // secondary
    }
    
    // Agregar estados en orden de importancia
    const ordenEstados = ['Disponibles', 'En Uso', 'En Faena', 'Inactivos'];
    const estadosAgregados = new Set();
    
    // Primero agregar estados conocidos en orden
    for (const estado of ordenEstados) {
        const valor = distribucionEquipos[estado];
        if (valor !== undefined && valor !== null && valor > 0) {
            labelsEquipos.push(estado);
            valoresEquipos.push(valor);
            coloresEquipos.push(obtenerColorEstado(estado));
            estadosAgregados.add(estado);
        }
    }
    
    // Luego agregar TODOS los demas estados (Shutdown, Operativo con anomalias, etc.)
    for (const estado in distribucionEquipos) {
        const valor = distribucionEquipos[estado];
        if (!estadosAgregados.has(estado) && valor !== undefined && valor !== null && valor > 0) {
            labelsEquipos.push(estado);
            valoresEquipos.push(valor);
            coloresEquipos.push(obtenerColorEstado(estado));
            estadosAgregados.add(estado);
        }
    }
    
    const distribucionEquiposData = {
        labels: labelsEquipos,
        datasets: [{
            data: valoresEquipos,
            backgroundColor: coloresEquipos
        }]
    };
    
    charts['operaciones-equipos'] = new Chart(ctxEquipos, {
        type: 'doughnut',
        data: distribucionEquiposData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            layout: {
                padding: {
                    left: 5,
                    right: 5,
                    top: 5,
                    bottom: 5
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: window.innerWidth < 768 ? 9 : 11
                        },
                        padding: window.innerWidth < 768 ? 8 : 12
                    },
                    onHover: function(e, legendItem) {
                        if (e.native && e.native.target) {
                            e.native.target.style.cursor = 'pointer';
                        }
                    },
                    onLeave: function(e, legendItem) {
                        if (e.native && e.native.target) {
                            e.native.target.style.cursor = 'default';
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = distribucionEquiposData.labels[index];
                    mostrarDetallesEquipos(label, data);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

/**
 * Renderiza el dashboard de Maquinarias con los datos recibidos de la API.
 * 
 * Crea las tarjetas de estadísticas, gráficos con Chart.js y tablas con los datos
 * de equipos, órdenes de trabajo y documentos por vencer.
 * 
 * @param {Object} data - Datos del dashboard recibidos de la API
 * @param {HTMLElement} container - Contenedor donde se renderizará el dashboard
 */
function renderizarDashboardMaquinarias(data, container) {
    let html = `
        <div class="row mb-4">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Ordenes de Trabajo por Estado</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-maquinarias-ots"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Estado de Equipos</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-maquinarias-equipos"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-list-ul me-2"></i>
                            Informacion de Equipos
                        </h6>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; height: 500px; padding: 1rem;">
                        <ul class="nav nav-tabs mb-3" id="tabsInfoMaquinarias" role="tablist" style="flex-shrink: 0;">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="tab-documentos-maquinarias" data-bs-toggle="tab" data-bs-target="#content-documentos-maquinarias" type="button" role="tab">
                                    <i class="bi bi-exclamation-triangle-fill me-2"></i>Documentos por Vencer
                                    <span class="badge bg-warning ms-2">${data.total_documentos_maquinarias_por_vencer || 0}</span>
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="tab-ranking-maquinarias" data-bs-toggle="tab" data-bs-target="#content-ranking-maquinarias" type="button" role="tab">
                                    <i class="bi bi-trophy-fill me-2"></i>Ranking Equipos Mas Intervenidos
                                    <span class="badge bg-info ms-2">${data.ranking_equipos_intervenidos ? data.ranking_equipos_intervenidos.length : 0}</span>
                                </button>
                            </li>
                        </ul>
                        
                        <div class="tab-content" id="tabsContentInfoMaquinarias" style="flex: 1; overflow: hidden; min-height: 0;">
                            <!-- Tab Documentos por Vencer -->
                            <div class="tab-pane fade show active" id="content-documentos-maquinarias" role="tabpanel" style="height: 100%; overflow: hidden;">
                                ${data.documentos_maquinarias_por_vencer && data.documentos_maquinarias_por_vencer.length > 0 ? `
                                    <div style="height: 100%; overflow-y: auto; overflow-x: auto; border: 1px solid #dee2e6; border-radius: 0.25rem;">
                                        <table class="table table-sm table-hover mb-0">
                                            <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                                <tr>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Tipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Equipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Codigo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Fecha Vencimiento</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">dias Restantes</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.documentos_maquinarias_por_vencer.map(doc => `
                                                    <tr class="${doc.dias_restantes <= 5 ? 'table-warning' : ''}">
                                                        <td><span class="badge bg-secondary">${doc.tipo}</span></td>
                                                        <td>${doc.equipo}</td>
                                                        <td>${doc.equipo_codigo}</td>
                                                        <td>${doc.fecha_vencimiento}</td>
                                                        <td>
                                                            <span class="badge ${doc.dias_restantes <= 5 ? 'bg-danger' : doc.dias_restantes <= 10 ? 'bg-warning' : 'bg-info'}">
                                                                ${doc.dias_restantes} dia${doc.dias_restantes !== 1 ? 's' : ''}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : `
                                    <div class="text-center py-3">
                                        <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                                        <p class="mt-2 text-muted mb-0">No hay documentos de maquinarias por vencer en los Proximos 30 dias</p>
                                    </div>
                                `}
                            </div>
                            
                            <!-- Tab Ranking Equipos Mas Intervenidos -->
                            <div class="tab-pane fade" id="content-ranking-maquinarias" role="tabpanel" style="height: 100%; overflow: hidden;">
                                ${data.ranking_equipos_intervenidos && data.ranking_equipos_intervenidos.length > 0 ? `
                                    <div style="height: 100%; overflow-y: auto; overflow-x: auto; border: 1px solid #dee2e6; border-radius: 0.25rem;">
                                        <table class="table table-sm table-hover mb-0">
                                            <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                                <tr>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6; width: 60px;">#</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Equipo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">Codigo</th>
                                                    <th style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6; text-align: center;">Total OTs</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${data.ranking_equipos_intervenidos.map(item => `
                                                    <tr>
                                                        <td>
                                                            <span class="badge ${item.posicion === 1 ? 'bg-warning' : item.posicion <= 3 ? 'bg-info' : 'bg-secondary'}">
                                                                ${item.posicion}
                                                            </span>
                                                        </td>
                                                        <td><strong>${item.equipo}</strong></td>
                                                        <td>${item.codigo}</td>
                                                        <td style="text-align: center;">
                                                            <span class="badge bg-primary">${item.total_ots} OT${item.total_ots !== 1 ? 's' : ''}</span>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : `
                                    <div class="text-center py-3">
                                        <i class="bi bi-info-circle-fill text-info" style="font-size: 2rem;"></i>
                                        <p class="mt-2 text-muted mb-0">No hay equipos con historial de Ordenes de trabajo</p>
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Crear grafico de OTs por estado (doughnut, similar a otros dashboards)
    if (data.ots_por_estado && data.ots_por_estado.length > 0) {
        const ctx = document.getElementById('chart-maquinarias-ots').getContext('2d');
        const bootstrapColorsOTs = [
            '#0d6efd', // primary
            '#198754', // success
            '#0dcaf0', // info
            '#ffc107', // warning
            '#dc3545', // danger
            '#6c757d', // secondary
            '#212529'  // dark
        ];
        charts['maquinarias-ots'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.ots_por_estado.map(e => e.estado),
                datasets: [{
                    data: data.ots_por_estado.map(e => e.total),
                    backgroundColor: bootstrapColorsOTs.slice(0, data.ots_por_estado.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Crear grafico de Distribucion de equipos (similar a operaciones)
    if (data.distribucion_equipos) {
        const ctxEquipos = document.getElementById('chart-maquinarias-equipos').getContext('2d');
        
        // Preparar datos de Distribucion de equipos
        const distribucionEquipos = data.distribucion_equipos || {};
        const labelsEquipos = [];
        const valoresEquipos = [];
        const coloresEquipos = [];
        
        // Colores predefinidos para estados comunes (igual que operaciones)
        const coloresEstados = {
            'Disponibles': '#198754', // success
            'En Uso': '#0dcaf0', // info
            'En Faena': '#ffc107', // warning
            'Inactivos': '#8b0000', // dark red - color diferente para inactivos
            'Shutdown': '#dc3545', // danger
            'Operativo con anomalias': '#fd7e14', // warning variant
            'Operativo con anomalías': '#fd7e14', // warning variant (con tilde)
            'En Mantenimiento': '#fd7e14', // warning variant
            'En Reparacion': '#e83e8c', // pink
            'Fuera de Servicio': '#6610f2', // purple
            'Disponible': '#198754' // success (singular)
        };
        
        // funcion para obtener color de un estado (igual que operaciones)
        function obtenerColorEstado(estado) {
            // Buscar coincidencia exacta primero
            if (coloresEstados[estado]) {
                return coloresEstados[estado];
            }
            // Buscar por coincidencia parcial (case insensitive)
            const estadoLower = estado.toLowerCase();
            for (const key in coloresEstados) {
                if (key.toLowerCase() === estadoLower) {
                    return coloresEstados[key];
                }
            }
            // Si no se encuentra, usar un color por defecto basado en el nombre
            if (estadoLower.includes('inactivo') || estadoLower.includes('inactivos')) {
                return '#8b0000'; // dark red - color diferente para inactivos
            }
            if (estadoLower.includes('shutdown') || estadoLower.includes('fuera')) {
                return '#dc3545'; // danger
            }
            if (estadoLower.includes('anomalia') || estadoLower.includes('anomalía') || estadoLower.includes('mantenimiento')) {
                return '#fd7e14'; // warning
            }
            if (estadoLower.includes('Reparacion') || estadoLower.includes('reparacion')) {
                return '#e83e8c'; // pink
            }
            // Color por defecto
            return '#6c757d'; // secondary
        }
        
        // Agregar estados en orden de importancia
        const ordenEstados = ['Disponibles', 'En Uso', 'En Faena', 'Inactivos'];
        const estadosAgregados = new Set();
        
        // Primero agregar estados conocidos en orden
        for (const estado of ordenEstados) {
            const valor = distribucionEquipos[estado];
            if (valor !== undefined && valor !== null && valor > 0) {
                labelsEquipos.push(estado);
                valoresEquipos.push(valor);
                coloresEquipos.push(obtenerColorEstado(estado));
                estadosAgregados.add(estado);
            }
        }
        
        // Luego agregar TODOS los demas estados (Shutdown, Operativo con anomalias, etc.)
        for (const estado in distribucionEquipos) {
            const valor = distribucionEquipos[estado];
            if (!estadosAgregados.has(estado) && valor !== undefined && valor !== null && valor > 0) {
                labelsEquipos.push(estado);
                valoresEquipos.push(valor);
                coloresEquipos.push(obtenerColorEstado(estado));
                estadosAgregados.add(estado);
            }
        }
        
        const distribucionEquiposData = {
            labels: labelsEquipos,
            datasets: [{
                data: valoresEquipos,
                backgroundColor: coloresEquipos
            }]
        };
        
        charts['maquinarias-equipos'] = new Chart(ctxEquipos, {
            type: 'doughnut',
            data: distribucionEquiposData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = distribucionEquiposData.labels[index];
                        mostrarDetallesEquipos(label, data);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }
}

/**
 * Muestra un modal con los detalles de equipos por estado.
 * 
 * @param {string} estado - Estado de los equipos ('En Faena', 'Con Anomalías', 'Shutdown', etc.)
 * @param {Object} data - Datos completos del dashboard de Operaciones o Maquinarias
 */
function mostrarDetallesEquipos(estado, data) {
    let titulo = '';
    let modalHTML = '';
    
    // Normalizar el nombre del estado para comparacion
    const estadoLower = estado.toLowerCase();
    
    if (estadoLower.includes('faena') || estadoLower.includes('asignado') || estado === 'En Faena' || estado === 'Asignado') {
        const detalles = data.equipos_en_faena_detalle || [];
        if (detalles.length === 0) {
            alert(`No hay equipos en faena`);
            return;
        }
        
        titulo = 'Equipos en Faena';
        modalHTML = `
            <div class="modal fade" id="modalDetallesEquipos" tabindex="-1" aria-labelledby="modalDetallesEquiposLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesEquiposLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                                <table class="table table-sm table-hover">
                                    <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                        <tr>
                                            <th>Equipo</th>
                                            <th>Codigo</th>
                                            <th>Faena</th>
                                            <th>Codigo Faena</th>
                                            <th>Fecha Inicio</th>
                                            <th>Fecha Fin</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(eq => `
                                            <tr>
                                                <td>${eq.equipo}</td>
                                                <td>${eq.codigo}</td>
                                                <td>${eq.faena}</td>
                                                <td>${eq.faena_codigo}</td>
                                                <td>${eq.fecha_inicio}</td>
                                                <td>${eq.fecha_fin}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (estadoLower.includes('anomalia') || estadoLower.includes('anomalía')) {
        const detalles = data.equipos_con_anomalias_detalle || [];
        if (detalles.length === 0) {
            alert(`No hay equipos operativos con anomalías`);
            return;
        }
        
        titulo = 'Equipos Operativos con Anomalías';
        modalHTML = `
            <div class="modal fade" id="modalDetallesEquipos" tabindex="-1" aria-labelledby="modalDetallesEquiposLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesEquiposLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                                <table class="table table-sm table-hover">
                                    <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                        <tr>
                                            <th>Equipo</th>
                                            <th>Codigo</th>
                                            <th>OT Folio</th>
                                            <th>Fecha Inicio</th>
                                            <th>Fecha Fin</th>
                                            <th>Observaciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(eq => `
                                            <tr>
                                                <td>${eq.equipo}</td>
                                                <td>${eq.codigo}</td>
                                                <td>${eq.ot_folio}</td>
                                                <td>${eq.fecha_inicio}</td>
                                                <td>${eq.fecha_fin}</td>
                                                <td>${eq.observaciones}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (estadoLower.includes('shutdown')) {
        const detalles = data.equipos_shutdown_detalle || [];
        if (detalles.length === 0) {
            alert(`No hay equipos en shutdown`);
            return;
        }
        
        titulo = 'Equipos en Shutdown';
        modalHTML = `
            <div class="modal fade" id="modalDetallesEquipos" tabindex="-1" aria-labelledby="modalDetallesEquiposLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesEquiposLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                                <table class="table table-sm table-hover">
                                    <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                        <tr>
                                            <th>Equipo</th>
                                            <th>Codigo</th>
                                            <th>OT Folio</th>
                                            <th>Fecha Inicio</th>
                                            <th>Fecha Fin</th>
                                            <th>Observaciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(eq => `
                                            <tr>
                                                <td>${eq.equipo}</td>
                                                <td>${eq.codigo}</td>
                                                <td>${eq.ot_folio || 'N/A'}</td>
                                                <td>${eq.fecha_inicio}</td>
                                                <td>${eq.fecha_fin}</td>
                                                <td>${eq.observaciones}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (estadoLower.includes('inactivo') || estadoLower.includes('inactivos')) {
        const detalles = data.equipos_inactivos_detalle || [];
        if (detalles.length === 0) {
            alert(`No hay equipos inactivos`);
            return;
        }
        
        titulo = 'Equipos Inactivos';
        modalHTML = `
            <div class="modal fade" id="modalDetallesEquipos" tabindex="-1" aria-labelledby="modalDetallesEquiposLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesEquiposLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                                <table class="table table-sm table-hover">
                                    <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                                        <tr>
                                            <th>Equipo</th>
                                            <th>Código</th>
                                            <th>Empresa</th>
                                            <th>Tipo</th>
                                            <th>Marca</th>
                                            <th>Modelo</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(eq => `
                                            <tr>
                                                <td>${eq.equipo}</td>
                                                <td>${eq.codigo}</td>
                                                <td>${eq.empresa}</td>
                                                <td>${eq.tipo}</td>
                                                <td>${eq.marca}</td>
                                                <td>${eq.modelo}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Para otros estados, no mostrar modal
        return;
    }
    
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesEquipos');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar el nuevo modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesEquipos'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesEquipos').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Renderiza el dashboard de Gerencia con los datos recibidos de la API.
 * 
 * Crea las tarjetas de KPIs estratégicos, gráficos consolidadas y tablas con métricas
 * de todas las áreas del sistema (RRHH, Operaciones, Maquinarias).
 * 
 * @param {Object} data - Datos del dashboard recibidos de la API
 * @param {HTMLElement} container - Contenedor donde se renderizará el dashboard
 */
function renderizarDashboardGerencia(data, container) {
    // Calcular datos para graficos
    const resumen = data.resumen_ejecutivo || {};
    const personalTotal = resumen.total_personal_activo || 0;
    const personalDisponible = resumen.personal_disponible || 0;
    const personalEnFaena = resumen.personal_en_faena || 0;
    const personalNoDisponible = personalTotal - personalDisponible;
    
    const equiposTotal = resumen.total_equipos_activos || 0;
    const equiposDisponibles = resumen.equipos_disponibles || 0;
    const equiposEnUso = resumen.equipos_en_uso || 0;
    
    let html = `
        <!-- graficos de KPIs Consolidados -->
        <div class="row mb-4">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Distribucion de Personal</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-gerencia-personal"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Distribucion de Equipos</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-gerencia-equipos"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- graficos de analisis -->
        <div class="row mb-4">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Preventivo vs Correctivo (Ultimos 30 dias)</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-gerencia-preventivo-correctivo"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">Estado de OTs</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="chart-gerencia-ots-estado"></canvas>
                        <p class="text-center mt-3 mb-0">
                            <small class="text-muted">Haz clic en un segmento para ver detalles</small>
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alertas Criticas y Resumen Ejecutivo -->
        <div class="row">
            <div class="col-12 col-md-6 mb-3 mb-md-0">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            Alertas Criticas
                        </h6>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        ${data.alertas_criticas && data.alertas_criticas.length > 0 ? `
                            <div class="list-group">
                                ${data.alertas_criticas.map(alerta => `
                                    ${alerta.documentos && alerta.documentos.length > 0 ? `
                                        <div class="list-group-item ${alerta.severidad === 'alta' ? 'list-group-item-danger' : alerta.severidad === 'media' ? 'list-group-item-warning' : 'list-group-item-info'} p-0">
                                            <div class="p-3 border-bottom bg-light">
                                                <div class="d-flex w-100 justify-content-between align-items-center">
                                                    <div>
                                                        <i class="bi bi-${alerta.icono || 'exclamation-triangle'} me-2"></i>
                                                        <strong>${alerta.tipo}</strong>
                                                    </div>
                                                    <span class="badge bg-dark rounded-pill">${alerta.cantidad}</span>
                                                </div>
                                            </div>
                                            <div class="p-0">
                                                <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                                                    <table class="table table-sm table-hover mb-0">
                                                        <thead class="table-light sticky-top">
                                                            <tr>
                                                                <th style="font-size: 0.75rem; padding: 0.5rem;">Tipo</th>
                                                                <th style="font-size: 0.75rem; padding: 0.5rem;">Documento</th>
                                                                <th style="font-size: 0.75rem; padding: 0.5rem;">Nombre</th>
                                                                <th style="font-size: 0.75rem; padding: 0.5rem; text-align: center;">Vence</th>
                                                                <th style="font-size: 0.75rem; padding: 0.5rem; text-align: center;">dias</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            ${alerta.documentos.map(doc => `
                                                                <tr>
                                                                    <td style="font-size: 0.8rem; padding: 0.5rem;">
                                                                        <i class="bi bi-${doc.tipo === 'Personal' ? 'person-fill text-primary' : 'gear-fill text-info'}"></i>
                                                                        <span class="ms-1">${doc.tipo}</span>
                                                                    </td>
                                                                    <td style="font-size: 0.8rem; padding: 0.5rem;">
                                                                        <strong>${doc.tipo_documento}</strong>
                                                                    </td>
                                                                    <td style="font-size: 0.8rem; padding: 0.5rem;">
                                                                        ${doc.nombre}
                                                                    </td>
                                                                    <td style="font-size: 0.8rem; padding: 0.5rem; text-align: center;">
                                                                        ${doc.fecha_vencimiento}
                                                                    </td>
                                                                    <td style="font-size: 0.8rem; padding: 0.5rem; text-align: center;">
                                                                        <span class="badge ${doc.dias_restantes <= 2 ? 'bg-danger' : 'bg-warning'}" style="font-size: 0.7rem;">
                                                                            ${doc.dias_restantes} dia${doc.dias_restantes !== 1 ? 's' : ''}
                                                                        </span>
                                                                    </td>
                                                                </tr>
                                                            `).join('')}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    ` : `
                                        <div class="list-group-item ${alerta.severidad === 'alta' ? 'list-group-item-danger' : alerta.severidad === 'media' ? 'list-group-item-warning' : 'list-group-item-info'}">
                                            <div class="d-flex w-100 justify-content-between align-items-center">
                                                <div>
                                                    <i class="bi bi-${alerta.icono || 'exclamation-triangle'} me-2"></i>
                                                    <strong>${alerta.tipo}</strong>
                                                </div>
                                                <span class="badge bg-dark rounded-pill">${alerta.cantidad}</span>
                                            </div>
                                        </div>
                                    `}
                                `).join('')}
                            </div>
                        ` : `
                            <div class="text-center py-3">
                                <i class="bi bi-check-circle-fill text-success" style="font-size: 2rem;"></i>
                                <p class="mt-2 text-muted mb-0">No hay alertas Criticas en este momento</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0">
                            <i class="bi bi-clipboard-data me-2"></i>
                            Resumen Ejecutivo
                        </h6>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        ${data.resumen_ejecutivo ? `
                            <table class="table table-sm table-hover mb-0">
                                <tbody>
                                    <tr>
                                        <td><strong>Personal Activo:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.total_personal_activo || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Personal Disponible:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.personal_disponible || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Personal en Faena:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.personal_en_faena || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Equipos Activos:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.total_equipos_activos || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Equipos Disponibles:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.equipos_disponibles || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Equipos en Uso:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.equipos_en_uso || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Faenas en Curso:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.faenas_en_curso || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Faenas Planificadas:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.faenas_planificadas || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Faenas Finalizadas:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.faenas_finalizadas || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>OTs Activas:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.ots_activas || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>OTs Finalizadas:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.ots_finalizadas || 0}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Alertas Criticas:</strong></td>
                                        <td class="text-end">${data.resumen_ejecutivo.alertas_criticas_pendientes || 0}</td>
                                    </tr>
                                </tbody>
                            </table>
                        ` : `
                            <div class="text-center py-3">
                                <p class="text-muted mb-0">No hay datos disponibles</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Crear grafico de Distribucion de Personal (colores iguales a operaciones)
    const ctxPersonal = document.getElementById('chart-gerencia-personal');
    if (ctxPersonal && personalTotal > 0) {
        charts['gerencia-personal'] = new Chart(ctxPersonal.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Disponible', 'En Faena', 'No Disponible'],
                datasets: [{
                    data: [
                        personalDisponible,
                        personalEnFaena,
                        personalNoDisponible - personalEnFaena
                    ],
                    backgroundColor: [
                        '#198754', // success - Disponible (igual que operaciones)
                        '#0dcaf0', // info - En Faena (igual que operaciones)
                        '#6c757d'  // secondary - No Disponible (licencias/ausentismo)
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const labels = ['Disponible', 'En Faena', 'No Disponible'];
                        const label = labels[index];
                        mostrarDetallesPersonalGerencia(label, data);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }
    
    // Crear grafico de Distribucion de Equipos (colores iguales a operaciones/maquinarias)
    const ctxEquipos = document.getElementById('chart-gerencia-equipos');
    if (ctxEquipos && equiposTotal > 0) {
        charts['gerencia-equipos'] = new Chart(ctxEquipos.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Disponibles', 'En Uso'],
                datasets: [{
                    data: [
                        equiposDisponibles,
                        equiposEnUso
                    ],
                    backgroundColor: [
                        '#198754', // success - Disponibles (igual que operaciones/maquinarias)
                        '#ffc107'  // warning - En Uso (igual que operaciones/maquinarias)
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const labels = ['Disponibles', 'En Uso'];
                        const label = labels[index];
                        mostrarDetallesEquiposGerencia(label, data);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }
    
    // Crear grafico Preventivo vs Correctivo (colores consistentes)
    if (data.ots_preventivas_30_dias !== undefined && data.ots_correctivas_30_dias !== undefined) {
        const ctxPreventivo = document.getElementById('chart-gerencia-preventivo-correctivo');
        if (ctxPreventivo) {
            charts['gerencia-preventivo'] = new Chart(ctxPreventivo.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Preventivo', 'Correctivo'],
                    datasets: [{
                        data: [data.ots_preventivas_30_dias || 0, data.ots_correctivas_30_dias || 0],
                        backgroundColor: ['#198754', '#dc3545'] // success y danger
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    aspectRatio: 2,
                    layout: {
                        padding: {
                            left: 5,
                            right: 5,
                            top: 5,
                            bottom: 5
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                font: {
                                    size: window.innerWidth < 768 ? 9 : 11
                                },
                                padding: window.innerWidth < 768 ? 8 : 12
                            },
                            onHover: function(e, legendItem) {
                                if (e.native && e.native.target) {
                                    e.native.target.style.cursor = 'pointer';
                                }
                            },
                            onLeave: function(e, legendItem) {
                                if (e.native && e.native.target) {
                                    e.native.target.style.cursor = 'default';
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const labels = ['Preventivo', 'Correctivo'];
                            const label = labels[index];
                            mostrarDetallesPreventivoCorrectivo(label, data);
                        }
                    },
                    onHover: (event, elements) => {
                        event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    }
                }
            });
        }
    }
    
    // Crear grafico Estado de OTs (colores consistentes)
    const ctxOTs = document.getElementById('chart-gerencia-ots-estado');
    if (ctxOTs) {
        charts['gerencia-ots'] = new Chart(ctxOTs.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Activas', 'Finalizadas'],
                datasets: [{
                    data: [data.ots_activas || 0, data.ots_finalizadas || 0],
                    backgroundColor: ['#198754', '#ffc107'] // Activas: verde (success), Finalizadas: amarillo (warning)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: window.innerWidth < 768 ? 9 : 11
                            },
                            padding: window.innerWidth < 768 ? 8 : 12
                        },
                        onHover: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'pointer';
                            }
                        },
                        onLeave: function(e, legendItem) {
                            if (e.native && e.native.target) {
                                e.native.target.style.cursor = 'default';
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const labels = ['Activas', 'Finalizadas'];
                        const label = labels[index];
                        mostrarDetallesOTsGerencia(label, data);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }
}

// Funciones para mostrar detalles de graficos de gerencia
/**
 * Muestra un modal con los detalles de personal para el dashboard de Gerencia.
 * 
 * @param {string} tipo - Tipo de personal ('disponible', 'en_faena', 'con_licencia', 'con_ausentismo')
 * @param {Object} data - Datos completos del dashboard de Gerencia
 */
function mostrarDetallesPersonalGerencia(tipo, data) {
    let titulo = '';
    let detalles = [];
    let modalHTML = '';
    
    if (tipo === 'En Faena') {
        titulo = 'Personal en Faena';
        detalles = data.detalles_personal_en_faena || [];
        
        if (detalles.length === 0) {
            modalHTML = `
                <div class="modal fade" id="modalDetallesGerencia" tabindex="-1" aria-labelledby="modalDetallesGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p class="text-muted">No hay personal en faena actualmente.</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            modalHTML = `
                <div class="modal fade" id="modalDetallesGerencia" tabindex="-1" aria-labelledby="modalDetallesGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead>
                                            <tr>
                                                <th>Nombre</th>
                                                <th>Faena</th>
                                                <th>Turno</th>
                                                <th>Fecha Inicio</th>
                                                <th>Fecha Fin</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${detalles.map(p => `
                                                <tr>
                                                    <td>${p.nombre}</td>
                                                    <td>${p.faena}</td>
                                                    <td>${p.turno}</td>
                                                    <td>${p.fecha_inicio}</td>
                                                    <td>${p.fecha_fin}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    } else if (tipo === 'No Disponible') {
        titulo = 'Personal No Disponible';
        detalles = data.detalles_personal_no_disponible || [];
        
        if (detalles.length === 0) {
            modalHTML = `
                <div class="modal fade" id="modalDetallesGerencia" tabindex="-1" aria-labelledby="modalDetallesGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p class="text-muted">No hay personal no disponible actualmente.</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            modalHTML = `
                <div class="modal fade" id="modalDetallesGerencia" tabindex="-1" aria-labelledby="modalDetallesGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead>
                                            <tr>
                                                <th>Nombre</th>
                                                <th>Tipo</th>
                                                <th>Detalle</th>
                                                <th>Fecha Fin</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${detalles.map(p => `
                                                <tr>
                                                    <td>${p.nombre}</td>
                                                    <td>${p.tipo}</td>
                                                    <td>${p.tipo === 'Licencia Medica' ? p.tipo_licencia : p.tipo_ausentismo}</td>
                                                    <td>${p.fecha_fin}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    } else {
        // Disponible - no mostrar detalles
        return;
    }
    
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesGerencia');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar el nuevo modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesGerencia'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesGerencia').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Muestra un modal con los detalles de equipos para el dashboard de Gerencia.
 * 
 * @param {string} tipo - Tipo de equipos ('disponibles', 'en_faena', 'anomalias', 'shutdown')
 * @param {Object} data - Datos completos del dashboard de Gerencia
 */
function mostrarDetallesEquiposGerencia(tipo, data) {
    let titulo = '';
    let detalles = [];
    let modalHTML = '';
    
    if (tipo === 'En Uso') {
        titulo = 'Equipos en Uso';
        // Combinar todos los equipos en uso
        detalles = [
            ...(data.detalles_equipos_en_uso || []),
            ...(data.detalles_equipos_shutdown || []),
            ...(data.detalles_equipos_anomalias || [])
        ];
        
        if (detalles.length === 0) {
            modalHTML = `
                <div class="modal fade" id="modalDetallesEquiposGerencia" tabindex="-1" aria-labelledby="modalDetallesEquiposGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesEquiposGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p class="text-muted">No hay equipos en uso actualmente.</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            modalHTML = `
                <div class="modal fade" id="modalDetallesEquiposGerencia" tabindex="-1" aria-labelledby="modalDetallesEquiposGerenciaLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-dark text-white">
                                <h5 class="modal-title" id="modalDetallesEquiposGerenciaLabel">${titulo}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead>
                                            <tr>
                                                <th>Equipo</th>
                                                <th>Codigo</th>
                                                <th>Tipo</th>
                                                <th>Detalle</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${detalles.map(e => `
                                                <tr>
                                                    <td>${e.nombre}</td>
                                                    <td>${e.codigo || 'N/A'}</td>
                                                    <td><span class="badge ${e.tipo === 'Shutdown' ? 'bg-danger' : e.tipo === 'anomalia' ? 'bg-warning' : 'bg-info'}">${e.tipo}</span></td>
                                                    <td>${e.faena || e.ot_folio || e.fecha_inicio || 'N/A'}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    } else {
        // Disponibles - no mostrar detalles
        return;
    }
    
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesEquiposGerencia');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar el nuevo modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesEquiposGerencia'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesEquiposGerencia').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Muestra un modal con los detalles de OTs preventivas o correctivas.
 * 
 * @param {string} tipo - Tipo de mantenimiento ('preventivo' o 'correctivo')
 * @param {Object} data - Datos completos del dashboard de Gerencia
 */
function mostrarDetallesPreventivoCorrectivo(tipo, data) {
    let titulo = '';
    let detalles = [];
    let modalHTML = '';
    
    if (tipo === 'Preventivo') {
        titulo = 'Ordenes de Trabajo Preventivas (Ultimos 30 dias)';
        detalles = data.detalles_ots_preventivas || [];
    } else if (tipo === 'Correctivo') {
        titulo = 'Ordenes de Trabajo Correctivas (Ultimos 30 dias)';
        detalles = data.detalles_ots_correctivas || [];
    } else {
        return;
    }
    
    if (detalles.length === 0) {
        modalHTML = `
            <div class="modal fade" id="modalDetallesPreventivoCorrectivo" tabindex="-1" aria-labelledby="modalDetallesPreventivoCorrectivoLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesPreventivoCorrectivoLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">No hay Ordenes de trabajo ${tipo.toLowerCase()} en los ultimos 30 dias.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        modalHTML = `
            <div class="modal fade" id="modalDetallesPreventivoCorrectivo" tabindex="-1" aria-labelledby="modalDetallesPreventivoCorrectivoLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesPreventivoCorrectivoLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Folio</th>
                                            <th>Equipo</th>
                                            <th>Fecha Creacion</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(ot => `
                                            <tr>
                                                <td>${ot.folio}</td>
                                                <td>${ot.equipo}</td>
                                                <td>${ot.fecha_creacion}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesPreventivoCorrectivo');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar el nuevo modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesPreventivoCorrectivo'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesPreventivoCorrectivo').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Muestra un modal con los detalles de órdenes de trabajo para el dashboard de Gerencia.
 * 
 * @param {string} tipo - Tipo de OTs ('activas' o 'finalizadas')
 * @param {Object} data - Datos completos del dashboard de Gerencia
 */
function mostrarDetallesOTsGerencia(tipo, data) {
    let titulo = '';
    let detalles = [];
    let modalHTML = '';
    
    if (tipo === 'Activas') {
        titulo = 'Ordenes de Trabajo Activas';
        detalles = data.detalles_ots_activas || [];
    } else if (tipo === 'Finalizadas') {
        titulo = 'Ordenes de Trabajo Finalizadas';
        detalles = data.detalles_ots_finalizadas || [];
    } else {
        return;
    }
    
    if (detalles.length === 0) {
        modalHTML = `
            <div class="modal fade" id="modalDetallesOTsGerencia" tabindex="-1" aria-labelledby="modalDetallesOTsGerenciaLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesOTsGerenciaLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">No hay Ordenes de trabajo ${tipo.toLowerCase()}.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        modalHTML = `
            <div class="modal fade" id="modalDetallesOTsGerencia" tabindex="-1" aria-labelledby="modalDetallesOTsGerenciaLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title" id="modalDetallesOTsGerenciaLabel">${titulo}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Folio</th>
                                            <th>Equipo</th>
                                            <th>Estado</th>
                                            <th>${tipo === 'Activas' ? 'Fecha Creacion' : 'Fecha Fin'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detalles.map(ot => `
                                            <tr>
                                                <td>${ot.folio}</td>
                                                <td>${ot.equipo}</td>
                                                <td><span class="badge bg-secondary">${ot.estado}</span></td>
                                                <td>${tipo === 'Activas' ? ot.fecha_creacion : ot.fecha_fin}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('modalDetallesOTsGerencia');
    if (modalAnterior) {
        modalAnterior.remove();
    }
    
    // Agregar el nuevo modal al body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetallesOTsGerencia'));
    modal.show();
    
    // Limpiar modal cuando se cierre
    document.getElementById('modalDetallesOTsGerencia').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}





