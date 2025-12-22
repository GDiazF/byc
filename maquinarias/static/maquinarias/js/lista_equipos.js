// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación
let tamanoPagina = 25;  // Cantidad de registros a mostrar por página
let currentToggle = null;  // Referencia al checkbox que se está desactivando (para el modal de confirmación)
let originalState = false;  // Estado original del checkbox antes del cambio
let changeConfirmed = false;  // Flag que indica si el cambio fue confirmado
let equiposSeleccionados = [];  // Array de objetos con información de equipos seleccionados para descarga
// Formato: [{equipo_id, nombreEquipo, codigoInterno, tipoEquipo, marcaEquipo}, ...]
let todosLosEquipos = [];  // Almacenar todos los equipos activos para búsqueda en el modal de selección
let equiposCargados = [];  // Almacenar los equipos de la página actual para acceso rápido
let ordenActual = null;  // Columna actual por la cual se está ordenando
let direccionOrden = 'asc';  // Dirección del ordenamiento ('asc' o 'desc')

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar equipos al iniciar la página
    // Esta función hace una petición AJAX para obtener la lista de equipos
    cargarEquipos();
    
    // Paso 2: Configurar event listeners para los filtros
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    // Se usa debounce en la búsqueda para evitar demasiadas ejecuciones mientras el usuario escribe
    document.getElementById('searchInput').addEventListener('input', debounce(cargarEquipos, 500));  // Búsqueda con delay de 500ms
    document.getElementById('empresaFilter').addEventListener('change', cargarEquipos);  // Filtro por empresa
    document.getElementById('tipoFilter').addEventListener('change', cargarEquipos);  // Filtro por tipo de equipo
    document.getElementById('marcaFilter').addEventListener('change', cargarEquipos);  // Filtro por marca
    
    // Paso 2.1: Configurar event listeners para ordenamiento por columnas
    // Los headers con clase 'sortable' permiten ordenar la tabla haciendo clic
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const columna = this.getAttribute('data-column');  // Obtener nombre de la columna desde atributo data
            ordenarPor(columna, this);  // Ordenar por la columna seleccionada
        });
    });
    
    // Paso 2.2: Configurar event delegation para los links de nombres de equipos
    // Usar event delegation porque los elementos se crean dinámicamente
    document.addEventListener('click', function(e) {
        const linkEquipo = e.target.closest('.equipo-nombre-link');
        if (linkEquipo) {
            e.preventDefault();
            const equipoId = linkEquipo.getAttribute('data-equipo-id');
            if (equipoId) {
                mostrarDetalleEquipo(parseInt(equipoId));
            }
        }
    });
    
    // Paso 3: Configurar el botón de confirmación del modal de desactivación
    // Cuando el usuario confirma la desactivación, se ejecuta esta función
    document.getElementById('btnConfirmarDesactivar').addEventListener('click', confirmarDesactivacion);
    
    // Paso 4: Limpiar estado cuando se cierra el modal de confirmación
    // Si el usuario cierra el modal sin confirmar, se revierte el cambio en el checkbox
    document.getElementById('confirmDesactivarModal').addEventListener('hidden.bs.modal', function() {
        // Si hay un toggle pendiente y no fue confirmado, revertir su estado
        if (currentToggle && !changeConfirmed) {
            currentToggle.checked = originalState;  // Restaurar estado original
        }
        // Limpiar referencias para el próximo uso
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
    
    // Inicializar modal de selección de equipos para descarga
    const btnSeleccionarEquipos = document.getElementById('btnSeleccionarEquipos');
    if (btnSeleccionarEquipos) {
        btnSeleccionarEquipos.addEventListener('click', function(e) {
            e.preventDefault();
            const modalElement = document.getElementById('modalSeleccionarEquipos');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                equiposSeleccionados = [];
                actualizarVistaSeleccionadosEquipos();
                // Cargar todos los equipos activos para búsqueda
                cargarTodosLosEquipos();
            }
        });
    }
    
    // Configurar búsqueda cuando el modal se muestra
    const modalSeleccionarEquipos = document.getElementById('modalSeleccionarEquipos');
    if (modalSeleccionarEquipos) {
        modalSeleccionarEquipos.addEventListener('shown.bs.modal', function() {
            console.log('Modal mostrado, configurando buscador...');
            // Configurar el event listener del buscador cuando el modal se muestra
            const buscarEquiposModal = document.getElementById('buscarEquiposModal');
            if (buscarEquiposModal) {
                console.log('Campo de búsqueda encontrado');
                // Remover listener anterior si existe
                if (buscarEquiposModal._buscarHandler) {
                    buscarEquiposModal.removeEventListener('input', buscarEquiposModal._buscarHandler);
                }
                // Crear nuevo handler - capturar el valor del input correctamente
                let timeoutBusqueda = null;
                buscarEquiposModal._buscarHandler = function(e) {
                    const inputElement = e.target || buscarEquiposModal;
                    const valor = inputElement.value;
                    console.log('Buscando:', valor);
                    
                    // Limpiar timeout anterior
                    if (timeoutBusqueda) {
                        clearTimeout(timeoutBusqueda);
                    }
                    
                    // Crear nuevo timeout para debounce
                    timeoutBusqueda = setTimeout(function() {
                        buscarEquiposEnModal(valor);
                    }, 300);
                };
                buscarEquiposModal.addEventListener('input', buscarEquiposModal._buscarHandler);
                // Limpiar el campo de búsqueda
                buscarEquiposModal.value = '';
                // Limpiar resultados
                const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
                if (resultadosDiv) {
                    resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
                }
            } else {
                console.error('No se encontró el campo buscarEquiposModal');
            }
        });
        
        // Limpiar búsqueda y selección cuando se cierra el modal
        modalSeleccionarEquipos.addEventListener('hidden.bs.modal', function() {
            // Limpiar campo de búsqueda
            const buscarEquiposModal = document.getElementById('buscarEquiposModal');
            if (buscarEquiposModal) {
                buscarEquiposModal.value = '';
            }
            // Limpiar resultados de búsqueda
            const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
            if (resultadosDiv) {
                resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
            }
            // Limpiar selección
            equiposSeleccionados = [];
            actualizarVistaSeleccionadosEquipos();
        });
    }
    
    // Botón limpiar selección
    const btnLimpiarSeleccionEquipos = document.getElementById('btnLimpiarSeleccionEquipos');
    if (btnLimpiarSeleccionEquipos) {
        btnLimpiarSeleccionEquipos.addEventListener('click', function() {
            equiposSeleccionados = [];
            actualizarVistaSeleccionadosEquipos();
            const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
            if (resultadosDiv) {
                resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
            }
        });
    }
    
    // Botón descargar ZIP - usar delegación de eventos ya que el botón está dentro del modal
    // Manejar clics tanto en el botón como en sus elementos hijos (íconos, texto)
    document.addEventListener('click', function(e) {
        const btnDescargarZip = e.target.closest('#btnDescargarZipEquipos');
        if (btnDescargarZip && !btnDescargarZip.disabled) {
            e.preventDefault();
            e.stopPropagation();
            descargarDocumentacionZipEquipos();
        }
    });
});

