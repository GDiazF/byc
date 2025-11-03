// Formulario de creación y edición de personal

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el manejador de región/comuna si existe
    if (typeof setupRegionComunaHandlers === 'function') {
        setupRegionComunaHandlers();
    }
    
    // Asegurar que el RUT nunca se formatee con puntos
    const rutInput = document.getElementById('id_rut');
    if (rutInput) {
        // Limpiar el valor inicial si tiene puntos
        if (rutInput.value) {
            let valorInicial = rutInput.value;
            valorInicial = valorInicial.replace(/\./g, '').replace(/-/g, '');
            rutInput.value = valorInicial;
        }
        
        // Forzar limpieza del RUT en cada evento
        rutInput.addEventListener('blur', function() {
            let valor = this.value;
            // Eliminar cualquier punto o guión
            valor = valor.replace(/\./g, '').replace(/-/g, '');
            this.value = valor;
        });
        
        rutInput.addEventListener('input', function() {
            let valor = this.value;
            // Eliminar cualquier punto o guión mientras se escribe
            valor = valor.replace(/\./g, '').replace(/-/g, '');
            this.value = valor;
        });
    }

    // Validación del formulario
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

