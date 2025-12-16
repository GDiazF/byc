// ============================================================================
// FORMULARIO DE PAUTA DE MANTENIMIENTO
// ============================================================================
// Este archivo maneja la lógica del formulario para crear y editar pautas de mantenimiento preventivo.
// Incluye filtros en cascada (Tipo -> Marca -> Modelo), gestión de items dinámicos,
// y validación antes de enviar los datos al servidor.

// Variables globales
// Contador para asignar índices únicos a cada item agregado a la pauta
let itemIndex = 0;
// Almacena todos los modelos de equipos disponibles para filtrado en cascada
// Se carga desde las opciones del select en el HTML
let todosModelos = [];

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Obtener referencias a los elementos principales del formulario
    const form = document.getElementById('formPautaMantenimiento');  // Formulario principal
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelo (puede ser hidden en edición)
    const tipoSelect = document.getElementById('tipo_equipo_id');  // Select de tipo de equipo
    const marcaSelect = document.getElementById('marca_equipo_id');  // Select de marca
    
    // Paso 2: Cargar modelos disponibles desde las opciones del select (solo si existe y no es hidden)
    // En modo edición, el modelo puede estar en un campo hidden, así que verificamos que sea un SELECT
    if (modeloSelect && modeloSelect.tagName === 'SELECT') {
        // Extraer datos de cada opción del select y almacenarlos en la variable global
        // Esto permite filtrar marcas y modelos sin hacer peticiones adicionales al servidor
        todosModelos = Array.from(modeloSelect.options).map(option => ({
            value: option.value,  // ID del modelo
            text: option.text,  // Nombre del modelo
            tipo: option.dataset.tipo,  // ID del tipo (desde atributo data-tipo)
            marca: option.dataset.marca  // ID de la marca (desde atributo data-marca)
        }));
    }
    
    // Paso 3: Configurar event listeners para filtros en cascada (solo si los selects existen)
    // Los filtros funcionan así: Tipo -> Marca -> Modelo
    if (tipoSelect && tipoSelect.tagName === 'SELECT') {
        tipoSelect.addEventListener('change', filtrarMarcas);  // Al cambiar tipo, filtrar marcas
    }
    if (marcaSelect && marcaSelect.tagName === 'SELECT') {
        marcaSelect.addEventListener('change', filtrarModelos);  // Al cambiar marca, filtrar modelos
    }
    
    // Paso 4: Configurar event listener para el envío del formulario
    if (form) {
        form.addEventListener('submit', guardarPauta);  // Al enviar, ejecutar función de guardado
    }
    
    // Paso 5: Aplicar filtrado inicial si estamos en modo creación (selects habilitados)
    // Si el tipo ya tiene un valor seleccionado, aplicar los filtros en cascada
    if (tipoSelect && tipoSelect.tagName === 'SELECT' && !tipoSelect.disabled && tipoSelect.value) {
        filtrarMarcas();  // Filtrar marcas según el tipo seleccionado
        setTimeout(() => {
            // Esperar un poco para que el filtro de marcas termine antes de filtrar modelos
            if (marcaSelect && marcaSelect.value) {
                filtrarModelos();  // Filtrar modelos según tipo y marca seleccionados
            }
        }, 100);
    }
    
    // Paso 6: Si estamos en modo edición, cargar los items existentes de la pauta
    // window.esEdicion y window.itemsExistentes se definen en el template HTML
    if (window.esEdicion && window.itemsExistentes) {
        // Agregar cada item existente al formulario con sus datos precargados
        window.itemsExistentes.forEach(item => {
            agregarItem(item.seccion_id, item.tipos_reparacion_ids);  // Agregar item con sección y tipos pre-seleccionados
        });
        // Actualizar disponibilidad de secciones después de cargar todos los items
        // Esto oculta las secciones ya seleccionadas en otros items
        setTimeout(() => {
            actualizarSeccionesDisponibles();
        }, 100);
    }
});