// Función debounce para optimizar búsquedas y filtros
// Esta función retrasa la ejecución de una función hasta que haya pasado un tiempo determinado
// sin nuevas llamadas. Útil para evitar ejecutar funciones costosas en cada tecla presionada.
// Parámetros:
//   func: función a ejecutar después del delay
//   wait: tiempo de espera en milisegundos
function debounce(func, wait) {
    let timeout;  // Variable para almacenar el ID del timeout
    return function executedFunction(...args) {
        // Función que se ejecuta cuando se llama a debounce
        const later = () => {
            clearTimeout(timeout);  // Limpiar timeout anterior si existe
            func(...args);  // Ejecutar la función original con los argumentos
        };
        clearTimeout(timeout);  // Cancelar timeout anterior si existe
        timeout = setTimeout(later, wait);  // Crear nuevo timeout
    };
}

// Función para cargar equipos desde el servidor con filtros aplicados
// Esta función obtiene la lista de equipos activos según los filtros seleccionados
// y actualiza la tabla, paginación y estadísticas
function cargarEquipos() {
    // Paso 1: Obtener valores de los campos de filtro
    // Estos valores se envían al servidor para filtrar los equipos
    const search = document.getElementById('searchInput').value;  // Texto de búsqueda
    const empresa = document.getElementById('empresaFilter').value;  // Empresa seleccionada
    const tipo = document.getElementById('tipoFilter').value;  // Tipo de equipo seleccionado
    const marca = document.getElementById('marcaFilter').value;  // Marca seleccionada
    
    // Paso 2: Construir parámetros de la petición
    // Se incluyen los filtros, paginación, ordenamiento y estado (siempre activos)
    const params = new URLSearchParams({
        search: search,  // Término de búsqueda
        empresa: empresa,  // Filtro por empresa
        tipo: tipo,  // Filtro por tipo
        marca: marca,  // Filtro por marca
        estado: 'activos',  // Siempre mostrar solo equipos activos
        page: paginaActual,  // Página actual
        page_size: tamanoPagina  // Tamaño de página
    });
    
    // Agregar parámetros de ordenamiento si hay una columna seleccionada
    if (ordenActual) {
        params.append('ordering', ordenActual);  // Columna por la cual ordenar
        params.append('order_direction', direccionOrden);  // Dirección del ordenamiento
    }
    
    // Paso 3: Realizar petición GET al endpoint de equipos con los parámetros
    fetch(`/maquinarias/api/equipos/?${params}`)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los equipos se cargaron correctamente
                // Paso 4.1: Guardar equipos cargados para acceso rápido
                equiposCargados = data.equipos;
                
                // Paso 4.2: Renderizar la tabla con los equipos recibidos
                renderizarEquipos(data.equipos);
                
                // Paso 4.3: Renderizar controles de paginación
                renderizarPaginacion(data.pagination);
                
                // Paso 4.4: Actualizar estadísticas (total de registros, etc.)
                actualizarEstadisticas(data.pagination);
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar equipos: ' + data.error);
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error de conexión al cargar equipos');  // Mostrar mensaje al usuario
        });
}

