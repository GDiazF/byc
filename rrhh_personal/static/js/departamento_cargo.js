// ============================================================================
// MANEJO DE CARGOS SEGÚN DEPARTAMENTO - VANILLA JS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const deptoSelect = document.getElementById('id_depto_id');
    const cargoSelect = document.getElementById('id_cargo_id');
    
    if (!deptoSelect || !cargoSelect) {
        console.warn('Elementos de departamento o cargo no encontrados');
        return;
    }
    
    // Event listener para cambio de departamento
    deptoSelect.addEventListener('change', function() {
        const deptoId = this.value;
        
        if (deptoId) {
            // Realizar petición AJAX para obtener cargos
            fetch(`/users/personal/get_cargos/?depto_id=${deptoId}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al cargar los cargos');
                }
                return response.json();
            })
            .then(data => {
                // Limpiar select de cargos
                cargoSelect.innerHTML = '';
                
                // Agregar opción por defecto
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Elija una opción';
                cargoSelect.appendChild(defaultOption);
                
                // Agregar opciones de cargos
                Object.entries(data).forEach(([id, nombre]) => {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = nombre;
                    cargoSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                // Limpiar y mostrar error
                cargoSelect.innerHTML = '<option value="">Error al cargar cargos</option>';
            });
        } else {
            // Si no hay departamento seleccionado, limpiar cargos
            cargoSelect.innerHTML = '<option value="">Elija una opción</option>';
        }
    });
});

