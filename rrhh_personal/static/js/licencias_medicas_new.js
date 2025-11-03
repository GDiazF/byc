// Manejo de licencias médicas (versión nueva con fetch)

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

