// ============================================
// DATE PICKER CHILENO - COMPONENTE REUTILIZABLE
// ============================================
// Este archivo proporciona un date picker nativo con formato chileno (DD-MM-YYYY)
// para usar en todo el proyecto sin dependencias externas.

/**
 * Convierte una fecha ISO (YYYY-MM-DD) a formato chileno (DD-MM-YYYY)
 * @param {string} fechaISO - Fecha en formato YYYY-MM-DD
 * @returns {string} Fecha en formato DD-MM-YYYY
 */
function convertirFechaISOAChileno(fechaISO) {
    if (!fechaISO) return '';
    
    const partes = fechaISO.split('-');
    if (partes.length !== 3) return '';
    
    const [anio, mes, dia] = partes;
    return `${dia.padStart(2, '0')}-${mes.padStart(2, '0')}-${anio}`;
}

/**
 * Convierte una fecha chilena (DD-MM-YYYY) a formato ISO (YYYY-MM-DD)
 * @param {string} fechaChilena - Fecha en formato DD-MM-YYYY
 * @returns {string} Fecha en formato YYYY-MM-DD
 */
function convertirFechaChilenoAISO(fechaChilena) {
    if (!fechaChilena) return '';
    
    const partes = fechaChilena.split('-');
    if (partes.length !== 3) return '';
    
    const [dia, mes, anio] = partes;
    return `${anio}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`;
}

/**
 * Convierte un input normal en un date picker chileno
 * @param {HTMLElement} inputOriginal - Input que se convertirá en date picker
 */
function convertirADatePickerChile(inputOriginal) {
    // Verificar si ya fue convertido
    if (inputOriginal.getAttribute('data-picker-initialized') === 'true') {
        return null;
    }
    
    // Guardar atributos del input original
    const id = inputOriginal.id;
    const name = inputOriginal.name || id;
    const required = inputOriginal.required;
    const value = inputOriginal.value;
    const placeholder = inputOriginal.placeholder || 'DD-MM-YYYY';
    const className = inputOriginal.className;
    
    // Detectar el tamaño del input original
    const isSmall = className.includes('form-control-sm');
    const isLarge = className.includes('form-control-lg');
    
    // Crear contenedor con el tamaño apropiado
    const contenedor = document.createElement('div');
    let inputGroupClass = 'input-group';
    if (isSmall) inputGroupClass += ' input-group-sm';
    if (isLarge) inputGroupClass += ' input-group-lg';
    contenedor.className = inputGroupClass;
    
    // Input de display (visible, formato chileno, readonly)
    const inputDisplay = document.createElement('input');
    inputDisplay.type = 'text';
    inputDisplay.className = className;
    inputDisplay.id = `${id}_display`;
    inputDisplay.placeholder = placeholder;
    inputDisplay.maxLength = 10;
    inputDisplay.required = required;
    inputDisplay.readOnly = true;
    
    // Botón de calendario con el tamaño apropiado
    const botonCalendario = document.createElement('button');
    let btnClass = 'btn btn-outline-secondary';
    if (isSmall) btnClass += ' btn-sm';
    if (isLarge) btnClass += ' btn-lg';
    botonCalendario.className = btnClass;
    botonCalendario.type = 'button';
    botonCalendario.innerHTML = '<i class="bi bi-calendar3"></i>';
    botonCalendario.title = 'Seleccionar fecha';
    
    // Input oculto tipo date (hace el trabajo real)
    const inputHidden = document.createElement('input');
    inputHidden.type = 'date';
    inputHidden.id = `${id}_hidden`;
    inputHidden.className = 'fecha-chile-hidden';
    inputHidden.style.cssText = 'position: absolute; opacity: 0; pointer-events: all; left: 0; top: 30px; width: 100%; height: 38px;';
    
    // Input real que se enviará al backend (con el ID y name originales)
    const inputReal = document.createElement('input');
    inputReal.type = 'hidden';
    inputReal.id = id;
    inputReal.name = name;
    
    // Si hay un valor inicial, configurarlo
    if (value) {
        // Si el valor está en formato ISO
        if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
            inputHidden.value = value;
            inputDisplay.value = convertirFechaISOAChileno(value);
            inputReal.value = value;
        }
        // Si el valor está en formato chileno
        else if (value.match(/^\d{2}-\d{2}-\d{4}$/)) {
            const iso = convertirFechaChilenoAISO(value);
            inputHidden.value = iso;
            inputDisplay.value = value;
            inputReal.value = iso;
        }
    }
    
    // Evento: cuando cambia el calendario oculto
    inputHidden.addEventListener('change', function() {
        if (this.value) {
            inputDisplay.value = convertirFechaISOAChileno(this.value);
            inputReal.value = this.value;
            
            // Disparar evento change en el input real para validaciones
            const event = new Event('change', { bubbles: true });
            inputReal.dispatchEvent(event);
        }
    });
    
    // Evento: hacer clic en el botón abre el calendario
    botonCalendario.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        inputHidden.showPicker();
    });
    
    // Evento: hacer clic en el display también abre el calendario
    inputDisplay.addEventListener('click', function() {
        inputHidden.showPicker();
    });
    
    // Construir la estructura
    contenedor.appendChild(inputDisplay);
    contenedor.appendChild(botonCalendario);
    
    // Crear un wrapper para contener todo
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.setAttribute('data-datepicker-chile-wrapper', 'true');
    wrapper.setAttribute('data-original-id', id);
    wrapper.appendChild(contenedor);
    wrapper.appendChild(inputHidden);
    wrapper.appendChild(inputReal);
    
    // Marcar el input real como inicializado
    inputReal.setAttribute('data-picker-initialized', 'true');
    
    // Reemplazar el input original con el nuevo sistema
    inputOriginal.parentNode.replaceChild(wrapper, inputOriginal);
    
    // Agregar método público para establecer valor desde fuera
    wrapper._datePickerChile = {
        display: inputDisplay,
        hidden: inputHidden,
        real: inputReal,
        container: wrapper,
        getValue: () => inputReal.value,
        setValue: (fechaISO) => {
            if (fechaISO) {
                inputHidden.value = fechaISO;
                inputDisplay.value = convertirFechaISOAChileno(fechaISO);
                inputReal.value = fechaISO;
                
                // Disparar evento change
                const event = new Event('change', { bubbles: true });
                inputReal.dispatchEvent(event);
            }
        },
        getValueChileno: () => inputDisplay.value,
        clear: () => {
            inputHidden.value = '';
            inputDisplay.value = '';
            inputReal.value = '';
        }
    };
    
    // Retornar referencias para acceso programático
    return wrapper._datePickerChile;
}

