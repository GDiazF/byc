// Variables globales
let itemSeccionIndex = 0;
let equiposDisponibles = [];
let personalDisponible = [];
let personalSeleccionados = [];
let modeloEquipoSeleccionado = null;
let cargosDisponibles = [];
let departamentosDisponibles = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('formOrdenTrabajo');
    
    if (form) {
        form.addEventListener('submit', guardarOrdenTrabajo);
    }
    
    // Cargar departamentos y personal al iniciar (solo si existen los elementos)
    cargarDepartamentos();
    cargarPersonal();
    
    // Event listeners para filtros en cascada de equipos (solo si existen)
    const empresaSelect = document.getElementById('empresa_id');
    if (empresaSelect) {
        empresaSelect.addEventListener('change', function() {
            filtrarEquipos();
        });
    }
    
    const tipoEquipoSelect = document.getElementById('tipo_equipo_id');
    if (tipoEquipoSelect) {
        tipoEquipoSelect.addEventListener('change', filtrarMarcasPorTipo);
    }
    
    const marcaEquipoSelect = document.getElementById('marca_equipo_id');
    if (marcaEquipoSelect) {
        marcaEquipoSelect.addEventListener('change', filtrarModelosPorTipoYMarca);
    }
    
    const modeloEquipoSelect = document.getElementById('modelo_equipo_id');
    if (modeloEquipoSelect) {
        modeloEquipoSelect.addEventListener('change', filtrarEquipos);
    }
    
    // Event listeners para filtros de personal (solo si existen)
    const personalSearch = document.getElementById('personalSearch');
    if (personalSearch) {
        personalSearch.addEventListener('input', debounce(cargarPersonal, 500));
    }
    
    const personalEmpresaFilter = document.getElementById('personalEmpresaFilter');
    if (personalEmpresaFilter) {
        personalEmpresaFilter.addEventListener('change', cargarPersonal);
    }
    
    const personalCargoFilter = document.getElementById('personalCargoFilter');
    if (personalCargoFilter) {
        personalCargoFilter.addEventListener('change', cargarPersonal);
    }
    
    const personalDeptoFilter = document.getElementById('personalDeptoFilter');
    if (personalDeptoFilter) {
        personalDeptoFilter.addEventListener('change', function() {
            cargarCargosPorDepto(this.value);
            cargarPersonal();
        });
    }
    
    // Si es edición, cargar datos existentes
    if (window.esEdicion && window.otData) {
        setTimeout(() => {
            cargarDatosEdicion();
        }, 500);
    }
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

// ============================================================================
// FILTROS EN CASCADA DE EQUIPOS (Tipo -> Marca -> Modelo -> Equipo)
// ============================================================================

// Filtrar marcas según tipo seleccionado
function filtrarMarcasPorTipo() {
    const tipoId = parseInt(document.getElementById('tipo_equipo_id').value);
    const marcaSelect = document.getElementById('marca_equipo_id');
    const modeloSelect = document.getElementById('modelo_equipo_id');
    const equipoSelect = document.getElementById('equipo_id');
    
    // Resetear marca, modelo y equipo
    marcaSelect.innerHTML = '<option value="">Todas</option>';
    marcaSelect.disabled = !tipoId;
    
    modeloSelect.innerHTML = '<option value="">Primero seleccione marca...</option>';
    modeloSelect.disabled = true;
    
    equipoSelect.innerHTML = '<option value="">Primero seleccione modelo...</option>';
    equipoSelect.disabled = true;
    
    if (!tipoId) {
        filtrarEquipos();
        return;
    }
    
    // Obtener marcas únicas para este tipo desde los modelos
    const marcasUnicas = new Set();
    window.todosModelos.forEach(modelo => {
        if (modelo.tipoEquipo_id === tipoId) {
            marcasUnicas.add(modelo.marcaEquipo_id);
        }
    });
    
    // Agregar marcas al select
    window.todasMarcas.forEach(marca => {
        if (marcasUnicas.has(marca.marcaEquipo_id)) {
            const option = document.createElement('option');
            option.value = marca.marcaEquipo_id;
            option.textContent = marca.marcaEquipo;
            marcaSelect.appendChild(option);
        }
    });
    
    filtrarEquipos();
}

// Filtrar modelos según tipo y marca seleccionados
function filtrarModelosPorTipoYMarca() {
    const tipoId = parseInt(document.getElementById('tipo_equipo_id').value);
    const marcaId = parseInt(document.getElementById('marca_equipo_id').value);
    const modeloSelect = document.getElementById('modelo_equipo_id');
    const equipoSelect = document.getElementById('equipo_id');
    
    // Resetear modelo y equipo
    modeloSelect.innerHTML = '<option value="">Todos</option>';
    modeloSelect.disabled = !tipoId || !marcaId;
    
    equipoSelect.innerHTML = '<option value="">Primero seleccione modelo...</option>';
    equipoSelect.disabled = true;
    
    if (!tipoId || !marcaId) {
        filtrarEquipos();
        return;
    }
    
    // Filtrar modelos por tipo y marca
    const modelosFiltrados = window.todosModelos.filter(m => 
        m.tipoEquipo_id === tipoId && m.marcaEquipo_id === marcaId
    );
    
    modelosFiltrados.forEach(modelo => {
        const option = document.createElement('option');
        option.value = modelo.modeloEquipo_id;
        option.textContent = modelo.modeloEquipo;
        modeloSelect.appendChild(option);
    });
    
    filtrarEquipos();
}

