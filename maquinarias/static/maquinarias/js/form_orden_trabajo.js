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
            limpiarPautaMantenimiento();
            // Reiniciar todos los filtros en cascada: tipo, marca, modelo y equipo
            reiniciarFiltrosDesdeTipo();
            filtrarEquipos();
        });
    }
    
    const tipoEquipoSelect = document.getElementById('tipo_equipo_id');
    if (tipoEquipoSelect) {
        tipoEquipoSelect.addEventListener('change', function() {
            limpiarPautaMantenimiento();
            filtrarMarcasPorTipo();
        });
    }
    
    const marcaEquipoSelect = document.getElementById('marca_equipo_id');
    if (marcaEquipoSelect) {
        marcaEquipoSelect.addEventListener('change', function() {
            limpiarPautaMantenimiento();
            filtrarModelosPorTipoYMarca();
        });
    }
    
    const modeloEquipoSelect = document.getElementById('modelo_equipo_id');
    if (modeloEquipoSelect) {
        modeloEquipoSelect.addEventListener('change', function() {
            limpiarPautaMantenimiento();
            // Reiniciar equipo cuando cambia el modelo
            const equipoSelect = document.getElementById('equipo_id');
            if (equipoSelect) {
                equipoSelect.value = '';
                equipoSelect.disabled = true;
                equipoSelect.innerHTML = '<option value="">Cargando equipos...</option>';
            }
            // Actualizar modeloEquipoSeleccionado cuando cambia el select de modelo
            modeloEquipoSeleccionado = modeloEquipoSelect.value || null;
            // Filtrar equipos con el nuevo modelo
            filtrarEquipos();
            // Si corresponde_pauta está marcado como "Sí", cargar pautas
            const correspondePautaSi = document.getElementById('corresponde_pauta_si');
            if (correspondePautaSi && correspondePautaSi.checked && modeloEquipoSeleccionado) {
                cargarPautasPorModelo(modeloEquipoSeleccionado);
            }
        });
    }
    
    const equipoSelect = document.getElementById('equipo_id');
    if (equipoSelect) {
        equipoSelect.addEventListener('change', function() {
            cargarDatosEquipo();
            validarDisponibilidad();
        });
    }
    
    // Event listeners para validación de fechas
    const fechaInicioInput = document.getElementById('fecha_inicio');
    if (fechaInicioInput) {
        fechaInicioInput.addEventListener('change', validarDisponibilidad);
        fechaInicioInput.addEventListener('blur', validarDisponibilidad);
    }
    
    const fechaFinInput = document.getElementById('fecha_fin');
    if (fechaFinInput) {
        fechaFinInput.addEventListener('change', function() {
            validarFechaFin();
            validarDisponibilidad();
        });
        fechaFinInput.addEventListener('blur', function() {
            validarFechaFin();
            validarDisponibilidad();
        });
    }
    
    const fechaFinEdicionInput = document.getElementById('fecha_fin_edicion');
    if (fechaFinEdicionInput) {
        fechaFinEdicionInput.addEventListener('change', validarFechaFinEdicion);
        fechaFinEdicionInput.addEventListener('blur', validarFechaFinEdicion);
    }
    
    const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');
    if (tipoMantenimientoSelect) {
        tipoMantenimientoSelect.addEventListener('change', cambiarTipoMantenimiento);
    }
    
    // Event listeners para radio buttons de corresponde_pauta
    const correspondePautaSi = document.getElementById('corresponde_pauta_si');
    const correspondePautaNo = document.getElementById('corresponde_pauta_no');
    if (correspondePautaSi) {
        correspondePautaSi.addEventListener('change', cambiarCorrespondePauta);
    }
    if (correspondePautaNo) {
        correspondePautaNo.addEventListener('change', cambiarCorrespondePauta);
    }
    
    // Event listener para select de pauta
    const pautaSelect = document.getElementById('pauta_id');
    if (pautaSelect) {
        pautaSelect.addEventListener('change', function(e) {
            const pautaId = e.target.value;
            if (pautaId) {
                console.log('Pauta seleccionada:', pautaId);
                cargarSeccionesPauta(pautaId);
            } else {
                // Si no hay pauta seleccionada, ocultar secciones
                const seccionesPautaContainer = document.querySelector('#seccionPreventivo #seccionesPautaContainer') || 
                                                 document.getElementById('seccionesPautaContainer');
                if (seccionesPautaContainer) {
                    seccionesPautaContainer.style.display = 'none';
                    seccionesPautaContainer.classList.add('hidden-section');
                }
            }
        });
    }
    
    // Event listener para botón agregar item sección
    const btnAgregarItemSeccion = document.getElementById('btnAgregarItemSeccion');
    if (btnAgregarItemSeccion) {
        btnAgregarItemSeccion.addEventListener('click', agregarItemSeccion);
    }
    
    // Event listener para botón agregar observación
    const btnAgregarObservacion = document.getElementById('btnAgregarObservacion');
    if (btnAgregarObservacion) {
        btnAgregarObservacion.addEventListener('click', agregarObservacion);
    }
    
    // Event listener para select all personal
    const selectAllPersonal = document.getElementById('selectAllPersonal');
    if (selectAllPersonal) {
        selectAllPersonal.addEventListener('change', toggleSeleccionarTodoPersonal);
    }
    
    // Event listeners delegados para elementos dinámicos (items de secciones)
    const itemsSeccionesContainer = document.getElementById('itemsSeccionesContainer');
    if (itemsSeccionesContainer) {
        // Delegar eventos para selects de sección
        itemsSeccionesContainer.addEventListener('change', function(e) {
            if (e.target.classList.contains('seccion-select')) {
                cargarTiposReparacionItem(e.target);
                // Actualizar disponibilidad de secciones después de cambiar selección
                actualizarSeccionesDisponibles();
            }
        });
        
        // Delegar eventos para selects de estado
        itemsSeccionesContainer.addEventListener('change', function(e) {
            if (e.target.classList.contains('estado-seccion-select')) {
                actualizarEstadoSeccion(e.target);
            }
        });
        
        // Delegar eventos para botones de eliminar
        itemsSeccionesContainer.addEventListener('click', function(e) {
            if (e.target.closest('.btnEliminarItemSeccion')) {
                eliminarItemSeccion(e.target.closest('.btnEliminarItemSeccion'));
            }
        });
    }
    
    // Event listener delegado para quitar personal seleccionado (badges)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-close') && e.target.closest('#personalSeleccionadoBadges')) {
            const badge = e.target.closest('.badge');
            const personalId = parseInt(badge.dataset.personalId);
            if (personalId) {
                quitarPersonalSeleccionado(personalId);
            }
        }
    });
    
    // Event listeners para filtros de personal (solo si existen)
    const personalSearch = document.getElementById('personalSearch');
    if (personalSearch) {
        personalSearch.addEventListener('input', debounce(cargarPersonal, 500));
    }
    
    const personalEmpresaFilter = document.getElementById('personalEmpresaFilter');
    if (personalEmpresaFilter) {
        personalEmpresaFilter.addEventListener('change', cargarPersonal);
    }
    
    // Los filtros de cargo y departamento están deshabilitados (solo MAQUINARIAS y MECÁNICO)
    // No se agregan event listeners para estos campos ya que están deshabilitados y se preseleccionan automáticamente
    
    // Inicializar date pickers chilenos
    if (typeof DatePickerChile !== 'undefined') {
        DatePickerChile.inicializar();
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

// Función para reiniciar filtros desde tipo (reinicia tipo, marca, modelo y equipo)
function reiniciarFiltrosDesdeTipo() {
    const tipoSelect = document.getElementById('tipo_equipo_id');
    const marcaSelect = document.getElementById('marca_equipo_id');
    const modeloSelect = document.getElementById('modelo_equipo_id');
    const equipoSelect = document.getElementById('equipo_id');
    
    if (tipoSelect) {
        tipoSelect.value = '';
    }
    if (marcaSelect) {
        marcaSelect.innerHTML = '<option value="">Todas</option>';
        marcaSelect.disabled = true;
    }
    if (modeloSelect) {
        modeloSelect.innerHTML = '<option value="">Primero seleccione marca...</option>';
        modeloSelect.disabled = true;
    }
    if (equipoSelect) {
        equipoSelect.innerHTML = '<option value="">Primero seleccione modelo...</option>';
        equipoSelect.disabled = true;
    }
}

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
        
        // Limpiar pauta seleccionada y ocultar secciones
        limpiarPautaMantenimiento();
        const pautaSelect = document.getElementById('pauta_id');
        if (pautaSelect) {
            pautaSelect.innerHTML = '<option value="">Primero seleccione un equipo...</option>';
        }
        
        return;
    }
    
    const option = equipoSelect.options[equipoSelect.selectedIndex];
    document.getElementById('horometro').value = option.dataset.horometro || '';
    document.getElementById('odometro').value = option.dataset.odometro || '';
    document.getElementById('horometro_superestructura').value = option.dataset.horometroSuperEstructural || '';
    
    const modeloAnterior = modeloEquipoSeleccionado;
    modeloEquipoSeleccionado = option.dataset.modeloId;
    
    // También actualizar el select de modelo si está disponible
    const modeloSelect = document.getElementById('modelo_equipo_id');
    if (modeloSelect && modeloEquipoSeleccionado && modeloSelect.value !== modeloEquipoSeleccionado) {
        modeloSelect.value = modeloEquipoSeleccionado;
    }
    
    // Debug: verificar que el modelo_id se obtuvo correctamente
    if (!modeloEquipoSeleccionado) {
        console.warn('No se pudo obtener modelo_id del equipo seleccionado');
    }
    
    // Si cambió el modelo del equipo, limpiar pauta seleccionada y ocultar secciones
    if (modeloAnterior && modeloAnterior !== modeloEquipoSeleccionado) {
        limpiarPautaMantenimiento();
    }
    
    // Si hay pauta seleccionada y corresponde_pauta está marcado, recargar pautas para este modelo
    const correspondePautaSi = document.getElementById('corresponde_pauta_si');
    if (correspondePautaSi && correspondePautaSi.checked && modeloEquipoSeleccionado) {
        cargarPautasPorModelo(modeloEquipoSeleccionado);
    }
}

