// Formulario de ausentismos (crear/editar)

$(document).ready(function() {
    console.log('Ausentismos form JS loaded');
    
    // Función para calcular la fecha de fin basándose en fecha inicio + días
    function calcularFechaFin() {
        // Obtener el valor del input hidden (formato ISO YYYY-MM-DD)
        // El date picker guarda el valor real en el input hidden con el mismo ID
        const fechaInicioInput = document.getElementById('id_fechaini');
        let fechaInicio = '';
        
        // Si es un input hidden (del date picker), obtener su valor directamente
        if (fechaInicioInput && fechaInicioInput.type === 'hidden') {
            fechaInicio = fechaInicioInput.value;
        } else {
            // Si no es hidden, obtener el valor normalmente
            fechaInicio = $('#id_fechaini').val();
        }
        
        const diasAusentismo = parseInt($('#id_dias_ausentismo').val());
        
        console.log('Calculando fecha fin:', {fechaInicio, diasAusentismo, inputType: fechaInicioInput ? fechaInicioInput.type : 'unknown'});
        
        if (fechaInicio && diasAusentismo && diasAusentismo > 0) {
            // El date picker siempre guarda en formato ISO (YYYY-MM-DD)
            // Parsear manualmente para evitar problemas de zona horaria
            const partes = fechaInicio.split('-');
            
            if (partes.length === 3) {
                const año = parseInt(partes[0]);
                const mes = parseInt(partes[1]) - 1; // Los meses en Date son 0-indexados
                const dia = parseInt(partes[2]);
                
                // Crear fecha usando constructor local (evita problemas de zona horaria)
                const fecha = new Date(año, mes, dia);
                
                // Agregar días (restar 1 porque incluye el día de inicio)
                // Ejemplo: Si inicia el 17/12/2025 y son 1 día, termina el 17/12/2025
                fecha.setDate(fecha.getDate() + diasAusentismo - 1);
                
                // Formatear fecha en formato chileno DD/MM/YYYY
                const day = String(fecha.getDate()).padStart(2, '0');
                const month = String(fecha.getMonth() + 1).padStart(2, '0');
                const year = fecha.getFullYear();
                const fechaFinFormateada = `${day}/${month}/${year}`;
                
                // También calcular en formato ISO para el input hidden
                const fechaFinISO = `${year}-${month}-${day}`;
                
                console.log('Fecha fin calculada:', {
                    formatoChileno: fechaFinFormateada,
                    formatoISO: fechaFinISO,
                    fechaObjeto: fecha
                });
                
                // Establecer la fecha de fin en el campo readonly (formato chileno DD/MM/YYYY)
                // El campo fechafin_display es readonly y muestra formato chileno
                $('#id_fechafin').val(fechaFinFormateada);
            }
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

