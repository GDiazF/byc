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
    
    // Toggle sidebar
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        
        // Para móviles
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('show');
        }
    });
    
    // Cerrar sidebar al hacer clic en un enlace en móvil
    if (window.innerWidth <= 768) {
        const navLinks = document.querySelectorAll('.nav-link:not([data-bs-toggle="collapse"])');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                sidebar.classList.remove('show');
            });
        });
    }
    
    // Ajustar sidebar al cambiar tamaño de pantalla
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('show');
        } else {
            if (!sidebar.classList.contains('collapsed')) {
                sidebar.classList.add('show');
            }
        }
    });
});