// ============================================================================
// TIPO DE MANTENIMIENTO Y PAUTAS
// ============================================================================

// Función para limpiar la pauta de mantenimiento preventivo
function limpiarPautaMantenimiento() {
    const pautaSelect = document.getElementById('pauta_id');
    if (pautaSelect) {
        pautaSelect.value = '';
        // No limpiar las opciones, solo el valor seleccionado
    }
    
    // Ocultar secciones de pauta cargadas
    const seccionesPautaContainer = document.querySelector('#seccionPreventivo #seccionesPautaContainer') || 
                                     document.getElementById('seccionesPautaContainer');
    if (seccionesPautaContainer) {
        seccionesPautaContainer.style.display = 'none';
        seccionesPautaContainer.classList.add('hidden-section');
        const seccionesPautaList = document.querySelector('#seccionPreventivo #seccionesPautaList') || 
                                    document.getElementById('seccionesPautaList');
        if (seccionesPautaList) {
            seccionesPautaList.innerHTML = '';
        }
    }
}

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
    // Buscar el contenedor dentro de #seccionPreventivo primero (modo creación)
    const seccionesPautaContainer = document.querySelector('#seccionPreventivo #seccionesPautaContainer') || 
                                     document.getElementById('seccionesPautaContainer');
    const seccionReparaciones = document.getElementById('seccionReparaciones');
    
    if (correspondePautaSi && correspondePautaSi.checked) {
        if (selectPautaContainer) {
            selectPautaContainer.style.display = 'block';
            selectPautaContainer.classList.remove('hidden-section');
        }
        if (seccionesPautaContainer) {
            seccionesPautaContainer.style.display = 'none';
            seccionesPautaContainer.classList.add('hidden-section');
        }
        if (seccionReparaciones) {
            seccionReparaciones.style.display = 'none';
        }
        
        // Obtener modelo_id del equipo seleccionado o del select de modelo
        let modeloIdParaPautas = modeloEquipoSeleccionado;
        
        // Si no hay modeloEquipoSeleccionado (no se ha seleccionado equipo), 
        // intentar obtenerlo del select de modelo directamente
        if (!modeloIdParaPautas) {
            const modeloSelect = document.getElementById('modelo_equipo_id');
            if (modeloSelect && modeloSelect.value) {
                modeloIdParaPautas = modeloSelect.value;
            }
        }
        
        // Cargar pautas si hay modelo disponible
        if (modeloIdParaPautas) {
            cargarPautasPorModelo(modeloIdParaPautas);
        } else {
            // Si no hay modelo seleccionado, mostrar mensaje
            const pautaSelect = document.getElementById('pauta_id');
            if (pautaSelect) {
                pautaSelect.innerHTML = '<option value="">Primero seleccione un equipo o modelo...</option>';
            }
        }
    } else if (correspondePautaNo && correspondePautaNo.checked) {
        if (selectPautaContainer) {
            selectPautaContainer.style.display = 'none';
            selectPautaContainer.classList.add('hidden-section');
        }
        if (seccionesPautaContainer) {
            seccionesPautaContainer.style.display = 'none';
            seccionesPautaContainer.classList.add('hidden-section');
        }
        if (seccionReparaciones) {
            seccionReparaciones.style.display = 'block';
        }
        // Limpiar items de secciones si había algo de preventivo con pauta
        const itemsContainer = document.getElementById('itemsSeccionesContainer');
        if (itemsContainer) {
            itemsContainer.innerHTML = '<p class="text-muted small" id="noItemsMessage">No hay items agregados. Haga clic en "Agregar Item" para comenzar.</p>';
            itemSeccionIndex = 0; // Reiniciar contador
        }
    } else {
        if (selectPautaContainer) {
            selectPautaContainer.style.display = 'none';
            selectPautaContainer.classList.add('hidden-section');
        }
        if (seccionesPautaContainer) {
            seccionesPautaContainer.style.display = 'none';
            seccionesPautaContainer.classList.add('hidden-section');
        }
        if (seccionReparaciones) {
            seccionReparaciones.style.display = 'none';
        }
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
    // Asegurarse de que pautaIdParam sea un número o string válido, no un objeto Event
    let pautaId = null;
    if (pautaIdParam) {
        // Si es un objeto Event, obtener el value del target
        if (pautaIdParam instanceof Event) {
            pautaId = pautaIdParam.target?.value;
        } else {
            pautaId = pautaIdParam;
        }
    }
    
    // Si aún no tenemos pautaId, intentar obtenerlo del select
    if (!pautaId) {
        const pautaSelect = document.getElementById('pauta_id');
        pautaId = pautaSelect?.value;
    }
    
    // Buscar el contenedor - puede estar en diferentes lugares según el modo
    // Priorizar el contenedor dentro de la sección de preventivo (modo creación)
    let seccionesPautaContainer = document.querySelector('#seccionPreventivo #seccionesPautaContainer');
    if (!seccionesPautaContainer) {
        seccionesPautaContainer = document.getElementById('seccionesPautaContainer');
    }
    
    let seccionesPautaList = document.querySelector('#seccionPreventivo #seccionesPautaList');
    if (!seccionesPautaList) {
        seccionesPautaList = document.getElementById('seccionesPautaList');
    }
    
    if (!pautaId) {
        console.log('No hay pautaId para cargar');
        if (seccionesPautaContainer) {
            seccionesPautaContainer.style.display = 'none';
            seccionesPautaContainer.classList.add('hidden-section');
        }
        return;
    }
    
    if (!seccionesPautaContainer || !seccionesPautaList) {
        console.error('No se encontraron los contenedores de secciones de pauta');
        console.error('seccionesPautaContainer:', seccionesPautaContainer);
        console.error('seccionesPautaList:', seccionesPautaList);
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
                    // Si no hay estado (nueva OT), usar Pendiente por defecto
                    let estadoActual = item.estado_seccion_id || null;
                    if (!estadoActual && window.estadosOT) {
                        const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
                        estadoActual = estadoPendiente ? estadoPendiente.estadoOT_id : null;
                    }
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
                
                // Mostrar el contenedor de secciones
                if (seccionesPautaContainer) {
                    seccionesPautaContainer.style.display = 'block';
                    seccionesPautaContainer.classList.remove('hidden-section');
                    console.log('Secciones cargadas exitosamente, contenedor mostrado');
                } else {
                    console.error('No se encontró el contenedor de secciones para mostrar');
                }
            } else {
                console.log('No se encontraron items en la respuesta');
                // Ocultar contenedor si no hay items
                if (seccionesPautaContainer) {
                    seccionesPautaContainer.style.display = 'none';
                }
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

// Cargar departamentos y preseleccionar MAQUINARIAS
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
                deptoSelect.innerHTML = '';
                
                // Buscar y preseleccionar MAQUINARIAS
                let deptoMaquinariasId = null;
                data.departamentos.forEach(depto => {
                    const option = document.createElement('option');
                    option.value = depto.depto_id;
                    option.textContent = depto.depto;
                    deptoSelect.appendChild(option);
                    
                    // Buscar MAQUINARIAS (case insensitive)
                    if (depto.depto.toUpperCase() === 'MAQUINARIAS') {
                        deptoMaquinariasId = depto.depto_id;
                    }
                });
                
                // Preseleccionar MAQUINARIAS y deshabilitar el select
                if (deptoMaquinariasId) {
                    deptoSelect.value = deptoMaquinariasId;
                    deptoSelect.disabled = true;
                    deptoSelect.classList.add('bg-light');
                    
                    // Cargar cargos para MAQUINARIAS
                    cargarCargosPorDepto(deptoMaquinariasId);
                }
            }
        })
        .catch(error => {
            console.error('Error al cargar departamentos:', error);
        });
}