// Función para filtrar las marcas disponibles según el tipo de equipo seleccionado
// Implementa el primer nivel del filtro en cascada: Tipo -> Marca -> Modelo
// Solo muestra las marcas que tienen modelos del tipo seleccionado
function filtrarMarcas() {
    // Paso 1: Obtener referencias a los elementos del formulario
    const tipoId = document.getElementById('tipo_equipo_id').value;  // ID del tipo seleccionado
    const marcaSelect = document.getElementById('marca_equipo_id');  // Select de marcas
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelos
    
    // Paso 2: Si no hay tipo seleccionado, deshabilitar y limpiar selects dependientes
    if (!tipoId) {
        marcaSelect.disabled = true;  // Deshabilitar select de marcas
        marcaSelect.value = '';  // Limpiar selección de marca
        modeloSelect.disabled = true;  // Deshabilitar select de modelos
        modeloSelect.value = '';  // Limpiar selección de modelo
        return;  // Salir de la función
    }
    
    // Paso 3: Obtener marcas únicas que tienen modelos del tipo seleccionado
    // Usar Set para evitar marcas duplicadas
    const marcasDisponibles = new Set();
    todosModelos.forEach(modelo => {
        // Si el modelo pertenece al tipo seleccionado y tiene un valor válido
        if (String(modelo.tipo) === String(tipoId) && modelo.value) {
            marcasDisponibles.add(String(modelo.marca));  // Agregar marca al Set
        }
    });
    
    // Paso 4: Filtrar opciones del select de marcas
    // Mostrar solo las marcas que están en el Set de marcas disponibles
    const marcaOptions = Array.from(marcaSelect.options);
    marcaOptions.forEach(option => {
        if (!option.value) return;  // Ignorar opción vacía (placeholder)
        // Mostrar u ocultar según si la marca está disponible para el tipo seleccionado
        option.style.display = marcasDisponibles.has(String(option.value)) ? '' : 'none';
    });
    
    // Paso 5: Habilitar select de marcas y limpiar selecciones dependientes
    marcaSelect.disabled = false;  // Habilitar para que el usuario pueda seleccionar
    marcaSelect.value = '';  // Limpiar selección previa de marca
    modeloSelect.disabled = true;  // Deshabilitar modelo hasta que se seleccione marca
    modeloSelect.value = '';  // Limpiar selección previa de modelo
}

// Función para filtrar los modelos disponibles según el tipo y marca seleccionados
// Implementa el segundo nivel del filtro en cascada: Tipo -> Marca -> Modelo
// Solo muestra los modelos que pertenecen al tipo y marca seleccionados
function filtrarModelos() {
    // Paso 1: Obtener referencias a los elementos del formulario
    const tipoId = document.getElementById('tipo_equipo_id').value;  // ID del tipo seleccionado
    const marcaId = document.getElementById('marca_equipo_id').value;  // ID de la marca seleccionada
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelos
    
    // Paso 2: Si no hay tipo o marca seleccionados, deshabilitar select de modelos
    if (!tipoId || !marcaId) {
        modeloSelect.disabled = true;  // Deshabilitar select de modelos
        modeloSelect.value = '';  // Limpiar selección de modelo
        return;  // Salir de la función
    }
    
    // Paso 3: Filtrar opciones del select de modelos
    // Mostrar solo los modelos que coinciden con el tipo y marca seleccionados
    const modeloOptions = Array.from(modeloSelect.options);
    modeloOptions.forEach(option => {
        if (!option.value) return;  // Ignorar opción vacía (placeholder)
        // Verificar si el modelo pertenece al tipo y marca seleccionados
        // Los datos vienen de los atributos data-tipo y data-marca de cada opción
        const visible = (String(option.dataset.tipo) === String(tipoId) && String(option.dataset.marca) === String(marcaId));
        option.style.display = visible ? '' : 'none';  // Mostrar u ocultar según coincidencia
    });
    
    // Paso 4: Habilitar select de modelos y limpiar selección previa
    modeloSelect.disabled = false;  // Habilitar para que el usuario pueda seleccionar
    modeloSelect.value = '';  // Limpiar selección previa de modelo
}

