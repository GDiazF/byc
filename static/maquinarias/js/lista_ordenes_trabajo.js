// ============================================================================
// LISTA DE ÓRDENES DE TRABAJO
// ============================================================================
// Este archivo maneja la visualización y gestión de órdenes de trabajo.
// Incluye dos tabs: "Activas" y "Finalizadas", con funcionalidades de búsqueda,
// filtrado múltiple, paginación, y visualización de detalles en modal.

// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación (empieza en 1)
let tamanoPagina = 25;  // Cantidad de registros a mostrar por página (por defecto 25)
let tabActual = 'activas';  // Tab actualmente activo: 'activas' o 'finalizadas'

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar órdenes de trabajo al iniciar la página
    // Esta función hace una petición AJAX para obtener la lista de órdenes
    cargarOrdenes();
    
    // Paso 2: Configurar event listeners para filtros del tab "Activas"
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros del tab activas
    const searchInput = document.getElementById('searchInput');
    const empresaFilter = document.getElementById('empresaFilter');
    const tipoEquipoFilter = document.getElementById('tipoEquipoFilter');
    const estadoOTFilter = document.getElementById('estadoOTFilter');
    const tipoMantenimientoFilter = document.getElementById('tipoMantenimientoFilter');
    
    // Búsqueda: usar debounce para evitar demasiadas ejecuciones mientras el usuario escribe
    // Asegurar que el tab se mantenga en 'activas' al buscar
    if (searchInput) searchInput.addEventListener('input', debounce(() => { tabActual = 'activas'; cargarOrdenes(); }, 500));
    
    // Filtros: cuando cambian, asegurar que el tab esté en 'activas' y recargar
    if (empresaFilter) empresaFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (tipoEquipoFilter) tipoEquipoFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (estadoOTFilter) estadoOTFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    if (tipoMantenimientoFilter) tipoMantenimientoFilter.addEventListener('change', () => { tabActual = 'activas'; cargarOrdenes(); });
    
    // Paso 3: Configurar event listeners para filtros del tab "Finalizadas"
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros del tab finalizadas
    const searchInputFinalizadas = document.getElementById('searchInputFinalizadas');
    const empresaFilterFinalizadas = document.getElementById('empresaFilterFinalizadas');
    const tipoEquipoFilterFinalizadas = document.getElementById('tipoEquipoFilterFinalizadas');
    const tipoMantenimientoFilterFinalizadas = document.getElementById('tipoMantenimientoFilterFinalizadas');
    
    // Búsqueda: usar debounce y asegurar que el tab se mantenga en 'finalizadas'
    if (searchInputFinalizadas) searchInputFinalizadas.addEventListener('input', debounce(() => { tabActual = 'finalizadas'; cargarOrdenes(); }, 500));
    
    // Filtros: cuando cambian, asegurar que el tab esté en 'finalizadas' y recargar
    if (empresaFilterFinalizadas) empresaFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    if (tipoEquipoFilterFinalizadas) tipoEquipoFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    if (tipoMantenimientoFilterFinalizadas) tipoMantenimientoFilterFinalizadas.addEventListener('change', () => { tabActual = 'finalizadas'; cargarOrdenes(); });
    
    // Paso 4: Configurar event listeners para los tabs de Bootstrap
    // Cuando se cambia de tab, actualizar el tab actual y recargar las órdenes
    const tabActivas = document.getElementById('tab-activas');
    const tabFinalizadas = document.getElementById('tab-finalizadas');
    
    if (tabActivas) {
        // Evento que se dispara cuando el tab "Activas" se muestra
        tabActivas.addEventListener('shown.bs.tab', () => {
            tabActual = 'activas';  // Actualizar tab actual
            paginaActual = 1;  // Volver a la primera página
            cargarOrdenes();  // Recargar órdenes del tab activas
        });
    }
    
    if (tabFinalizadas) {
        // Evento que se dispara cuando el tab "Finalizadas" se muestra
        tabFinalizadas.addEventListener('shown.bs.tab', () => {
            tabActual = 'finalizadas';  // Actualizar tab actual
            paginaActual = 1;  // Volver a la primera página
            cargarOrdenes();  // Recargar órdenes del tab finalizadas
        });
    }
    
    // Paso 5: Configurar event listeners para botones de limpiar filtros
    // Cada tab tiene su propio botón para limpiar sus filtros específicos
    const btnLimpiarFiltros = document.getElementById('btnLimpiarFiltros');
    if (btnLimpiarFiltros) {
        btnLimpiarFiltros.addEventListener('click', limpiarFiltros);  // Limpiar filtros del tab activas
    }
    
    const btnLimpiarFiltrosFinalizadas = document.getElementById('btnLimpiarFiltrosFinalizadas');
    if (btnLimpiarFiltrosFinalizadas) {
        btnLimpiarFiltrosFinalizadas.addEventListener('click', limpiarFiltrosFinalizadas);  // Limpiar filtros del tab finalizadas
    }
    
    // Paso 6: Configurar event listener para cambiar tamaño de página
    // Cuando el usuario cambia cuántos registros ver por página
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', cambiarTamanoPagina);
    }
});

// Función debounce para optimizar búsquedas
// Evita ejecutar una función demasiadas veces mientras el usuario escribe
// Espera un tiempo determinado (wait) después de la última llamada antes de ejecutar la función
// Parámetros:
//   func: Función a ejecutar después del delay
//   wait: Tiempo de espera en milisegundos
// Retorna:
//   Función que puede ser llamada múltiples veces pero solo ejecuta 'func' después del delay
function debounce(func, wait) {
    let timeout;  // Variable para almacenar el ID del timeout
    return function executedFunction(...args) {
        // Función que se ejecuta después del delay
        const later = () => {
            clearTimeout(timeout);  // Limpiar el timeout (por si acaso)
            func(...args);  // Ejecutar la función original con los argumentos recibidos
        };
        clearTimeout(timeout);  // Cancelar timeout anterior si existe
        timeout = setTimeout(later, wait);  // Crear nuevo timeout con el tiempo de espera especificado
    };
}

