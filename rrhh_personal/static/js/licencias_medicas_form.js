// Formulario de licencias médicas (crear)

$(document).ready(function() {
    // Manejar clic en botón de guardar
    $('#submitButton').on('click', function(e) {
        e.preventDefault();
        
        // Validar formulario
        const form = document.getElementById('licenciaForm');
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Mostrar modal de confirmación
        $('#confirmModal').modal('show');
    });

    // Manejar confirmación de guardado
    $('#confirmButton').on('click', function() {
        // Enviar el formulario
        $('#licenciaForm').submit();
    });
});

