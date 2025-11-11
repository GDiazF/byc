// Variables globales
let itemIndex = 0;
let todosModelos = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('formPautaMantenimiento');
    const modeloSelect = document.getElementById('modeloEquipo_id');
    const tipoSelect = document.getElementById('tipo_equipo_id');
    const marcaSelect = document.getElementById('marca_equipo_id');
    
    // Solo cargar modelos si existe el select (no es hidden)
    if (modeloSelect && modeloSelect.tagName === 'SELECT') {
        todosModelos = Array.from(modeloSelect.options).map(option => ({
            value: option.value,
            text: option.text,
            tipo: option.dataset.tipo,
            marca: option.dataset.marca
        }));
    }
    
    // Event listeners para cascada de selects (solo si existen)
    if (tipoSelect && tipoSelect.tagName === 'SELECT') {
        tipoSelect.addEventListener('change', filtrarMarcas);
    }
    if (marcaSelect && marcaSelect.tagName === 'SELECT') {
        marcaSelect.addEventListener('change', filtrarModelos);
    }
    if (form) {
        form.addEventListener('submit', guardarPauta);
    }
    
    // Solo aplicar filtrado si los selects existen y no están disabled (creación normal)
    if (tipoSelect && tipoSelect.tagName === 'SELECT' && !tipoSelect.disabled && tipoSelect.value) {
        filtrarMarcas();
        setTimeout(() => {
            if (marcaSelect && marcaSelect.value) {
                filtrarModelos();
            }
        }, 100);
    }
    
    // Si es edición, cargar items existentes
    if (window.esEdicion && window.itemsExistentes) {
        window.itemsExistentes.forEach(item => {
            agregarItem(item.seccion_id, item.tipos_reparacion_ids);
        });
    }
});

// Filtrar marcas según tipo seleccionado
function filtrarMarcas() {
    const tipoId = document.getElementById('tipo_equipo_id').value;
    const marcaSelect = document.getElementById('marca_equipo_id');
    const modeloSelect = document.getElementById('modeloEquipo_id');
    
    if (!tipoId) {
        marcaSelect.disabled = true;
        marcaSelect.value = '';
        modeloSelect.disabled = true;
        modeloSelect.value = '';
        return;
    }
    
    // Obtener marcas únicas para el tipo seleccionado
    const marcasDisponibles = new Set();
    todosModelos.forEach(modelo => {
        if (String(modelo.tipo) === String(tipoId) && modelo.value) {
            marcasDisponibles.add(String(modelo.marca));
        }
    });
    
    // Habilitar y filtrar el select de marcas
    const marcaOptions = Array.from(marcaSelect.options);
    marcaOptions.forEach(option => {
        if (!option.value) return;
        option.style.display = marcasDisponibles.has(String(option.value)) ? '' : 'none';
    });
    
    marcaSelect.disabled = false;
    marcaSelect.value = '';
    modeloSelect.disabled = true;
    modeloSelect.value = '';
}

// Filtrar modelos según tipo y marca seleccionados
function filtrarModelos() {
    const tipoId = document.getElementById('tipo_equipo_id').value;
    const marcaId = document.getElementById('marca_equipo_id').value;
    const modeloSelect = document.getElementById('modeloEquipo_id');
    
    if (!tipoId || !marcaId) {
        modeloSelect.disabled = true;
        modeloSelect.value = '';
        return;
    }
    
    // Filtrar modelos
    const modeloOptions = Array.from(modeloSelect.options);
    modeloOptions.forEach(option => {
        if (!option.value) return;
        const visible = (String(option.dataset.tipo) === String(tipoId) && String(option.dataset.marca) === String(marcaId));
        option.style.display = visible ? '' : 'none';
    });
    
    modeloSelect.disabled = false;
    modeloSelect.value = '';
}

// Agregar un nuevo item a la pauta
function agregarItem(seccionIdInicial = null, tiposIdsIniciales = []) {
    const container = document.getElementById('itemsContainer');
    const noItemsMessage = document.getElementById('noItemsMessage');
    const template = document.getElementById('itemPautaTemplate');
    
    if (!template) return;
    
    // Ocultar mensaje de "no hay items"
    if (noItemsMessage) {
        noItemsMessage.style.display = 'none';
    }
    
    // Clonar template
    const clone = template.content.cloneNode(true);
    const itemDiv = clone.querySelector('.item-pauta');
    
    // Asignar índice
    itemIndex++;
    itemDiv.dataset.itemIndex = itemIndex;
    itemDiv.querySelector('.item-number').textContent = itemIndex;
    
    // Agregar al DOM primero
    container.appendChild(clone);
    
    // Si es un item existente, pre-seleccionar sección DESPUÉS de agregar al DOM
    if (seccionIdInicial) {
        // Buscar el item recién agregado en el DOM
        const itemAgregado = container.querySelector(`[data-item-index="${itemIndex}"]`);
        if (!itemAgregado) return;
        
        const seccionSelect = itemAgregado.querySelector('.seccion-select');
        seccionSelect.value = seccionIdInicial;
        
        // Cargar tipos de reparación y pre-seleccionar
        const tiposContainer = itemAgregado.querySelector('.tipos-reparacion-list');
        cargarTiposReparacionParaSeccion(seccionIdInicial, tiposContainer, tiposIdsIniciales);
    }
}

