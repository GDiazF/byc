// ============================================================================
// JAVASCRIPT PARA LA PÁGINA DE LOGIN
// ============================================================================
// Este archivo maneja la lógica JavaScript para la página de inicio de sesión,
// incluyendo la visualización del modal de error cuando hay credenciales incorrectas.
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Mostrar modal de error si hay errores de login
    // Se verifica el atributo data-has-errors en el body que se establece desde el template
    const body = document.body;
    if (body.getAttribute('data-has-errors') === 'true') {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
});