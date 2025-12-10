// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado de la página y los datos cargados
let paginaActual = 1;  // Página actual de la paginación
let registrosPorPagina = 10;  // Cantidad de registros a mostrar por página
let equiposDesactivados = [];  // Lista completa de equipos desactivados desde el servidor
let equiposFiltrados = [];  // Lista de equipos después de aplicar filtros
let currentToggle = null;  // Referencia al checkbox que se está activando (para el modal de confirmación)
let originalState = false;  // Estado original del checkbox antes del cambio
let changeConfirmed = false;  // Flag que indica si el cambio fue confirmado

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar todos los equipos desactivados desde el servidor
    // Esta función hace una petición AJAX para obtener la lista completa
    cargarEquiposDesactivados();
    
    // Paso 2: Configurar event listeners para los filtros
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    // Se usa debounce en la búsqueda para evitar demasiadas ejecuciones mientras el usuario escribe
    document.getElementById('searchInput').addEventListener('input', debounce(filtrarEquipos, 300));
    document.getElementById('filtroTipo').addEventListener('change', filtrarEquipos);
    document.getElementById('filtroEmpresa').addEventListener('change', filtrarEquipos);
    
    // Paso 3: Configurar el botón de confirmación del modal de activación
    // Cuando el usuario confirma la activación, se ejecuta esta función
    document.getElementById('btnConfirmarActivar').addEventListener('click', confirmarActivacion);
    
    // Paso 4: Limpiar estado cuando se cierra el modal de confirmación
    // Si el usuario cierra el modal sin confirmar, se revierte el cambio en el checkbox
    document.getElementById('confirmActivarModal').addEventListener('hidden.bs.modal', function() {
        // Si hay un toggle pendiente y no fue confirmado, revertir su estado
        if (currentToggle && !changeConfirmed) {
            currentToggle.checked = originalState;  // Restaurar estado original
        }
        // Limpiar referencias para el próximo uso
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
});

// Función debounce para optimizar búsquedas
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

// Función para cargar equipos desactivados desde el servidor
// Esta función obtiene todos los equipos con estado 'inactivo' desde la API
function cargarEquiposDesactivados() {
    // Paso 1: Construir parámetros de la petición
    // Se solicita estado 'inactivos' y un page_size grande para traer todos los registros
    // La paginación se maneja en el frontend para mejor control
    const params = new URLSearchParams({
        estado: 'inactivos',  // Solo equipos desactivados
        page: 1,  // Primera página
        page_size: 9999  // Traer todos para manejar paginación en frontend
    });
    
    // Paso 2: Realizar petición GET al endpoint de equipos con los parámetros
    fetch(`/maquinarias/api/equipos/?${params}`)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // Paso 3: Guardar los equipos en la variable global
                // Estos equipos se usarán para filtrar localmente sin más peticiones al servidor
                equiposDesactivados = data.equipos;
                
                // Paso 4: Aplicar filtros y renderizar la tabla
                // Esto muestra los equipos en la interfaz
                filtrarEquipos();
            }
        })
        .catch(error => console.error('Error:', error));  // Manejar errores de red o del servidor
}

// Función para filtrar equipos según los criterios de búsqueda y filtros seleccionados
// Esta función aplica filtros locales sobre la lista de equipos desactivados
// Los filtros se combinan con AND (todos deben cumplirse)
function filtrarEquipos() {
    // Paso 1: Obtener valores de los campos de filtro
    // Convertir búsqueda a minúsculas para comparación case-insensitive
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();  // Texto de búsqueda
    const tipoFiltro = document.getElementById('filtroTipo').value;  // Tipo de equipo seleccionado
    const empresaFiltro = document.getElementById('filtroEmpresa').value;  // Empresa seleccionada
    
    // Paso 2: Filtrar la lista de equipos desactivados
    // Se aplican tres filtros: búsqueda de texto, tipo y empresa
    equiposFiltrados = equiposDesactivados.filter(equipo => {
        // Filtro de búsqueda: busca en nombre y código interno
        // Si no hay término de búsqueda, se considera que coincide
        const matchSearch = !searchTerm || 
            equipo.nombreEquipo.toLowerCase().includes(searchTerm) ||  // Buscar en nombre
            equipo.codigoInterno.toLowerCase().includes(searchTerm);  // Buscar en código interno
        
        // Filtro de tipo: debe coincidir exactamente con el tipo seleccionado
        // Si no hay tipo seleccionado, se considera que coincide
        const matchTipo = !tipoFiltro || equipo.tipoEquipo.nombre === tipoFiltro;
        
        // Filtro de empresa: debe coincidir exactamente con la empresa seleccionada
        // Si no hay empresa seleccionada, se considera que coincide
        const matchEmpresa = !empresaFiltro || equipo.empresa.nombre === empresaFiltro;
        
        // Retornar true solo si todos los filtros coinciden (AND lógico)
        return matchSearch && matchTipo && matchEmpresa;
    });
    
    // Paso 3: Resetear a la primera página y renderizar la tabla
    // Al cambiar los filtros, siempre se muestra desde la primera página
    paginaActual = 1;
    renderizarTabla();  // Actualizar la visualización de la tabla
}