// Filtrar equipos según empresa, tipo, marca y modelo
function filtrarEquipos() {
    const empresaId = document.getElementById('empresa_id').value;
    const tipoId = document.getElementById('tipo_equipo_id').value;
    const marcaId = document.getElementById('marca_equipo_id').value;
    const modeloId = document.getElementById('modelo_equipo_id').value;
    const equipoSelect = document.getElementById('equipo_id');
    
    const params = new URLSearchParams();
    if (empresaId) params.append('empresa_id', empresaId);
    if (tipoId) params.append('tipo_equipo_id', tipoId);
    if (marcaId) params.append('marca_equipo_id', marcaId);
    if (modeloId) params.append('modelo_equipo_id', modeloId);
    
    equipoSelect.disabled = true;
    equipoSelect.innerHTML = '<option value="">Cargando equipos...</option>';
    
    fetch(`${window.apiEquiposFiltrados}?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                equiposDisponibles = data.equipos;
                renderizarEquipos(data.equipos);
            } else {
                mostrarError('Error al cargar equipos: ' + data.message);
                equipoSelect.innerHTML = '<option value="">Error al cargar</option>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar equipos');
            equipoSelect.innerHTML = '<option value="">Error de conexión</option>';
        });
}

// Renderizar equipos en el select
function renderizarEquipos(equipos) {
    const equipoSelect = document.getElementById('equipo_id');
    equipoSelect.innerHTML = '<option value="">Seleccione equipo...</option>';
    
    if (equipos.length === 0) {
        equipoSelect.innerHTML = '<option value="">No hay equipos disponibles</option>';
        equipoSelect.disabled = true;
        return;
    }
    
    equipos.forEach(equipo => {
        const option = document.createElement('option');
        option.value = equipo.equipo_id;
        option.textContent = `${equipo.nombreEquipo} - ${equipo.codigoInterno}`;
        option.dataset.horometro = equipo.horometro || '';
        option.dataset.odometro = equipo.odometro || '';
        option.dataset.horometroSuperEstructural = equipo.horometroSuperEstructural || '';
        option.dataset.modeloId = equipo.modeloEquipo_id || '';
        equipoSelect.appendChild(option);
    });
    
    equipoSelect.disabled = false;
}

// Cargar datos del equipo seleccionado
function cargarDatosEquipo() {
    const equipoSelect = document.getElementById('equipo_id');
    const equipoId = equipoSelect.value;
    
    if (!equipoId) {
        document.getElementById('horometro').value = '';
        document.getElementById('odometro').value = '';
        document.getElementById('horometro_superestructura').value = '';
        modeloEquipoSeleccionado = null;
        return;
    }
    
    const option = equipoSelect.options[equipoSelect.selectedIndex];
    document.getElementById('horometro').value = option.dataset.horometro || '';
    document.getElementById('odometro').value = option.dataset.odometro || '';
    document.getElementById('horometro_superestructura').value = option.dataset.horometroSuperEstructural || '';
    
    modeloEquipoSeleccionado = option.dataset.modeloId;
    
    // Debug: verificar que el modelo_id se obtuvo correctamente
    if (!modeloEquipoSeleccionado) {
        console.warn('No se pudo obtener modelo_id del equipo seleccionado');
    }
    
    // Si hay pauta seleccionada, recargar pautas para este modelo
    const correspondePautaSi = document.getElementById('corresponde_pauta_si');
    if (correspondePautaSi && correspondePautaSi.checked && modeloEquipoSeleccionado) {
        cargarPautasPorModelo(modeloEquipoSeleccionado);
    }
}

// ============================================================================
// TIPO DE MANTENIMIENTO Y PAUTAS
// ============================================================================

// Cambiar tipo de mantenimiento
function cambiarTipoMantenimiento() {
    const tipoMantenimientoId = document.getElementById('tipo_mantenimiento_id').value;
    const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');
    const seccionPreventivo = document.getElementById('seccionPreventivo');
    const seccionReparaciones = document.getElementById('seccionReparaciones');
    
    // Obtener el nombre del tipo seleccionado
    const tipoNombre = tipoMantenimientoSelect.options[tipoMantenimientoSelect.selectedIndex]?.textContent?.toLowerCase() || '';
    
    if (tipoNombre.includes('preventivo')) {
        seccionPreventivo.style.display = 'block';
        // Limpiar radio buttons
        document.getElementById('corresponde_pauta_si').checked = false;
        document.getElementById('corresponde_pauta_no').checked = false;
        cambiarCorrespondePauta();
    } else if (tipoNombre.includes('correctivo')) {
        seccionPreventivo.style.display = 'none';
        seccionReparaciones.style.display = 'block';
        // Limpiar items de secciones si había algo de preventivo
        document.getElementById('itemsSeccionesContainer').innerHTML = '<p class="text-muted small" id="noItemsMessage">No hay items agregados. Haga clic en "Agregar Item" para comenzar.</p>';
        itemSeccionIndex = 0;
    } else {
        seccionPreventivo.style.display = 'none';
        seccionReparaciones.style.display = 'none';
    }
}

// Cambiar corresponde pauta
function cambiarCorrespondePauta() {
    const correspondePautaSi = document.getElementById('corresponde_pauta_si');
    const correspondePautaNo = document.getElementById('corresponde_pauta_no');
    const selectPautaContainer = document.getElementById('selectPautaContainer');
    const seccionesPautaContainer = document.getElementById('seccionesPautaContainer');
    const seccionReparaciones = document.getElementById('seccionReparaciones');
    
    if (correspondePautaSi && correspondePautaSi.checked) {
        selectPautaContainer.style.display = 'block';
        seccionesPautaContainer.style.display = 'none';
        seccionReparaciones.style.display = 'none';
        
        // Cargar pautas si hay modelo seleccionado
        if (modeloEquipoSeleccionado) {
            cargarPautasPorModelo(modeloEquipoSeleccionado);
        }
    } else if (correspondePautaNo && correspondePautaNo.checked) {
        selectPautaContainer.style.display = 'none';
        seccionesPautaContainer.style.display = 'none';
        seccionReparaciones.style.display = 'block';
    } else {
        selectPautaContainer.style.display = 'none';
        seccionesPautaContainer.style.display = 'none';
        seccionReparaciones.style.display = 'none';
    }
}

// Cargar pautas por modelo
function cargarPautasPorModelo(modeloId) {
    const pautaSelect = document.getElementById('pauta_id');
    
    if (!modeloId) {
        pautaSelect.innerHTML = '<option value="">Seleccione un equipo primero...</option>';
        return;
    }
    
    // Construir URL correctamente - reemplazar el 0 por el modelo_id
    let url = window.apiPautasPorModeloBase;
    // Reemplazar cualquier número al final de la URL o el 0 específico
    url = url.replace(/\/\d+\//, `/${modeloId}/`);
    // Si no hay reemplazo, intentar reemplazar solo el 0
    if (url === window.apiPautasPorModeloBase) {
        url = url.replace('/0/', `/${modeloId}/`);
    }
    // Si aún no funcionó, reemplazar cualquier ocurrencia de 0
    if (url === window.apiPautasPorModeloBase) {
        url = url.replace('0', modeloId);
    }
    
    console.log('Cargando pautas para modelo:', modeloId);
    console.log('URL:', url);
    
    pautaSelect.disabled = true;
    pautaSelect.innerHTML = '<option value="">Cargando pautas...</option>';
    
    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            pautaSelect.disabled = false;
            if (data.success && data.pautas && data.pautas.length > 0) {
                pautaSelect.innerHTML = '<option value="">Seleccione una pauta...</option>';
                let pautasActivas = 0;
                data.pautas.forEach(pauta => {
                    if (pauta.activo) {
                        pautasActivas++;
                        const option = document.createElement('option');
                        option.value = pauta.pauta_id;
                        option.textContent = pauta.nombre;
                        pautaSelect.appendChild(option);
                    }
                });
                
                if (pautasActivas === 0) {
                    pautaSelect.innerHTML = '<option value="">No hay pautas activas disponibles para este modelo</option>';
                }
            } else {
                pautaSelect.innerHTML = '<option value="">No hay pautas disponibles para este modelo</option>';
            }
        })
        .catch(error => {
            console.error('Error al cargar pautas:', error);
            console.error('URL intentada:', url);
            pautaSelect.disabled = false;
            pautaSelect.innerHTML = '<option value="">Error al cargar pautas. Verifique la consola.</option>';
        });
}

// Cargar secciones de la pauta seleccionada
function cargarSeccionesPauta(pautaIdParam = null) {
    const pautaId = pautaIdParam || document.getElementById('pauta_id')?.value;
    
    // Buscar el contenedor - puede estar en diferentes lugares según el modo
    let seccionesPautaContainer = document.getElementById('seccionesPautaContainer');
    let seccionesPautaList = document.getElementById('seccionesPautaList');
    
    // Si no se encuentra, buscar en todo el documento
    if (!seccionesPautaContainer) {
        seccionesPautaContainer = document.querySelector('#seccionesPautaContainer');
    }
    if (!seccionesPautaList) {
        seccionesPautaList = document.querySelector('#seccionesPautaList');
    }
    
    if (!pautaId) {
        console.log('No hay pautaId para cargar');
        if (seccionesPautaContainer) {
            seccionesPautaContainer.style.display = 'none';
        }
        return;
    }
    
    if (!seccionesPautaContainer || !seccionesPautaList) {
        console.error('No se encontraron los contenedores de secciones de pauta');
        return;
    }
    
    console.log('Cargando pauta con ID:', pautaId);
    
    // Construir URL correctamente
    let url = window.apiDetallePautaOT;
    url = url.replace(/\/\d+\//, `/${pautaId}/`);
    if (url === window.apiDetallePautaOT) {
        url = url.replace('/0/', `/${pautaId}/`);
    }
    if (url === window.apiDetallePautaOT) {
        url = url.replace('0', pautaId);
    }
    
    // Si estamos en modo edición, agregar ot_id a la URL
    if (window.esEdicion && window.otData && window.otData.ot_id) {
        url += `?ot_id=${window.otData.ot_id}`;
    }
    
    console.log('URL de API:', url);
    
    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            if (data.success && data.items) {
                seccionesPautaList.innerHTML = '';
                
                data.items.forEach((item, index) => {
                    const estadoActual = item.estado_seccion_id || null;
                    const estadoNombre = item.estado_seccion_nombre || 'Sin estado';
                    
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'card mb-2';
                    itemDiv.innerHTML = `
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="mb-0">
                                    <i class="bi bi-diagram-3 me-2"></i>${item.seccion_nombre}
                                </h6>
                                <select class="form-select form-select-sm estado-pauta-select" 
                                        style="width: auto;" 
                                        data-item-id="${item.itemPauta_id}"
                                        data-seccion-id="${item.seccion_id}">
                                    <option value="">Seleccione estado...</option>
                                    ${window.estadosOT.map(estado => 
                                        `<option value="${estado.estadoOT_id}" ${estado.estadoOT_id == estadoActual ? 'selected' : ''}>${estado.nombre}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted d-block mb-1">Tipos de Reparación:</small>
                                ${item.tipos_reparacion && item.tipos_reparacion.length > 0 ? 
                                    `<ul class="mb-0 ps-3" style="font-size: 0.875rem;">
                                        ${item.tipos_reparacion.map(tipo => `<li>${tipo.nombre}</li>`).join('')}
                                    </ul>` : 
                                    '<span class="text-muted small">No hay tipos de reparación asignados</span>'
                                }
                            </div>
                        </div>
                    `;
                    seccionesPautaList.appendChild(itemDiv);
                });
                
                seccionesPautaContainer.style.display = 'block';
                console.log('Secciones cargadas exitosamente');
            } else {
                console.log('No se encontraron items en la respuesta');
                seccionesPautaContainer.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error al cargar secciones:', error);
            mostrarError('Error al cargar secciones de la pauta');
            if (seccionesPautaContainer) {
                seccionesPautaContainer.style.display = 'none';
            }
        });
}

