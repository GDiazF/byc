// ============================================================================
// SCRIPT PARA LA PÁGINA DE CAMBIAR CONTRASEÑA
// ============================================================================
// Agrega clases de Bootstrap a los campos del formulario de cambio de contraseña
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Agregar clases de Bootstrap a los campos del formulario
    const inputs = document.querySelectorAll('input[type="password"]');
    inputs.forEach(input => {
        input.classList.add('form-control');
    });
});

