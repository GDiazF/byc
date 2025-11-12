// Variables globales
let paginaActual = 1;
let tamanoPagina = 10;
let pautaIdAccion = null;
let modeloActual = null;
let ordenActual = '';
let direccionOrden = 'asc';

// Cargar modelos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarModelos();
    
    // Event listeners para filtros
    document.getElementById('searchInput').addEventListener('input', debounce(cargarModelos, 500));
    document.getElementById('tipoFilter').addEventListener('change', cargarModelos);
    document.getElementById('marcaFilter').addEventListener('change', cargarModelos);
    document.getElementById('modeloFilter').addEventListener('change', cargarModelos);
    document.getElementById('perPageSelect').addEventListener('change', function() {
        tamanoPagina = parseInt(this.value);
        paginaActual = 1;
        cargarModelos();
    });
    
    // Event listeners para ordenamiento por columnas
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const columna = this.getAttribute('data-column');
            ordenarPor(columna, this);
        });
    });
});

// Función debounce para búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Cargar modelos con filtros
function cargarModelos() {
    const search = document.getElementById('searchInput').value;
    const tipo = document.getElementById('tipoFilter').value;
    const marca = document.getElementById('marcaFilter').value;
    const modelo = document.getElementById('modeloFilter').value;
    
    const params = new URLSearchParams({
        search: search,
        tipo_equipo_id: tipo,
        marca_id: marca,
        modelo_id: modelo,
        order_by: ordenActual,
        direction: direccionOrden,
        page: paginaActual,
        per_page: tamanoPagina
    });
    
    fetch(`/maquinarias/api/pautas-mantenimiento/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarModelos(data.modelos);
                renderizarPaginacion(data);
                actualizarEstadisticas(data.total, data);
            } else {
                mostrarError('Error al cargar modelos: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar modelos');
        });
}

// Renderizar tabla de modelos
function renderizarModelos(modelos) {
    const tbody = document.getElementById('modelosTableBody');
    
    if (modelos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-5">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No se encontraron modelos de equipo</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = modelos.map(modelo => `
        <tr>
            <td><strong>${modelo.modeloEquipo.nombre}</strong></td>
            <td>
                <span class="badge bg-secondary">${modelo.tipoEquipo.sigla}</span>
                <span class="ms-1">${modelo.tipoEquipo.nombre}</span>
            </td>
            <td>${modelo.marcaEquipo.nombre}</td>
            <td class="text-center">
                <a href="/maquinarias/pautas-mantenimiento/modelo/${modelo.modeloEquipo.modeloEquipo_id}/" 
                   class="btn btn-sm btn-primary" 
                   title="Ver pautas">
                    <i class="bi bi-eye"></i> ${modelo.total_pautas}
                </a>
            </td>
            <td class="text-center">
                <a href="/maquinarias/pautas-mantenimiento/crear/?modelo=${modelo.modeloEquipo.modeloEquipo_id}" 
                   class="btn btn-sm btn-success" 
                   title="Nueva pauta para este modelo">
                    <i class="bi bi-plus-circle"></i>
                </a>
            </td>
        </tr>
    `).join('');
}

// Renderizar paginación
function renderizarPaginacion(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.total_pages;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    const maxPaginas = 5;
    let inicio = Math.max(1, paginaActual - Math.floor(maxPaginas / 2));
    let fin = Math.min(totalPages, inicio + maxPaginas - 1);
    
    if (fin - inicio < maxPaginas - 1) {
        inicio = Math.max(1, fin - maxPaginas + 1);
    }
    
    if (inicio > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a>
            </li>
        `;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (fin < totalPages) {
        if (fin < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// Actualizar estadísticas
function actualizarEstadisticas(total, data) {
    document.getElementById('totalModelos').textContent = total;
    
    // Calcular rango de registros mostrados
    const inicio = total === 0 ? 0 : ((data.page - 1) * data.per_page) + 1;
    const fin = Math.min(data.page * data.per_page, total);
    
    document.getElementById('registroInicio').textContent = inicio;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistros').textContent = total;
}

// Cambiar página
function cambiarPagina(pagina) {
    paginaActual = pagina;
    cargarModelos();
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('tipoFilter').value = '';
    document.getElementById('marcaFilter').value = '';
    document.getElementById('modeloFilter').value = '';
    paginaActual = 1;
    cargarModelos();
}

// Ordenar por columna
function ordenarPor(columna, headerElement) {
    // Si es la misma columna, cambiar dirección
    if (ordenActual === columna) {
        direccionOrden = direccionOrden === 'asc' ? 'desc' : 'asc';
    } else {
        ordenActual = columna;
        direccionOrden = 'asc';
    }
    
    // Actualizar iconos en todos los headers
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up ms-1';
    });
    
    // Actualizar icono del header clickeado
    const icon = headerElement.querySelector('i');
    if (icon) {
        icon.className = direccionOrden === 'asc' ? 'bi bi-arrow-up ms-1' : 'bi bi-arrow-down ms-1';
    }
    
    paginaActual = 1;
    cargarModelos();
}

// Ya no se usan estas funciones porque ahora es una página dedicada
// Las funciones toggle y eliminar están en ver_pautas_modelo.html

// Mostrar notificación estilo alert
function showNotification(message, type = 'success') {
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 3000);
}

// Mostrar mensaje de éxito
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

