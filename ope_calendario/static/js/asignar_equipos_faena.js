// ============================================================================
// ASIGNAR EQUIPOS A FAENA
// ============================================================================
// Este archivo maneja la asignación de equipos a faenas.
// Permite buscar, filtrar, seleccionar y asignar múltiples equipos a una faena
// con fechas de inicio y fin, incluyendo gestión de equipos ya asignados.

// Variables globales (se inicializan desde el template con datos de Django)
let equipos = [];  // Array con todos los equipos disponibles
let faena = {};  // Objeto con información de la faena actual
let equiposSeleccionados = [];  // Array con IDs de equipos seleccionados para asignar
let faenaFechaInicio = null;  // Fecha de inicio de la faena (para validaciones)
let faenaFechaFin = null;  // Fecha de fin de la faena (para validaciones)
let todasAsignacionesEquipos = [];  // Array con todas las asignaciones de equipos a otras faenas (para validación dinámica)

// Variables de paginación
let paginaActual = 1;  // Página actual de la tabla de equipos (empieza en 1)
let registrosPorPagina = 10;  // Cantidad de equipos a mostrar por página
let equiposFiltrados = [];  // Array con equipos filtrados según búsqueda y filtros

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

// Función de inicialización llamada desde el template HTML
// Configura los datos iniciales y los event listeners del formulario
// Parámetros:
//   equiposData: Array - Array de equipos disponibles
//   faenaData: Object - Objeto con información de la faena
//   fechaInicio: String - Fecha de inicio de la faena (formato ISO)
//   fechaFin: String - Fecha de fin de la faena (formato ISO, puede ser null)
//   asignacionesData: Array - Array con todas las asignaciones de equipos a otras faenas
function initDataEquipos(equiposData, faenaData, fechaInicio, fechaFin, asignacionesData) {
    // Paso 1: Inicializar variables globales con los datos recibidos
    equipos = equiposData || [];  // Array de equipos disponibles
    faena = faenaData || {};  // Información de la faena
    faenaFechaInicio = fechaInicio;  // Fecha de inicio para validaciones
    faenaFechaFin = fechaFin;  // Fecha de fin para validaciones
    todasAsignacionesEquipos = asignacionesData || [];  // Todas las asignaciones de equipos a otras faenas
    
    // Paso 2: Establecer fechas por defecto en los campos del formulario si están disponibles
    // Las fechas se formatean al formato chileno (DD-MM-YYYY) para mostrar en los inputs
    if (faenaFechaInicio) {
        document.getElementById('fecha_inicio').value = formatearFechaChilena(faenaFechaInicio);
    }
    if (faenaFechaFin) {
        document.getElementById('fecha_fin').value = formatearFechaChilena(faenaFechaFin);
    }
    
    // Paso 3: Renderizar tablas iniciales
    renderizarTablaEquipos();  // Tabla de equipos disponibles para asignar
    renderizarEquiposAsignados();  // Tabla de equipos ya asignados a la faena
    
    // Paso 4: Configurar event listeners para filtros y búsqueda
    // Estos listeners reaccionan a cambios y actualizan la tabla automáticamente
    document.getElementById('searchInput').addEventListener('input', renderizarTablaEquipos);  // Búsqueda por texto
    document.getElementById('filtroEstado').addEventListener('change', renderizarTablaEquipos);  // Filtro por estado
    
    // Paso 5: Event listener para cuando se active el tab de "Equipos Asignados"
    // Re-renderiza la tabla para asegurar que los botones se muestren correctamente
    const gestionarTab = document.getElementById('gestionar-tab');
    if (gestionarTab) {
        gestionarTab.addEventListener('shown.bs.tab', function() {
            renderizarEquiposAsignados();
        });
    }
    document.getElementById('filtroTipo').addEventListener('change', renderizarTablaEquipos);  // Filtro por tipo
    document.getElementById('filtroEmpresa').addEventListener('change', renderizarTablaEquipos);  // Filtro por empresa
    
    // Paso 6: Event listeners para validación dinámica cuando cambien las fechas
    const fechaInicioInput = document.getElementById('fecha_inicio');
    const fechaFinInput = document.getElementById('fecha_fin');
    if (fechaInicioInput) {
        fechaInicioInput.addEventListener('change', validarYActualizarTablaEquipos);
        fechaInicioInput.addEventListener('blur', validarYActualizarTablaEquipos);
    }
    if (fechaFinInput) {
        fechaFinInput.addEventListener('change', validarYActualizarTablaEquipos);
        fechaFinInput.addEventListener('blur', validarYActualizarTablaEquipos);
    }
}

// ============================================================================
// UTILIDADES
// ============================================================================

// Función helper para obtener el valor de una cookie por su nombre
// Útil para obtener el token CSRF de Django para las peticiones AJAX
// Parámetros:
//   name: String - Nombre de la cookie a obtener (ej: 'csrftoken')
// Retorna:
//   String - Valor de la cookie, o null si no existe
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        // Dividir las cookies por el separador ';'
        const cookies = document.cookie.split(';');
        // Buscar la cookie con el nombre especificado
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();  // Eliminar espacios
            // Verificar si la cookie comienza con el nombre buscado seguido de '='
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                // Decodificar el valor de la cookie
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;  // Salir del bucle una vez encontrada
            }
        }
    }
    return cookieValue;
}

// Función helper para formatear fecha a formato chileno (DD-MM-YYYY)
// Convierte fechas del formato ISO (YYYY-MM-DD) al formato chileno más legible
// Parámetros:
//   fecha: String - Fecha en formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
// Retorna:
//   String - Fecha formateada en formato DD-MM-YYYY, o string vacío si no hay fecha
function formatearFechaChilena(fecha) {
    if (!fecha) return '';  // Si no hay fecha, retornar string vacío
    
    try {
        // Crear objeto Date desde el string ISO
        // Agregar 'T00:00:00' para evitar problemas de timezone
        const date = new Date(fecha + 'T00:00:00');
        const dia = String(date.getDate()).padStart(2, '0');  // Día con cero a la izquierda
        const mes = String(date.getMonth() + 1).padStart(2, '0');  // Mes (getMonth() es 0-based)
        const anio = date.getFullYear();  // Año completo
        return `${dia}-${mes}-${anio}`;  // Retornar fecha formateada
    } catch (error) {
        console.error('Error formateando fecha:', error);
        return fecha;  // Retornar fecha original si hay error
    }
}

