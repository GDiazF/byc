// ============================================================================
// DOCUMENTACIÓN DE MAQUINARIAS
// ============================================================================

let documentoAEliminar = null;
let tiposDocumentos = [];

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    cargarDocumentos();
});

function inicializarEventos() {
    // Select de tipo de documento - cambiar formulario dinámicamente
    const tipoDocumentoSelect = document.getElementById('tipoDocumentoSelect');
    if (tipoDocumentoSelect) {
        tipoDocumentoSelect.addEventListener('change', function() {
            actualizarFormularioSegunTipo();
        });
    }
    
    // Formulario de subir documento
    const formSubirDocumento = document.getElementById('formSubirDocumento');
    if (formSubirDocumento) {
        formSubirDocumento.addEventListener('submit', function(e) {
            e.preventDefault();
            subirDocumento();
        });
    }
    
    // Botón limpiar formulario
    const btnLimpiarForm = document.getElementById('btnLimpiarForm');
    if (btnLimpiarForm) {
        btnLimpiarForm.addEventListener('click', function() {
            limpiarFormulario();
        });
    }
    
    // Botón toggle historial
    const btnToggleHistorial = document.getElementById('btnToggleHistorial');
    if (btnToggleHistorial) {
        btnToggleHistorial.addEventListener('click', function() {
            toggleHistorial();
        });
    }
    
    // Botón confirmar eliminación
    const btnConfirmarEliminacion = document.getElementById('btnConfirmarEliminacion');
    if (btnConfirmarEliminacion) {
        btnConfirmarEliminacion.addEventListener('click', function() {
            if (documentoAEliminar) {
                eliminarDocumento(documentoAEliminar);
            }
        });
    }
}

// ============================================================================
// FUNCIONES PARA FORMULARIO DINÁMICO
// ============================================================================

function actualizarFormularioSegunTipo() {
    const tipoSelect = document.getElementById('tipoDocumentoSelect');
    const fechaVencimientoGroup = document.getElementById('fechaVencimientoGroup');
    const fechaVencimientoInput = document.getElementById('fechaVencimientoInput');
    
    if (!tipoSelect || !fechaVencimientoGroup) return;
    
    const selectedOption = tipoSelect.options[tipoSelect.selectedIndex];
    const requiereFecha = selectedOption.getAttribute('data-requiere-fecha') === 'true';
    
    if (requiereFecha) {
        fechaVencimientoGroup.classList.add('show');
        fechaVencimientoInput.setAttribute('required', 'required');
    } else {
        fechaVencimientoGroup.classList.remove('show');
        fechaVencimientoInput.removeAttribute('required');
        fechaVencimientoInput.value = '';
    }
}

function limpiarFormulario() {
    const form = document.getElementById('formSubirDocumento');
    if (form) {
        form.reset();
        actualizarFormularioSegunTipo();
    }
}

// ============================================================================
// FUNCIONES PARA CARGAR DOCUMENTOS
// ============================================================================

function cargarDocumentos() {
    const tbody = document.getElementById('documentosTbody');
    if (!tbody) return;
    
    fetch(window.DOCUMENTOS_URL)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarDocumentos(data.documentos);
            } else {
                mostrarError('Error al cargar documentos: ' + (data.error || 'Error desconocido'));
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Error al cargar documentos</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar documentos');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Error al cargar documentos</td></tr>';
        });
}

