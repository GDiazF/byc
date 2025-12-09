// ============================================================================
// JAVASCRIPT PARA LA PÁGINA DE NOTIFICACIONES
// ============================================================================
// Este archivo maneja la lógica JavaScript para la página de notificaciones,
// incluyendo manejo de tabs, filtros, acciones de notificaciones, etc.
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Obtener token CSRF desde las cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrfToken = getCookie('csrftoken');
    
    // Manejar cambio de tabs
    const tabNoArchivadas = document.getElementById('tab-no-archivadas');
    const tabArchivadas = document.getElementById('tab-archivadas');
    
    if (tabNoArchivadas) {
        tabNoArchivadas.addEventListener('shown.bs.tab', function() {
            window.location.href = '/notificaciones/?archivada=false';
        });
    }
    
    if (tabArchivadas) {
        tabArchivadas.addEventListener('shown.bs.tab', function() {
            window.location.href = '/notificaciones/?archivada=true';
        });
    }
    
    // Aplicar filtros automáticamente al cambiar los selects (No Archivadas)
    const filtroLeida = document.getElementById('filtroLeida');
    const filtroCategoria = document.getElementById('filtroCategoria');
    
    if (filtroLeida) {
        filtroLeida.addEventListener('change', function() {
            document.getElementById('filtrosForm').submit();
        });
    }
    
    if (filtroCategoria) {
        filtroCategoria.addEventListener('change', function() {
            document.getElementById('filtrosForm').submit();
        });
    }
    
    // Aplicar filtros automáticamente al cambiar los selects (Archivadas)
    const filtroLeidaArchivadas = document.getElementById('filtroLeidaArchivadas');
    const filtroCategoriaArchivadas = document.getElementById('filtroCategoriaArchivadas');
    
    if (filtroLeidaArchivadas) {
        filtroLeidaArchivadas.addEventListener('change', function() {
            document.getElementById('filtrosFormArchivadas').submit();
        });
    }
    
    if (filtroCategoriaArchivadas) {
        filtroCategoriaArchivadas.addEventListener('change', function() {
            document.getElementById('filtrosFormArchivadas').submit();
        });
    }
    
    // Función para limpiar filtros (No Archivadas)
    window.limpiarFiltros = function() {
        document.getElementById('filtroLeida').value = '';
        document.getElementById('filtroCategoria').value = '';
        window.location.href = '/notificaciones/?archivada=false';
    };
    
    // Función para limpiar filtros (Archivadas)
    window.limpiarFiltrosArchivadas = function() {
        document.getElementById('filtroLeidaArchivadas').value = '';
        document.getElementById('filtroCategoriaArchivadas').value = '';
        window.location.href = '/notificaciones/?archivada=true';
    };
    
    // Función auxiliar para escapar HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Función para mostrar detalles de la notificación en un modal
    function mostrarDetalleNotificacion(notif) {
        const modal = document.getElementById('modalDetalleNotificacion');
        const modalBody = document.getElementById('modalDetalleNotificacionBody');
        
        if (!modal || !modalBody) return;
        
        // Construir el contenido del modal (solo lo esencial)
        let contenido = `
            <div class="mb-3">
                <h6 class="fw-bold mb-3">${escapeHtml(notif.titulo)}</h6>
                <div class="bg-light p-3 rounded">
                    <p class="mb-0 modal-message-text">${escapeHtml(notif.mensaje)}</p>
                </div>
            </div>
            <div class="text-muted small">
                <i class="bi bi-clock me-1"></i>${notif.fecha_creacion}
            </div>
        `;
        
        // Actualizar contenido del modal
        modalBody.innerHTML = contenido;
        
        // Mostrar el modal usando Bootstrap 5
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    // Marcar como leída
    document.querySelectorAll('.marcar-leida').forEach(btn => {
        btn.addEventListener('click', function() {
            const notifId = this.dataset.id;
            fetch(`/notificaciones/api/${notifId}/marcar-leida/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        });
    });
    
    // Archivar
    document.querySelectorAll('.archivar').forEach(btn => {
        btn.addEventListener('click', function() {
            const notifId = this.dataset.id;
            fetch(`/notificaciones/api/${notifId}/archivar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        });
    });
    
    // Desarchivar
    document.querySelectorAll('.desarchivar').forEach(btn => {
        btn.addEventListener('click', function() {
            const notifId = this.dataset.id;
            fetch(`/notificaciones/api/${notifId}/desarchivar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        });
    });
    
    // Marcar todas como leídas
    const btnMarcarTodasLeidas = document.getElementById('btnMarcarTodasLeidas');
    if (btnMarcarTodasLeidas) {
        btnMarcarTodasLeidas.addEventListener('click', function() {
            fetch('/notificaciones/api/marcar-todas-leidas/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        });
    }
    
    // Hacer las filas clickeables (excepto la columna de acciones)
    document.querySelectorAll('.notification-item').forEach(row => {
        row.addEventListener('click', function(e) {
            // No hacer nada si se hizo clic en un botón
            if (e.target.closest('button') || e.target.closest('.btn-group')) {
                return;
            }
            
            const notifId = this.dataset.notificacionId;
            const titulo = this.dataset.titulo;
            const mensaje = this.dataset.mensaje;
            const fecha = this.dataset.fecha;
            
            // Marcar como leída si no está leída
            const isUnread = this.classList.contains('unread');
            if (isUnread) {
                fetch(`/notificaciones/api/${notifId}/marcar-leida/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Actualizar visualmente la fila
                        this.classList.remove('unread');
                        const badge = this.querySelector('.badge');
                        if (badge) {
                            badge.className = 'badge bg-secondary';
                            badge.textContent = 'Leída';
                        }
                    }
                });
            }
            
            // Mostrar modal con detalles
            mostrarDetalleNotificacion({
                titulo: titulo,
                mensaje: mensaje,
                fecha_creacion: fecha
            });
        });
    });
});

