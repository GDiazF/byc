// ============================================================================
// DOCUMENTACIÓN DE MAQUINARIAS
// ============================================================================
// Este archivo maneja la gestión de documentación de equipos (subir, ver, eliminar).
// Incluye funcionalidades para mostrar/ocultar campos según el tipo de documento,
// validación de archivos PDF, gestión de fechas de vencimiento, y visualización de historial.

// Variables globales para el estado de la aplicación
let documentoAEliminar = null;  // ID del documento pendiente de eliminación (se usa en el modal de confirmación)
let tiposDocumentos = [];  // Array para almacenar tipos de documentos (actualmente no se usa, pero se mantiene para futuras mejoras)

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Inicializar todos los event listeners de los elementos del formulario
    inicializarEventos();
    
    // Paso 2: Cargar la lista de documentos desde el servidor
    cargarDocumentos();
    
    // Paso 3: Verificar si hay un tipo de documento seleccionado inicialmente
    // Esto ajusta la visibilidad del campo de fecha de vencimiento según el tipo
    actualizarFormularioSegunTipo();
});

// Función para inicializar todos los event listeners de la página
// Configura los listeners para los elementos interactivos del formulario y botones
function inicializarEventos() {
    // Paso 1: Configurar listener para el select de tipo de documento
    // Cuando cambia el tipo, se actualiza dinámicamente el formulario (muestra/oculta fecha de vencimiento)
    const tipoDocumentoSelect = document.getElementById('tipoDocumentoSelect');
    if (tipoDocumentoSelect) {
        tipoDocumentoSelect.addEventListener('change', function() {
            actualizarFormularioSegunTipo();  // Actualizar formulario según el tipo seleccionado
        });
    }
    
    // Paso 2: Configurar listener para el formulario de subir documento
    // Previene el envío por defecto y ejecuta la función personalizada de subida
    const formSubirDocumento = document.getElementById('formSubirDocumento');
    if (formSubirDocumento) {
        formSubirDocumento.addEventListener('submit', function(e) {
            e.preventDefault();  // Prevenir envío por defecto del formulario
            subirDocumento();  // Ejecutar función personalizada de subida
        });
    }
    
    // Paso 3: Configurar listener para el botón de limpiar formulario
    // Resetea todos los campos del formulario a sus valores iniciales
    const btnLimpiarForm = document.getElementById('btnLimpiarForm');
    if (btnLimpiarForm) {
        btnLimpiarForm.addEventListener('click', function() {
            limpiarFormulario();  // Limpiar y resetear el formulario
        });
    }
    
    // Paso 4: Configurar listener para el botón de toggle historial
    // Muestra u oculta la sección de historial de documentos
    const btnToggleHistorial = document.getElementById('btnToggleHistorial');
    if (btnToggleHistorial) {
        btnToggleHistorial.addEventListener('click', function() {
            toggleHistorial();  // Alternar visibilidad del historial
        });
    }
    
    // Paso 5: Configurar listener para el botón de confirmar eliminación
    // Ejecuta la eliminación del documento cuando el usuario confirma en el modal
    const btnConfirmarEliminacion = document.getElementById('btnConfirmarEliminacion');
    if (btnConfirmarEliminacion) {
        btnConfirmarEliminacion.addEventListener('click', function() {
            if (documentoAEliminar) {
                eliminarDocumento(documentoAEliminar);  // Eliminar documento si hay uno pendiente
            }
        });
    }
}

// ============================================================================
// FUNCIONES PARA FORMULARIO DINÁMICO
// ============================================================================

