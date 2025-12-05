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
                    <div class="d-flex align-items-start" style="gap: 0.5rem;">
                        <div class="flex-grow-1" style="min-width: 0;">
                            <div class="fw-bold" style="font-size: 0.875rem;">${notif.titulo}</div>
                            <div class="text-muted" style="font-size: 0.75rem; margin-top: 0.25rem;">${notif.mensaje.substring(0, 60)}${notif.mensaje.length > 60 ? '...' : ''}</div>
                            <small class="text-muted" style="font-size: 0.65rem;">${notif.fecha_creacion}</small>
                        </div>
                        <button class="btn btn-sm btn-link p-0 text-muted ver-detalle-btn" 
                                style="flex-shrink: 0; padding: 0.25rem !important; min-width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;"
                                title="Ver detalles"
                                data-notif-id="${notif.id}">
                            <i class="bi bi-eye" style="font-size: 0.875rem;"></i>
                        </button>
                    </div>
                `;
                
                // Guardar datos completos de la notificación en el elemento
                item.setAttribute('data-notif-data', JSON.stringify(notif));
                
                // Evento click en el item: solo marcar como leída
                item.addEventListener('click', function(e) {
                    // Si el clic fue en el botón de ver detalles, no hacer nada aquí
                    if (e.target.closest('.ver-detalle-btn')) {
                        return;
                    }
                    
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Solo marcar como leída si NO está leída actualmente
                    if (!notif.leida) {
                        marcarComoLeida(notif.id);
                    }
                });
                
                // Evento click en el botón de ver detalles: mostrar modal
                const verDetalleBtn = item.querySelector('.ver-detalle-btn');
                if (verDetalleBtn) {
                    verDetalleBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Obtener los datos de la notificación
                        const notifData = JSON.parse(item.getAttribute('data-notif-data'));
                        
                        // Mostrar modal con detalles completos
                        mostrarDetalleNotificacion(notifData);
                        
                        // Opcional: marcar como leída al ver detalles
                        if (!notifData.leida) {
                            marcarComoLeida(notifData.id);
                        }
                    });
                }
                
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
    
    // Variables para SSE (Server-Sent Events)
    let eventSource = null;
    let ultimoContador = null; // null inicialmente para detectar primera carga
    let reconexionTimeout = null;
    let intentosReconexion = 0;
    const MAX_INTENTOS_RECONEXION = 5;
    const DELAY_RECONEXION = 3000; // 3 segundos
    
    // Función para iniciar conexión SSE
    function iniciarSSE() {
        // Cerrar conexión anterior si existe
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        
        // Verificar si el navegador soporta EventSource
        if (typeof EventSource === 'undefined') {
            console.warn('EventSource no está disponible, usando polling como fallback');
            iniciarPollingFallback();
            return;
        }
        
        try {
            // Crear nueva conexión SSE
            eventSource = new EventSource('/notificaciones/api/sse/');
            
            // Evento cuando se establece la conexión
            eventSource.addEventListener('connected', function(e) {
                intentosReconexion = 0; // Resetear contador de intentos
                try {
                    const data = JSON.parse(e.data);
                    ultimoContador = data.count;
                    actualizarBadge(data.count);
                    console.log('Conexión SSE establecida:', data.message, 'Contador:', data.count);
                } catch (error) {
                    console.error('Error al procesar evento connected:', error);
                }
            });
            
            // Evento cuando llega una nueva notificación
            eventSource.addEventListener('notification', function(e) {
                try {
                    const message = JSON.parse(e.data);
                    // El mensaje tiene estructura: {type: 'notification', data: {...}, timestamp: ...}
                    const data = message.data || message; // Compatibilidad con ambos formatos
                    const notificacion = data.notificacion;
                    const nuevoContador = data.count;
                    
                    if (!notificacion) {
                        console.warn('Evento de notificación recibido sin datos de notificación:', message);
                        return;
                    }
                    
                    // Reproducir sonido siempre que llegue una notificación nueva
                    inicializarAudio();
                    reproducirSonidoNotificacion();
                    
                    // Actualizar contador
                    ultimoContador = nuevoContador;
                    actualizarBadge(nuevoContador);
                    
                    // Recargar notificaciones solo si el dropdown no está abierto
                    const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
                    const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
                    if (!isOpen) {
                        cargarNotificaciones();
                    }
                    
                    console.log('Notificación recibida en tiempo real:', notificacion.titulo, 'Contador:', nuevoContador);
                } catch (error) {
                    console.error('Error al procesar evento de notificación:', error, 'Datos recibidos:', e.data);
                }
            });
            
            // Evento cuando se actualiza el contador (marcar como leída, etc.)
            eventSource.addEventListener('count_update', function(e) {
                try {
                    const message = JSON.parse(e.data);
                    // El mensaje tiene estructura: {type: 'count_update', data: {...}, timestamp: ...}
                    const data = message.data || message; // Compatibilidad con ambos formatos
                    ultimoContador = data.count;
                    actualizarBadge(data.count);
                    console.log('Contador actualizado vía SSE:', data.count);
                } catch (error) {
                    console.error('Error al procesar evento count_update:', error);
                }
            });
            
            // Evento de heartbeat (mantener conexión viva)
            eventSource.addEventListener('heartbeat', function(e) {
                // Solo para mantener la conexión viva, no hacer nada
            });
            
            // Evento de timeout
            eventSource.addEventListener('timeout', function(e) {
                const data = JSON.parse(e.data);
                console.log('Conexión SSE cerrada por timeout:', data.message);
                // Reconectar después de un delay
                programarReconexion();
            });
            
            // Evento de error
            eventSource.addEventListener('error', function(e) {
                console.error('Error en conexión SSE:', e);
                // Cerrar conexión y reconectar
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                programarReconexion();
            });
            
            // Manejar errores generales
            eventSource.onerror = function(e) {
                console.error('Error general en SSE. Estado:', eventSource.readyState, e);
                if (eventSource.readyState === EventSource.CLOSED) {
                    // Conexión cerrada, intentar reconectar
                    console.log('Conexión SSE cerrada, intentando reconectar...');
                    programarReconexion();
                } else if (eventSource.readyState === EventSource.CONNECTING) {
                    console.log('Reconectando SSE...');
                }
            };
            
            // Log cuando se abre la conexión
            eventSource.onopen = function(e) {
                console.log('Conexión SSE abierta');
            };
            
        } catch (error) {
            console.error('Error al iniciar SSE:', error);
            // Fallback a polling si SSE falla
            iniciarPollingFallback();
        }
    }
    
    // Función para programar reconexión
    function programarReconexion() {
        if (reconexionTimeout) {
            clearTimeout(reconexionTimeout);
        }
        
        if (intentosReconexion < MAX_INTENTOS_RECONEXION) {
            intentosReconexion++;
            const delay = DELAY_RECONEXION * intentosReconexion; // Delay exponencial
            console.log(`Reintentando conexión SSE en ${delay/1000} segundos (intento ${intentosReconexion}/${MAX_INTENTOS_RECONEXION})`);
            
            reconexionTimeout = setTimeout(function() {
                iniciarSSE();
            }, delay);
        } else {
            console.warn('Máximo de intentos de reconexión alcanzado, usando polling como fallback');
            iniciarPollingFallback();
        }
    }
    
    // Función de fallback a polling (si SSE no está disponible)
    function iniciarPollingFallback() {
        console.log('Usando polling como método de actualización');
        let intervaloPolling = 15000;
        let timeoutPolling = null;
        
        function ejecutarPolling() {
            const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
            const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
            
            if (!isOpen) {
                actualizarContadorDesdeServidor().then(function(count) {
                    const contadorAnterior = ultimoContador;
                    if (contadorAnterior === null || count !== contadorAnterior) {
                        ultimoContador = count;
                        cargarNotificaciones();
                        intervaloPolling = 5000;
                    } else {
                        intervaloPolling = Math.min(intervaloPolling + 5000, 30000);
                    }
                    timeoutPolling = setTimeout(ejecutarPolling, intervaloPolling);
                });
            } else {
                timeoutPolling = setTimeout(ejecutarPolling, 5000);
            }
        }
        
        // Cargar inicialmente
        actualizarContadorDesdeServidor().then(function(count) {
            ultimoContador = count;
        });
        cargarNotificaciones();
        
        // Iniciar polling
        timeoutPolling = setTimeout(ejecutarPolling, intervaloPolling);
    }
    
    // Cargar notificaciones al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Cargar contador primero para mostrar el número correcto inmediatamente
            actualizarContadorDesdeServidor().then(function(count) {
                ultimoContador = count; // Guardar el contador inicial
            });
            // Luego cargar las notificaciones
            cargarNotificaciones();
            // Iniciar SSE
            iniciarSSE();
        });
    } else {
        // Cargar contador primero
        actualizarContadorDesdeServidor().then(function(count) {
            ultimoContador = count; // Guardar el contador inicial
        });
        // Luego cargar las notificaciones
        cargarNotificaciones();
        iniciarSSE();
    }
    
    // Cerrar conexión SSE cuando se cierra la página
    window.addEventListener('beforeunload', function() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        if (reconexionTimeout) {
            clearTimeout(reconexionTimeout);
        }
    });
    
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
    
    // Audio context global para reutilizar
    let audioContextGlobal = null;
    let audioInicializado = false;
    
    // Inicializar audio con cualquier interacción del usuario
    function inicializarAudio() {
        if (!audioInicializado) {
            try {
                audioContextGlobal = new (window.AudioContext || window.webkitAudioContext)();
                if (audioContextGlobal.state === 'suspended') {
                    audioContextGlobal.resume().catch(function(e) {
                        console.warn('No se pudo reanudar el audio context:', e);
                    });
                }
                audioInicializado = true;
                console.log('Audio inicializado correctamente');
            } catch (e) {
                console.warn('Error al inicializar audio:', e);
            }
        }
    }
    
    // Función para reproducir sonido de notificación estilo moderno (como Facebook/WhatsApp)
    function reproducirSonidoNotificacion() {
        try {
            // Si no está inicializado, intentar inicializar
            if (!audioInicializado || !audioContextGlobal) {
                inicializarAudio();
            }
            
            // Si aún no hay audioContext, crear uno temporal
            let audioContext = audioContextGlobal;
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Reanudar si está suspendido
            if (audioContext.state === 'suspended') {
                audioContext.resume().then(function() {
                    crearSonidoNotificacionModerno(audioContext);
                }).catch(function() {
                    // Si falla, intentar crear sonido de todas formas
                    crearSonidoNotificacionModerno(audioContext);
                });
            } else {
                crearSonidoNotificacionModerno(audioContext);
            }
        } catch (error) {
            console.warn('Error al reproducir sonido de notificación:', error);
        }
    }
    
    // Función para crear sonido de notificación moderno (suave y agradable)
    function crearSonidoNotificacionModerno(audioContext) {
        try {
            const now = audioContext.currentTime;
            
            // Crear un sonido más suave y melódico, similar a Facebook/WhatsApp
            // Usamos frecuencias más agradables y un patrón más suave
            
            // Primer tono - más suave y bajo
            const osc1 = audioContext.createOscillator();
            const gain1 = audioContext.createGain();
            osc1.connect(gain1);
            gain1.connect(audioContext.destination);
            
            osc1.frequency.setValueAtTime(523.25, now); // Nota C5 (más agradable)
            osc1.type = 'sine'; // Onda senoidal para sonido más suave
            
            // Envelope suave del primer tono
            gain1.gain.setValueAtTime(0, now);
            gain1.gain.linearRampToValueAtTime(0.15, now + 0.05); // Subida más suave
            gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
            
            osc1.start(now);
            osc1.stop(now + 0.12);
            
            // Segundo tono - más alto pero suave, con ligera variación
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            
            osc2.frequency.setValueAtTime(659.25, now + 0.08); // Nota E5 (quinta perfecta, más armoniosa)
            osc2.type = 'sine';
            
            // Envelope suave del segundo tono (empieza antes de que termine el primero)
            const startTime2 = now + 0.08;
            gain2.gain.setValueAtTime(0, startTime2);
            gain2.gain.linearRampToValueAtTime(0.15, startTime2 + 0.05);
            gain2.gain.exponentialRampToValueAtTime(0.01, startTime2 + 0.15);
            
            osc2.start(startTime2);
            osc2.stop(startTime2 + 0.15);
            
        } catch (error) {
            console.warn('Error al crear sonido de notificación:', error);
        }
    }
    
    // Inicializar con cualquier interacción (múltiples eventos para asegurar)
    ['click', 'keydown', 'touchstart', 'mousedown', 'scroll'].forEach(evento => {
        document.addEventListener(evento, inicializarAudio, { once: true });
    });
    
    // También intentar inicializar al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarAudio);
    } else {
        // Si ya está cargado, inicializar inmediatamente
        setTimeout(inicializarAudio, 100);
    }
    
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
    
    // Función para configurar el listener del botón "Marcar todas como leídas"
    function configurarBotonMarcarTodas() {
        const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
        if (!dropdownMenu) return;
        
        // Remover listener anterior si existe
        const nuevoBoton = dropdownMenu.querySelector('#btnMarcarTodasLeidasDropdown');
        if (nuevoBoton && !nuevoBoton.hasAttribute('data-listener-configurado')) {
            nuevoBoton.setAttribute('data-listener-configurado', 'true');
            
            nuevoBoton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
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
                        
                        // Actualizar el contador
                        if (data.count !== undefined) {
                            ultimoContador = data.count;
                            actualizarBadge(data.count);
                        } else {
                            // Si no viene el contador, consultarlo
                            actualizarContadorDesdeServidor();
                        }
                        
                        // Recargar notificaciones para actualizar el estado visual
                        setTimeout(() => {
                            cargarNotificaciones();
                        }, 200);
                    } else {
                        console.error('Error al marcar todas como leídas:', data.error || 'Error desconocido');
                    }
                })
                .catch(error => {
                    console.error('Error al marcar todas como leídas:', error);
                });
                
                return false;
            }, true); // Usar capture phase
        }
    }
    
    // Configurar el botón cuando se carga la página
    configurarBotonMarcarTodas();
    
    // También configurar cuando se abre el dropdown (por si se recrea dinámicamente)
    const dropdownToggleMarcarTodas = document.querySelector('#notificationsDropdown');
    if (dropdownToggleMarcarTodas) {
        dropdownToggleMarcarTodas.addEventListener('shown.bs.dropdown', function() {
            setTimeout(configurarBotonMarcarTodas, 50);
        });
    }
    
    // También usar event delegation como respaldo
    document.addEventListener('click', function(e) {
        const btnMarcarTodas = e.target.closest('#btnMarcarTodasLeidasDropdown');
        if (btnMarcarTodas) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
        }
    }, true);
    
})();


