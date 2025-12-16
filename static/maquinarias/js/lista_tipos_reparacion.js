// ============================================================================
// LISTA DE TIPOS DE REPARACIÓN
// ============================================================================
// Este archivo maneja la visualización y gestión de tipos de reparación de equipos.
// Incluye funcionalidades de búsqueda, filtrado por sección, paginación, creación, edición y eliminación.

// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación (empieza en 1)
let tamanoPagina = 10;  // Cantidad de registros a mostrar por página (por defecto 10)
let tipoIdEliminar = null;  // ID del tipo de reparación pendiente de eliminación (se usa en el modal de confirmación)

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar tipos de reparación al iniciar la página
    // Esta función hace una petición AJAX para obtener la lista de tipos de reparación
    cargarTiposReparacion();
    
    // Paso 2: Configurar event listeners para los controles de la página
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    
    // Búsqueda: usar debounce para evitar demasiadas ejecuciones mientras el usuario escribe
    // El debounce espera 500ms después de que el usuario deja de escribir antes de ejecutar la búsqueda
    document.getElementById('searchInput').addEventListener('input', debounce(cargarTiposReparacion, 500));
    
    // Filtro por sección: cuando el usuario selecciona una sección, filtrar tipos de reparación
    document.getElementById('seccionFilter').addEventListener('change', cargarTiposReparacion);
    
    // Cambio de tamaño de página: cuando el usuario cambia cuántos registros ver por página
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);  // Actualizar tamaño de página con el valor seleccionado
        paginaActual = 1;  // Volver a la primera página cuando cambia el tamaño
        cargarTiposReparacion();  // Recargar tipos de reparación con el nuevo tamaño de página
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

// Función para cargar tipos de reparación desde el servidor con paginación, búsqueda y filtros
// Hace una petición AJAX al endpoint de la API para obtener los tipos filtrados y paginados
// Actualiza la tabla, la paginación y las estadísticas con los datos recibidos
function cargarTiposReparacion() {
    // Paso 1: Obtener valores de los filtros del formulario
    const search = document.getElementById('searchInput').value;  // Término de búsqueda (puede estar vacío)
    const seccionId = document.getElementById('seccionFilter').value;  // ID de sección para filtrar (puede estar vacío)
    
    // Paso 2: Construir parámetros de la petición HTTP
    // URLSearchParams facilita la construcción de query strings
    const params = new URLSearchParams({
        search: search,  // Término de búsqueda
        seccion_id: seccionId,  // ID de sección para filtrar
        page: paginaActual,  // Página actual a cargar
        per_page: tamanoPagina  // Cantidad de registros por página
    });
    
    // Paso 3: Realizar petición GET al endpoint de la API
    fetch(`/maquinarias/api/tipos-reparacion/?${params}`)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los datos se cargaron correctamente
                // Paso 4.1: Renderizar la tabla con los tipos de reparación recibidos
                renderizarTiposReparacion(data.tipos_reparacion);
                
                // Paso 4.2: Renderizar controles de paginación
                renderizarPaginacion(data);
                
                // Paso 4.3: Actualizar estadísticas (total de tipos de reparación)
                actualizarEstadisticas(data.total);
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar tipos de reparación: ' + data.message);
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error de conexión al cargar tipos de reparación');  // Mostrar mensaje genérico al usuario
        });
}

