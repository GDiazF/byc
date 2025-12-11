/**
 * JavaScript para el widget de checkboxes de notificaciones
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        /**
         * Actualiza el contador de notificaciones seleccionadas.
         * 
         * Cuenta cuántos checkboxes de notificaciones están marcados y actualiza
         * el elemento que muestra el contador en la interfaz.
         */
        function updateSelectedCount() {
            var selected = $('.notificacion-checkbox:checked').length;
            var total = $('.notificacion-checkbox').length;
            var countElement = $('#notificaciones-seleccionadas-count');
            
            if (countElement.length) {
                countElement.text(selected);
            }
        }
        
        // Actualizar contador cuando cambie un checkbox
        $(document).on('change', '.notificacion-checkbox', function() {
            updateSelectedCount();
        });
        
        // Inicializar contador al cargar
        updateSelectedCount();
    });
    
})(django.jQuery);

