$(document).ready(function() {
    // Función para crear un campo teléfono con prefijo fijo +56
    function crearCampoTelefonoConPrefijoFijo(selector) {
        // Seleccionar el campo original
        const inputOriginal = $(selector);
        if (!inputOriginal.length) return;
        
        // Verificar si ya existe un campo con prefijo para este input
        const existingContainer = inputOriginal.next('.input-group');
        if (existingContainer.length) {
            // Si ya existe, actualizar el valor visible con el valor actual
            const valorActual = inputOriginal.val().replace('+56', '');
            existingContainer.find('input.form-control').val(valorActual);
            return;
        }
        
        // Obtener información del campo original
        const valorActual = inputOriginal.val().replace('+56', '');
        const idOriginal = inputOriginal.attr('id');
        const placeholder = inputOriginal.attr('placeholder') || '';
        
        // Crear estructura de contenedor
        const contenedor = $('<div class="input-group"></div>');
        
        // Prefijo fijo
        const prefijo = $('<div class="input-group-prepend"></div>');
        const textoPrefix = $('<span class="input-group-text">+56</span>');
        prefijo.append(textoPrefix);
        
        // Nuevo campo para números
        const campoNumeros = $('<input type="text" class="form-control">');
        campoNumeros.attr('id', idOriginal + '_visible');
        campoNumeros.attr('placeholder', placeholder);
        campoNumeros.val(valorActual);
        
        // Construir estructura
        contenedor.append(prefijo);
        contenedor.append(campoNumeros);
        
        // Insertar la nueva estructura en la página
        inputOriginal.after(contenedor);
        inputOriginal.hide();
        
        // Si no tiene valor, establecer el prefijo
        if (!inputOriginal.val()) {
            inputOriginal.val('+56');
        }
        
        // Sincronizar datos
        campoNumeros.on('input', function() {
            // Eliminar caracteres no numéricos
            let valorNumerico = $(this).val().replace(/[^\d]/g, '');
            
            // Limitar a 9 dígitos (longitud típica para Chile)
            if (valorNumerico.length > 9) {
                valorNumerico = valorNumerico.substring(0, 9);
            }
            
            // Actualizar campos
            $(this).val(valorNumerico);
            inputOriginal.val('+56' + valorNumerico);
        });
    }
    
    // Aplicar a los campos de teléfono en el formulario de creación
    crearCampoTelefonoConPrefijoFijo('#id_telefono');
    
    // Para el modal de edición, limpiar cualquier instancia antigua y aplicar cuando se muestre
    $('#editModal').on('shown.bs.modal', function() {
        // Asegurarse de que el campo original esté visible antes de crear el nuevo campo
        $('#edit-telefono').show();
        
        // Eliminar contenedores antiguos si existen
        $('#edit-telefono').next('.input-group').remove();
        
        // Ahora crear el nuevo campo con prefijo
        crearCampoTelefonoConPrefijoFijo('#edit-telefono');
    });
    
    // Cuando se cierre el modal, eliminar el campo personalizado para evitar acumulación
    $('#editModal').on('hidden.bs.modal', function() {
        $('#edit-telefono').next('.input-group').remove();
        $('#edit-telefono').show();
    });
}); 