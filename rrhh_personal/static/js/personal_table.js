// Esperar a que el documento esté listo
$(document).ready(function() {
    console.log('Inicializando DataTable con opciones extendidas...');
    
    // Verificar si la tabla existe (solo se renderiza si hay datos)
    if ($('#personalTable').length === 0) {
        console.log('No hay tabla para inicializar (lista vacía).');
        return; // Salir si no hay tabla
    }
    
    // Inicializar DataTable
    const table = $('#personalTable').DataTable({
        language: {
            "lengthMenu": "Mostrar _MENU_ registros",
            "zeroRecords": "No se encontraron registros",
            "info": "Mostrando _START_ a _END_ de _TOTAL_ registros",
            "infoEmpty": "Mostrando 0 a 0 de 0 registros",
            "infoFiltered": "(filtrado de _MAX_ registros totales)",
            "search": "Buscar:",
            "paginate": {
                "first": "Primero",
                "last": "Último",
                "next": "Siguiente",
                "previous": "Anterior"
            }
        },
        lengthMenu: [[5, 10, 25, 50, 100, 500, 1000, -1], ["5", "10", "25", "50", "100", "500", "1000", "Todos"]],
        pageLength: 10,
        order: [[1, 'asc']],
        columnDefs: [
            {
                targets: [-1, -2], // Columnas de acciones y estado
                orderable: false,
                searchable: false
            }
        ],
        dom: '<"d-flex justify-content-between align-items-center mb-3"lf>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
        lengthChange: true,
        paging: true,
        info: true,
        initComplete: function() {
            console.log('DataTable inicializado correctamente');
        }
    });
    
    // Forzar el texto "Todos" en el dropdown
    setTimeout(function() {
        $('.dataTables_length select option[value="-1"]').text('Todos');
    }, 100);

    // Manejar el filtro de empresa
    $('#filtroEmpresa').on('change', function() {
        const empresaSeleccionada = $(this).val();
        table.column(4).search(empresaSeleccionada).draw();
    });

    // Variables para el manejo del toggle de estado
    let currentToggle = null;
    let originalState = false;
    let changeConfirmed = false;

    // Manejar el click en el toggle de estado
    $('.toggle-status').on('change', function(e) {
        e.preventDefault();
        currentToggle = $(this);
        originalState = !currentToggle.prop('checked');
        changeConfirmed = false;
        
        // NO modificar el contenido del modal - ya está definido correctamente en el HTML
        // El modal de table_personal.html tiene la advertencia de DESACTIVAR
        // El modal de personal_desactivado.html tiene la confirmación de ACTIVAR
        
        // Mostrar modal
        $('#confirmModal').modal('show');
        
        // Revertir el cambio del toggle hasta que se confirme
        currentToggle.prop('checked', originalState);
    });

    // Manejar la confirmación del modal
    $('#confirmButton').on('click', function() {
        if (currentToggle) {
            const personalId = currentToggle.data('id');
            const nuevoEstado = !originalState;

            // Llamada AJAX para actualizar el estado (nueva URL)
            $.ajax({
                url: '/users/personal/toggle-activo/',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    personal_id: personalId
                }),
                headers: {
                    'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // Marcar que el cambio fue confirmado
                        changeConfirmed = true;
                        
                        // Cerrar el modal de confirmación
                        $('#confirmModal').modal('hide');
                        
                        // Mostrar mensaje de éxito
                        const accion = response.activo ? 'activado' : 'desactivado';
                        $('#successModalBody').html(`
                            <i class="bi bi-check-circle me-2"></i>Personal ${accion} correctamente
                        `);
                        $('#successModal').modal('show');
                        
                        // Redirigir después de mostrar el mensaje
                        setTimeout(function() {
                            window.location.replace(window.location.pathname + '?updated=' + Date.now());
                        }, 1500);
                    } else {
                        $('#confirmModal').modal('hide');
                        alert('Error: ' + (response.message || 'Error al cambiar el estado del personal'));
                        currentToggle.prop('checked', originalState);
                    }
                },
                error: function(xhr) {
                    $('#confirmModal').modal('hide');
                    const errorMsg = xhr.responseJSON && xhr.responseJSON.message 
                        ? xhr.responseJSON.message 
                        : 'Error al cambiar el estado del personal';
                    alert('Error: ' + errorMsg);
                    currentToggle.prop('checked', originalState);
                }
            });
        }
    });

    // Limpiar variables cuando se cierra el modal de confirmación
    $('#confirmModal').on('hidden.bs.modal', function() {
        if (currentToggle && !changeConfirmed) {
            currentToggle.prop('checked', originalState);
        }
        currentToggle = null;
        originalState = false;
        changeConfirmed = false;
    });
}); 