// Función helper para convertir fecha chilena a formato ISO (YYYY-MM-DD)
// Convierte fechas del formato chileno (DD-MM-YYYY) al formato ISO requerido por la API
// Parámetros:
//   fechaChilena: String - Fecha en formato chileno (DD-MM-YYYY)
// Retorna:
//   String - Fecha en formato ISO (YYYY-MM-DD), o null si no es válida
function fechaChilenaToISO(fechaChilena) {
    if (!fechaChilena) return null;  // Si no hay fecha, retornar null
    
    // Dividir la fecha por el separador '-'
    const partes = fechaChilena.split('-');
    if (partes.length === 3) {
        // Reordenar: [dia, mes, año] -> [año, mes, dia]
        return `${partes[2]}-${partes[1]}-${partes[0]}`;
    }
    return null;  // Si el formato no es válido, retornar null
}

// ============================================================================
// RENDERIZADO DE TABLA
// ============================================================================

// Función para renderizar la tabla de equipos con paginación y filtros
// Filtra los equipos según búsqueda y filtros, y muestra solo los de la página actual
// Excluye equipos ya asignados a esta faena para evitar duplicados
function renderizarTablaEquipos() {
    // Paso 1: Obtener referencias a elementos del DOM y valores de filtros
    const tbody = document.getElementById('equiposTableBody');
    const busqueda = document.getElementById('searchInput').value.toLowerCase();  // Término de búsqueda en minúsculas
    const filtroEstado = document.getElementById('filtroEstado').value;  // Filtro por estado (disponible/asignado)
    const filtroTipo = document.getElementById('filtroTipo').value;  // Filtro por tipo de equipo
    const filtroEmpresa = document.getElementById('filtroEmpresa').value;  // Filtro por empresa
    
    // Paso 2: Obtener IDs de equipos ya asignados a ESTA faena
    // Estos equipos se excluyen de la lista para evitar asignaciones duplicadas
    const idsAsignadosEstaFaena = faena.asignaciones ? faena.asignaciones.map(a => a.equipo.id) : [];
    
    // Paso 3: Filtrar equipos según criterios de búsqueda y filtros
    equiposFiltrados = equipos.filter(eq => {
        // Paso 3.1: NO mostrar equipos ya asignados a ESTA faena
        // Esto evita que se puedan asignar equipos que ya están asignados a la misma faena
        if (idsAsignadosEstaFaena.includes(eq.id)) {
            return false;  // Excluir equipo ya asignado
        }
        
        // Paso 3.2: Búsqueda por código interno, nombre o patente
        const codigo = eq.codigo_interno.toLowerCase();
        const nombre = eq.nombre.toLowerCase();
        const patente = (eq.patente || '').toLowerCase();
        // El equipo coincide si no hay búsqueda o si alguno de estos campos contiene el término
        const matchBusqueda = !busqueda || codigo.includes(busqueda) || nombre.includes(busqueda) || patente.includes(busqueda);
        
        // Paso 3.3: Filtro de estado (disponible/asignado)
        let matchEstado = true;  // Por defecto, todos los estados coinciden
        if (filtroEstado === 'disponible') {
            // CASO: Solo equipos disponibles (sin asignación activa)
            matchEstado = !eq.tiene_asignacion;
        } else if (filtroEstado === 'asignado') {
            // CASO: Solo equipos asignados (con asignación activa)
            matchEstado = eq.tiene_asignacion;
        }
        
        // Paso 3.4: Filtro de tipo de equipo
        const matchTipo = !filtroTipo || eq.tipo === filtroTipo;
        
        // Paso 3.5: Filtro de empresa
        const matchEmpresa = !filtroEmpresa || eq.empresa === filtroEmpresa;
        
        // Paso 3.6: El equipo se incluye si cumple todos los criterios
        return matchBusqueda && matchEstado && matchTipo && matchEmpresa;
    });
    
    // Actualizar contador total
    document.getElementById('totalEquipos').textContent = equiposFiltrados.length;
    
    // Calcular paginación
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, equiposFiltrados.length);
    const equiposPagina = equiposFiltrados.slice(inicio, fin);
    
    // Actualizar contadores
    document.getElementById('registroInicio').textContent = equiposFiltrados.length > 0 ? inicio + 1 : 0;
    document.getElementById('registroFin').textContent = fin;
    document.getElementById('totalRegistros').textContent = equiposFiltrados.length;
    
    // Renderizar tabla
    if (equiposPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="bi bi-inbox me-2"></i>No se encontraron equipos
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = equiposPagina.map(eq => {
            const estaSeleccionado = equiposSeleccionados.includes(eq.id);
            const tieneAsignacion = eq.tiene_asignacion;
            const asignacionInfo = eq.asignacion_actual;
            
            // Validar si el equipo tiene asignación conflictiva en las fechas seleccionadas
            const tieneConflictoEnFechas = validarConflictoEquipoEnFechas(eq.id);
            // Debug: verificar que se encuentren todos los conflictos
            if (tieneConflictoEnFechas.conflicto && tieneConflictoEnFechas.asignaciones) {
                if (tieneConflictoEnFechas.asignaciones.length > 1) {
                    console.log(`[TABLA] Equipo ${eq.nombre} (ID: ${eq.id}) tiene ${tieneConflictoEnFechas.asignaciones.length} conflictos:`, tieneConflictoEnFechas.asignaciones);
                } else if (tieneConflictoEnFechas.asignaciones.length === 1) {
                    console.log(`[TABLA] Equipo ${eq.nombre} (ID: ${eq.id}) tiene 1 conflicto:`, tieneConflictoEnFechas.asignaciones[0]);
                }
            }
            const tieneAsignacionFinal = tieneAsignacion || tieneConflictoEnFechas.conflicto;
            
            // Estado: Disponible o Asignado
            const estadoClass = tieneAsignacionFinal ? 'bg-warning' : 'bg-success';
            const estadoText = tieneAsignacionFinal ? 'Asignado' : 'Disponible';
            
            // Asignación Actual: mostrar todas las asignaciones conflictivas o la asignación general
            let asignacionActualHTML = '-';
            if (tieneAsignacionFinal) {
                // SIEMPRE priorizar mostrar los conflictos encontrados en las fechas seleccionadas
                if (tieneConflictoEnFechas && tieneConflictoEnFechas.conflicto && tieneConflictoEnFechas.asignaciones && tieneConflictoEnFechas.asignaciones.length > 0) {
                    // Mostrar TODAS las asignaciones conflictivas en fechas seleccionadas
                    asignacionActualHTML = tieneConflictoEnFechas.asignaciones.map(asig => {
                        return asig.faena_nombre || '-';
                    }).join(', ');
                    // Debug: verificar que se muestren todas
                    if (tieneConflictoEnFechas.asignaciones.length > 1) {
                        console.log(`[RENDER] Equipo ${eq.nombre}: Mostrando ${tieneConflictoEnFechas.asignaciones.length} asignaciones: ${asignacionActualHTML}`);
                    }
                } else if (asignacionInfo) {
                    // Si no hay conflictos en fechas seleccionadas, mostrar la asignación general
                    if (asignacionInfo.tipo === 'ot') {
                        asignacionActualHTML = `OT: ${asignacionInfo.folio}`;
                    } else {
                        asignacionActualHTML = asignacionInfo.faena || '-';
                    }
                    // Debug: verificar por qué no se muestran los conflictos
                    if (tieneConflictoEnFechas && tieneConflictoEnFechas.conflicto === false) {
                        console.log(`[RENDER] Equipo ${eq.nombre}: No hay conflictos en fechas seleccionadas, usando asignacionInfo:`, asignacionInfo);
                    } else if (!tieneConflictoEnFechas || !tieneConflictoEnFechas.asignaciones || tieneConflictoEnFechas.asignaciones.length === 0) {
                        console.log(`[RENDER] Equipo ${eq.nombre}: tieneConflictoEnFechas:`, tieneConflictoEnFechas);
                    }
                }
            }
            
            // Fecha Asignación: mostrar todas las fechas de las asignaciones conflictivas
            let fechaAsignacionHTML = '-';
            if (tieneAsignacionFinal) {
                // SIEMPRE priorizar mostrar los conflictos encontrados en las fechas seleccionadas
                if (tieneConflictoEnFechas.conflicto && tieneConflictoEnFechas.asignaciones && tieneConflictoEnFechas.asignaciones.length > 0) {
                    // Mostrar TODAS las fechas de los conflictos en fechas seleccionadas
                    fechaAsignacionHTML = tieneConflictoEnFechas.asignaciones.map(asig => {
                        const fechaInicio = formatearFechaChilena(asig.fecha_inicio);
                        const fechaFin = asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : 'Indefinida';
                        return `${fechaInicio} → ${fechaFin}`;
                    }).join('<br>');
                } else if (asignacionInfo && asignacionInfo.fecha_inicio) {
                    // Si no hay conflictos en fechas seleccionadas, mostrar la fecha de la asignación general
                    const fechaInicio = formatearFechaChilena(asignacionInfo.fecha_inicio);
                    const fechaFin = asignacionInfo.fecha_fin ? formatearFechaChilena(asignacionInfo.fecha_fin) : 'Indefinida';
                    fechaAsignacionHTML = `${fechaInicio} → ${fechaFin}`;
                }
            }
            
            return `
                <tr class="${tieneAsignacionFinal ? 'table-secondary' : ''}">
                    <td class="text-center">
                        <input class="form-check-input" type="checkbox" 
                               ${estaSeleccionado ? 'checked' : ''}
                               onchange="toggleEquipoSeleccionado(${eq.id})"
                               id="equipo_${eq.id}"
                               ${tieneAsignacionFinal ? `title="Equipo asignado a ${asignacionActualHTML !== '-' ? asignacionActualHTML : 'otra faena/OT'} en ${fechaAsignacionHTML !== '-' ? fechaAsignacionHTML : 'fechas específicas'}"` : ''}>
                    </td>
                    <td>${eq.nombre}</td>
                    <td>${eq.patente || '-'}</td>
                    <td>${eq.tipo}</td>
                    <td>${eq.empresa}</td>
                    <td>
                        <span class="badge ${estadoClass}">${estadoText}</span>
                    </td>
                    <td>${asignacionActualHTML}</td>
                    <td class="small">${fechaAsignacionHTML}</td>
                </tr>
            `;
        }).join('');
    }
    
    // Renderizar paginación
    renderizarPaginacionEquipos(totalPaginas);
    
    // Actualizar contador de seleccionados
    actualizarContadorSeleccionados();
    
    // Actualizar estado del botón
    actualizarBotonAsignar();
}