// Función para renderizar la tabla de equipos en el HTML
// Esta función genera el HTML de las filas de la tabla con los datos de los equipos
// Parámetros:
//   equipos: Array de objetos con información de equipos recibidos del servidor
function renderizarEquipos(equipos) {
    // Paso 1: Obtener referencia al tbody de la tabla
    const tbody = document.getElementById('equiposTableBody');
    
    // Paso 2: Manejar caso cuando no hay equipos para mostrar
    // Mostrar mensaje informativo cuando no se encuentran resultados
    if (equipos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron equipos activos</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función ya que no hay nada más que hacer
    }
    
    // Paso 3: Generar HTML para cada equipo usando map()
    // Se crea una fila de tabla por cada equipo con toda su información
    tbody.innerHTML = equipos.map(equipo => `
        <tr>
            <td>
                <a href="#" 
                   class="equipo-nombre-link" 
                   data-equipo-id="${equipo.equipo_id}"
                   title="Click para ver información del equipo y documentación">
                    ${equipo.nombreEquipo}
                </a>
            </td>
            <td>
                <span class="badge bg-secondary">${equipo.tipoEquipo.sigla}</span>
                <span class="ms-1">${equipo.tipoEquipo.nombre}</span>
            </td>
            <td>${equipo.marcaEquipo.nombre}</td>
            <td>${equipo.modeloEquipo.nombre}</td>
            <td>${equipo.empresa.nombre}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${window.userPermissions.canViewDocumentacion ? `
                    <a href="/maquinarias/equipos/${equipo.equipo_id}/documentacion/" 
                       class="btn btn-sm btn-primary" 
                       title="Ver Documentación">
                        <i class="bi bi-folder"></i>
                    </a>
                    ` : ''}
                    ${window.userPermissions.canEdit ? `
                    <a href="/maquinarias/equipos/${equipo.equipo_id}/editar/" 
                       class="btn btn-sm btn-secondary" 
                       title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    ` : ''}
                    ${window.userPermissions.canViewHistorial ? `
                    <button type="button" class="btn btn-sm btn-info" onclick="verHistorialEquipo(${equipo.equipo_id}, '${equipo.nombreEquipo.replace(/'/g, "\\'")}')" title="Ver Historial">
                        <i class="bi bi-clock-history"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-switch d-inline-block">
                    <input class="form-check-input" type="checkbox" 
                           style="cursor: ${window.userPermissions.canDesactivar || window.userPermissions.canActivar ? 'pointer' : 'not-allowed'};"
                           data-equipo-id="${equipo.equipo_id}"
                           data-nombre-equipo="${equipo.nombreEquipo.replace(/'/g, "\\'")}"
                           ${equipo.activo ? 'checked' : ''} 
                           ${(equipo.activo && !window.userPermissions.canDesactivar) || (!equipo.activo && !window.userPermissions.canActivar) ? 'disabled' : ''}
                           onchange="toggleEstadoEquipo(this)"
                           title="${equipo.activo ? (window.userPermissions.canDesactivar ? 'Desactivar equipo' : 'No tiene permiso para desactivar') : (window.userPermissions.canActivar ? 'Activar equipo' : 'No tiene permiso para activar')}">
                </div>
            </td>
        </tr>
    `).join('');  // Unir todos los strings HTML en uno solo
}

// Función para ordenar la tabla por una columna específica
// Alterna entre orden ascendente y descendente si se hace clic en la misma columna
// Actualiza los iconos visuales en los headers para indicar el ordenamiento actual
// Parámetros:
//   columna: Nombre de la columna por la cual ordenar
//   headerElement: Elemento DOM del header que fue clickeado
function ordenarPor(columna, headerElement) {
    // Paso 1: Determinar la dirección del ordenamiento
    // Si es la misma columna, cambiar dirección (asc <-> desc)
    if (ordenActual === columna) {
        direccionOrden = direccionOrden === 'asc' ? 'desc' : 'asc';  // Alternar dirección
    } else {
        // Si es una columna diferente, establecer como nueva columna y empezar con ascendente
        ordenActual = columna;  // Actualizar columna actual
        direccionOrden = 'asc';  // Empezar con orden ascendente
    }
    
    // Paso 2: Actualizar iconos en todos los headers ordenables
    // Resetear todos los iconos a estado neutro (flecha bidireccional)
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up ms-1';  // Icono neutro
    });
    
    // Paso 3: Actualizar icono del header clickeado según la dirección del ordenamiento
    const icon = headerElement.querySelector('i');
    if (icon) {
        // Mostrar flecha hacia arriba para ascendente, hacia abajo para descendente
        icon.className = direccionOrden === 'asc' ? 'bi bi-arrow-up ms-1' : 'bi bi-arrow-down ms-1';
    }
    
    // Paso 4: Volver a la primera página y recargar equipos con el nuevo ordenamiento
    paginaActual = 1;  // Volver a la primera página
    cargarEquipos();  // Recargar equipos con el ordenamiento aplicado
}

// Función para renderizar los controles de paginación en la interfaz
// Genera los botones de página anterior, números de página y página siguiente
// Parámetros:
//   pagination: Objeto con información de paginación del servidor (current_page, total_pages, has_previous, has_next)
function renderizarPaginacion(pagination) {
    // Paso 1: Obtener referencia al contenedor de paginación
    const paginacionDiv = document.getElementById('paginacion');
    
    // Paso 2: Si hay una página o menos, no mostrar controles de paginación
    // No tiene sentido mostrar paginación si no hay múltiples páginas
    if (pagination.total_pages <= 1) {
        paginacionDiv.innerHTML = '';  // Limpiar cualquier paginación previa
        return;  // Salir de la función
    }
    
    // Paso 3: Inicializar variable para construir el HTML de la paginación
    let html = '';
    
    // Paso 4: Generar botón de página anterior
    // Se deshabilita si no hay página anterior disponible
    html += `
        <li class="page-item ${!pagination.has_previous ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Paso 5: Calcular rango de páginas a mostrar alrededor de la página actual
    // Se muestran 2 páginas antes y 2 después de la página actual (total 5 páginas visibles)
    const startPage = Math.max(1, pagination.current_page - 2);  // Primera página a mostrar (mínimo 1)
    const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);  // Última página a mostrar (máximo total_pages)
    
    // Paso 6: Si el rango no comienza en la página 1, mostrar botón de página 1 y elipsis
    // Esto permite navegar rápidamente a la primera página
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a></li>`;
        if (startPage > 2) {
            // Si hay más de una página entre el inicio y la página 1, mostrar elipsis
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Paso 7: Generar botones para cada página en el rango visible
    // La página actual se marca como 'active' para indicar visualmente dónde está el usuario
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === pagination.current_page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Paso 8: Si el rango no termina en la última página, mostrar elipsis y botón de última página
    // Esto permite navegar rápidamente a la última página
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            // Si hay más de una página entre el final y la última página, mostrar elipsis
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${pagination.total_pages}); return false;">${pagination.total_pages}</a></li>`;
    }
    
    // Paso 9: Generar botón de página siguiente
    // Se deshabilita si no hay página siguiente disponible
    html += `
        <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${pagination.current_page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    // Paso 10: Actualizar el HTML del contenedor de paginación con todos los botones generados
    paginacionDiv.innerHTML = html;
}

// Función para actualizar las estadísticas de paginación mostradas al usuario
// Muestra información sobre el total de registros y el rango de registros visible en la página actual
// Parámetros:
//   pagination: Objeto con información de paginación del servidor (current_page, total_count, page_size)
function actualizarEstadisticas(pagination) {
    // Paso 1: Actualizar el total de equipos encontrados
    // Este número representa todos los equipos que cumplen los filtros aplicados
    document.getElementById('totalEquipos').textContent = pagination.total_count;
    
    // Paso 2: Calcular el rango de registros visible en la página actual
    // inicio: número del primer registro visible (1-indexed)
    // fin: número del último registro visible
    const inicio = (pagination.current_page - 1) * pagination.page_size + 1;  // Primer registro de la página
    const fin = Math.min(pagination.current_page * pagination.page_size, pagination.total_count);  // Último registro (puede ser menor si es la última página)
    
    // Paso 3: Actualizar los elementos HTML con las estadísticas calculadas
    // Estos elementos muestran información como "Mostrando 1-25 de 150 registros"
    document.getElementById('registroInicio').textContent = pagination.total_count > 0 ? inicio : 0;  // Primer registro visible (0 si no hay registros)
    document.getElementById('registroFin').textContent = fin;  // Último registro visible
    document.getElementById('totalRegistros').textContent = pagination.total_count;  // Total de registros
}

// Función para cambiar a una página específica de la paginación
// Se ejecuta cuando el usuario hace clic en un número de página o en los botones anterior/siguiente
// Parámetros:
//   pagina: Número de página a la que se quiere navegar (1-indexed)
function cambiarPagina(pagina) {
    // Paso 1: Actualizar la variable global con la nueva página actual
    paginaActual = pagina;
    
    // Paso 2: Recargar los equipos con la nueva página
    // Esto hace una nueva petición al servidor con el número de página actualizado
    cargarEquipos();
}

// Función para cambiar la cantidad de registros mostrados por página
// Se ejecuta cuando el usuario selecciona un nuevo tamaño de página desde el select
function cambiarTamanoPagina() {
    // Paso 1: Obtener el nuevo tamaño de página seleccionado por el usuario
    // Se convierte a entero porque viene como string desde el select
    tamanoPagina = parseInt(document.getElementById('pageSizeSelect').value);
    
    // Paso 2: Resetear a la primera página cuando cambia el tamaño
    // Esto evita problemas si la página actual ya no existe con el nuevo tamaño
    paginaActual = 1;
    
    // Paso 3: Recargar los equipos con el nuevo tamaño de página
    // Esto hace una nueva petición al servidor con el tamaño de página actualizado
    cargarEquipos();
}

// Función para limpiar todos los filtros aplicados y resetear la búsqueda
// Se ejecuta cuando el usuario hace clic en el botón "Limpiar filtros"
function limpiarFiltros() {
    // Paso 1: Limpiar el campo de búsqueda de texto
    document.getElementById('searchInput').value = '';
    
    // Paso 2: Limpiar el filtro de empresa (volver a "Todas")
    document.getElementById('empresaFilter').value = '';
    
    // Paso 3: Limpiar el filtro de tipo de equipo (volver a "Todos")
    document.getElementById('tipoFilter').value = '';
    
    // Paso 4: Limpiar el filtro de marca (volver a "Todas")
    document.getElementById('marcaFilter').value = '';
    
    // Paso 5: Resetear a la primera página después de limpiar filtros
    paginaActual = 1;
    
    // Paso 6: Recargar los equipos sin filtros aplicados
    // Esto muestra todos los equipos activos desde el principio
    cargarEquipos();
}

// ============================================================================
// TOGGLE DE ESTADO (ACTIVAR/DESACTIVAR EQUIPO)
// ============================================================================

// Función que se ejecuta cuando el usuario intenta cambiar el estado activo/inactivo de un equipo
// Muestra un modal de confirmación antes de realizar el cambio
// Parámetros:
//   checkbox: Elemento checkbox que fue cambiado
function toggleEstadoEquipo(checkbox) {
    // Paso 1: Guardar referencias del checkbox y su estado original
    // Esto permite revertir el cambio si el usuario cancela la acción
    currentToggle = checkbox;  // Guardar referencia al checkbox actual
    originalState = !checkbox.checked;  // Guardar estado original (antes del cambio)
    changeConfirmed = false;  // Marcar que el cambio aún no está confirmado
    
    // Paso 2: Revertir el cambio visual inmediatamente
    // El checkbox vuelve a su estado original hasta que se confirme en el modal
    checkbox.checked = originalState;
    
    // Paso 3: Actualizar el nombre del equipo en el modal de confirmación
    // Esto muestra al usuario qué equipo está intentando desactivar/activar
    const nombreEquipo = checkbox.dataset.nombreEquipo;  // Obtener nombre desde atributo data
    const nombreElement = document.getElementById('equipoDesactivarNombre');
    if (nombreElement) {
        nombreElement.textContent = nombreEquipo;  // Mostrar nombre en el modal
    }
    
    // Paso 4: Preparar el modal de confirmación
    // Cerrar cualquier instancia existente del modal para evitar conflictos
    const modalElement = document.getElementById('confirmDesactivarModal');
    if (!modalElement) {
        console.error('Modal element not found');
        return;  // Salir si no se encuentra el elemento del modal
    }
    
    // Paso 5: Cerrar y limpiar cualquier instancia previa del modal
    // Esto asegura que el modal se muestre correctamente
    const existingModal = bootstrap.Modal.getInstance(modalElement);
    if (existingModal) {
        existingModal.dispose();  // Limpiar instancia anterior
    }
    
    // Paso 6: Mostrar el modal de confirmación
    // El usuario debe confirmar antes de que se cambie el estado del equipo
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Función que se ejecuta cuando el usuario confirma el cambio de estado del equipo
// Realiza la petición al servidor para cambiar el estado activo/inactivo
function confirmarDesactivacion() {
    // Paso 1: Validar que hay un toggle pendiente
    // Si no hay checkbox seleccionado, salir sin hacer nada
    if (!currentToggle) return;
    
    // Paso 2: Obtener el ID del equipo desde el atributo data del checkbox
    // Este ID se usa para identificar qué equipo cambiar en el servidor
    const equipoId = parseInt(currentToggle.dataset.equipoId);
    
    // Paso 3: Calcular el nuevo estado (opuesto al estado original)
    // Si estaba activo, se desactiva; si estaba inactivo, se activa
    const nuevoEstado = !originalState;
    
    // Paso 4: Realizar petición POST al servidor para cambiar el estado
    // Se envía el ID del equipo y el token CSRF para seguridad
    fetch(`/maquinarias/api/equipos/${equipoId}/toggle-activo/`, {
        method: 'POST',  // Método HTTP POST para modificar datos
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken  // Token CSRF para protección contra ataques
        }
    })
    .then(response => response.json())  // Convertir respuesta a JSON
    .then(data => {
        if (data.status === 'success') {
            // CASO ÉXITO: El estado fue cambiado correctamente
            // Paso 5.1: Marcar que el cambio fue confirmado
            // Esto previene que se revierta el cambio cuando se cierre el modal
            changeConfirmed = true;
            
            // Paso 5.2: Cerrar el modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
            confirmModal.hide();
            
            // Paso 5.3: Mostrar notificación de éxito al usuario
            // El mensaje varía según si se activó o desactivó el equipo
            const accion = data.activo ? 'activado' : 'desactivado';
            mostrarExito(`Equipo ${accion} correctamente`);
            
            // Paso 5.4: Recargar la lista de equipos
            // Esto actualiza la tabla con el nuevo estado del equipo
            cargarEquipos();
        } else {
            // CASO ERROR: El servidor retornó un error
            // Paso 6.1: Cerrar el modal
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
            confirmModal.hide();
            
            // Paso 6.2: Mostrar mensaje de error al usuario
            alert('Error: ' + (data.message || 'Error al cambiar el estado del equipo'));
            
            // Paso 6.3: Revertir el checkbox a su estado original
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        // Paso 7.1: Registrar error en consola para debugging
        console.error('Error:', error);
        
        // Paso 7.2: Cerrar el modal
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDesactivarModal'));
        confirmModal.hide();
        
        // Paso 7.3: Mostrar mensaje genérico de error
        alert('Error al cambiar el estado del equipo');
        
        // Paso 7.4: Revertir el checkbox a su estado original
        currentToggle.checked = originalState;
    });
}


// Mostrar notificación estilo alert
function showNotification(message, type = 'success') {
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 3000);
}

// Mostrar mensaje de éxito
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

// ============================================================================
// MODAL DE SELECCIÓN DE EQUIPOS PARA DESCARGA
// ============================================================================

// Cargar todos los equipos activos para búsqueda en modal
function cargarTodosLosEquipos() {
    console.log('Cargando todos los equipos...');
    fetch('/maquinarias/api/equipos/?estado=activos&page_size=9999')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                todosLosEquipos = data.equipos;
                console.log(`Cargados ${todosLosEquipos.length} equipos para búsqueda`);
            } else {
                console.error('Error al cargar equipos:', data.error);
            }
        })
        .catch(error => {
            console.error('Error al cargar equipos:', error);
        });
}

// Buscar equipos en el modal
function buscarEquiposEnModal(termino) {
    console.log('buscarEquiposEnModal llamada con término:', termino);
    const resultadosDiv = document.getElementById('resultadosBusquedaEquipos');
    
    if (!resultadosDiv) {
        console.error('No se encontró el div de resultados');
        return;
    }
    
    if (!termino || termino.trim() === '') {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">Ingrese un término de búsqueda...</p>';
        return;
    }
    
    // Verificar que los equipos estén cargados
    if (!todosLosEquipos || todosLosEquipos.length === 0) {
        console.log('Equipos no cargados aún, esperando...');
        resultadosDiv.innerHTML = '<p class="text-warning text-center mb-0"><i class="bi bi-hourglass-split me-1"></i>Cargando equipos...</p>';
        // Intentar cargar nuevamente
        cargarTodosLosEquipos();
        // Reintentar después de un segundo
        setTimeout(() => {
            if (todosLosEquipos && todosLosEquipos.length > 0) {
                buscarEquiposEnModal(termino);
            } else {
                resultadosDiv.innerHTML = '<p class="text-danger text-center mb-0">Error al cargar equipos. Por favor recargue la página.</p>';
            }
        }, 1000);
        return;
    }
    
    console.log(`Buscando en ${todosLosEquipos.length} equipos`);
    const terminoLower = termino.toLowerCase().trim();
    console.log('Término de búsqueda (lowercase):', terminoLower);
    
    const resultados = todosLosEquipos.filter(e => {
        const nombreMatch = e.nombreEquipo && e.nombreEquipo.toLowerCase().includes(terminoLower);
        const codigoMatch = e.codigoInterno && e.codigoInterno.toLowerCase().includes(terminoLower);
        const patenteMatch = e.patente && e.patente !== '-' && e.patente.toLowerCase().includes(terminoLower);
        const marcaMatch = e.marcaEquipo && e.marcaEquipo.nombre && e.marcaEquipo.nombre.toLowerCase().includes(terminoLower);
        const modeloMatch = e.modeloEquipo && e.modeloEquipo.nombre && e.modeloEquipo.nombre.toLowerCase().includes(terminoLower);
        const tipoMatch = e.tipoEquipo && e.tipoEquipo.nombre && e.tipoEquipo.nombre.toLowerCase().includes(terminoLower);
        
        return nombreMatch || codigoMatch || patenteMatch || marcaMatch || modeloMatch || tipoMatch;
    });
    
    console.log(`Resultados encontrados: ${resultados.length}`);
    
    if (resultados.length === 0) {
        resultadosDiv.innerHTML = '<p class="text-muted text-center mb-0">No se encontraron resultados</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    resultados.forEach(e => {
        const yaSeleccionado = equiposSeleccionados.some(es => es.equipo_id === e.equipo_id);
        html += `
            <div class="list-group-item list-group-item-action ${yaSeleccionado ? 'bg-light' : ''}" 
                 style="cursor: pointer;" 
                 data-equipo-id="${e.equipo_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${e.nombreEquipo}</h6>
                        <small class="text-muted">Código: ${e.codigoInterno} | ${e.tipoEquipo.nombre} | ${e.marcaEquipo.nombre} ${e.modeloEquipo.nombre}</small>
                    </div>
                    ${yaSeleccionado 
                        ? '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Seleccionado</span>'
                        : '<button class="btn btn-sm btn-primary btn-agregar-equipo" data-equipo-id="' + e.equipo_id + '"><i class="bi bi-plus-circle me-1"></i>Agregar</button>'
                    }
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultadosDiv.innerHTML = html;
    
    // Agregar event listeners a los botones y items
    resultadosDiv.querySelectorAll('.btn-agregar-equipo').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const equipoId = parseInt(this.dataset.equipoId);
            agregarEquipoSeleccionado(equipoId);
        });
    });
    
    resultadosDiv.querySelectorAll('.list-group-item').forEach(item => {
        item.addEventListener('click', function() {
            const equipoId = parseInt(this.dataset.equipoId);
            if (!equiposSeleccionados.some(es => es.equipo_id === equipoId)) {
                agregarEquipoSeleccionado(equipoId);
            }
        });
    });
}