// Eliminar un item
function eliminarItem(button) {
    const itemDiv = button.closest('.item-pauta');
    itemDiv.remove();
    
    // Renumerar items
    renumerarItems();
    
    // Si no quedan items, mostrar mensaje
    const items = document.querySelectorAll('.item-pauta');
    if (items.length === 0) {
        const noItemsMessage = document.getElementById('noItemsMessage');
        if (noItemsMessage) {
            noItemsMessage.style.display = 'block';
        }
    }
}

// Renumerar items después de eliminar
function renumerarItems() {
    const items = document.querySelectorAll('.item-pauta');
    items.forEach((item, index) => {
        item.querySelector('.item-number').textContent = index + 1;
    });
}

// Cargar tipos de reparación cuando se selecciona una sección
function cargarTiposReparacionItem(selectElement) {
    const seccionId = selectElement.value;
    const itemDiv = selectElement.closest('.item-pauta');
    const tiposContainer = itemDiv.querySelector('.tipos-reparacion-list');
    
    if (!seccionId) {
        tiposContainer.innerHTML = '<p class="text-muted small mb-0">Seleccione primero una sección</p>';
        return;
    }
    
    cargarTiposReparacionParaSeccion(seccionId, tiposContainer);
}

// Cargar tipos de reparación para una sección
function cargarTiposReparacionParaSeccion(seccionId, container, idsSeleccionados = []) {
    // Filtrar tipos de reparación para la sección
    const tiposFiltrados = window.tiposReparacion.filter(tipo => tipo.seccion_id == seccionId);
    
    if (tiposFiltrados.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">No hay tipos de reparación para esta sección</p>';
        return;
    }
    
    // Generar checkboxes
    let html = '';
    const timestamp = Date.now();
    tiposFiltrados.forEach((tipo, index) => {
        const checked = idsSeleccionados.includes(tipo.tipoReparacion_id) ? 'checked' : '';
        const uniqueId = `tipo_${tipo.tipoReparacion_id}_${timestamp}_${index}`;
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
    
    container.innerHTML = html;
}

// Guardar pauta
function guardarPauta(e) {
    e.preventDefault();
    
    // Obtener modeloId (puede ser select o hidden)
    const modeloId = document.getElementById('modeloEquipo_id').value;
    const nombre = document.getElementById('nombre').value.trim();
    
    if (!modeloId) {
        mostrarError('Debe seleccionar un modelo de equipo');
        return;
    }
    
    if (!nombre) {
        mostrarError('El nombre de la pauta es requerido');
        return;
    }
    
    // Recopilar items
    const items = [];
    const itemDivs = document.querySelectorAll('.item-pauta');
    
    if (itemDivs.length === 0) {
        mostrarError('Debe agregar al menos un item a la pauta');
        return;
    }
    
    let hayError = false;
    itemDivs.forEach((itemDiv, index) => {
        const seccionId = itemDiv.querySelector('.seccion-select').value;
        const tiposCheckboxes = itemDiv.querySelectorAll('.tipos-reparacion-list input[type="checkbox"]:checked');
        const tiposIds = Array.from(tiposCheckboxes).map(cb => parseInt(cb.value));
        
        if (!seccionId) {
            mostrarError(`Item ${index + 1}: Debe seleccionar una sección`);
            hayError = true;
            return;
        }
        
        if (tiposIds.length === 0) {
            mostrarError(`Item ${index + 1}: Debe seleccionar al menos un tipo de reparación`);
            hayError = true;
            return;
        }
        
        items.push({
            seccion_id: parseInt(seccionId),
            tipos_reparacion_ids: tiposIds
        });
    });
    
    if (hayError) return;
    
    // Preparar datos
    const data = {
        modeloEquipo_id: parseInt(modeloId),
        nombre: nombre,
        descripcion: document.getElementById('descripcion').value.trim(),
        items: items
    };
    
    // Si es edición, agregar ID
    if (window.esEdicion) {
        const pautaId = document.getElementById('pauta_id').value;
        if (pautaId) {
            data.pauta_id = parseInt(pautaId);
        }
    }
    
    console.log('Datos a enviar:', data);
    
    // Enviar al servidor
    fetch('/maquinarias/api/pautas-mantenimiento/guardar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            setTimeout(() => {
                window.location.href = '/maquinarias/pautas-mantenimiento/';
            }, 1500);
        } else {
            mostrarError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al guardar pauta de mantenimiento');
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