// Función para validar si un equipo tiene conflictos en las fechas seleccionadas
// Parámetros:
//   equipoId: Number - ID del equipo a validar
// Retorna:
//   Object - { conflicto: boolean, asignaciones: Array } - Array con todas las asignaciones que conflictan
function validarConflictoEquipoEnFechas(equipoId) {
    // Obtener fechas seleccionadas del formulario
    let fechaInicio = null;
    let fechaFin = null;
    
    // Intentar obtener fechas usando DatePickerChile si está disponible
    if (window.DatePickerChile && typeof window.DatePickerChile.getValor === 'function') {
        fechaInicio = window.DatePickerChile.getValor('fecha_inicio');
        fechaFin = window.DatePickerChile.getValor('fecha_fin');
    }
    
    // Fallback: obtener del input hidden o del input original
    if (!fechaInicio) {
        const fechaInicioHidden = document.getElementById('fecha_inicio_hidden');
        if (fechaInicioHidden && fechaInicioHidden.value) {
            fechaInicio = fechaInicioHidden.value;
        } else {
            const fechaInicioInput = document.getElementById('fecha_inicio');
            if (fechaInicioInput && fechaInicioInput.value) {
                const fechaValue = fechaInicioInput.value;
                if (fechaValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaInicio = fechaValue;
                } else {
                    fechaInicio = fechaChilenaToISO(fechaValue);
                }
            }
        }
    }
    
    if (!fechaFin) {
        const fechaFinHidden = document.getElementById('fecha_fin_hidden');
        if (fechaFinHidden && fechaFinHidden.value) {
            fechaFin = fechaFinHidden.value;
        } else {
            const fechaFinInput = document.getElementById('fecha_fin');
            if (fechaFinInput && fechaFinInput.value) {
                const fechaValue = fechaFinInput.value;
                if (fechaValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaFin = fechaValue;
                } else {
                    fechaFin = fechaChilenaToISO(fechaValue);
                }
            }
        }
    }
    
    // Si no hay fecha de inicio seleccionada, usar fechas de la faena como fallback
    if (!fechaInicio && faenaFechaInicio) {
        fechaInicio = faenaFechaInicio;
    }
    if (!fechaFin && faenaFechaFin) {
        fechaFin = faenaFechaFin;
    }
    
    // Si aún no hay fecha de inicio, no hay conflicto
    if (!fechaInicio) {
        return { conflicto: false, asignaciones: [] };
    }
    
    const asignacionesConflictivas = [];
    
    // Buscar TODAS las asignaciones del equipo que se solapen con las fechas seleccionadas
    // Esto incluye tanto asignaciones a otras faenas como OTs
    // Excluir asignaciones de la faena actual (las OTs tienen faena_id: null, así que pasan el filtro)
    const asignacionesEquipo = todasAsignacionesEquipos.filter(asig => 
        asig.equipo_id === equipoId && (asig.faena_id === null || asig.faena_id !== faena.id)
    );
    
    // Debug: verificar que se encuentren todas las asignaciones del equipo
    if (asignacionesEquipo.length > 0) {
        console.log(`Equipo ID ${equipoId}: encontradas ${asignacionesEquipo.length} asignaciones (faenas/OTs) para validar`, asignacionesEquipo);
    }
    
    for (const asignacion of asignacionesEquipo) {
        const asigInicio = asignacion.fecha_inicio;
        const asigFin = asignacion.fecha_fin;
        
        // Verificar solapamiento: dos rangos se solapan si inicio1 <= fin2 AND inicio2 <= fin1
        let haySolapamiento = false;
        
        if (fechaFin) {
            // Rango con fecha fin: verificar solapamiento
            if (asigFin) {
                // Ambas tienen fecha fin: se solapan si inicio1 <= fin2 AND inicio2 <= fin1
                if (asigInicio <= fechaFin && asigFin >= fechaInicio) {
                    haySolapamiento = true;
                }
            } else {
                // La asignación no tiene fecha fin: se solapa si comienza antes o en la fecha fin seleccionada
                if (asigInicio <= fechaFin) {
                    haySolapamiento = true;
                }
            }
        } else {
            // Rango sin fecha fin: se solapa si la asignación comienza antes o en la fecha inicio seleccionada
            if (asigFin) {
                // La asignación tiene fecha fin: se solapa si termina después o en la fecha inicio seleccionada
                if (asigFin >= fechaInicio) {
                    haySolapamiento = true;
                }
            } else {
                // Ninguna tiene fecha fin: siempre hay conflicto si hay asignación
                haySolapamiento = true;
            }
        }
        
        if (haySolapamiento) {
            asignacionesConflictivas.push(asignacion);
        }
    }
    
    return { 
        conflicto: asignacionesConflictivas.length > 0, 
        asignaciones: asignacionesConflictivas 
    };
}

