// ============================================================================
// LISTA DE PAUTAS DE MANTENIMIENTO
// ============================================================================
// Este archivo maneja la visualización de modelos de equipos con sus pautas de mantenimiento.
// Incluye funcionalidades de búsqueda, filtrado múltiple (tipo, marca, modelo),
// paginación, ordenamiento por columnas, y navegación a pautas específicas.

// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación (empieza en 1)
let tamanoPagina = 10;  // Cantidad de registros a mostrar por página (por defecto 10)
let pautaIdAccion = null;  // ID de la pauta pendiente de acción (actualmente no se usa, mantenido para compatibilidad)
let modeloActual = null;  // Modelo actualmente seleccionado (actualmente no se usa, mantenido para compatibilidad)
let ordenActual = '';  // Columna actualmente utilizada para ordenar (vacío por defecto)
let direccionOrden = 'asc';  // Dirección del ordenamiento ('asc' para ascendente, 'desc' para descendente)

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar modelos al iniciar la página
    // Esta función hace una petición AJAX para obtener la lista de modelos con sus pautas
    cargarModelos();
    
    // Paso 2: Configurar event listeners para los filtros
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    
    // Búsqueda: usar debounce para evitar demasiadas ejecuciones mientras el usuario escribe
    // El debounce espera 500ms después de que el usuario deja de escribir antes de ejecutar la búsqueda
    document.getElementById('searchInput').addEventListener('input', debounce(cargarModelos, 500));
    
    // Filtros: cuando cambian, recargar modelos con los nuevos filtros aplicados
    document.getElementById('tipoFilter').addEventListener('change', cargarModelos);  // Filtro por tipo de equipo
    document.getElementById('marcaFilter').addEventListener('change', cargarModelos);  // Filtro por marca
    document.getElementById('modeloFilter').addEventListener('change', cargarModelos);  // Filtro por modelo
    
    // Cambio de tamaño de página: cuando el usuario cambia cuántos registros ver por página
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);  // Actualizar tamaño de página con el valor seleccionado
        paginaActual = 1;  // Volver a la primera página cuando cambia el tamaño
        cargarModelos();  // Recargar modelos con el nuevo tamaño de página
    });
    
    // Paso 3: Configurar event listeners para ordenamiento por columnas
    // Los headers con clase 'sortable' permiten ordenar la tabla haciendo clic
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const columna = this.getAttribute('data-column');  // Obtener nombre de la columna desde atributo data
            ordenarPor(columna, this);  // Ordenar por la columna seleccionada
        });
    });
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

// Función para cargar modelos de equipos desde el servidor con filtros, ordenamiento y paginación
// Hace una petición AJAX al endpoint de la API para obtener los modelos filtrados y paginados
// Actualiza la tabla, la paginación y las estadísticas con los datos recibidos
function cargarModelos() {
    // Paso 1: Obtener valores de los filtros del formulario
    const search = document.getElementById('searchInput').value;  // Término de búsqueda (puede estar vacío)
    const tipo = document.getElementById('tipoFilter').value;  // ID de tipo de equipo para filtrar (puede estar vacío)
    const marca = document.getElementById('marcaFilter').value;  // ID de marca para filtrar (puede estar vacío)
    const modelo = document.getElementById('modeloFilter').value;  // ID de modelo para filtrar (puede estar vacío)
    
    // Paso 2: Construir parámetros de la petición HTTP
    // URLSearchParams facilita la construcción de query strings
    const params = new URLSearchParams({
        search: search,  // Término de búsqueda
        tipo_equipo_id: tipo,  // ID de tipo de equipo para filtrar
        marca_id: marca,  // ID de marca para filtrar
        modelo_id: modelo,  // ID de modelo para filtrar
        order_by: ordenActual,  // Columna para ordenar (vacío si no hay ordenamiento)
        direction: direccionOrden,  // Dirección del ordenamiento ('asc' o 'desc')
        page: paginaActual,  // Página actual a cargar
        per_page: tamanoPagina  // Cantidad de registros por página
    });
    
    // Paso 3: Realizar petición GET al endpoint de la API
    fetch(`/maquinarias/api/pautas-mantenimiento/?${params}`)
        .then(response => {
            // Validar que la respuesta HTTP sea exitosa
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();  // Convertir respuesta HTTP a JSON
        })
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los datos se cargaron correctamente
                // Paso 4.1: Renderizar la tabla con los modelos recibidos
                renderizarModelos(data.modelos);
                
                // Paso 4.2: Renderizar controles de paginación
                renderizarPaginacion(data);
                
                // Paso 4.3: Actualizar estadísticas (total de modelos, rango mostrado, etc.)
                actualizarEstadisticas(data.total, data);
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar modelos: ' + (data.message || 'Error desconocido'));
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error al cargar modelos:', error);  // Registrar error en consola para debugging
            mostrarError('Error de conexión al cargar modelos: ' + error.message);  // Mostrar mensaje de error al usuario
        });
}

