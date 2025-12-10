// ============================================================================
// LISTA DE SECCIONES DE EQUIPOS
// ============================================================================
// Este archivo maneja la visualización y gestión de secciones de equipos.
// Incluye funcionalidades de búsqueda, paginación, creación, edición y eliminación de secciones.

// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación (empieza en 1)
let tamanoPagina = 10;  // Cantidad de registros a mostrar por página (por defecto 10)
let seccionIdEliminar = null;  // ID de la sección pendiente de eliminación (se usa en el modal de confirmación)

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar secciones al iniciar la página
    // Esta función hace una petición AJAX para obtener la lista de secciones
    cargarSecciones();
    
    // Paso 2: Configurar event listeners para los controles de la página
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    
    // Búsqueda: usar debounce para evitar demasiadas ejecuciones mientras el usuario escribe
    // El debounce espera 500ms después de que el usuario deja de escribir antes de ejecutar la búsqueda
    document.getElementById('searchInput').addEventListener('input', debounce(cargarSecciones, 500));
    
    // Cambio de tamaño de página: cuando el usuario cambia cuántos registros ver por página
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);  // Actualizar tamaño de página con el valor seleccionado
        paginaActual = 1;  // Volver a la primera página cuando cambia el tamaño
        cargarSecciones();  // Recargar secciones con el nuevo tamaño de página
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

// Función para cargar secciones desde el servidor con paginación y búsqueda
// Hace una petición AJAX al endpoint de la API para obtener las secciones filtradas y paginadas
// Actualiza la tabla, la paginación y las estadísticas con los datos recibidos
function cargarSecciones() {
    // Paso 1: Obtener el término de búsqueda del campo de búsqueda
    const search = document.getElementById('searchInput').value;
    
    // Paso 2: Construir parámetros de la petición HTTP
    // URLSearchParams facilita la construcción de query strings
    const params = new URLSearchParams({
        search: search,  // Término de búsqueda (puede estar vacío)
        page: paginaActual,  // Página actual a cargar
        per_page: tamanoPagina  // Cantidad de registros por página
    });
    
    // Paso 3: Realizar petición GET al endpoint de la API
    fetch(`/maquinarias/api/secciones/?${params}`)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los datos se cargaron correctamente
                // Paso 4.1: Renderizar la tabla con las secciones recibidas
                renderizarSecciones(data.secciones);
                
                // Paso 4.2: Renderizar controles de paginación
                renderizarPaginacion(data);
                
                // Paso 4.3: Actualizar estadísticas (total de secciones)
                actualizarEstadisticas(data.total);
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar secciones: ' + data.message);
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error de conexión al cargar secciones');  // Mostrar mensaje genérico al usuario
        });
}

