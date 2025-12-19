/**
 * Función para convertir texto a mayúsculas, eliminar tildes y símbolos
 * @param {string} texto - El texto a formatear
 * @param {boolean} aplicarTrim - Si debe aplicar trim (solo al terminar de escribir)
 * @returns {string} - El texto formateado
 */
function formatearTexto(texto, aplicarTrim = false) {
    // Convertir a mayúsculas
    texto = texto.toUpperCase();
    
    // Reemplazar caracteres con tildes
    const caracteresConTildes = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N'
    };
    
    for (const [conTilde, sinTilde] of Object.entries(caracteresConTildes)) {
        texto = texto.replace(new RegExp(conTilde, 'g'), sinTilde);
    }
    
    // Eliminar símbolos y caracteres especiales (mantener letras, números y espacios)
    texto = texto.replace(/[^A-Z0-9\s]/g, '');
    
    // Eliminar espacios al inicio y al final (solo si aplicarTrim es true)
    if (aplicarTrim) {
        texto = texto.trim();
    }
    
    return texto;
}

/**
 * Función para aplicar el formateo a un elemento de entrada
 * @param {HTMLElement} elemento - El elemento de entrada a formatear
 */
function aplicarFormateo(elemento) {
    // Verificar si ya tiene listeners (evitar duplicados)
    if (elemento.hasAttribute('data-formateador-aplicado')) {
        return; // Ya tiene el formateo aplicado
    }
    
    // Marcar como procesado
    elemento.setAttribute('data-formateador-aplicado', 'true');
    
    // Aplicar formateo al perder el foco (CON trim)
    elemento.addEventListener('blur', function() {
        // Verificar nuevamente que no sea un campo de fecha
        if (this.classList.contains('fecha-chile-picker') || 
            this.closest('[data-datepicker-chile-wrapper]') ||
            this.hasAttribute('data-datepicker-field') ||
            this.hasAttribute('data-picker-initialized')) {
            return;
        }
        this.value = formatearTexto(this.value, true);
    });
    
    // Aplicar formateo mientras se escribe (SIN trim para permitir espacios)
    elemento.addEventListener('input', function() {
        // Verificar nuevamente que no sea un campo de fecha
        if (this.classList.contains('fecha-chile-picker') || 
            this.closest('[data-datepicker-chile-wrapper]') ||
            this.hasAttribute('data-datepicker-field') ||
            this.hasAttribute('data-picker-initialized')) {
            return;
        }
        
        // Guardar la posición del cursor
        const posicionCursor = this.selectionStart;
        
        // Formatear el texto sin trim (permite espacios intermedios)
        const textoFormateado = formatearTexto(this.value, false);
        
        // Si el texto cambió, actualizar el valor
        if (this.value !== textoFormateado) {
            this.value = textoFormateado;
            
            // Restaurar la posición del cursor
            this.setSelectionRange(posicionCursor, posicionCursor);
        }
    });
}

// Función para aplicar formateo a todos los campos de texto
function aplicarFormateoATodosLosCampos() {
    // Seleccionar todos los campos de texto en formularios
    const camposTexto = document.querySelectorAll('input[type="text"], textarea');
    
    // Aplicar formateo a cada campo, EXCLUYENDO los datepickers chilenos
    camposTexto.forEach(campo => {
        // Excluir campos de fecha (datepicker chileno)
        if (campo.classList.contains('fecha-chile-picker') || 
            campo.closest('[data-datepicker-chile-wrapper]') ||
            campo.hasAttribute('data-picker-initialized') ||
            campo.hasAttribute('data-datepicker-field')) {
            return; // Saltar este campo
        }
        
        aplicarFormateo(campo);
    });
}

// Aplicar formateo a todos los campos cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    aplicarFormateoATodosLosCampos();
});

// Observar cambios en el DOM para aplicar formateo a nuevos campos
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            // Esperar un poco para que el datepicker se inicialice primero si es necesario
            setTimeout(function() {
                aplicarFormateoATodosLosCampos();
            }, 100);
        }
    });
});

// Configurar el observador
observer.observe(document.body, {
    childList: true,
    subtree: true
}); 