// Función para cargar órdenes de trabajo desde el servidor con filtros y paginación
// Determina automáticamente qué tab está activo y obtiene los filtros correspondientes
// Hace una petición AJAX al endpoint de la API para obtener las órdenes filtradas y paginadas
// Actualiza la tabla, la paginación y las estadísticas con los datos recibidos
function cargarOrdenes() {
    // Paso 1: Determinar qué tab está activo actualmente
    const esFinalizadas = tabActual === 'finalizadas';
    
    // Paso 2: Obtener valores de los filtros según el tab activo
    // Cada tab tiene sus propios campos de filtro en el HTML
    let search, empresa, tipoEquipo, estadoOT, tipoMantenimiento;
    
    if (esFinalizadas) {
        // CASO: Tab "Finalizadas" activo
        // Obtener filtros del tab finalizadas (no incluye filtro de estado OT)
        search = document.getElementById('searchInputFinalizadas')?.value || '';
        empresa = document.getElementById('empresaFilterFinalizadas')?.value || '';
        tipoEquipo = document.getElementById('tipoEquipoFilterFinalizadas')?.value || '';
        estadoOT = '';  // Las finalizadas no se filtran por estado OT (ya están finalizadas)
        tipoMantenimiento = document.getElementById('tipoMantenimientoFilterFinalizadas')?.value || '';
    } else {
        // CASO: Tab "Activas" activo
        // Obtener filtros del tab activas (incluye todos los filtros disponibles)
        search = document.getElementById('searchInput')?.value || '';
        empresa = document.getElementById('empresaFilter')?.value || '';
        tipoEquipo = document.getElementById('tipoEquipoFilter')?.value || '';
        estadoOT = document.getElementById('estadoOTFilter')?.value || '';
        tipoMantenimiento = document.getElementById('tipoMantenimientoFilter')?.value || '';
    }
    
    // Paso 3: Construir parámetros de la petición HTTP
    // URLSearchParams facilita la construcción de query strings
    const params = new URLSearchParams({
        search: search,  // Término de búsqueda
        empresa_id: empresa,  // ID de empresa para filtrar
        tipo_equipo_id: tipoEquipo,  // ID de tipo de equipo para filtrar
        estado_ot: estadoOT,  // Estado de OT para filtrar (solo en tab activas)
        tipo_mantenimiento: tipoMantenimiento,  // Tipo de mantenimiento para filtrar
        solo_finalizadas: esFinalizadas ? 'true' : 'false',  // Indicar si solo se buscan finalizadas
        page: paginaActual,  // Página actual a cargar
        per_page: tamanoPagina  // Cantidad de registros por página
    });
    
    // Paso 4: Realizar petición GET al endpoint de la API
    // window.apiListarOrdenes se define en el template HTML con la URL base
    fetch(`${window.apiListarOrdenes}?${params}`)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los datos se cargaron correctamente
                // Paso 5.1: Renderizar la tabla según el tab activo
                if (esFinalizadas) {
                    renderizarOrdenesFinalizadas(data.ordenes);  // Renderizar tab finalizadas
                } else {
                    renderizarOrdenes(data.ordenes);  // Renderizar tab activas
                }
                
                // Paso 5.2: Renderizar controles de paginación
                renderizarPaginacion(data.pagination);
                
                // Paso 5.3: Actualizar estadísticas (total de órdenes, rango mostrado, etc.)
                actualizarEstadisticas(data.pagination);
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar ordenes de trabajo: ' + data.message);
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error de conexión al cargar ordenes de trabajo');  // Mostrar mensaje genérico al usuario
        });
}

// Función helper para obtener el color del badge según el tipo de mantenimiento
// Asigna colores visuales para facilitar la identificación rápida del tipo
// Parámetros:
//   tipo: Nombre del tipo de mantenimiento (ej: "Preventivo", "Correctivo")
// Retorna:
//   String con el nombre de la clase de color de Bootstrap ('success', 'danger', 'secondary')
function getColorTipoMantenimiento(tipo) {
    if (!tipo) return 'secondary';  // Si no hay tipo, usar color secundario (gris)
    const tipoLower = tipo.toLowerCase();  // Convertir a minúsculas para comparación
    if (tipoLower.includes('preventivo')) return 'success';  // Verde para mantenimiento preventivo
    if (tipoLower.includes('correctivo')) return 'danger';  // Rojo para mantenimiento correctivo
    return 'secondary';  // Color por defecto (gris) para otros tipos
}

// Función helper para obtener el color del badge según el estado de la OT
// Asigna colores visuales para facilitar la identificación rápida del estado
// Parámetros:
//   estado: Nombre del estado de la OT (ej: "Pendiente", "En Proceso", "Finalizada")
// Retorna:
//   String con el nombre de la clase de color de Bootstrap
function getColorEstadoOT(estado) {
    if (!estado) return 'secondary';  // Si no hay estado, usar color secundario (gris)
    const estadoLower = estado.toLowerCase();  // Convertir a minúsculas para comparación
    if (estadoLower.includes('pendiente')) return 'secondary';  // Gris para pendiente
    if (estadoLower.includes('proceso') || estadoLower.includes('en proceso')) return 'success';  // Verde para en proceso
    if (estadoLower.includes('finalizada') || estadoLower.includes('terminada')) return 'dark';  // Negro para finalizada
    if (estadoLower.includes('cancelada')) return 'danger';  // Rojo para cancelada
    return 'secondary';  // Color por defecto (gris) para otros estados
}

