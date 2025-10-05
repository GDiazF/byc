document.addEventListener('DOMContentLoaded', function() {
    const formElement = document.querySelector('form');
    
    if (formElement && formElement.classList.contains('has-errors')) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
});