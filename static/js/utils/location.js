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

    // Función para cargar comunas
    async function cargarComunas(regionId, comunaPreseleccionada = null) {
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
                const selected = comunaPreseleccionada && comuna.id == comunaPreseleccionada ? ' selected' : '';
                options += `<option value="${comuna.id}"${selected}>${comuna.nombre}</option>`;
            });
            
            comunaSelect.innerHTML = options;
        } catch (error) {
            console.error('Error:', error);
            alert('Error al cargar las comunas');
        }
    }

    // Cargar comunas al cambiar la región
    regionSelect.addEventListener('change', async function() {
        await cargarComunas(this.value);
    });

    // Si hay una región preseleccionada al cargar la página (modo edición), cargar sus comunas
    if (regionSelect.value) {
        const comunaPreseleccionada = comunaSelect.value;
        cargarComunas(regionSelect.value, comunaPreseleccionada);
    }
} 