// Función para renderizar la tabla de modelos en el DOM
// Genera las filas de la tabla HTML con los datos de los modelos recibidos
// Incluye validación de datos y manejo de errores para casos de datos inválidos
// Parámetros:
//   modelos: Array de objetos con los datos de los modelos a mostrar
function renderizarModelos(modelos) {
    // Paso 1: Obtener referencia al tbody de la tabla donde se insertarán las filas
    const tbody = document.getElementById('modelosTableBody');
    
    // Paso 2: Validar que modelos sea un array válido
    if (!modelos || !Array.isArray(modelos)) {
        console.error('Error: modelos no es un array válido', modelos);  // Registrar error en consola
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-5">
                    <i class="bi bi-exclamation-triangle fs-1 text-danger"></i>
                    <p class="text-danger mt-2">Error al cargar modelos: datos inválidos</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Si no hay modelos, mostrar mensaje de "sin resultados"
    if (modelos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron modelos de equipo</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 4: Generar HTML para cada modelo usando map() y join()
    // Usar try-catch para manejar errores durante el renderizado
    try {
        tbody.innerHTML = modelos.map(modelo => {
            // Paso 4.1: Validar que el modelo tenga la estructura esperada
            // Cada modelo debe tener modeloEquipo, tipoEquipo y marcaEquipo
            if (!modelo.modeloEquipo || !modelo.tipoEquipo || !modelo.marcaEquipo) {
                console.error('Error: modelo con estructura inválida', modelo);  // Registrar error en consola
                return `
                    <tr>
                        <td colspan="5" class="text-danger">
                            Error: datos del modelo incompletos
                        </td>
                    </tr>
                `;
            }
            
            // Paso 4.2: Generar HTML de la fila con los datos del modelo
            return `
                <tr>
                    <td><strong>${modelo.modeloEquipo.nombre || 'N/A'}</strong></td>
                    <td>
                        <span class="badge bg-secondary">${modelo.tipoEquipo.sigla || 'N/A'}</span>
                        <span class="ms-1">${modelo.tipoEquipo.nombre || 'N/A'}</span>
                    </td>
                    <td>${modelo.marcaEquipo.nombre || 'N/A'}</td>
                    <td class="text-center">
                        <a href="/maquinarias/pautas-mantenimiento/modelo/${modelo.modeloEquipo.modeloEquipo_id}/" 
                           class="btn btn-sm btn-primary" 
                           title="Ver pautas">
                            <i class="bi bi-eye"></i> ${modelo.total_pautas || 0}
                        </a>
                    </td>
                    <td class="text-center">
                        ${window.userPermissions && window.userPermissions.canAdd ? `
                        <a href="/maquinarias/pautas-mantenimiento/crear/?modelo=${modelo.modeloEquipo.modeloEquipo_id}" 
                           class="btn btn-sm btn-success" 
                           title="Nueva pauta para este modelo">
                            <i class="bi bi-plus-circle"></i>
                        </a>
                        ` : `
                        <button class="btn btn-sm btn-success" disabled title="No tiene permiso para crear pautas de mantenimiento">
                            <i class="bi bi-plus-circle"></i>
                        </button>
                        `}
                    </td>
                </tr>
            `;
        }).join('');  // Unir todas las filas en un solo string HTML
    } catch (error) {
        // CASO EXCEPCIÓN: Error durante el renderizado (ej: error de acceso a propiedades)
        console.error('Error al renderizar modelos:', error);  // Registrar error en consola
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-5">
                    <i class="bi bi-exclamation-triangle fs-1 text-danger"></i>
                    <p class="text-danger mt-2">Error al renderizar modelos: ${error.message}</p>
                </td>
            </tr>
        `;
    }
}

// Función para renderizar los controles de paginación
// Genera los botones de navegación de páginas con lógica de "páginas visibles"
// Muestra máximo 5 páginas alrededor de la página actual, con elipsis si hay más páginas
// Parámetros:
//   data: Objeto con datos de paginación (total_pages, etc.)
function renderizarPaginacion(data) {
    // Paso 1: Obtener referencia al contenedor de paginación y calcular total de páginas
    const pagination = document.getElementById('pagination');
    const totalPages = data.total_pages;
    
    // Paso 2: Si hay una página o menos, no mostrar controles de paginación
    if (totalPages <= 1) {
        pagination.innerHTML = '';  // Limpiar contenido
        return;  // Salir de la función
    }
    
    let html = '';  // Variable para acumular el HTML generado
    
    // Paso 3: Generar botón "Anterior"
    // Se deshabilita si estamos en la primera página
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Paso 4: Calcular rango de páginas a mostrar (máximo 5 páginas visibles)
    const maxPaginas = 5;  // Cantidad máxima de números de página a mostrar
    let inicio = Math.max(1, paginaActual - Math.floor(maxPaginas / 2));  // Página inicial del rango
    let fin = Math.min(totalPages, inicio + maxPaginas - 1);  // Página final del rango
    
    // Ajustar inicio si el rango es menor al máximo (cuando estamos cerca del final)
    if (fin - inicio < maxPaginas - 1) {
        inicio = Math.max(1, fin - maxPaginas + 1);
    }
    
    // Paso 5: Agregar botón para la primera página si no está en el rango visible
    if (inicio > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a>
            </li>
        `;
        // Agregar elipsis si hay un salto entre la primera página y el rango visible
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Paso 6: Generar botones para las páginas del rango visible
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Paso 7: Agregar botón para la última página si no está en el rango visible
    if (fin < totalPages) {
        // Agregar elipsis si hay un salto entre el rango visible y la última página
        if (fin < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // Paso 8: Generar botón "Siguiente"
    // Se deshabilita si estamos en la última página
    html += `
        <li class="page-item ${paginaActual === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    // Paso 9: Insertar el HTML generado en el contenedor de paginación
    pagination.innerHTML = html;
}

// Función para actualizar las estadísticas mostradas en la página
// Actualiza contadores de total de modelos, rango de registros mostrados, etc.
// Parámetros:
//   total: Número total de modelos que cumplen los filtros aplicados
//   data: Objeto con datos de paginación (page, per_page, etc.)
function actualizarEstadisticas(total, data) {
    // Paso 1: Actualizar total de modelos encontrados
    document.getElementById('totalModelos').textContent = total;
    
    // Paso 2: Calcular rango de registros mostrados en la página actual
    // Primer registro: (página - 1) * registros_por_página + 1
    const inicio = total === 0 ? 0 : ((data.page - 1) * data.per_page) + 1;
    // Último registro: mínimo entre (página * registros_por_página) y total
    const fin = Math.min(data.page * data.per_page, total);
    
    // Paso 3: Actualizar elementos de estadísticas en el DOM
    document.getElementById('registroInicio').textContent = inicio;  // Número del primer registro mostrado
    document.getElementById('registroFin').textContent = fin;  // Número del último registro mostrado
    document.getElementById('totalRegistros').textContent = total;  // Total de registros
}

// Función para cambiar a una página específica de la paginación
// Se ejecuta cuando el usuario hace clic en un número de página o botón de navegación
// Parámetros:
//   pagina: Número de página a la que se quiere navegar
function cambiarPagina(pagina) {
    paginaActual = pagina;  // Actualizar variable global con la nueva página
    cargarModelos();  // Recargar modelos con la nueva página
}

// Función para limpiar todos los filtros y recargar la lista completa
// Se ejecuta cuando el usuario hace clic en el botón de limpiar filtros
function limpiarFiltros() {
    // Limpiar todos los campos de filtro
    document.getElementById('searchInput').value = '';  // Limpiar búsqueda
    document.getElementById('tipoFilter').value = '';  // Limpiar filtro de tipo
    document.getElementById('marcaFilter').value = '';  // Limpiar filtro de marca
    document.getElementById('modeloFilter').value = '';  // Limpiar filtro de modelo
    paginaActual = 1;  // Volver a la primera página
    cargarModelos();  // Recargar modelos sin filtros
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
    
    // Paso 4: Volver a la primera página y recargar modelos con el nuevo ordenamiento
    paginaActual = 1;  // Volver a la primera página
    cargarModelos();  // Recargar modelos con el ordenamiento aplicado
}

// Nota: Las funciones toggle y eliminar de pautas están en ver_pautas_modelo.js
// Este archivo solo maneja la lista de modelos con sus pautas

// Función para mostrar notificaciones temporales al usuario
// Crea alertas de Bootstrap en la esquina superior derecha de la pantalla
// Las notificaciones desaparecen automáticamente después de 3 segundos
// Parámetros:
//   message: Texto del mensaje a mostrar
//   type: Tipo de notificación ('success' para éxito, cualquier otro valor para error)
function showNotification(message, type = 'success') {
    // Paso 1: Obtener o crear el contenedor de mensajes
    // El contenedor se crea una sola vez y se reutiliza para todas las notificaciones
    let container = document.querySelector('.messages-container');
    if (!container) {
        // Si no existe, crear el contenedor con estilos apropiados
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);  // Agregar al body del documento
    }
    
    // Paso 2: Determinar clases CSS e icono según el tipo de notificación
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';  // Clase de Bootstrap para el color
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';  // Icono de Bootstrap Icons
    
    // Paso 3: Crear el elemento de alerta con el mensaje
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;  // Clases de Bootstrap
    alertDiv.setAttribute('role', 'alert');  // Atributo de accesibilidad
    alertDiv.style.marginBottom = '10px';  // Espaciado entre notificaciones
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Paso 4: Agregar la notificación al contenedor
    container.appendChild(alertDiv);
    
    // Paso 5: Configurar eliminación automática después de 3 segundos
    // La notificación desaparece automáticamente para no saturar la interfaz
    setTimeout(() => {
        alertDiv.classList.remove('show');  // Iniciar animación de desvanecimiento
        setTimeout(() => {
            alertDiv.remove();  // Eliminar el elemento del DOM después de la animación
        }, 150);  // Esperar a que termine la animación CSS (150ms)
    }, 3000);  // Mostrar durante 3 segundos
}

// Función auxiliar para mostrar mensajes de éxito
// Es un wrapper que simplifica el uso de showNotification para casos de éxito
// Parámetros:
//   mensaje: Texto del mensaje de éxito a mostrar
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Función auxiliar para mostrar mensajes de error
// Es un wrapper que simplifica el uso de showNotification para casos de error
// Parámetros:
//   mensaje: Texto del mensaje de error a mostrar
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

