/**
 * JavaScript para gestionar notificaciones en el navbar
 */

(function() {
    'use strict';
    
    // Función para cargar notificaciones
    function cargarNotificaciones() {
        // Cargar todas las notificaciones (leídas y no leídas) pero solo no archivadas
        fetch('/notificaciones/api/?limit=10&archivada=false')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Contar solo las no leídas para el badge
                    const noLeidas = data.notificaciones.filter(n => !n.leida).length;
                    actualizarBadge(noLeidas);
                    actualizarDropdown(data.notificaciones);
                }
            })
            .catch(error => {
                console.error('Error al cargar notificaciones:', error);
            });
    }
    
    // Función para actualizar el badge
    function actualizarBadge(count) {
        const badge = document.getElementById('notificationsBadge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count.toString();
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    // Función para actualizar el dropdown
    function actualizarDropdown(notificaciones) {
        const dropdown = document.querySelector('#notificationsDropdown + .dropdown-menu');
        if (!dropdown) return;
        
        // Guardar la posición del scroll antes de actualizar
        const contenedorScroll = dropdown.querySelector('ul[style*="overflow-y"]');
        let scrollPosition = 0;
        if (contenedorScroll) {
            scrollPosition = contenedorScroll.scrollTop;
        }
        
        // Limpiar TODO el contenido excepto el header
        const header = dropdown.querySelector('.dropdown-header');
        const headerHTML = header ? header.outerHTML : '';
        
        // Limpiar todo el contenido del dropdown
        dropdown.innerHTML = '';
        
        // Restaurar el header
        if (headerHTML) {
            dropdown.insertAdjacentHTML('beforeend', headerHTML);
        }
        
        // Agregar divisor después del header
        const divider = document.createElement('li');
        divider.innerHTML = '<hr class="dropdown-divider">';
        dropdown.appendChild(divider);
        
        // Crear contenedor con scroll para las notificaciones
        const contenedorNotificaciones = document.createElement('ul');
        contenedorNotificaciones.style.maxHeight = '400px';
        contenedorNotificaciones.style.overflowY = 'auto';
        contenedorNotificaciones.style.overflowX = 'hidden';
        contenedorNotificaciones.style.padding = '0';
        contenedorNotificaciones.style.margin = '0';
        contenedorNotificaciones.style.listStyle = 'none';
        
        // Agregar notificaciones
        if (notificaciones.length === 0) {
            const emptyMsg = document.createElement('li');
            emptyMsg.className = 'px-3 py-2 text-center text-muted';
            emptyMsg.style.fontSize = '0.875rem';
            emptyMsg.textContent = 'No hay notificaciones';
            dropdown.appendChild(emptyMsg);
        } else {
            notificaciones.forEach(notif => {
                const item = document.createElement('li');
                item.className = 'dropdown-item';
                item.style.cursor = 'pointer';
                item.setAttribute('data-notif-id', notif.id);
                
                // Determinar color del borde izquierdo según tipo de notificación
                // Rojo para vencimientos, amarillo para las demás
                const esVencimiento = (notif.tipo && notif.tipo.includes('Vencimiento')) || 
                                     (notif.codigo_tipo && notif.codigo_tipo.includes('VENCIMIENTO'));
                
                // Solo mostrar borde de color si NO está leída
                if (!notif.leida) {
                    if (esVencimiento) {
                        item.style.borderLeft = '3px solid #dc3545'; // Rojo para vencimientos
                    } else {
                        item.style.borderLeft = '3px solid #ffc107'; // Amarillo para otras
                    }
                } else {
                    // Si está leída, sin borde de color
                    item.style.borderLeft = 'none';
                }
                
                // Estilo diferente para notificaciones leídas
                if (notif.leida) {
                    item.style.opacity = '0.7';
                    item.style.backgroundColor = '#f8f9fa';
                }
                
                item.innerHTML = `
                    <div class="d-flex align-items-start">
                        <div class="flex-grow-1">
                            <div class="fw-bold" style="font-size: 0.875rem;">${notif.titulo}</div>
                            <div class="text-muted" style="font-size: 0.75rem; margin-top: 0.25rem;">${notif.mensaje.substring(0, 60)}${notif.mensaje.length > 60 ? '...' : ''}</div>
                            <small class="text-muted" style="font-size: 0.65rem;">${notif.fecha_creacion}</small>
                        </div>
                    </div>
                `;
                
                // Agregar evento click solo para marcar como leída (sin redirigir)
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Solo marcar como leída si no está leída
                    if (!notif.leida) {
                        marcarComoLeida(notif.id);
                    }
                });
                
                contenedorNotificaciones.appendChild(item);
            });
            
            // Agregar el contenedor con scroll al dropdown
            const contenedorLi = document.createElement('li');
            contenedorLi.style.padding = '0';
            contenedorLi.appendChild(contenedorNotificaciones);
            dropdown.appendChild(contenedorLi);
            
            // Restaurar la posición del scroll después de un pequeño delay
            if (scrollPosition > 0) {
                setTimeout(() => {
                    contenedorNotificaciones.scrollTop = scrollPosition;
                }, 50);
            }
        }
    }
    
    // Función para marcar como leída
    function marcarComoLeida(notificacionId) {
        fetch(`/notificaciones/api/${notificacionId}/marcar-leida/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar visualmente el item inmediatamente
                const item = document.querySelector(`[data-notif-id="${notificacionId}"]`);
                if (item) {
                    item.style.borderLeft = 'none'; // Quitar borde de color
                    item.style.opacity = '0.7';
                    item.style.backgroundColor = '#f8f9fa';
                }
                
                // Actualizar contador inmediatamente (sin esperar)
                actualizarContadorRapido();
                
                // NO recargar notificaciones si el dropdown está abierto para evitar perder la posición del scroll
                // El estado visual ya se actualizó arriba (borde removido, opacidad cambiada)
                const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
                const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
                
                if (!isOpen) {
                    // Solo recargar si el dropdown está cerrado
                    setTimeout(() => {
                        cargarNotificaciones();
                    }, 200);
                }
                // Si el dropdown está abierto, no recargar para mantener la posición del scroll
            }
        })
        .catch(error => {
            console.error('Error al marcar como leída:', error);
        });
    }
    
    // Función para obtener cookie CSRF
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
    
    // Cargar notificaciones al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            cargarNotificaciones();
            // Iniciar polling cada 15 segundos para actualizar automáticamente
            iniciarPolling();
        });
    } else {
        cargarNotificaciones();
        iniciarPolling();
    }
    
    // Función para iniciar polling de notificaciones
    function iniciarPolling() {
        // Recargar notificaciones cada 15 segundos
        setInterval(function() {
            // Solo actualizar si el dropdown no está abierto (para no interrumpir al usuario)
            const dropdown = document.querySelector('#notificationsDropdown');
            const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
            const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
            
            if (!isOpen) {
                cargarNotificaciones();
            }
        }, 15000); // 15 segundos
    }
    
    // Recargar cuando se abre el dropdown
    const dropdownToggle = document.querySelector('#notificationsDropdown');
    if (dropdownToggle) {
        dropdownToggle.addEventListener('shown.bs.dropdown', cargarNotificaciones);
    }
    
    // También actualizar el contador rápidamente cuando se marca como leída
    function actualizarContadorRapido() {
        // Actualizar inmediatamente de forma optimista (sin esperar respuesta del servidor)
        // Esto hace que la UI responda instantáneamente
        const badge = document.getElementById('notificationsBadge');
        if (badge) {
            // Obtener el número actual del badge (manejar casos como "99+")
            let currentCount = 0;
            const badgeText = badge.textContent.trim();
            if (badgeText.includes('+')) {
                currentCount = parseInt(badgeText.replace('+', '')) || 0;
            } else {
                currentCount = parseInt(badgeText) || 0;
            }
            
            // Restar 1 y actualizar inmediatamente
            const newCount = Math.max(0, currentCount - 1);
            actualizarBadge(newCount);
        }
        
        // Luego sincronizar con el servidor para asegurar precisión
        fetch('/notificaciones/api/contar/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    actualizarBadge(data.count);
                }
            })
            .catch(error => {
                console.error('Error al actualizar contador:', error);
            });
    }
    
    // Botón "Marcar todas como leídas" en el dropdown
    const btnMarcarTodas = document.querySelector('#btnMarcarTodasLeidasDropdown');
    if (btnMarcarTodas) {
        btnMarcarTodas.addEventListener('click', function(e) {
            e.stopPropagation();
            fetch('/notificaciones/api/marcar-todas-leidas/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarContadorRapido(); // Actualizar contador inmediatamente
                // Recargar notificaciones para actualizar el estado visual
                setTimeout(() => {
                    cargarNotificaciones();
                }, 300); // Pequeño delay para que se vea el cambio
            }
        })
            .catch(error => {
                console.error('Error al marcar todas como leídas:', error);
            });
        });
    }
    
})();