// Función para renderizar la tabla de tipos de reparación en el DOM
// Genera las filas de la tabla HTML con los datos de los tipos recibidos
// Parámetros:
//   tipos: Array de objetos con los datos de los tipos de reparación a mostrar
function renderizarTiposReparacion(tipos) {
    // Paso 1: Obtener referencia al tbody de la tabla donde se insertarán las filas
    const tbody = document.getElementById('tiposTableBody');
    
    // Paso 2: Si no hay tipos de reparación, mostrar mensaje de "sin resultados"
    if (tipos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron tipos de reparación</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para cada tipo de reparación usando map() y join()
    // map() transforma cada tipo en una fila HTML, join() une todas las filas en un solo string
    tbody.innerHTML = tipos.map(tipo => `
        <tr>
            <td><strong>${tipo.nombre}</strong></td>
            <td>
                <span class="badge bg-primary">${tipo.seccion_nombre}</span>
            </td>
            <td>${tipo.descripcion || '<span class="text-muted">Sin descripción</span>'}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${window.userPermissions.canChange ? `
                    <button class="btn btn-sm btn-secondary" 
                            onclick="mostrarModalEditar(${tipo.tipoReparacion_id})" 
                            title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ` : ''}
                    ${window.userPermissions.canDelete ? `
                    <button class="btn btn-sm btn-danger" 
                            onclick="mostrarModalEliminar(${tipo.tipoReparacion_id}, '${tipo.nombre}')" 
                            title="Eliminar">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');  // Unir todas las filas en un solo string HTML
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
// Actualiza el contador de total de tipos de reparación encontrados
// Parámetros:
//   total: Número total de tipos de reparación que cumplen los filtros aplicados
function actualizarEstadisticas(total) {
    document.getElementById('totalTipos').textContent = total;
}

// Función para cambiar a una página específica de la paginación
// Se ejecuta cuando el usuario hace clic en un número de página o botón de navegación
// Parámetros:
//   pagina: Número de página a la que se quiere navegar
function cambiarPagina(pagina) {
    paginaActual = pagina;  // Actualizar variable global con la nueva página
    cargarTiposReparacion();  // Recargar tipos de reparación con la nueva página
}

// Función para limpiar todos los filtros y recargar la lista completa
// Se ejecuta cuando el usuario hace clic en el botón de limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';  // Limpiar campo de búsqueda
    document.getElementById('seccionFilter').value = '';  // Limpiar filtro de sección
    paginaActual = 1;  // Volver a la primera página
    cargarTiposReparacion();  // Recargar tipos de reparación sin filtros
}

// Función para mostrar el modal de creación de tipo de reparación
// Limpia los campos del formulario y muestra el modal vacío para crear un nuevo tipo
// Se ejecuta cuando el usuario hace clic en el botón "Nuevo Tipo de Reparación"
function mostrarModalCrear() {
    // Paso 1: Limpiar todos los campos del formulario
    document.getElementById('tipoReparacion_id').value = '';  // Limpiar ID (no hay en creación)
    document.getElementById('seccion_id').value = '';  // Limpiar campo de sección
    document.getElementById('nombre').value = '';  // Limpiar campo de nombre
    document.getElementById('descripcion').value = '';  // Limpiar campo de descripción
    
    // Paso 2: Actualizar el título del modal para indicar que es creación
    document.getElementById('modalTitulo').textContent = 'Nuevo Tipo de Reparación';
    
    // Paso 3: Crear instancia del modal de Bootstrap y mostrarlo
    const modal = new bootstrap.Modal(document.getElementById('modalTipoReparacion'));
    modal.show();
}

// Función para mostrar el modal de edición de tipo de reparación
// Carga los datos del tipo desde el servidor y los muestra en el formulario
// Parámetros:
//   tipoId: ID del tipo de reparación a editar
function mostrarModalEditar(tipoId) {
    // Paso 1: Cargar todos los tipos de reparación desde el servidor (con límite alto para encontrar el deseado)
    // Nota: En una implementación más eficiente, se podría usar un endpoint específico para obtener un tipo
    fetch(`/maquinarias/api/tipos-reparacion/?search=&seccion_id=&page=1&per_page=1000`)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // Paso 2: Buscar el tipo específico en los resultados
                const tipo = data.tipos_reparacion.find(t => t.tipoReparacion_id === tipoId);
                
                if (tipo) {
                    // Paso 3: Rellenar los campos del formulario con los datos del tipo
                    document.getElementById('tipoReparacion_id').value = tipo.tipoReparacion_id;  // ID del tipo (para identificar en edición)
                    document.getElementById('seccion_id').value = tipo.seccion_id;  // ID de la sección a la que pertenece
                    document.getElementById('nombre').value = tipo.nombre;  // Nombre del tipo
                    document.getElementById('descripcion').value = tipo.descripcion || '';  // Descripción (vacío si no tiene)
                    
                    // Paso 4: Actualizar el título del modal para indicar que es edición
                    document.getElementById('modalTitulo').textContent = 'Editar Tipo de Reparación';
                    
                    // Paso 5: Crear instancia del modal de Bootstrap y mostrarlo
                    const modal = new bootstrap.Modal(document.getElementById('modalTipoReparacion'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            // CASO ERROR: Error al cargar datos desde el servidor
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error al cargar datos del tipo de reparación');  // Mostrar mensaje de error al usuario
        });
}

// Función para guardar un tipo de reparación (crear nuevo o actualizar existente)
// Valida los datos, los prepara y los envía al servidor mediante AJAX
// Determina automáticamente si es creación o edición basándose en la presencia de tipoReparacion_id
function guardarTipoReparacion() {
    // Paso 1: Obtener y limpiar datos del formulario
    const tipoId = document.getElementById('tipoReparacion_id').value;  // ID del tipo (vacío en creación)
    const seccionId = document.getElementById('seccion_id').value;  // ID de la sección a la que pertenece
    const nombre = document.getElementById('nombre').value.trim();  // Nombre del tipo (trim elimina espacios)
    const descripcion = document.getElementById('descripcion').value.trim();  // Descripción (opcional)
    
    // Paso 2: Validar datos requeridos
    // La sección es obligatoria porque cada tipo de reparación debe pertenecer a una sección
    if (!seccionId) {
        mostrarError('La sección es requerida');
        return;  // Detener ejecución si falta la sección
    }
    
    // El nombre es obligatorio para crear o editar un tipo de reparación
    if (!nombre) {
        mostrarError('El nombre es requerido');
        return;  // Detener ejecución si falta el nombre
    }
    
    // Paso 3: Preparar objeto con los datos a enviar al servidor
    const data = {
        tipoReparacion_id: tipoId || null,  // ID del tipo (null si es creación, ID si es edición)
        seccion_id: seccionId,  // ID de la sección a la que pertenece
        nombre: nombre,  // Nombre del tipo de reparación
        descripcion: descripcion  // Descripción (puede estar vacía)
    };
    
    // Paso 4: Enviar datos al servidor mediante petición AJAX
    fetch('/maquinarias/api/tipos-reparacion/guardar/', {
        method: 'POST',  // Método HTTP POST para crear/actualizar
        headers: {
            'Content-Type': 'application/json',  // Indicar que enviamos JSON
        },
        body: JSON.stringify(data)  // Convertir objeto JavaScript a JSON
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: El tipo de reparación fue guardado correctamente
            mostrarExito(data.message);  // Mostrar mensaje de éxito
            bootstrap.Modal.getInstance(document.getElementById('modalTipoReparacion')).hide();  // Cerrar el modal
            cargarTiposReparacion();  // Recargar la lista de tipos para mostrar los cambios
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarError(data.message);  // Mostrar mensaje de error del servidor
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al guardar tipo de reparación');  // Mostrar mensaje genérico de error
    });
}

// Función para mostrar el modal de confirmación de eliminación
// Guarda el ID del tipo a eliminar y muestra el nombre en el modal
// Parámetros:
//   tipoId: ID del tipo de reparación a eliminar
//   nombre: Nombre del tipo de reparación a eliminar (para mostrar en el modal)
function mostrarModalEliminar(tipoId, nombre) {
    // Paso 1: Guardar el ID del tipo en variable global para usar en la confirmación
    tipoIdEliminar = tipoId;
    
    // Paso 2: Mostrar el nombre del tipo en el modal de confirmación
    document.getElementById('tipoEliminarNombre').textContent = nombre;
    
    // Paso 3: Crear instancia del modal de Bootstrap y mostrarlo
    const modal = new bootstrap.Modal(document.getElementById('confirmEliminarModal'));
    modal.show();
}

// Función para confirmar y ejecutar la eliminación del tipo de reparación
// Se ejecuta cuando el usuario confirma la eliminación en el modal
// Realiza la petición DELETE al servidor para eliminar el tipo
function confirmarEliminar() {
    // Paso 1: Validar que hay un tipo pendiente de eliminación
    if (!tipoIdEliminar) return;  // Si no hay ID guardado, salir sin hacer nada
    
    // Paso 2: Realizar petición DELETE al servidor para eliminar el tipo de reparación
    fetch(`/maquinarias/api/tipos-reparacion/${tipoIdEliminar}/eliminar/`, {
        method: 'DELETE'  // Método HTTP DELETE para eliminar recursos
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: El tipo fue eliminado correctamente
            mostrarExito(data.message);  // Mostrar mensaje de éxito
            bootstrap.Modal.getInstance(document.getElementById('confirmEliminarModal')).hide();  // Cerrar el modal
            cargarTiposReparacion();  // Recargar la lista de tipos para reflejar la eliminación
        } else {
            // CASO ERROR: El servidor retornó un error (ej: el tipo está en uso)
            mostrarError(data.message);  // Mostrar mensaje de error del servidor
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al eliminar tipo de reparación');  // Mostrar mensaje genérico de error
    });
}

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

