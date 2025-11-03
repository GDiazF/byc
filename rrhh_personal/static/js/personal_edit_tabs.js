// Manejo de tabs en edición de personal

document.addEventListener('DOMContentLoaded', function() {
    // Configurar el manejador de departamento/cargo si existe
    if (typeof setupDepartmentCargoHandlers === 'function') {
        setupDepartmentCargoHandlers();
    }

    // Mantener la pestaña activa después de enviar el formulario
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    if (activeTab) {
        const tab = new bootstrap.Tab(document.querySelector(`#${activeTab}-tab`));
        tab.show();
    }

    // Actualizar la URL cuando se cambia de pestaña
    const triggerTabList = document.querySelectorAll('#personalTabs button');
    triggerTabList.forEach(triggerEl => {
        triggerEl.addEventListener('shown.bs.tab', function(event) {
            const tabId = event.target.id.replace('-tab', '');
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('tab', tabId);
            window.history.pushState({}, '', newUrl);
        });
    });
});

