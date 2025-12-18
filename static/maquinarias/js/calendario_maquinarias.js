// ============================================================================
// CALENDARIO DE MAQUINARIAS
// ============================================================================
// Este archivo maneja la visualización del calendario de equipos con sus estados y órdenes de trabajo.
// Genera una tabla calendario donde cada fila es un equipo y cada columna es un día del mes.
// Muestra estados calculados del backend (OT, estado manual, asignación a faena) con colores.

// Variables globales para el estado del calendario
// Estas variables mantienen los datos filtrados y el estado de la aplicación
let equiposFiltrados = [];  // Array de equipos filtrados según los filtros aplicados
let ordenesFiltradas = [];  // Array de órdenes de trabajo filtradas (actualmente no se usa para filtrar, solo para mostrar)

// Función wrapper para inicializar calendario de operaciones con IDs correctos
// Esta función adapta el calendario de operaciones para que funcione con IDs específicos del tab
// Cambia temporalmente los IDs de los elementos para que el script del calendario funcione correctamente
function inicializarCalendarioOperaciones() {
    // Paso 1: Validar que la función generateCalendar esté disponible
    // Esta función viene de otro script (probablemente calendario_operaciones.js)
    if (typeof generateCalendar !== 'function') {
        console.warn('generateCalendar no está disponible');  // Advertir si no está disponible
        return;  // Salir sin hacer nada
    }
    
    // Paso 2: Obtener referencias a los elementos del tab de operaciones
    const headerOperaciones = document.getElementById('calendarHeaderOperaciones');  // Header del calendario de operaciones
    const bodyOperaciones = document.getElementById('calendarBodyOperaciones');  // Body del calendario de operaciones
    
    // Validar que los elementos existan
    if (!headerOperaciones || !bodyOperaciones) {
        console.warn('Elementos del calendario de operaciones no encontrados');  // Advertir si no existen
        return;  // Salir sin hacer nada
    }
    
    // Paso 3: Guardar IDs originales antes de cambiarlos temporalmente
    // Esto permite restaurarlos después de usar el script del calendario
    const originalHeaderId = headerOperaciones.id;  // Guardar ID original del header
    const originalBodyId = bodyOperaciones.id;  // Guardar ID original del body
    
    // Paso 4: Cambiar temporalmente los IDs para que el script del calendario funcione
    // El script generateCalendar busca elementos con IDs específicos ('calendarHeader' y 'calendarBody')
    headerOperaciones.id = 'calendarHeader';  // Cambiar a ID esperado por el script
    bodyOperaciones.id = 'calendarBody';  // Cambiar a ID esperado por el script
    
    // Paso 5: Llamar a la función de generación del calendario y funciones relacionadas
    try {
        // Paso 5.1: Generar el calendario usando la función externa
        generateCalendar();
        
        // Paso 5.2: Configurar filtros si la función existe
        // setupFilters viene del script del calendario de operaciones
        if (typeof setupFilters === 'function') {
            setupFilters();  // Configurar filtros del calendario de operaciones
        }
        
        // Paso 5.3: Limpiar y generar leyenda de estados si la función existe
        // generateStatusLegend viene del script del calendario de operaciones
        if (typeof generateStatusLegend === 'function') {
            // Limpiar la leyenda antes de regenerarla para evitar duplicados
            const legendContainer = document.getElementById('statusLegend');
            if (legendContainer) {
                // Guardar solo el texto base "Estados:" y limpiar el resto
                legendContainer.innerHTML = '<small class="me-2 fw-bold">Estados:</small>';
            }
            generateStatusLegend();  // Regenerar leyenda de estados
        }
    } catch (error) {
        // CASO EXCEPCIÓN: Error al generar calendario o funciones relacionadas
        console.error('Error al generar calendario de operaciones:', error);  // Registrar error en consola
    }
    
    // Paso 6: Restaurar los IDs originales después de usar el script
    // Esto evita conflictos con otros elementos que puedan usar los mismos IDs
    headerOperaciones.id = originalHeaderId;  // Restaurar ID original del header
    bodyOperaciones.id = originalBodyId;  // Restaurar ID original del body
}

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Inicializar calendario de maquinarias directamente
    // Esta función carga los equipos y genera el calendario inicial
    inicializarCalendarioMaquinarias();
    
    // Paso 2: Configurar event listeners para filtros de maquinarias
    // Estos listeners reaccionan a cambios en los campos de búsqueda y filtros
    const searchInputMaquinarias = document.getElementById('searchInputMaquinarias');  // Campo de búsqueda
    const empresaFilterMaquinarias = document.getElementById('empresaFilterMaquinarias');  // Filtro de empresa
    const faenaFilterMaquinarias = document.getElementById('faenaFilterMaquinarias');  // Filtro de faena
    
    // Paso 2.1: Filtro de búsqueda: filtrar localmente sin recargar página (como tabla de personal)
    // Filtrado instantáneo sin bloqueos
    if (searchInputMaquinarias) {
        searchInputMaquinarias.addEventListener('input', function() {
            filtrarEquiposLocalmente();
        });
    }
    
    // Paso 2.2: Filtros de empresa y faena: recargar página
    // Estos filtros requieren consulta al backend porque pueden afectar qué equipos se cargan
    if (empresaFilterMaquinarias) {
        empresaFilterMaquinarias.addEventListener('change', aplicarFiltrosMaquinarias);  // Recargar con filtro de empresa
    }
    if (faenaFilterMaquinarias) {
        faenaFilterMaquinarias.addEventListener('change', aplicarFiltrosMaquinarias);  // Recargar con filtro de faena
    }
});


// Función para inicializar el calendario de maquinarias
// Carga los equipos y órdenes de trabajo desde las variables globales definidas en el template
// Verifica la disponibilidad de estados calculados y genera el calendario inicial
function inicializarCalendarioMaquinarias() {
    // Paso 1: Copiar arrays de equipos y órdenes de trabajo a variables locales
    // window.equipos y window.ordenesTrabajo se definen en el template HTML
    // Usar spread operator para crear copias independientes (evita mutaciones accidentales)
    equiposFiltrados = [...window.equipos];  // Copiar equipos disponibles
    ordenesFiltradas = [...window.ordenesTrabajo];  // Copiar órdenes de trabajo disponibles
    
    // Paso 2: Debug: verificar que los estados calculados estén disponibles
    // window.estadosCalculados contiene los estados pre-calculados del backend para cada equipo y día
    if (window.estadosCalculados) {
        console.log('Estados calculados disponibles:', Object.keys(window.estadosCalculados).length, 'equipos');
        // Mostrar estructura completa del primer equipo para debug
        const primerEquipoId = Object.keys(window.estadosCalculados)[0];
        if (primerEquipoId) {
            console.log('Primer equipo ID:', primerEquipoId);
            console.log('Días con estados para primer equipo:', Object.keys(window.estadosCalculados[primerEquipoId]));
            const primerDia = Object.keys(window.estadosCalculados[primerEquipoId])[0];
            if (primerDia) {
                console.log('Estado para primer día:', window.estadosCalculados[primerEquipoId][primerDia]);
            }
        }
    } else {
        console.warn('No hay estados calculados disponibles');  // Advertir si no hay estados
    }
    
    // Paso 3: Generar el calendario con los equipos cargados
    // Los equipos ya vienen filtrados del backend si hay parámetros en la URL
    // Solo generamos el calendario con los equipos cargados
    generarCalendarioMaquinarias();
}

