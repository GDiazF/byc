// Manejo de cargos según departamento

$(document).ready(function() {
    // Script para actualizar los cargos cuando cambia el departamento
    $('#id_depto_id').change(function() {
        const deptoId = $(this).val();
        const cargoSelect = $('#id_cargo_id');
        
        if (deptoId) {
            $.ajax({
                url: '/users/get_cargos/',
                data: {
                    'depto_id': deptoId
                },
                success: function(data) {
                    cargoSelect.empty();
                    cargoSelect.append($('<option>').text('elija una opción').attr('value', ''));
                    $.each(data, function(id, nombre) {
                        cargoSelect.append($('<option>').text(nombre).attr('value', id));
                    });
                }
            });
        } else {
            cargoSelect.empty().append($('<option>').text('elija una opción').attr('value', ''));
        }
    });
});

