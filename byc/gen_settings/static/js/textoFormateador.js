/**
 * Función para convertir texto a mayúsculas, eliminar tildes y símbolos
 * @param {string} texto - El texto a formatear
 * @returns {string} - El texto formateado
 */
function formatearTexto(texto) {
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
    
    return texto;
}

/**
 * Función para aplicar el formateo a un elemento de entrada
 * @param {HTMLElement} elemento - El elemento de entrada a formatear
 */
function aplicarFormateo(elemento) {
    // Aplicar formateo al perder el foco
    elemento.addEventListener('blur', function() {
        this.value = formatearTexto(this.value);
    });
    
    // Aplicar formateo mientras se escribe
    elemento.addEventListener('input', function() {
        // Guardar la posición del cursor
        const posicionCursor = this.selectionStart;
        
        // Formatear el texto
        const textoFormateado = formatearTexto(this.value);
        
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
    
    // Aplicar formateo a cada campo
    camposTexto.forEach(campo => {
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
            aplicarFormateoATodosLosCampos();
        }
    });
});

// Configurar el observador
observer.observe(document.body, {
    childList: true,
    subtree: true
}); 