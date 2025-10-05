$(document).ready(function() {
    // Inicializar DataTable
    const table = $('#regionTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Spanish.json"
        }
    });

    // Manejar el formulario de creación
    $('#form-add').on('submit', function(e) {
        e.preventDefault();
        $.ajax({
            url: '/gen_settings/regiones/crear/',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al crear la región');
                }
            }
        });
    });

    // Manejar el formulario de edición
    $('#form-edit').on('submit', function(e) {
        e.preventDefault();
        const id = $('#edit-id').val();
        const nombre = $('#edit-nombre').val();
        
        $.ajax({
            url: `/gen_settings/regiones/${id}/editar/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                'nombre': nombre
            },
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al editar la región: ' + (response.errors || 'Error desconocido'));
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
            url: `/gen_settings/regiones/${id}/eliminar/`,
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
                    alert('Error al eliminar la región: ' + (response.error || 'Error desconocido'));
                }
            },
            error: function(xhr, status, error) {
                alert('Error al eliminar la región: ' + error);
            }
        });
    });

    // Configurar los botones de edición
    $('.edit-btn').on('click', function() {
        const id = $(this).data('id');
        const nombre = $(this).data('nombre');
        $('#edit-id').val(id);
        $('#edit-nombre').val(nombre);
    });

    // Configurar los botones de eliminación
    $('.delete-btn').on('click', function() {
        const id = $(this).data('id');
        $('#delete-id').val(id);
    });
});