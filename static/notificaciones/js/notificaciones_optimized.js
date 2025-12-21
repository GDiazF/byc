/**
 * ============================================================================
 * JAVASCRIPT OPTIMIZADO PARA NOTIFICACIONES (SIN SSE, LAZY LOADING)
 * ============================================================================
 * Versión optimizada que:
 * - NO usa SSE (Server-Sent Events)
 * - Lazy loading: Solo carga notificaciones al hacer clic en la campanita
 * - Polling espaciado: Actualiza contador cada 60 segundos
 * - Usa caché del backend para evitar queries innecesarias
 * ============================================================================
 */

(function() {
    'use strict';
    
    let ultimoContador = null;
    let notificacionesCargadas = false;
    let pollingInterval = null;
    
    /**
     * Carga las notificaciones desde la API (solo cuando se abre el dropdown).
     */
    function cargarNotificaciones() {
        fetch('/notificaciones/api/?limit=10&archiviada=false')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    actualizarDropdown(data.notificaciones);
                    notificacionesCargadas = true;
                }
            })
            .catch(error => {
                console.error('Error al cargar notificaciones:', error);
            });
    }
    
    /**
     * Actualiza el badge del contador de notificaciones.
     * Solo muestra el badge si hay notificaciones (count > 0).
     */
    function actualizarBadge(count) {
        const badge = document.getElementById('notificationsBadge');
        if (badge) {
            const numCount = parseInt(count) || 0;
            
            if (numCount > 0) {
                badge.textContent = numCount > 99 ? '99+' : numCount.toString();
                badge.style.display = 'flex';
                badge.style.visibility = 'visible';
            } else {
                // Ocultar badge completamente cuando no hay notificaciones
                badge.style.display = 'none';
                badge.style.visibility = 'hidden';
                badge.textContent = ''; // Limpiar el texto para evitar que muestre "0"
            }
        }
    }
    
    /**
     * Actualiza el contador desde el servidor (usa caché del backend).
     */
    function actualizarContadorDesdeServidor() {
        return fetch('/notificaciones/api/contar/')
            .then(response => response.json())
            .then(data => {
                if (data.success !== undefined && data.success) {
                    const count = parseInt(data.count) || 0;
                    actualizarBadge(count);
                    ultimoContador = count;
                    return count;
                }
                return ultimoContador || 0;
            })
            .catch(error => {
                console.error('Error al actualizar contador:', error);
                return ultimoContador || 0;
            });
    }
    
    /**
     * Actualiza el dropdown con las notificaciones.
     */
    function actualizarDropdown(notificaciones) {
        const dropdownMenu = document.querySelector('.dropdown-menu-notifications');
        if (!dropdownMenu) return;
        
        // Encontrar el divider después del header
        const divider = dropdownMenu.querySelector('.dropdown-divider');
        if (!divider) return;
        
        // Encontrar todos los <li> después del divider (notificaciones existentes o mensaje vacío)
        const allItems = Array.from(dropdownMenu.querySelectorAll('li'));
        const dividerIndex = allItems.indexOf(divider.parentElement);
        
        // Eliminar todos los <li> después del divider
        for (let i = dividerIndex + 1; i < allItems.length; i++) {
            allItems[i].remove();
        }
        
        // Si no hay notificaciones, mostrar mensaje vacío
        if (notificaciones.length === 0) {
            const emptyLi = document.createElement('li');
            emptyLi.className = 'px-3 py-2 text-center text-muted dropdown-text-muted';
            emptyLi.textContent = 'No hay notificaciones';
            dropdownMenu.appendChild(emptyLi);
            return;
        }
        
        // Renderizar notificaciones
        notificaciones.forEach(notif => {
            const item = document.createElement('li');
            item.className = `dropdown-item notification-item ${notif.leida ? 'leida' : 'no-leida'}`;
            item.style.cssText = 'padding: 0.75rem 1rem; border-bottom: 1px solid #e9ecef;';
            
            // Truncar mensaje si es muy largo
            const mensajeTruncado = notif.mensaje.length > 80 
                ? notif.mensaje.substring(0, 80) + '...' 
                : notif.mensaje;
            
            item.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <div class="flex-grow-1" style="min-width: 0;">
                        <div class="d-flex align-items-start justify-content-between mb-1">
                            <strong class="text-dark" style="font-size: 0.875rem; line-height: 1.3;">${escapeHtml(notif.titulo)}</strong>
                            ${!notif.leida ? '<span class="badge bg-primary ms-2" style="font-size: 0.65rem;">Nueva</span>' : ''}
                        </div>
                        <p class="mb-1 small text-muted" style="font-size: 0.8rem; line-height: 1.4; word-wrap: break-word;">${escapeHtml(mensajeTruncado)}</p>
                        <small class="text-muted" style="font-size: 0.75rem;">
                            <i class="bi bi-clock me-1"></i>${notif.fecha_creacion}
                        </small>
                    </div>
                    <button class="btn btn-sm btn-link p-0 text-primary ver-detalle-btn" 
                            data-notificacion-id="${notif.id}"
                            style="flex-shrink: 0; padding: 0.25rem !important; min-width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;"
                            title="Ver detalles">
                        <i class="bi bi-eye" style="font-size: 1rem;"></i>
                    </button>
                </div>
            `;
            
            // Marcar como leída al hacer clic en el contenido (no en el botón de ojo)
            const contenido = item.querySelector('.flex-grow-1');
            contenido.style.cursor = 'pointer';
            contenido.addEventListener('click', function(e) {
                e.stopPropagation();
                if (!notif.leida) {
                    marcarComoLeida(notif.id);
                }
            });
            
            // Botón de ver detalles - abrir modal
            const btnVerDetalle = item.querySelector('.ver-detalle-btn');
            btnVerDetalle.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                mostrarDetalleNotificacion(notif);
            });
            
            dropdownMenu.appendChild(item);
        });
    }
    
    /**
     * Marca una notificación como leída.
     */
    function marcarComoLeida(notificacionId) {
        fetch(`/notificaciones/api/${notificacionId}/marcar-leida/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarBadge(data.count);
                cargarNotificaciones(); // Recargar lista
            }
        })
        .catch(error => {
            console.error('Error al marcar como leída:', error);
        });
    }
    
    /**
     * Muestra los detalles completos de una notificación en un modal.
     */
    function mostrarDetalleNotificacion(notif) {
        const modal = document.getElementById('modalDetalleNotificacion');
        const modalBody = document.getElementById('modalDetalleNotificacionBody');
        const modalTitle = document.getElementById('modalDetalleNotificacionLabel');
        
        if (!modal || !modalBody) return;
        
        // Actualizar título
        if (modalTitle) {
            modalTitle.textContent = 'Detalle de Notificación';
        }
        
        // Construir el contenido del modal
        let contenido = `
            <div class="mb-3">
                <h6 class="fw-bold mb-3">${escapeHtml(notif.titulo)}</h6>
                <div class="bg-light p-3 rounded" style="white-space: pre-wrap; line-height: 1.6;">
                    <p class="mb-0">${escapeHtml(notif.mensaje)}</p>
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
    
    /**
     * Marca todas las notificaciones como leídas.
     * Usa una bandera para prevenir múltiples ejecuciones simultáneas.
     */
    let marcandoTodasComoLeidas = false;
    
    function marcarTodasComoLeidas() {
        // Prevenir múltiples ejecuciones simultáneas
        if (marcandoTodasComoLeidas) {
            console.log('Ya se está procesando la solicitud de marcar todas como leídas...');
            return;
        }
        
        marcandoTodasComoLeidas = true;
        console.log('Marcando todas las notificaciones como leídas...');
        
        fetch('/notificaciones/api/marcar-todas-leidas/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Todas las notificaciones marcadas como leídas. Nuevo contador:', data.count);
                
                // Actualizar el contador inmediatamente con el valor del servidor
                if (data.count !== undefined) {
                    ultimoContador = parseInt(data.count) || 0;
                    actualizarBadge(ultimoContador);
                } else {
                    // Si no viene el contador, consultarlo desde el servidor
                    actualizarContadorDesdeServidor().then(count => {
                        ultimoContador = count;
                        actualizarBadge(count);
                    });
                }
                
                // Recargar notificaciones para actualizar el estado visual
                setTimeout(() => {
                    cargarNotificaciones();
                    // Forzar actualización del contador desde el servidor para asegurar sincronización
                    actualizarContadorDesdeServidor().then(count => {
                        ultimoContador = count;
                        actualizarBadge(count);
                        marcandoTodasComoLeidas = false;
                    }).catch(() => {
                        marcandoTodasComoLeidas = false;
                    });
                }, 200);
            } else {
                console.error('Error al marcar todas como leídas:', data.error || 'Error desconocido');
                marcandoTodasComoLeidas = false;
            }
        })
        .catch(error => {
            console.error('Error al marcar todas como leídas:', error);
            marcandoTodasComoLeidas = false;
        });
    }
    
    /**
     * Escapa HTML para prevenir XSS.
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Obtiene el valor de una cookie.
     */
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
    
    /**
     * Inicia polling del contador para detectar nuevas notificaciones.
     * Actualiza cada 30 segundos (coincide con el caché del backend de 30s).
     * Esto es eficiente porque la mayoría de requests serán desde caché (< 5ms).
     */
    function iniciarPolling() {
        // Polling cada 30 segundos (coincide con caché del backend)
        // La mayoría de requests serán desde caché, así que es muy rápido
        pollingInterval = setInterval(function() {
            actualizarContadorDesdeServidor().then(function(count) {
                // Si cambió el contador (nueva notificación), actualizar badge y recargar si el dropdown está abierto
                if (count !== ultimoContador && ultimoContador !== null) {
                    // Hay una nueva notificación
                    const dropdownMenu = document.querySelector('.dropdown-menu-notifications');
                    const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
                    
                    // Si el dropdown está abierto, recargar notificaciones para mostrar la nueva
                    if (isOpen) {
                        cargarNotificaciones();
                    }
                    // El badge ya se actualiza en actualizarBadge()
                }
            });
        }, 30000); // 30 segundos - coincide con caché del backend, mayoría de requests desde caché (< 5ms)
    }
    
    /**
     * Inicialización al cargar la página.
     */
    function inicializar() {
        // Asegurarse de que el badge esté oculto inicialmente
        const badge = document.getElementById('notificationsBadge');
        if (badge) {
            badge.style.display = 'none';
            badge.style.visibility = 'hidden';
            badge.textContent = '';
        }
        
        // Cargar contador Y notificaciones al inicio (sin lazy loading)
        actualizarContadorDesdeServidor();
        cargarNotificaciones();
        
        // Marcar como cargadas
        notificacionesCargadas = true;
        
        // Botón de marcar todas como leídas - usar event delegation para que funcione incluso cuando el botón se recrea
        // Usar capture phase para asegurar que se ejecute antes que otros listeners
        document.addEventListener('click', function(e) {
            const btnMarcarTodas = e.target.closest('#btnMarcarTodasLeidasDropdown');
            if (btnMarcarTodas) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                marcarTodasComoLeidas();
            }
        }, true);
        
        // Iniciar polling del contador
        iniciarPolling();
        
        // Listener para cuando se abre el dropdown - recargar notificaciones si hay nuevas
        const dropdownToggle = document.getElementById('notificationsDropdown');
        if (dropdownToggle) {
            dropdownToggle.addEventListener('click', function() {
                // Recargar notificaciones cuando se abre el dropdown para mostrar las más recientes
                cargarNotificaciones();
            });
        }
        
        console.log('✅ Sistema de notificaciones optimizado iniciado (polling cada 30s, usa caché del backend)');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }
    
    // Limpiar interval al salir de la página
    window.addEventListener('beforeunload', function() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });
    
})();