// Función para agregar un nuevo item a la pauta de mantenimiento
// Cada item representa una sección del equipo con sus tipos de reparación asociados
// Parámetros:
//   seccionIdInicial: ID de la sección a pre-seleccionar (opcional, para modo edición)
//   tiposIdsIniciales: Array de IDs de tipos de reparación a pre-seleccionar (opcional, para modo edición)
function agregarItem(seccionIdInicial = null, tiposIdsIniciales = []) {
    // Paso 1: Obtener referencias a los elementos del DOM
    const container = document.getElementById('itemsContainer');  // Contenedor donde se agregan los items
    const noItemsMessage = document.getElementById('noItemsMessage');  // Mensaje que se muestra cuando no hay items
    const template = document.getElementById('itemPautaTemplate');  // Template HTML para clonar nuevos items
    
    // Validar que el template existe antes de continuar
    if (!template) return;
    
    // Paso 2: Ocultar mensaje de "no hay items" si existe
    // Este mensaje se muestra cuando la lista de items está vacía
    if (noItemsMessage) {
        noItemsMessage.style.display = 'none';
    }
    
    // Paso 3: Clonar el template HTML para crear un nuevo item
    // cloneNode(true) clona también los elementos hijos del template
    const clone = template.content.cloneNode(true);
    const itemDiv = clone.querySelector('.item-pauta');  // Contenedor principal del item
    
    // Paso 4: Asignar un índice único al nuevo item
    // El índice se usa para identificar y numerar cada item
    itemIndex++;  // Incrementar contador global
    itemDiv.dataset.itemIndex = itemIndex;  // Guardar índice en atributo data
    itemDiv.querySelector('.item-number').textContent = itemIndex;  // Mostrar número en la interfaz
    
    // Paso 5: Agregar el item clonado al DOM
    // Esto hace que el item sea visible en la página
    container.appendChild(clone);
    
    // Paso 6: Si es un item existente (modo edición), pre-seleccionar valores
    // Esto se hace DESPUÉS de agregar al DOM para que los elementos estén disponibles
    if (seccionIdInicial) {
        // Buscar el item recién agregado en el DOM usando su índice
        const itemAgregado = container.querySelector(`[data-item-index="${itemIndex}"]`);
        if (!itemAgregado) return;  // Si no se encuentra, salir
        
        // Pre-seleccionar la sección en el select del item
        const seccionSelect = itemAgregado.querySelector('.seccion-select');
        seccionSelect.value = seccionIdInicial;
        
        // Cargar tipos de reparación para la sección y pre-seleccionar los indicados
        const tiposContainer = itemAgregado.querySelector('.tipos-reparacion-list');
        cargarTiposReparacionParaSeccion(seccionIdInicial, tiposContainer, tiposIdsIniciales);
    }
    
    // Paso 7: Actualizar disponibilidad de secciones en todos los selects
    // Esto oculta las secciones ya seleccionadas en otros items para evitar duplicados
    actualizarSeccionesDisponibles();
}