// Función para renderizar la tabla de equipos desactivados
// Esta función muestra los equipos de la página actual en la tabla HTML
// Maneja la paginación local y actualiza los contadores de registros
function renderizarTabla() {
    // Paso 1: Obtener referencia al tbody de la tabla y calcular rango de registros a mostrar
    const tbody = document.getElementById('equiposTableBody');  // Contenedor de las filas de la tabla
    const inicio = (paginaActual - 1) * registrosPorPagina;  // Índice del primer registro de la página
    const fin = inicio + registrosPorPagina;  // Índice del último registro de la página (no inclusivo)
    
    // Paso 2: Obtener solo los equipos de la página actual usando slice
    // slice(inicio, fin) extrae una porción del array sin modificar el original
    const equiposPagina = equiposFiltrados.slice(inicio, fin);
    
    // Paso 3: Manejar caso cuando no hay equipos para mostrar
    // Mostrar mensaje positivo indicando que no hay equipos desactivados
    if (equiposPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5">
                    <i class="bi bi-check-circle text-success" style="font-size: 4rem;"></i>
                    <h5 class="mt-3 text-success">¡Excelente!</h5>
                    <p class="text-muted">No hay equipos desactivados en este momento.</p>
                    <p class="text-muted small">Todos los equipos se encuentran activos y disponibles.</p>
                </td>
            </tr>
        `;
        // Actualizar contadores a cero cuando no hay registros
        document.getElementById('totalRegistros').textContent = '0';
        document.getElementById('registroInicio').textContent = '0';
        document.getElementById('registroFin').textContent = '0';
        document.getElementById('totalRegistrosPaginacion').textContent = '0';
        return;  // Salir de la función ya que no hay nada más que hacer
    }
    
    // Paso 4: Generar HTML para cada equipo de la página actual
    // Se usa map() para crear un array de strings HTML y luego join() para unirlos
    tbody.innerHTML = equiposPagina.map(equipo => `
        <tr>
            <td><strong>${equipo.nombreEquipo}</strong></td>
            <td>
                <span class="badge bg-secondary">${equipo.tipoEquipo.sigla}</span>
                <span class="ms-1">${equipo.tipoEquipo.nombre}</span>
            </td>
            <td>${equipo.marcaEquipo.nombre}</td>
            <td>${equipo.modeloEquipo.nombre}</td>
            <td>${equipo.empresa.nombre}</td>
            <td class="text-center">
                <div class="form-check form-switch d-inline-block">
                    <input class="form-check-input" type="checkbox" 
                           style="cursor: pointer;"
                           data-equipo-id="${equipo.equipo_id}"
                           data-nombre-equipo="${equipo.nombreEquipo.replace(/'/g, "\\'")}"
                           ${equipo.activo ? 'checked' : ''} 
                           onchange="toggleEstadoEquipo(this)"
                           title="Activar equipo">
                </div>
            </td>
        </tr>
    `).join('');  // Unir todos los strings HTML en uno solo
    
    // Paso 5: Actualizar contadores de registros en la interfaz
    // Estos contadores muestran información sobre la paginación al usuario
    document.getElementById('totalRegistros').textContent = equiposFiltrados.length;  // Total de equipos filtrados
    document.getElementById('registroInicio').textContent = equiposFiltrados.length > 0 ? inicio + 1 : 0;  // Primer registro visible (1-indexed)
    document.getElementById('registroFin').textContent = Math.min(fin, equiposFiltrados.length);  // Último registro visible
    document.getElementById('totalRegistrosPaginacion').textContent = equiposFiltrados.length;  // Total para paginación
    
    // Paso 6: Renderizar controles de paginación
    // Esto actualiza los botones de página anterior/siguiente y números de página
    renderizarPaginacion();
}

// Renderizar paginación
function renderizarPaginacion() {
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    const paginacionDiv = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacionDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActual - 2 && i <= paginaActual + 2)) {
            html += `
                <li class="page-item ${i === paginaActual ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActual - 3 || i === paginaActual + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginacionDiv.innerHTML = html;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    renderizarTabla();
}

// Cambiar registros por página
function cambiarRegistrosPorPagina() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1;
    renderizarTabla();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filtroTipo').value = '';
    document.getElementById('filtroEmpresa').value = '';
    filtrarEquipos();
}