// Función para validar y actualizar la tabla de equipos cuando cambien las fechas
function validarYActualizarTablaEquipos() {
    // Pequeño delay para asegurar que las fechas se hayan actualizado
    setTimeout(() => {
        renderizarTablaEquipos();
    }, 100);
}

// Renderizar paginación
function renderizarPaginacionEquipos(totalPaginas) {
    const paginacion = document.getElementById('paginacion');
    
    if (totalPaginas <= 1) {
        paginacion.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${paginaActual - 1}); return false;">Anterior</a>
        </li>
    `;
    
    // Números de página
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === 1 || i === totalPaginas || (i >= paginaActual - 2 && i <= paginaActual + 2)) {
            html += `
                <li class="page-item ${i === paginaActual ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === paginaActual - 3 || i === paginaActual + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPaginaEquipos(${paginaActual + 1}); return false;">Siguiente</a>
        </li>
    `;
    
    paginacion.innerHTML = html;
}

// Cambiar página
function cambiarPaginaEquipos(nuevaPagina) {
    const totalPaginas = Math.ceil(equiposFiltrados.length / registrosPorPagina);
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas) {
        paginaActual = nuevaPagina;
        renderizarTablaEquipos();
    }
}

// Cambiar registros por página
function cambiarRegistrosPorPaginaEquipos() {
    registrosPorPagina = parseInt(document.getElementById('registrosPorPagina').value);
    paginaActual = 1;
    renderizarTablaEquipos();
}

// ============================================================================
// SELECCIÓN DE EQUIPOS
// ============================================================================

// Función para alternar la selección de un equipo individual
// Agrega o elimina el equipo del array de seleccionados según el estado del checkbox
// Parámetros:
//   equipoId: Number - ID del equipo a seleccionar/deseleccionar
function toggleEquipoSeleccionado(equipoId) {
    // Paso 1: Obtener referencia al checkbox del equipo
    const checkbox = document.getElementById(`equipo_${equipoId}`);
    
    // Paso 2: Si el checkbox está deshabilitado (equipo con asignación conflictiva), no hacer nada
    if (checkbox.disabled) return;
    
    // Paso 3: Agregar o eliminar el equipo del array de seleccionados según el estado del checkbox
    if (checkbox.checked) {
        // CASO: Checkbox marcado -> Agregar equipo a la selección
        if (!equiposSeleccionados.includes(equipoId)) {
            equiposSeleccionados.push(equipoId);  // Agregar ID al array si no está ya incluido
        }
    } else {
        // CASO: Checkbox desmarcado -> Eliminar equipo de la selección
        equiposSeleccionados = equiposSeleccionados.filter(id => id !== equipoId);  // Filtrar el ID del array
    }
    
    // Paso 4: Actualizar contador y estado del botón después del cambio
    actualizarContadorSeleccionados();  // Actualizar contador visual
    actualizarBotonAsignar();  // Habilitar/deshabilitar botón según selección
}

// Función para seleccionar/deseleccionar todos los equipos visibles
// Alterna el estado de todos los checkboxes habilitados según el checkbox "seleccionar todos"
function toggleSelectAllEquipos() {
    // Paso 1: Obtener referencia al checkbox "seleccionar todos"
    const selectAll = document.getElementById('selectAllEquipos');
    
    // Paso 2: Obtener todos los checkboxes de equipos que NO estén deshabilitados
    // Solo se pueden seleccionar equipos disponibles (sin asignaciones conflictivas)
    const checkboxes = document.querySelectorAll('#equiposTableBody input[type="checkbox"]:not(:disabled)');
    
    // Paso 3: Actualizar estado de cada checkbox y el array de seleccionados
    checkboxes.forEach(cb => {
        // Paso 3.1: Marcar/desmarcar checkbox según el estado de "seleccionar todos"
        cb.checked = selectAll.checked;
        
        // Paso 3.2: Extraer ID del equipo desde el ID del checkbox (formato: "equipo_123")
        const equipoId = parseInt(cb.id.replace('equipo_', ''));
        
        // Paso 3.3: Agregar o eliminar del array de seleccionados según el estado
        if (selectAll.checked) {
            // CASO: Seleccionar todos -> Agregar equipo al array si no está ya incluido
            if (!equiposSeleccionados.includes(equipoId)) {
                equiposSeleccionados.push(equipoId);
            }
        } else {
            // CASO: Deseleccionar todos -> Eliminar equipo del array
            equiposSeleccionados = equiposSeleccionados.filter(id => id !== equipoId);
        }
    });
    
    // Paso 4: Actualizar contador y estado del botón después del cambio
    actualizarContadorSeleccionados();  // Actualizar contador visual
    actualizarBotonAsignar();  // Habilitar/deshabilitar botón según selección
}

// Función para actualizar el contador visual de equipos seleccionados
// Muestra la cantidad de equipos seleccionados en el elemento del DOM
function actualizarContadorSeleccionados() {
    document.getElementById('totalSeleccionados').textContent = equiposSeleccionados.length;
}

// Función para actualizar el estado del botón de asignar
// Habilita el botón solo si hay equipos seleccionados, lo deshabilita si no hay ninguno
function actualizarBotonAsignar() {
    const btn = document.getElementById('btnAsignarEquiposMasivo');
    btn.disabled = equiposSeleccionados.length === 0;  // Deshabilitar si no hay selección
}

// ============================================================================
// FILTROS
// ============================================================================

// Función para limpiar todos los filtros y recargar la tabla
// Restablece todos los campos de filtro a sus valores por defecto y vuelve a la primera página
function limpiarFiltrosEquipos() {
    // Limpiar todos los campos de filtro
    document.getElementById('searchInput').value = '';  // Limpiar búsqueda
    document.getElementById('filtroEstado').value = '';  // Limpiar filtro de estado
    document.getElementById('filtroTipo').value = '';  // Limpiar filtro de tipo
    document.getElementById('filtroEmpresa').value = '';  // Limpiar filtro de empresa
    paginaActual = 1;  // Volver a la primera página
    renderizarTablaEquipos();  // Re-renderizar tabla sin filtros
}

// ============================================================================
// ASIGNACIÓN MASIVA
// ============================================================================

// Función para asignar múltiples equipos a la faena de forma masiva
// Obtiene las fechas del formulario, valida los datos y envía la petición a la API
// Parámetros:
//   Ninguno (usa variables globales y elementos del DOM)
async function asignarEquiposMasivo() {
    // Paso 1: Obtener valores de fecha del date picker en formato ISO
    // Se intentan múltiples métodos para obtener las fechas en el formato correcto
    let fechaInicio = null;
    let fechaFin = null;
    
    // Paso 1.1: Intentar usar DatePickerChile.getValor() si está disponible (devuelve formato ISO)
    if (window.DatePickerChile && typeof window.DatePickerChile.getValor === 'function') {
        fechaInicio = window.DatePickerChile.getValor('fecha_inicio');
        fechaFin = window.DatePickerChile.getValor('fecha_fin');
    } else {
        // Paso 1.2: Fallback: intentar obtener del input hidden (formato ISO)
        const fechaInicioHidden = document.getElementById('fecha_inicio_hidden');
        const fechaFinHidden = document.getElementById('fecha_fin_hidden');
        
        if (fechaInicioHidden && fechaInicioHidden.value) {
            fechaInicio = fechaInicioHidden.value;
        } else {
            // Paso 1.3: Último recurso: obtener del input original y convertir
            const fechaInicioValue = document.getElementById('fecha_inicio').value;
            if (fechaInicioValue) {
                // Verificar si ya está en formato ISO (YYYY-MM-DD)
                if (fechaInicioValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaInicio = fechaInicioValue;
                } else {
                    // Convertir de formato chileno (DD-MM-YYYY) a ISO (YYYY-MM-DD)
                    fechaInicio = fechaChilenaToISO(fechaInicioValue);
                }
            }
        }
        
        // Mismo proceso para fecha de fin
        if (fechaFinHidden && fechaFinHidden.value) {
            fechaFin = fechaFinHidden.value;
        } else {
            const fechaFinValue = document.getElementById('fecha_fin').value;
            if (fechaFinValue) {
                // Verificar si ya está en formato ISO
                if (fechaFinValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaFin = fechaFinValue;
                } else {
                    // Convertir de formato chileno a ISO
                    fechaFin = fechaChilenaToISO(fechaFinValue);
                }
            }
        }
    }
    
    // Paso 2: Obtener observaciones del formulario
    const observaciones = document.getElementById('observaciones').value.trim();
    
    // Paso 3: Validar datos antes de enviar
    if (!fechaInicio) {
        mostrarAlerta('La fecha de inicio es requerida', 'error');
        return;  // Detener ejecución si falta fecha de inicio
    }
    
    if (equiposSeleccionados.length === 0) {
        mostrarAlerta('Debe seleccionar al menos un equipo', 'error');
        return;  // Detener ejecución si no hay equipos seleccionados
    }
    
    // Paso 3.1: Validar conflictos de fechas para cada equipo seleccionado
    const equiposConConflicto = [];
    for (const equipoId of equiposSeleccionados) {
        const validacion = validarConflictoEquipoEnFechas(equipoId);
        if (validacion.conflicto && validacion.asignaciones && validacion.asignaciones.length > 0) {
            const equipo = equipos.find(eq => eq.id === equipoId);
            const nombreEquipo = equipo ? equipo.nombre : `Equipo ID ${equipoId}`;
            
            // Agregar todas las asignaciones conflictivas para este equipo
            const conflictosEquipo = validacion.asignaciones.map(asignacion => {
                const fechaInicioConflicto = formatearFechaChilena(asignacion.fecha_inicio);
                const fechaFinConflicto = asignacion.fecha_fin ? formatearFechaChilena(asignacion.fecha_fin) : 'Indefinida';
                return {
                    nombre: nombreEquipo,
                    faena: asignacion.faena_nombre,
                    fechaInicio: fechaInicioConflicto,
                    fechaFin: fechaFinConflicto
                };
            });
            
            equiposConConflicto.push(...conflictosEquipo);
        }
    }
    
    // Si hay equipos con conflicto, mostrar error y detener ejecución
    if (equiposConConflicto.length > 0) {
        let mensajeError = 'Los siguientes equipos tienen asignaciones conflictivas en las fechas seleccionadas:\n\n';
        equiposConConflicto.forEach(conflicto => {
            mensajeError += `• ${conflicto.nombre}: Asignado a "${conflicto.faena}" (${conflicto.fechaInicio} → ${conflicto.fechaFin})\n`;
        });
        mensajeError += '\nPor favor, seleccione otras fechas o deseleccione estos equipos.';
        mostrarAlerta(mensajeError, 'error');
        return;  // Detener ejecución si hay conflictos
    }
    
    // Paso 4: Construir objeto con los datos a enviar a la API
    const data = {
        faena_id: faena.id,  // ID de la faena
        equipos_ids: equiposSeleccionados,  // Array de IDs de equipos seleccionados
        fecha_inicio: fechaInicio,  // Fecha de inicio en formato ISO
        fecha_fin: fechaFin || null,  // Fecha de fin en formato ISO (puede ser null)
        observaciones: observaciones  // Observaciones opcionales
    };
    
    // Paso 5: Enviar petición a la API para crear las asignaciones
    try {
        const response = await fetch('/calendario/api/crear-asignacion-equipos/', {
            method: 'POST',  // Método HTTP POST para crear recursos
            headers: {
                'Content-Type': 'application/json',  // Tipo de contenido JSON
                'X-CSRFToken': getCookie('csrftoken')  // Token CSRF de Django
            },
            body: JSON.stringify(data)  // Convertir objeto a JSON
        });
        
        const result = await response.json();  // Convertir respuesta a JSON
        
        if (response.ok && result.success) {
            // CASO ÉXITO: Las asignaciones se crearon correctamente
            mostrarAlerta(result.message || 'Equipos asignados correctamente', 'success');
            
            // Paso 5.1: Limpiar selección después del éxito
            equiposSeleccionados = [];  // Limpiar array de seleccionados
            document.getElementById('selectAllEquipos').checked = false;  // Desmarcar checkbox "seleccionar todos"
            
            // Paso 5.2: Recargar página para actualizar datos después de 1.5 segundos
            // Esto permite que el usuario vea el mensaje de éxito antes de recargar
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            // CASO ERROR: El servidor retornó un error
            mostrarAlerta(result.error || 'Error al asignar equipos', 'error');
        }
    } catch (error) {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);
        mostrarAlerta('Error de conexión al asignar equipos', 'error');
    }
}

// ============================================================================
// GESTIÓN DE EQUIPOS ASIGNADOS
// ============================================================================

// Función para renderizar la tabla de equipos ya asignados a la faena
// Muestra todos los equipos que están actualmente asignados con sus fechas y permite editarlos/eliminarlos
function renderizarEquiposAsignados() {
    // Paso 1: Obtener referencia al tbody de la tabla de equipos asignados
    const tbody = document.getElementById('equiposAsignadosBody');
    
    // Paso 2: Verificar si hay asignaciones de equipos
    if (!faena.asignaciones || faena.asignaciones.length === 0) {
        // CASO: No hay asignaciones -> Mostrar mensaje informativo
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="bi bi-inbox me-2"></i>No hay equipos asignados
                </td>
            </tr>
        `;
        return;  // Salir de la función
    }
    
    tbody.innerHTML = faena.asignaciones.map(asig => {
        return `
            <tr>
                <td>${asig.equipo.nombre}</td>
                <td>${asig.equipo.patente || '-'}</td>
                <td>${asig.equipo.tipo}</td>
                <td>${asig.equipo.empresa}</td>
                <td>${formatearFechaChilena(asig.fecha_inicio)}</td>
                <td>${asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : 'Indefinida'}</td>
                <td class="text-center">
                    <div class="btn-group btn-group-sm">
                        ${(!window.userPermissions || window.userPermissions.canModificarAsignacion || window.userPermissions.canChange) ? `
                        <button class="btn btn-sm btn-primary" onclick="editarAsignacionEquipo(${asig.id})" title="Editar asignación">
                            <i class="bi bi-pencil"></i>
                        </button>
                        ` : ''}
                        ${(!window.userPermissions || window.userPermissions.canDelete) ? `
                        <button class="btn btn-sm btn-danger" onclick="eliminarAsignacionEquipo(${asig.id})" title="Eliminar asignación">
                            <i class="bi bi-trash"></i>
                        </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Función para abrir el modal de edición de asignación de equipo
// Carga los datos de la asignación en el formulario del modal
// Parámetros:
//   asignacionId: Number - ID de la asignación a editar
function editarAsignacionEquipo(asignacionId) {
    // Paso 1: Buscar la asignación en el array de asignaciones de la faena
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) {
        console.error('Asignación no encontrada:', asignacionId);
        mostrarAlerta('Error: Asignación no encontrada', 'error');
        return;  // Salir si no se encuentra la asignación
    }
    
    // Paso 2: Limpiar alertas previas del modal
    const alertContainer = document.getElementById('alertEditAsignacionEquipo');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    // Paso 3: Llenar campos del formulario con los datos de la asignación
    document.getElementById('editEquipoAsig_id').value = asignacion.id;  // ID de la asignación
    document.getElementById('editEquipoAsig_faena_id').value = faena.id;  // ID de la faena
    document.getElementById('editEquipoAsig_nombreEquipo').textContent = asignacion.equipo.nombre;  // Nombre del equipo
    
    // Paso 4: Llenar fechas usando DatePickerChile si está disponible
    if (window.DatePickerChile) {
        DatePickerChile.setValor('editEquipoAsig_fechaInicio', asignacion.fecha_inicio);  // Establecer fecha inicio
        if (asignacion.fecha_fin) {
            DatePickerChile.setValor('editEquipoAsig_fechaFin', asignacion.fecha_fin);  // Establecer fecha fin si existe
        } else {
            DatePickerChile.limpiar('editEquipoAsig_fechaFin');  // Limpiar fecha fin si no existe
        }
    }
    
    // Paso 5: Llenar campo de observaciones
    document.getElementById('editEquipoAsig_obs').value = asignacion.observaciones || '';
    
    // Paso 6: Abrir el modal de edición
    const modalElement = document.getElementById('modalEditarAsignacionEquipo');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Función para guardar la edición de una asignación de equipo
// Valida los datos, envía la petición a la API y actualiza la interfaz
// Parámetros:
//   event: Event - Evento del formulario (se previene el submit por defecto)
async function guardarEdicionAsignacionEquipo(event) {
    event.preventDefault();  // Prevenir envío por defecto del formulario
    
    // Paso 1: Obtener IDs de la asignación y la faena desde el formulario
    const id = document.getElementById('editEquipoAsig_id').value;
    const faenaId = document.getElementById('editEquipoAsig_faena_id').value;
    
    // Paso 2: Obtener fechas en formato ISO desde el formulario
    // Se intentan múltiples métodos para obtener las fechas en el formato correcto
    let fechaInicio = null;
    let fechaFin = null;
    
    if (window.DatePickerChile && typeof window.DatePickerChile.getValor === 'function') {
        // Método preferido: usar DatePickerChile si está disponible
        fechaInicio = window.DatePickerChile.getValor('editEquipoAsig_fechaInicio');
        fechaFin = window.DatePickerChile.getValor('editEquipoAsig_fechaFin');
    } else {
        // Fallback: intentar obtener del input hidden (formato ISO)
        const fechaInicioHidden = document.getElementById('editEquipoAsig_fechaInicio_hidden');
        const fechaFinHidden = document.getElementById('editEquipoAsig_fechaFin_hidden');
        
        if (fechaInicioHidden && fechaInicioHidden.value) {
            fechaInicio = fechaInicioHidden.value;
        } else {
            // Último recurso: obtener del input original y convertir
            const fechaInicioValue = document.getElementById('editEquipoAsig_fechaInicio').value;
            if (fechaInicioValue) {
                // Verificar si ya está en formato ISO
                if (fechaInicioValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaInicio = fechaInicioValue;
                } else {
                    // Convertir de formato chileno a ISO
                    fechaInicio = fechaChilenaToISO(fechaInicioValue);
                }
            }
        }
        
        // Mismo proceso para fecha de fin
        if (fechaFinHidden && fechaFinHidden.value) {
            fechaFin = fechaFinHidden.value;
        } else {
            const fechaFinValue = document.getElementById('editEquipoAsig_fechaFin').value;
            if (fechaFinValue) {
                if (fechaFinValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    fechaFin = fechaFinValue;
                } else {
                    fechaFin = fechaChilenaToISO(fechaFinValue);
                }
            }
        }
    }
    
    // Paso 3: Obtener observaciones del formulario
    const obs = document.getElementById('editEquipoAsig_obs').value.trim();
    
    // Paso 4: Validar datos antes de enviar
    // Validación 1: Fecha fin debe ser posterior a fecha inicio
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
        mostrarAlertaEnModal('La fecha de fin debe ser posterior a la fecha de inicio', 'error', 'alertEditAsignacionEquipo');
        return;  // Detener ejecución si la validación falla
    }
    
    // Validación 2: Fecha inicio de asignación no puede ser antes del inicio de la faena
    // Esto asegura que la asignación esté dentro del rango de la faena
    if (faenaFechaInicio && fechaInicio && fechaInicio < faenaFechaInicio) {
        mostrarAlertaEnModal(`La fecha de inicio no puede ser anterior al inicio de la faena (${formatearFechaChilena(faenaFechaInicio)})`, 'error', 'alertEditAsignacionEquipo');
        return;  // Detener ejecución si la validación falla
    }
    
    // Validación 3: Fecha fin de asignación no puede ser posterior al fin de la faena (si la faena tiene fin)
    // Esto asegura que la asignación no se extienda más allá de la faena
    if (faenaFechaFin && fechaFin && fechaFin > faenaFechaFin) {
        mostrarAlertaEnModal(`La fecha de fin no puede ser posterior al fin de la faena (${formatearFechaChilena(faenaFechaFin)})`, 'error', 'alertEditAsignacionEquipo');
        return;  // Detener ejecución si la validación falla
    }
    
    try {
        const response = await fetch('/calendario/api/actualizar-asignacion-equipo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                asignacion_id: parseInt(id),
                faena_id: parseInt(faenaId),
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin || null,
                observaciones: obs
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Cerrar modal
            const modalElement = document.getElementById('modalEditarAsignacionEquipo');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar mensaje de éxito
            mostrarAlerta(result.message || 'Asignación actualizada correctamente', 'success');
            
            // Actualizar los datos localmente
            const asignacion = faena.asignaciones.find(a => a.id === parseInt(id));
            if (asignacion) {
                asignacion.fecha_inicio = fechaInicio;
                asignacion.fecha_fin = fechaFin || null;
                asignacion.observaciones = obs;
            }
            
            // Re-renderizar la tabla de equipos asignados
            renderizarEquiposAsignados();
        } else {
            mostrarAlertaEnModal(result.error || 'Error al actualizar la asignación', 'error', 'alertEditAsignacionEquipo');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarAlertaEnModal('Error de conexión al actualizar la asignación', 'error', 'alertEditAsignacionEquipo');
    }
}

// Función auxiliar para mostrar alertas dentro de un modal específico
// Crea un alert de Bootstrap dentro del contenedor especificado
// Parámetros:
//   mensaje: String - Texto del mensaje a mostrar
//   tipo: String - Tipo de alerta ('error', 'success', 'info')
//   containerId: String - ID del contenedor donde mostrar la alerta
function mostrarAlertaEnModal(mensaje, tipo, containerId) {
    // Paso 1: Obtener referencia al contenedor de alertas del modal
    const container = document.getElementById(containerId);
    if (!container) return;  // Si no existe el contenedor, salir sin hacer nada
    
    // Paso 2: Determinar clase CSS e icono según el tipo de alerta
    const alertClass = tipo === 'error' ? 'danger' : tipo;  // 'error' se mapea a 'danger' en Bootstrap
    const icon = tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle';
    
    // Paso 3: Crear y mostrar el alert de Bootstrap
    container.innerHTML = `
        <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi bi-${icon} me-2"></i>${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
}

// Variable para guardar el ID de la asignación de equipo a eliminar
let asignacionEquipoAEliminar = null;

// Función para eliminar una asignación de equipo
// Muestra modal de confirmación antes de eliminar
// Parámetros:
//   asignacionId: Number - ID de la asignación a eliminar
function eliminarAsignacionEquipo(asignacionId) {
    const asignacion = faena.asignaciones.find(a => a.id === asignacionId);
    if (!asignacion) return;
    
    // Guardar ID para usar en la confirmación
    asignacionEquipoAEliminar = asignacionId;
    
    // Mostrar nombre del equipo en el modal
    const nombreEquipo = asignacion.equipo.nombre || 'Equipo';
    document.getElementById('confirmarEliminarEquipo_nombreEquipo').textContent = nombreEquipo;
    
    // Configurar botón de confirmar
    document.getElementById('btnConfirmarEliminarEquipo').onclick = confirmarEliminacionEquipo;
    
    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminarEquipo'));
    modal.show();
}

/**
 * Confirma y ejecuta la eliminación de la asignación de equipo.
 * Hace una petición AJAX al backend y actualiza la tabla localmente.
 * Muestra mensaje de éxito/error.
 */
async function confirmarEliminacionEquipo() {
    if (!asignacionEquipoAEliminar) return;
    
    // Cerrar modal de confirmación
    const modalElement = document.getElementById('modalConfirmarEliminarEquipo');
    const modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) {
        modalInstance.hide();
    }
    
    try {
        const response = await fetch('/calendario/api/eliminar-asignacion-equipo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ asignacion_id: asignacionEquipoAEliminar })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            mostrarAlerta(result.message || 'Asignación eliminada correctamente', 'success');
            
            // Eliminar de los datos locales
            const index = faena.asignaciones.findIndex(a => a.id === asignacionEquipoAEliminar);
            if (index !== -1) {
                faena.asignaciones.splice(index, 1);
            }
            
            // Re-renderizar la tabla dinámicamente
            renderizarEquiposAsignados();
            
            // Limpiar variable
            asignacionEquipoAEliminar = null;
        } else {
            mostrarAlerta(result.error || 'Error al eliminar asignación', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error de conexión: ' + error.message, 'error');
    }
}

// ============================================================================
// ALERTAS
// ============================================================================

// Función para mostrar alertas flotantes en la esquina superior derecha
// Crea un contenedor de mensajes si no existe y muestra un alert que se cierra automáticamente
// Parámetros:
//   mensaje: String - Texto del mensaje a mostrar
//   tipo: String - Tipo de alerta ('success' para éxito, 'error' para error)
function mostrarAlerta(mensaje, tipo) {
    // Crear contenedor de alertas flotantes si no existe
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
            // Si no hay más alertas, remover el contenedor
            if (container.children.length === 0) {
                container.remove();
            }
        }, 150);
    }, 5000);
}

