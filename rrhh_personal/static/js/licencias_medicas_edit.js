// Formulario de edición de licencias médicas

$(document).ready(function() {
    // Variable para almacenar el ID de la licencia
    let currentLicenciaId = null;
    
    // Manejar clic en botón de eliminar archivo
    $('#deleteFileBtn').on('click', function() {
        currentLicenciaId = $(this).data('licencia-id');
        // Mostrar modal de confirmación
        $('#deleteFileModal').modal('show');
    });

    // Manejar confirmación de eliminación de archivo
    $('#confirmDeleteFile').on('click', function() {
        if (currentLicenciaId) {
            const url = `/users/licencia_medica/${currentLicenciaId}/delete_archivo/`;
            
            $.ajax({
                url: url,
                type: 'DELETE',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // Cerrar el modal
                        $('#deleteFileModal').modal('hide');
                        // Ocultar la sección del documento actual
                        $('.mb-3.p-3.border.rounded.bg-light').hide();
                        // Mostrar la sección de subida de archivo
                        $('#fileUploadSection').show();
                        // Mostrar mensaje de éxito
                        $('#successModalBody').text('Documento eliminado exitosamente. Ahora puede subir un nuevo documento.');
                        $('#successModal').modal('show');
                    } else {
                        alert('Error: ' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    let errorMessage = 'Error desconocido';
                    try {
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMessage = xhr.responseJSON.message;
                        } else if (xhr.responseText) {
                            errorMessage = xhr.responseText;
                        } else if (xhr.status === 404) {
                            errorMessage = 'No se encontró la licencia médica';
                        } else if (xhr.status === 403) {
                            errorMessage = 'No tiene permisos para realizar esta acción';
                        } else if (xhr.status === 500) {
                            errorMessage = 'Error interno del servidor';
                        }
                    } catch (e) {
                        console.error('Error parsing response:', e);
                    }
                    alert('Error al eliminar el documento: ' + errorMessage);
                }
            });
        } else {
            alert('Error: No se pudo identificar la licencia médica');
        }
    });

    // Manejar clic en botón de actualizar
    $('#submitButton').on('click', function(e) {
        e.preventDefault();
        
        // Validar formulario
        const form = document.getElementById('licenciaForm');
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Mostrar modal de confirmación
        $('#confirmModal').modal('show');
    });

    // Manejar confirmación de actualización
    $('#confirmButton').on('click', function() {
        // Enviar el formulario
        $('#licenciaForm').submit();
    });
});