// Función para actualizar la disponibilidad de secciones en todos los selects de items
// Evita que se seleccione la misma sección en múltiples items de la pauta
// Las secciones ya seleccionadas se ocultan en otros selects, pero permanecen visibles en el select donde están seleccionadas
function actualizarSeccionesDisponibles() {
    // Paso 1: Obtener todas las secciones que ya están seleccionadas en algún item
    // Recorrer todos los selects de sección y recopilar sus valores
    const seccionesSeleccionadas = [];
    document.querySelectorAll('.seccion-select').forEach(select => {
        if (select.value) {
            seccionesSeleccionadas.push(select.value);  // Agregar ID de sección a la lista
        }
    });
    
    // Paso 2: Actualizar cada select de sección individualmente
    // Para cada select, mostrar u ocultar opciones según si están seleccionadas en otros items
    document.querySelectorAll('.seccion-select').forEach(select => {
        const valorActual = select.value;  // Sección seleccionada en este select (si hay)
        
        // Paso 3: Recorrer todas las opciones del select
        Array.from(select.options).forEach(option => {
            if (!option.value) return;  // Ignorar opción vacía (placeholder)
            
            // Paso 4: Determinar si la opción debe estar visible o no
            // Ocultar si la sección está seleccionada en otro select (pero mantener visible si está seleccionada en este)
            if (seccionesSeleccionadas.includes(option.value) && option.value !== valorActual) {
                // CASO: Sección seleccionada en otro item -> Ocultar y deshabilitar
                option.style.display = 'none';  // Ocultar visualmente
                option.disabled = true;  // Deshabilitar para evitar selección
            } else {
                // CASO: Sección disponible o seleccionada en este item -> Mostrar y habilitar
                option.style.display = '';  // Mostrar visualmente
                option.disabled = false;  // Habilitar para permitir selección
            }
        });
    });
}

// Función para eliminar un item de la pauta
// Se ejecuta cuando el usuario hace clic en el botón de eliminar de un item
// Parámetros:
//   button: Elemento botón que disparó la eliminación (se usa para encontrar el item)
function eliminarItem(button) {
    // Paso 1: Encontrar el contenedor del item usando el botón como referencia
    // closest() busca el ancestro más cercano con la clase especificada
    const itemDiv = button.closest('.item-pauta');
    
    // Paso 2: Eliminar el item del DOM
    // Esto lo remueve visualmente de la página
    itemDiv.remove();
    
    // Paso 3: Actualizar disponibilidad de secciones después de eliminar
    // La sección del item eliminado ahora está disponible para otros items
    actualizarSeccionesDisponibles();
    
    // Paso 4: Renumerar todos los items restantes
    // Los números deben ser consecutivos (1, 2, 3...) sin saltos
    renumerarItems();
    
    // Paso 5: Si no quedan items, mostrar mensaje informativo
    // Esto indica al usuario que debe agregar al menos un item a la pauta
    const items = document.querySelectorAll('.item-pauta');
    if (items.length === 0) {
        const noItemsMessage = document.getElementById('noItemsMessage');
        if (noItemsMessage) {
            noItemsMessage.style.display = 'block';  // Mostrar mensaje "No hay items agregados"
        }
    }
}

// Función para renumerar todos los items de la pauta después de eliminar uno
// Asegura que los números de los items sean consecutivos (1, 2, 3...) sin saltos
// Se ejecuta automáticamente después de eliminar un item
function renumerarItems() {
    // Paso 1: Obtener todos los items actuales en el DOM
    const items = document.querySelectorAll('.item-pauta');
    
    // Paso 2: Renumerar cada item con números consecutivos empezando desde 1
    items.forEach((item, index) => {
        // Buscar el elemento que muestra el número del item y actualizar su texto
        item.querySelector('.item-number').textContent = index + 1;  // index es 0-based, así que sumamos 1
    });
}

// Función que se ejecuta cuando el usuario selecciona una sección en un item
// Carga los tipos de reparación disponibles para esa sección y los muestra como checkboxes
// Parámetros:
//   selectElement: Elemento select que disparó el evento (contiene el ID de la sección seleccionada)
function cargarTiposReparacionItem(selectElement) {
    // Paso 1: Obtener el ID de la sección seleccionada
    const seccionId = selectElement.value;
    
    // Paso 2: Encontrar el contenedor del item y el contenedor de tipos de reparación
    const itemDiv = selectElement.closest('.item-pauta');  // Contenedor del item completo
    const tiposContainer = itemDiv.querySelector('.tipos-reparacion-list');  // Donde se mostrarán los tipos
    
    // Paso 3: Si no hay sección seleccionada, mostrar mensaje y salir
    if (!seccionId) {
        tiposContainer.innerHTML = '<p class="text-muted small mb-0">Seleccione primero una sección</p>';
        // Actualizar disponibilidad de secciones (por si se deseleccionó una sección)
        actualizarSeccionesDisponibles();
        return;  // Salir de la función
    }
    
    // Paso 4: Cargar y mostrar los tipos de reparación para la sección seleccionada
    cargarTiposReparacionParaSeccion(seccionId, tiposContainer);
    
    // Paso 5: Actualizar disponibilidad de secciones en todos los selects
    // Esto oculta la sección recién seleccionada en otros items
    actualizarSeccionesDisponibles();
}

