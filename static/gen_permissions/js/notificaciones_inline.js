/**
 * Script para evitar duplicados en el inline de notificaciones.
 * Oculta las opciones ya seleccionadas en otros dropdowns del mismo formulario.
 */

(function() {
    'use strict';
    
    // Esperar a que jQuery este disponible
    function inicializar() {
        var $ = django.jQuery || jQuery;
        
        /**
         * Actualiza las opciones disponibles en todos los selects de notificaciones.
         * 
         * Oculta las opciones que ya están seleccionadas en otros selects del mismo
         * formulario para evitar duplicados en el inline de notificaciones.
         */
        function actualizarOpcionesNotificaciones() {
            // Buscar todos los selects de tipo_notificacion en el inline
            // Probar multiples selectores para asegurar compatibilidad
            var selects = $('select[id*="tipo_notificacion"]:not([id*="__prefix__"])');
            
            if (selects.length === 0) {
                // Intentar con selector por name
                selects = $('select[name*="tipo_notificacion"]:not([name*="__prefix__"])');
            }
            
            if (selects.length === 0) {
                // ultimo intento: buscar en el grupo del inline
                selects = $('.inline-related select').filter(function() {
                    var name = $(this).attr('name') || '';
                    var id = $(this).attr('id') || '';
                    return (name.indexOf('tipo_notificacion') > -1 || id.indexOf('tipo_notificacion') > -1) && 
                           name.indexOf('__prefix__') === -1;
                });
            }
            
            // Obtener todos los valores seleccionados
            var valoresSeleccionados = [];
            selects.each(function() {
                var valor = $(this).val();
                if (valor && valor !== '') {
                    valoresSeleccionados.push(valor);
                }
            });
            
            // Para cada select, ocultar las opciones que ya estan seleccionadas en otros selects
            selects.each(function() {
                var selectActual = $(this);
                var valorActual = selectActual.val();
                
                // Restaurar todas las opciones primero (mostrarlas)
                selectActual.find('option').show();
                
                // Ocultar las opciones que estan seleccionadas en otros selects
                valoresSeleccionados.forEach(function(valor) {
                    if (valor !== valorActual) {
                        selectActual.find('option[value="' + valor + '"]').hide();
                    }
                });
            });
        }
        
        // Ejecutar al cargar la pagina
        $(document).ready(function() {
            setTimeout(actualizarOpcionesNotificaciones, 500);
        });
        
        // Ejecutar cuando cambie algun select (usar selector mas amplio)
        $(document).on('change', 'select[id*="tipo_notificacion"], select[name*="tipo_notificacion"]', function() {
            actualizarOpcionesNotificaciones();
        });
        
        // Ejecutar cuando se agregue una nueva fila (inline)
        $(document).on('click', '.add-row a, .inline-related .add-row a', function() {
            setTimeout(actualizarOpcionesNotificaciones, 200);
        });
        
        // Ejecutar cuando se elimine una fila
        $(document).on('click', '.inline-deletelink', function() {
            setTimeout(actualizarOpcionesNotificaciones, 200);
        });
        
        // Para Django 4.x+ que usa formset:added
        $(document).on('formset:added', function() {
            setTimeout(actualizarOpcionesNotificaciones, 200);
        });
        
        // Para Django 4.x+ que usa formset:removed
        $(document).on('formset:removed', function() {
            setTimeout(actualizarOpcionesNotificaciones, 200);
        });
    }
    
    // Intentar inicializar cuando el DOM este listo
    if (typeof django !== 'undefined' && django.jQuery) {
        inicializar();
    } else if (typeof jQuery !== 'undefined') {
        inicializar();
    } else {
        // Esperar a que jQuery este disponible
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(inicializar, 500);
        });
    }
})();