// Función principal para generar el calendario de maquinarias
// Crea una tabla donde cada fila es un equipo y cada columna es un día del mes
// Muestra estados calculados del backend con colores y permite hacer clic para ver detalles
function generarCalendarioMaquinarias() {
    // Paso 1: Obtener año y mes actuales desde variables globales
    // window.currentYear y window.currentMonth se definen en el template HTML
    const year = window.currentYear;  // Año actual (ej: 2024)
    const month = window.currentMonth - 1;  // Mes actual (JavaScript usa 0-11 para meses, por eso -1)
    
    // Paso 2: Calcular información del mes
    const daysInMonth = new Date(year, month + 1, 0).getDate();  // Cantidad de días en el mes
    const today = new Date();  // Fecha de hoy para marcar el día actual
    
    // Paso 3: Definir nombres abreviados de los días de la semana
    const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    
    // Paso 4: Generar encabezado del calendario (días del mes)
    const headerRow = document.getElementById('calendarHeaderMaquinarias');
    if (!headerRow) return;  // Si no existe el elemento, salir sin hacer nada
    
    // Paso 4.1: Iniciar HTML del header con columna sticky para nombres de equipos
    let headerHTML = '<th class="sticky-col">Equipo</th>';
    
    // Paso 4.2: Generar columna para cada día del mes
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);  // Crear fecha para este día
        const dayOfWeek = date.getDay();  // Día de la semana (0=Domingo, 6=Sábado)
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;  // Verificar si es fin de semana
        const isToday = date.toDateString() === today.toDateString();  // Verificar si es hoy
        
        // Paso 4.3: Construir clases CSS según el tipo de día
        let classes = [];
        if (isWeekend) classes.push('weekend');  // Agregar clase para fin de semana
        if (isToday) classes.push('today');  // Agregar clase para día actual
        
        // Paso 4.4: Generar HTML de la columna del día
        headerHTML += `<th class="${classes.join(' ')}" title="${dayNames[dayOfWeek]} ${day}">
            <div>${day}</div>
            <small style="font-size: 0.7rem;">${dayNames[dayOfWeek]}</small>
        </th>`;
    }
    
    // Paso 4.5: Insertar HTML del header en el DOM
    headerRow.innerHTML = headerHTML;
    
    // Paso 5: Generar filas del calendario (una fila por cada equipo)
    const tbody = document.getElementById('calendarBodyMaquinarias');
    if (!tbody) return;  // Si no existe el elemento, salir sin hacer nada
    
    let bodyHTML = '';  // Variable para acumular el HTML de las filas
    
    // Paso 5.1: Generar una fila para cada equipo filtrado
    equiposFiltrados.forEach(equipo => {
        bodyHTML += '<tr>';  // Iniciar fila del equipo
        
        // Paso 5.2: Generar columna de nombre del equipo (sticky, siempre visible al hacer scroll horizontal)
        // Construir información de tipo, marca y modelo para mostrar en la columna
        const tipoInfo = [];
        if (equipo.tipoEquipo) tipoInfo.push(equipo.tipoEquipo.toUpperCase());  // Tipo en mayúsculas
        if (equipo.marcaEquipo) tipoInfo.push(equipo.marcaEquipo);  // Marca
        if (equipo.modeloEquipo) tipoInfo.push(equipo.modeloEquipo);  // Modelo
        const tipoMarcaModelo = tipoInfo.length > 0 ? tipoInfo.join(' - ') : '';  // Unir con guiones
        
        // Generar HTML de la columna sticky con información del equipo (clickeable para ver detalles)
        bodyHTML += `<td class="sticky-col">
            <div class="equipo-name-container">
                <div class="equipo-info" onclick="mostrarDetalleEquipo(${equipo.equipo_id})" 
                     style="cursor: pointer; text-align: left;" 
                     title="Click para ver información del equipo">
                    <div style="font-size: 0.75rem; font-weight: 600; text-align: left;">${equipo.nombreEquipo}</div>
                    <small style="color: #fd7e14; font-style: italic; font-size: 0.65rem; text-align: left; display: block;">${tipoMarcaModelo || 'Sin información'}</small>
                    <small style="color: #6c757d; font-size: 0.65rem; text-align: left; display: block;">${equipo.empresa || 'Sin empresa'}</small>
                </div>
            </div>
        </td>`;
        
        // Paso 5.3: Generar celdas de días con estados calculados (una celda por cada día del mes)
        for (let day = 1; day <= daysInMonth; day++) {
            // Paso 5.3.1: Obtener estado calculado del backend para este equipo y día
            // Los estados están indexados por equipo_id como string y día como string
            let estado = null;
            const equipoIdStr = String(equipo.equipo_id);  // Convertir ID a string para acceso al objeto
            const dayStr = String(day);  // Convertir día a string para acceso al objeto
            
            // Buscar estado en window.estadosCalculados[equipoId][day]
            if (window.estadosCalculados && 
                window.estadosCalculados[equipoIdStr] && 
                window.estadosCalculados[equipoIdStr][dayStr]) {
                const estadosDelDia = window.estadosCalculados[equipoIdStr][dayStr];
                if (estadosDelDia && estadosDelDia.length > 0) {
                    estado = estadosDelDia[0];  // Tomar el primer estado (mayor prioridad)
                }
            }
            
            // Paso 5.3.2: Buscar órdenes de trabajo para este equipo y día
            // Esto permite mostrar información adicional al hacer clic en la celda
            const fechaActual = new Date(year, month, day);  // Crear fecha para este día
            const fechaISO = fechaActual.toISOString().split('T')[0];  // Convertir a formato ISO (YYYY-MM-DD)
            const otsDelDia = ordenesFiltradas.filter(ot => {
                // Filtrar OTs que pertenecen a este equipo y están activas en este día
                if (ot.equipo_id !== equipo.equipo_id) return false;  // Debe ser del mismo equipo
                // Verificar si la fecha está dentro del rango de la OT
                if (ot.fecha_inicio && ot.fecha_fin) {
                    // CASO: OT con rango de fechas -> verificar si la fecha está dentro del rango
                    return fechaISO >= ot.fecha_inicio.split('T')[0] && fechaISO <= ot.fecha_fin.split('T')[0];
                } else if (ot.fecha_inicio) {
                    // CASO: OT solo con fecha inicio -> verificar si coincide con la fecha
                    return fechaISO === ot.fecha_inicio.split('T')[0];
                } else if (ot.fecha_fin) {
                    // CASO: OT solo con fecha fin -> verificar si coincide con la fecha
                    return fechaISO === ot.fecha_fin.split('T')[0];
                }
                return false;  // Si no tiene fechas, no incluir
            });
            
            // Paso 5.3.3: Generar celda según si hay estado calculado o no
            if (estado) {
                // CASO: Hay estado calculado (viene de OT, estado manual o asignación a faena)
                const otId = otsDelDia.length > 0 ? otsDelDia[0].ot_id : null;  // ID de OT si existe
                
                // Paso 5.3.3.1: Buscar asignación a faena para este día
                // window.asignacionesFaena contiene las asignaciones de equipos a faenas
                const asignacionesDelDia = (window.asignacionesFaena || []).filter(asig => {
                    if (asig.equipo_id !== equipo.equipo_id) return false;  // Debe ser del mismo equipo
                    const fechaInicio = asig.fecha_inicio ? asig.fecha_inicio.split('T')[0] : null;  // Fecha inicio sin hora
                    const fechaFin = asig.fecha_fin ? asig.fecha_fin.split('T')[0] : null;  // Fecha fin sin hora
                    // Verificar si la fecha está dentro del rango de la asignación
                    if (fechaInicio && fechaFin) {
                        return fechaISO >= fechaInicio && fechaISO <= fechaFin;  // Dentro del rango
                    } else if (fechaInicio) {
                        return fechaISO >= fechaInicio;  // Desde fecha inicio (sin fin)
                    }
                    return false;  // Si no tiene fecha inicio, no incluir
                });
                
                // Paso 5.3.3.2: Determinar qué función ejecutar al hacer clic en la celda
                // Prioridad: OT > Asignación a faena > Estado general
                let onclickAttr = '';
                if (otId) {
                    // Si hay OT, mostrar detalle de la OT al hacer clic
                    onclickAttr = `onclick="mostrarDetalleOT(${otId})"`;
                } else if (asignacionesDelDia.length > 0) {
                    // Si hay asignación a faena, mostrar información del estado
                    onclickAttr = `onclick="showEstadoInfoEquipo(${equipo.equipo_id}, ${day})"`;
                } else {
                    // Si solo hay estado general, mostrar información del estado
                    onclickAttr = `onclick="showEstadoInfoEquipo(${equipo.equipo_id}, ${day})"`;
                }
                
                // Paso 5.3.3.3: Construir tooltip con información detallada para mostrar al pasar el mouse
                let tooltipText = estado.nombre || 'Sin nombre';  // Nombre del estado
                if (otsDelDia.length > 0) {
                    // Si hay OT, agregar información de la OT al tooltip
                    const ot = otsDelDia[0];
                    tooltipText += `\nOT: ${ot.folio}`;  // Folio de la OT
                    if (ot.estado_ot) {
                        tooltipText += `\nEstado OT: ${ot.estado_ot}`;  // Estado de la OT
                    }
                    if (ot.estado_equipo) {
                        tooltipText += `\nEstado Equipo: ${ot.estado_equipo}`;  // Estado del equipo
                    }
                } else if (asignacionesDelDia.length > 0) {
                    // Si hay asignación a faena, agregar nombre de la faena al tooltip
                    const asig = asignacionesDelDia[0];
                    tooltipText += `\nFaena: ${asig.faena_nombre}`;
                }
                
                // Paso 5.3.3.4: Generar HTML de la celda con estado (usar colores del estado)
                bodyHTML += `<td ${onclickAttr}
                                style="background-color: ${estado.background_color}; color: ${estado.color};"
                                title="${tooltipText.replace(/"/g, '&quot;')}">
                    <div class="estado-cell">${estado.nombre_corto}</div>
                </td>`;
            } else {
                // CASO: Sin estado calculado -> mostrar estado predeterminado si existe
                const estadoPred = window.estadoPredeterminado;  // Estado por defecto (ej: "Disponible")
                if (estadoPred) {
                    // Si hay estado predeterminado, mostrar celda con ese estado
                    bodyHTML += `<td onclick="showEstadoInfoEquipo(${equipo.equipo_id}, ${day})"
                                    style="background-color: ${estadoPred.background_color}; color: ${estadoPred.color};"
                                    title="${estadoPred.nombre}">
                        <div class="estado-cell">${estadoPred.nombre_corto}</div>
                    </td>`;
                } else {
                    // Si no hay estado predeterminado, mostrar celda vacía
                    bodyHTML += `<td class="empty-cell" onclick="showEstadoInfoEquipo(${equipo.equipo_id}, ${day})"></td>`;
                }
            }
        }
        
        bodyHTML += '</tr>';  // Cerrar fila del equipo
    });
    
    // Paso 6: Insertar el HTML generado en el tbody del calendario
    tbody.innerHTML = bodyHTML;
}