// Función para cargar y mostrar los tipos de reparación disponibles para una sección específica
// Genera checkboxes para cada tipo de reparación, permitiendo selección múltiple
// Parámetros:
//   seccionId: ID de la sección para la cual se cargarán los tipos de reparación
//   container: Elemento DOM donde se insertarán los checkboxes generados
//   idsSeleccionados: Array de IDs de tipos de reparación a pre-seleccionar (opcional, para modo edición)
function cargarTiposReparacionParaSeccion(seccionId, container, idsSeleccionados = []) {
    // Paso 1: Filtrar tipos de reparación que pertenecen a la sección seleccionada
    // window.tiposReparacion se define en el template HTML con todos los tipos disponibles
    const tiposFiltrados = window.tiposReparacion.filter(tipo => tipo.seccion_id == seccionId);
    
    // Paso 2: Si no hay tipos de reparación para esta sección, mostrar mensaje y salir
    if (tiposFiltrados.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">No hay tipos de reparación para esta sección</p>';
        return;  // Salir de la función
    }
    
    // Paso 3: Generar HTML para los checkboxes de tipos de reparación
    let html = '';
    const timestamp = Date.now();  // Timestamp para hacer IDs únicos (evita conflictos si hay múltiples items)
    
    tiposFiltrados.forEach((tipo, index) => {
        // Determinar si este tipo debe estar marcado (pre-seleccionado)
        const checked = idsSeleccionados.includes(tipo.tipoReparacion_id) ? 'checked' : '';
        
        // Generar ID único para el checkbox (combina ID del tipo, timestamp e índice)
        const uniqueId = `tipo_${tipo.tipoReparacion_id}_${timestamp}_${index}`;
        
        // Generar HTML del checkbox con su label
        html += `
            <div class="tipo-checkbox">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           value="${tipo.tipoReparacion_id}" 
                           id="${uniqueId}"
                           ${checked}>
                    <label class="form-check-label small" for="${uniqueId}">
                        ${tipo.nombre}
                    </label>
                </div>
            </div>
        `;
    });
    
    // Paso 4: Insertar el HTML generado en el contenedor
    container.innerHTML = html;
}

