// Funciones para manejar licencias médicas

// Función para calcular fecha fin de licencia
function calcularFechaFin() {
    const fechaEmision = document.getElementById('id_fechaEmision');
    const diasLicencia = document.getElementById('id_dias_licencia');
    const fechaFinElement = document.getElementById('fecha_fin_licencia');
    
    if (fechaEmision && diasLicencia && fechaFinElement) {
        const fechaEmisionValue = fechaEmision.value;
        const diasLicenciaValue = parseInt(diasLicencia.value);
        
        if (fechaEmisionValue && diasLicenciaValue) {
            const partes = fechaEmisionValue.split('-');
            // yyyy-mm-dd
            const fecha = new Date(partes[0], partes[1] - 1, partes[2]);
            fecha.setDate(fecha.getDate() + diasLicenciaValue - 1);
            const yyyy = fecha.getFullYear();
            const mm = String(fecha.getMonth() + 1).padStart(2, '0');
            const dd = String(fecha.getDate()).padStart(2, '0');
            fechaFinElement.value = `${dd}-${mm}-${yyyy}`;
        } else {
            fechaFinElement.value = '';
        }
    }
}

// Inicializar eventos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Eventos para calcular fecha fin
    const fechaEmision = document.getElementById('id_fechaEmision');
    const diasLicencia = document.getElementById('id_dias_licencia');
    
    if (fechaEmision) {
        fechaEmision.addEventListener('change', calcularFechaFin);
    }
    
    if (diasLicencia) {
        diasLicencia.addEventListener('input', calcularFechaFin);
    }
    
    // Calcular fecha fin al cargar la página
    calcularFechaFin();
}); 