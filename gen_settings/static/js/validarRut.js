/**
 * Calcula el dígito verificador de un RUT chileno.
 * 
 * Utiliza el algoritmo estándar chileno para calcular el dígito verificador
 * basado en los dígitos del RUT.
 * 
 * @param {string} rut - RUT sin dígito verificador (solo números)
 * @returns {string} Dígito verificador calculado ('0'-'9' o 'K')
 */
function calcularDV(rut) {
    let suma = 0;
    let multiplicador = 2;
    
    // Para cada dígito del RUT
    for (let i = rut.length - 1; i >= 0; i--) {
        suma += parseInt(rut.charAt(i)) * multiplicador;
        multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
    }
    
    const resto = suma % 11;
    const dv = 11 - resto;
    
    if (dv === 11) return '0';
    if (dv === 10) return 'K';
    return dv.toString();
}

/**
 * Formatea un RUT eliminando puntos y guiones.
 * 
 * NOTA: Esta función está deshabilitada y ya no se usa para evitar
 * formateo con puntos. Solo limpia el RUT.
 * 
 * @param {string} rut - RUT a formatear
 * @returns {string} RUT limpio sin puntos ni guiones
 * @deprecated Esta función ya no se usa para evitar formateo con puntos
 */
function formatearRut(rut) {
    // Solo devolver el RUT limpio sin formateo
    return rut.replace(/\./g, '').replace(/-/g, '');
}

/**
 * Valida un RUT chileno completo (con dígito verificador).
 * 
 * Verifica que el formato sea correcto y que el dígito verificador
 * coincida con el calculado según el algoritmo chileno.
 * 
 * @param {string} rut - RUT completo a validar (puede incluir puntos y guión)
 * @returns {boolean} true si el RUT es válido, false en caso contrario
 */
function validarRut(rut) {
    // Eliminar puntos y guión
    rut = rut.replace(/\./g, '').replace(/-/g, '');
    
    // Validar largo mínimo y que solo contenga números y K
    if (rut.length < 2 || !/^[0-9]+[0-9K]$/.test(rut.toUpperCase())) {
        return false;
    }
    
    const rutBase = rut.slice(0, -1);
    const dvIngresado = rut.slice(-1).toUpperCase();
    const dvCalculado = calcularDV(rutBase);
    
    return dvIngresado === dvCalculado;
}

/**
 * Limpia un RUT eliminando puntos y guiones.
 * 
 * Deja solo los caracteres numéricos y la K (si existe) del dígito verificador.
 * 
 * @param {string} rut - RUT a limpiar
 * @returns {string} RUT limpio sin puntos ni guiones
 */
function limpiarRut(rut) {
    return rut.replace(/\./g, '').replace(/-/g, '');
}

// Configurar los eventos para los campos de RUT cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Configura los eventos para un campo RUT y su campo de dígito verificador.
     * 
     * Configura eventos para:
     * - Calcular automáticamente el dígito verificador al salir del campo RUT
     * - Limpiar caracteres no numéricos mientras se escribe
     * - Validar el RUT completo al enviar el formulario
     * 
     * @param {HTMLElement} rutInput - Campo de entrada para el RUT
     * @param {HTMLElement} dvInput - Campo de entrada para el dígito verificador
     */
    function configurarCampoRut(rutInput, dvInput) {
        if (!rutInput || !dvInput) return;

        // Al salir del campo RUT
        rutInput.addEventListener('blur', function() {
            let rut = this.value;
            if (rut) {
                rut = limpiarRut(rut);
                // Calcular DV
                const dv = calcularDV(rut);
                dvInput.value = dv;
                
                // Nunca formatear con puntos, mantener solo números
                this.value = rut;
            }
        });

        // Mientras se escribe en el campo RUT
        rutInput.addEventListener('input', function() {
            let valor = this.value;
            
            // Eliminar caracteres no numéricos
            valor = valor.replace(/[^\d]/g, '');
            
            // Nunca formatear con puntos, mantener solo números
            this.value = valor;
        });

        // Validar al enviar el formulario
        rutInput.closest('form').addEventListener('submit', function(e) {
            const rutCompleto = limpiarRut(rutInput.value) + dvInput.value;
            if (!validarRut(rutCompleto)) {
                e.preventDefault();
                alert('El RUT ingresado no es válido');
            }
        });
    }

    // Configurar para el formulario de creación
    configurarCampoRut(
        document.getElementById('id_rut'),
        document.getElementById('id_dv')
    );

    // Configurar para el formulario de edición
    configurarCampoRut(
        document.getElementById('edit-rut'),
        document.getElementById('edit-dv')
    );
}); 