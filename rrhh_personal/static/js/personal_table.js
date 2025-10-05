// Esperar a que el documento esté listo
$(document).ready(function() {
    // Inicializar DataTable
    const table = $('#personalTable').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
        },
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
        lengthMenu: [[5, 10, 25, 50], [5, 10, 25, 50]]
    });

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
        
        // Actualizar texto del modal según el estado
        const nuevoEstado = currentToggle.prop('checked') ? 'activar' : 'desactivar';
        $('#confirmModalBody').text(`¿Está seguro que desea ${nuevoEstado} a este personal?`);
        
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

            // Llamada AJAX para actualizar el estado
            $.ajax({
                url: `/users/personal/${personalId}/toggle-status/`,
                type: 'POST',
                data: {
                    activo: nuevoEstado,
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        // Marcar que el cambio fue confirmado
                        changeConfirmed = true;
                        // Actualizar el toggle al nuevo estado
                        currentToggle.prop('checked', nuevoEstado);
                        
                        // Cerrar el modal de confirmación
                        $('#confirmModal').modal('hide');
                        
                        // Mostrar mensaje de éxito en el modal
                        const mensaje = nuevoEstado ? 'activado' : 'desactivado';
                        $('#successModalBody').text(`El personal ha sido ${mensaje} exitosamente.`);
                        $('#successModal').modal('show');
                    } else {
                        $('#confirmModal').modal('hide');
                        alert('Error al cambiar el estado del personal');
                        currentToggle.prop('checked', originalState);
                    }
                },
                error: function() {
                    $('#confirmModal').modal('hide');
                    alert('Error al cambiar el estado del personal');
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