// Función para actualizar el formulario dinámicamente según el tipo de documento seleccionado
// Muestra u oculta el campo de fecha de vencimiento según si el tipo de documento lo requiere
// Algunos tipos de documentos (como "Revisión Técnica") siempre requieren fecha de vencimiento
function actualizarFormularioSegunTipo() {
    // Paso 1: Obtener referencias a los elementos del formulario
    const tipoSelect = document.getElementById('tipoDocumentoSelect');  // Select de tipo de documento
    const fechaVencimientoGroup = document.getElementById('fechaVencimientoGroup');  // Grupo del campo de fecha
    const fechaVencimientoInput = document.getElementById('fechaVencimientoInput');  // Input de fecha de vencimiento
    
    // Validar que los elementos existan antes de continuar
    if (!tipoSelect || !fechaVencimientoGroup) return;
    
    // Paso 2: Obtener la opción seleccionada del select
    const selectedIndex = tipoSelect.selectedIndex;
    
    // Paso 2.1: Validar que el índice seleccionado sea válido
    if (selectedIndex < 0 || selectedIndex >= tipoSelect.options.length) {
        // Si no hay opción seleccionada válida, ocultar el campo de fecha
        fechaVencimientoGroup.classList.remove('show');
        fechaVencimientoGroup.style.display = 'none';
        if (fechaVencimientoInput) {
            fechaVencimientoInput.removeAttribute('required');  // Quitar requerimiento
            fechaVencimientoInput.value = '';  // Limpiar valor
        }
        return;  // Salir de la función
    }
    
    // Paso 2.2: Obtener la opción seleccionada y validar que tenga valor
    const selectedOption = tipoSelect.options[selectedIndex];
    if (!selectedOption || !selectedOption.value) {
        // Si no hay valor en la opción seleccionada, ocultar el campo de fecha
        fechaVencimientoGroup.classList.remove('show');
        fechaVencimientoGroup.style.display = 'none';
        if (fechaVencimientoInput) {
            fechaVencimientoInput.removeAttribute('required');  // Quitar requerimiento
            fechaVencimientoInput.value = '';  // Limpiar valor
        }
        return;  // Salir de la función
    }
    
    // Paso 3: Obtener información del tipo de documento seleccionado
    const tipoNombre = selectedOption.textContent.trim().toLowerCase();  // Nombre del tipo en minúsculas
    const requiereFecha = selectedOption.getAttribute('data-requiere-fecha') === 'true';  // Atributo data que indica si requiere fecha
    
    // Paso 4: Verificar si es "Revisión Técnica" (siempre requiere fecha de vencimiento)
    // Normalizar el nombre removiendo acentos y espacios extras para comparación más flexible
    const nombreNormalizado = tipoNombre
        .normalize('NFD')  // Normalizar a Forma de Descomposición Canónica
        .replace(/[\u0300-\u036f]/g, '')  // Remover acentos (marcas diacríticas)
        .replace(/\s+/g, ' ')  // Normalizar espacios múltiples a uno solo
        .trim();  // Eliminar espacios al inicio y final
    
    // Comparación más flexible para "Revisión Técnica" (con o sin acentos)
    const esRevisionTecnica = nombreNormalizado.includes('revision') && nombreNormalizado.includes('tecnica') ||
                              tipoNombre.includes('revisión') && tipoNombre.includes('técnica') ||
                              tipoNombre.includes('revision') && tipoNombre.includes('tecnica');
    
    // Debug temporal - remover después de verificar
    console.log('Tipo seleccionado:', tipoNombre, 'Requiere fecha:', requiereFecha, 'Es revisión técnica:', esRevisionTecnica);
    
    // Paso 5: Mostrar u ocultar el campo de fecha según si requiere fecha
    if (requiereFecha || esRevisionTecnica) {
        // CASO: El tipo requiere fecha de vencimiento -> Mostrar campo y hacerlo requerido
        fechaVencimientoGroup.classList.add('show');  // Agregar clase para animación
        fechaVencimientoGroup.style.display = 'block';  // Mostrar el campo
        if (fechaVencimientoInput) {
            fechaVencimientoInput.setAttribute('required', 'required');  // Hacer el campo requerido
            fechaVencimientoInput.classList.remove('is-invalid');  // Remover clase de error si existe
        }
    } else {
        // CASO: El tipo NO requiere fecha de vencimiento -> Ocultar campo y quitar requerimiento
        fechaVencimientoGroup.classList.remove('show');  // Remover clase para animación
        fechaVencimientoGroup.style.display = 'none';  // Ocultar el campo
        if (fechaVencimientoInput) {
            fechaVencimientoInput.removeAttribute('required');  // Quitar requerimiento
            fechaVencimientoInput.value = '';  // Limpiar valor
            fechaVencimientoInput.classList.remove('is-invalid');  // Remover clase de error si existe
        }
    }
}

