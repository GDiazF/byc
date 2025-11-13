// ============================================================================
// GESTIÓN DE DOCUMENTACIÓN DE PERSONAL
// Version: v29.0 - CORREGIDO: Duplicación al editar (obtener ID antes de cerrar modal)
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

// Función para mostrar notificaciones estilo Django
function showNotification(title, message, type = 'success') {
    // Crear contenedor de alertas si no existe
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    // Determinar clase de Bootstrap según tipo
    const baseType = type.replace('-no-reload', '');
    const alertClass = baseType === 'success' ? 'alert-success' : 'alert-danger';
    const icon = baseType === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    // Crear el alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Agregar al contenedor
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de 3 segundos
    setTimeout(() => {
        // Iniciar animación de salida
        alertDiv.classList.remove('show');
        
        // Remover del DOM después de la animación
        setTimeout(() => {
            alertDiv.remove();
        }, 150); // Tiempo de la animación fade de Bootstrap
    }, 3000);
    
    // Recargar página solo si el tipo no incluye "-no-reload"
    if (type === 'success' && !type.includes('-no-reload')) {
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

// ============================================================================
// MODAL RESET HANDLERS
// ============================================================================

function initializeModalResetHandlers() {
    // Función helper para limpiar completamente un formulario
    const cleanFormCompletely = (form) => {
        if (!form) return;
        
        form.reset();
        
        // Limpiar mensajes de validación y estilos is-invalid
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
            el.setCustomValidity('');
        });
        
        // Ocultar mensajes de error
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.style.display = 'none';
            el.textContent = '';
        });
        
        // Remover información de documento existente
        const existingDocInfo = form.querySelector('.existing-document-info');
        if (existingDocInfo) existingDocInfo.remove();
    };
    
    // Limpiar formulario de licencias cuando se abre en modo "agregar"
    const licenseModal = document.getElementById('addLicenseModal');
    if (licenseModal) {
        licenseModal.addEventListener('show.bs.modal', function (event) {
            // Si no se abrió desde un botón de editar, limpiar el formulario
            const button = event.relatedTarget;
            if (button && !button.classList.contains('edit-license')) {
                const form = document.getElementById('licenseForm');
                if (form) {
                    cleanFormCompletely(form);
                    // Remover campo hidden de ID
                    const hiddenId = form.querySelector('[name="license_id"]');
                    if (hiddenId) hiddenId.remove();
                    // Restaurar título
                    document.querySelector('#addLicenseModal .modal-title').textContent = 'Agregar Licencia';
                }
            }
        });
    }
    
    // Limpiar formulario de licencias internas cuando se abre en modo "agregar"
    const internalLicenseModal = document.getElementById('addInternalLicenseModal');
    if (internalLicenseModal) {
        internalLicenseModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (button && !button.classList.contains('edit-internal-license')) {
                const form = document.getElementById('internalLicenseForm');
                if (form) {
                    cleanFormCompletely(form);
                    const hiddenId = form.querySelector('[name="internal_license_id"]');
                    if (hiddenId) hiddenId.remove();
                    document.querySelector('#addInternalLicenseModal .modal-title').textContent = 'Agregar Licencia Interna';
                }
            }
        });
    }
    
    // Limpiar formulario de exámenes cuando se abre en modo "agregar"
    const examModal = document.getElementById('addExamModal');
    if (examModal) {
        examModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (button && !button.classList.contains('edit-exam')) {
                const form = document.getElementById('examForm');
                if (form) {
                    cleanFormCompletely(form);
                    const hiddenId = form.querySelector('[name="exam_id"]');
                    if (hiddenId) hiddenId.remove();
                    document.querySelector('#addExamModal .modal-title').textContent = 'Agregar Examen';
                }
            }
        });
    }
    
    // Limpiar formulario de certificaciones cuando se abre en modo "agregar"
    const certificationModal = document.getElementById('addCertificationModal');
    if (certificationModal) {
        certificationModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (button && !button.classList.contains('edit-certification')) {
                const form = document.getElementById('certificationForm');
                if (form) {
                    cleanFormCompletely(form);
                    const hiddenId = form.querySelector('[name="cert_id"]');
                    if (hiddenId) hiddenId.remove();
                    document.querySelector('#addCertificationModal .modal-title').textContent = 'Agregar Certificación';
                }
            }
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
    
    // Initialize modal reset handlers
    initializeModalResetHandlers();
    
    // Initialize personal document handlers
    initializePersonalDocumentHandlers();
    
    // Initialize date validation
    initializeDateValidation();
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
            resetModalForm('internalLicenseForm', 'internal_license_id', 'Agregar Licencia Interna');
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
        
        // Limpiar TODOS los mensajes de validación y estilos is-invalid
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
            el.setCustomValidity(''); // Limpiar mensajes de validación personalizados
        });
        
        // Ocultar TODOS los mensajes de error
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.style.display = 'none';
            el.textContent = '';
        });
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
        console.log('[CERT] Inicializando formulario de certificaciones');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('[CERT] Submit interceptado');
            submitForm(this, 'certification');
        });
        form.dataset.initialized = 'true';
    }
}

// ============================================================================
// SUBMIT FORM
// ============================================================================