// Cargar cargos por departamento y preseleccionar MECÁNICO
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
                cargoSelect.innerHTML = '';
                
                // Buscar y preseleccionar MECÁNICO
                let cargoMecanicoId = null;
                data.cargos.forEach(cargo => {
                    const option = document.createElement('option');
                    option.value = cargo.cargo_id;
                    option.textContent = cargo.cargo;
                    cargoSelect.appendChild(option);
                    
                    // Buscar MECÁNICO (case insensitive)
                    if (cargo.cargo.toUpperCase() === 'MECÁNICO' || cargo.cargo.toUpperCase() === 'MECANICO') {
                        cargoMecanicoId = cargo.cargo_id;
                    }
                });
                
                // Preseleccionar MECÁNICO y deshabilitar el select
                if (cargoMecanicoId) {
                    cargoSelect.value = cargoMecanicoId;
                    cargoSelect.disabled = true;
                    cargoSelect.classList.add('bg-light');
                }
                
                // Cargar personal después de preseleccionar los filtros
                cargarPersonal();
            }
        })
        .catch(error => {
            console.error('Error al cargar cargos:', error);
        });
}

// Cargar personal con filtros
function cargarPersonal() {
    // Verificar si los elementos existen
    const searchElement = document.getElementById('personalSearch');
    const empresaFilter = document.getElementById('personalEmpresaFilter');
    const cargoFilter = document.getElementById('personalCargoFilter');
    const deptoFilter = document.getElementById('personalDeptoFilter');
    
    if (!searchElement || !empresaFilter || !cargoFilter || !deptoFilter) {
        // Los elementos no existen aún (puede pasar si se ejecuta antes de que el DOM esté listo)
        console.warn('Elementos de filtro de personal no encontrados');
        return;
    }
    
    const search = searchElement.value;
    const empresaId = empresaFilter.value;
    // El backend siempre filtra automáticamente por departamento MAQUINARIAS y cargo MECÁNICO
    // No es necesario enviar cargo_id ni depto_id
    
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (empresaId) params.append('empresa_id', empresaId);
    // El backend aplica automáticamente los filtros de MAQUINARIAS y MECÁNICO
    
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
    
    // Validar disponibilidad cuando cambia el personal
    if (!window.esEdicion) {
        validarDisponibilidad();
    }
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
        <span class="badge bg-primary" data-personal-id="${p.personal_id}">
            ${p.nombre_completo}
            <button type="button" class="btn-close btn-close-white ms-1"></button>
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
    
    // Obtener número de items actuales para numeración correcta
    const itemsActuales = container.querySelectorAll('.item-seccion').length;
    const nuevoIndice = itemsActuales + 1;
    
    // Clonar template
    const clone = template.content.cloneNode(true);
    const itemDiv = clone.querySelector('.item-seccion');
    
    // Asignar índice basado en la cantidad actual de items
    itemSeccionIndex = nuevoIndice;
    itemDiv.dataset.itemIndex = nuevoIndice;
    itemDiv.querySelector('.item-number').textContent = nuevoIndice;
    
    // Agregar al DOM primero
    container.appendChild(clone);
    
    // Obtener el item agregado del DOM
    const itemAgregado = container.querySelector(`[data-item-index="${nuevoIndice}"]`);
    if (!itemAgregado) return;
    
    // Preseleccionar estado "Pendiente" por defecto si no se proporciona uno inicial
    const estadoSelect = itemAgregado.querySelector('.estado-seccion-select');
    if (estadoSelect && window.estadosOT) {
        if (estadoInicial) {
            // Si se proporciona un estado inicial, usarlo
            estadoSelect.value = estadoInicial;
        } else {
            // Si no hay estado inicial, preseleccionar "Pendiente"
            const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
            if (estadoPendiente) {
                estadoSelect.value = estadoPendiente.estadoOT_id;
            }
        }
    }
    
    // Si es un item existente, pre-seleccionar sección DESPUÉS de agregar al DOM
    if (seccionIdInicial) {
        const seccionSelect = itemAgregado.querySelector('.seccion-select');
        seccionSelect.value = seccionIdInicial;
        
        // Cargar tipos de reparación y pre-seleccionar
        const tiposContainer = itemAgregado.querySelector('.tipos-reparacion-list');
        cargarTiposReparacionParaSeccion(seccionIdInicial, tiposContainer, tiposIdsIniciales);
    }
    
    // Actualizar disponibilidad de secciones en todos los selects
    actualizarSeccionesDisponibles();
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
    
    // Renumerar items después de eliminar
    renumerarItemsSecciones();
    
    // Si no quedan items, mostrar mensaje y reiniciar contador
    const container = document.getElementById('itemsSeccionesContainer');
    if (container.children.length === 0) {
        container.innerHTML = '<p class="text-muted small" id="noItemsMessage">No hay items agregados. Haga clic en "Agregar Item" para comenzar.</p>';
        itemSeccionIndex = 0; // Reiniciar contador cuando no hay items
    }
    
    // Actualizar disponibilidad de secciones después de eliminar
    actualizarSeccionesDisponibles();
}