// Agregar equipo a la lista de seleccionados
function agregarEquipoSeleccionado(equipoId) {
    const equipo = todosLosEquipos.find(e => e.equipo_id === equipoId);
    if (!equipo) return;
    
    // Verificar si ya está seleccionado
    if (equiposSeleccionados.some(es => es.equipo_id === equipoId)) {
        return;
    }
    
    equiposSeleccionados.push({
        equipo_id: equipo.equipo_id,
        nombreEquipo: equipo.nombreEquipo,
        codigoInterno: equipo.codigoInterno,
        tipoEquipo: equipo.tipoEquipo.nombre,
        marcaEquipo: equipo.marcaEquipo.nombre,
        modeloEquipo: equipo.modeloEquipo.nombre
    });
    
    actualizarVistaSeleccionadosEquipos();
    
    // Actualizar la vista de resultados para mostrar que está seleccionado
    const termino = document.getElementById('buscarEquiposModal').value;
    if (termino) {
        buscarEquiposEnModal(termino);
    }
}

// Remover equipo de la lista de seleccionados
function removerEquipoSeleccionado(equipoId) {
    equiposSeleccionados = equiposSeleccionados.filter(es => es.equipo_id !== equipoId);
    actualizarVistaSeleccionadosEquipos();
    
    // Actualizar la vista de resultados
    const termino = document.getElementById('buscarEquiposModal').value;
    if (termino) {
        buscarEquiposEnModal(termino);
    }
}