/**
 * Inicializa todos los date pickers chilenos en la página
 * Busca inputs con clase 'fecha-chile-picker' y los convierte automáticamente
 */
function inicializarDatePickersChile() {
    // Buscar inputs con la clase pero que NO estén ya inicializados
    const todosInputs = document.querySelectorAll('input.fecha-chile-picker');
    const inputs = [];
    
    todosInputs.forEach(input => {
        // Verificar si ya fue inicializado
        if (input.getAttribute('data-picker-initialized') === 'true') {
            return;
        }
        
        // Verificar si está dentro de un wrapper ya creado
        const wrapper = input.closest('[data-datepicker-chile-wrapper]');
        if (wrapper) {
            return;
        }
        
        inputs.push(input);
    });
    
    // Solo loguear si hay inputs para inicializar
    if (inputs.length > 0) {
        console.log(`Inicializando ${inputs.length} date picker(s) chileno(s)...`);
    }
    
    inputs.forEach(input => {
        try {
            convertirADatePickerChile(input);
        } catch (error) {
            console.error('Error inicializando date picker en', input.id, ':', error);
        }
    });
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarDatePickersChile);
} else {
    // DOM ya está listo
    inicializarDatePickersChile();
}

// Exportar funciones para uso global
window.DatePickerChile = {
    inicializar: inicializarDatePickersChile,
    convertir: convertirADatePickerChile,
    convertirISOAChileno: convertirFechaISOAChileno,
    convertirChilenoAISO: convertirFechaChilenoAISO,
    
    /**
     * Establece el valor de un date picker por su ID
     * @param {string} inputId - ID del input original
     * @param {string} fechaISO - Fecha en formato YYYY-MM-DD
     */
    setValor: function(inputId, fechaISO) {
        // Buscar el wrapper del date picker
        const wrapper = document.querySelector(`[data-datepicker-chile-wrapper][data-original-id="${inputId}"]`);
        
        if (wrapper && wrapper._datePickerChile) {
            wrapper._datePickerChile.setValue(fechaISO);
        } else {
            // Si no existe el wrapper, intentar establecer en el input directamente
            const input = document.getElementById(inputId);
            if (input) {
                input.value = fechaISO;
            }
        }
    },
    
    /**
     * Obtiene el valor de un date picker por su ID
     * @param {string} inputId - ID del input original
     * @returns {string} Fecha en formato YYYY-MM-DD
     */
    getValor: function(inputId) {
        const wrapper = document.querySelector(`[data-datepicker-chile-wrapper][data-original-id="${inputId}"]`);
        if (wrapper && wrapper._datePickerChile) {
            return wrapper._datePickerChile.getValue();
        }
        return '';
    },
    
    /**
     * Limpia el valor de un date picker por su ID
     * @param {string} inputId - ID del input original
     */
    limpiar: function(inputId) {
        const wrapper = document.querySelector(`[data-datepicker-chile-wrapper][data-original-id="${inputId}"]`);
        if (wrapper && wrapper._datePickerChile) {
            wrapper._datePickerChile.clear();
        }
    }
};

