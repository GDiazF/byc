/**
 * Maneja la actualización de comunas basado en la región seleccionada
 * @param {string} regionSelectId - ID del select de región
 * @param {string} comunaSelectId - ID del select de comuna
 */
function setupRegionComunaHandlers(regionSelectId = 'id_region_id', comunaSelectId = 'id_comuna_id') {
    const regionSelect = document.getElementById(regionSelectId);
    const comunaSelect = document.getElementById(comunaSelectId);

    if (!regionSelect || !comunaSelect) {
        console.error('No se encontraron los elementos de región o comuna');
        return;
    }

    regionSelect.addEventListener('change', async function() {
        const regionId = this.value;
        
        if (!regionId) {
            comunaSelect.innerHTML = '<option value="">---------</option>';
            return;
        }

        try {
            const response = await fetch(`/gen_settings/ajax/load-comunas/?region_id=${regionId}`);
            if (!response.ok) {
                throw new Error('Error al obtener las comunas');
            }

            const data = await response.json();
            let options = '<option value="">---------</option>';
            
            data.comunas.forEach(comuna => {
                options += `<option value="${comuna.id}">${comuna.nombre}</option>`;
            });
            
            comunaSelect.innerHTML = options;
        } catch (error) {
            console.error('Error:', error);
            alert('Error al cargar las comunas');
        }
    });
} 