// Función para limpiar y resetear el formulario de subir documento
// Restablece todos los campos a sus valores iniciales y actualiza la visibilidad de campos dinámicos
function limpiarFormulario() {
    const form = document.getElementById('formSubirDocumento');
    if (form) {
        form.reset();  // Resetear todos los campos del formulario a sus valores iniciales
        actualizarFormularioSegunTipo();  // Actualizar visibilidad de campos según el tipo seleccionado (puede estar vacío después del reset)
    }
}

// ============================================================================
// FUNCIONES PARA CARGAR DOCUMENTOS
// ============================================================================

// Función para cargar la lista de documentos desde el servidor
// Hace una petición AJAX al endpoint de la API para obtener todos los documentos del equipo
// Actualiza la tabla con los documentos recibidos
function cargarDocumentos() {
    // Paso 1: Obtener referencia al tbody de la tabla donde se mostrarán los documentos
    const tbody = document.getElementById('documentosTbody');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Realizar petición GET al endpoint de la API
    // window.DOCUMENTOS_URL se define en el template HTML con la URL del endpoint
    fetch(window.DOCUMENTOS_URL)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los documentos se cargaron correctamente
                renderizarDocumentos(data.documentos);  // Renderizar la tabla con los documentos
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar documentos: ' + (data.error || 'Error desconocido'));  // Mostrar mensaje de error
                tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Error al cargar documentos</td></tr>';  // Mostrar mensaje en la tabla
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error al cargar documentos');  // Mostrar mensaje genérico de error
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Error al cargar documentos</td></tr>';  // Mostrar mensaje en la tabla
        });
}

