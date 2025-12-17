// Función para ocultar el spinner
function hideSpinner() {
    const body = document.body;
    const contentLoading = document.getElementById('contentLoading');
    
    if (body && contentLoading) {
        body.classList.remove('loading');
        body.classList.add('loaded');
        
        setTimeout(function() {
            if (contentLoading) {
                contentLoading.style.display = 'none';
                contentLoading.style.pointerEvents = 'none';
            }
        }, 200);
    }
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // 1. Ocultar spinner
    hideSpinner();
    
    // 2. Auto-hide messages after 5 seconds (excepto .alert-permanent)
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // 3. Configurar sidebar
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainContent = document.getElementById('mainContent');
    
    // Inicializar sidebar como colapsado por defecto
    sidebar.classList.add('collapsed');
    
    // Variables para manejar hover en desktop
    let hoverTimeout;
    let isDesktop = window.innerWidth > 768;
    
    // Toggle sidebar - funciona en desktop y móvil
    sidebarToggle.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            // En móvil: toggle normal
            sidebar.classList.toggle('show');
            sidebar.classList.toggle('collapsed');
        } else {
            // En desktop: abrir sidebar y mantenerlo abierto temporalmente
            clearTimeout(hoverTimeout);
            sidebar.classList.remove('collapsed');
            sidebar.classList.add('hover-active');
            // Mantener abierto por más tiempo después del click
            hoverTimeout = setTimeout(function() {
                if (!sidebar.classList.contains('show')) {
                    sidebar.classList.add('collapsed');
                    sidebar.classList.remove('hover-active');
                }
            }, 5000); // Mantener abierto 5 segundos después del click
        }
    });
    
    // Hover sobre el botón hamburguesa en desktop
    sidebarToggle.addEventListener('mouseenter', function() {
        if (isDesktop) {
            clearTimeout(hoverTimeout);
            sidebar.classList.remove('collapsed');
            sidebar.classList.add('hover-active');
        }
    });
    
    // Cerrar sidebar al hacer clic en un enlace en móvil
    if (window.innerWidth <= 768) {
        const navLinks = document.querySelectorAll('.nav-link:not([data-bs-toggle="collapse"])');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                sidebar.classList.remove('show');
                sidebar.classList.add('collapsed');
            });
        });
    }
    
    function handleDesktopHover(e) {
        if (!isDesktop) return;
        
        // Si el mouse está dentro de los primeros 15px del borde izquierdo
        // O si está sobre el botón hamburguesa (que está en el navbar)
        const toggleButton = document.getElementById('sidebarToggle');
        const toggleRect = toggleButton ? toggleButton.getBoundingClientRect() : null;
        const isOverToggle = toggleRect && 
                            e.clientX >= toggleRect.left && 
                            e.clientX <= toggleRect.right &&
                            e.clientY >= toggleRect.top && 
                            e.clientY <= toggleRect.bottom;
        
        if (e.clientX <= 15 || isOverToggle) {
            clearTimeout(hoverTimeout);
            sidebar.classList.remove('collapsed');
            sidebar.classList.add('hover-active');
        } else if (e.clientX > 250 && e.clientY > 100) {
            // Si el mouse está lejos del sidebar (y no está cerca del navbar), cerrarlo después de un delay
            hoverTimeout = setTimeout(function() {
                if (!sidebar.classList.contains('show')) {
                    sidebar.classList.add('collapsed');
                    sidebar.classList.remove('hover-active');
                }
            }, 150);
        }
    }
    
    // Detectar movimiento del mouse para abrir sidebar en desktop
    document.addEventListener('mousemove', handleDesktopHover);
    
    // Mantener abierto cuando el mouse está sobre el sidebar
    sidebar.addEventListener('mouseenter', function() {
        if (!isDesktop) return;
        clearTimeout(hoverTimeout);
        sidebar.classList.remove('collapsed');
        sidebar.classList.add('hover-active');
    });
    
    sidebar.addEventListener('mouseleave', function() {
        if (!isDesktop) return;
        hoverTimeout = setTimeout(function() {
            if (!sidebar.classList.contains('show')) {
                sidebar.classList.add('collapsed');
                sidebar.classList.remove('hover-active');
            }
        }, 150);
    });
    
    // Ajustar sidebar al cambiar tamaño de pantalla
    window.addEventListener('resize', function() {
        const wasDesktop = isDesktop;
        isDesktop = window.innerWidth > 768;
        
        if (isDesktop) {
            // En desktop, siempre colapsado (se abre con hover)
            sidebar.classList.remove('show');
            if (!sidebar.classList.contains('hover-active')) {
                sidebar.classList.add('collapsed');
            }
        } else {
            // En móvil, remover hover-active
            sidebar.classList.remove('hover-active');
        }
    });
    
    // Ajustar posicionamiento de dropdowns en móviles
    function ajustarDropdownsMovil() {
        if (window.innerWidth <= 768) {
            const notificationDropdown = document.querySelector('.dropdown-menu-notifications');
            const userDropdown = document.querySelector('#userDropdown + .dropdown-menu');
            
            // Ajustar dropdown de notificaciones
            if (notificationDropdown) {
                const toggle = document.getElementById('notificationsDropdown');
                if (toggle) {
                    const rect = toggle.getBoundingClientRect();
                    notificationDropdown.style.top = (rect.bottom + window.scrollY + 5) + 'px';
                    notificationDropdown.style.left = '0.5rem';
                    notificationDropdown.style.right = 'auto';
                    notificationDropdown.style.width = 'calc(100vw - 1rem)';
                }
            }
            
            // Ajustar dropdown de usuario
            if (userDropdown) {
                const toggle = document.getElementById('userDropdown');
                if (toggle) {
                    const rect = toggle.getBoundingClientRect();
                    userDropdown.style.top = (rect.bottom + window.scrollY + 5) + 'px';
                    userDropdown.style.left = '0.5rem';
                    userDropdown.style.right = 'auto';
                    userDropdown.style.width = 'calc(100vw - 1rem)';
                }
            }
        }
    }
    
    // Ajustar dropdowns cuando se abren
    document.addEventListener('shown.bs.dropdown', function(e) {
        ajustarDropdownsMovil();
    });
    
    // Ajustar dropdowns al redimensionar
    window.addEventListener('resize', ajustarDropdownsMovil);
});