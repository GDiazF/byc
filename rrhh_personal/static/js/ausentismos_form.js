// Formulario de ausentismos (crear/editar)

$(document).ready(function() {
    console.log('Ausentismos form JS loaded');
    
    // Manejar clic en botón de envío (crear/editar)
    $('#submitButton').on('click', function(e) {
        e.preventDefault();
        console.log('Submit button clicked');
        
        // Validar formulario
        const form = document.getElementById('ausentismoForm');
        console.log('Form validity:', form.checkValidity());
        
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            console.log('Form is invalid, showing validation messages');
            return;
        }
        
        console.log('Form is valid, showing confirmation modal');
        // Mostrar modal de confirmación
        $('#confirmModal').modal('show');
    });

    // Manejar confirmación de guardado/actualización
    $('#confirmButton').on('click', function() {
        console.log('Confirm button clicked, submitting form');
        // Enviar el formulario
        $('#ausentismoForm').submit();
    });
});