// Nota: Los colores de estados ahora vienen de los estados calculados del backend
// No se necesita función adicional para determinar colores

// Función para filtrar equipos localmente sin recargar la página
// Similar a la tabla de personal, filtra los equipos ya cargados en memoria según criterios de búsqueda
// Solo funciona con el campo de búsqueda; los filtros de empresa y faena requieren recarga de página
function filtrarEquiposLocalmente() {
    // Paso 1: Obtener valores de los filtros del formulario
    const search = document.getElementById('searchInputMaquinarias')?.value || '';  // Término de búsqueda
    const empresa = document.getElementById('empresaFilterMaquinarias')?.value || '';  // ID de empresa (no se usa en filtro local)
    const faena = document.getElementById('faenaFilterMaquinarias')?.value || '';  // Nombre de faena (no se usa en filtro local)
    
    // Paso 2: Validar que window.equipos esté disponible
    if (!window.equipos || !Array.isArray(window.equipos)) {
        console.error('window.equipos no está disponible o no es un array');
        return;
    }
    
    // Paso 3: Filtrar equipos localmente basándose en el texto de búsqueda
    // Convertir término de búsqueda a minúsculas y eliminar espacios en blanco
    const searchTrimmed = search.trim();
    const searchLower = searchTrimmed.toLowerCase();
    
    // Paso 4: Filtrar equipos según criterios de búsqueda
    equiposFiltrados = window.equipos.filter(equipo => {
        // Paso 4.1: Búsqueda por nombre, código interno o modelo
        // Si no hay búsqueda, incluir todos los equipos
        let matchBusqueda = true;
        if (searchLower) {
            // Si hay búsqueda, verificar si alguno de los campos contiene el término
            const nombreMatch = equipo.nombreEquipo ? equipo.nombreEquipo.toLowerCase().includes(searchLower) : false;
            const codigoMatch = equipo.codigoInterno ? equipo.codigoInterno.toLowerCase().includes(searchLower) : false;
            const modeloMatch = equipo.modeloEquipo ? equipo.modeloEquipo.toLowerCase().includes(searchLower) : false;
            matchBusqueda = nombreMatch || codigoMatch || modeloMatch;
        }
        
        // Paso 4.2: Filtro de empresa (si está seleccionado)
        // El equipo coincide si no hay filtro de empresa o si su empresa coincide
        const matchEmpresa = !empresa || (equipo.empresa && equipo.empresa === empresa);
        
        // Paso 4.3: Filtro de faena (si está seleccionado)
        // Este filtro requiere buscar en las asignaciones a faenas que estén activas en el mes actual
        let matchFaena = true;  // Por defecto, todos los equipos coinciden
        if (faena) {
            // Obtener rango de fechas del mes actual
            const fechaInicioMes = window.fechaInicioMes ? new Date(window.fechaInicioMes) : null;
            const fechaFinMes = window.fechaFinMes ? new Date(window.fechaFinMes) : null;
            
            // Obtener asignaciones del equipo desde window.asignacionesFaena
            const asignacionesEquipo = (window.asignacionesFaena || []).filter(asig => {
                // Filtrar solo asignaciones de este equipo
                if (asig.equipo_id !== equipo.equipo_id) return false;
                
                // Verificar que la asignación esté activa en el mes actual
                if (fechaInicioMes && fechaFinMes) {
                    const fechaInicioAsig = asig.fecha_inicio ? new Date(asig.fecha_inicio.split('T')[0]) : null;
                    const fechaFinAsig = asig.fecha_fin ? new Date(asig.fecha_fin.split('T')[0]) : null;
                    
                    // La asignación está activa si:
                    // - Comienza antes o en el último día del mes Y
                    // - Termina después o en el primer día del mes, o no tiene fecha fin
                    if (fechaInicioAsig) {
                        const comienzaAntesDelFin = fechaInicioAsig <= fechaFinMes;
                        const terminaDespuesDelInicio = !fechaFinAsig || fechaFinAsig >= fechaInicioMes;
                        return comienzaAntesDelFin && terminaDespuesDelInicio;
                    }
                }
                return false;
            });
            
            if (faena === 'Sin asignar') {
                // CASO: Buscar equipos sin asignaciones activas en el mes actual
                matchFaena = asignacionesEquipo.length === 0;  // No tiene asignaciones activas
            } else {
                // CASO: Buscar equipos con asignación activa a la faena específica
                matchFaena = asignacionesEquipo.some(asig => asig.faena_nombre === faena);  // Tiene asignación activa a esta faena
            }
        }
        
        // Paso 4.4: El equipo se incluye si cumple todos los criterios
        return matchBusqueda && matchEmpresa && matchFaena;
    });
    
    // Paso 5: Re-renderizar calendario con equipos filtrados
    // Esto actualiza la tabla sin recargar la página
    console.log(`Filtrado: ${equiposFiltrados.length} de ${window.equipos.length} equipos`);  // Debug
    generarCalendarioMaquinarias();
}

