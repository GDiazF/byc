// ============================================================================
// GESTIÓN DE DOCUMENTACIÓN DE PERSONAL
// ============================================================================

// ============================================================================
// UTILIDADES GLOBALES
// ============================================================================

// Get CSRF token from cookie
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

// Función para mostrar notificaciones
function showNotification(title, message, type = 'success') {
    const modal = document.getElementById('notificationModal');
    const modalTitle = document.getElementById('notificationTitle');
    const modalMessage = document.getElementById('notificationMessage');
    const modalHeader = modal.querySelector('.modal-header');
    
    modalHeader.className = 'modal-header';
    if (type === 'success') {
        modalHeader.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        modalHeader.classList.add('bg-danger', 'text-white');
    }
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    if (type === 'success') {
        modal.addEventListener('hidden.bs.modal', function handler() {
            window.location.reload();
            modal.removeEventListener('hidden.bs.modal', handler);
        });
    }
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tabs
    initializeTabs();
    
    // Initialize modal handlers
    initializeModalHandlers();
    
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize delete buttons
    initializeDeleteButtons();
    
    // Initialize edit buttons
    initializeEditButtons();
    
    // Initialize personal document handlers
    initializePersonalDocumentHandlers();
});

// ============================================================================
// TABS
// ============================================================================

function initializeTabs() {
    const triggerTabList = [].slice.call(document.querySelectorAll('#docTabs button'));
    triggerTabList.forEach(function(triggerEl) {
        new bootstrap.Tab(triggerEl);
    });

    // Mantener la pestaña activa después de enviar el formulario
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    if (activeTab) {
        const tab = new bootstrap.Tab(document.querySelector(`#${activeTab}-tab`));
        tab.show();
    }

    // Actualizar la URL cuando se cambia de pestaña
    triggerTabList.forEach(triggerEl => {
        triggerEl.addEventListener('shown.bs.tab', function(event) {
            const tabId = event.target.id.replace('-tab', '');
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('tab', tabId);
            window.history.pushState({}, '', newUrl);
        });
    });
}

// ============================================================================
// MODAL HANDLERS
// ============================================================================

function initializeModalHandlers() {
    // Licencia de conducir
    const addLicenseModal = document.getElementById('addLicenseModal');
    if (addLicenseModal) {
        addLicenseModal.addEventListener('shown.bs.modal', initializeLicenseForm);
        addLicenseModal.addEventListener('hidden.bs.modal', () => {
            resetModalForm('licenseForm', 'license_id', 'Agregar Licencia de Conducir');
        });
    }

    // Licencia interna
    const addInternalLicenseModal = document.getElementById('addInternalLicenseModal');
    if (addInternalLicenseModal) {
        addInternalLicenseModal.addEventListener('shown.bs.modal', initializeInternalLicenseForm);
        addInternalLicenseModal.addEventListener('hidden.bs.modal', () => {
            resetModalForm('internalLicenseForm', 'license_id', 'Agregar Licencia Interna');
        });
    }

    // Examen
    const addExamModal = document.getElementById('addExamModal');
    if (addExamModal) {
        addExamModal.addEventListener('shown.bs.modal', initializeExamForm);
        addExamModal.addEventListener('hidden.bs.modal', () => {
            resetModalForm('examForm', 'exam_id', 'Agregar Examen');
        });
    }

    // Certificación
    const addCertificationModal = document.getElementById('addCertificationModal');
    if (addCertificationModal) {
        addCertificationModal.addEventListener('shown.bs.modal', initializeCertificationForm);
        addCertificationModal.addEventListener('hidden.bs.modal', () => {
            resetModalForm('certificationForm', 'cert_id', 'Agregar Certificación');
        });
    }
}

function resetModalForm(formId, hiddenIdName, modalTitle) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        
        // Remover campo oculto de ID
        const hiddenId = form.querySelector(`[name="${hiddenIdName}"]`);
        if (hiddenId) hiddenId.remove();
        
        // Remover información de documento existente
        const existingDocInfo = form.querySelector('.existing-document-info');
        if (existingDocInfo) existingDocInfo.remove();
        
        // Restaurar campo de archivo como requerido
        const fileInput = form.querySelector('[name="rutaDoc"]');
        if (fileInput) fileInput.required = true;
    }
    
    // Resetear título del modal
    const modal = document.getElementById(formId.replace('Form', 'Modal'));
    if (modal) {
        const titleEl = modal.querySelector('.modal-title');
        if (titleEl) titleEl.textContent = modalTitle;
    }
}

