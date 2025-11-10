// Variables globales
let todosLosModelos = [];

// Cargar al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarModelos();
    
    // Event listener para el formulario
    document.getElementById('equipoForm').addEventListener('submit', guardarEquipo);
    
    // Si estamos en modo edición, cargar datos
    if (window.equipoEdicion) {
        cargarDatosEdicion();
    }
});

// Cargar todos los modelos con tipo y marca
function cargarModelos() {
    fetch('/maquinarias/api/modelos-equipo/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                todosLosModelos = data.modelos;
                
                // Si es edición, cargar filtros con los datos del equipo
                if (window.equipoEdicion) {
                    setTimeout(() => {
                        document.getElementById('tipoEquipo_id').value = window.equipoEdicion.tipo_id;
                        filtrarMarcasPorTipo();
                        
                        setTimeout(() => {
                            document.getElementById('marcaEquipo_id').value = window.equipoEdicion.marca_id;
                            filtrarModelosPorTipoYMarca();
                            
                            setTimeout(() => {
                                document.getElementById('modeloEquipo_id').value = window.equipoEdicion.modelo_id;
                                actualizarNombrePreview();
                            }, 100);
                        }, 100);
                    }, 100);
                }
            }
        })
        .catch(error => console.error('Error al cargar modelos:', error));
}

// Cargar datos para edición
function cargarDatosEdicion() {
    actualizarNombrePreview();
}

// Filtrar marcas según el tipo seleccionado
function filtrarMarcasPorTipo() {
    const tipoSelect = document.getElementById('tipoEquipo_id');
    const marcaSelect = document.getElementById('marcaEquipo_id');
    const modeloSelect = document.getElementById('modeloEquipo_id');
    const tipoId = parseInt(tipoSelect.value);
    
    console.log('Filtrando marcas para tipo:', tipoId);
    console.log('Total modelos disponibles:', todosLosModelos.length);
    
    // Resetear marca y modelo
    marcaSelect.innerHTML = '<option value="">Seleccione marca...</option>';
    modeloSelect.innerHTML = '<option value="">Primero seleccione marca...</option>';
    modeloSelect.disabled = true;
    document.getElementById('nombrePreview').value = '-';
    
    if (!tipoId) {
        marcaSelect.disabled = true;
        return;
    }
    
    // Obtener marcas únicas para este tipo
    const marcasUnicas = new Set();
    const modelosFiltrados = todosLosModelos.filter(m => m.tipo_id === tipoId);
    console.log('Modelos filtrados por tipo:', modelosFiltrados.length);
    
    modelosFiltrados.forEach(m => {
        marcasUnicas.add(JSON.stringify({id: m.marca_id, nombre: m.marca_nombre}));
    });
    
    const marcasArray = Array.from(marcasUnicas).map(m => JSON.parse(m));
    marcasArray.sort((a, b) => a.nombre.localeCompare(b.nombre));
    
    console.log('Marcas únicas encontradas:', marcasArray.length);
    
    if (marcasArray.length > 0) {
        marcasArray.forEach(marca => {
            const option = document.createElement('option');
            option.value = marca.id;
            option.textContent = marca.nombre;
            marcaSelect.appendChild(option);
        });
        marcaSelect.disabled = false;
        console.log('Marcas cargadas, select habilitado');
    } else {
        marcaSelect.innerHTML = '<option value="">No hay marcas disponibles para este tipo</option>';
        marcaSelect.disabled = true;
        console.log('No hay marcas disponibles');
    }
}

// Filtrar modelos según tipo y marca seleccionados
function filtrarModelosPorTipoYMarca() {
    const tipoId = parseInt(document.getElementById('tipoEquipo_id').value);
    const marcaId = parseInt(document.getElementById('marcaEquipo_id').value);
    const modeloSelect = document.getElementById('modeloEquipo_id');
    
    modeloSelect.innerHTML = '<option value="">Seleccione modelo...</option>';
    document.getElementById('nombrePreview').value = '-';
    
    if (!tipoId || !marcaId) {
        modeloSelect.disabled = true;
        return;
    }
    
    // Filtrar modelos por tipo y marca
    const modelosFiltrados = todosLosModelos.filter(m => 
        m.tipo_id === tipoId && m.marca_id === marcaId
    );
    
    modelosFiltrados.sort((a, b) => a.nombre.localeCompare(b.nombre));
    
    if (modelosFiltrados.length > 0) {
        modelosFiltrados.forEach(modelo => {
            const option = document.createElement('option');
            option.value = modelo.id;
            option.textContent = modelo.nombre;
            option.setAttribute('data-sigla', modelo.tipo_sigla);
            modeloSelect.appendChild(option);
        });
        modeloSelect.disabled = false;
    } else {
        modeloSelect.innerHTML = '<option value="">No hay modelos disponibles para esta combinación</option>';
        modeloSelect.disabled = true;
    }
}

