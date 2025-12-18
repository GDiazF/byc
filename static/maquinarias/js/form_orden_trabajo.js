// Variables globales para el estado de la aplicación
// Estas variables mantienen el estado del formulario y los datos cargados
let itemSeccionIndex = 0;  // Contador para índices únicos de items de sección
let equiposDisponibles = [];  // Lista de equipos disponibles según filtros
let personalDisponible = [];  // Lista de personal disponible para asignar
let personalSeleccionados = [];  // Lista de IDs de personal seleccionado
let modeloEquipoSeleccionado = null;  // ID del modelo de equipo seleccionado
let cargosDisponibles = [];  // Lista de cargos disponibles (para filtros)
let departamentosDisponibles = [];  // Lista de departamentos disponibles (para filtros)

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Configurar el event listener para el envío del formulario
    // Cuando el usuario envía el formulario, se ejecutará la función guardarOrdenTrabajo
    const form = document.getElementById('formOrdenTrabajo');
    
    if (form) {
        form.addEventListener('submit', guardarOrdenTrabajo);
    }
    
    // Paso 2: Cargar datos iniciales necesarios para el formulario
    // Estos datos se cargan al iniciar para tenerlos disponibles inmediatamente
    cargarDepartamentos();  // Cargar departamentos para filtros de personal
    cargarPersonal();  // Cargar personal disponible para asignar
    
    // Paso 3: Configurar event listeners para filtros en cascada de equipos
    // Estos listeners reaccionan a cambios en los selects y actualizan los filtros dependientes
    const empresaSelect = document.getElementById('empresa_id');
    if (empresaSelect) {
        empresaSelect.addEventListener('change', function() {
            // Cuando cambia la empresa, limpiar la pauta de mantenimiento seleccionada
            limpiarPautaMantenimiento();
            // Reiniciar todos los filtros en cascada: tipo, marca, modelo y equipo
            // Esto asegura que los filtros sean consistentes con la empresa seleccionada
            reiniciarFiltrosDesdeTipo();
            filtrarEquipos();  // Filtrar equipos según la nueva empresa
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
    
    // Event listener para select de pauta (modo creación)
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
    
    // Event listener para select de pauta en modo edición
    const pautaSelectEdicion = document.getElementById('pauta_id_edicion');
    if (pautaSelectEdicion) {
        pautaSelectEdicion.addEventListener('change', function(e) {
            const pautaId = e.target.value;
            if (pautaId) {
                console.log('Pauta seleccionada en edición:', pautaId);
                cargarSeccionesPauta(pautaId);
            } else {
                // Si no hay pauta seleccionada, ocultar secciones
                const seccionesPautaContainer = document.getElementById('seccionesPautaContainer');
                if (seccionesPautaContainer) {
                    seccionesPautaContainer.style.display = 'none';
                    seccionesPautaContainer.classList.add('hidden-section');
                }
            }
        });
    }
    
    // Event listener para botón agregar item sección (solo en modo creación)
    const btnAgregarItemSeccion = document.getElementById('btnAgregarItemSeccion');
    if (btnAgregarItemSeccion) {
        // Ocultar botón en modo edición
        if (window.esEdicion) {
            btnAgregarItemSeccion.style.display = 'none';
        } else {
            btnAgregarItemSeccion.addEventListener('click', agregarItemSeccion);
        }
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

// Función debounce para optimizar búsquedas y filtros
// Esta función retrasa la ejecución de una función hasta que haya pasado un tiempo determinado
// sin nuevas llamadas. Útil para evitar ejecutar funciones costosas en cada tecla presionada.
// Parámetros:
//   func: función a ejecutar después del delay
//   wait: tiempo de espera en milisegundos
function debounce(func, wait) {
    let timeout;  // Variable para almacenar el ID del timeout
    return function executedFunction(...args) {
        // Función que se ejecuta cuando se llama a debounce
        const later = () => {
            clearTimeout(timeout);  // Limpiar timeout anterior si existe
            func(...args);  // Ejecutar la función original con los argumentos
        };
        clearTimeout(timeout);  // Cancelar timeout anterior si existe
        timeout = setTimeout(later, wait);  // Crear nuevo timeout
    };
}

// ============================================================================
// FILTROS EN CASCADA DE EQUIPOS (Tipo -> Marca -> Modelo -> Equipo)
// ============================================================================

// Función para reiniciar todos los filtros en cascada desde el tipo de equipo
// Esta función limpia los valores de tipo, marca, modelo y equipo cuando cambia la empresa
// o cuando se necesita resetear los filtros. Mantiene la consistencia de los filtros.
function reiniciarFiltrosDesdeTipo() {
    // Paso 1: Obtener referencias a todos los selects del filtro en cascada
    const tipoSelect = document.getElementById('tipo_equipo_id');  // Select de tipo de equipo
    const marcaSelect = document.getElementById('marca_equipo_id');  // Select de marca
    const modeloSelect = document.getElementById('modelo_equipo_id');  // Select de modelo
    const equipoSelect = document.getElementById('equipo_id');  // Select de equipo
    
    // Paso 2: Limpiar el valor del select de tipo
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

// Función para filtrar los modelos disponibles según el tipo y marca seleccionados
// Implementa el segundo nivel del filtro en cascada: Tipo -> Marca -> Modelo -> Equipo
// Esta función se ejecuta cuando el usuario selecciona una marca después de haber seleccionado un tipo
function filtrarModelosPorTipoYMarca() {
    // Paso 1: Obtener referencias a los elementos select y sus valores seleccionados
    const tipoId = parseInt(document.getElementById('tipo_equipo_id').value);  // ID del tipo seleccionado
    const marcaId = parseInt(document.getElementById('marca_equipo_id').value);  // ID de la marca seleccionada
    const modeloSelect = document.getElementById('modelo_equipo_id');  // Select de modelo
    const equipoSelect = document.getElementById('equipo_id');  // Select de equipo
    
    // Paso 2: Resetear el select de modelo y equipo
    // Limpiar las opciones y deshabilitar hasta que se seleccione un modelo válido
    modeloSelect.innerHTML = '<option value="">Todos</option>';  // Opción por defecto
    modeloSelect.disabled = !tipoId || !marcaId;  // Deshabilitar si falta tipo o marca
    
    equipoSelect.innerHTML = '<option value="">Primero seleccione modelo...</option>';  // Mensaje instructivo
    equipoSelect.disabled = true;  // Deshabilitar hasta que se seleccione un modelo
    
    // Paso 3: Validar que tanto tipo como marca estén seleccionados
    // Si falta alguno, filtrar equipos sin restricciones y salir
    if (!tipoId || !marcaId) {
        filtrarEquipos();  // Filtrar equipos sin restricciones
        return;  // Salir de la función
    }
    
    // Paso 4: Filtrar modelos que pertenecen tanto al tipo como a la marca seleccionados
    // Se usa filter() para obtener solo los modelos que cumplen ambas condiciones
    const modelosFiltrados = window.todosModelos.filter(m => 
        m.tipoEquipo_id === tipoId && m.marcaEquipo_id === marcaId  // Debe coincidir tipo Y marca
    );
    
    // Paso 5: Poblar el select de modelos con las opciones filtradas
    modelosFiltrados.forEach(modelo => {
        const option = document.createElement('option');  // Crear elemento option
        option.value = modelo.modeloEquipo_id;  // Valor del option (ID del modelo)
        option.textContent = modelo.modeloEquipo;  // Texto visible (nombre del modelo)
        modeloSelect.appendChild(option);  // Agregar al select
    });
    
    // Paso 6: Filtrar equipos con los nuevos filtros de tipo y marca aplicados
    // Esto actualiza la lista de equipos disponibles según las selecciones
    filtrarEquipos();
}

// Función para filtrar equipos según los filtros seleccionados (empresa, tipo, marca, modelo)
// Esta función realiza una petición AJAX al servidor para obtener equipos filtrados
// Se ejecuta cuando cambian cualquiera de los filtros en cascada
function filtrarEquipos() {
    // Paso 1: Obtener valores de los filtros desde los selects del formulario
    // Estos valores se enviarán al servidor para filtrar los equipos
    const empresaId = document.getElementById('empresa_id').value;  // ID de empresa seleccionada
    const tipoId = document.getElementById('tipo_equipo_id').value;  // ID de tipo seleccionado
    const marcaId = document.getElementById('marca_equipo_id').value;  // ID de marca seleccionada
    const modeloId = document.getElementById('modelo_equipo_id').value;  // ID de modelo seleccionado
    const equipoSelect = document.getElementById('equipo_id');  // Select de equipo a poblar
    
    // Paso 2: Construir parámetros de la petición
    // Solo se incluyen los filtros que tienen un valor seleccionado
    const params = new URLSearchParams();
    if (empresaId) params.append('empresa_id', empresaId);  // Agregar filtro de empresa si existe
    if (tipoId) params.append('tipo_equipo_id', tipoId);  // Agregar filtro de tipo si existe
    if (marcaId) params.append('marca_equipo_id', marcaId);  // Agregar filtro de marca si existe
    if (modeloId) params.append('modelo_equipo_id', modeloId);  // Agregar filtro de modelo si existe
    
    // Paso 3: Mostrar estado de carga mientras se obtienen los equipos
    // Deshabilitar el select y mostrar mensaje de carga
    equipoSelect.disabled = true;  // Deshabilitar para evitar selecciones durante la carga
    equipoSelect.innerHTML = '<option value="">Cargando equipos...</option>';  // Mensaje de carga
    
    // Paso 4: Realizar petición GET al servidor para obtener equipos filtrados
    // window.apiEquiposFiltrados contiene la URL del endpoint definida en el template
    fetch(`${window.apiEquiposFiltrados}?${params}`)
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // CASO ÉXITO: Los equipos se cargaron correctamente
                // Paso 5.1: Guardar los equipos en la variable global
                // Esto permite acceder a los datos sin hacer más peticiones
                equiposDisponibles = data.equipos;
                
                // Paso 5.2: Renderizar los equipos en el select
                // Esto actualiza las opciones disponibles para el usuario
                renderizarEquipos(data.equipos);
            } else {
                // CASO ERROR: El servidor retornó un error
                // Paso 6.1: Mostrar mensaje de error al usuario
                mostrarError('Error al cargar equipos: ' + data.message);
                
                // Paso 6.2: Mostrar mensaje de error en el select
                equipoSelect.innerHTML = '<option value="">Error al cargar</option>';
            }
        })
        .catch(error => {
            // CASO EXCEPCIÓN: Error de red o excepción no manejada
            // Paso 7.1: Registrar error en consola para debugging
            console.error('Error:', error);
            
            // Paso 7.2: Mostrar mensaje genérico de error al usuario
            mostrarError('Error de conexión al cargar equipos');
            
            // Paso 7.3: Mostrar mensaje de error en el select
            equipoSelect.innerHTML = '<option value="">Error de conexión</option>';
        });
}

// Función para renderizar los equipos filtrados en el select de equipos
// Pobla el select con las opciones de equipos disponibles según los filtros aplicados
// Parámetros:
//   equipos: Array de objetos con información de equipos recibidos del servidor
function renderizarEquipos(equipos) {
    // Paso 1: Obtener referencia al select de equipos
    const equipoSelect = document.getElementById('equipo_id');
    
    // Paso 2: Limpiar el select y agregar opción por defecto
    equipoSelect.innerHTML = '<option value="">Seleccione equipo...</option>';
    
    // Paso 3: Manejar caso cuando no hay equipos disponibles
    // Mostrar mensaje informativo y deshabilitar el select
    if (equipos.length === 0) {
        equipoSelect.innerHTML = '<option value="">No hay equipos disponibles</option>';
        equipoSelect.disabled = true;  // Deshabilitar porque no hay opciones
        return;  // Salir de la función
    }
    
    // Paso 4: Generar opciones para cada equipo disponible
    // Se crea una opción por cada equipo con su información completa
    equipos.forEach(equipo => {
        const option = document.createElement('option');  // Crear elemento option
        option.value = equipo.equipo_id;  // Valor del option (ID del equipo)
        option.textContent = `${equipo.nombreEquipo} - ${equipo.codigoInterno}`;  // Texto visible (nombre y código)
        
        // Paso 4.1: Guardar datos adicionales del equipo en atributos data
        // Estos datos se usan para precargar información cuando se selecciona el equipo
        option.dataset.horometro = equipo.horometro || '';  // Horas de uso del equipo
        option.dataset.odometro = equipo.odometro || '';  // Kilómetros recorridos
        option.dataset.horometroSuperEstructural = equipo.horometroSuperEstructural || '';  // Horas de superestructura
        option.dataset.modeloId = equipo.modeloEquipo_id || '';  // ID del modelo (para cargar pautas)
        
        equipoSelect.appendChild(option);  // Agregar la opción al select
    });
    
    // Paso 5: Habilitar el select ahora que tiene opciones disponibles
    equipoSelect.disabled = false;
}

// Función para cargar los datos del equipo seleccionado en los campos del formulario
// Se ejecuta cuando el usuario selecciona un equipo del select
// Precarga información como horómetros, odómetros y modelo del equipo
function cargarDatosEquipo() {
    // Paso 1: Obtener referencia al select de equipos y el equipo seleccionado
    const equipoSelect = document.getElementById('equipo_id');
    const equipoId = equipoSelect.value;  // ID del equipo seleccionado
    
    // Paso 2: Si no hay equipo seleccionado, limpiar todos los campos relacionados
    // Esto ocurre cuando el usuario deselecciona el equipo o selecciona la opción vacía
    if (!equipoId) {
        // Limpiar campos de horómetros y odómetros
        document.getElementById('horometro').value = '';
        document.getElementById('odometro').value = '';
        document.getElementById('horometro_superestructura').value = '';
        modeloEquipoSeleccionado = null;  // Limpiar referencia al modelo
        
        // Limpiar pauta seleccionada y ocultar secciones de mantenimiento preventivo
        limpiarPautaMantenimiento();
        
        // Resetear el select de pautas con mensaje instructivo
        const pautaSelect = document.getElementById('pauta_id');
        if (pautaSelect) {
            pautaSelect.innerHTML = '<option value="">Primero seleccione un equipo...</option>';
        }
        
        return;  // Salir de la función
    }
    
    // Paso 3: Obtener la opción seleccionada del select
    // Esta opción contiene los datos del equipo guardados en atributos data
    const option = equipoSelect.options[equipoSelect.selectedIndex];
    
    // Paso 4: Precargar los valores de horómetros y odómetros en los campos del formulario
    // Estos valores se obtienen de los atributos data de la opción seleccionada
    document.getElementById('horometro').value = option.dataset.horometro || '';  // Horas de uso
    document.getElementById('odometro').value = option.dataset.odometro || '';  // Kilómetros recorridos
    document.getElementById('horometro_superestructura').value = option.dataset.horometroSuperEstructural || '';  // Horas de superestructura
    
    // Paso 5: Actualizar el modelo de equipo seleccionado
    // Se guarda el modelo anterior para detectar cambios y cargar pautas si es necesario
    const modeloAnterior = modeloEquipoSeleccionado;  // Guardar modelo anterior
    modeloEquipoSeleccionado = option.dataset.modeloId;  // Actualizar con el nuevo modelo
    
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

// Función para limpiar la pauta de mantenimiento preventivo seleccionada
// Se ejecuta cuando cambia el equipo, modelo o cuando se deselecciona la pauta
// Limpia el valor seleccionado y oculta las secciones de la pauta cargadas
function limpiarPautaMantenimiento() {
    // Paso 1: Limpiar el valor seleccionado del select de pautas
    // No se eliminan las opciones, solo se resetea la selección
    const pautaSelect = document.getElementById('pauta_id');
    if (pautaSelect) {
        pautaSelect.value = '';  // Deseleccionar cualquier pauta seleccionada
        // No limpiar las opciones, solo el valor seleccionado (las opciones se mantienen para reutilización)
    }
    
    // Paso 2: Ocultar el contenedor de secciones de la pauta cargada
    // Esto oculta las secciones y tipos de reparación que se habían cargado desde la pauta
    const seccionesPautaContainer = document.querySelector('#seccionPreventivo #seccionesPautaContainer') || 
                                     document.getElementById('seccionesPautaContainer');
    if (seccionesPautaContainer) {
        seccionesPautaContainer.style.display = 'none';  // Ocultar visualmente
        seccionesPautaContainer.classList.add('hidden-section');  // Agregar clase CSS para ocultar
        
        // Paso 2.1: Limpiar el contenido de la lista de secciones
        // Esto elimina las secciones renderizadas para que no queden datos obsoletos
        const seccionesPautaList = document.querySelector('#seccionPreventivo #seccionesPautaList') || 
                                    document.getElementById('seccionesPautaList');
        if (seccionesPautaList) {
            seccionesPautaList.innerHTML = '';  // Limpiar HTML de las secciones
        }
    }
}

// Función que se ejecuta cuando cambia el tipo de mantenimiento seleccionado
// Muestra u oculta las secciones del formulario según el tipo de mantenimiento
// Los tipos pueden ser: Preventivo (usa pautas), Correctivo (usa items de secciones), u otros
function cambiarTipoMantenimiento() {
    // Paso 1: Obtener referencias a los elementos del formulario
    const tipoMantenimientoId = document.getElementById('tipo_mantenimiento_id').value;  // ID del tipo seleccionado
    const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');  // Select de tipo de mantenimiento
    const seccionPreventivo = document.getElementById('seccionPreventivo');  // Contenedor de sección preventiva
    const seccionReparaciones = document.getElementById('seccionReparaciones');  // Contenedor de sección de reparaciones
    
    // Paso 2: Obtener el nombre del tipo seleccionado (en minúsculas para comparación)
    // Se usa el texto visible de la opción seleccionada para determinar el tipo
    const tipoNombre = tipoMantenimientoSelect.options[tipoMantenimientoSelect.selectedIndex]?.textContent?.toLowerCase() || '';
    
    // Paso 3: Mostrar/ocultar secciones según el tipo de mantenimiento seleccionado
    if (tipoNombre.includes('preventivo')) {
        // CASO: Mantenimiento Preventivo
        // Paso 3.1: Mostrar la sección de mantenimiento preventivo
        seccionPreventivo.style.display = 'block';
        
        // Paso 3.2: Limpiar la selección de radio buttons de corresponde_pauta
        // Esto resetea el estado para que el usuario seleccione nuevamente
        document.getElementById('corresponde_pauta_si').checked = false;
        document.getElementById('corresponde_pauta_no').checked = false;
        
        // Paso 3.3: Ejecutar la función que maneja el cambio de corresponde_pauta
        // Esto oculta/muestra los campos relacionados según la nueva selección
        cambiarCorrespondePauta();
        
    } else if (tipoNombre.includes('correctivo')) {
        // CASO: Mantenimiento Correctivo
        // Paso 3.4: Ocultar sección preventiva y mostrar sección de reparaciones
        seccionPreventivo.style.display = 'none';
        seccionReparaciones.style.display = 'block';
        
        // Paso 3.5: Limpiar items de secciones si había algo de preventivo
        // Resetear el contenedor de items y el índice para comenzar desde cero
        document.getElementById('itemsSeccionesContainer').innerHTML = '<p class="text-muted small" id="noItemsMessage">No hay items agregados. Haga clic en "Agregar Item" para comenzar.</p>';
        itemSeccionIndex = 0;  // Resetear contador de items
        
    } else {
        // CASO: Otro tipo de mantenimiento o ninguno seleccionado
        // Paso 3.6: Ocultar ambas secciones si no es preventivo ni correctivo
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
function cargarPautasPorModelo(modeloId, selectElement = null) {
    const pautaSelect = selectElement || document.getElementById('pauta_id');
    
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
    
    // Si aún no tenemos pautaId, intentar obtenerlo del select (creación o edición)
    if (!pautaId) {
        const pautaSelect = document.getElementById('pauta_id');
        const pautaSelectEdicion = document.getElementById('pauta_id_edicion');
        pautaId = pautaSelect?.value || pautaSelectEdicion?.value;
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

// Agregar item de sección (solo permitido en creación, NO en edición)
function agregarItemSeccion(seccionIdInicial = null, tiposIdsIniciales = [], estadoInicial = null) {
    // En modo edición, solo permitir cargar secciones existentes, NO agregar nuevas
    if (window.esEdicion && !seccionIdInicial) {
        // No mostrar alert, simplemente retornar sin hacer nada
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
        // Establecer data-seccion-id en el select de estado para poder recolectarlo después
        if (seccionIdInicial) {
            estadoSelect.dataset.seccionId = seccionIdInicial;
        }
        
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
        
        // En modo edición, deshabilitar select de sección y checkboxes (solo se puede cambiar el estado)
        if (window.esEdicion) {
            seccionSelect.disabled = true;
            seccionSelect.classList.add('bg-light');
            
            // Ocultar botón eliminar
            const btnEliminar = itemAgregado.querySelector('.btnEliminarItemSeccion');
            if (btnEliminar) {
                btnEliminar.style.display = 'none';
            }
        }
        
        console.log('Agregando item con sección inicial:', {
            seccionIdInicial: seccionIdInicial,
            tiposIdsIniciales: tiposIdsIniciales,
            estadoInicial: estadoInicial,
            esEdicion: window.esEdicion
        });
        
        // Cargar tipos de reparación y pre-seleccionar
        const tiposContainer = itemAgregado.querySelector('.tipos-reparacion-list');
        cargarTiposReparacionParaSeccion(seccionIdInicial, tiposContainer, tiposIdsIniciales);
        
        // En modo edición, deshabilitar checkboxes después de cargarlos
        if (window.esEdicion) {
            setTimeout(() => {
                const checkboxes = tiposContainer.querySelectorAll('.tipo-reparacion-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.disabled = true;
                    checkbox.parentElement.classList.add('text-muted');
                });
            }, 100);
        }
        
        // Verificar después de un pequeño delay que los checkboxes se marcaron correctamente
        setTimeout(() => {
            const checkboxesMarcados = tiposContainer.querySelectorAll('.tipo-reparacion-checkbox:checked');
            console.log(`Verificación post-carga para sección ${seccionIdInicial}:`, {
                checkboxesEsperados: tiposIdsIniciales.length,
                checkboxesMarcados: checkboxesMarcados.length,
                tiposIdsIniciales: tiposIdsIniciales
            });
            
            if (checkboxesMarcados.length !== tiposIdsIniciales.length) {
                console.error('ERROR: No todos los checkboxes se marcaron correctamente', {
                    esperados: tiposIdsIniciales,
                    marcados: Array.from(checkboxesMarcados).map(cb => parseInt(cb.value))
                });
            }
        }, 200);
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
    
    // Convertir todos los IDs a números para comparación correcta
    const tiposIdsPreseleccionadosNumeros = tiposIdsPreseleccionados.map(id => parseInt(id));
    
    console.log('Cargando tipos de reparación para sección:', {
        seccionId: seccionId,
        tiposIdsPreseleccionados: tiposIdsPreseleccionados,
        tiposIdsPreseleccionadosNumeros: tiposIdsPreseleccionadosNumeros,
        tiposFiltrados: tiposFiltrados.length
    });
    
    container.innerHTML = '<div class="row g-2">' + tiposFiltrados.map(tipo => {
        // Comparar como números para evitar problemas de tipo
        const tipoIdNumero = parseInt(tipo.tipoReparacion_id);
        const checked = tiposIdsPreseleccionadosNumeros.includes(tipoIdNumero) ? 'checked' : '';
        
        if (checked) {
            console.log(`Marcando checkbox para tipo: ${tipo.nombre} (ID: ${tipoIdNumero})`);
        }
        
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
    
    // Verificar que los checkboxes se marcaron correctamente
    setTimeout(() => {
        const checkboxesMarcados = container.querySelectorAll('.tipo-reparacion-checkbox:checked');
        console.log(`Checkboxes marcados después de cargar: ${checkboxesMarcados.length} de ${tiposFiltrados.length}`);
        if (checkboxesMarcados.length !== tiposIdsPreseleccionadosNumeros.length) {
            console.warn('ADVERTENCIA: No todos los checkboxes se marcaron correctamente', {
                esperados: tiposIdsPreseleccionadosNumeros.length,
                marcados: checkboxesMarcados.length
            });
        }
    }, 100);
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
            // También cargar pautas disponibles en el select de edición
            const pautaSelectEdicion = document.getElementById('pauta_id_edicion');
            if (pautaSelectEdicion && data.modelo_id) {
                // Cargar pautas disponibles para el modelo
                cargarPautasPorModelo(data.modelo_id, pautaSelectEdicion);
                // Preseleccionar la pauta actual después de cargar
                setTimeout(() => {
                    pautaSelectEdicion.value = data.pauta_id;
                }, 500);
            }
            cargarSeccionesPauta(data.pauta_id);
        } else if (data.items_secciones && data.items_secciones.length > 0) {
            // Cargar items de secciones manuales usando el template para permitir edición
            const container = document.getElementById('itemsSeccionesContainer');
            const noItemsMessage = document.getElementById('noItemsMessage');
            if (container) {
                container.innerHTML = '';
                if (noItemsMessage) {
                    noItemsMessage.style.display = 'none';
                }
                
                console.log('Cargando secciones existentes en modo edición:', data.items_secciones.length);
                
                data.items_secciones.forEach((item, index) => {
                    // Obtener el nombre de la sección desde window.secciones
                    const seccion = window.secciones.find(s => s.seccion_id === item.seccion_id);
                    const seccionNombre = seccion ? seccion.nombre : `Sección ID: ${item.seccion_id}`;
                    
                    // Obtener los nombres de los tipos de reparación desde window.tiposReparacion
                    const tiposReparacionNombres = [];
                    if (item.tipos_reparacion_ids && Array.isArray(item.tipos_reparacion_ids)) {
                        item.tipos_reparacion_ids.forEach(tipoId => {
                            const tipo = window.tiposReparacion.find(t => t.tipoReparacion_id === tipoId);
                            if (tipo) {
                                tiposReparacionNombres.push(tipo.nombre);
                            }
                        });
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
    const equipoSelect = document.getElementById('equipo_id');
    const validacionDiv = document.getElementById('validacionDisponibilidad');
    const alertDiv = document.getElementById('alertDisponibilidad');
    
    if (!validacionDiv || !alertDiv) return;
    
    let equipoId = null;
    let fechaInicio = null;
    let fechaFin = null;
    let otId = null;
    
    if (window.esEdicion) {
        // Modo edición: usar datos de la OT actual
        otId = document.getElementById('ot_id')?.value || null;
        if (window.otData) {
            equipoId = window.otData.equipo_id || null;
            fechaInicio = window.otData.fecha_inicio || null;
            
            // Obtener fecha_fin del formulario de edición
            const fechaFinInput = document.getElementById('fecha_fin_edicion');
            if (fechaFinInput) {
                if (typeof DatePickerChile !== 'undefined') {
                    fechaFin = DatePickerChile.getValor('fecha_fin_edicion');
                } else {
                    fechaFin = fechaFinInput.value || null;
                }
            }
        }
    } else {
        // Modo creación: usar datos del formulario
        if (!equipoSelect) return;
        
        const fechaInicioInput = document.getElementById('fecha_inicio');
        const fechaFinInput = document.getElementById('fecha_fin');
        
        equipoId = equipoSelect.value;
        
        if (typeof DatePickerChile !== 'undefined') {
            fechaInicio = DatePickerChile.getValor('fecha_inicio');
            fechaFin = DatePickerChile.getValor('fecha_fin');
        } else {
            if (fechaInicioInput) fechaInicio = fechaInicioInput.value || null;
            if (fechaFinInput) fechaFin = fechaFinInput.value || null;
        }
    }
    
    const personalIds = personalSeleccionados || [];
    
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
    
    // Si no hay equipo ni personal seleccionado, no validar
    if (!equipoId && personalIds.length === 0) {
        validacionDiv.style.display = 'none';
        return;
    }
    
    try {
        const requestBody = {
            equipo_id: equipoId || null,
            personal_ids: personalIds,
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin || null
        };
        
        // En modo edición, incluir ot_id para excluir la OT actual de la validación
        if (otId) {
            requestBody.ot_id = otId;
        }
        
        const response = await fetch(window.apiValidarDisponibilidad, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(requestBody)
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
                const seccionId = parseInt(select.dataset.seccionId);
                const estadoSeccionId = parseInt(select.value);
                console.log('Recolectando estado de sección:', {
                    seccion_id: seccionId,
                    estado_seccion_id: estadoSeccionId,
                    data_seccion_id: select.dataset.seccionId,
                    select_value: select.value
                });
                estadosSecciones.push({
                    seccion_id: seccionId,
                    estado_seccion_id: estadoSeccionId
                });
            } else {
                console.warn('Select de estado sin seccion_id o value:', {
                    hasValue: !!select.value,
                    hasSeccionId: !!select.dataset.seccionId,
                    seccionId: select.dataset.seccionId,
                    value: select.value
                });
            }
        });
        
        console.log('Estados de secciones recolectados:', estadosSecciones);
        
        formData.estados_pauta = estadosPauta;
        formData.estados_secciones = estadosSecciones;
        
        // En modo edición, verificar si se cambió la pauta
        const pautaSelectEdicion = document.getElementById('pauta_id_edicion');
        if (pautaSelectEdicion && pautaSelectEdicion.value) {
            formData.pauta_id = pautaSelectEdicion.value;
            formData.corresponde_pauta = true;
        }
        
        // En modo edición, NO enviar items_secciones (solo se pueden cambiar estados, no agregar/modificar/eliminar secciones)
        // Los cambios de estado se manejan a través de estados_secciones
        if (window.esEdicion) {
            // NO recolectar items_secciones en modo edición
            // Solo se procesan cambios de estado a través de estados_secciones
            // No incluir items_secciones en formData para que el backend no procese cambios en secciones
            console.log('Modo edición: No se enviarán items_secciones. Solo se procesarán cambios de estado.');
        } else if (!window.esEdicion) {
            // En modo creación, recolectar según el tipo de mantenimiento
            const correspondePautaSi = document.getElementById('corresponde_pauta_si');
            const esPauta = correspondePautaSi && correspondePautaSi.checked;
            const tipoMantenimientoSelect = document.getElementById('tipo_mantenimiento_id');
            const tipoMantenimientoNombre = tipoMantenimientoSelect ? tipoMantenimientoSelect.options[tipoMantenimientoSelect.selectedIndex]?.textContent?.toLowerCase() || '' : '';
            const esPreventivo = tipoMantenimientoNombre.includes('preventivo');
            
            // Si NO es pauta (preventivo sin pauta o correctivo), recolectar items_secciones
            if ((!esPauta && esPreventivo) || tipoMantenimientoNombre.includes('correctivo')) {
                formData.items_secciones = recolectarItemsSecciones();
            }
        }
        
        // Validar disponibilidad antes de guardar en modo edición
        if (window.otData && window.otData.equipo_id && window.otData.fecha_inicio) {
            const equipoId = window.otData.equipo_id;
            const fechaInicio = window.otData.fecha_inicio;
            const fechaFinValidacion = fechaFin || null;
            const otId = document.getElementById('ot_id').value;
            
            // Convertir fecha al formato YYYY-MM-DD si es necesario
            let fechaInicioFormato = fechaInicio;
            let fechaFinFormato = fechaFinValidacion;
            
            if (fechaInicio && fechaInicio.includes('/')) {
                const parts = fechaInicio.split('/');
                fechaInicioFormato = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            if (fechaFinValidacion && fechaFinValidacion.includes('/')) {
                const parts = fechaFinValidacion.split('/');
                fechaFinFormato = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            
            try {
                const validacionResponse = await fetch(window.apiValidarDisponibilidad, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.csrfToken
                    },
                    body: JSON.stringify({
                        equipo_id: equipoId,
                        personal_ids: personalSeleccionados || [],
                        fecha_inicio: fechaInicioFormato,
                        fecha_fin: fechaFinFormato || null,
                        ot_id: otId
                    })
                });
                
                const validacionData = await validacionResponse.json();
                
                if (validacionData.success && !validacionData.disponible) {
                    // Hay conflictos de disponibilidad
                    const conflictos = validacionData.conflictos || {};
                    const conflictosEquipo = conflictos.equipo || [];
                    const conflictosPersonal = conflictos.personal || [];
                    
                    let mensajes = [];
                    
                    if (conflictosEquipo.length > 0) {
                        conflictosEquipo.forEach(conflicto => {
                            if (conflicto.tipo === 'faena') {
                                mensajes.push(`El equipo está asignado a faena "${conflicto.faena}" del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                            } else if (conflicto.tipo === 'ot') {
                                mensajes.push(`El equipo está asignado a OT ${conflicto.folio} del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                            }
                        });
                    }
                    
                    if (conflictosPersonal.length > 0) {
                        conflictosPersonal.forEach(conflicto => {
                            const nombrePersonal = conflicto.personal_nombre || `ID: ${conflicto.personal_id}`;
                            if (conflicto.tipo === 'faena') {
                                mensajes.push(`El mecánico "${nombrePersonal}" está asignado a faena "${conflicto.faena}" del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                            } else if (conflicto.tipo === 'ot') {
                                mensajes.push(`El mecánico "${nombrePersonal}" está asignado a OT ${conflicto.folio} del ${conflicto.fecha_inicio} al ${conflicto.fecha_fin}`);
                            }
                        });
                    }
                    
                    if (mensajes.length > 0) {
                        // Usar el mismo modal que en creación
                        mostrarModalConflictos(validacionData.conflictos);
                        return; // Detener el guardado
                    }
                }
            } catch (error) {
                console.error('Error al validar disponibilidad:', error);
                // Continuar con el guardado si hay error en la validación
            }
        }
        
        // Enviar solo actualización de estados
        fetch(window.apiGuardarOT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            // Verificar si la respuesta es un error HTTP
            if (!response.ok) {
                // Si es un error 400, intentar parsear el JSON para obtener los conflictos
                return response.json().then(data => {
                    throw { isHttpError: true, data: data };
                }).catch(() => {
                    throw { isHttpError: true, data: { success: false, message: 'Error al actualizar la orden de trabajo' } };
                });
            }
            return response.json();
        })
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
                // Mostrar error en modal si hay conflictos de disponibilidad
                if (data.conflictos) {
                    mostrarModalConflictos(data.conflictos);
                } else {
                    alert('Error al actualizar: ' + (data.message || 'Error desconocido'));
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Si es un error HTTP con datos, mostrar el modal de conflictos
            if (error.isHttpError && error.data && error.data.conflictos) {
                mostrarModalConflictos(error.data.conflictos);
            } else if (error.isHttpError && error.data) {
                // Si hay mensaje pero no conflictos, mostrar alert
                alert('Error al actualizar: ' + (error.data.message || 'Error desconocido'));
            } else {
                alert('Error de conexión al actualizar');
            }
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
    
    console.log('Recolectando items de secciones. Total encontrados:', itemsSecciones.length);
    
    // Obtener estado PENDIENTE por defecto (para creación)
    const estadoPendiente = window.estadosOT.find(e => e.nombre.toLowerCase() === 'pendiente');
    const estadoPendienteId = estadoPendiente ? estadoPendiente.estadoOT_id : null;
    
    itemsSecciones.forEach((itemDiv, index) => {
        const seccionSelect = itemDiv.querySelector('.seccion-select');
        const checkboxes = itemDiv.querySelectorAll('.tipo-reparacion-checkbox:checked');
        const estadoSelect = itemDiv.querySelector('.estado-seccion-select');
        
        console.log(`Item ${index + 1}:`, {
            seccion_id: seccionSelect ? seccionSelect.value : 'NO SELECT',
            checkboxes_count: checkboxes.length,
            estado: estadoSelect ? estadoSelect.value : 'NO SELECT'
        });
        
        // Validar que tenga sección seleccionada
        if (!seccionSelect || !seccionSelect.value) {
            console.warn(`Item ${index + 1} NO incluido: No tiene sección seleccionada`);
            return; // Continuar con el siguiente item
        }
        
        // Validar que tenga al menos un tipo de reparación marcado
        if (checkboxes.length === 0) {
            console.warn(`Item ${index + 1} NO incluido: Sección "${seccionSelect.options[seccionSelect.selectedIndex]?.text}" no tiene tipos de reparación marcados`);
            return; // Continuar con el siguiente item
        }
        
        // En edición, usar el estado seleccionado; en creación, usar Pendiente
        let estadoSeccionId = estadoPendienteId;
        if (window.esEdicion && estadoSelect && estadoSelect.value) {
            estadoSeccionId = parseInt(estadoSelect.value);
        }
        
        items.push({
            seccion_id: parseInt(seccionSelect.value),
            tipos_reparacion_ids: Array.from(checkboxes).map(cb => parseInt(cb.value)),
            estado_seccion_id: estadoSeccionId
        });
        
        console.log(`Item ${index + 1} incluido correctamente:`, {
            seccion_id: parseInt(seccionSelect.value),
            tipos_count: checkboxes.length,
            estado_id: estadoSeccionId
        });
    });
    
    console.log('Items recolectados:', items);
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