// ============================================================================
// PERSONAL A ASIGNAR (CON TABLA Y FILTROS)
// ============================================================================

// Cargar departamentos
function cargarDepartamentos() {
    const deptoSelect = document.getElementById('personalDeptoFilter');
    if (!deptoSelect) {
        // El elemento no existe (probablemente en modo edición)
        return;
    }
    
    fetch(window.apiDepartamentos)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                departamentosDisponibles = data.departamentos;
                deptoSelect.innerHTML = '<option value="">Todos</option>';
                data.departamentos.forEach(depto => {
                    const option = document.createElement('option');
                    option.value = depto.depto_id;
                    option.textContent = depto.depto;
                    deptoSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error al cargar departamentos:', error);
        });
}

// Cargar cargos por departamento
function cargarCargosPorDepto(deptoId) {
    const cargoSelect = document.getElementById('personalCargoFilter');
    if (!cargoSelect) {
        // El elemento no existe (probablemente en modo edición)
        return;
    }
    
    if (!deptoId) {
        cargoSelect.innerHTML = '<option value="">Todos</option>';
        return;
    }
    
    fetch(`${window.apiCargosPorDepto}?depto_id=${deptoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cargoSelect.innerHTML = '<option value="">Todos</option>';
                data.cargos.forEach(cargo => {
                    const option = document.createElement('option');
                    option.value = cargo.cargo_id;
                    option.textContent = cargo.cargo;
                    cargoSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error al cargar cargos:', error);
        });
}

// Cargar personal con filtros
function cargarPersonal() {
    // Verificar si los elementos existen (no existen en modo edición)
    const searchElement = document.getElementById('personalSearch');
    const empresaFilter = document.getElementById('personalEmpresaFilter');
    const cargoFilter = document.getElementById('personalCargoFilter');
    const deptoFilter = document.getElementById('personalDeptoFilter');
    
    if (!searchElement || !empresaFilter || !cargoFilter || !deptoFilter) {
        // Los elementos no existen (probablemente en modo edición)
        return;
    }
    
    const search = searchElement.value;
    const empresaId = empresaFilter.value;
    const cargoId = cargoFilter.value;
    const deptoId = deptoFilter.value;
    
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (empresaId) params.append('empresa_id', empresaId);
    if (cargoId) params.append('cargo_id', cargoId);
    if (deptoId) params.append('depto_id', deptoId);
    
    fetch(`${window.apiPersonalMaquinarias}?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                personalDisponible = data.personal;
                // Solo renderizar si existe la tabla (no existe en modo edición)
                const personalTableBody = document.getElementById('personalTableBody');
                if (personalTableBody) {
                    renderizarTablaPersonal(data.personal);
                    actualizarPersonalSeleccionado();
                }
            } else {
                mostrarError('Error al cargar personal: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error de conexión al cargar personal');
        });
}