// Función para aplicar filtros al calendario de maquinarias (recarga página)
// Los filtros de empresa y faena requieren consulta al backend, por lo que se recarga la página
// Mantiene los parámetros de fecha y paginación al recargar
function aplicarFiltrosMaquinarias() {
    // Paso 1: Obtener valores de los filtros del formulario
    const search = document.getElementById('searchInputMaquinarias')?.value || '';  // Término de búsqueda
    const empresa = document.getElementById('empresaFilterMaquinarias')?.value || '';  // ID de empresa para filtrar
    const faena = document.getElementById('faenaFilterMaquinarias')?.value || '';  // Nombre de faena para filtrar
    
    // Paso 2: Construir URL con filtros y recargar página
    // Crear objeto URL desde la URL actual para modificar parámetros
    const url = new URL(window.location.href);
    
    // Paso 3: Mantener parámetros de fecha y paginación existentes
    const year = url.searchParams.get('year') || window.currentYear;  // Año actual o de la URL
    const month = url.searchParams.get('month') || window.currentMonth;  // Mes actual o de la URL
    const pageSize = url.searchParams.get('page_size') || window.pageSize || '25';  // Tamaño de página
    
    // Limpiar y reconstruir todos los parámetros (resetear página a 1 al aplicar filtros)
    url.search = '';
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    url.searchParams.set('page', '1');  // Resetear a página 1 al aplicar filtros
    url.searchParams.set('page_size', pageSize);
    
    // Paso 4: Agregar o eliminar filtros de la URL según sus valores
    if (search) {
        url.searchParams.set('search', search);  // Agregar filtro de búsqueda si tiene valor
    } else {
        url.searchParams.delete('search');  // Eliminar filtro si está vacío
    }
    
    if (empresa) {
        url.searchParams.set('empresa', empresa);  // Agregar filtro de empresa si tiene valor
    } else {
        url.searchParams.delete('empresa');  // Eliminar filtro si está vacío
    }
    
    if (faena) {
        url.searchParams.set('faena', faena);  // Agregar filtro de faena si tiene valor
    } else {
        url.searchParams.delete('faena');  // Eliminar filtro si está vacío
    }
    
    // Paso 6: Recargar página con los nuevos filtros
    // Esto hace que el backend recargue los equipos con los filtros aplicados
    window.location.href = url.toString();
}

