// Gestión de ausentismos

// Inicializar DataTable con jQuery
$(document).ready(function() {
    console.log('=== Inicializando DataTable de Ausentismos ===');
    
    // Verificar si la tabla existe (solo se renderiza si hay datos)
    if ($('#ausentismosTable').length === 0) {
        console.log('No hay tabla para inicializar (lista vacía).');
        return; // Salir si no hay tabla
    }
    
    // Inicializar DataTable
    const table = $('#ausentismosTable').DataTable({
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
                order: [[1, 'desc']], // Ordenar por fecha inicio descendente
                columnDefs: [
                    { orderable: false, targets: 6 } // Deshabilitar ordenamiento en acciones
                ],
                dom: '<"d-flex justify-content-between align-items-center mb-3"fl>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
                responsive: true,
                initComplete: function() {
                    console.log('✓ DataTable inicializado exitosamente');
                    // Mostrar la tabla solo cuando esté completamente inicializada
                    $('#ausentismosTable').css('visibility', 'visible');
                }
        });
});

// Eventos de gestión con Vanilla JS
document.addEventListener('DOMContentLoaded', function() {
    let ausentismoToDelete = null;

    // Eliminar desde botón de tabla
    document.querySelectorAll('.delete-ausentismo').forEach(btn => {
        btn.addEventListener('click', function() {
            ausentismoToDelete = this.dataset.id;
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();
        });
    });

    // Confirmar eliminación
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async function() {
            if (!ausentismoToDelete) return;
            
            try {
                const response = await fetch(`/users/personal/ausentismos/${ausentismoToDelete}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    }
                });
                
                const data = await response.json();
                
                const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
                confirmModal.hide();
                
                if (data.status === 'success') {
                    // Recargar la página
                    location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error al eliminar el ausentismo');
            }
        });
    }
});