// Función helper para obtener el color del badge según el estado del equipo
// Asigna colores visuales para facilitar la identificación rápida del estado del equipo
// Parámetros:
//   estado: Nombre del estado del equipo (ej: "Disponible", "En Reparación", "Shutdown")
// Retorna:
//   String con el nombre de la clase de color de Bootstrap
function getColorEstadoEquipo(estado) {
    if (!estado) return 'secondary';  // Si no hay estado, usar color secundario (gris)
    const estadoLower = estado.toLowerCase();  // Convertir a minúsculas para comparación
    if (estadoLower.includes('shutdown')) return 'danger';  // Rojo para shutdown (equipo detenido)
    if (estadoLower.includes('disponible') && !estadoLower.includes('reparación')) return 'success';  // Verde para disponible
    if (estadoLower.includes('reparación disponible') || estadoLower.includes('en reparación disponible')) return 'warning';  // Amarillo para reparación disponible
    if (estadoLower.includes('reparación') || estadoLower.includes('en reparación')) return 'dark';  // Negro para en reparación
    return 'secondary';  // Color por defecto (gris) para otros estados
}

// Función para renderizar la tabla de órdenes de trabajo activas en el DOM
// Genera las filas de la tabla HTML con los datos de las órdenes recibidas
// Incluye badges de colores para estados y tipos, y botones de acción según permisos
// Parámetros:
//   ordenes: Array de objetos con los datos de las órdenes de trabajo a mostrar
function renderizarOrdenes(ordenes) {
    // Paso 1: Obtener referencia al tbody de la tabla donde se insertarán las filas
    const tbody = document.getElementById('ordenesTableBody');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Si no hay órdenes, mostrar mensaje de "sin resultados"
    if (ordenes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron ordenes de trabajo</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    tbody.innerHTML = ordenes.map(ot => {
        // Badge para estado OT con colores definidos
        const estadoOTColor = getColorEstadoOT(ot.estado_ot);
        const estadoOTBadge = `<span class="badge bg-${estadoOTColor}">${ot.estado_ot || 'No disponible'}</span>`;
        
        // Badge para estado equipo con colores definidos
        const estadoEquipoColor = getColorEstadoEquipo(ot.estado_equipo);
        const estadoEquipoBadge = `<span class="badge bg-${estadoEquipoColor}">${ot.estado_equipo || 'No disponible'}</span>`;
        
        // Badge para tipo mantenimiento con colores definidos
        const tipoMantenimientoColor = getColorTipoMantenimiento(ot.tipo_mantenimiento);
        const tipoMantenimientoBadge = ot.tipo_mantenimiento 
            ? `<span class="badge bg-${tipoMantenimientoColor}">${ot.tipo_mantenimiento}</span>`
            : '<span class="badge bg-secondary">N/A</span>';
        
        // Fecha fin
        const fechaFin = ot.fecha_fin 
            ? new Date(ot.fecha_fin).toLocaleDateString('es-CL')
            : '<span class="text-muted">Sin fecha</span>';
        
        return `
            <tr>
                <td>
                    <a href="#" class="text-primary text-decoration-none fw-bold" onclick="verDetalleOT(${ot.ot_id}); return false;" title="Ver detalle">
                        ${ot.folio}
                    </a>
                </td>
                <td>
                    <strong>${ot.equipo.nombreEquipo}</strong>
                </td>
                <td>${ot.empresa.nomFantasia}</td>
                <td>${tipoMantenimientoBadge}</td>
                <td>${estadoOTBadge}</td>
                <td>${estadoEquipoBadge}</td>
                <td>${fechaFin}</td>
                <td class="text-center">
                    ${ot.estado_ot && (ot.estado_ot.toUpperCase().includes('FINALIZADA') || ot.estado_ot.toUpperCase().includes('CANCELADA')) 
                        ? (window.userPermissions && window.userPermissions.canView ? `
                        <button type="button" 
                            class="btn btn-info btn-sm" 
                            onclick="verDetalleOT(${ot.ot_id})"
                            title="Ver Detalle">
                            <i class="bi bi-eye"></i> Ver
                        </button>` : '')
                        : (window.userPermissions && window.userPermissions.canChange ? `
                        <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/editar/" 
                            class="btn btn-primary btn-sm" 
                            title="Actualizar">
                            <i class="bi bi-pencil"></i> Actualizar
                        </a>` : (window.userPermissions && window.userPermissions.canView ? `
                        <button type="button" 
                            class="btn btn-info btn-sm" 
                            onclick="verDetalleOT(${ot.ot_id})"
                            title="Ver Detalle">
                            <i class="bi bi-eye"></i> Ver
                        </button>` : ''))
                    }
                </td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canGenerarPDF ? `
                    <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/pdf/" 
                       class="btn btn-danger btn-sm" 
                       title="Descargar PDF"
                       target="_blank">
                        <i class="bi bi-file-pdf"></i> PDF
                    </a>
                    ` : `
                    <button class="btn btn-danger btn-sm" disabled title="No tiene permiso para descargar PDF">
                        <i class="bi bi-file-pdf"></i> PDF
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

// Función para renderizar la tabla de órdenes de trabajo finalizadas en el DOM
// Similar a renderizarOrdenes pero para el tab de finalizadas
// Las órdenes finalizadas solo muestran botón "Ver" (no se pueden editar)
// Parámetros:
//   ordenes: Array de objetos con los datos de las órdenes finalizadas a mostrar
function renderizarOrdenesFinalizadas(ordenes) {
    // Paso 1: Obtener referencia al tbody de la tabla de finalizadas
    const tbody = document.getElementById('ordenesTableBodyFinalizadas');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Si no hay órdenes, mostrar mensaje de "sin resultados"
    if (ordenes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron ordenes finalizadas</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para cada orden finalizada usando map() y join()
    tbody.innerHTML = ordenes.map(ot => {
        // Paso 3.1: Generar badges de colores para estados y tipos (igual que en activas)
        
        // Badge para estado de la OT con colores definidos según el estado
        const estadoOTColor = getColorEstadoOT(ot.estado_ot);
        const estadoOTBadge = `<span class="badge bg-${estadoOTColor}">${ot.estado_ot || 'No disponible'}</span>`;
        
        // Badge para estado del equipo con colores definidos según el estado
        const estadoEquipoColor = getColorEstadoEquipo(ot.estado_equipo);
        const estadoEquipoBadge = `<span class="badge bg-${estadoEquipoColor}">${ot.estado_equipo || 'No disponible'}</span>`;
        
        // Badge para tipo de mantenimiento con colores definidos según el tipo
        const tipoMantenimientoColor = getColorTipoMantenimiento(ot.tipo_mantenimiento);
        const tipoMantenimientoBadge = ot.tipo_mantenimiento 
            ? `<span class="badge bg-${tipoMantenimientoColor}">${ot.tipo_mantenimiento}</span>`
            : '<span class="badge bg-secondary">N/A</span>';
        
        // Paso 3.2: Formatear fecha de fin en formato chileno
        const fechaFin = ot.fecha_fin 
            ? new Date(ot.fecha_fin).toLocaleDateString('es-CL')  // Formato DD/MM/YYYY
            : '<span class="text-muted">Sin fecha</span>';
        
        return `
            <tr>
                <td>
                    <a href="#" class="text-primary text-decoration-none fw-bold" onclick="verDetalleOT(${ot.ot_id}); return false;" title="Ver detalle">
                        ${ot.folio}
                    </a>
                </td>
                <td>
                    <strong>${ot.equipo.nombreEquipo}</strong>
                </td>
                <td>${ot.empresa.nomFantasia}</td>
                <td>${tipoMantenimientoBadge}</td>
                <td>${estadoOTBadge}</td>
                <td>${estadoEquipoBadge}</td>
                <td>${fechaFin}</td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canView ? `
                    <button type="button" 
                        class="btn btn-info btn-sm" 
                        onclick="verDetalleOT(${ot.ot_id})"
                        title="Ver Detalle">
                        <i class="bi bi-eye"></i> Ver
                    </button>
                    ` : ''}
                </td>
                <td class="text-center">
                    ${window.userPermissions && window.userPermissions.canGenerarPDF ? `
                    <a href="/maquinarias/ordenes-trabajo/${ot.ot_id}/pdf/" 
                       class="btn btn-danger btn-sm" 
                       title="Descargar PDF"
                       target="_blank">
                        <i class="bi bi-file-pdf"></i> PDF
                    </a>
                    ` : `
                    <button class="btn btn-danger btn-sm" disabled title="No tiene permiso para descargar PDF">
                        <i class="bi bi-file-pdf"></i> PDF
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

// Función para renderizar los controles de paginación
// Genera los botones de navegación de páginas con lógica de "páginas visibles"
// Muestra máximo 5 páginas alrededor de la página actual, con elipsis si hay más páginas
// Parámetros:
//   pagination: Objeto con datos de paginación (page, pages, has_prev, has_next, etc.)
function renderizarPaginacion(pagination) {
    // Paso 1: Obtener referencia al contenedor de paginación
    const paginacionEl = document.getElementById('paginacion');
    if (!paginacionEl) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Si hay una página o menos, no mostrar controles de paginación
    if (!pagination || pagination.pages <= 1) {
        paginacionEl.innerHTML = '';  // Limpiar contenido
        return;  // Salir de la función
    }
    
    let html = '';  // Variable para acumular el HTML generado
    
    // Paso 3: Generar botón "Anterior"
    // Se deshabilita si no hay página anterior (has_prev es false)
    html += `
        <li class="page-item ${!pagination.has_prev ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="irAPagina(${pagination.page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Paso 4: Calcular rango de páginas a mostrar (máximo 5 páginas visibles)
    // Mostrar 2 páginas antes y 2 después de la página actual
    const inicio = Math.max(1, pagination.page - 2);  // Página inicial del rango
    const fin = Math.min(pagination.pages, pagination.page + 2);  // Página final del rango
    
    // Paso 5: Agregar botón para la primera página si no está en el rango visible
    if (inicio > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="irAPagina(1); return false;">1</a></li>`;
        // Agregar elipsis si hay un salto entre la primera página y el rango visible
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Paso 6: Generar botones para las páginas del rango visible
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="irAPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Paso 7: Agregar botón para la última página si no está en el rango visible
    if (fin < pagination.pages) {
        // Agregar elipsis si hay un salto entre el rango visible y la última página
        if (fin < pagination.pages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="irAPagina(${pagination.pages}); return false;">${pagination.pages}</a></li>`;
    }
    
    // Paso 8: Generar botón "Siguiente"
    // Se deshabilita si no hay página siguiente (has_next es false)
    html += `
        <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="irAPagina(${pagination.page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    // Paso 9: Insertar el HTML generado en el contenedor de paginación
    paginacionEl.innerHTML = html;
}

// Función para navegar a una página específica de la paginación
// Se ejecuta cuando el usuario hace clic en un número de página o botón de navegación
// Parámetros:
//   pagina: Número de página a la que se quiere navegar
function irAPagina(pagina) {
    if (pagina < 1) return;  // Validar que la página sea válida (mayor o igual a 1)
    paginaActual = pagina;  // Actualizar variable global con la nueva página
    cargarOrdenes();  // Recargar órdenes con la nueva página
    window.scrollTo({ top: 0, behavior: 'smooth' });  // Hacer scroll suave hacia arriba para ver la tabla
}

// Función para cambiar el tamaño de página (cantidad de registros por página)
// Se ejecuta cuando el usuario cambia el valor del select de tamaño de página
function cambiarTamanoPagina() {
    tamanoPagina = parseInt(document.getElementById('pageSizeSelect').value);  // Actualizar tamaño de página
    paginaActual = 1;  // Volver a la primera página cuando cambia el tamaño
    cargarOrdenes();  // Recargar órdenes con el nuevo tamaño de página
}

// Función para actualizar las estadísticas mostradas en la página
// Actualiza contadores de total de órdenes, rango de registros mostrados, etc.
// Parámetros:
//   pagination: Objeto con datos de paginación (total, page, per_page, etc.)
function actualizarEstadisticas(pagination) {
    // Paso 1: Obtener referencias a los elementos donde se muestran las estadísticas
    const totalOrdenes = document.getElementById('totalOrdenes');  // Total de órdenes encontradas
    const registroInicio = document.getElementById('registroInicio');  // Número del primer registro mostrado
    const registroFin = document.getElementById('registroFin');  // Número del último registro mostrado
    const totalRegistros = document.getElementById('totalRegistros');  // Total de registros (igual a totalOrdenes)
    
    // Paso 2: Actualizar cada estadística si el elemento existe
    if (totalOrdenes) totalOrdenes.textContent = pagination.total;  // Total de órdenes
    
    // Calcular número del primer registro mostrado: (página - 1) * registros_por_página + 1
    if (registroInicio) registroInicio.textContent = pagination.total > 0 
        ? ((pagination.page - 1) * pagination.per_page + 1) 
        : 0;
    
    // Calcular número del último registro mostrado: mínimo entre (página * registros_por_página) y total
    if (registroFin) registroFin.textContent = Math.min(
        pagination.page * pagination.per_page,  // Último registro de la página actual
        pagination.total  // Total de registros (si es menor que el último de la página)
    );
    
    if (totalRegistros) totalRegistros.textContent = pagination.total;  // Total de registros
}

// Función para limpiar todos los filtros del tab "Activas"
// Se ejecuta cuando el usuario hace clic en el botón "Limpiar Filtros" del tab activas
function limpiarFiltros() {
    // Limpiar todos los campos de filtro del tab activas
    document.getElementById('searchInput').value = '';  // Limpiar búsqueda
    document.getElementById('empresaFilter').value = '';  // Limpiar filtro de empresa
    document.getElementById('tipoEquipoFilter').value = '';  // Limpiar filtro de tipo de equipo
    document.getElementById('estadoOTFilter').value = '';  // Limpiar filtro de estado OT
    document.getElementById('tipoMantenimientoFilter').value = '';  // Limpiar filtro de tipo de mantenimiento
    paginaActual = 1;  // Volver a la primera página
    tabActual = 'activas';  // Asegurar que el tab esté en activas
    cargarOrdenes();  // Recargar órdenes sin filtros
}

// Función para limpiar todos los filtros del tab "Finalizadas"
// Se ejecuta cuando el usuario hace clic en el botón "Limpiar Filtros" del tab finalizadas
function limpiarFiltrosFinalizadas() {
    // Limpiar todos los campos de filtro del tab finalizadas
    document.getElementById('searchInputFinalizadas').value = '';  // Limpiar búsqueda
    document.getElementById('empresaFilterFinalizadas').value = '';  // Limpiar filtro de empresa
    document.getElementById('tipoEquipoFilterFinalizadas').value = '';  // Limpiar filtro de tipo de equipo
    document.getElementById('tipoMantenimientoFilterFinalizadas').value = '';  // Limpiar filtro de tipo de mantenimiento
    paginaActual = 1;  // Volver a la primera página
    tabActual = 'finalizadas';  // Asegurar que el tab esté en finalizadas
    cargarOrdenes();  // Recargar órdenes sin filtros
}

// Función para mostrar el modal con el detalle completo de una orden de trabajo
// Carga información general, observaciones e historial desde el servidor mediante AJAX
// El modal tiene tres pestañas: Información, Observaciones e Historial
// Parámetros:
//   ot_id: ID de la orden de trabajo cuyo detalle se va a mostrar
function verDetalleOT(ot_id) {
    // Paso 1: Obtener referencias a los elementos del modal
    const modal = new bootstrap.Modal(document.getElementById('modalDetalleOT'));  // Instancia del modal
    const modalTitle = document.getElementById('modalDetalleOTLabel');  // Título del modal
    const panelInformacion = document.getElementById('panel-informacion');  // Panel de información general
    const panelObservaciones = document.getElementById('panel-observaciones');  // Panel de observaciones
    const panelHistorial = document.getElementById('panel-historial');  // Panel de historial de cambios
    
    // Paso 2: Mostrar indicadores de carga en todas las pestañas mientras se cargan los datos
    // Esto mejora la experiencia del usuario mostrando que algo está pasando
    panelInformacion.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando detalles...</p>
        </div>
    `;
    panelObservaciones.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando observaciones...</p>
        </div>
    `;
    panelHistorial.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando historial...</p>
        </div>
    `;
    
    // Paso 3: Activar la primera pestaña (Información) por defecto
    const tabInformacion = document.getElementById('tab-informacion');
    if (tabInformacion) {
        const bsTab = new bootstrap.Tab(tabInformacion);
        bsTab.show();  // Mostrar la pestaña de información
    }
    
    // Paso 4: Mostrar el modal (los datos se cargarán después mediante AJAX)
    modal.show();
    
    // Paso 5: Cargar detalles de la OT desde el servidor (información general y observaciones)
    // window.apiDetalleOT se define en el template HTML con la URL base (contiene '0' como placeholder)
    const urlDetalle = window.apiDetalleOT.replace('0', ot_id);  // Reemplazar '0' con el ID real
    fetch(urlDetalle)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los datos se cargaron correctamente
                // Paso 5.1: Actualizar título del modal con el folio de la OT
                modalTitle.innerHTML = `<i class="bi bi-clipboard-data me-2"></i>Detalle - ${data.ot.folio}`;
                
                // Paso 5.2: Renderizar información general de la OT (equipo, fechas, estados, etc.)
                renderizarDetalleOT(data.ot, panelInformacion);
                
                // Paso 5.3: Renderizar observaciones de la OT (iniciales e historial)
                renderizarObservacionesOT(data.ot, panelObservaciones);
            } else {
                // CASO ERROR: El servidor retornó un error
                panelInformacion.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar detalles: ${data.message}
                    </div>
                `;
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            panelInformacion.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar detalles
                </div>
            `;
        });
    
    // Paso 6: Cargar historial de cambios de la OT desde el servidor (en paralelo con los detalles)
    // window.apiHistorialOT se define en el template HTML con la URL base (contiene '0' como placeholder)
    const urlHistorial = window.apiHistorialOT.replace('0', ot_id);  // Reemplazar '0' con el ID real
    fetch(urlHistorial)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: El historial se cargó correctamente
                // Renderizar historial de cambios en el panel correspondiente
                renderizarHistorialOT(data, panelHistorial, null);
            } else {
                // CASO ERROR: El servidor retornó un error
                panelHistorial.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar historial: ${data.message}
                    </div>
                `;
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            panelHistorial.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar historial
                </div>
            `;
        });
}

// Función para renderizar las observaciones de una orden de trabajo en el modal
// Muestra la observación inicial (si existe) y el historial de observaciones agregadas
// Parámetros:
//   ot: Objeto con los datos de la orden de trabajo (incluye observaciones e historial_observaciones)
//   container: Elemento DOM donde se insertará el HTML generado
function renderizarObservacionesOT(ot, container) {
    let html = '';  // Variable para acumular el HTML generado
    
    // Paso 1: Mostrar observación inicial si existe
    // La observación inicial se guarda al crear la OT
    if (ot.observaciones) {
        html += `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary">
                                <i class="bi bi-file-text me-1"></i>Observación Inicial
                            </strong>
                        </div>
                        <small class="text-muted">
                            <i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(ot.fecha_creacion)}
                        </small>
                    </div>
                    <p class="mb-0">${ot.observaciones}</p>
                </div>
            </div>
        `;
    }
    
    // Paso 2: Mostrar historial de observaciones agregadas después de la creación
    // Estas observaciones se agregan mediante la función de agregar observación
    if (ot.historial_observaciones && ot.historial_observaciones.length > 0) {
        // Generar HTML para cada observación del historial
        html += ot.historial_observaciones.map(obs => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary"><i class="bi bi-person-circle me-1"></i>${obs.usuario}</strong>
                        </div>
                        <small class="text-muted"><i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(obs.fecha)}</small>
                    </div>
                    <p class="mb-0">${obs.observacion}</p>
                </div>
            </div>
        `).join('');  // Unir todas las observaciones en un solo string
    } else if (!ot.observaciones) {
        // Si no hay observación inicial ni historial, mostrar mensaje informativo
        html = '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay observaciones registradas</div>';
    }
    
    // Paso 3: Insertar el HTML generado en el contenedor
    container.innerHTML = `
        <div class="card border">
            <div class="card-body">
                ${html}
            </div>
        </div>
    `;
}

// Renderizar historial de OT en el modal
function renderizarHistorialOT(data, modalBody, modalTitle) {
    const historial = data.historial || [];
    
    // Actualizar título del modal solo si se proporciona
    if (modalTitle && data.ot) {
        modalTitle.innerHTML = `<i class="bi bi-clock-history me-2"></i>Historial - ${data.ot.folio}`;
    }
    
    let infoHTML = '';
    
    if (historial.length > 0) {
        // Tabla simple con filas expandibles (acordeón)
        infoHTML = `
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
            
            // Generar detalles expandibles solo si hay información adicional que no esté en la descripción
            let detallesHTML = '';
            let tieneDetalles = false;
            
            // Solo mostrar detalles si hay información adicional relevante que no esté en la descripción
            // La descripción ya contiene los cambios principales, así que solo mostramos:
            // 1. Personal asignado (lista completa de nombres)
            // 2. Información adicional que no esté en la descripción
            
            if (evento.personal && Array.isArray(evento.personal) && evento.personal.length > 0) {
                // Personal asignado - mostrar lista completa si hay múltiples personas
                const nombres = evento.personal.map(p => p.nombre_completo).join(', ');
                detallesHTML = '<div class="small">';
                detallesHTML += `<div class="mb-2"><strong>Personal asignado:</strong><ul class="mb-0 mt-1">`;
                evento.personal.forEach(p => {
                    detallesHTML += `<li>${p.nombre_completo}${p.rut ? ` (RUT: ${p.rut})` : ''}</li>`;
                });
                detallesHTML += '</ul></div>';
                tieneDetalles = true;
            }
            
            // Información adicional que no esté en la descripción (solo campos realmente útiles)
            if (evento.datos_nuevos) {
                const camposTecnicos = [
                    'estado_ot_nombre', 'estado_equipo_nombre', 'estado_seccion_nombre',
                    'seccion_nombre', 'fecha_fin', 'personal_ids',
                    'estado_ot_id', 'estado_equipo_id', 'estado_seccion_id',
                    'seccion_id', 'equipo_id', 'equipo_nombre', 'folio',
                    'tipo_mantenimiento', 'estado_ot', 'estado_equipo'
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
    } else {
        infoHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay registros en el historial de esta orden de trabajo.
            </div>
        `;
    }
    
    modalBody.innerHTML = infoHTML;
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

// Funciones helper para iconos y colores según acción
function getIconoAccion(accion) {
    const iconos = {
        'OT_CREADA': '<i class="bi bi-plus-circle-fill text-success fs-5"></i>',
        'OT_MODIFICADA': '<i class="bi bi-pencil-fill text-primary fs-5"></i>',
        'ESTADO_OT_CAMBIADO': '<i class="bi bi-arrow-repeat text-info fs-5"></i>',
        'ESTADO_EQUIPO_CAMBIADO': '<i class="bi bi-gear-fill text-warning fs-5"></i>',
        'ESTADO_SECCION_CAMBIADO': '<i class="bi bi-diagram-3-fill text-secondary fs-5"></i>',
        'FECHA_INICIO_CAMBIADA': '<i class="bi bi-calendar-event-fill text-primary fs-5"></i>',
        'FECHA_FIN_CAMBIADA': '<i class="bi bi-calendar-event-fill text-primary fs-5"></i>',
        'PERSONAL_ASIGNADO': '<i class="bi bi-person-plus-fill text-success fs-5"></i>',
        'PERSONAL_ELIMINADO': '<i class="bi bi-person-dash-fill text-danger fs-5"></i>',
        'OBSERVACION_AGREGADA': '<i class="bi bi-chat-left-text-fill text-info fs-5"></i>'
    };
    return iconos[accion] || '<i class="bi bi-info-circle-fill text-secondary fs-5"></i>';
}

function getBadgeColorAccion(accion) {
    const colores = {
        'OT_CREADA': 'bg-success',
        'OT_MODIFICADA': 'bg-primary',
        'ESTADO_OT_CAMBIADO': 'bg-info',
        'ESTADO_EQUIPO_CAMBIADO': 'bg-warning text-dark',
        'ESTADO_SECCION_CAMBIADO': 'bg-secondary',
        'FECHA_INICIO_CAMBIADA': 'bg-primary',
        'FECHA_FIN_CAMBIADA': 'bg-primary',
        'PERSONAL_ASIGNADO': 'bg-success',
        'PERSONAL_ELIMINADO': 'bg-danger',
        'OBSERVACION_AGREGADA': 'bg-info'
    };
    return colores[accion] || 'bg-secondary';
}

function getBorderColorAccion(index) {
    const colores = ['border-primary', 'border-secondary', 'border-info', 'border-warning', 'border-success'];
    return colores[index % colores.length];
}

function getBackgroundColorAccion(accion) {
    const colores = {
        'OT_CREADA': 'bg-light',
        'OT_MODIFICADA': '',
        'ESTADO_OT_CAMBIADO': 'bg-light bg-opacity-50',
        'ESTADO_EQUIPO_CAMBIADO': 'bg-light bg-opacity-50',
        'ESTADO_SECCION_CAMBIADO': 'bg-light bg-opacity-50',
        'FECHA_INICIO_CAMBIADA': '',
        'FECHA_FIN_CAMBIADA': '',
        'PERSONAL_ASIGNADO': 'bg-light',
        'PERSONAL_ELIMINADO': 'bg-light bg-opacity-50',
        'OBSERVACION_AGREGADA': 'bg-light'
    };
    return colores[accion] || '';
}

function getBorderLeftColorAccion(accion) {
    const colores = {
        'OT_CREADA': '#198754',
        'OT_MODIFICADA': '#0d6efd',
        'ESTADO_OT_CAMBIADO': '#0dcaf0',
        'ESTADO_EQUIPO_CAMBIADO': '#ffc107',
        'ESTADO_SECCION_CAMBIADO': '#6c757d',
        'FECHA_INICIO_CAMBIADA': '#0d6efd',
        'FECHA_FIN_CAMBIADA': '#0d6efd',
        'PERSONAL_ASIGNADO': '#198754',
        'PERSONAL_ELIMINADO': '#dc3545',
        'OBSERVACION_AGREGADA': '#0dcaf0'
    };
    return colores[accion] || '#6c757d';
}

// Función helper para formatear fechas en formato chileno (DD/MM/YYYY o DD/MM/YYYY HH:MM)
// Convierte fechas del formato ISO (YYYY-MM-DD) al formato chileno más legible
// Parámetros:
//   fechaString: String con la fecha en formato ISO (YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
// Retorna:
//   String con la fecha formateada en formato chileno, o 'N/A' si no hay fecha, o el string original si hay error
function formatearFechaChilena(fechaString) {
    if (!fechaString) return 'N/A';  // Si no hay fecha, retornar 'N/A'
    
    try {
        // Paso 1: Intentar parsear diferentes formatos de fecha
        let fecha;
        
        // Si incluye hora (formato: YYYY-MM-DD HH:MM:SS)
        if (fechaString.includes(' ')) {
            // Reemplazar espacio con 'T' para que JavaScript pueda parsear correctamente
            fecha = new Date(fechaString.replace(' ', 'T'));
        } else {
            // Solo fecha (formato: YYYY-MM-DD)
            // Agregar 'T00:00:00' para crear una fecha válida a medianoche
            fecha = new Date(fechaString + 'T00:00:00');
        }
        
        // Paso 2: Validar que la fecha se pudo parsear correctamente
        if (isNaN(fecha.getTime())) {
            return fechaString;  // Si no se puede parsear, devolver string original
        }
        
        // Paso 3: Formatear en formato chileno DD/MM/YYYY o DD/MM/YYYY HH:MM si tiene hora
        const dia = String(fecha.getDate()).padStart(2, '0');  // Día con cero a la izquierda si es necesario
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');  // Mes (getMonth() es 0-based, por eso +1)
        const año = fecha.getFullYear();  // Año completo
        
        if (fechaString.includes(' ')) {
            // Si tiene hora, incluir también horas y minutos
            const horas = String(fecha.getHours()).padStart(2, '0');  // Horas con cero a la izquierda
            const minutos = String(fecha.getMinutes()).padStart(2, '0');  // Minutos con cero a la izquierda
            return `${dia}/${mes}/${año} ${horas}:${minutos}`;  // Formato: DD/MM/YYYY HH:MM
        } else {
            return `${dia}/${mes}/${año}`;  // Formato: DD/MM/YYYY
        }
    } catch (e) {
        // CASO EXCEPCIÓN: Cualquier error al parsear o formatear
        return fechaString;  // Si hay error, devolver string original
    }
}

// Renderizar detalle de OT en modal
function renderizarDetalleOT(ot, container) {
    const secciones = ot.corresponde_pauta && ot.secciones_pauta.length > 0 
        ? ot.secciones_pauta 
        : ot.secciones_manuales;
    
    const seccionesHTML = secciones && secciones.length > 0 ? secciones.map(sec => `
        <div class="card mb-2 border">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0 fw-bold">${sec.seccion_nombre}</h6>
                    <span class="badge bg-${getColorEstadoOT(sec.estado_seccion)}" style="font-size: 0.75rem;">${sec.estado_seccion || 'Pendiente'}</span>
                </div>
                ${sec.tipos_reparacion && sec.tipos_reparacion.length > 0 
                    ? `<div class="mt-2">
                        <small class="text-muted d-block mb-1">Tipos de Reparación:</small>
                        <ul class="mb-0 ps-3" style="font-size: 0.875rem;">
                            ${sec.tipos_reparacion.map(tr => `<li>${tr}</li>`).join('')}
                        </ul>
                    </div>`
                    : '<small class="text-muted">Sin tipos de reparación</small>'
                }
            </div>
        </div>
    `).join('') : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay secciones registradas</div>';
    
    const personalHTML = ot.personal_asignado && ot.personal_asignado.length > 0
        ? ot.personal_asignado.map(p => `
            <div class="card mb-2 border">
                <div class="card-body p-2">
                    <div class="d-flex justify-content-between align-items-center" style="font-size: 0.875rem;">
                        <div>
                            <strong class="d-block" style="font-size: 0.875rem;">${p.nombre_completo}</strong>
                            <small class="text-muted" style="font-size: 0.8rem;">${p.rut}</small>
                        </div>
                        <span class="badge bg-primary" style="font-size: 0.75rem;">${p.cargo}</span>
                    </div>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>Sin personal asignado</div>';
    
    const historialObservacionesHTML = ot.historial_observaciones && ot.historial_observaciones.length > 0
        ? ot.historial_observaciones.map(obs => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-primary"><i class="bi bi-person-circle me-1"></i>${obs.usuario}</strong>
                        </div>
                        <small class="text-muted"><i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(obs.fecha)}</small>
                    </div>
                    <p class="mb-0">${obs.observacion}</p>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay observaciones registradas</div>';
    
    const historialCambiosHTML = ot.historial_cambios && ot.historial_cambios.length > 0
        ? ot.historial_cambios.map(cambio => `
            <div class="card mb-2 border">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong class="d-block mb-1"><i class="bi bi-arrow-repeat me-1"></i>${cambio.accion}</strong>
                            <small class="text-muted d-block mb-2">${cambio.descripcion}</small>
                        </div>
                        <div class="text-end ms-3">
                            <small class="text-muted d-block"><i class="bi bi-person me-1"></i>${cambio.usuario}</small>
                            <small class="text-muted d-block"><i class="bi bi-clock me-1"></i>${formatearFechaChilena(cambio.fecha_hora)}</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('')
        : '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>No hay cambios registrados</div>';
    
    container.innerHTML = `
        <div class="row g-3">
            <div class="col-md-6">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-info-circle me-2 text-primary"></i>Información General</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-sm table-bordered mb-0">
                            <tbody>
                                <tr>
                                    <th style="width: 40%;" class="bg-light">Folio:</th>
                                    <td><strong class="text-primary">${ot.folio}</strong></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Equipo:</th>
                                    <td>${ot.equipo.nombreEquipo} <small class="text-muted">(${ot.equipo.codigoInterno})</small></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Tipo:</th>
                                    <td>${ot.equipo.tipoEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Marca:</th>
                                    <td>${ot.equipo.marcaEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Modelo:</th>
                                    <td>${ot.equipo.modeloEquipo || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Empresa:</th>
                                    <td>${ot.empresa.nomFantasia}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Tipo Mantenimiento:</th>
                                    <td><span class="badge bg-${getColorTipoMantenimiento(ot.tipo_mantenimiento)}">${ot.tipo_mantenimiento}</span></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Estado OT:</th>
                                    <td><span class="badge bg-${getColorEstadoOT(ot.estado_ot)}">${ot.estado_ot}</span></td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Estado Equipo:</th>
                                    <td><span class="badge bg-${getColorEstadoEquipo(ot.estado_equipo)}">${ot.estado_equipo}</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-calendar-event me-2 text-primary"></i>Fechas y Mediciones</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-sm table-bordered mb-0">
                            <tbody>
                                <tr>
                                    <th style="width: 40%;" class="bg-light">Fecha Creación:</th>
                                    <td>${formatearFechaChilena(ot.fecha_creacion)}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Fecha Inicio:</th>
                                    <td>${ot.fecha_inicio ? formatearFechaChilena(ot.fecha_inicio) : 'Sin fecha'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Fecha Fin:</th>
                                    <td>${ot.fecha_fin ? formatearFechaChilena(ot.fecha_fin) : 'Sin fecha'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Horómetro:</th>
                                    <td>${ot.horometro || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Odómetro:</th>
                                    <td>${ot.odometro || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th class="bg-light">Horómetro Superestructura:</th>
                                    <td>${ot.horometro_superestructura || 'N/A'}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        ${ot.corresponde_pauta && ot.pauta_nombre ? `
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-clipboard-check me-2 text-primary"></i>Pauta de Mantenimiento</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-0"><strong>${ot.pauta_nombre}</strong></p>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-list-check me-2 text-primary"></i>Secciones</h6>
                    </div>
                    <div class="card-body">
                        ${seccionesHTML}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-people me-2 text-primary"></i>Personal Asignado</h6>
                    </div>
                    <div class="card-body">
                        ${personalHTML}
                    </div>
                </div>
            </div>
        </div>
        
        ${ot.observaciones ? `
        <div class="row mt-3">
            <div class="col-12">
                <div class="card border">
                    <div class="card-header bg-light">
                        <h6 class="mb-0 fw-bold"><i class="bi bi-journal-text me-2 text-primary"></i>Observación Inicial</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <strong class="text-primary">
                                    <i class="bi bi-file-text me-1"></i>Observación Inicial
                                </strong>
                            </div>
                            <small class="text-muted">
                                <i class="bi bi-calendar3 me-1"></i>${formatearFechaChilena(ot.fecha_creacion)}
                            </small>
                        </div>
                        <p class="mb-0">${ot.observaciones}</p>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
    `;
}

// Función para mostrar mensajes de error al usuario
// Usa alert() nativo del navegador para mostrar el error
// También registra el error en la consola para debugging
// Parámetros:
//   mensaje: Texto del mensaje de error a mostrar
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);  // Mostrar alerta al usuario
    console.error(mensaje);  // Registrar error en consola para debugging
}
