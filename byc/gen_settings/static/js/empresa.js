$(document).ready(function() {
    // Inicializar DataTable
    const table = $('#empresaTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Spanish.json"
        },
    });

    // Función para cargar comunas
    function cargarComunas(regionId, comunaId = null, isEdit = false) {
        // Determinar qué select de comuna usar
        const comunaSelect = isEdit ? $('#edit-comuna') : $('#id_comuna');
        
        // Limpiar y deshabilitar el select de comunas
        comunaSelect.empty();
        comunaSelect.append('<option value="">---------</option>');
        comunaSelect.prop('disabled', true);
        
        if (regionId) {
            $.ajax({
                url: '/gen_settings/ajax/load-comunas/',
                data: {
                    'region_id': regionId
                },
                success: function(data) {
                    comunaSelect.prop('disabled', false);
                    $.each(data, function(index, comuna) {
                        comunaSelect.append(
                            $('<option></option>').val(comuna.id).html(comuna.nombre)
                        );
                    });
                    if (comunaId) {
                        comunaSelect.val(comunaId);
                    }
                }
            });
        }
    }

    // Manejar el cambio de región para cargar comunas dinámicamente en el formulario de creación
    $('#id_region').on('change', function() {
        const regionId = $(this).val();
        cargarComunas(regionId, null, false);
    });

    // Manejar el cambio de región para cargar comunas dinámicamente en el formulario de edición
    $('#edit-region').on('change', function() {
        const regionId = $(this).val();
        cargarComunas(regionId, null, true);
    });

    // Manejar el formulario de creación
    $('#form-add').on('submit', function(e) {
        e.preventDefault();
        $.ajax({
            url: '/gen_settings/empresas/crear/',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al crear la empresa');
                }
            }
        });
    });

    // Manejar el formulario de edición
    $('#form-edit').on('submit', function(e) {
        e.preventDefault();
        const id = $('#edit-id').val();
        $.ajax({
            url: `/gen_settings/empresas/${id}/editar/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                'rut': $('#edit-rut').val(),
                'dv': $('#edit-dv').val(),
                'razonSocial': $('#edit-razonSocial').val(),
                'nomFantasia': $('#edit-nomFantasia').val(),
                'giro': $('#edit-giro').val(),
                'direccion': $('#edit-direccion').val(),
                'telefono': $('#edit-telefono').val(),
                'email': $('#edit-email').val(),
                'region': $('#edit-region').val(),
                'comuna': $('#edit-comuna').val()
            },
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    alert('Error al editar la empresa: ' + (response.errors || 'Error desconocido'));
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
            url: `/gen_settings/empresas/${id}/eliminar/`,
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
                    alert('Error al eliminar la empresa: ' + (response.error || 'Error desconocido'));
                }
            },
            error: function(xhr, status, error) {
                alert('Error al eliminar la empresa: ' + error);
            }
        });
    });

    // Configurar los botones de edición
    $('.edit-btn').on('click', function() {
        const id = $(this).data('id');
        const rut = $(this).data('rut');
        const dv = $(this).data('dv');
        const razonSocial = $(this).data('razonsocial');
        const nomFantasia = $(this).data('nomfantasia');
        const giro = $(this).data('giro');
        const direccion = $(this).data('direccion');
        const telefono = $(this).data('telefono');
        const email = $(this).data('email');
        const region = $(this).data('region');
        const comuna = $(this).data('comuna');

        $('#edit-id').val(id);
        $('#edit-rut').val(rut);
        $('#edit-dv').val(dv);
        $('#edit-razonSocial').val(razonSocial);
        $('#edit-nomFantasia').val(nomFantasia);
        $('#edit-giro').val(giro);
        $('#edit-direccion').val(direccion);
        $('#edit-telefono').val(telefono);
        $('#edit-email').val(email);
        $('#edit-region').val(region);
        
        // Cargar comunas y seleccionar la comuna correcta
        cargarComunas(region, comuna, true);
    });

    // Configurar los botones de eliminación
    $('.delete-btn').on('click', function() {
        const id = $(this).data('id');
        $('#delete-id').val(id);
    });

    // Trigger inicial para cargar las comunas si hay una región seleccionada en el formulario de creación
    const regionSeleccionada = $('#id_region').val();
    if (regionSeleccionada) {
        cargarComunas(regionSeleccionada, null, false);
    }
}); 