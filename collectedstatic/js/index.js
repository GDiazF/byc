document.addEventListener('DOMContentLoaded', function() {
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