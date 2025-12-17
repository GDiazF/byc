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
    
    // Toggle para mostrar/ocultar contraseña
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('id_password');
    const togglePasswordIcon = document.getElementById('togglePasswordIcon');
    
    if (togglePassword && passwordInput && togglePasswordIcon) {
        // Función para alternar la visibilidad de la contraseña
        function togglePasswordVisibility(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            // Alternar tipo de input entre password y text
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Cambiar ícono entre ojo abierto y cerrado
            if (type === 'text') {
                togglePasswordIcon.classList.remove('bi-eye');
                togglePasswordIcon.classList.add('bi-eye-slash');
                togglePassword.setAttribute('aria-label', 'Ocultar contraseña');
            } else {
                togglePasswordIcon.classList.remove('bi-eye-slash');
                togglePasswordIcon.classList.add('bi-eye');
                togglePassword.setAttribute('aria-label', 'Mostrar contraseña');
            }
        }
        
        // Agregar múltiples eventos para compatibilidad móvil y desktop
        togglePassword.addEventListener('click', togglePasswordVisibility);
        togglePassword.addEventListener('touchend', function(e) {
            // Prevenir el doble evento (click después de touchend)
            e.preventDefault();
            togglePasswordVisibility(e);
        });
    }
});