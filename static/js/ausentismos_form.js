// Formulario de ausentismos (crear/editar)

$(document).ready(function() {
    console.log('Ausentismos form JS loaded');
    
    // Función para calcular la fecha de fin basándose en fecha inicio + días
    function calcularFechaFin() {
        const fechaInicio = $('#id_fechaini').val();
        const diasAusentismo = parseInt($('#id_dias_ausentismo').val());
        
        console.log('Calculando fecha fin:', {fechaInicio, diasAusentismo});
        
        if (fechaInicio && diasAusentismo && diasAusentismo > 0) {
            // Parsear fecha manualmente para evitar problemas de zona horaria
            // El formato puede ser YYYY-MM-DD o DD/MM/YYYY
            let fecha;
            if (fechaInicio.includes('/')) {
                // Formato DD/MM/YYYY
                const partes = fechaInicio.split('/');
                fecha = new Date(parseInt(partes[2]), parseInt(partes[1]) - 1, parseInt(partes[0]));
            } else {
                // Formato YYYY-MM-DD
                const partes = fechaInicio.split('-');
                fecha = new Date(parseInt(partes[0]), parseInt(partes[1]) - 1, parseInt(partes[2]));
            }
            
            // Agregar días (restar 1 porque incluye el día de inicio)
            // Ejemplo: Si inicia el 17/12/2025 y son 1 día, termina el 17/12/2025
            fecha.setDate(fecha.getDate() + diasAusentismo - 1);
            
            // Formatear fecha en formato chileno DD/MM/YYYY
            const day = String(fecha.getDate()).padStart(2, '0');
            const month = String(fecha.getMonth() + 1).padStart(2, '0');
            const year = fecha.getFullYear();
            const fechaFinFormateada = `${day}/${month}/${year}`;
            
            console.log('Fecha fin calculada (formato chileno):', fechaFinFormateada);
            
            // Establecer la fecha de fin en el campo con formato chileno
            $('#id_fechafin').val(fechaFinFormateada);
        } else {
            $('#id_fechafin').val('');
        }
    }
    
    // Calcular fecha fin cuando cambie la fecha de inicio o los días
    $('#id_fechaini, #id_dias_ausentismo').on('change input', function() {
        calcularFechaFin();
    });
    
    // Calcular fecha fin al cargar la página (para modo edición)
    calcularFechaFin();
    
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