async function submitForm(form, type) {
    console.log('[SUBMIT] Tipo:', type, 'Form ID:', form.id);
    
    // Validar fechas ANTES de enviar
    const emisionField = form.querySelector('[name="fechaEmision"]');
    const vencimientoField = form.querySelector('[name="fechaVencimiento"]');
    
    console.log('[VALIDACION] Campos encontrados:', {
        emisionField: emisionField ? emisionField.value : 'NO ENCONTRADO',
        vencimientoField: vencimientoField ? vencimientoField.value : 'NO ENCONTRADO'
    });
    
    if (emisionField && vencimientoField && emisionField.value && vencimientoField.value) {
        const emisionDate = new Date(emisionField.value);
        const vencimientoDate = new Date(vencimientoField.value);
        
        console.log('[VALIDACION] Comparando fechas:', {
            emision: emisionDate,
            vencimiento: vencimientoDate,
            vencimientoMenor: vencimientoDate < emisionDate
        });
        
        if (vencimientoDate < emisionDate) {
            console.log('[VALIDACION] ERROR: Fecha de vencimiento < emisión');
            vencimientoField.classList.add('is-invalid');
            let errorDiv = vencimientoField.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                vencimientoField.parentNode.appendChild(errorDiv);
            }
            errorDiv.textContent = 'La fecha de vencimiento no puede ser anterior a la fecha de emisión';
            errorDiv.style.display = 'block';
            
            showNotification('Error de Validación', 'La fecha de vencimiento no puede ser anterior a la fecha de emisión', 'error');
            return; // No enviar el formulario
        } else {
            console.log('[VALIDACION] Fechas válidas');
            vencimientoField.classList.remove('is-invalid');
            const errorDiv = vencimientoField.nextElementSibling;
            if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                errorDiv.style.display = 'none';
            }
        }
    }
    
    const formData = new FormData(form);
    let url;
    
    // Determinar URL según tipo y si es edición o creación
    const licenseId = form.querySelector('[name="license_id"]');
    const internalLicenseId = form.querySelector('[name="internal_license_id"]');
    const certId = form.querySelector('[name="cert_id"]');
    const examId = form.querySelector('[name="exam_id"]');
    
    console.log('[SUBMIT] IDs encontrados:', {
        licenseId: licenseId ? licenseId.value : 'NO',
        internalLicenseId: internalLicenseId ? internalLicenseId.value : 'NO',
        certId: certId ? certId.value : 'NO',
        examId: examId ? examId.value : 'NO'
    });
    
    if (type === 'internal-license' && internalLicenseId && internalLicenseId.value) {
        url = `/users/personal/${internalLicenseId.value}/edit_internal_license/`;
        console.log('[SUBMIT] Modo: EDITAR licencia interna, ID:', internalLicenseId.value);
    } else if (type === 'license' && licenseId && licenseId.value) {
        url = `/users/personal/${licenseId.value}/edit_license/`;
        console.log('[SUBMIT] Modo: EDITAR licencia, ID:', licenseId.value);
    } else if (type === 'certification' && certId && certId.value) {
        url = `/users/personal/${certId.value}/edit_certification/`;
        console.log('[SUBMIT] Modo: EDITAR certificación, ID:', certId.value);
    } else if (type === 'exam' && examId && examId.value) {
        url = `/users/personal/${examId.value}/edit_exam/`;
        console.log('[SUBMIT] Modo: EDITAR examen, ID:', examId.value);
    } else {
        // URLs para crear nuevos registros - estas deben venir del template
        url = form.dataset.submitUrl;
        console.log('[SUBMIT] Modo: CREAR nuevo registro');
    }
    
    console.log('[SUBMIT] URL final:', url);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        console.log('Response status:', response.status); // DEBUG
        const data = await response.json();
        console.log('Response data:', data); // DEBUG
        
        // IMPORTANTE: Determinar si es edición ANTES de cerrar el modal
        const licenseId = form.querySelector('[name="license_id"]');
        const certId = form.querySelector('[name="cert_id"]');
        const examId = form.querySelector('[name="exam_id"]');
        const internalLicenseId = form.querySelector('[name="internal_license_id"]');
        
        let isEdit = false;
        let recordId = null;
        
        if (type === 'license' && licenseId && licenseId.value) {
            isEdit = true;
            recordId = licenseId.value;
        } else if (type === 'internal-license' && internalLicenseId && internalLicenseId.value) {
            isEdit = true;
            recordId = internalLicenseId.value;
        } else if (type === 'certification' && certId && certId.value) {
            isEdit = true;
            recordId = certId.value;
        } else if (type === 'exam' && examId && examId.value) {
            isEdit = true;
            recordId = examId.value;
        }
        
        console.log('[SUBMIT] Es edición (antes de cerrar modal)?', isEdit, 'ID:', recordId, 'Type:', type); // DEBUG
        
        // Cerrar el modal DESPUÉS de obtener el ID
        const modalId = {
            'license': 'addLicenseModal',
            'internal-license': 'addInternalLicenseModal',
            'exam': 'addExamModal',
            'certification': 'addCertificationModal'
        }[type];
        
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                console.log('Cerrando modal:', modalId); // DEBUG
                modal.hide();
            }
        }
        
        setTimeout(() => {
            if (data.status === 'success') {
                showNotification('Éxito', data.message, 'success-no-reload');
                
                console.log('[SUBMIT] Procesando respuesta - Es edición?', isEdit, 'ID:', recordId); // DEBUG
                console.log('[SUBMIT] Data recibida del servidor:', data.data); // DEBUG
                
                // Si es edición, actualizar la fila; si es nuevo, agregar la fila
                if (isEdit && recordId) {
                    console.log('[SUBMIT] Actualizando fila con ID:', recordId); // DEBUG
                    updateRowById(type, recordId, data.data);
                } else {
                    console.log('[SUBMIT] Agregando nueva fila...'); // DEBUG
                    addRowToTable(type, data.data);
                }
            } else {
                if (data.errors) {
                    handleFormErrors(form, data.errors);
                }
                showNotification('Error', data.message || 'Error al guardar', 'error');
            }
        }, 300);
    } catch (error) {
        console.error('Error completo:', error);
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
    // Usar event delegation para soportar elementos dinámicos
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.edit-license');
        if (target) {
            e.preventDefault();
            editLicense(target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.edit-internal-license');
        if (target) {
            e.preventDefault();
            editInternalLicense(target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.edit-certification');
        if (target) {
            e.preventDefault();
            editCertification(target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.edit-exam');
        if (target) {
            e.preventDefault();
            editExam(target.dataset.id);
        }
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
            
            // Seleccionar tipos (checkboxes)
            form.querySelectorAll('[name="tipos"]').forEach(checkbox => {
                checkbox.checked = data.license_data.tipos.includes(parseInt(checkbox.value));
            });
            
            // Manejar documento existente
            handleExistingDocument(form, data.license_data);
            
            // Agregar campo oculto de ID
            addHiddenId(form, 'license_id', licenseId);
            
            // Mostrar modal
            const modalElement = document.getElementById('addLicenseModal');
            const modalLicense = new bootstrap.Modal(modalElement);
            
            // Usar evento 'shown.bs.modal' para mejor timing
            const handleModalShown = () => {
                if (window.DatePickerChile) {
                    DatePickerChile.inicializar();
                    
                    setTimeout(() => {
                        const modal = document.getElementById('addLicenseModal');
                        const inputEmision = modal.querySelector('[name="fechaEmision"]');
                        const inputVencimiento = modal.querySelector('[name="fechaVencimiento"]');
                        
                        if (inputEmision && data.license_data.fecha_emision) {
                            const wrapperEmision = inputEmision.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperEmision && wrapperEmision._datePickerChile) {
                                wrapperEmision._datePickerChile.setValue(data.license_data.fecha_emision);
                            }
                        }
                        
                        if (inputVencimiento && data.license_data.fecha_vencimiento) {
                            const wrapperVencimiento = inputVencimiento.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperVencimiento && wrapperVencimiento._datePickerChile) {
                                wrapperVencimiento._datePickerChile.setValue(data.license_data.fecha_vencimiento);
                            }
                        }
                    }, 50);
                }
                
                modalElement.removeEventListener('shown.bs.modal', handleModalShown);
            };
            
            modalElement.addEventListener('shown.bs.modal', handleModalShown);
            modalLicense.show();
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
        console.log('[EDIT INTERNAL] Cargando licencia interna ID:', licenseId);
        const response = await fetch(`/users/personal/${licenseId}/edit_internal_license/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        console.log('[EDIT INTERNAL] Datos recibidos:', data);
        
        if (data.status === 'success') {
            const form = document.getElementById('internalLicenseForm');
            if (!form) return;
            
            document.querySelector('#addInternalLicenseModal .modal-title').textContent = 'Editar Licencia Interna';
            
            form.querySelector('[name="tipoLicenciaInterna_id"]').value = data.license_data.tipo_id;
            form.querySelector('[name="numero_licencia"]').value = data.license_data.numero || '';
            form.querySelector('[name="empresa_emisora"]').value = data.license_data.empresa || '';
            form.querySelector('[name="observacion"]').value = data.license_data.observacion || '';
            
            handleExistingDocument(form, data.license_data);
            addHiddenId(form, 'internal_license_id', licenseId);
            
            console.log('[EDIT INTERNAL] Verificando campo hidden después de agregar:');
            const hiddenCheck = form.querySelector('[name="internal_license_id"]');
            console.log('[EDIT INTERNAL] Hidden field:', hiddenCheck ? hiddenCheck.value : 'NO ENCONTRADO');
            
            const modalElement = document.getElementById('addInternalLicenseModal');
            const modalInternal = new bootstrap.Modal(modalElement);
            
            // Usar evento 'shown.bs.modal' en lugar de setTimeout para mejor timing
            const handleModalShown = () => {
                if (window.DatePickerChile) {
                    DatePickerChile.inicializar();
                    
                    // Pequeño delay para asegurar que los pickers estén listos
                    setTimeout(() => {
                        const modal = document.getElementById('addInternalLicenseModal');
                        const inputEmision = modal.querySelector('[name="fechaEmision"]');
                        const inputVencimiento = modal.querySelector('[name="fechaVencimiento"]');
                        
                        if (inputEmision && data.license_data.fecha_emision) {
                            const wrapperEmision = inputEmision.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperEmision && wrapperEmision._datePickerChile) {
                                wrapperEmision._datePickerChile.setValue(data.license_data.fecha_emision);
                            }
                        }
                        
                        if (inputVencimiento && data.license_data.fecha_vencimiento) {
                            const wrapperVencimiento = inputVencimiento.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperVencimiento && wrapperVencimiento._datePickerChile) {
                                wrapperVencimiento._datePickerChile.setValue(data.license_data.fecha_vencimiento);
                            }
                        }
                    }, 50);
                }
                
                // Remover el listener después de usarlo (solo se ejecuta una vez)
                modalElement.removeEventListener('shown.bs.modal', handleModalShown);
            };
            
            modalElement.addEventListener('shown.bs.modal', handleModalShown);
            modalInternal.show();
        } else {
            alert('Error al cargar los datos: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos: ' + error.message);
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
            
            handleExistingDocument(form, data.cert_data);
            addHiddenId(form, 'cert_id', certId);
            
            const modalElement = document.getElementById('addCertificationModal');
            const modalCert = new bootstrap.Modal(modalElement);
            
            // Usar evento 'shown.bs.modal' para mejor timing
            const handleModalShown = () => {
                if (window.DatePickerChile) {
                    DatePickerChile.inicializar();
                    
                    setTimeout(() => {
                        const modal = document.getElementById('addCertificationModal');
                        const inputEmision = modal.querySelector('[name="fechaEmision"]');
                        const inputVencimiento = modal.querySelector('[name="fechaVencimiento"]');
                        
                        if (inputEmision && data.cert_data.fecha_emision) {
                            const wrapperEmision = inputEmision.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperEmision && wrapperEmision._datePickerChile) {
                                wrapperEmision._datePickerChile.setValue(data.cert_data.fecha_emision);
                            }
                        }
                        
                        if (inputVencimiento && data.cert_data.fecha_vencimiento) {
                            const wrapperVencimiento = inputVencimiento.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperVencimiento && wrapperVencimiento._datePickerChile) {
                                wrapperVencimiento._datePickerChile.setValue(data.cert_data.fecha_vencimiento);
                            }
                        }
                    }, 50);
                }
                
                modalElement.removeEventListener('shown.bs.modal', handleModalShown);
            };
            
            modalElement.addEventListener('shown.bs.modal', handleModalShown);
            modalCert.show();
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
            
            handleExistingDocument(form, data.exam_data);
            addHiddenId(form, 'exam_id', examId);
            
            const modalElement = document.getElementById('addExamModal');
            const modalExam = new bootstrap.Modal(modalElement);
            
            // Usar evento 'shown.bs.modal' para mejor timing
            const handleModalShown = () => {
                if (window.DatePickerChile) {
                    DatePickerChile.inicializar();
                    
                    setTimeout(() => {
                        const modal = document.getElementById('addExamModal');
                        const inputEmision = modal.querySelector('[name="fechaEmision"]');
                        const inputVencimiento = modal.querySelector('[name="fechaVencimiento"]');
                        
                        if (inputEmision && data.exam_data.fecha_emision) {
                            const wrapperEmision = inputEmision.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperEmision && wrapperEmision._datePickerChile) {
                                wrapperEmision._datePickerChile.setValue(data.exam_data.fecha_emision);
                            }
                        }
                        
                        if (inputVencimiento && data.exam_data.fecha_vencimiento) {
                            const wrapperVencimiento = inputVencimiento.closest('[data-datepicker-chile-wrapper]');
                            if (wrapperVencimiento && wrapperVencimiento._datePickerChile) {
                                wrapperVencimiento._datePickerChile.setValue(data.exam_data.fecha_vencimiento);
                            }
                        }
                    }, 50);
                }
                
                modalElement.removeEventListener('shown.bs.modal', handleModalShown);
            };
            
            modalElement.addEventListener('shown.bs.modal', handleModalShown);
            modalExam.show();
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
        console.log('[HIDDEN] Creado nuevo campo hidden:', name, '=', value);
    } else {
        console.log('[HIDDEN] Campo hidden ya existía:', name, '- actualizando de', hiddenId.value, 'a', value);
    }
    hiddenId.value = value;
}

// ============================================================================
// DELETE FUNCTIONS
// ============================================================================

function initializeDeleteButtons() {
    // Usar event delegation para soportar elementos dinámicos
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.delete-license');
        if (target) {
            e.preventDefault();
            showDeleteConfirmation('license', target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.delete-internal-license');
        if (target) {
            e.preventDefault();
            showDeleteConfirmation('internal-license', target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.delete-exam');
        if (target) {
            e.preventDefault();
            showDeleteConfirmation('exam', target.dataset.id);
        }
    });

    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.delete-certification');
        if (target) {
            e.preventDefault();
            showDeleteConfirmation('certification', target.dataset.id);
        }
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
    console.log('Eliminando:', { type, id, url }); // DEBUG
    
    if (!url) {
        console.error('URL no definida para tipo:', type);
        showNotification('Error', 'URL no configurada', 'error');
        return;
    }
    
    try {
        const method = type === 'certification' ? 'POST' : 'DELETE';
        console.log('Enviando request:', { method, url }); // DEBUG
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status); // DEBUG
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data); // DEBUG
        
        confirmModal.hide();
        
        setTimeout(() => {
            if (data.status === 'success') {
                showNotification('Éxito', data.message, 'success-no-reload');
                // Eliminar la fila dinámicamente
                removeRowById(type, id);
            } else {
                showNotification('Error', data.message || 'Error al eliminar', 'error');
            }
        }, 300);
    } catch (error) {
        console.error('Error completo:', error);
        confirmModal.hide();
        setTimeout(() => {
            showNotification('Error', `Error al procesar la solicitud: ${error.message}`, 'error');
        }, 300);
    }
}

function removeRowById(type, id) {
    // Buscar y eliminar la fila correspondiente
    const tableIds = {
        'license': 'licenses-table',
        'internal-license': 'internal-licenses-table',
        'exam': 'exams-table',
        'certification': 'certifications-table'
    };
    
    const tableId = tableIds[type];
    const table = document.getElementById(tableId);
    
    if (table) {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const deleteBtn = row.querySelector(`.delete-${type}`);
            if (deleteBtn && deleteBtn.dataset.id === id.toString()) {
                // Animar la eliminación
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 300);
                
                // Si no quedan más filas, mostrar mensaje de "sin registros"
                setTimeout(() => {
                    const remainingRows = table.querySelectorAll('tbody tr');
                    if (remainingRows.length === 0) {
                        const colCount = table.querySelectorAll('thead th').length;
                        const emptyRow = document.createElement('tr');
                        emptyRow.innerHTML = `
                            <td colspan="${colCount}" class="text-center text-muted py-4">
                                <i class="bi bi-inbox me-2"></i>No hay registros
                            </td>
                        `;
                        table.querySelector('tbody').appendChild(emptyRow);
                    }
                }, 350);
            }
        });
    }
}

function addRowToTable(type, data) {
    console.log('[ADD ROW] Agregando nueva fila:', type, 'con ID:', data.id);
    
    const tableIds = {
        'license': 'licenses-table',
        'internal-license': 'internal-licenses-table',
        'exam': 'exams-table',
        'certification': 'certifications-table'
    };
    
    const tableId = tableIds[type];
    const table = document.getElementById(tableId);
    
    if (!table) {
        console.error('[ADD ROW] Tabla no encontrada:', tableId);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    
    // Si existe fila de "No hay registros", eliminarla
    const noDataRow = tbody.querySelector('tr td[colspan]');
    if (noDataRow) {
        noDataRow.closest('tr').remove();
    }
    
    // Crear nueva fila según el tipo
    const newRow = createRowElement(type, data);
    tbody.insertBefore(newRow, tbody.firstChild); // Insertar al inicio
    console.log('[ADD ROW] Fila agregada exitosamente');
}

function updateRowById(type, id, data) {
    const tableIds = {
        'license': 'licenses-table',
        'internal-license': 'internal-licenses-table',
        'exam': 'exams-table',
        'certification': 'certifications-table'
    };
    
    const tableId = tableIds[type];
    const table = document.getElementById(tableId);
    
    if (!table) {
        console.error('Tabla no encontrada:', tableId);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    
    console.log(`[UPDATE] Buscando fila con tipo: ${type}, id: ${id}`);
    console.log(`[UPDATE] Data.id del servidor:`, data.id);
    
    let found = false;
    let rowIndex = 0;
    rows.forEach(row => {
        const deleteBtn = row.querySelector(`.delete-${type}`);
        const deleteBtnId = deleteBtn ? deleteBtn.dataset.id : 'NO BUTTON';
        console.log(`[UPDATE] Fila ${rowIndex}: delete button id="${deleteBtnId}", comparando con id="${id}" (string: "${id.toString()}")`);
        console.log(`[UPDATE] Fila ${rowIndex}: ¿Son iguales? ${deleteBtnId === id.toString()}, ¿Son iguales con ==? ${deleteBtnId == id}`);
        
        if (deleteBtn && deleteBtn.dataset.id === id.toString()) {
            console.log(`[UPDATE] ✓ FILA ENCONTRADA en índice ${rowIndex} - Actualizando...`);
            // Crear nueva fila con datos actualizados
            const newRow = createRowElement(type, data);
            row.replaceWith(newRow);
            found = true;
        }
        rowIndex++;
    });
    
    if (!found) {
        console.error(`[UPDATE] ✗ NO SE ENCONTRÓ la fila con id: ${id}. Esto causará duplicación.`);
        console.error(`[UPDATE] Tipo: ${type}, ID buscado: "${id}" (tipo: ${typeof id}), Total de filas: ${rows.length}`);
        console.error(`[UPDATE] IDs de botones encontrados:`, Array.from(rows).map(r => {
            const btn = r.querySelector(`.delete-${type}`);
            return btn ? btn.dataset.id : 'NO BUTTON';
        }));
    }
}

// Función helper para calcular si un documento está vigente o vencido
function calcularEstadoVigencia(fechaVencimiento) {
    if (!fechaVencimiento) return '<span class="badge bg-secondary">Sin fecha</span>';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let vencimiento;
    
    // Soportar múltiples formatos de fecha: DD/MM/YYYY o YYYY-MM-DD
    if (fechaVencimiento.includes('/')) {
        // Formato DD/MM/YYYY
        const [day, month, year] = fechaVencimiento.split('/').map(Number);
        vencimiento = new Date(year, month - 1, day);
    } else {
        // Formato YYYY-MM-DD
        const [year, month, day] = fechaVencimiento.split('-').map(Number);
        vencimiento = new Date(year, month - 1, day);
    }
    
    vencimiento.setHours(0, 0, 0, 0);
    
    // Vigente si la fecha es mayor O IGUAL a hoy (incluyendo el mismo día)
    if (vencimiento >= today) {
        return '<span class="badge bg-success">Vigente</span>';
    } else {
        return '<span class="badge bg-danger">Vencida</span>';
    }
}

function createRowElement(type, data) {
    console.log('[CREATE ROW] Creando fila para tipo:', type, 'con data.id:', data.id);
    
    const row = document.createElement('tr');
    
    let rowHTML = '';
    
    switch(type) {
        case 'license':
            // Dividir las clases en badges
            const clasesBadges = data.clase ? data.clase.split(', ').map(clase => 
                `<span class="badge bg-primary me-1">${clase}</span>`
            ).join('') : '';
            
            rowHTML = `
                <td>
                    <i class="bi bi-card-text me-2"></i>
                    ${clasesBadges}
                </td>
                <td class="text-center">${data.fecha_emision ? window.DatePickerChile.convertirISOAChileno(data.fecha_emision) : ''}</td>
                <td class="text-center">${data.fecha_vencimiento ? window.DatePickerChile.convertirISOAChileno(data.fecha_vencimiento) : ''}</td>
                <td class="text-center">
                    ${calcularEstadoVigencia(data.fecha_vencimiento)}
                </td>
                <td>
                    ${data.documento ? `<a href="${data.documento_url}" target="_blank" class="btn btn-sm btn-primary me-1"><i class="bi bi-eye"></i></a>` : ''}
                    <button class="btn btn-sm btn-secondary me-1 edit-license" data-id="${data.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-license" data-id="${data.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            break;
            
        case 'internal-license':
            rowHTML = `
                <td>
                    <i class="bi bi-award me-2"></i>${data.tipo || ''}
                </td>
                <td class="text-center">${data.numero || '-'}</td>
                <td>${data.empresa || '-'}</td>
                <td class="text-center">${data.fecha_emision ? window.DatePickerChile.convertirISOAChileno(data.fecha_emision) : ''}</td>
                <td class="text-center">${data.fecha_vencimiento ? window.DatePickerChile.convertirISOAChileno(data.fecha_vencimiento) : ''}</td>
                <td class="text-center">
                    ${calcularEstadoVigencia(data.fecha_vencimiento)}
                </td>
                <td>
                    ${data.documento ? `<a href="${data.documento_url}" target="_blank" class="btn btn-sm btn-primary me-1"><i class="bi bi-eye"></i></a>` : ''}
                    <button class="btn btn-sm btn-secondary me-1 edit-internal-license" data-id="${data.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-internal-license" data-id="${data.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            break;
            
        case 'exam':
            // Determinar el color del badge del resultado
            let resultadoBadgeClass = 'bg-primary';
            const resultadoLower = (data.resultado || '').toLowerCase();
            if (resultadoLower.includes('aprobado')) {
                resultadoBadgeClass = 'bg-success';
            } else if (resultadoLower.includes('reprobado')) {
                resultadoBadgeClass = 'bg-danger';
            }
            
            rowHTML = `
                <td>
                    <i class="bi bi-clipboard2-pulse me-2"></i>${data.tipo || ''}
                </td>
                <td class="text-center">
                    ${data.resultado && data.resultado !== '-' ? `<span class="badge ${resultadoBadgeClass}">${data.resultado}</span>` : '<span class="text-muted">-</span>'}
                </td>
                <td>${data.proveedor || ''}</td>
                <td class="text-center">${data.fecha_emision ? window.DatePickerChile.convertirISOAChileno(data.fecha_emision) : ''}</td>
                <td class="text-center">${data.fecha_vencimiento ? window.DatePickerChile.convertirISOAChileno(data.fecha_vencimiento) : ''}</td>
                <td class="text-center">
                    ${calcularEstadoVigencia(data.fecha_vencimiento)}
                </td>
                <td>
                    ${data.documento ? `<a href="${data.documento_url}" target="_blank" class="btn btn-sm btn-primary me-1"><i class="bi bi-eye"></i></a>` : ''}
                    <button class="btn btn-sm btn-secondary me-1 edit-exam" data-id="${data.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-exam" data-id="${data.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            break;
            
        case 'certification':
            rowHTML = `
                <td>
                    <i class="bi bi-patch-check me-2"></i>${data.tipo || ''}
                </td>
                <td>${data.proveedor || ''}</td>
                <td class="text-center">${data.fecha_emision ? window.DatePickerChile.convertirISOAChileno(data.fecha_emision) : ''}</td>
                <td class="text-center">${data.fecha_vencimiento ? window.DatePickerChile.convertirISOAChileno(data.fecha_vencimiento) : ''}</td>
                <td class="text-center">
                    ${calcularEstadoVigencia(data.fecha_vencimiento)}
                </td>
                <td>
                    ${data.documento ? `<a href="${data.documento_url}" target="_blank" class="btn btn-sm btn-primary me-1"><i class="bi bi-eye"></i></a>` : ''}
                    <button class="btn btn-sm btn-secondary me-1 edit-certification" data-id="${data.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-certification" data-id="${data.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            break;
    }
    
    row.innerHTML = rowHTML;
    return row;
}

// ============================================================================
// PERSONAL DOCUMENTS
// ============================================================================

function initializePersonalDocumentHandlers() {
    // Limpiar event listeners duplicados usando delegación de eventos
    document.body.removeEventListener('submit', handleDocumentFormSubmit);
    document.body.addEventListener('submit', handleDocumentFormSubmit);
}

function handleDocumentFormSubmit(e) {
    // Manejar submit del formulario de carnet
    if (e.target.id === 'uploadCarnetForm') {
        e.preventDefault();
        uploadCarnetDocument(e.target);
        return;
    }
    
    // Manejar submit del formulario de documento personal
    if (e.target.id === 'uploadDocumentForm') {
        e.preventDefault();
        uploadPersonalDocument(e.target);
        return;
    }
}

function showUploadModal(fieldName, documentTitle) {
    document.getElementById('uploadDocumentTitle').textContent = `Subir ${documentTitle}`;
    document.getElementById('documentField').value = fieldName;
    document.getElementById('documentFile').value = '';
    
    new bootstrap.Modal(document.getElementById('uploadDocumentModal')).show();
}

function showUploadCarnetModal() {
    // Limpiar el campo de fecha cuando se abre el modal
    document.getElementById('fechaVencimientoCarnet').value = '';
    // Limpiar el campo de archivo
    document.getElementById('carnetFile').value = '';
    
    new bootstrap.Modal(document.getElementById('uploadCarnetModal')).show();
}

async function uploadCarnetDocument(form) {
    const formData = new FormData(form);
    const url = form.dataset.uploadUrl;
    const documentField = 'fotocopia_carnet'; // El modal de carnet siempre sube este documento específico
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        // Cerrar el modal primero
        const modalElement = document.getElementById('uploadCarnetModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        
        // Esperar a que el modal se cierre completamente
        setTimeout(() => {
            if (data.status === 'success') {
                showNotification('Éxito', data.message, 'success-no-reload');
                // Actualizar la tabla dinámicamente con la URL del servidor
                updateDocumentRow(documentField, data.document_url);
            } else {
                showNotification('Error', data.message || 'Error al subir el carnet', 'error');
            }
        }, 300);
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Error al procesar la solicitud', 'error');
    }
}

async function uploadPersonalDocument(form) {
    const formData = new FormData(form);
    const url = form.dataset.uploadUrl;
    const documentField = document.getElementById('documentField').value;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        // Cerrar el modal primero
        const modalElement = document.getElementById('uploadDocumentModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        
        // Esperar a que el modal se cierre completamente
        setTimeout(() => {
            if (data.status === 'success') {
                showNotification('Éxito', data.message, 'success-no-reload');
                // Actualizar la tabla dinámicamente con la URL del servidor
                updateDocumentRow(documentField, data.document_url);
            } else {
                showNotification('Error', data.message || 'Error al subir el documento', 'error');
            }
        }, 300);
        
    } catch (error) {
        console.error('Error en upload:', error);
        showNotification('Error', 'Error al procesar la solicitud', 'error');
    }
}

function updateDocumentRow(documentField, documentUrl) {
    // Buscar la fila que contiene este documento
    const rows = document.querySelectorAll('#personal-docs tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length < 3) return;
        
        // Verificar si esta fila corresponde al documento
        const actionCell = cells[2];
        const buttons = actionCell.querySelectorAll('button');
        
        // Variable para verificar si esta es la fila correcta
        let isCorrectRow = false;
        
        buttons.forEach(button => {
            const onclick = button.getAttribute('onclick');
            // Para fotocopia_carnet buscar showUploadCarnetModal, para otros documentos buscar el nombre del campo
            if (documentField === 'fotocopia_carnet' && onclick && onclick.includes('showUploadCarnetModal')) {
                isCorrectRow = true;
            } else if (onclick && onclick.includes(`'${documentField}'`)) {
                isCorrectRow = true;
            }
        });
        
        if (isCorrectRow) {
            // Actualizar el badge de estado
            const statusCell = cells[1];
            statusCell.innerHTML = '<span class="badge bg-success">✓ Cargado</span>';
            
            // Determinar qué función de modal usar según el tipo de documento
            let uploadFunction = `showUploadModal('${documentField}', '${getDocumentTitle(documentField)}')`;
            if (documentField === 'fotocopia_carnet') {
                uploadFunction = 'showUploadCarnetModal()';
            }
            
            // Actualizar los botones de acción con la URL real del servidor
            actionCell.innerHTML = `
                <a href="${documentUrl}" target="_blank" class="btn btn-sm btn-primary me-1">
                    <i class="bi bi-eye"></i> Ver
                </a>
                <button class="btn btn-sm btn-warning me-1" onclick="${uploadFunction}">
                    <i class="bi bi-arrow-repeat"></i> Reemplazar
                </button>
                <button class="btn btn-sm btn-danger" onclick="deletePersonalDocument('${documentField}')">
                    <i class="bi bi-trash"></i>
                </button>
            `;
        }
    });
}

function getDocumentTitle(fieldName) {
    const titles = {
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
    return titles[fieldName] || 'Documento';
}

async function deletePersonalDocument(fieldName) {
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
        const url = window.DELETE_PERSONAL_DOCUMENT_URL;
        
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
            
            // Esperar a que el modal se cierre completamente
            setTimeout(() => {
                if (data.status === 'success') {
                    showNotification('Éxito', data.message, 'success-no-reload');
                    // Actualizar la tabla dinámicamente eliminando el documento
                    removeDocumentFromRow(fieldName);
                } else {
                    showNotification('Error', data.message, 'error');
                }
            }, 300);
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error', 'Error al procesar la solicitud', 'error');
        }
    };
    
    confirmModal.show();
}

function removeDocumentFromRow(documentField) {
    // Buscar la fila que contiene este documento
    const rows = document.querySelectorAll('#personal-docs tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length < 3) return;
        
        // Verificar si esta fila corresponde al documento
        const actionCell = cells[2];
        const buttons = actionCell.querySelectorAll('button, a');
        
        // Variable para verificar si esta es la fila correcta
        let isCorrectRow = false;
        
        buttons.forEach(button => {
            const onclick = button.getAttribute('onclick');
            // Para fotocopia_carnet buscar showUploadCarnetModal, para otros documentos buscar el nombre del campo
            if (documentField === 'fotocopia_carnet' && onclick && onclick.includes('showUploadCarnetModal')) {
                isCorrectRow = true;
            } else if (onclick && onclick.includes(`'${documentField}'`)) {
                isCorrectRow = true;
            }
        });
        
        if (isCorrectRow) {
            // Actualizar el badge de estado
            const statusCell = cells[1];
            statusCell.innerHTML = '<span class="badge bg-secondary">Sin archivo</span>';
            
            // Determinar qué función de modal usar según el tipo de documento
            let uploadFunction = `showUploadModal('${documentField}', '${getDocumentTitle(documentField)}')`;
            if (documentField === 'fotocopia_carnet') {
                uploadFunction = 'showUploadCarnetModal()';
            }
            
            // Actualizar el botón de acción a solo "Subir"
            actionCell.innerHTML = `
                <button class="btn btn-sm btn-success" onclick="${uploadFunction}">
                    <i class="bi bi-upload"></i> Subir
                </button>
            `;
        }
    });
}

// ============================================================================
// DATE VALIDATION
// ============================================================================

function initializeDateValidation() {
    // Validar fechas en formularios
    validateDatesInForm('licenseForm', 'id_fechaEmision', 'id_fechaVencimiento');
    validateDatesInForm('internalLicenseForm', 'id_fechaEmision', 'id_fechaVencimiento');
    validateDatesInForm('examForm', 'id_fechaEmision', 'id_fechaVencimiento');
    validateDatesInForm('certificationForm', 'id_fechaEmision', 'id_fechaVencimiento');
}

function validateDatesInForm(formId, emisionFieldId, vencimientoFieldId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const emisionField = form.querySelector(`#${emisionFieldId}`);
    const vencimientoField = form.querySelector(`#${vencimientoFieldId}`);
    
    if (!emisionField || !vencimientoField) return;
    
    const validateDates = () => {
        const emisionValue = emisionField.value;
        const vencimientoValue = vencimientoField.value;
        
        if (emisionValue && vencimientoValue) {
            const emisionDate = new Date(emisionValue);
            const vencimientoDate = new Date(vencimientoValue);
            
            if (vencimientoDate < emisionDate) {
                vencimientoField.setCustomValidity('La fecha de vencimiento no puede ser anterior a la fecha de emisión');
                vencimientoField.classList.add('is-invalid');
                
                // Mostrar mensaje de error
                let errorDiv = vencimientoField.nextElementSibling;
                if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    vencimientoField.parentNode.appendChild(errorDiv);
                }
                errorDiv.textContent = 'La fecha de vencimiento no puede ser anterior a la fecha de emisión';
                errorDiv.style.display = 'block';
                return false; // Retornar false si hay error
            } else {
                vencimientoField.setCustomValidity('');
                vencimientoField.classList.remove('is-invalid');
                
                // Ocultar mensaje de error
                const errorDiv = vencimientoField.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.style.display = 'none';
                }
                return true; // Retornar true si no hay error
            }
        }
        return true; // Si no hay ambas fechas, dejar pasar
    };
    
    // Agregar event listeners para validación en tiempo real
    emisionField.addEventListener('change', validateDates);
    vencimientoField.addEventListener('change', validateDates);
    vencimientoField.addEventListener('input', validateDates);
    emisionField.addEventListener('input', validateDates);
}

// Exponer funciones globalmente para uso desde HTML onclick
window.showUploadModal = showUploadModal;
window.showUploadCarnetModal = showUploadCarnetModal;
window.deletePersonalDocument = deletePersonalDocument;

