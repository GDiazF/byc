// Gestión de ausentismos

document.addEventListener('DOMContentLoaded', function() {
    let ausentismoToDelete = null;

    // Manejar envío del formulario de ausentismo
    const ausentismoForm = document.getElementById('ausentismoForm');
    if (ausentismoForm) {
        const personalId = ausentismoForm.getAttribute('data-personal-id');
        
        ausentismoForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const ausentismoId = formData.get('ausentismo_id');
            const url = ausentismoId ? 
                `/users/personal/${personalId}/ausentismos/${ausentismoId}/update/` :
                `/users/personal/${personalId}/ausentismos/create/`;
            
            const data = {
                tipo_ausentismo_id: formData.get('tipo_ausentismo'),
                fecha_inicio: formData.get('fecha_inicio'),
                fecha_fin: formData.get('fecha_fin'),
                observaciones: formData.get('observaciones')
            };
            
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                // Cerrar modal del formulario
                const formModal = bootstrap.Modal.getInstance(document.getElementById('addAusentismoModal'));
                formModal.hide();
                
                if (result.status === 'success') {
                    showMessage('Éxito', result.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showMessage('Error', result.message, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('Error', 'Error al guardar el ausentismo', 'error');
            }
        });
    }

    // Editar ausentismo
    document.querySelectorAll('.edit-ausentismo').forEach(btn => {
        btn.addEventListener('click', function() {
            document.getElementById('ausentismoModalTitle').textContent = 'Editar Ausentismo';
            document.getElementById('ausentismoId').value = this.dataset.id;
            document.getElementById('tipoAusentismo').value = this.dataset.tipo;
            document.getElementById('fechaInicio').value = this.dataset.fechaini;
            document.getElementById('fechaFin').value = this.dataset.fechafin;
            document.getElementById('observaciones').value = this.dataset.observacion || '';
            document.getElementById('btnEliminar').style.display = 'inline-block';
            
            const modal = new bootstrap.Modal(document.getElementById('addAusentismoModal'));
            modal.show();
        });
    });

    // Eliminar desde modal de edición
    const btnEliminar = document.getElementById('btnEliminar');
    if (btnEliminar) {
        btnEliminar.addEventListener('click', function() {
            const ausentismoId = document.getElementById('ausentismoId').value;
            if (ausentismoId) {
                const formModal = bootstrap.Modal.getInstance(document.getElementById('addAusentismoModal'));
                formModal.hide();
                
                ausentismoToDelete = ausentismoId;
                const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
                confirmModal.show();
            }
        });
    }

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
                    showMessage('Éxito', data.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showMessage('Error', data.message, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('Error', 'Error al eliminar el ausentismo', 'error');
            }
        });
    }

    // Al abrir modal para nuevo, limpiar formulario
    const addAusentismoModal = document.getElementById('addAusentismoModal');
    if (addAusentismoModal) {
        addAusentismoModal.addEventListener('show.bs.modal', function(e) {
            if (!e.relatedTarget || !e.relatedTarget.classList.contains('edit-ausentismo')) {
                document.getElementById('ausentismoModalTitle').textContent = 'Nuevo Ausentismo';
                document.getElementById('ausentismoForm').reset();
                document.getElementById('ausentismoId').value = '';
                const btnElim = document.getElementById('btnEliminar');
                if (btnElim) {
                    btnElim.style.display = 'none';
                }
            }
        });
    }
});

function showMessage(title, message, type) {
    const modal = new bootstrap.Modal(document.getElementById('messageModal'));
    const header = document.getElementById('messageModalHeader');
    const titleEl = document.getElementById('messageModalTitle');
    const body = document.getElementById('messageModalBody');
    
    if (type === 'success') {
        header.className = 'modal-header bg-success text-white';
    } else {
        header.className = 'modal-header bg-danger text-white';
    }
    
    titleEl.textContent = title;
    body.textContent = message;
    modal.show();
}

