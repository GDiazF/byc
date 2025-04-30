$(document).ready(function() {
    // Inicializar DataTable
    const table = $('#comunaTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Spanish.json"
        },
    });

    // Manejar el formulario de creación
    $('#form-add').on('submit', function(e) {
        e.preventDefault();
        $.ajax({
            url: '/gen_settings/comunas/crear/',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al crear la comuna');
                }
            }
        });
    });

    // Manejar el formulario de edición
    $('#form-edit').on('submit', function(e) {
        e.preventDefault();
        const id = $('#edit-id').val();
        $.ajax({
            url: `/gen_settings/comunas/${id}/editar/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                'nombre': $('#edit-nombre').val(),
                'region': $('#edit-region').val()
            },
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al editar la comuna: ' + (response.errors || 'Error desconocido'));
                }
            },
            error: function() {
                alert('Error al comunicarse con el servidor');
            }
        });
    });

    // Manejar la eliminación
    $('#confirm-delete').on('click', function() {
        const id = $('#delete-id').val();
        $.ajax({
            url: `/gen_settings/comunas/${id}/eliminar/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    $('#deleteModal').modal('hide');
                    setTimeout(function() {
                        location.reload();
                    }, 500);
                } else {
                    alert('Error al eliminar la comuna: ' + (response.error || 'Error desconocido'));
                }
            },
            error: function(xhr, status, error) {
                alert('Error al eliminar la comuna: ' + error);
            }
        });
    });

    // Configurar los botones de edición
    $('.edit-btn').on('click', function() {
        const id = $(this).data('id');
        const nombre = $(this).data('nombre');
        const region = $(this).data('region');
        $('#edit-id').val(id);
        $('#edit-nombre').val(nombre);
        $('#edit-region').val(region);
    });

    // Configurar los botones de eliminación
    $('.delete-btn').on('click', function() {
        const id = $(this).data('id');
        $('#delete-id').val(id);
    });
}); 