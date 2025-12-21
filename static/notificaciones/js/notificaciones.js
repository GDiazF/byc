/**
 * ============================================================================
 * JAVASCRIPT PARA GESTIONAR NOTIFICACIONES EN EL NAVBAR
 * ============================================================================
 * Este módulo maneja la visualización de notificaciones en el dropdown del navbar,
 * incluyendo carga de notificaciones, actualización del contador, Server-Sent Events
 * para actualizaciones en tiempo real, y sonidos de notificación.
 * ============================================================================
 */

(function() {
    'use strict';
    
    /**
     * Carga las notificaciones desde la API y actualiza el dropdown.
     * Carga las últimas 10 notificaciones no archivadas (leídas y no leídas).
     */
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
    
    /**
     * Actualiza el badge del contador de notificaciones en el navbar.
     * 
     * @param {number} count - Número de notificaciones no leídas.
     *                         Si es mayor a 99, muestra "99+".
     *                         Si es 0, oculta el badge.
     */
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
    
    /**
     * Actualiza el contenido del dropdown de notificaciones.
     * 
     * Renderiza las notificaciones en el dropdown, preservando la posición
     * del scroll si el usuario estaba navegando. Aplica estilos diferentes
     * según el estado de lectura y tipo de notificación.
     * 
     * @param {Array} notificaciones - Array de objetos notificación a mostrar.
     */
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
            // Reconfigurar el botón después de restaurar el header
            setTimeout(() => {
                configurarBotonMarcarTodas();
            }, 10);
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
                    <div class="d-flex align-items-start" style="gap: 0.5rem; position: relative;">
                        <div class="flex-grow-1" style="min-width: 0; overflow: hidden; padding-right: 0.25rem;">
                            <div class="fw-bold" style="font-size: 0.875rem; word-wrap: break-word; overflow-wrap: break-word;">${notif.titulo}</div>
                            <div class="text-muted" style="font-size: 0.75rem; margin-top: 0.25rem; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.3;">${notif.mensaje.substring(0, 60)}${notif.mensaje.length > 60 ? '...' : ''}</div>
                            <small class="text-muted" style="font-size: 0.65rem; display: block; margin-top: 0.25rem;">${notif.fecha_creacion}</small>
                        </div>
                        <button class="btn btn-sm btn-link p-0 text-muted ver-detalle-btn" 
                                style="flex-shrink: 0; padding: 0.25rem !important; min-width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; position: relative; z-index: 10; background-color: rgba(255, 255, 255, 0.9); border-radius: 4px;"
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
    
    /**
     * Muestra los detalles completos de una notificación en un modal.
     * 
     * @param {Object} notif - Objeto con los datos de la notificación
     *                         (titulo, mensaje, fecha_creacion, etc.)
     */
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
    
    /**
     * Escapa caracteres HTML especiales para prevenir XSS.
     * 
     * @param {string} text - Texto a escapar.
     * @returns {string} Texto escapado seguro para HTML.
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Marca una notificación como leída.
     * 
     * Actualiza visualmente el estado de la notificación antes de llamar
     * al servidor (feedback inmediato) y luego sincroniza con el servidor.
     * Si falla, revierte los cambios visuales.
     * 
     * @param {number} notificacionId - ID de la notificación a marcar como leída.
     */
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
    
    /**
     * Obtiene el valor de una cookie por su nombre.
     * 
     * @param {string} name - Nombre de la cookie.
     * @returns {string|null} Valor de la cookie o null si no existe.
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
    
    // Variables para SSE (Server-Sent Events)
    let eventSource = null;
    let ultimoContador = null; // null inicialmente para detectar primera carga
    let reconexionTimeout = null;
    let intentosReconexion = 0;
    const MAX_INTENTOS_RECONEXION = 5;
    const DELAY_RECONEXION = 3000; // 3 segundos
    
    /**
     * Inicia la conexión Server-Sent Events (SSE) para recibir notificaciones en tiempo real.
     * 
     * Establece una conexión SSE con el servidor y configura los event listeners
     * para manejar diferentes tipos de eventos: connected, notification, count_update,
     * heartbeat, timeout y error. Si SSE no está disponible, usa polling como fallback.
     */
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
    
    /**
     * Programa una reconexión SSE después de un delay exponencial.
     * 
     * Si se alcanza el máximo de intentos de reconexión, cambia a polling
     * como método de actualización.
     */
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
    
    /**
     * Inicia polling como método de actualización cuando SSE no está disponible.
     * 
     * Usa un intervalo adaptativo que aumenta cuando no hay cambios y disminuye
     * cuando se detectan cambios. Evita hacer polling cuando el dropdown está abierto.
     */
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
    
    /**
     * Inicializa el contexto de audio para reproducir sonidos de notificación.
     * 
     * Crea un AudioContext global que se reutiliza para todas las notificaciones.
     * El audio solo se puede inicializar después de una interacción del usuario
     * debido a las políticas del navegador.
     */
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
    
    /**
     * Reproduce un sonido de notificación estilo moderno (similar a Facebook/WhatsApp).
     * 
     * Crea un sonido suave y melódico usando Web Audio API con dos tonos
     * armoniosos que se superponen ligeramente.
     */
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
    
    /**
     * Crea el sonido de notificación usando Web Audio API.
     * 
     * Genera dos tonos melódicos (C5 y E5) con envolventes suaves que se superponen
     * para crear un sonido agradable y no intrusivo.
     * 
     * @param {AudioContext} audioContext - Contexto de audio para generar el sonido.
     */
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
    
    /**
     * Actualiza el contador de notificaciones no leídas desde el servidor.
     * 
     * Hace una petición al servidor para obtener el contador actualizado.
     * Si el contador aumentó desde la última vez, reproduce un sonido de notificación.
     * 
     * @returns {Promise<number>} Promise que resuelve con el número de notificaciones no leídas.
     */
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
    
    /**
     * Actualiza el contador de forma optimista (sin esperar respuesta del servidor).
     * 
     * Resta 1 del contador actual inmediatamente para dar feedback visual instantáneo,
     * y luego sincroniza con el servidor para asegurar precisión.
     */
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
    
    /**
     * Función para marcar todas las notificaciones como leídas.
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
                    marcandoTodasComoLeidas = false;
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
     * Configura el event listener del botón "Marcar todas como leídas" en el dropdown.
     * Usa event delegation para que funcione incluso cuando el botón se recrea dinámicamente.
     */
    function configurarBotonMarcarTodas() {
        // No necesitamos hacer nada aquí, el event delegation se encarga de todo
        // Esta función se mantiene por compatibilidad pero no hace nada
    }
    
    // Event delegation robusto que funciona incluso cuando el botón se recrea
    // Usar capture phase para asegurar que se ejecute antes que otros listeners
    document.addEventListener('click', function(e) {
        // Verificar si el click fue en el botón o en un elemento dentro del botón
        const btnMarcarTodas = e.target.closest('#btnMarcarTodasLeidasDropdown');
        if (btnMarcarTodas) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Llamar a la función que maneja la lógica
            marcarTodasComoLeidas();
        }
    }, true); // Usar capture phase para ejecutarse antes que otros listeners
    
})();