// Función para renderizar la tabla de secciones en el DOM
// Genera las filas de la tabla HTML con los datos de las secciones recibidas
// Parámetros:
//   secciones: Array de objetos con los datos de las secciones a mostrar
function renderizarSecciones(secciones) {
    // Paso 1: Obtener referencia al tbody de la tabla donde se insertarán las filas
    const tbody = document.getElementById('seccionesTableBody');
    
    // Paso 2: Si no hay secciones, mostrar mensaje de "sin resultados"
    if (secciones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron secciones</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para cada sección usando map() y join()
    // map() transforma cada sección en una fila HTML, join() une todas las filas en un solo string
    tbody.innerHTML = secciones.map(seccion => `
        <tr>
            <td><strong>${seccion.nombre}</strong></td>
            <td>${seccion.descripcion || '<span class="text-muted">Sin descripción</span>'}</td>
            <td class="text-center">
                <span class="badge bg-info">${seccion.total_tipos_reparacion}</span>
            </td>
            <td class="text-center">
                <div class="btn-group btn-group-sm" role="group">
                    ${window.userPermissions.canChange ? `
                    <button class="btn btn-sm btn-secondary" 
                            onclick="mostrarModalEditar(${seccion.seccion_id})" 
                            title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ` : ''}
                    ${window.userPermissions.canDelete ? `
                    <button class="btn btn-sm btn-danger" 
                            onclick="mostrarModalEliminar(${seccion.seccion_id}, '${seccion.nombre}')" 
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
// Actualiza el contador de total de secciones encontradas
// Parámetros:
//   total: Número total de secciones que cumplen los filtros aplicados
function actualizarEstadisticas(total) {
    document.getElementById('totalSecciones').textContent = total;
}

// Función para cambiar a una página específica de la paginación
// Se ejecuta cuando el usuario hace clic en un número de página o botón de navegación
// Parámetros:
//   pagina: Número de página a la que se quiere navegar
function cambiarPagina(pagina) {
    paginaActual = pagina;  // Actualizar variable global con la nueva página
    cargarSecciones();  // Recargar secciones con la nueva página
}

// Función para limpiar el campo de búsqueda y recargar la lista
// Se ejecuta cuando el usuario hace clic en el botón de limpiar búsqueda
function limpiarBusqueda() {
    document.getElementById('searchInput').value = '';  // Limpiar campo de búsqueda
    paginaActual = 1;  // Volver a la primera página
    cargarSecciones();  // Recargar secciones sin filtro de búsqueda
}

// Función para mostrar el modal de creación de sección
// Limpia los campos del formulario y muestra el modal vacío para crear una nueva sección
// Se ejecuta cuando el usuario hace clic en el botón "Nueva Sección"
function mostrarModalCrear() {
    // Paso 1: Limpiar todos los campos del formulario
    document.getElementById('seccion_id').value = '';  // Limpiar ID (no hay en creación)
    document.getElementById('nombre').value = '';  // Limpiar campo de nombre
    document.getElementById('descripcion').value = '';  // Limpiar campo de descripción
    
    // Paso 2: Actualizar el título del modal para indicar que es creación
    document.getElementById('modalTitulo').textContent = 'Nueva Sección';
    
    // Paso 3: Crear instancia del modal de Bootstrap y mostrarlo
    const modal = new bootstrap.Modal(document.getElementById('modalSeccion'));
    modal.show();
}

// Función para mostrar el modal de edición de sección
// Carga los datos de la sección desde el servidor y los muestra en el formulario
// Parámetros:
//   seccionId: ID de la sección a editar
function mostrarModalEditar(seccionId) {
    // Paso 1: Cargar todas las secciones desde el servidor (con límite alto para encontrar la deseada)
    // Nota: En una implementación más eficiente, se podría usar un endpoint específico para obtener una sección
    fetch(`/maquinarias/api/secciones/?search=&page=1&per_page=1000`)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // Paso 2: Buscar la sección específica en los resultados
                const seccion = data.secciones.find(s => s.seccion_id === seccionId);
                
                if (seccion) {
                    // Paso 3: Rellenar los campos del formulario con los datos de la sección
                    document.getElementById('seccion_id').value = seccion.seccion_id;  // ID de la sección (para identificar en edición)
                    document.getElementById('nombre').value = seccion.nombre;  // Nombre de la sección
                    document.getElementById('descripcion').value = seccion.descripcion || '';  // Descripción (vacío si no tiene)
                    
                    // Paso 4: Actualizar el título del modal para indicar que es edición
                    document.getElementById('modalTitulo').textContent = 'Editar Sección';
                    
                    // Paso 5: Crear instancia del modal de Bootstrap y mostrarlo
                    const modal = new bootstrap.Modal(document.getElementById('modalSeccion'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            // CASO ERROR: Error al cargar datos desde el servidor
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error al cargar datos de la sección');  // Mostrar mensaje de error al usuario
        });
}

// Función para guardar una sección (crear nueva o actualizar existente)
// Valida los datos, los prepara y los envía al servidor mediante AJAX
// Determina automáticamente si es creación o edición basándose en la presencia de seccion_id
function guardarSeccion() {
    // Paso 1: Obtener y limpiar datos del formulario
    const seccionId = document.getElementById('seccion_id').value;  // ID de la sección (vacío en creación)
    const nombre = document.getElementById('nombre').value.trim();  // Nombre de la sección (trim elimina espacios)
    const descripcion = document.getElementById('descripcion').value.trim();  // Descripción (opcional)
    
    // Paso 2: Validar datos requeridos
    // El nombre es obligatorio para crear o editar una sección
    if (!nombre) {
        mostrarError('El nombre es requerido');
        return;  // Detener ejecución si falta el nombre
    }
    
    // Paso 3: Preparar objeto con los datos a enviar al servidor
    const data = {
        seccion_id: seccionId || null,  // ID de la sección (null si es creación, ID si es edición)
        nombre: nombre,  // Nombre de la sección
        descripcion: descripcion  // Descripción (puede estar vacía)
    };
    
    // Paso 4: Enviar datos al servidor mediante petición AJAX
    fetch('/maquinarias/api/secciones/guardar/', {
        method: 'POST',  // Método HTTP POST para crear/actualizar
        headers: {
            'Content-Type': 'application/json',  // Indicar que enviamos JSON
        },
        body: JSON.stringify(data)  // Convertir objeto JavaScript a JSON
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: La sección fue guardada correctamente
            mostrarExito(data.message);  // Mostrar mensaje de éxito
            bootstrap.Modal.getInstance(document.getElementById('modalSeccion')).hide();  // Cerrar el modal
            cargarSecciones();  // Recargar la lista de secciones para mostrar los cambios
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarError(data.message);  // Mostrar mensaje de error del servidor
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al guardar sección');  // Mostrar mensaje genérico de error
    });
}

// Función para mostrar el modal de confirmación de eliminación
// Guarda el ID de la sección a eliminar y muestra el nombre en el modal
// Parámetros:
//   seccionId: ID de la sección a eliminar
//   nombre: Nombre de la sección a eliminar (para mostrar en el modal)
function mostrarModalEliminar(seccionId, nombre) {
    // Paso 1: Guardar el ID de la sección en variable global para usar en la confirmación
    seccionIdEliminar = seccionId;
    
    // Paso 2: Mostrar el nombre de la sección en el modal de confirmación
    document.getElementById('seccionEliminarNombre').textContent = nombre;
    
    // Paso 3: Crear instancia del modal de Bootstrap y mostrarlo
    const modal = new bootstrap.Modal(document.getElementById('confirmEliminarModal'));
    modal.show();
}

// Función para confirmar y ejecutar la eliminación de la sección
// Se ejecuta cuando el usuario confirma la eliminación en el modal
// Realiza la petición DELETE al servidor para eliminar la sección
function confirmarEliminar() {
    // Paso 1: Validar que hay una sección pendiente de eliminación
    if (!seccionIdEliminar) return;  // Si no hay ID guardado, salir sin hacer nada
    
    // Paso 2: Realizar petición DELETE al servidor para eliminar la sección
    fetch(`/maquinarias/api/secciones/${seccionIdEliminar}/eliminar/`, {
        method: 'DELETE'  // Método HTTP DELETE para eliminar recursos
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: La sección fue eliminada correctamente
            mostrarExito(data.message);  // Mostrar mensaje de éxito
            bootstrap.Modal.getInstance(document.getElementById('confirmEliminarModal')).hide();  // Cerrar el modal
            cargarSecciones();  // Recargar la lista de secciones para reflejar la eliminación
        } else {
            // CASO ERROR: El servidor retornó un error (ej: la sección está en uso)
            mostrarError(data.message);  // Mostrar mensaje de error del servidor
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al eliminar sección');  // Mostrar mensaje genérico de error
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