// Función principal para guardar la pauta de mantenimiento
// Se ejecuta cuando el usuario envía el formulario
// Valida los datos, los prepara y los envía al servidor mediante AJAX
// Parámetros:
//   e: Evento del formulario (se usa para prevenir el envío por defecto)
function guardarPauta(e) {
    // Paso 1: Prevenir el envío por defecto del formulario (evita recargar la página)
    e.preventDefault();
    
    // Paso 2: Obtener y validar datos básicos de la pauta
    // El modelo puede estar en un select (creación) o campo hidden (edición)
    const modeloId = document.getElementById('modeloEquipo_id').value;
    const nombre = document.getElementById('nombre').value.trim();  // trim() elimina espacios al inicio/final
    
    // Validación 1: Verificar que se haya seleccionado un modelo
    if (!modeloId) {
        mostrarError('Debe seleccionar un modelo de equipo');
        return;  // Detener ejecución si falta el modelo
    }
    
    // Validación 2: Verificar que se haya ingresado un nombre
    if (!nombre) {
        mostrarError('El nombre de la pauta es requerido');
        return;  // Detener ejecución si falta el nombre
    }
    
    // Paso 3: Recopilar todos los items de la pauta
    // Cada item contiene una sección y múltiples tipos de reparación seleccionados
    const items = [];
    const itemDivs = document.querySelectorAll('.item-pauta');  // Todos los items agregados al formulario
    
    // Validación 3: Verificar que haya al menos un item agregado
    if (itemDivs.length === 0) {
        mostrarError('Debe agregar al menos un item a la pauta');
        return;  // Detener ejecución si no hay items
    }
    
    // Paso 4: Validar y recopilar datos de cada item
    let hayError = false;
    itemDivs.forEach((itemDiv, index) => {
        // Obtener sección seleccionada en este item
        const seccionId = itemDiv.querySelector('.seccion-select').value;
        
        // Obtener tipos de reparación marcados (checkboxes seleccionados)
        const tiposCheckboxes = itemDiv.querySelectorAll('.tipos-reparacion-list input[type="checkbox"]:checked');
        const tiposIds = Array.from(tiposCheckboxes).map(cb => parseInt(cb.value));  // Convertir a números
        
        // Validación 4: Verificar que cada item tenga una sección seleccionada
        if (!seccionId) {
            mostrarError(`Item ${index + 1}: Debe seleccionar una sección`);
            hayError = true;
            return;  // Continuar con el siguiente item
        }
        
        // Validación 5: Verificar que cada item tenga al menos un tipo de reparación seleccionado
        if (tiposIds.length === 0) {
            mostrarError(`Item ${index + 1}: Debe seleccionar al menos un tipo de reparación`);
            hayError = true;
            return;  // Continuar con el siguiente item
        }
        
        // Si el item es válido, agregarlo al array de items
        items.push({
            seccion_id: parseInt(seccionId),  // ID de la sección (convertido a número)
            tipos_reparacion_ids: tiposIds  // Array de IDs de tipos de reparación
        });
    });
    
    // Si hubo errores de validación en algún item, detener ejecución
    if (hayError) return;
    
    // Paso 5: Preparar objeto con todos los datos de la pauta para enviar al servidor
    const data = {
        modeloEquipo_id: parseInt(modeloId),  // ID del modelo de equipo
        nombre: nombre,  // Nombre de la pauta
        descripcion: document.getElementById('descripcion').value.trim(),  // Descripción (opcional)
        items: items  // Array de items con secciones y tipos de reparación
    };
    
    // Paso 6: Si estamos en modo edición, agregar el ID de la pauta
    // Esto permite al servidor distinguir entre creación y edición
    if (window.esEdicion) {
        const pautaId = document.getElementById('pauta_id').value;
        if (pautaId) {
            data.pauta_id = parseInt(pautaId);  // ID de la pauta a editar
        }
    }
    
    console.log('Datos a enviar:', data);  // Log para debugging
    
    // Paso 7: Enviar datos al servidor mediante petición AJAX
    fetch('/maquinarias/api/pautas-mantenimiento/guardar/', {
        method: 'POST',  // Método HTTP POST para crear/actualizar
        headers: {
            'Content-Type': 'application/json',  // Indicar que enviamos JSON
        },
        body: JSON.stringify(data)  // Convertir objeto JavaScript a JSON
    })
    .then(response => response.json())  // Convertir respuesta del servidor a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: La pauta fue guardada correctamente
            mostrarExito(data.message);  // Mostrar mensaje de éxito
            // Redirigir a la lista de pautas después de un breve delay
            setTimeout(() => {
                window.location.href = '/maquinarias/pautas-mantenimiento/';
            }, 1500);  // Esperar 1.5 segundos para que el usuario vea el mensaje
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarError(data.message);  // Mostrar mensaje de error del servidor
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        mostrarError('Error al guardar pauta de mantenimiento');  // Mostrar mensaje genérico de error
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