// Renderizar tabla de personal
function renderizarTablaPersonal(personal) {
    const tbody = document.getElementById('personalTableBody');
    
    if (personal.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-3">
                    <i class="bi bi-inbox fs-4 text-muted"></i>
                    <p class="text-muted small mb-0 mt-2">No se encontró personal con los filtros aplicados</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = personal.map(p => {
        const isChecked = personalSeleccionados.includes(p.personal_id);
        return `
            <tr class="${isChecked ? 'table-primary' : ''}">
                <td class="text-center">
                    <input class="form-check-input personal-checkbox" type="checkbox" 
                           value="${p.personal_id}" 
                           ${isChecked ? 'checked' : ''}
                           onchange="togglePersonalSeleccionado(this)">
                </td>
                <td><strong>${p.nombre_completo}</strong></td>
                <td>${p.rut}</td>
                <td>${p.cargo}</td>
                <td>${p.departamento}</td>
                <td>${p.empresa}</td>
            </tr>
        `;
    }).join('');
}

// Toggle personal seleccionado
function togglePersonalSeleccionado(checkbox) {
    const personalId = parseInt(checkbox.value);
    
    if (checkbox.checked) {
        if (!personalSeleccionados.includes(personalId)) {
            personalSeleccionados.push(personalId);
        }
    } else {
        personalSeleccionados = personalSeleccionados.filter(id => id !== personalId);
    }
    
    // Actualizar visualización
    const row = checkbox.closest('tr');
    if (checkbox.checked) {
        row.classList.add('table-primary');
    } else {
        row.classList.remove('table-primary');
    }
    
    actualizarPersonalSeleccionado();
}

// Seleccionar/deseleccionar todo el personal visible
function toggleSeleccionarTodoPersonal() {
    const selectAll = document.getElementById('selectAllPersonal');
    const checkboxes = document.querySelectorAll('.personal-checkbox');
    const todosSeleccionados = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => {
        cb.checked = !todosSeleccionados;
        togglePersonalSeleccionado(cb);
    });
}

