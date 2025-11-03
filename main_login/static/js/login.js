document.addEventListener('DOMContentLoaded', function() {
    // Mostrar modal de error si hay errores de login
    if (window.showLoginError) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
});