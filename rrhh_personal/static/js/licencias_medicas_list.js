// Manejo de listado de licencias médicas

$(document).ready(function() {
    // Inicializar DataTable si existe
    const table = $('#licenciasMedicasTable');
    if (table.length) {
        table.DataTable({
            paging: false,
            searching: false,
            info: false,
            order: [[2, 'desc']] // Ordenar por fecha de emisión descendente
        });
    }

    // Variables para el manejo de eliminación
    let licenciaToDelete = null;

    // Manejar clic en botón de eliminar
    $('.delete-licencia').on('click', function(e) {
        e.preventDefault();
        licenciaToDelete = $(this).data('id');
        
        // Mostrar modal de confirmación
        $('#confirmModal').modal('show');
    });

    // Manejar confirmación de eliminación
    $('#confirmButton').on('click', function() {
        if (licenciaToDelete) {
            // Llamada AJAX para eliminar la licencia
            $.ajax({
                url: `/users/licencia_medica/${licenciaToDelete}/delete/`,
                type: 'DELETE',
                headers: {
                    'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // Cerrar el modal de confirmación
                        $('#confirmModal').modal('hide');
                        
                        // Mostrar mensaje de éxito
                        $('#successModalBody').text(response.message);
                        $('#successModal').modal('show');
                        
                        // Recargar la página después de un breve delay
                        setTimeout(function() {
                            location.reload();
                        }, 1500);
                    } else {
                        $('#confirmModal').modal('hide');
                        alert('Error al eliminar la licencia médica: ' + response.message);
                    }
                },
                error: function() {
                    $('#confirmModal').modal('hide');
                    alert('Error al eliminar la licencia médica');
                }
            });
        }
    });
});