// Actualizar la vista de equipos seleccionados
function actualizarVistaSeleccionadosEquipos() {
    const contador = document.getElementById('contadorSeleccionadosEquipos');
    const vistaSeleccionados = document.getElementById('equiposSeleccionados');
    const btnDescargarZipEquipos = document.getElementById('btnDescargarZipEquipos');
    
    if (!vistaSeleccionados) return; // Si el modal no está abierto, no hacer nada
    
    if (contador) {
        contador.textContent = equiposSeleccionados.length;
    }
    
    if (btnDescargarZipEquipos) {
        // Verificar permisos - igual que personal_table.js
        const canViewDocumentation = window.userPermissions && (
            window.userPermissions.canViewDocumentacion === true || 
            window.userPermissions.canViewDocumentacion === 'true' ||
            window.userPermissions.canView === true ||
            window.userPermissions.canView === 'true'
        );
        // Deshabilitar si no tiene permisos O si no hay equipos seleccionados
        btnDescargarZipEquipos.disabled = !canViewDocumentation || equiposSeleccionados.length === 0;
    }
    
    if (equiposSeleccionados.length === 0) {
        vistaSeleccionados.innerHTML = '<p class="text-muted text-center mb-0">No hay equipos seleccionados</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    equiposSeleccionados.forEach(e => {
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${e.nombreEquipo}</h6>
                        <small class="text-muted">Código: ${e.codigoInterno} | ${e.tipoEquipo}</small>
                    </div>
                    <button class="btn btn-sm btn-danger btn-remover-equipo" data-equipo-id="${e.equipo_id}">
                        <i class="bi bi-x-circle me-1"></i>Quitar
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    vistaSeleccionados.innerHTML = html;
    
    // Agregar event listeners a los botones de quitar
    vistaSeleccionados.querySelectorAll('.btn-remover-equipo').forEach(btn => {
        btn.addEventListener('click', function() {
            const equipoId = parseInt(this.dataset.equipoId);
            removerEquipoSeleccionado(equipoId);
        });
    });
}

// Descargar documentación en ZIP
function descargarDocumentacionZipEquipos() {
    console.log('descargarDocumentacionZipEquipos llamada');
    console.log('Equipos seleccionados:', equiposSeleccionados);
    
    if (equiposSeleccionados.length === 0) {
        alert('Por favor seleccione al menos un equipo');
        return;
    }
    
    const equipoIds = equiposSeleccionados.map(e => e.equipo_id);
    console.log('IDs de equipos:', equipoIds);
    
    // Obtener URL
    const url = window.descargarDocumentacionZipEquiposUrl || '/maquinarias/equipos/descargar-documentacion-zip/';
    console.log('URL de descarga:', url);
    
    // Crear formulario para enviar POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    
    // Agregar CSRF token
    const csrfToken = window.csrfToken || getCookie('csrftoken');
    console.log('CSRF Token:', csrfToken ? 'Encontrado' : 'No encontrado');
    
    if (!csrfToken) {
        alert('Error: No se pudo obtener el token CSRF. Por favor recargue la página.');
        return;
    }
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
    // Agregar IDs de los equipos
    equipoIds.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'equipo_ids';
        input.value = id;
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    console.log('Enviando formulario...');
    form.submit();
    document.body.removeChild(form);
    
    // Cerrar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalSeleccionarEquipos'));
    if (modal) {
        modal.hide();
    }
    
    // Limpiar selección
    equiposSeleccionados = [];
    actualizarVistaSeleccionadosEquipos();
}

// Función helper para obtener cookie
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

// Función para mostrar el detalle del equipo en un modal
// Similar a la función del calendario de equipos
// Hacerla disponible globalmente para que pueda ser llamada desde onclick en el HTML
window.mostrarDetalleEquipo = function(equipoId) {
    console.log('mostrarDetalleEquipo llamado con equipoId:', equipoId);
    console.log('equiposCargados:', equiposCargados);
    
    // Buscar el equipo en los datos cargados
    const equipo = equiposCargados.find(e => e.equipo_id === equipoId);
    if (!equipo) {
        console.error('Equipo no encontrado:', equipoId, 'Total equipos cargados:', equiposCargados.length);
        alert('Error: No se pudo encontrar la información del equipo. Por favor, recargue la página.');
        return;
    }
    
    const modalBody = document.getElementById('equipoModalBody');
    if (!modalBody) return;
    
    // Crear estructura con tabs simplificada (estilo del proyecto)
    modalBody.innerHTML = `
        <!-- Nav tabs -->
        <ul class="nav nav-tabs mb-3" id="equipoTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="info-tab" data-bs-toggle="tab" data-bs-target="#info-pane" type="button" role="tab" aria-controls="info-pane" aria-selected="true">
                    <i class="bi bi-info-circle me-1"></i>Información
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="documentacion-tab" data-bs-toggle="tab" data-bs-target="#documentacion-pane" type="button" role="tab" aria-controls="documentacion-pane" aria-selected="false" data-equipo-id="${equipoId}">
                    <i class="bi bi-folder me-1"></i>Documentación
                </button>
            </li>
        </ul>
        
        <!-- Tab panes -->
        <div class="tab-content" id="equipoTabContent">
            <!-- Tab: Información -->
            <div class="tab-pane fade show active" id="info-pane" role="tabpanel" aria-labelledby="info-tab">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-info-circle me-2 text-primary"></i>Información General</h6>
                            </div>
                            <div class="card-body p-0">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Nombre:</th>
                                            <td><strong>${equipo.nombreEquipo}</strong></td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Código Interno:</th>
                                            <td>${equipo.codigoInterno || 'N/A'}</td>
                                        </tr>
                                        ${equipo.patente && equipo.patente !== '-' ? `
                                        <tr>
                                            <th class="bg-light">Patente:</th>
                                            <td>${equipo.patente}</td>
                                        </tr>
                                        ` : ''}
                                        <tr>
                                            <th class="bg-light">Empresa:</th>
                                            <td>${equipo.empresa.nombre || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Tipo:</th>
                                            <td>${equipo.tipoEquipo.nombre || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Marca:</th>
                                            <td>${equipo.marcaEquipo.nombre || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Modelo:</th>
                                            <td>${equipo.modeloEquipo.nombre || 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-speedometer2 me-2 text-success"></i>Horómetros y Odómetro</h6>
                            </div>
                            <div class="card-body p-0">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Horómetro:</th>
                                            <td>${equipo.horometro ? equipo.horometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Odómetro:</th>
                                            <td>${equipo.odometro ? equipo.odometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Horómetro Superestructura:</th>
                                            <td>${equipo.horometroSuperEstructural ? equipo.horometroSuperEstructural.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tab: Documentación -->
            <div class="tab-pane fade" id="documentacion-pane" role="tabpanel" aria-labelledby="documentacion-tab">
                <div id="documentosContainer">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando documentación...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('equipoModal'));
    modal.show();
    
    // Actualizar título del modal
    const modalTitle = document.getElementById('equipoModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `Información del Equipo: ${equipo.nombreEquipo}`;
    }
    
    // Agregar listener para cuando se active el tab de documentación
    const documentacionTab = document.getElementById('documentacion-tab');
    if (documentacionTab) {
        documentacionTab.addEventListener('shown.bs.tab', function (e) {
            const equipoId = e.target.getAttribute('data-equipo-id');
            if (equipoId) {
                cargarDocumentosEquipo(parseInt(equipoId));
            }
        });
    }
}

// Cargar documentos del equipo
async function cargarDocumentosEquipo(equipoId) {
    const container = document.getElementById('documentosContainer');
    if (!container) return;
    
    try {
        const response = await fetch(`/maquinarias/api/equipos/${equipoId}/documentos/`);
        const data = await response.json();
        
        if (data.success && data.documentos) {
            renderizarDocumentosEquipo(data.documentos, container);
        } else {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay documentación disponible para este equipo.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error al cargar documentos:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error al cargar la documentación. Por favor, intente nuevamente.
            </div>
        `;
    }
}

