/**
 * Maneja la actualización de cargos basado en el departamento seleccionado
 * @param {string} deptoSelectId - ID del select de departamento
 * @param {string} cargoSelectId - ID del select de cargo
 */
function setupDepartmentCargoHandlers(deptoSelectId = 'id_depto_id', cargoSelectId = 'id_cargo_id') {
    const deptoSelect = document.getElementById(deptoSelectId);
    const cargoSelect = document.getElementById(cargoSelectId);

    if (!deptoSelect || !cargoSelect) {
        console.error('No se encontraron los elementos de departamento o cargo');
        return;
    }

    deptoSelect.addEventListener('change', async function() {
        const deptoId = this.value;
        
        if (!deptoId) {
            cargoSelect.innerHTML = '<option value="">---------</option>';
            return;
        }

        try {
            const response = await fetch(`/users/personal/get_cargos/?depto_id=${deptoId}`);
            if (!response.ok) {
                throw new Error('Error al obtener los cargos');
            }

            const data = await response.json();
            let options = '<option value="">---------</option>';
            
            // Los datos vienen como un objeto con cargo_id como clave y cargo como valor
            Object.entries(data).forEach(([cargoId, cargoName]) => {
                options += `<option value="${cargoId}">${cargoName}</option>`;
            });
            
            cargoSelect.innerHTML = options;
        } catch (error) {
            console.error('Error:', error);
            alert('Error al cargar los cargos');
        }
    });
}