// Función para limpiar todos los filtros del calendario de maquinarias
// Elimina todos los parámetros de filtro de la URL y recarga la página
// Mantiene solo los parámetros de fecha y paginación
function clearFiltersMaquinarias() {
    // Paso 1: Construir URL desde la URL actual
    const url = new URL(window.location.href);
    
    // Paso 2: Obtener parámetros que se deben mantener (fecha y paginación)
    const year = url.searchParams.get('year') || window.currentYear;  // Año actual
    const month = url.searchParams.get('month') || window.currentMonth;  // Mes actual
    const pageSize = url.searchParams.get('page_size') || window.pageSize || '25';  // Tamaño de página
    
    // Paso 3: Limpiar todos los parámetros y reconstruir URL solo con fecha y paginación
    url.search = '';  // Limpiar todos los parámetros de búsqueda
    url.searchParams.set('year', year);  // Agregar año
    url.searchParams.set('month', month);  // Agregar mes
    url.searchParams.set('page', '1');  // Resetear a página 1
    url.searchParams.set('page_size', pageSize);  // Mantener tamaño de página
    
    // Paso 4: Recargar página sin filtros
    window.location.href = url.toString();
}

// Función para cambiar el tamaño de página (cantidad de equipos por página)
// Actualiza el parámetro page_size en la URL y recarga la página
// Mantiene todos los demás parámetros (fecha, filtros, etc.)
// Parámetros:
//   newSize: Nuevo tamaño de página (ej: '10', '25', '50')
function cambiarTamanioPaginaMaquinarias(newSize) {
    // Paso 1: Construir URL desde la URL actual
    const url = new URL(window.location.href);
    
    // Paso 2: Obtener parámetros actuales que se deben mantener
    const year = url.searchParams.get('year') || window.currentYear;  // Año
    const month = url.searchParams.get('month') || window.currentMonth;  // Mes
    const search = url.searchParams.get('search') || '';  // Búsqueda
    const empresa = url.searchParams.get('empresa') || '';  // Empresa
    const estado = url.searchParams.get('estado') || '';  // Estado (si existe)
    
    // Paso 3: Limpiar parámetros y reconstruir URL con el nuevo tamaño de página
    url.search = '';  // Limpiar todos los parámetros
    url.searchParams.set('year', year);  // Agregar año
    url.searchParams.set('month', month);  // Agregar mes
    url.searchParams.set('page', '1');  // Resetear a página 1 al cambiar tamaño
    url.searchParams.set('page_size', newSize);  // Establecer nuevo tamaño de página
    
    // Paso 4: Agregar filtros si tienen valores
    if (search) url.searchParams.set('search', search);
    if (empresa) url.searchParams.set('empresa', empresa);
    if (estado) url.searchParams.set('estado', estado);
    
    // Paso 5: Recargar página con el nuevo tamaño de página
    window.location.href = url.toString();
}

// Función helper para formatear fecha a formato chileno largo y legible
// Convierte fechas del formato ISO al formato "Día de la semana, día de mes de año"
// Ejemplo: "Lunes, 15 de enero de 2024"
// Parámetros:
//   fecha: String con la fecha en formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
// Retorna:
//   String con la fecha formateada en formato largo chileno, o string vacío si no hay fecha
function formatearFechaChilenaLarga(fecha) {
    if (!fecha) return '';  // Si no hay fecha, retornar string vacío
    
    try {
        // Paso 1: Crear objeto Date desde el string ISO
        const date = new Date(fecha);
        
        // Paso 2: Definir arrays con nombres de días y meses en español
        const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
        const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
        
        // Paso 3: Extraer componentes de la fecha
        const diaSemana = diasSemana[date.getDay()];  // Nombre del día de la semana
        const dia = date.getDate();  // Día del mes (1-31)
        const mes = meses[date.getMonth()];  // Nombre del mes
        const anio = date.getFullYear();  // Año completo
        
        // Paso 4: Retornar fecha formateada en formato largo chileno
        return `${diaSemana}, ${dia} de ${mes} de ${anio}`;
    } catch (error) {
        // CASO EXCEPCIÓN: Error al parsear o formatear la fecha
        console.error('Error formateando fecha:', error);  // Registrar error en consola
        return fecha;  // Retornar fecha original si hay error
    }
}

// Función helper para formatear fecha a formato chileno corto (DD-MM-YYYY)
// Convierte fechas del formato ISO al formato DD-MM-YYYY más legible
// Parámetros:
//   fecha: String con la fecha en formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
// Retorna:
//   String con la fecha formateada en formato DD-MM-YYYY, o string vacío si no hay fecha
function formatearFechaChilena(fecha) {
    if (!fecha) return '';  // Si no hay fecha, retornar string vacío
    
    try {
        // Paso 1: Crear objeto Date desde el string ISO
        // Agregar 'T00:00:00' si solo tiene fecha para crear una fecha válida a medianoche
        const date = new Date(fecha + 'T00:00:00');
        
        // Paso 2: Extraer componentes de la fecha y formatearlos
        const dia = String(date.getDate()).padStart(2, '0');  // Día con cero a la izquierda si es necesario
        const mes = String(date.getMonth() + 1).padStart(2, '0');  // Mes (getMonth() es 0-based, por eso +1)
        const anio = date.getFullYear();  // Año completo
        
        // Paso 3: Retornar fecha formateada en formato DD-MM-YYYY
        return `${dia}-${mes}-${anio}`;
    } catch (error) {
        // CASO EXCEPCIÓN: Error al parsear o formatear la fecha
        console.error('Error formateando fecha:', error);  // Registrar error en consola
        return fecha;  // Retornar fecha original si hay error
    }
}