// Función para renderizar la tabla de documentos en el DOM
// Genera las filas de la tabla HTML con los datos de los documentos recibidos
// Incluye badges de estado, fechas formateadas y botones de acción según permisos
// Parámetros:
//   documentos: Array de objetos con los datos de los documentos a mostrar
function renderizarDocumentos(documentos) {
    // Paso 1: Obtener referencia al tbody de la tabla donde se insertarán las filas
    const tbody = document.getElementById('documentosTbody');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Si no hay documentos, mostrar mensaje de "sin resultados"
    if (documentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 text-muted">
                    <i class="bi bi-folder-x fs-1"></i>
                    <p class="mt-2">No hay documentos registrados</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para cada documento
    let html = '';
    documentos.forEach(doc => {
        // Paso 3.1: Obtener badge de estado según el estado y días restantes del documento
        const estadoBadge = obtenerBadgeEstado(doc.estado, doc.dias_restantes);
        
        // Paso 3.2: Formatear fecha de vencimiento (o mostrar N/A si no tiene)
        const fechaVencimiento = doc.fecha_vencimiento 
            ? formatearFechaChilena(doc.fecha_vencimiento)  // Formatear en formato DD/MM/YYYY
            : '<span class="text-muted">N/A</span>';  // Mostrar N/A si no tiene fecha
        
        // Paso 3.3: Formatear fecha de subida
        const fechaSubida = formatearFechaChilena(doc.fecha_subida);
        
        // Paso 3.4: Generar HTML de la fila con los datos del documento
        html += `
            <tr>
                <td>${escapeHtml(doc.tipo_documento_nombre)}</td>
                <td>${fechaVencimiento}</td>
                <td class="text-center">${estadoBadge}</td>
                <td>${fechaSubida}</td>
                <td class="text-center">
                    ${doc.archivo_url ? `
                        <a href="${doc.archivo_url}" target="_blank" class="btn btn-sm btn-primary me-1" title="Ver documento">
                            <i class="bi bi-eye"></i>
                        </a>
                    ` : ''}
                    ${window.userPermissions && window.userPermissions.canEliminar ? `
                    <button class="btn btn-sm btn-danger" onclick="mostrarModalEliminacion(${doc.id})" title="Eliminar documento">
                        <i class="bi bi-trash"></i>
                    </button>
                    ` : ''}
                </td>
            </tr>
        `;
    });
    
    // Paso 4: Insertar el HTML generado en el tbody de la tabla
    tbody.innerHTML = html;
}

// Función helper para obtener el badge de estado de un documento
// Genera un badge HTML con color y texto según el estado y días restantes del documento
// Parámetros:
//   estado: Estado del documento ('vencido', 'por_vencer', 'vigente')
//   diasRestantes: Cantidad de días restantes hasta el vencimiento (null si no aplica)
// Retorna:
//   String con el HTML del badge de estado
function obtenerBadgeEstado(estado, diasRestantes) {
    // Paso 1: Si no hay días restantes (null o undefined) y no es 0, mostrar badge genérico "Vigente"
    // Esto ocurre cuando el documento no tiene fecha de vencimiento
    if (!diasRestantes && diasRestantes !== 0) {
        return '<span class="badge bg-success estado-badge">Vigente</span>';
    }
    
    // Paso 2: Generar badge según el estado del documento
    if (estado === 'vencido') {
        // CASO: Documento vencido -> Badge rojo
        return `<span class="badge bg-danger estado-badge">Vencido</span>`;
    } else if (estado === 'por_vencer') {
        // CASO: Documento por vencer -> Badge amarillo con días restantes
        return `<span class="badge bg-warning text-dark estado-badge">Por vencer (${diasRestantes}d)</span>`;
    } else {
        // CASO: Documento vigente -> Badge verde con días restantes
        return `<span class="badge bg-success estado-badge">Vigente (${diasRestantes}d)</span>`;
    }
}

// ============================================================================
// FUNCIONES PARA SUBIR DOCUMENTO
// ============================================================================

// Función principal para subir un documento al servidor
// Valida los datos del formulario, prepara el FormData y lo envía mediante AJAX
// Muestra feedback al usuario durante y después del proceso de subida
function subirDocumento() {
    // Paso 1: Obtener referencia al formulario
    const form = document.getElementById('formSubirDocumento');
    if (!form) return;  // Si no existe el formulario, salir sin hacer nada
    
    // Paso 2: Crear FormData con los datos del formulario (incluye archivo)
    const formData = new FormData(form);
    const tipoDocumentoId = formData.get('tipo_documento_id');  // ID del tipo de documento
    const archivo = formData.get('archivo');  // Archivo seleccionado
    const fechaVencimiento = formData.get('fecha_vencimiento');  // Fecha de vencimiento (opcional)
    
    // Paso 3: Validar campos requeridos
    if (!tipoDocumentoId || !archivo) {
        mostrarError('Por favor complete todos los campos requeridos');
        return;  // Detener ejecución si faltan campos requeridos
    }
    
    // Paso 4: Validar que el archivo sea PDF
    // Solo se aceptan archivos con extensión .pdf
    if (!archivo.name.toLowerCase().endsWith('.pdf')) {
        mostrarError('Solo se aceptan archivos PDF');
        return;  // Detener ejecución si el archivo no es PDF
    }
    
    // Paso 5: Validar que "Revisión Técnica" tenga fecha de vencimiento
    // Este tipo de documento siempre requiere fecha de vencimiento
    const tipoSelect = document.getElementById('tipoDocumentoSelect');
    if (tipoSelect) {
        const selectedOption = tipoSelect.options[tipoSelect.selectedIndex];
        const tipoNombre = selectedOption.textContent.trim().toLowerCase();
        const esRevisionTecnica = tipoNombre.includes('revisión técnica') || tipoNombre.includes('revision tecnica');
        
        if (esRevisionTecnica && !fechaVencimiento) {
            // CASO ERROR: Revisión Técnica sin fecha de vencimiento
            mostrarError('El documento "Revisión Técnica" requiere una fecha de vencimiento');
            const fechaVencimientoInput = document.getElementById('fechaVencimientoInput');
            if (fechaVencimientoInput) {
                fechaVencimientoInput.focus();  // Enfocar el campo de fecha
                fechaVencimientoInput.classList.add('is-invalid');  // Marcar como inválido visualmente
            }
            return;  // Detener ejecución
        }
    }
    
    // Paso 6: Deshabilitar botón de envío y mostrar estado de carga
    // Esto evita múltiples envíos y proporciona feedback visual al usuario
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;  // Guardar texto original del botón
    submitBtn.disabled = true;  // Deshabilitar botón
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Subiendo...';  // Cambiar texto a "Subiendo..."
    
    // Paso 7: Enviar datos al servidor mediante petición AJAX
    // window.SUBIR_DOCUMENTO_URL se define en el template HTML con la URL del endpoint
    fetch(window.SUBIR_DOCUMENTO_URL, {
        method: 'POST',  // Método HTTP POST para crear/actualizar
        body: formData,  // FormData incluye archivo y otros campos
        headers: {
            'X-CSRFToken': getCookie('csrftoken')  // Token CSRF de Django para seguridad
        }
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: El documento fue subido correctamente
            mostrarExito(data.message || 'Documento subido correctamente');  // Mostrar mensaje de éxito
            limpiarFormulario();  // Limpiar formulario para permitir subir otro documento
            cargarDocumentos();  // Recargar lista de documentos para mostrar el nuevo
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarError(data.error || 'Error al subir documento');  // Mostrar mensaje de error
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al subir documento');  // Mostrar mensaje genérico de error
    })
    .finally(() => {
        // Paso 8: Restaurar estado del botón (siempre se ejecuta, éxito o error)
        submitBtn.disabled = false;  // Habilitar botón nuevamente
        submitBtn.innerHTML = originalText;  // Restaurar texto original del botón
    });
}

// ============================================================================
// FUNCIONES PARA ELIMINAR DOCUMENTO
// ============================================================================

// Función para mostrar el modal de confirmación de eliminación
// Guarda el ID del documento a eliminar y muestra el modal de Bootstrap
// Parámetros:
//   documentoId: ID del documento a eliminar
function mostrarModalEliminacion(documentoId) {
    // Paso 1: Guardar el ID del documento en variable global para usar en la confirmación
    documentoAEliminar = documentoId;
    
    // Paso 2: Crear instancia del modal de Bootstrap y mostrarlo
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminacion'));
    modal.show();
}

// Función para confirmar y ejecutar la eliminación del documento
// Se ejecuta cuando el usuario confirma la eliminación en el modal
// Realiza la petición DELETE al servidor para eliminar el documento
// Parámetros:
//   documentoId: ID del documento a eliminar
function eliminarDocumento(documentoId) {
    // Paso 1: Validar que hay un ID de documento
    if (!documentoId) return;  // Si no hay ID, salir sin hacer nada
    
    // Paso 2: Construir URL del endpoint de eliminación
    // window.ELIMINAR_DOCUMENTO_URL contiene '0' como placeholder que se reemplaza con el ID real
    const url = window.ELIMINAR_DOCUMENTO_URL.replace('0', documentoId);
    
    // Paso 3: Realizar petición DELETE al servidor para eliminar el documento
    fetch(url, {
        method: 'DELETE',  // Método HTTP DELETE para eliminar recursos
        headers: {
            'X-CSRFToken': getCookie('csrftoken')  // Token CSRF de Django para seguridad
        }
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        // Paso 4: Cerrar el modal de confirmación
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarEliminacion'));
        if (modal) modal.hide();
        
        if (data.success) {
            // CASO ÉXITO: El documento fue eliminado correctamente
            mostrarExito(data.message || 'Documento eliminado correctamente');  // Mostrar mensaje de éxito
            cargarDocumentos();  // Recargar lista de documentos para reflejar la eliminación
            
            // Si el historial está visible, recargarlo también para mantener consistencia
            const historialContainer = document.getElementById('historialContainer');
            if (historialContainer && historialContainer.style.display !== 'none') {
                cargarHistorial();  // Recargar historial si está visible
            }
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarError(data.error || 'Error al eliminar documento');  // Mostrar mensaje de error
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al eliminar documento');  // Mostrar mensaje genérico de error
    })
    .finally(() => {
        // Paso 5: Limpiar variable global (siempre se ejecuta, éxito o error)
        documentoAEliminar = null;  // Limpiar ID guardado
    });
}

// ============================================================================
// FUNCIONES PARA HISTORIAL
// ============================================================================

// Función para alternar la visibilidad de la sección de historial
// Muestra u oculta el contenedor del historial y actualiza el texto del botón
// Si se muestra, carga automáticamente el historial desde el servidor
function toggleHistorial() {
    // Paso 1: Obtener referencias a los elementos del historial
    const container = document.getElementById('historialContainer');  // Contenedor del historial
    const btn = document.getElementById('btnToggleHistorial');  // Botón de toggle
    
    // Validar que los elementos existan
    if (!container || !btn) return;
    
    // Paso 2: Alternar visibilidad según el estado actual
    if (container.style.display === 'none') {
        // CASO: Historial oculto -> Mostrarlo
        container.style.display = 'block';  // Mostrar contenedor
        btn.innerHTML = '<i class="bi bi-chevron-up me-1"></i>Ocultar Historial';  // Cambiar texto del botón
        cargarHistorial();  // Cargar historial desde el servidor
    } else {
        // CASO: Historial visible -> Ocultarlo
        container.style.display = 'none';  // Ocultar contenedor
        btn.innerHTML = '<i class="bi bi-chevron-down me-1"></i>Mostrar Historial';  // Cambiar texto del botón
    }
}

// Función para cargar el historial de documentos desde el servidor
// Hace una petición AJAX al endpoint de la API para obtener el historial
// Actualiza la tabla con los documentos históricos recibidos
function cargarHistorial() {
    // Paso 1: Obtener referencia al tbody de la tabla del historial
    const tbody = document.getElementById('historialTbody');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Realizar petición GET al endpoint de la API
    // window.HISTORIAL_URL se define en el template HTML con la URL del endpoint
    fetch(window.HISTORIAL_URL)
        .then(response => response.json())  // Convertir respuesta HTTP a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: El historial se cargó correctamente
                renderizarHistorial(data.historial);  // Renderizar la tabla con el historial
            } else {
                // CASO ERROR: El servidor retornó un error
                mostrarError('Error al cargar historial: ' + (data.error || 'Error desconocido'));  // Mostrar mensaje de error
                tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Error al cargar historial</td></tr>';  // Mostrar mensaje en la tabla
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            console.error('Error:', error);  // Registrar error en consola para debugging
            mostrarError('Error al cargar historial');  // Mostrar mensaje genérico de error
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Error al cargar historial</td></tr>';  // Mostrar mensaje en la tabla
        });
}

