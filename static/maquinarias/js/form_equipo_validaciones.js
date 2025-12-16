// ============================================================================
// VALIDACIONES DE FORMULARIO DE EQUIPO
// ============================================================================
// Este archivo contiene validaciones adicionales para campos numéricos del formulario de equipo.
// Previene la entrada de valores negativos en campos como horómetro, odómetro y horómetro de superestructura,
// ya que estos valores representan mediciones que no pueden ser negativas.

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Definir lista de campos numéricos que requieren validación
    // Estos campos representan mediciones de equipos que no pueden tener valores negativos
    const camposNumericos = [
        'horometro',  // Horómetro del equipo (horas de funcionamiento)
        'odometro',  // Odómetro del equipo (kilómetros recorridos)
        'horometroSuperEstructural'  // Horómetro de superestructura (horas de funcionamiento de la superestructura)
    ];
    
    // Paso 2: Configurar validaciones para cada campo numérico
    camposNumericos.forEach(campo => {
        // Paso 2.1: Obtener referencia al campo de entrada
        const input = document.getElementById(campo);
        
        // Validar que el campo exista antes de agregar listeners
        if (input) {
            // Paso 2.2: Agregar listener para el evento 'input'
            // Se ejecuta cada vez que el usuario escribe o modifica el valor del campo
            input.addEventListener('input', function() {
                // Si el campo tiene un valor y es negativo, establecerlo a 0
                // Esto corrige automáticamente valores negativos que puedan ingresarse
                if (this.value && parseFloat(this.value) < 0) {
                    this.value = 0;  // Establecer valor a 0 si es negativo
                }
            });
            
            // Paso 2.3: Agregar listener para el evento 'keypress'
            // Previene que el usuario pueda escribir el signo negativo (-) desde el teclado
            input.addEventListener('keypress', function(e) {
                // Prevenir signo negativo: si el usuario intenta escribir '-', cancelar el evento
                if (e.key === '-') {
                    e.preventDefault();  // Cancelar la entrada del carácter '-'
                }
            });
        }
    });
});