// Mostrar información de estado del equipo (similar a showEstadoInfo del calendario de personal)
function showEstadoInfoEquipo(equipoId, day) {
    const equipo = window.equipos.find(e => e.equipo_id === equipoId);
    if (!equipo) return;
    
    const nombreEquipo = equipo.nombreEquipo || 'Sin nombre';
    const fecha = new Date(window.currentYear, window.currentMonth - 1, day);
    const fechaISO = fecha.toISOString().split('T')[0];
    
    // Obtener estado calculado del backend
    let estado = null;
    const equipoIdStr = String(equipoId);
    const dayStr = String(day);
    
    if (window.estadosCalculados && 
        window.estadosCalculados[equipoIdStr] && 
        window.estadosCalculados[equipoIdStr][dayStr]) {
        const estadosDelDia = window.estadosCalculados[equipoIdStr][dayStr];
        if (estadosDelDia && estadosDelDia.length > 0) {
            estado = estadosDelDia[0];
        }
    }
    
    // Si no hay estado, usar el predeterminado
    if (!estado && window.estadoPredeterminado) {
        estado = window.estadoPredeterminado;
    }
    
    // Buscar OT del día
    const otsDelDia = (window.ordenesTrabajo || []).filter(ot => {
        if (ot.equipo_id !== equipoId) return false;
        if (ot.fecha_inicio && ot.fecha_fin) {
            return fechaISO >= ot.fecha_inicio.split('T')[0] && fechaISO <= ot.fecha_fin.split('T')[0];
        } else if (ot.fecha_inicio) {
            return fechaISO === ot.fecha_inicio.split('T')[0];
        } else if (ot.fecha_fin) {
            return fechaISO === ot.fecha_fin.split('T')[0];
        }
        return false;
    });
    
    // Buscar asignación a faena del día
    const asignacionesDelDia = (window.asignacionesFaena || []).filter(asig => {
        if (asig.equipo_id !== equipoId) return false;
        const fechaInicio = asig.fecha_inicio ? asig.fecha_inicio.split('T')[0] : null;
        const fechaFin = asig.fecha_fin ? asig.fecha_fin.split('T')[0] : null;
        if (fechaInicio && fechaFin) {
            return fechaISO >= fechaInicio && fechaISO <= fechaFin;
        } else if (fechaInicio) {
            return fechaISO >= fechaInicio;
        }
        return false;
    });
    
    // Determinar asignación actual
    let asignacionTexto = 'Disponible';
    let periodoTexto = '-';
    let otActual = null;
    
    if (otsDelDia.length > 0) {
        otActual = otsDelDia[0];
        asignacionTexto = `OT: ${otActual.folio}`;
        if (otActual.fecha_inicio && otActual.fecha_fin) {
            periodoTexto = `${formatearFechaChilena(otActual.fecha_inicio)} → ${formatearFechaChilena(otActual.fecha_fin)}`;
        } else if (otActual.fecha_inicio) {
            periodoTexto = `Desde ${formatearFechaChilena(otActual.fecha_inicio)}`;
        }
    } else if (asignacionesDelDia.length > 0) {
        const asig = asignacionesDelDia[0];
        asignacionTexto = asig.faena_nombre || 'Faena asignada';
        if (asig.fecha_inicio && asig.fecha_fin) {
            periodoTexto = `${formatearFechaChilena(asig.fecha_inicio)} → ${formatearFechaChilena(asig.fecha_fin)}`;
        } else if (asig.fecha_inicio) {
            periodoTexto = `Desde ${formatearFechaChilena(asig.fecha_inicio)}`;
        }
    }
    
    // Llenar modal
    document.getElementById('modalEquipoNombre').textContent = nombreEquipo;
    document.getElementById('modalEquipoFecha').textContent = formatearFechaChilenaLarga(fechaISO);
    
    // Mostrar estado con badge si hay OT, sino mostrar solo texto
    const estadoElement = document.getElementById('modalEquipoEstado');
    if (otActual && (otActual.estado_ot || otActual.estado_equipo)) {
        // Si hay OT, mostrar badges con estados
        const estadoOTColors = getColorEstadoOT(otActual.estado_ot);
        const estadoEquipoColors = getColorEstadoEquipo(otActual.estado_equipo);
        
        // Forzar texto blanco con estilo inline cuando corresponda
        const estadoOTStyle = estadoOTColors.text === 'text-white' ? 'style="color: #ffffff !important;"' : '';
        const estadoEquipoStyle = estadoEquipoColors.text === 'text-white' ? 'style="color: #ffffff !important;"' : '';
        
        let estadoHTML = '';
        if (otActual.estado_ot) {
            estadoHTML += `<span class="badge bg-${estadoOTColors.bg} ${estadoOTColors.text} me-2" ${estadoOTStyle}>${otActual.estado_ot}</span>`;
        }
        if (otActual.estado_equipo) {
            estadoHTML += `<span class="badge bg-${estadoEquipoColors.bg} ${estadoEquipoColors.text}" ${estadoEquipoStyle}>${otActual.estado_equipo}</span>`;
        }
        estadoElement.innerHTML = estadoHTML || (estado ? estado.nombre : 'Sin estado');
    } else {
        // Si no hay OT, mostrar solo el nombre del estado
        estadoElement.textContent = estado ? estado.nombre : 'Sin estado';
    }
    
    document.getElementById('modalEquipoAsignacion').textContent = asignacionTexto;
    document.getElementById('modalEquipoPeriodo').textContent = periodoTexto;
    
    // Mostrar detalles adicionales si existen
    const detallesDiv = document.getElementById('modalEquipoDetallesEstado');
    detallesDiv.innerHTML = '';
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('estadoEquipoModal'));
    modal.show();
}