// Renumerar items de secciones después de eliminar
function renumerarItemsSecciones() {
    const items = document.querySelectorAll('.item-seccion');
    items.forEach((item, index) => {
        const itemNumber = item.querySelector('.item-number');
        if (itemNumber) {
            itemNumber.textContent = index + 1;
        }
        item.dataset.itemIndex = index + 1;
    });
    // Actualizar el contador global al último número usado
    itemSeccionIndex = items.length;
}

// Actualizar estado de sección
function actualizarEstadoSeccion(selectElement) {
    // Solo actualizar visualmente, el valor se guarda en el submit
}

// Actualizar secciones disponibles en todos los selects (ocultar las ya seleccionadas)
function actualizarSeccionesDisponibles() {
    // Obtener todas las secciones ya seleccionadas
    const seccionesSeleccionadas = [];
    document.querySelectorAll('.seccion-select').forEach(select => {
        if (select.value) {
            seccionesSeleccionadas.push(select.value);
        }
    });
    
    // Actualizar cada select
    document.querySelectorAll('.seccion-select').forEach(select => {
        const valorActual = select.value;
        
        // Recorrer todas las opciones
        Array.from(select.options).forEach(option => {
            if (!option.value) return; // Ignorar opción vacía "Seleccione una sección"
            
            // Ocultar si está seleccionada en otro select (pero no en este)
            if (seccionesSeleccionadas.includes(option.value) && option.value !== valorActual) {
                option.style.display = 'none';
                option.disabled = true;
            } else {
                option.style.display = '';
                option.disabled = false;
            }
        });
    });
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
                                
                                // Después de cargar datos del equipo, sobrescribir con valores de la OT si existen
                                setTimeout(() => {
                                    if (data.horometro !== null && data.horometro !== undefined) {
                                        const horometroInput = document.getElementById('horometro');
                                        if (horometroInput) {
                                            horometroInput.value = data.horometro || '';
                                        }
                                    }
                                    
                                    if (data.odometro !== null && data.odometro !== undefined) {
                                        const odometroInput = document.getElementById('odometro');
                                        if (odometroInput) {
                                            odometroInput.value = data.odometro || '';
                                        }
                                    }
                                    
                                    if (data.horometro_superestructura !== null && data.horometro_superestructura !== undefined) {
                                        const horometroSuperInput = document.getElementById('horometro_superestructura');
                                        if (horometroSuperInput) {
                                            horometroSuperInput.value = data.horometro_superestructura || '';
                                        }
                                    }
                                }, 100);
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
    
    // Precargar fecha_fin si existe
    if (data.fecha_fin && typeof DatePickerChile !== 'undefined') {
        setTimeout(() => {
            DatePickerChile.setValor('fecha_fin_edicion', data.fecha_fin);
        }, 100);
    }
    
    // Precargar horómetros y odómetro si existen
    // En modo edición, precargar directamente ya que no existe el select de equipo
    // En modo creación, se precargan después de cargarDatosEquipo() (ver más arriba)
    setTimeout(() => {
        // Horómetro: puede ser número (incluyendo 0) o null/undefined
        if (data.horometro !== null && data.horometro !== undefined) {
            const horometroInput = document.getElementById('horometro');
            if (horometroInput) {
                horometroInput.value = data.horometro.toString();
            }
        }
        
        // Odómetro: puede ser número (incluyendo 0) o null/undefined
        if (data.odometro !== null && data.odometro !== undefined) {
            const odometroInput = document.getElementById('odometro');
            if (odometroInput) {
                odometroInput.value = data.odometro.toString();
            }
        }
        
        // Horómetro superestructura: puede ser número (incluyendo 0) o null/undefined
        if (data.horometro_superestructura !== null && data.horometro_superestructura !== undefined) {
            const horometroSuperInput = document.getElementById('horometro_superestructura');
            if (horometroSuperInput) {
                horometroSuperInput.value = data.horometro_superestructura.toString();
            }
        }
    }, 200);
    
    // Cargar personal seleccionado (también en modo edición)
    // Reducir timeout para mejorar la experiencia del usuario
    setTimeout(() => {
        if (data.personal_asignado) {
            personalSeleccionados = [...data.personal_asignado];
            const personalTableBody = document.getElementById('personalTableBody');
            if (personalTableBody) {
                cargarPersonal();
            }
        }
    }, 200);
    
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
// Función para validar que fecha_fin no sea antes de fecha_inicio
function validarFechaFin() {
    const fechaInicioInput = document.getElementById('fecha_inicio');
    const fechaFinInput = document.getElementById('fecha_fin');
    const fechaFinError = document.getElementById('fecha_fin_error');
    
    if (!fechaInicioInput || !fechaFinInput) return;
    
    let fechaInicio = null;
    let fechaFin = null;
    
    if (typeof DatePickerChile !== 'undefined') {
        fechaInicio = DatePickerChile.getValor('fecha_inicio');
        fechaFin = DatePickerChile.getValor('fecha_fin');
    } else {
        fechaInicio = fechaInicioInput.value || null;
        fechaFin = fechaFinInput.value || null;
    }
    
    if (fechaInicio && fechaFin) {
        const fechaInicioDate = new Date(fechaInicio);
        const fechaFinDate = new Date(fechaFin);
        
        if (fechaFinDate < fechaInicioDate) {
            fechaFinInput.classList.add('is-invalid');
            if (fechaFinError) {
                fechaFinError.textContent = 'La fecha de fin no puede ser anterior a la fecha de inicio';
            }
            return false;
        } else {
            fechaFinInput.classList.remove('is-invalid');
            if (fechaFinError) {
                fechaFinError.textContent = '';
            }
            return true;
        }
    }
    
    return true;
}

// Función para validar fecha fin en modo edición
function validarFechaFinEdicion() {
    const fechaFinInput = document.getElementById('fecha_fin_edicion');
    
    if (!fechaFinInput || !window.otData || !window.otData.fecha_inicio) return;
    
    let fechaFin = null;
    
    if (typeof DatePickerChile !== 'undefined') {
        fechaFin = DatePickerChile.getValor('fecha_fin_edicion');
    } else {
        fechaFin = fechaFinInput.value || null;
    }
    
    if (fechaFin) {
        const fechaInicio = new Date(window.otData.fecha_inicio);
        const fechaFinDate = new Date(fechaFin);
        
        if (fechaFinDate < fechaInicio) {
            fechaFinInput.classList.add('is-invalid');
            alert('La fecha de fin no puede ser anterior a la fecha de inicio');
            return false;
        } else {
            fechaFinInput.classList.remove('is-invalid');
            return true;
        }
    }
    
    return true;
}

// Función para validar disponibilidad de equipo y mecánico
async function validarDisponibilidad() {
    // Solo validar en modo creación
    if (window.esEdicion) return;
    
    const equipoSelect = document.getElementById('equipo_id');
    const fechaInicioInput = document.getElementById('fecha_inicio');
    const fechaFinInput = document.getElementById('fecha_fin');
    const validacionDiv = document.getElementById('validacionDisponibilidad');
    const alertDiv = document.getElementById('alertDisponibilidad');
    
    if (!equipoSelect || !fechaInicioInput || !validacionDiv || !alertDiv) return;
    
    const equipoId = equipoSelect.value;
    const personalIds = personalSeleccionados;
    
    let fechaInicio = null;
    let fechaFin = null;
    
    if (typeof DatePickerChile !== 'undefined') {
        fechaInicio = DatePickerChile.getValor('fecha_inicio');
        fechaFin = DatePickerChile.getValor('fecha_fin');
    } else {
        fechaInicio = fechaInicioInput.value || null;
        fechaFin = fechaFinInput.value || null;
    }
    
    // Si no hay fecha de inicio, no validar
    if (!fechaInicio) {
        validacionDiv.style.display = 'none';
        return;
    }
    
    // Convertir fecha al formato YYYY-MM-DD si es necesario
    if (fechaInicio && fechaInicio.includes('/')) {
        const parts = fechaInicio.split('/');
        fechaInicio = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    if (fechaFin && fechaFin.includes('/')) {
        const parts = fechaFin.split('/');
        fechaFin = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    
    // Si no hay equipo seleccionado, no validar
    if (!equipoId && personalIds.length === 0) {
        validacionDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(window.apiValidarDisponibilidad, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                equipo_id: equipoId || null,
                personal_ids: personalIds,
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const conflictos = data.conflictos;
            const conflictosEquipo = conflictos.equipo || [];
            const conflictosPersonal = conflictos.personal || [];
            
            // Limpiar clases de error
            if (equipoSelect) {
                equipoSelect.classList.remove('is-invalid');
            }
            
            // Mostrar mensajes de conflicto
            let mensajes = [];
            
            if (conflictosEquipo.length > 0) {
                equipoSelect.classList.add('is-invalid');
                const equipoError = document.getElementById('equipo_id_error');
                if (equipoError) {
                    equipoError.textContent = 'El equipo tiene conflictos de disponibilidad';
                }
                
                conflictosEquipo.forEach(conflicto => {
                    if (conflicto.tipo === 'faena') {
                        mensajes.push(`Equipo asignado a faena "${conflicto.faena}" del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                    } else if (conflicto.tipo === 'ot') {
                        mensajes.push(`Equipo asignado a OT ${conflicto.folio} del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                    }
                });
            } else {
                const equipoError = document.getElementById('equipo_id_error');
                if (equipoError) {
                    equipoError.textContent = '';
                }
            }
            
            // Agrupar conflictos de personal por personal_id
            const conflictosPorPersonal = {};
            conflictosPersonal.forEach(conflicto => {
                if (!conflictosPorPersonal[conflicto.personal_id]) {
                    conflictosPorPersonal[conflicto.personal_id] = [];
                }
                conflictosPorPersonal[conflicto.personal_id].push(conflicto);
            });
            
            Object.keys(conflictosPorPersonal).forEach(personalId => {
                const conflictos = conflictosPorPersonal[personalId];
                const personal = personalDisponible.find(p => p.personal_id == personalId);
                const nombrePersonal = personal ? `${personal.nombre} ${personal.apepat}` : `ID: ${personalId}`;
                
                conflictos.forEach(conflicto => {
                    if (conflicto.tipo === 'faena') {
                        mensajes.push(`Mecánico "${nombrePersonal}" asignado a faena "${conflicto.faena}" del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                    } else if (conflicto.tipo === 'ot') {
                        mensajes.push(`Mecánico "${nombrePersonal}" asignado a OT ${conflicto.folio} del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                    }
                });
            });
            
            if (mensajes.length > 0) {
                alertDiv.innerHTML = '<strong>Conflictos de disponibilidad detectados:</strong><ul class="mb-0 mt-2">' +
                    mensajes.map(msg => `<li>${msg}</li>`).join('') +
                    '</ul>';
                alertDiv.className = 'alert alert-warning';
                validacionDiv.style.display = 'block';
            } else {
                validacionDiv.style.display = 'none';
            }
        } else {
            console.error('Error al validar disponibilidad:', data.message);
        }
    } catch (error) {
        console.error('Error al validar disponibilidad:', error);
    }
}

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

async function guardarOrdenTrabajo(event) {
    event.preventDefault();
    
    // Si es edición, solo actualizar estados y fecha_fin
    if (window.esEdicion) {
        // Obtener fecha_fin usando DatePickerChile si está disponible
        let fechaFin = null;
        const fechaFinInput = document.getElementById('fecha_fin_edicion');
        if (fechaFinInput) {
            if (typeof DatePickerChile !== 'undefined') {
                fechaFin = DatePickerChile.getValor('fecha_fin_edicion');
            } else {
                // Fallback: buscar el input hidden real
                const hiddenInput = document.getElementById('fecha_fin_edicion');
                if (hiddenInput) {
                    fechaFin = hiddenInput.value || null;
                }
            }
        }
        
        // Validar fecha fin vs fecha inicio (si ambas están presentes)
        if (fechaFin && window.otData && window.otData.fecha_inicio) {
            const fechaInicio = new Date(window.otData.fecha_inicio);
            const fechaFinDate = new Date(fechaFin);
            if (fechaFinDate < fechaInicio) {
                alert('La fecha de fin no puede ser anterior a la fecha de inicio');
                return;
            }
        }
        
        const formData = {
            ot_id: document.getElementById('ot_id').value,
            estado_ot_id: document.getElementById('estado_ot_id').value,
            estado_equipo_id: document.getElementById('estado_equipo_id').value,
            fecha_fin: fechaFin,
            personal_asignado: personalSeleccionados  // Incluir personal asignado
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
    
    // Obtener fechas usando DatePickerChile si está disponible
    let fechaInicio = null;
    let fechaFin = null;
    
    if (typeof DatePickerChile !== 'undefined') {
        fechaInicio = DatePickerChile.getValor('fecha_inicio');
        fechaFin = DatePickerChile.getValor('fecha_fin');
    } else {
        // Fallback: buscar los inputs hidden reales
        const fechaInicioInput = document.getElementById('fecha_inicio');
        const fechaFinInput = document.getElementById('fecha_fin');
        if (fechaInicioInput) fechaInicio = fechaInicioInput.value || null;
        if (fechaFinInput) fechaFin = fechaFinInput.value || null;
    }
    
    // Validar que fecha_fin no sea antes de fecha_inicio
    if (fechaInicio && fechaFin) {
        const fechaInicioDate = new Date(fechaInicio);
        const fechaFinDate = new Date(fechaFin);
        if (fechaFinDate < fechaInicioDate) {
            alert('La fecha de fin no puede ser anterior a la fecha de inicio');
            return;
        }
    }
    
    // Validar disponibilidad antes de guardar
    if (equipoId && fechaInicio) {
        // Convertir fecha al formato YYYY-MM-DD si es necesario
        let fechaInicioFormato = fechaInicio;
        let fechaFinFormato = fechaFin;
        
        if (fechaInicio && fechaInicio.includes('/')) {
            const parts = fechaInicio.split('/');
            fechaInicioFormato = `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        if (fechaFin && fechaFin.includes('/')) {
            const parts = fechaFin.split('/');
            fechaFinFormato = `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        
        try {
            const response = await fetch(window.apiValidarDisponibilidad, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({
                    equipo_id: equipoId,
                    personal_ids: personalSeleccionados,
                    fecha_inicio: fechaInicioFormato,
                    fecha_fin: fechaFinFormato || null
                })
            });
            
            const data = await response.json();
            
            if (data.success && !data.disponible) {
                mostrarModalConflictos(data.conflictos);
                return;
            }
        } catch (error) {
            console.error('Error al validar disponibilidad:', error);
            // Continuar con el guardado si hay error en la validación
        }
    }
    
    // Recolectar datos del formulario
    const observacionesElement = document.getElementById('observaciones');
    const observacionesValue = observacionesElement ? observacionesElement.value.trim() : '';
    
    const formData = {
        ot_id: null,
        equipo_id: equipoId,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        tipo_mantenimiento_id: tipoMantenimientoId,
        estado_ot_id: estadoPendienteId,  // Siempre PENDIENTE en creación
        estado_equipo_id: document.getElementById('estado_equipo_id').value,
        observaciones: observacionesValue,
        personal_asignado: personalSeleccionados
    };
    
    console.log('Observaciones a guardar:', observacionesValue);
    
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
            mostrarNotificacion('Orden de trabajo guardada exitosamente', 'success');
            // Redirigir a la lista después de 1.5 segundos
            setTimeout(() => {
                window.location.replace('/maquinarias/ordenes-trabajo/');
            }, 1500);
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

// Función para mostrar modal de conflictos de disponibilidad
function mostrarModalConflictos(conflictos) {
    const contenidoDiv = document.getElementById('contenidoConflictos');
    if (!contenidoDiv) return;
    
    let html = '';
    
    // Conflictos de equipo
    if (conflictos.equipo && conflictos.equipo.length > 0) {
        html += '<div class="mb-4">';
        html += '<h6 class="text-danger mb-3"><i class="bi bi-tools me-2"></i><strong>EQUIPO:</strong></h6>';
        html += '<ul class="list-group">';
        conflictos.equipo.forEach(c => {
            if (c.tipo === 'faena') {
                html += `<li class="list-group-item">
                    <i class="bi bi-building me-2 text-warning"></i>
                    <strong>Asignado a faena:</strong> "${c.faena}"<br>
                    <small class="text-muted">Del ${c.fecha_inicio} al ${c.fecha_fin}</small>
                </li>`;
            } else if (c.tipo === 'ot') {
                html += `<li class="list-group-item">
                    <i class="bi bi-clipboard-check me-2 text-danger"></i>
                    <strong>Asignado a OT:</strong> ${c.folio}<br>
                    <small class="text-muted">Del ${c.fecha_inicio} al ${c.fecha_fin}</small>
                </li>`;
            }
        });
        html += '</ul></div>';
    }
    
    // Conflictos de personal
    if (conflictos.personal && conflictos.personal.length > 0) {
        html += '<div class="mb-4">';
        html += '<h6 class="text-danger mb-3"><i class="bi bi-people me-2"></i><strong>MECÁNICOS:</strong></h6>';
        html += '<ul class="list-group">';
        conflictos.personal.forEach(c => {
            const nombrePersonal = c.personal_nombre || `ID: ${c.personal_id}`;
            if (c.tipo === 'faena') {
                html += `<li class="list-group-item">
                    <i class="bi bi-building me-2 text-warning"></i>
                    <strong>${nombrePersonal}:</strong> Asignado a faena "${c.faena}"<br>
                    <small class="text-muted">Del ${c.fecha_inicio} al ${c.fecha_fin}</small>
                </li>`;
            } else if (c.tipo === 'ot') {
                html += `<li class="list-group-item">
                    <i class="bi bi-clipboard-check me-2 text-danger"></i>
                    <strong>${nombrePersonal}:</strong> Asignado a OT ${c.folio}<br>
                    <small class="text-muted">Del ${c.fecha_inicio} al ${c.fecha_fin}</small>
                </li>`;
            }
        });
        html += '</ul></div>';
    }
    
    contenidoDiv.innerHTML = html;
    
    // Mostrar el modal
    const modalElement = document.getElementById('modalConflictosDisponibilidad');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}
