/**
 * Gestión del formulario de licencias médicas (crear/editar).
 * 
 * Calcula automáticamente la fecha de fin basándose en la fecha de emisión
 * y los días de licencia. Valida el formulario antes de enviarlo.
 */

console.log('=== Archivo licencias_medicas.js cargado ===');

/**
 * Calcula la fecha de fin basándose en la fecha de emisión y los días de licencia.
 * 
 * La fecha de fin se calcula como: fecha_emision + (días - 1)
 * Se formatea en formato DD-MM-YYYY.
 */
function calcularFechaFin() {
    const fechaEmision = document.getElementById('id_fechaEmision');
    const diasLicencia = document.getElementById('id_dias_licencia');
    const fechaFinElement = document.getElementById('fecha_fin_licencia');
    
    if (fechaEmision && diasLicencia && fechaFinElement) {
        const fechaEmisionValue = fechaEmision.value;
        const diasLicenciaValue = parseInt(diasLicencia.value);
        
        if (fechaEmisionValue && diasLicenciaValue) {
            const partes = fechaEmisionValue.split('-');
            // yyyy-mm-dd
            const fecha = new Date(partes[0], partes[1] - 1, partes[2]);
            fecha.setDate(fecha.getDate() + diasLicenciaValue - 1);
            const yyyy = fecha.getFullYear();
            const mm = String(fecha.getMonth() + 1).padStart(2, '0');
            const dd = String(fecha.getDate()).padStart(2, '0');
            fechaFinElement.value = `${dd}-${mm}-${yyyy}`;
        } else {
            fechaFinElement.value = '';
        }
    }
}

// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM Content Loaded ===');
    
    // Verificar si jQuery está disponible
    if (typeof jQuery !== 'undefined') {
        console.log('jQuery está disponible, versión:', jQuery.fn.jquery);
    } else {
        console.error('jQuery NO está disponible');
    }
    
    // Eventos para calcular fecha fin
    const fechaEmision = document.getElementById('id_fechaEmision');
    const diasLicencia = document.getElementById('id_dias_licencia');
    
    if (fechaEmision) {
        fechaEmision.addEventListener('change', calcularFechaFin);
        console.log('Event listener agregado a fechaEmision');
    }
    
    if (diasLicencia) {
        diasLicencia.addEventListener('input', calcularFechaFin);
        console.log('Event listener agregado a diasLicencia');
    }
    
    // Calcular fecha fin al cargar la página
    calcularFechaFin();
    
    // Verificar si el botón existe
    const submitButton = document.getElementById('submitButton');
    console.log('Submit button encontrado:', submitButton);
    
    const confirmButton = document.getElementById('confirmButton');
    console.log('Confirm button encontrado:', confirmButton);
    
    // Usar jQuery si está disponible
    if (typeof jQuery !== 'undefined') {
        jQuery(document).ready(function($) {
            console.log('=== jQuery ready ===');
            
            // Manejar clic en botón de envío (crear/editar)
            $('#submitButton').on('click', function(e) {
                e.preventDefault();
                console.log('>>> Submit button clicked');
                
                // Validar formulario
                const form = document.getElementById('licenciaForm');
                console.log('Form found:', form);
                console.log('Form validity:', form ? form.checkValidity() : 'N/A');
                
                if (form && !form.checkValidity()) {
                    form.classList.add('was-validated');
                    console.log('Form is INVALID, showing validation messages');
                    return;
                }
                
                console.log('Form is VALID, showing confirmation modal');
                // Mostrar modal de confirmación
                $('#confirmModal').modal('show');
            });

            // Manejar confirmación de guardado/actualización
            $('#confirmButton').on('click', function() {
                console.log('>>> Confirm button clicked, submitting form');
                // Enviar el formulario
                $('#licenciaForm').submit();
            });
        });
    } else {
        console.error('No se puede usar jQuery - no disponible');
    }
}); 