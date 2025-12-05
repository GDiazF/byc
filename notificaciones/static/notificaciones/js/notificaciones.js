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
                    // Actualizar dropdown con las notificaciones
                    actualizarDropdown(data.notificaciones);
                    // Actualizar contador desde el servidor para asegurar precisión
                    actualizarContadorDesdeServidor();
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
            // Asegurar que count sea un número
            const numCount = parseInt(count) || 0;
            
            if (numCount > 0) {
                badge.textContent = numCount > 99 ? '99+' : numCount.toString();
                badge.style.display = 'block';
                badge.style.visibility = 'visible';
            } else {
                badge.textContent = '0';
                badge.style.display = 'none';
                badge.style.visibility = 'hidden';
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
                
                // Guardar datos completos de la notificación en el elemento
                item.setAttribute('data-notif-data', JSON.stringify(notif));
                
                // Agregar evento click para marcar como leída y mostrar detalles
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Solo marcar como leída si NO está leída actualmente
                    if (!notif.leida) {
                        // Marcar como leída inmediatamente
                        marcarComoLeida(notif.id);
                    }
                    
                    // Mostrar modal con detalles completos
                    mostrarDetalleNotificacion(notif);
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
                    <p class="mb-0" style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(notif.mensaje)}</p>
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
    
    // Función auxiliar para escapar HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Función para marcar como leída
    function marcarComoLeida(notificacionId) {
        // Verificar primero si ya está marcada como leída en el DOM para evitar doble procesamiento
        const item = document.querySelector(`[data-notif-id="${notificacionId}"]`);
        if (item && item.getAttribute('data-leida') === 'true') {
            return; // Ya está marcada como leída, no hacer nada
        }
        
        // Actualizar visualmente el item ANTES de la llamada al servidor (feedback inmediato)
        if (item) {
            item.style.borderLeft = 'none'; // Quitar borde de color
            item.style.opacity = '0.7';
            item.style.backgroundColor = '#f8f9fa';
            item.setAttribute('data-leida', 'true'); // Marcar como leída en el DOM
        }
        
        // Llamar al servidor para marcar como leída
        fetch(`/notificaciones/api/${notificacionId}/marcar-leida/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // El servidor retorna el nuevo contador, usarlo directamente
                if (data.count !== undefined) {
                    actualizarBadge(data.count);
                } else {
                    // Si no viene el contador, consultarlo después de un pequeño delay
                    setTimeout(() => {
                        actualizarContadorDesdeServidor();
                    }, 100);
                }
            } else {
                // Si falla, revertir el cambio visual
                if (item) {
                    item.style.borderLeft = '3px solid #ffc107';
                    item.style.opacity = '1';
                    item.style.backgroundColor = '';
                    item.removeAttribute('data-leida');
                }
            }
        })
        .catch(error => {
            console.error('Error al marcar como leída:', error);
            // Revertir el cambio visual si hay error
            if (item) {
                item.style.borderLeft = '3px solid #ffc107';
                item.style.opacity = '1';
                item.style.backgroundColor = '';
                item.removeAttribute('data-leida');
            }
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
    
    // Variables para polling adaptativo
    let intervaloPolling = 15000; // Empezar con 15 segundos
    let ultimoContador = null; // null inicialmente para detectar primera carga
    let timeoutPolling = null;
    
    // Cargar notificaciones al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Cargar contador primero para mostrar el número correcto inmediatamente
            actualizarContadorDesdeServidor().then(function(count) {
                ultimoContador = count; // Guardar el contador inicial
            });
            // Luego cargar las notificaciones
            cargarNotificaciones();
            // Iniciar polling adaptativo
            iniciarPolling();
        });
    } else {
        // Cargar contador primero
        actualizarContadorDesdeServidor().then(function(count) {
            ultimoContador = count; // Guardar el contador inicial
        });
        // Luego cargar las notificaciones
        cargarNotificaciones();
        iniciarPolling();
    }
    
    // Función para iniciar polling adaptativo de notificaciones
    function iniciarPolling() {
        function ejecutarPolling() {
            // Solo actualizar si el dropdown no está abierto (para no interrumpir al usuario)
            const dropdown = document.querySelector('#notificationsDropdown');
            const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
            const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
            
            if (!isOpen) {
                // Actualizar solo el contador (más ligero que cargar todas las notificaciones)
                actualizarContadorDesdeServidor().then(function(count) {
                    const contadorAnterior = ultimoContador;
                    // Si el contador cambió, recargar las notificaciones también
                    if (contadorAnterior === null || count !== contadorAnterior) {
                        ultimoContador = count;
                        // Recargar notificaciones siempre que haya cambio (incluyendo primera carga)
                        cargarNotificaciones();
                        // Si hay cambios, usar intervalo más corto (5 segundos)
                        intervaloPolling = 5000;
                    } else {
                        // Si no hay cambios, aumentar gradualmente el intervalo (hasta 30 segundos máximo)
                        intervaloPolling = Math.min(intervaloPolling + 5000, 30000);
                    }
                    
                    // Programar siguiente polling
                    timeoutPolling = setTimeout(ejecutarPolling, intervaloPolling);
                });
            } else {
                // Si el dropdown está abierto, esperar un poco más
                timeoutPolling = setTimeout(ejecutarPolling, 5000);
            }
        }
        
        // Iniciar el primer polling después de 15 segundos
        timeoutPolling = setTimeout(ejecutarPolling, intervaloPolling);
    }
    
    // Función para detener el polling (útil si se implementa SSE o WebSockets en el futuro)
    function detenerPolling() {
        if (timeoutPolling) {
            clearTimeout(timeoutPolling);
            timeoutPolling = null;
        }
    }
    
    // Recargar cuando se abre el dropdown
    const dropdownToggle = document.querySelector('#notificationsDropdown');
    if (dropdownToggle) {
        dropdownToggle.addEventListener('shown.bs.dropdown', function() {
            cargarNotificaciones();
        });
        
        // Actualizar contador cuando se cierra el dropdown (por si acaso)
        dropdownToggle.addEventListener('hidden.bs.dropdown', function() {
            // Pequeño delay para asegurar que cualquier cambio se haya procesado
            setTimeout(() => {
                actualizarContadorDesdeServidor();
            }, 200);
        });
    }
    
    // Función simple para reproducir sonido de notificación
    function reproducirSonidoNotificacion() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Reanudar si está suspendido (async)
            if (audioContext.state === 'suspended') {
                audioContext.resume().then(() => {
                    crearBeep(audioContext);
                }).catch(() => {
                    crearBeep(audioContext);
                });
            } else {
                crearBeep(audioContext);
            }
        } catch (error) {
            // Si falla, no hacer nada
        }
    }
    
    // Inicializar audio con cualquier interacción del usuario
    let audioInicializado = false;
    function inicializarAudio() {
        if (!audioInicializado) {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }
                audioInicializado = true;
            } catch (e) {
                // Ignorar errores
            }
        }
    }
    
    // Función auxiliar para crear el beep
    function crearBeep(audioContext) {
        try {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Sonido simple de beep
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            const now = audioContext.currentTime;
            gainNode.gain.setValueAtTime(0, now);
            gainNode.gain.linearRampToValueAtTime(0.5, now + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
            
            oscillator.start(now);
            oscillator.stop(now + 0.2);
        } catch (error) {
            // Si falla, no hacer nada
        }
    }
    
    // Inicializar con cualquier interacción
    ['click', 'keydown', 'touchstart', 'mousedown'].forEach(evento => {
        document.addEventListener(evento, inicializarAudio, { once: true });
    });
    
    // Función para actualizar el contador desde el servidor (más confiable)
    function actualizarContadorDesdeServidor() {
        return fetch('/notificaciones/api/contar/')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success !== undefined && data.success) {
                    // Asegurar que el count sea un número válido
                    const count = parseInt(data.count) || 0;
                    const contadorAnterior = ultimoContador !== null ? ultimoContador : 0;
                    
                    // Si el contador aumentó y no es la primera carga, reproducir sonido
                    if (ultimoContador !== null && count > ultimoContador) {
                        // Inicializar audio primero
                        inicializarAudio();
                        // Reproducir sonido inmediatamente
                        reproducirSonidoNotificacion();
                    }
                    
                    actualizarBadge(count);
                    
                    // Retornar el contador para el polling adaptativo
                    return count;
                } else {
                    return ultimoContador !== null ? ultimoContador : 0; // Retornar el último contador conocido
                }
            })
            .catch(error => {
                console.error('Error al actualizar contador:', error);
                return ultimoContador !== null ? ultimoContador : 0; // Retornar el último contador conocido en caso de error
            });
    }
    
    // Función para actualizar el contador rápidamente (optimista)
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
        actualizarContadorDesdeServidor();
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
                // El servidor retorna el nuevo contador, usarlo directamente
                if (data.count !== undefined) {
                    actualizarBadge(data.count);
                } else {
                    // Si no viene el contador, consultarlo
                    actualizarContadorDesdeServidor();
                }
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

