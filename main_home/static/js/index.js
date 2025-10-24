// Función para ocultar el spinner
function hideSpinner() {
    const body = document.body;
    const contentLoading = document.getElementById('contentLoading');
    
    if (body && contentLoading) {
        // Cambiar clase del body
        body.classList.remove('loading');
        body.classList.add('loaded');
        
        // Ocultar spinner después de la transición
        setTimeout(function() {
            if (contentLoading) {
                contentLoading.style.display = 'none';
                contentLoading.style.pointerEvents = 'none'; // Asegurar que no bloquee clics
            }
        }, 500);
    }
}

        // Función para verificar si los estilos están cargados
        function checkStylesLoaded() {
            // Verificar que Bootstrap CSS esté cargado
            const testElement = document.createElement('div');
            testElement.className = 'container-fluid';
            testElement.style.display = 'none';
            document.body.appendChild(testElement);
            
            const computedStyle = window.getComputedStyle(testElement);
            const isBootstrapLoaded = computedStyle.paddingLeft !== '' || computedStyle.paddingRight !== '';
            
            document.body.removeChild(testElement);
            
            // Si estamos en la página de personal, verificar también DataTables
            if (window.location.pathname.includes('/personal/')) {
                const dataTable = document.querySelector('#personalTable');
                if (dataTable) {
                    const dataTableStyle = window.getComputedStyle(dataTable);
                    const isDataTableStyled = dataTableStyle.display === 'table' || 
                                            dataTable.classList.contains('dataTable') ||
                                            dataTable.querySelector('.dataTables_wrapper');
                    return isBootstrapLoaded && isDataTableStyled;
                }
            }
            
            return isBootstrapLoaded;
        }

        // Función para ocultar el spinner cuando los estilos estén listos
        function waitForStyles() {
            if (checkStylesLoaded()) {
                hideSpinner();
            } else {
                // Reintentar cada 50ms hasta que los estilos estén listos
                setTimeout(waitForStyles, 50);
            }
        }

        // Esperar a que la página esté completamente cargada
        window.addEventListener('load', function() {
            // Esperar a que los estilos estén realmente cargados
            waitForStyles();
        });

        // Fallback: si la página ya está cargada
        if (document.readyState === 'complete') {
            waitForStyles();
        }

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