// Actualizar badges de personal seleccionado
function actualizarPersonalSeleccionado() {
    const container = document.getElementById('personalSeleccionadoContainer');
    const badges = document.getElementById('personalSeleccionadoBadges');
    
    if (personalSeleccionados.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Obtener información del personal seleccionado
    const personalSeleccionadoInfo = personalSeleccionados.map(id => {
        const p = personalDisponible.find(per => per.personal_id === id);
        return p || { personal_id: id, nombre_completo: 'Desconocido' };
    });
    
    badges.innerHTML = personalSeleccionadoInfo.map(p => `
        <span class="badge bg-primary">
            ${p.nombre_completo}
            <button type="button" class="btn-close btn-close-white ms-1" 
                    onclick="quitarPersonalSeleccionado(${p.personal_id})" 
                    style="font-size: 0.6rem;"></button>
        </span>
    `).join('');
}

// Quitar personal seleccionado
function quitarPersonalSeleccionado(personalId) {
    personalSeleccionados = personalSeleccionados.filter(id => id !== personalId);
    
    // Actualizar checkbox
    const checkbox = document.querySelector(`.personal-checkbox[value="${personalId}"]`);
    if (checkbox) {
        checkbox.checked = false;
        togglePersonalSeleccionado(checkbox);
    }
    
    actualizarPersonalSeleccionado();
}

// ============================================================================
// ITEMS DE SECCIONES (Para cuando NO es pauta o es correctivo)
// ============================================================================

// Agregar item de sección (solo en modo creación)
function agregarItemSeccion(seccionIdInicial = null, tiposIdsIniciales = [], estadoInicial = null) {
    if (window.esEdicion) {
        alert('No se pueden agregar items en modo edición');
        return;
    }
    const container = document.getElementById('itemsSeccionesContainer');
    const noItemsMessage = document.getElementById('noItemsMessage');
    const template = document.getElementById('itemSeccionTemplate');
    
    if (!template) return;
    
    // Ocultar mensaje de "no hay items"
    if (noItemsMessage) {
        noItemsMessage.style.display = 'none';
    }
    
    // Clonar template
    const clone = template.content.cloneNode(true);
    const itemDiv = clone.querySelector('.item-seccion');
    
    // Asignar índice
    itemSeccionIndex++;
    itemDiv.dataset.itemIndex = itemSeccionIndex;
    itemDiv.querySelector('.item-number').textContent = itemSeccionIndex;
    
    // Agregar al DOM primero
    container.appendChild(clone);
    
    // Si es un item existente, pre-seleccionar sección DESPUÉS de agregar al DOM
    if (seccionIdInicial) {
        const itemAgregado = container.querySelector(`[data-item-index="${itemSeccionIndex}"]`);
        if (!itemAgregado) return;
        
        const seccionSelect = itemAgregado.querySelector('.seccion-select');
        seccionSelect.value = seccionIdInicial;
        
        // Cargar tipos de reparación y pre-seleccionar
        const tiposContainer = itemAgregado.querySelector('.tipos-reparacion-list');
        cargarTiposReparacionParaSeccion(seccionIdInicial, tiposContainer, tiposIdsIniciales);
        
        // Establecer estado
        const estadoSelect = itemAgregado.querySelector('.estado-seccion-select');
        if (estadoSelect && estadoInicial) {
            estadoSelect.value = estadoInicial;
        }
    }
}

// Cargar tipos de reparación para una sección
function cargarTiposReparacionItem(selectElement) {
    const seccionId = selectElement.value;
    const itemDiv = selectElement.closest('.item-seccion');
    const tiposContainer = itemDiv.querySelector('.tipos-reparacion-list');
    
    if (!seccionId) {
        tiposContainer.innerHTML = '<p class="text-muted small mb-0">Seleccione primero una sección</p>';
        return;
    }
    
    cargarTiposReparacionParaSeccion(seccionId, tiposContainer);
}

// Cargar tipos de reparación para una sección (función auxiliar)
function cargarTiposReparacionParaSeccion(seccionId, container, tiposIdsPreseleccionados = []) {
    const tiposFiltrados = window.tiposReparacion.filter(t => t.seccion_id == seccionId);
    
    if (tiposFiltrados.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">No hay tipos de reparación para esta sección</p>';
        return;
    }
    
    container.innerHTML = '<div class="row g-2">' + tiposFiltrados.map(tipo => {
        const checked = tiposIdsPreseleccionados.includes(tipo.tipoReparacion_id) ? 'checked' : '';
        return `
            <div class="col-md-6">
                <div class="form-check">
                    <input class="form-check-input tipo-reparacion-checkbox" type="checkbox" 
                           value="${tipo.tipoReparacion_id}" ${checked}>
                    <label class="form-check-label">
                        ${tipo.nombre}
                    </label>
                </div>
            </div>
        `;
    }).join('') + '</div>';
}

// Eliminar item de sección
function eliminarItemSeccion(button) {
    const itemDiv = button.closest('.item-seccion');
    itemDiv.remove();
    
    // Si no quedan items, mostrar mensaje
    const container = document.getElementById('itemsSeccionesContainer');
    if (container.children.length === 0) {
        container.innerHTML = '<p class="text-muted small" id="noItemsMessage">No hay items agregados. Haga clic en "Agregar Item" para comenzar.</p>';
    }
}

// Actualizar estado de sección
function actualizarEstadoSeccion(selectElement) {
    // Solo actualizar visualmente, el valor se guarda en el submit
}

// ============================================================================
// CARGAR DATOS DE EDICIÓN
// ============================================================================

function cargarDatosEdicion() {
    const data = window.otData;
    
    // Cargar filtros en cascada de equipos (solo si existen - no existen en modo edición)
    const tipoEquipoSelect = document.getElementById('tipo_equipo_id');
    if (tipoEquipoSelect && data.tipo_equipo_id) {
        tipoEquipoSelect.value = data.tipo_equipo_id;
        filtrarMarcasPorTipo();
        
        setTimeout(() => {
            const marcaEquipoSelect = document.getElementById('marca_equipo_id');
            if (marcaEquipoSelect && data.marca_equipo_id) {
                marcaEquipoSelect.value = data.marca_equipo_id;
                filtrarModelosPorTipoYMarca();
                
                setTimeout(() => {
                    const modeloEquipoSelect = document.getElementById('modelo_equipo_id');
                    if (modeloEquipoSelect && data.modelo_id) {
                        modeloEquipoSelect.value = data.modelo_id;
                        filtrarEquipos();
                        
                        setTimeout(() => {
                            const equipoSelect = document.getElementById('equipo_id');
                            if (equipoSelect && data.equipo_id) {
                                equipoSelect.value = data.equipo_id;
                                cargarDatosEquipo();
                            }
                        }, 500);
                    }
                }, 500);
            }
        }, 500);
    }
    
    // Cargar tipo de mantenimiento (solo si existe - no existe en modo edición)
    const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');
    if (tipoMantenimientoSelect && data.tipo_mantenimiento_id) {
        tipoMantenimientoSelect.value = data.tipo_mantenimiento_id;
        cambiarTipoMantenimiento();
    }
    
    // Cargar estados (siempre existen)
    const estadoOTSelect = document.getElementById('estado_ot_id');
    if (estadoOTSelect && data.estado_ot_id) {
        estadoOTSelect.value = data.estado_ot_id;
    }
    
    const estadoEquipoSelect = document.getElementById('estado_equipo_id');
    if (estadoEquipoSelect && data.estado_equipo_id) {
        estadoEquipoSelect.value = data.estado_equipo_id;
    }
    
    // Cargar personal seleccionado (solo si existe la tabla - no existe en modo edición)
    setTimeout(() => {
        if (data.personal_asignado) {
            personalSeleccionados = [...data.personal_asignado];
            const personalTableBody = document.getElementById('personalTableBody');
            if (personalTableBody) {
                cargarPersonal();
            }
        }
    }, 1000);
    
    // Cargar secciones en modo edición - función auxiliar
    function cargarSeccionesEdicion() {
        // Verificar que los datos necesarios estén disponibles
        if (!window.secciones || !window.tiposReparacion || !window.estadosOT) {
            // Si no están disponibles, esperar un poco más
            setTimeout(cargarSeccionesEdicion, 100);
            return;
        }
        
        if (data.corresponde_pauta && data.pauta_id) {
            // Cargar secciones de la pauta
            cargarSeccionesPauta(data.pauta_id);
        } else if (data.items_secciones && data.items_secciones.length > 0) {
            // Cargar items de secciones manuales
            const container = document.getElementById('itemsSeccionesContainer');
            if (container) {
                container.innerHTML = '';
                data.items_secciones.forEach((item, index) => {
                    // Buscar nombre de sección
                    let seccionNombre = 'Sección';
                    if (window.secciones && window.secciones.length > 0) {
                        const seccion = window.secciones.find(s => s.seccion_id == item.seccion_id);
                        if (seccion) {
                            seccionNombre = seccion.nombre;
                        }
                    }
                    
                    // Buscar nombres de tipos de reparación
                    let tiposReparacionNombres = [];
                    if (window.tiposReparacion && window.tiposReparacion.length > 0 && item.tipos_reparacion_ids) {
                        tiposReparacionNombres = item.tipos_reparacion_ids.map(id => {
                            const tipo = window.tiposReparacion.find(t => t.tipoReparacion_id == id);
                            return tipo ? tipo.nombre : '';
                        }).filter(n => n);
                    }
                    
                    // Crear elemento para mostrar la sección con selector de estado
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'card mb-2';
                    
                    itemDiv.innerHTML = `
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="mb-0">
                                    <i class="bi bi-diagram-3 me-2"></i>${seccionNombre}
                                </h6>
                                <select class="form-select form-select-sm estado-seccion-select" 
                                        style="width: auto;" 
                                        data-seccion-id="${item.seccion_id}"
                                        data-item-id="${item.itemSeccionOT_id || ''}">
                                    <option value="">Seleccione estado...</option>
                                    ${window.estadosOT.map(estado => 
                                        `<option value="${estado.estadoOT_id}" ${estado.estadoOT_id == item.estado_seccion_id ? 'selected' : ''}>${estado.nombre}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted d-block mb-1">Tipos de Reparación:</small>
                                ${tiposReparacionNombres.length > 0 ? 
                                    `<ul class="mb-0 ps-3" style="font-size: 0.875rem;">
                                        ${tiposReparacionNombres.map(nombre => `<li>${nombre}</li>`).join('')}
                                    </ul>` : 
                                    '<span class="text-muted small">No hay tipos de reparación asignados</span>'
                                }
                            </div>
                        </div>
                    `;
                    container.appendChild(itemDiv);
                });
            }
        }
    }
    
    // Intentar cargar inmediatamente, y si no están los datos, esperar
    if (window.secciones && window.tiposReparacion && window.estadosOT) {
        cargarSeccionesEdicion();
    } else {
        setTimeout(cargarSeccionesEdicion, 100);
    }
}

// ============================================================================
// GUARDAR ORDEN DE TRABAJO
// ============================================================================

// Agregar observación (solo en modo edición)
function agregarObservacion() {
    const nuevaObservacion = document.getElementById('nuevaObservacion');
    const observacionTexto = nuevaObservacion.value.trim();
    
    if (!observacionTexto) {
        alert('Debe ingresar una observación');
        return;
    }
    
    if (!window.esEdicion || !window.apiAgregarObservacionOT) {
        alert('Error: No se puede agregar observación en modo creación');
        return;
    }
    
    fetch(window.apiAgregarObservacionOT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify({
            observacion: observacionTexto
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Agregar la nueva observación al historial visualmente
            const historialContainer = document.getElementById('historialObservaciones');
            const nuevaObsDiv = document.createElement('div');
            nuevaObsDiv.className = 'mb-3 pb-3 border-bottom';
            nuevaObsDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-1">
                    <strong class="text-primary">${data.historial.usuario || 'Sistema'}</strong>
                    <small class="text-muted">${data.historial.fecha}</small>
                </div>
                <p class="mb-0">${data.historial.observacion}</p>
            `;
            historialContainer.insertBefore(nuevaObsDiv, historialContainer.firstChild);
            
            // Limpiar el campo
            nuevaObservacion.value = '';
            
            mostrarNotificacion('Observación agregada exitosamente', 'success');
        } else {
            alert('Error al agregar observación: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error de conexión al agregar observación');
    });
}

function guardarOrdenTrabajo(event) {
    event.preventDefault();
    
    // Si es edición, solo actualizar estados y fecha_fin
    if (window.esEdicion) {
        const formData = {
            ot_id: document.getElementById('ot_id').value,
            estado_ot_id: document.getElementById('estado_ot_id').value,
            estado_equipo_id: document.getElementById('estado_equipo_id').value,
            fecha_fin: document.getElementById('fecha_fin_edicion')?.value || null
        };
        
        // Recolectar estados de secciones de pauta
        const estadosPauta = [];
        document.querySelectorAll('.estado-pauta-select').forEach(select => {
            if (select.value) {
                estadosPauta.push({
                    itemPauta_id: parseInt(select.dataset.itemId),
                    seccion_id: parseInt(select.dataset.seccionId),
                    estado_seccion_id: parseInt(select.value)
                });
            }
        });
        
        // Recolectar estados de items de secciones manuales
        const estadosSecciones = [];
        document.querySelectorAll('.estado-seccion-select').forEach(select => {
            if (select.value && select.dataset.seccionId) {
                estadosSecciones.push({
                    seccion_id: parseInt(select.dataset.seccionId),
                    estado_seccion_id: parseInt(select.value)
                });
            }
        });
        
        formData.estados_pauta = estadosPauta;
        formData.estados_secciones = estadosSecciones;
        
        // Enviar solo actualización de estados
        fetch(window.apiGuardarOT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data);
            if (data.success) {
                // Verificar si se marcó como FINALIZADA
                const estadoOTSelect = document.getElementById('estado_ot_id');
                const estadoOTNombre = estadoOTSelect ? estadoOTSelect.options[estadoOTSelect.selectedIndex]?.textContent?.toUpperCase() || '' : '';
                
                try {
                    if (estadoOTNombre.includes('FINALIZADA')) {
                        mostrarNotificacion('Orden de trabajo finalizada exitosamente. Será movida a la lista de finalizadas.', 'success');
                    } else {
                        mostrarNotificacion('Orden de trabajo actualizada exitosamente', 'success');
                    }
                } catch (e) {
                    console.error('Error al mostrar notificación:', e);
                    alert('Orden de trabajo actualizada exitosamente');
                }
                
                // Redirigir a la lista después de 1.5 segundos
                console.log('Redirigiendo a la lista de OTs...');
                setTimeout(() => {
                    window.location.replace('/maquinarias/ordenes-trabajo/');
                }, 1500);
            } else {
                alert('Error al actualizar: ' + (data.message || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión al actualizar');
        });
        
        return;
    }
    
    // Modo creación - validaciones básicas
    const equipoId = document.getElementById('equipo_id').value;
    const tipoMantenimientoId = document.getElementById('tipo_mantenimiento_id').value;
    
    if (!equipoId) {
        alert('Debe seleccionar un equipo');
        return;
    }
    
    if (!tipoMantenimientoId) {
        alert('Debe seleccionar un tipo de mantenimiento');
        return;
    }
    
    // Obtener estado PENDIENTE por defecto (siempre se usa en creación)
    const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
    const estadoPendienteId = estadoPendiente ? estadoPendiente.estadoOT_id : null;
    
    // Recolectar datos del formulario
    const formData = {
        ot_id: null,
        equipo_id: equipoId,
        fecha_inicio: document.getElementById('fecha_inicio').value,
        fecha_fin: document.getElementById('fecha_fin').value,
        tipo_mantenimiento_id: tipoMantenimientoId,
        estado_ot_id: estadoPendienteId,  // Siempre PENDIENTE en creación
        estado_equipo_id: document.getElementById('estado_equipo_id').value,
        observaciones: document.getElementById('observaciones').value,
        personal_asignado: personalSeleccionados
    };
    
    // Obtener nombre del tipo de mantenimiento
    const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');
    const tipoMantenimientoNombre = tipoMantenimientoSelect.options[tipoMantenimientoSelect.selectedIndex]?.textContent?.toLowerCase() || '';
    
    // Si es preventivo
    if (tipoMantenimientoNombre.includes('preventivo')) {
        const correspondePautaSi = document.getElementById('corresponde_pauta_si').checked;
        formData.corresponde_pauta = correspondePautaSi;
        
        if (correspondePautaSi) {
            formData.pauta_id = document.getElementById('pauta_id').value;
            
            // Recolectar estados de las secciones de la pauta
            // En creación, siempre usar PENDIENTE (se ignora en el backend)
            const estadosPauta = [];
            const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
            const estadoPendienteId = estadoPendiente ? estadoPendiente.estadoOT_id : null;
            
            document.querySelectorAll('.estado-pauta-select').forEach(select => {
                if (select.dataset.seccionId) {
                    estadosPauta.push({
                        itemPauta_id: parseInt(select.dataset.itemId),
                        seccion_id: parseInt(select.dataset.seccionId),
                        estado_seccion_id: estadoPendienteId  // Siempre PENDIENTE en creación
                    });
                }
            });
            formData.estados_pauta = estadosPauta;
        } else {
            // Recolectar items de secciones manuales
            formData.items_secciones = recolectarItemsSecciones();
        }
    } else {
        // Correctivo - recolectar items de secciones
        formData.items_secciones = recolectarItemsSecciones();
    }
    
    // Enviar datos
    fetch(window.apiGuardarOT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Orden de trabajo guardada exitosamente');
            window.location.href = '/maquinarias/ordenes-trabajo/';
        } else {
            alert('Error al guardar: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error de conexión al guardar');
    });
}

// Función auxiliar para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo) {
    // Crear elemento de notificación
    const notificacion = document.createElement('div');
    notificacion.className = `alert alert-${tipo === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notificacion.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notificacion.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notificacion);
    
    // Auto-remover después de 3 segundos
    setTimeout(() => {
        notificacion.remove();
    }, 3000);
}

// Recolectar items de secciones
function recolectarItemsSecciones() {
    const items = [];
    const itemsSecciones = document.querySelectorAll('.item-seccion');
    
    // Obtener estado PENDIENTE por defecto (siempre se usa en creación)
    const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
    const estadoPendienteId = estadoPendiente ? estadoPendiente.estadoOT_id : null;
    
    itemsSecciones.forEach(itemDiv => {
        const seccionSelect = itemDiv.querySelector('.seccion-select');
        const checkboxes = itemDiv.querySelectorAll('.tipo-reparacion-checkbox:checked');
        
        if (seccionSelect.value && checkboxes.length > 0) {
            items.push({
                seccion_id: parseInt(seccionSelect.value),
                tipos_reparacion_ids: Array.from(checkboxes).map(cb => parseInt(cb.value)),
                estado_seccion_id: estadoPendienteId  // Siempre PENDIENTE en creación
            });
        }
    });
    
    return items;
}

// Mostrar error
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);
    console.error(mensaje);
}
