// Función para calcular el dígito verificador
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

// Función para formatear el RUT
function formatearRut(rut) {
    // Eliminar puntos y guión
    rut = rut.replace(/\./g, '').replace(/-/g, '');
    
    // Obtener el número base y el dígito verificador
    const rutBase = rut.slice(0, -1);
    const dv = rut.slice(-1).toUpperCase();
    
    // Formatear con puntos
    let rutFormateado = '';
    for (let i = rutBase.length - 1, j = 0; i >= 0; i--, j++) {
        rutFormateado = rutBase.charAt(i) + rutFormateado;
        if ((j + 1) % 3 === 0 && i !== 0) {
            rutFormateado = '.' + rutFormateado;
        }
    }
    
    return rutFormateado + '-' + dv;
}

// Función para validar el RUT
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

// Función para limpiar el RUT (dejar solo números)
function limpiarRut(rut) {
    return rut.replace(/\./g, '').replace(/-/g, '');
}

// Configurar los eventos para los campos de RUT
document.addEventListener('DOMContentLoaded', function() {
    // Función para configurar los eventos en un campo RUT
    function configurarCampoRut(rutInput, dvInput) {
        if (!rutInput) return;

        // Si no se proporciona el campo DV, intentar encontrarlo
        if (!dvInput) {
            // Intentar encontrar el campo DV con diferentes IDs posibles
            dvInput = document.getElementById('id_dv') || document.getElementById('id_dvrut') || 
                     document.getElementById('edit-dv') || document.getElementById('edit-dvrut');
        }

        if (!dvInput) return;

        // Función para actualizar el DV
        function actualizarDV(rutValue) {
            // Limpiar el RUT de puntos y guiones
            const rutLimpio = limpiarRut(rutValue);
            
            // Solo calcular DV si hay al menos 7 dígitos
            if (rutLimpio.length >= 7) {
                const dv = calcularDV(rutLimpio);
                dvInput.value = dv;
            } else {
                dvInput.value = ''; // Limpiar el campo DV si no hay suficientes dígitos
            }
        }

        // Al salir del campo RUT
        rutInput.addEventListener('blur', function() {
            let rut = this.value;
            if (rut) {
                rut = limpiarRut(rut);
                // Solo formatear y calcular DV si hay suficientes dígitos
                if (rut.length >= 7) {
                    const dv = calcularDV(rut);
                    dvInput.value = dv;
                    this.value = formatearRut(rut + dv).split('-')[0];
                }
            }
        });

        // Mientras se escribe en el campo RUT
        rutInput.addEventListener('input', function() {
            let valor = this.value;
            
            // Eliminar caracteres no numéricos
            valor = valor.replace(/[^\d]/g, '');
            
            // Formatear con puntos
            let valorFormateado = '';
            for (let i = valor.length - 1, j = 0; i >= 0; i--, j++) {
                valorFormateado = valor.charAt(i) + valorFormateado;
                if ((j + 1) % 3 === 0 && i !== 0) {
                    valorFormateado = '.' + valorFormateado;
                }
            }
            
            this.value = valorFormateado;

            // Actualizar DV solo si hay suficientes dígitos
            actualizarDV(valor);
        });

        // Validar al enviar el formulario
        rutInput.closest('form').addEventListener('submit', function(e) {
            const rutLimpio = limpiarRut(rutInput.value);
            if (rutLimpio.length < 7) {
                e.preventDefault();
                alert('El RUT debe tener al menos 7 dígitos');
                return;
            }
            
            const rutCompleto = rutLimpio + dvInput.value;
            if (!validarRut(rutCompleto)) {
                e.preventDefault();
                alert('El RUT ingresado no es válido');
            }
        });
    }

    // Configurar para el formulario de creación
    configurarCampoRut(
        document.getElementById('id_rut'),
        document.getElementById('id_dvrut')
    );

    // Configurar para el formulario de edición
    configurarCampoRut(
        document.getElementById('edit-rut'),
        document.getElementById('edit-dv')
    );
}); 