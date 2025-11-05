// Manejo de listado de licencias médicas

$(document).ready(function() {
    // Verificar si la tabla existe (solo se renderiza si hay datos)
    if ($('#licenciasMedicasTable').length === 0) {
        console.log('No hay tabla para inicializar (lista vacía).');
        return; // Salir si no hay tabla
    }
    
    // Inicializar DataTable
    const table = $('#licenciasMedicasTable').DataTable({
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
            pageLength: 25,
            order: [[1, 'desc']], // Ordenar por fecha de emisión descendente
            columnDefs: [
                { orderable: false, targets: 6 } // Deshabilitar ordenamiento en acciones
            ],
            dom: '<"d-flex justify-content-between align-items-center mb-3"fl>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
            responsive: true,
            initComplete: function() {
                console.log('DataTable de licencias inicializado correctamente');
                // Mostrar la tabla solo cuando esté completamente inicializada
                $('#licenciasMedicasTable').css('visibility', 'visible');
            }
        });

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