// ============================================================================
// FORM HANDLERS
// ============================================================================

function initializeFormHandlers() {
    // Ya no necesitamos inicializar aquí porque lo hacemos en los eventos shown.bs.modal
}

function initializeLicenseForm() {
    const form = document.getElementById('licenseForm');
    if (form && !form.dataset.initialized) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(this, 'license');
        });
        form.dataset.initialized = 'true';
    }
}

function initializeInternalLicenseForm() {
    const form = document.getElementById('internalLicenseForm');
    if (form && !form.dataset.initialized) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(this, 'internal-license');
        });
        form.dataset.initialized = 'true';
    }
}

function initializeExamForm() {
    const form = document.getElementById('examForm');
    if (form && !form.dataset.initialized) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(this, 'exam');
        });
        form.dataset.initialized = 'true';
    }
}

function initializeCertificationForm() {
    const form = document.getElementById('certificationForm');
    if (form && !form.dataset.initialized) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(this, 'certification');
        });
        form.dataset.initialized = 'true';
    }
}

// ============================================================================
// SUBMIT FORM
// ============================================================================

async function submitForm(form, type) {
    const formData = new FormData(form);
    let url;
    
    // Determinar URL según tipo y si es edición o creación
    const licenseId = form.querySelector('[name="license_id"]');
    const certId = form.querySelector('[name="cert_id"]');
    const examId = form.querySelector('[name="exam_id"]');
    
    if (type === 'internal-license' && licenseId && licenseId.value) {
        url = `/users/personal/${licenseId.value}/edit_internal_license/`;
    } else if (type === 'license' && licenseId && licenseId.value) {
        url = `/users/personal/${licenseId.value}/edit_license/`;
    } else if (type === 'certification' && certId && certId.value) {
        url = `/users/personal/${certId.value}/edit_certification/`;
    } else if (type === 'exam' && examId && examId.value) {
        url = `/users/personal/${examId.value}/edit_exam/`;
    } else {
        // URLs para crear nuevos registros - estas deben venir del template
        url = form.dataset.submitUrl;
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        // Cerrar el modal
        const modalId = {
            'license': 'addLicenseModal',
            'internal-license': 'addInternalLicenseModal',
            'exam': 'addExamModal',
            'certification': 'addCertificationModal'
        }[type];
        
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        }
        
        if (data.status === 'success') {
            showNotification('Éxito', data.message, 'success');
        } else {
            if (data.errors) {
                handleFormErrors(form, data.errors);
            }
            showNotification('Error', data.message || 'Error al guardar', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', `Error al procesar la solicitud: ${error.message}`, 'error');
    }
}

function handleFormErrors(form, errors) {
    // Limpiar errores previos
    form.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');
    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    
    // Mostrar nuevos errores
    Object.entries(errors).forEach(([field, fieldErrors]) => {
        const fieldElement = form.querySelector(`[name="${field}"]`);
        if (fieldElement) {
            fieldElement.classList.add('is-invalid');
            const errorDiv = fieldElement.nextElementSibling;
            if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                errorDiv.textContent = Array.isArray(fieldErrors) ? fieldErrors.join(', ') : fieldErrors;
            }
        }
    });
}

// ============================================================================
// EDIT FUNCTIONS
// ============================================================================

function initializeEditButtons() {
    document.querySelectorAll('.edit-license').forEach(button => {
        button.addEventListener('click', function() {
            editLicense(this.dataset.id);
        });
    });

    document.querySelectorAll('.edit-internal-license').forEach(button => {
        button.addEventListener('click', function() {
            editInternalLicense(this.dataset.id);
        });
    });

    document.querySelectorAll('.edit-certification').forEach(button => {
        button.addEventListener('click', function() {
            editCertification(this.dataset.id);
        });
    });

    document.querySelectorAll('.edit-exam').forEach(button => {
        button.addEventListener('click', function() {
            editExam(this.dataset.id);
        });
    });
}