// ============================================================================
// TOGGLE DE ESTADO (ACTIVAR EQUIPO)
// ============================================================================

// Función que se ejecuta cuando el usuario intenta activar un equipo desactivado
// Muestra un modal de confirmación antes de realizar el cambio
// Parámetros:
//   checkbox: elemento checkbox que fue cambiado
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
    // Esto muestra al usuario qué equipo está intentando activar
    const nombreEquipo = checkbox.dataset.nombreEquipo;  // Obtener nombre desde atributo data
    const nombreElement = document.getElementById('equipoActivarNombre');
    if (nombreElement) {
        nombreElement.textContent = nombreEquipo;  // Mostrar nombre en el modal
    }
    
    // Paso 4: Preparar el modal de confirmación
    // Cerrar cualquier instancia existente del modal para evitar conflictos
    const modalElement = document.getElementById('confirmActivarModal');
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
    // El usuario debe confirmar antes de que se active el equipo
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Función que se ejecuta cuando el usuario confirma la activación del equipo
// Realiza la petición al servidor para cambiar el estado del equipo
function confirmarActivacion() {
    // Paso 1: Validar que hay un toggle pendiente
    // Si no hay checkbox seleccionado, salir sin hacer nada
    if (!currentToggle) return;
    
    // Paso 2: Obtener el ID del equipo desde el atributo data del checkbox
    // Este ID se usa para identificar qué equipo activar en el servidor
    const equipoId = parseInt(currentToggle.dataset.equipoId);
    
    // Paso 3: Realizar petición POST al servidor para cambiar el estado
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
            // CASO ÉXITO: El equipo fue activado correctamente
            // Paso 4.1: Marcar que el cambio fue confirmado
            // Esto previene que se revierta el cambio cuando se cierre el modal
            changeConfirmed = true;
            
            // Paso 4.2: Cerrar el modal de confirmación
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
            confirmModal.hide();
            
            // Paso 4.3: Mostrar notificación de éxito al usuario
            showNotification('Equipo activado correctamente', 'success');
            
            // Paso 4.4: Recargar la lista de equipos desactivados
            // El equipo activado ya no debería aparecer en esta lista
            cargarEquiposDesactivados();
        } else {
            // CASO ERROR: El servidor retornó un error
            // Paso 5.1: Cerrar el modal
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
            confirmModal.hide();
            
            // Paso 5.2: Mostrar mensaje de error al usuario
            alert('Error: ' + (data.message || 'Error al cambiar el estado del equipo'));
            
            // Paso 5.3: Revertir el checkbox a su estado original
            currentToggle.checked = originalState;
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        // Paso 6.1: Registrar error en consola para debugging
        console.error('Error:', error);
        
        // Paso 6.2: Cerrar el modal
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmActivarModal'));
        confirmModal.hide();
        
        // Paso 6.3: Mostrar mensaje genérico de error
        alert('Error al cambiar el estado del equipo');
        
        // Paso 6.4: Revertir el checkbox a su estado original
        currentToggle.checked = originalState;
    });
}

// Sistema de notificaciones
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