function mostrarDetalleEquipo(equipoId) {
    const equipo = window.equipos.find(e => e.equipo_id === equipoId);
    if (!equipo) return;
    
    const modalBody = document.getElementById('equipoModalBody');
    if (!modalBody) return;
    
    // Obtener asignaciones a faenas del equipo
    const asignacionesEquipo = (window.asignacionesFaena || []).filter(asig => asig.equipo_id === equipoId);
    
    // Crear estructura con tabs simplificada (estilo del proyecto)
    modalBody.innerHTML = `
        <!-- Nav tabs -->
        <ul class="nav nav-tabs mb-3" id="equipoTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="info-tab" data-bs-toggle="tab" data-bs-target="#info-pane" type="button" role="tab" aria-controls="info-pane" aria-selected="true">
                    <i class="bi bi-info-circle me-1"></i>Información
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="documentacion-tab" data-bs-toggle="tab" data-bs-target="#documentacion-pane" type="button" role="tab" aria-controls="documentacion-pane" aria-selected="false" data-equipo-id="${equipoId}">
                    <i class="bi bi-folder me-1"></i>Documentación
                </button>
            </li>
        </ul>
        
        <!-- Tab panes -->
        <div class="tab-content" id="equipoTabContent">
            <!-- Tab: Información -->
            <div class="tab-pane fade show active" id="info-pane" role="tabpanel" aria-labelledby="info-tab">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-info-circle me-2 text-primary"></i>Información General</h6>
                            </div>
                            <div class="card-body p-0">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Nombre:</th>
                                            <td><strong>${equipo.nombreEquipo}</strong></td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Código Interno:</th>
                                            <td>${equipo.codigoInterno || 'N/A'}</td>
                                        </tr>
                                        ${equipo.patente ? `
                                        <tr>
                                            <th class="bg-light">Patente:</th>
                                            <td>${equipo.patente}</td>
                                        </tr>
                                        ` : ''}
                                        <tr>
                                            <th class="bg-light">Empresa:</th>
                                            <td>${equipo.empresa || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Tipo:</th>
                                            <td>${equipo.tipoEquipo || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Marca:</th>
                                            <td>${equipo.marcaEquipo || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Modelo:</th>
                                            <td>${equipo.modeloEquipo || 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card border">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 fw-bold"><i class="bi bi-speedometer2 me-2 text-success"></i>Horómetros y Odómetro</h6>
                            </div>
                            <div class="card-body p-0">
                                <table class="table table-sm table-bordered mb-0">
                                    <tbody>
                                        <tr>
                                            <th style="width: 40%;" class="bg-light">Horómetro:</th>
                                            <td>${equipo.horometro ? equipo.horometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Odómetro:</th>
                                            <td>${equipo.odometro ? equipo.odometro.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="bg-light">Horómetro Superestructura:</th>
                                            <td>${equipo.horometroSuperEstructural ? equipo.horometroSuperEstructural.toLocaleString('es-CL') : 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                ${asignacionesEquipo.length > 0 ? `
                <div class="mt-3">
                    <h6 class="border-bottom pb-2 mb-3"><i class="bi bi-briefcase me-2"></i>Asignaciones a Faenas</h6>
                    <div class="list-group">
                        ${asignacionesEquipo.map(asig => {
                            const fechaInicio = formatearFechaChilena(asig.fecha_inicio);
                            const fechaFin = asig.fecha_fin ? formatearFechaChilena(asig.fecha_fin) : 'Sin fecha fin';
                            return `
                                <div class="list-group-item px-0 py-2">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div class="flex-grow-1 me-2">
                                            <div class="fw-bold small">${asig.faena_nombre || 'Faena sin nombre'}</div>
                                            <div class="text-muted" style="font-size: 0.75rem;">
                                                <i class="bi bi-calendar-range me-1"></i>${fechaInicio} → ${fechaFin}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                ` : `
                <div class="mt-3">
                    <h6 class="border-bottom pb-2 mb-3"><i class="bi bi-briefcase me-2"></i>Asignaciones a Faenas</h6>
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle me-2"></i>No hay asignaciones a faenas registradas.
                    </div>
                </div>
                `}
            </div>
            
            <!-- Tab: Documentación -->
            <div class="tab-pane fade" id="documentacion-pane" role="tabpanel" aria-labelledby="documentacion-tab">
                <div id="documentosContainer">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando documentación...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('equipoModal'));
    modal.show();
    
    // Agregar listener para cuando se active el tab de documentación
    const documentacionTab = document.getElementById('documentacion-tab');
    if (documentacionTab) {
        documentacionTab.addEventListener('shown.bs.tab', function (e) {
            const equipoId = e.target.getAttribute('data-equipo-id');
            if (equipoId) {
                cargarDocumentosEquipo(parseInt(equipoId));
            }
        });
    }
}

// Cargar documentos del equipo
async function cargarDocumentosEquipo(equipoId) {
    const container = document.getElementById('documentosContainer');
    if (!container) return;
    
    try {
        const response = await fetch(`/maquinarias/api/equipos/${equipoId}/documentos/`);
        const data = await response.json();
        
        if (data.success && data.documentos) {
            renderizarDocumentosEquipo(data.documentos, container);
        } else {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay documentación disponible para este equipo.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error al cargar documentos:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error al cargar la documentación. Por favor, intente nuevamente.
            </div>
        `;
    }
}

// Renderizar documentos del equipo en formato tabla simple (estilo del proyecto)
function renderizarDocumentosEquipo(documentos, container) {
    if (!documentos || documentos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                No hay documentación disponible para este equipo.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-sm table-hover table-bordered rrhh-table">
                <thead class="table-dark">
                    <tr>
                        <th>Tipo de Documento</th>
                        <th>Fecha Subida</th>
                        <th>Fecha Vencimiento</th>
                        <th>Estado</th>
                        <th class="text-center">Acciones</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    documentos.forEach(doc => {
        const fechaVencimiento = doc.fecha_vencimiento 
            ? new Date(doc.fecha_vencimiento).toLocaleDateString('es-CL')
            : 'N/A';
        const fechaSubida = new Date(doc.fecha_subida).toLocaleDateString('es-CL');
        
        let badgeEstado = '';
        if (doc.estado === 'vencido') {
            badgeEstado = '<span class="badge bg-danger">Vencido</span>';
        } else if (doc.estado === 'por_vencer') {
            badgeEstado = `<span class="badge bg-warning text-dark">Por vencer (${doc.dias_restantes} días)</span>`;
        } else {
            badgeEstado = '<span class="badge bg-success text-white">Vigente</span>';
        }
        
        const archivoLink = doc.archivo_url 
            ? `<a href="${doc.archivo_url}" target="_blank" class="btn btn-sm btn-primary" title="${doc.archivo_nombre || 'Ver documento'}">
                 <i class="bi bi-eye"></i>
               </a>`
            : '<span class="text-muted">N/A</span>';
        
        html += `
            <tr>
                <td><strong>${doc.tipo_documento_nombre}</strong></td>
                <td>${fechaSubida}</td>
                <td>${fechaVencimiento}</td>
                <td>${badgeEstado}</td>
                <td class="text-center">${archivoLink}</td>
            </tr>
        `;
        
        if (doc.observaciones) {
            html += `
                <tr>
                    <td colspan="5" class="small text-muted bg-light">
                        <strong>Observaciones:</strong> ${doc.observaciones}
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Función helper para obtener colores del badge según el estado de la OT
// Retorna un objeto con las clases CSS de Bootstrap para el fondo y el texto
// Parámetros:
//   estado: Nombre del estado de la OT (ej: "Pendiente", "En Proceso", "Finalizada")
// Retorna:
//   Objeto con propiedades 'bg' (clase de fondo) y 'text' (clase de texto)
function getColorEstadoOT(estado) {
    if (!estado) return { bg: 'secondary', text: 'text-white' };  // Color por defecto si no hay estado
    const estadoLower = estado.toLowerCase();  // Convertir a minúsculas para comparación
    if (estadoLower.includes('pendiente')) return { bg: 'secondary', text: 'text-white' };  // Gris con texto blanco
    if (estadoLower.includes('proceso') || estadoLower.includes('en proceso')) return { bg: 'success', text: 'text-white' };  // Verde con texto blanco
    if (estadoLower.includes('finalizada') || estadoLower.includes('terminada')) return { bg: 'dark', text: 'text-white' };  // Negro con texto blanco
    if (estadoLower.includes('cancelada')) return { bg: 'danger', text: 'text-white' };  // Rojo con texto blanco
    return { bg: 'secondary', text: 'text-white' };  // Color por defecto para otros estados
}

// Función helper para obtener colores del badge según el estado del equipo
// Retorna un objeto con las clases CSS de Bootstrap para el fondo y el texto
// Parámetros:
//   estado: Nombre del estado del equipo (ej: "Disponible", "En Reparación", "Shutdown")
// Retorna:
//   Objeto con propiedades 'bg' (clase de fondo) y 'text' (clase de texto)
function getColorEstadoEquipo(estado) {
    if (!estado) return { bg: 'secondary', text: 'text-white' };  // Color por defecto si no hay estado
    const estadoLower = estado.toLowerCase();  // Convertir a minúsculas para comparación
    if (estadoLower.includes('shutdown')) return { bg: 'danger', text: 'text-white' };  // Rojo con texto blanco
    if (estadoLower.includes('disponible') && !estadoLower.includes('reparación')) return { bg: 'success', text: 'text-dark' };  // Verde con texto negro
    if (estadoLower.includes('reparación') || estadoLower.includes('en reparación')) return { bg: 'dark', text: 'text-white' };  // Negro con texto blanco
    if (estadoLower.includes('operativo con anomalías') || estadoLower.includes('operativo con anomalias')) return { bg: 'warning', text: 'text-white' };  // Amarillo con texto blanco
    return { bg: 'secondary', text: 'text-white' };  // Color por defecto para otros estados
}

// Mostrar detalle de OT
function mostrarDetalleOT(otId) {
    const ot = window.ordenesTrabajo.find(o => o.ot_id === otId);
    if (!ot) return;
    
    const modalBody = document.getElementById('otModalBody');
    if (!modalBody) return;
    
    const fechaInicio = ot.fecha_inicio ? new Date(ot.fecha_inicio).toLocaleDateString('es-CL') : 'No definida';
    const fechaFin = ot.fecha_fin ? new Date(ot.fecha_fin).toLocaleDateString('es-CL') : 'No definida';
    const fechaCreacion = new Date(ot.fecha_creacion).toLocaleDateString('es-CL');
    
    const personalHTML = ot.personal_asignado && ot.personal_asignado.length > 0
        ? ot.personal_asignado.map(p => `<li>${p.nombre}</li>`).join('')
        : '<li class="text-muted">Sin personal asignado</li>';
    
    // Obtener colores de los estados
    const estadoOTColors = getColorEstadoOT(ot.estado_ot);
    const estadoEquipoColors = getColorEstadoEquipo(ot.estado_equipo);
    
    // Forzar texto blanco con estilo inline cuando corresponda
    const estadoOTStyle = estadoOTColors.text === 'text-white' ? 'style="color: #ffffff !important;"' : '';
    const estadoEquipoStyle = estadoEquipoColors.text === 'text-white' ? 'style="color: #ffffff !important;"' : '';
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <p><strong>Folio:</strong> ${ot.folio}</p>
                <p><strong>Equipo:</strong> ${ot.equipo_nombre}</p>
                <p><strong>Empresa:</strong> ${ot.empresa}</p>
                <p><strong>Tipo de Mantenimiento:</strong> ${ot.tipo_mantenimiento || 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Estado OT:</strong> <span class="badge bg-${estadoOTColors.bg} ${estadoOTColors.text}" ${estadoOTStyle}>${ot.estado_ot || 'N/A'}</span></p>
                <p><strong>Estado Equipo:</strong> <span class="badge bg-${estadoEquipoColors.bg} ${estadoEquipoColors.text}" ${estadoEquipoStyle}>${ot.estado_equipo || 'N/A'}</span></p>
                <p><strong>Fecha de Creación:</strong> ${fechaCreacion}</p>
                <p><strong>Fecha de Inicio:</strong> ${fechaInicio}</p>
                <p><strong>Fecha de Fin:</strong> ${fechaFin}</p>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <strong>Personal Asignado:</strong>
                <ul>
                    ${personalHTML}
                </ul>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('otModal'));
    modal.show();
}

// Función para navegar por el calendario (cambiar mes o año)
// Mantiene todos los filtros y parámetros de paginación al cambiar de mes/año
// Parámetros:
//   type: Tipo de navegación ('month' para cambiar mes, 'year' para cambiar año)
//   direction: Dirección de navegación (1 para avanzar, -1 para retroceder)
function navigateCalendar(type, direction) {
    // Paso 1: Obtener año y mes actuales desde variables globales
    let newYear = window.currentYear;  // Año actual
    let newMonth = window.currentMonth;  // Mes actual
    
    // Paso 2: Calcular nuevo año y mes según el tipo de navegación
    if (type === 'month') {
        // CASO: Navegación por mes
        newMonth += direction;  // Sumar o restar meses
        if (newMonth < 1) {
            // Si el mes es menor a 1, ir al mes 12 del año anterior
            newMonth = 12;
            newYear -= 1;
        } else if (newMonth > 12) {
            // Si el mes es mayor a 12, ir al mes 1 del año siguiente
            newMonth = 1;
            newYear += 1;
        }
    } else if (type === 'year') {
        // CASO: Navegación por año
        newYear += direction;  // Sumar o restar años
    }
    
    // Paso 3: Construir URL con parámetros actuales (mantener filtros y paginación)
    const url = new URL(window.location.href);
    url.searchParams.set('year', newYear);  // Establecer nuevo año
    url.searchParams.set('month', newMonth);  // Establecer nuevo mes
    url.searchParams.set('page', '1');  // Resetear a página 1 al cambiar mes/año
    
    // Paso 4: Recargar página con el nuevo mes/año
    window.location.href = url.toString();
}

// Función para navegar al mes actual (hoy)
// Establece el calendario al mes y año actuales
// Mantiene todos los filtros y parámetros de paginación
function goToToday() {
    // Paso 1: Obtener fecha de hoy
    const today = new Date();
    
    // Paso 2: Construir URL con el mes y año actuales
    const url = new URL(window.location.href);
    url.searchParams.set('year', today.getFullYear());  // Establecer año actual
    url.searchParams.set('month', today.getMonth() + 1);  // Establecer mes actual (getMonth() es 0-based)
    url.searchParams.set('page', '1');  // Resetear a página 1
    
    // Paso 3: Recargar página con el mes/año actual
    window.location.href = url.toString();
}