// Actualizar preview del nombre
function actualizarNombrePreview() {
    const modeloSelect = document.getElementById('modeloEquipo_id');
    const codigo = document.getElementById('codigoInterno').value;
    const patente = document.getElementById('patente').value;
    
    if (!modeloSelect.value || !codigo) {
        document.getElementById('nombrePreview').value = '-';
        return;
    }
    
    // Buscar el modelo en la lista global
    const modelo = todosLosModelos.find(m => m.id === parseInt(modeloSelect.value));
    if (!modelo) {
        document.getElementById('nombrePreview').value = '-';
        return;
    }
    
    const sigla = modelo.tipo_sigla;
    let nombrePreview = sigla + codigo;
    
    if (patente && patente.trim()) {
        nombrePreview += ' - ' + patente.trim().toUpperCase();
    }
    
    document.getElementById('nombrePreview').value = nombrePreview;
}

// Guardar equipo (crear o editar)
function guardarEquipo(event) {
    event.preventDefault();
    
    const equipoId = document.getElementById('equipo_id').value;
    const empresaSelect = document.getElementById('empresa_id');
    const empresaId = empresaSelect ? empresaSelect.value : '';
    const modeloId = document.getElementById('modeloEquipo_id').value;
    const codigo = document.getElementById('codigoInterno').value;
    const horometro = document.getElementById('horometro').value;
    const odometro = document.getElementById('odometro').value;
    const horometroSE = document.getElementById('horometroSuperEstructural').value;
    
    console.log('=== DEBUG FORMULARIO ===');
    console.log('Select empresa existe?', empresaSelect !== null);
    if (empresaSelect) {
        console.log('Opciones en select:', empresaSelect.options.length);
        console.log('Opción seleccionada:', empresaSelect.selectedIndex);
        console.log('Valor de la opción:', empresaSelect.options[empresaSelect.selectedIndex]?.value);
    }
    console.log('empresaId capturado:', `"${empresaId}"`, 'tipo:', typeof empresaId);
    console.log('modeloId:', modeloId, 'tipo:', typeof modeloId);
    console.log('codigo:', codigo);
    
    // Validación básica en frontend
    if (!empresaId || empresaId === '' || empresaId === 'Seleccione empresa...') {
        mostrarError('Debe seleccionar una empresa');
        console.error('Validación falló: empresa_id es', empresaId);
        return;
    }
    if (!modeloId) {
        mostrarError('Debe seleccionar un modelo de equipo');
        return;
    }
    if (!codigo) {
        mostrarError('Debe ingresar un código interno');
        return;
    }
    
    const data = {
        equipo_id: equipoId || null,
        empresa_id: parseInt(empresaId),
        modeloEquipo_id: parseInt(modeloId),
        codigoInterno: codigo,
        patente: document.getElementById('patente').value.trim(),
        horometro: parseInt(horometro) || 0,
        odometro: parseInt(odometro) || 0,
        horometroSuperEstructural: horometroSE ? parseInt(horometroSE) : 0
    };
    
    console.log('Datos a enviar:', data);
    
    // Deshabilitar botón submit
    const submitBtn = event.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando...';
    
    fetch('/maquinarias/api/equipos/guardar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarExito(data.message);
            // Redirigir a la lista después de 1 segundo
            setTimeout(() => {
                window.location.href = '/maquinarias/equipos/';
            }, 1000);
        } else {
            mostrarError(data.error);
            // Re-habilitar botón
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>' + (equipoId ? 'Actualizar' : 'Crear') + ' Equipo';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error de conexión al guardar el equipo');
        // Re-habilitar botón
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>' + (equipoId ? 'Actualizar' : 'Crear') + ' Equipo';
    });
}

// Mostrar notificación estilo toast (igual que en personal)
function showNotification(message, type = 'success') {
    // Crear contenedor de alertas si no existe
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    // Determinar clase de Bootstrap según tipo
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle-fill' : 'exclamation-triangle-fill';
    
    // Crear el alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        <strong>${message}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Agregar al contenedor
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de 4 segundos
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 4000);
}

// Mostrar mensaje de éxito
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');
}

