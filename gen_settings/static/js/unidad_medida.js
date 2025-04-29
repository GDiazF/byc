$(document).ready(function() {
    // Inicializar DataTable
    const table = $('#unidadMedidaTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Spanish.json"
        }
    });

    // Manejar el formulario de creación
    $('#form-add').on('submit', function(e) {
        e.preventDefault();
        $.ajax({
            url: '/gen_settings/unidades-medida/crear/',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al crear la unidad de medida');
                }
            }
        });
    });

    // Manejar el formulario de edición
    $('#form-edit').on('submit', function(e) {
        e.preventDefault();
        const id = $('#edit-id').val();
        $.ajax({
            url: `/gen_settings/unidades-medida/${id}/editar/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                'codigo': $('#edit-codigo').val(),
                'descripcion': $('#edit-descripcion').val()
            },
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al editar la unidad de medida: ' + (response.errors || 'Error desconocido'));
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
            url: `/gen_settings/unidades-medida/${id}/eliminar/`,
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
                    alert('Error al eliminar la unidad de medida: ' + (response.error || 'Error desconocido'));
                }
            },
            error: function(xhr, status, error) {
                alert('Error al eliminar la unidad de medida: ' + error);
            }
        });
    });

    // Configurar los botones de edición
    $('.edit-btn').on('click', function() {
        const id = $(this).data('id');
        const codigo = $(this).data('codigo');
        const descripcion = $(this).data('descripcion');
        $('#edit-id').val(id);
        $('#edit-codigo').val(codigo);
        $('#edit-descripcion').val(descripcion);
    });

    // Configurar los botones de eliminación
    $('.delete-btn').on('click', function() {
        const id = $(this).data('id');
        $('#delete-id').val(id);
    });
}); 