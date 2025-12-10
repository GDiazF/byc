/**
 * Gestión de licencias médicas con DataTables (versión nueva con fetch).
 * 
 * Inicializa la tabla de licencias médicas con DataTables y maneja
 * la eliminación de licencias con confirmación mediante fetch API.
 */

$(document).ready(function() {
    console.log('=== Inicializando DataTable de Licencias Médicas ===');
    
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
                order: [[1, 'desc']], // Ordenar por fecha emisión descendente
                columnDefs: [
                    { orderable: false, targets: 5 } // Deshabilitar ordenamiento en acciones
                ],
                dom: '<"d-flex justify-content-between align-items-center mb-3"fl>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
                responsive: true,
            initComplete: function() {
                console.log('DataTable de licencias inicializado correctamente');
                // Mostrar la tabla solo cuando esté completamente inicializada
                $('#licenciasMedicasTable').css('visibility', 'visible');
            }
        });
});

// Eventos de gestión con Vanilla JS
document.addEventListener('DOMContentLoaded', function() {
    let licenciaToDelete = null;

    // Manejar clic en botón de eliminar
    document.querySelectorAll('.delete-licencia').forEach(button => {
        button.addEventListener('click', function() {
            licenciaToDelete = this.dataset.id;
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();
        });
    });

    // Manejar confirmación de eliminación
    const confirmButton = document.getElementById('confirmButton');
    if (confirmButton) {
        confirmButton.addEventListener('click', async function() {
            if (!licenciaToDelete) return;
            
            try {
                const response = await fetch(`/users/licencia_medica/${licenciaToDelete}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    }
                });
                
                const data = await response.json();
                
                // Cerrar modal de confirmación
                const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
                confirmModal.hide();
                
                if (data.status === 'success') {
                    // Mostrar modal de éxito
                    document.getElementById('successModalBody').textContent = data.message;
                    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
                    successModal.show();
                    
                    // Recargar después de 1.5 segundos
                    setTimeout(() => location.reload(), 1500);
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error al eliminar la licencia médica');
            }
        });
    }
});