// Renderizar documentos del equipo en formato tabla simple (estilo del proyecto)
function renderizarDocumentosEquipo(documentos, container) {
    if (!documentos || documentos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay documentación disponible para este equipo.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-sm table-hover table-bordered rrhh-table">
                <thead class="table-dark">
                    <tr>
                        <th>Tipo de Documento</th>
                        <th>Fecha Subida</th>
                        <th>Fecha Vencimiento</th>
                        <th>Estado</th>
                        <th class="text-center">Acciones</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    documentos.forEach(doc => {
        const fechaVencimiento = doc.fecha_vencimiento 
            ? new Date(doc.fecha_vencimiento).toLocaleDateString('es-CL')
            : 'N/A';
        const fechaSubida = new Date(doc.fecha_subida).toLocaleDateString('es-CL');
        
        let badgeEstado = '';
        if (doc.estado === 'vencido') {
            badgeEstado = '<span class="badge bg-danger">Vencido</span>';
        } else if (doc.estado === 'por_vencer') {
            badgeEstado = `<span class="badge bg-warning text-dark">Por vencer (${doc.dias_restantes} días)</span>`;
        } else {
            badgeEstado = '<span class="badge bg-success text-white">Vigente</span>';
        }
        
        const archivoLink = doc.archivo_url 
            ? `<a href="${doc.archivo_url}" target="_blank" class="btn btn-sm btn-primary" title="${doc.archivo_nombre || 'Ver documento'}">
                 <i class="bi bi-eye"></i>
               </a>`
            : '<span class="text-muted">N/A</span>';
        
        html += `
            <tr>
                <td><strong>${doc.tipo_documento_nombre}</strong></td>
                <td>${fechaSubida}</td>
                <td>${fechaVencimiento}</td>
                <td>${badgeEstado}</td>
                <td class="text-center">${archivoLink}</td>
            </tr>
        `;
        
        if (doc.observaciones) {
            html += `
                <tr>
                    <td colspan="5" class="small text-muted bg-light">
                        <strong>Observaciones:</strong> ${doc.observaciones}
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