function renderizarDocumentos(documentos) {
    const tbody = document.getElementById('documentosTbody');
    if (!tbody) return;
    
    if (documentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="bi bi-folder-x fs-1"></i>
                    <p class="mt-2">No hay documentos registrados</p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    documentos.forEach(doc => {
        const estadoBadge = obtenerBadgeEstado(doc.estado, doc.dias_restantes);
        const fechaVencimiento = doc.fecha_vencimiento 
            ? formatearFechaChilena(doc.fecha_vencimiento) 
            : '<span class="text-muted">N/A</span>';
        const fechaSubida = formatearFechaChilena(doc.fecha_subida);
        
        html += `
            <tr>
                <td>${escapeHtml(doc.tipo_documento_nombre)}</td>
                <td>
                    ${doc.archivo_nombre ? escapeHtml(doc.archivo_nombre) : 'Sin archivo'}
                </td>
                <td>${fechaVencimiento}</td>
                <td class="text-center">${estadoBadge}</td>
                <td>${fechaSubida}</td>
                <td class="text-center">
                    ${doc.archivo_url ? `
                        <a href="${doc.archivo_url}" target="_blank" class="btn btn-sm btn-primary me-1" title="Ver documento">
                            <i class="bi bi-eye"></i>
                        </a>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="mostrarModalEliminacion(${doc.id})" title="Eliminar documento">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function obtenerBadgeEstado(estado, diasRestantes) {
    if (!diasRestantes && diasRestantes !== 0) {
        return '<span class="badge bg-success estado-badge">Vigente</span>';
    }
    
    if (estado === 'vencido') {
        return `<span class="badge bg-danger estado-badge">Vencido</span>`;
    } else if (estado === 'por_vencer') {
        return `<span class="badge bg-warning text-dark estado-badge">Por vencer (${diasRestantes}d)</span>`;
    } else {
        return `<span class="badge bg-success estado-badge">Vigente (${diasRestantes}d)</span>`;
    }
}

// ============================================================================
// FUNCIONES PARA SUBIR DOCUMENTO
// ============================================================================

function subirDocumento() {
    const form = document.getElementById('formSubirDocumento');
    if (!form) return;
    
    const formData = new FormData(form);
    const tipoDocumentoId = formData.get('tipo_documento_id');
    const archivo = formData.get('archivo');
    
    if (!tipoDocumentoId || !archivo) {
        mostrarError('Por favor complete todos los campos requeridos');
        return;
    }
    
    // Validar que sea PDF
    if (!archivo.name.toLowerCase().endsWith('.pdf')) {
        mostrarError('Solo se aceptan archivos PDF');
        return;
    }
    
    // Deshabilitar botón de envío
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Subiendo...';
    
    fetch(window.SUBIR_DOCUMENTO_URL, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message || 'Documento subido correctamente');
            limpiarFormulario();
            cargarDocumentos();
        } else {
            mostrarError(data.error || 'Error al subir documento');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al subir documento');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

// ============================================================================
// FUNCIONES PARA ELIMINAR DOCUMENTO
// ============================================================================

function mostrarModalEliminacion(documentoId) {
    documentoAEliminar = documentoId;
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminacion'));
    modal.show();
}

function eliminarDocumento(documentoId) {
    if (!documentoId) return;
    
    const url = window.ELIMINAR_DOCUMENTO_URL.replace('0', documentoId);
    
    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarEliminacion'));
        if (modal) modal.hide();
        
        if (data.success) {
            mostrarExito(data.message || 'Documento eliminado correctamente');
            cargarDocumentos();
            // Si el historial está visible, recargarlo también
            const historialContainer = document.getElementById('historialContainer');
            if (historialContainer && historialContainer.style.display !== 'none') {
                cargarHistorial();
            }
        } else {
            mostrarError(data.error || 'Error al eliminar documento');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al eliminar documento');
    })
    .finally(() => {
        documentoAEliminar = null;
    });
}

// ============================================================================
// FUNCIONES PARA HISTORIAL
// ============================================================================

function toggleHistorial() {
    const container = document.getElementById('historialContainer');
    const btn = document.getElementById('btnToggleHistorial');
    
    if (!container || !btn) return;
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        btn.innerHTML = '<i class="bi bi-chevron-up me-1"></i>Ocultar Historial';
        cargarHistorial();
    } else {
        container.style.display = 'none';
        btn.innerHTML = '<i class="bi bi-chevron-down me-1"></i>Mostrar Historial';
    }
}

function cargarHistorial() {
    const tbody = document.getElementById('historialTbody');
    if (!tbody) return;
    
    fetch(window.HISTORIAL_URL)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderizarHistorial(data.historial);
            } else {
                mostrarError('Error al cargar historial: ' + (data.error || 'Error desconocido'));
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Error al cargar historial</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar historial');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Error al cargar historial</td></tr>';
        });
}

function renderizarHistorial(historial) {
    const tbody = document.getElementById('historialTbody');
    if (!tbody) return;
    
    if (historial.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="bi bi-folder-x fs-1"></i>
                    <p class="mt-2">No hay documentos en el historial</p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    historial.forEach(item => {
        const fechaVencimiento = item.fecha_vencimiento 
            ? formatearFechaChilena(item.fecha_vencimiento) 
            : '<span class="text-muted">N/A</span>';
        const fechaSubidaOriginal = item.fecha_subida_original 
            ? formatearFechaChilena(item.fecha_subida_original) 
            : '<span class="text-muted">N/A</span>';
        const fechaReemplazo = formatearFechaChilena(item.fecha_reemplazo);
        
        html += `
            <tr>
                <td>${escapeHtml(item.tipo_documento_nombre)}</td>
                <td>
                    ${item.archivo_nombre ? escapeHtml(item.archivo_nombre) : 'Sin archivo'}
                </td>
                <td>${fechaVencimiento}</td>
                <td>${fechaSubidaOriginal}</td>
                <td>${fechaReemplazo}</td>
                <td class="text-center">
                    ${item.archivo_url ? `
                        <a href="${item.archivo_url}" target="_blank" class="btn btn-sm btn-primary" title="Ver documento">
                            <i class="bi bi-eye"></i>
                        </a>
                    ` : ''}
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

function formatearFechaChilena(fechaISO) {
    if (!fechaISO) return '';
    
    const fecha = new Date(fechaISO);
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const año = fecha.getFullYear();
    
    return `${dia}-${mes}-${año}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function mostrarExito(mensaje) {
    // Usar toast de Bootstrap si está disponible, sino alert
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        // Crear toast dinámicamente
        const toastContainer = document.getElementById('toast-container') || crearToastContainer();
        const toast = crearToast('success', mensaje);
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    } else {
        alert('✓ ' + mensaje);
    }
}

function mostrarError(mensaje) {
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toastContainer = document.getElementById('toast-container') || crearToastContainer();
        const toast = crearToast('danger', mensaje);
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    } else {
        alert('✗ ' + mensaje);
    }
}

function crearToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function crearToast(tipo, mensaje) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${escapeHtml(mensaje)}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    return toast;
}