async function editLicense(licenseId) {
    try {
        const response = await fetch(`/users/personal/${licenseId}/edit_license/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const form = document.getElementById('licenseForm');
            if (!form) {
                console.error('Formulario licenseForm no encontrado');
                return;
            }
            
            // Cambiar título
            document.querySelector('#addLicenseModal .modal-title').textContent = 'Editar Licencia de Conducir';
            
            // Llenar campos
            const fechaEmision = form.querySelector('[name="fechaEmision"]');
            const fechaVencimiento = form.querySelector('[name="fechaVencimiento"]');
            
            if (fechaEmision) fechaEmision.value = data.license_data.fecha_emision;
            if (fechaVencimiento) fechaVencimiento.value = data.license_data.fecha_vencimiento;
            
            // Seleccionar tipos (checkboxes)
            form.querySelectorAll('[name="tipos"]').forEach(checkbox => {
                checkbox.checked = data.license_data.tipos.includes(parseInt(checkbox.value));
            });
            
            // Manejar documento existente
            handleExistingDocument(form, data.license_data);
            
            // Agregar campo oculto de ID
            addHiddenId(form, 'license_id', licenseId);
            
            // Mostrar modal
            new bootstrap.Modal(document.getElementById('addLicenseModal')).show();
        } else {
            alert('Error al cargar los datos: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos: ' + error.message);
    }
}

async function editInternalLicense(licenseId) {
    try {
        const response = await fetch(`/users/personal/${licenseId}/edit_internal_license/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const form = document.getElementById('internalLicenseForm');
            if (!form) return;
            
            document.querySelector('#addInternalLicenseModal .modal-title').textContent = 'Editar Licencia Interna';
            
            form.querySelector('[name="tipoLicenciaInterna_id"]').value = data.license_data.tipo_id;
            form.querySelector('[name="numero_licencia"]').value = data.license_data.numero || '';
            form.querySelector('[name="empresa_emisora"]').value = data.license_data.empresa || '';
            form.querySelector('[name="fechaEmision"]').value = data.license_data.fecha_emision;
            form.querySelector('[name="fechaVencimiento"]').value = data.license_data.fecha_vencimiento;
            form.querySelector('[name="observacion"]').value = data.license_data.observacion || '';
            form.querySelector('[name="activo"]').checked = data.license_data.activo;
            
            handleExistingDocument(form, data.license_data);
            addHiddenId(form, 'license_id', licenseId);
            
            new bootstrap.Modal(document.getElementById('addInternalLicenseModal')).show();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos');
    }
}

async function editCertification(certId) {
    try {
        const response = await fetch(`/users/personal/${certId}/edit_certification/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const form = document.getElementById('certificationForm');
            if (!form) return;
            
            document.querySelector('#addCertificationModal .modal-title').textContent = 'Editar Certificación';
            
            form.querySelector('[name="tipoCertificacion_id"]').value = data.cert_data.tipo_id;
            form.querySelector('[name="proveedor_id"]').value = data.cert_data.proveedor_id;
            form.querySelector('[name="fechaEmision"]').value = data.cert_data.fecha_emision;
            form.querySelector('[name="fechaVencimiento"]').value = data.cert_data.fecha_vencimiento;
            
            handleExistingDocument(form, data.cert_data);
            addHiddenId(form, 'cert_id', certId);
            
            new bootstrap.Modal(document.getElementById('addCertificationModal')).show();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos');
    }
}

async function editExam(examId) {
    try {
        const response = await fetch(`/users/personal/${examId}/edit_exam/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const form = document.getElementById('examForm');
            if (!form) return;
            
            document.querySelector('#addExamModal .modal-title').textContent = 'Editar Examen';
            
            form.querySelector('[name="tipoEx_id"]').value = data.exam_data.tipo_id;
            form.querySelector('[name="resultadoEx_id"]').value = data.exam_data.resultado_id;
            form.querySelector('[name="proveedor_id"]').value = data.exam_data.proveedor_id;
            form.querySelector('[name="fechaEmision"]').value = data.exam_data.fecha_emision;
            form.querySelector('[name="fechaVencimiento"]').value = data.exam_data.fecha_vencimiento;
            
            handleExistingDocument(form, data.exam_data);
            addHiddenId(form, 'exam_id', examId);
            
            new bootstrap.Modal(document.getElementById('addExamModal')).show();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos');
    }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function handleExistingDocument(form, data) {
    const fileInput = form.querySelector('[name="rutaDoc"]');
    if (!fileInput) return;
    
    fileInput.required = false;
    
    if (data.documento_url) {
        const fileContainer = fileInput.parentElement;
        let existingDocInfo = fileContainer.querySelector('.existing-document-info');
        
        if (!existingDocInfo) {
            existingDocInfo = document.createElement('div');
            existingDocInfo.className = 'existing-document-info mt-2';
            fileContainer.appendChild(existingDocInfo);
        }
        
        const fileName = data.documento_nombre ? 
            data.documento_nombre.split('/').pop() : 'Documento actual';
        
        const shortFileName = fileName.length > 30 ? 
            fileName.substring(0, 27) + '...' : fileName;
        
        existingDocInfo.innerHTML = `
            <div class="alert alert-info d-flex justify-content-between align-items-center">
                <div class="flex-grow-1">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    <strong>Documento actual:</strong> 
                    <a href="${data.documento_url}" target="_blank" class="text-decoration-none" title="${fileName}">
                        ${shortFileName}
                    </a>
                </div>
                <small class="text-muted ms-2">Opcional: subir nuevo documento</small>
            </div>
        `;
    }
}

function addHiddenId(form, name, value) {
    let hiddenId = form.querySelector(`[name="${name}"]`);
    if (!hiddenId) {
        hiddenId = document.createElement('input');
        hiddenId.type = 'hidden';
        hiddenId.name = name;
        form.appendChild(hiddenId);
    }
    hiddenId.value = value;
}

// ============================================================================
// DELETE FUNCTIONS
// ============================================================================

function initializeDeleteButtons() {
    document.querySelectorAll('.delete-license').forEach(button => {
        button.addEventListener('click', function() {
            showDeleteConfirmation('license', this.dataset.id);
        });
    });

    document.querySelectorAll('.delete-internal-license').forEach(button => {
        button.addEventListener('click', function() {
            showDeleteConfirmation('internal-license', this.dataset.id);
        });
    });

    document.querySelectorAll('.delete-exam').forEach(button => {
        button.addEventListener('click', function() {
            showDeleteConfirmation('exam', this.dataset.id);
        });
    });

    document.querySelectorAll('.delete-certification').forEach(button => {
        button.addEventListener('click', function() {
            showDeleteConfirmation('certification', this.dataset.id);
        });
    });
}

function showDeleteConfirmation(type, id) {
    const confirmModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    const modalTitle = document.querySelector('#confirmDeleteModal .modal-title');
    const modalBody = document.querySelector('#confirmDeleteModal .modal-body p');
    
    const documentTypes = {
        'license': 'licencia',
        'internal-license': 'licencia interna',
        'exam': 'examen',
        'certification': 'certificación'
    };
    
    const documentType = documentTypes[type];
    modalTitle.textContent = `Confirmar Eliminación de ${documentType.charAt(0).toUpperCase() + documentType.slice(1)}`;
    modalBody.textContent = `¿Está seguro que desea eliminar esta ${documentType}? Esta acción no se puede deshacer.`;
    
    document.getElementById('confirmDeleteBtn').onclick = async function() {
        await deleteDocument(type, id, confirmModal);
    };
    
    confirmModal.show();
}

async function deleteDocument(type, id, confirmModal) {
    // Las URLs deben ser configuradas desde el template
    const urls = {
        'license': window.DELETE_LICENSE_URL?.replace('0', id),
        'internal-license': window.DELETE_INTERNAL_LICENSE_URL?.replace('0', id),
        'exam': window.DELETE_EXAM_URL?.replace('0', id),
        'certification': window.DELETE_CERTIFICATION_URL?.replace('0', id)
    };
    
    const url = urls[type];
    if (!url) {
        console.error('URL no definida para tipo:', type);
        return;
    }
    
    try {
        const response = await fetch(url, {
            method: type === 'certification' ? 'POST' : 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        confirmModal.hide();
        
        if (data.status === 'success') {
            showNotification('Éxito', data.message, 'success');
        } else {
            showNotification('Error', data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Error al procesar la solicitud', 'error');
    }
}

// ============================================================================
// PERSONAL DOCUMENTS
// ============================================================================

function initializePersonalDocumentHandlers() {
    // Upload carnet form
    const uploadCarnetForm = document.getElementById('uploadCarnetForm');
    if (uploadCarnetForm) {
        uploadCarnetForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await uploadCarnetDocument(this);
        });
    }

    // Upload document form
    const uploadDocumentForm = document.getElementById('uploadDocumentForm');
    if (uploadDocumentForm) {
        uploadDocumentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await uploadPersonalDocument(this);
        });
    }
}

function showUploadModal(fieldName, documentTitle) {
    document.getElementById('uploadDocumentTitle').textContent = `Subir ${documentTitle}`;
    document.getElementById('documentField').value = fieldName;
    document.getElementById('documentFile').value = '';
    
    new bootstrap.Modal(document.getElementById('uploadDocumentModal')).show();
}

function showUploadCarnetModal() {
    new bootstrap.Modal(document.getElementById('uploadCarnetModal')).show();
}

async function uploadCarnetDocument(form) {
    const formData = new FormData(form);
    const url = form.dataset.uploadUrl; // URL debe venir del template
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('uploadCarnetModal'));
        modal.hide();
        
        if (data.status === 'success') {
            showNotification('Éxito', data.message, 'success');
        } else {
            showNotification('Error', data.message || 'Error al subir el carnet', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Error al procesar la solicitud', 'error');
    }
}

async function uploadPersonalDocument(form) {
    const formData = new FormData(form);
    const url = form.dataset.uploadUrl; // URL debe venir del template
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('uploadDocumentModal'));
        modal.hide();
        
        if (data.status === 'success') {
            showNotification('Éxito', data.message, 'success');
        } else {
            showNotification('Error', data.message || 'Error al subir el documento', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Error al procesar la solicitud', 'error');
    }
}

async function deleteDocument(fieldName) {
    const documentNames = {
        'curriculum': 'Curriculum Vitae',
        'certificado_antecedentes': 'Certificado de Antecedentes',
        'hoja_vida_conductor': 'Hoja de Vida del Conductor',
        'foto_carnet': 'Foto Carnet',
        'certificado_afp': 'Certificado AFP',
        'certificado_salud': 'Certificado de Salud',
        'certificado_estudios': 'Certificado de Estudios',
        'certificado_residencia': 'Certificado de Residencia',
        'fotocopia_carnet': 'Fotocopia Carnet',
        'fotocopia_finiquito': 'Fotocopia Finiquito',
        'comprobante_banco': 'Comprobante Banco'
    };
    
    const confirmModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    const modalTitle = document.querySelector('#confirmDeleteModal .modal-title');
    const modalBody = document.querySelector('#confirmDeleteModal .modal-body p');
    
    modalTitle.textContent = `Eliminar ${documentNames[fieldName]}`;
    modalBody.textContent = `¿Está seguro que desea eliminar ${documentNames[fieldName]}? Esta acción no se puede deshacer.`;
    
    document.getElementById('confirmDeleteBtn').onclick = async function() {
        const url = window.DELETE_PERSONAL_DOCUMENT_URL; // URL debe venir del template
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ document_field: fieldName })
            });
            
            const data = await response.json();
            confirmModal.hide();
            
            if (data.status === 'success') {
                showNotification('Éxito', data.message, 'success');
            } else {
                showNotification('Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error', 'Error al procesar la solicitud', 'error');
        }
    };
    
    confirmModal.show();
}

// Exponer funciones globalmente para uso desde HTML onclick
window.showUploadModal = showUploadModal;
window.showUploadCarnetModal = showUploadCarnetModal;
window.deleteDocument = deleteDocument;