// Función para renderizar la tabla del historial de documentos en el DOM
// Genera las filas de la tabla HTML con los datos del historial recibido
// Muestra información sobre documentos reemplazados (fecha original, fecha de reemplazo, etc.)
// Parámetros:
//   historial: Array de objetos con los datos del historial de documentos a mostrar
function renderizarHistorial(historial) {
    // Paso 1: Obtener referencia al tbody de la tabla del historial
    const tbody = document.getElementById('historialTbody');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 2: Si no hay documentos en el historial, mostrar mensaje de "sin resultados"
    if (historial.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 text-muted">
                    <i class="bi bi-folder-x fs-1"></i>
                    <p class="mt-2">No hay documentos en el historial</p>
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para cada documento del historial
    let html = '';
    historial.forEach(item => {
        // Paso 3.1: Formatear fechas (o mostrar N/A si no tienen)
        const fechaVencimiento = item.fecha_vencimiento 
            ? formatearFechaChilena(item.fecha_vencimiento)  // Formatear en formato DD/MM/YYYY
            : '<span class="text-muted">N/A</span>';  // Mostrar N/A si no tiene fecha
        
        const fechaSubidaOriginal = item.fecha_subida_original 
            ? formatearFechaChilena(item.fecha_subida_original)  // Fecha de subida original del documento reemplazado
            : '<span class="text-muted">N/A</span>';  // Mostrar N/A si no tiene fecha
        
        const fechaReemplazo = formatearFechaChilena(item.fecha_reemplazo);  // Fecha en que fue reemplazado
        
        // Paso 3.2: Generar HTML de la fila con los datos del documento histórico
        html += `
            <tr>
                <td>${escapeHtml(item.tipo_documento_nombre)}</td>
                <td>${fechaVencimiento}</td>
                <td>${fechaSubidaOriginal}</td>
                <td>${fechaReemplazo}</td>
                <td class="text-center">
                    ${item.archivo_url ? `
                        <a href="${item.archivo_url}" target="_blank" class="btn btn-sm btn-primary" title="Ver documento">
                            <i class="bi bi-eye"></i>
                        </a>
                    ` : ''}
                </td>
            </tr>
        `;
    });
    
    // Paso 4: Insertar el HTML generado en el tbody de la tabla
    tbody.innerHTML = html;
}

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

// Función helper para formatear fechas en formato chileno (DD/MM/YYYY)
// Convierte fechas del formato ISO (YYYY-MM-DD) al formato chileno más legible
// Parámetros:
//   fechaISO: String con la fecha en formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
// Retorna:
//   String con la fecha formateada en formato DD/MM/YYYY, o string vacío si no hay fecha
function formatearFechaChilena(fechaISO) {
    if (!fechaISO) return '';  // Si no hay fecha, retornar string vacío
    
    // Crear objeto Date desde el string ISO
    const fecha = new Date(fechaISO);
    
    // Extraer día, mes y año
    const dia = String(fecha.getDate()).padStart(2, '0');  // Día con cero a la izquierda si es necesario
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');  // Mes (getMonth() es 0-based, por eso +1)
    const año = fecha.getFullYear();  // Año completo
    
    // Retornar fecha formateada en formato DD/MM/YYYY
    return `${dia}/${mes}/${año}`;
}

// Función helper para escapar caracteres HTML especiales
// Previene ataques XSS escapando caracteres que podrían ser interpretados como HTML
// Parámetros:
//   text: String con texto que puede contener caracteres HTML especiales
// Retorna:
//   String con los caracteres HTML escapados (ej: < se convierte en &lt;)
function escapeHtml(text) {
    // Crear un elemento div temporal y asignar el texto como contenido de texto (no HTML)
    // Esto automáticamente escapa los caracteres especiales
    const div = document.createElement('div');
    div.textContent = text;  // textContent escapa automáticamente los caracteres HTML
    return div.innerHTML;  // Retornar el HTML escapado
}

// Función helper para obtener el valor de una cookie por su nombre
// Útil para obtener el token CSRF de Django para las peticiones AJAX
// Parámetros:
//   name: Nombre de la cookie a obtener (ej: 'csrftoken')
// Retorna:
//   String con el valor de la cookie, o null si no existe
function getCookie(name) {
    let cookieValue = null;
    
    // Verificar que existan cookies
    if (document.cookie && document.cookie !== '') {
        // Dividir las cookies por el separador ';'
        const cookies = document.cookie.split(';');
        
        // Buscar la cookie con el nombre especificado
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();  // Eliminar espacios al inicio y final
            
            // Verificar si la cookie comienza con el nombre buscado seguido de '='
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                // Decodificar el valor de la cookie (puede estar codificado con encodeURIComponent)
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;  // Salir del bucle una vez encontrada la cookie
            }
        }
    }
    
    return cookieValue;  // Retornar el valor de la cookie o null si no se encontró
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
    
    // Paso 3: Crear el elemento de alerta con el mensaje (escapado para seguridad)
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;  // Clases de Bootstrap
    alertDiv.setAttribute('role', 'alert');  // Atributo de accesibilidad
    alertDiv.style.marginBottom = '10px';  // Espaciado entre notificaciones
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${escapeHtml(message)}
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

