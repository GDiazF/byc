// Variables globales
// Almacena todos los modelos de equipos cargados desde el servidor
// Se usa para filtrar marcas y modelos sin necesidad de hacer nuevas peticiones al servidor
let todosLosModelos = [];

// Inicialización cuando el DOM está completamente cargado
// Este evento asegura que todos los elementos HTML estén disponibles antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: Cargar todos los modelos de equipos desde el servidor
    // Esto permite tener todos los datos disponibles localmente para filtros en cascada
    cargarModelos();
    
    // Paso 2: Configurar el event listener para el envío del formulario
    // Cuando el usuario envía el formulario, se ejecutará la función guardarEquipo
    document.getElementById('equipoForm').addEventListener('submit', guardarEquipo);
    
    // Paso 3: Si estamos en modo edición, cargar los datos del equipo existente
    // window.equipoEdicion se define en el template HTML con los datos del equipo a editar
    if (window.equipoEdicion) {
        cargarDatosEdicion();
    }
});

// Función para cargar todos los modelos de equipos desde el servidor
// Esta función obtiene todos los modelos con sus relaciones (tipo y marca) en una sola petición
function cargarModelos() {
    // Realizar petición GET al endpoint de modelos
    fetch('/maquinarias/api/modelos-equipo/')
        .then(response => response.json())  // Convertir respuesta a JSON
        .then(data => {
            if (data.success) {
                // Paso 1: Guardar todos los modelos en la variable global
                // Esto permite acceder a los datos sin hacer más peticiones al servidor
                todosLosModelos = data.modelos;
                
                // Paso 2: Si estamos editando un equipo, precargar los valores en los selects
                // Se usan timeouts para asegurar que los selects estén listos antes de asignar valores
                if (window.equipoEdicion) {
                    setTimeout(() => {
                        // Establecer el tipo de equipo seleccionado
                        document.getElementById('tipoEquipo_id').value = window.equipoEdicion.tipo_id;
                        filtrarMarcasPorTipo();  // Filtrar marcas según el tipo seleccionado
                        
                        setTimeout(() => {
                            // Establecer la marca seleccionada
                            document.getElementById('marcaEquipo_id').value = window.equipoEdicion.marca_id;
                            filtrarModelosPorTipoYMarca();  // Filtrar modelos según tipo y marca
                            
                            setTimeout(() => {
                                // Establecer el modelo seleccionado y actualizar el preview del nombre
                                document.getElementById('modeloEquipo_id').value = window.equipoEdicion.modelo_id;
                                actualizarNombrePreview();  // Actualizar vista previa del nombre del equipo
                            }, 100);
                        }, 100);
                    }, 100);
                }
            }
        })
        .catch(error => console.error('Error al cargar modelos:', error));  // Manejar errores de red
}

// Función para cargar datos cuando se está editando un equipo
// Se ejecuta después de que se cargan los modelos para precargar los valores
function cargarDatosEdicion() {
    // Actualizar la vista previa del nombre del equipo con los datos existentes
    actualizarNombrePreview();
}

// Función para filtrar las marcas disponibles según el tipo de equipo seleccionado
// Implementa un filtro en cascada: Tipo -> Marca -> Modelo
function filtrarMarcasPorTipo() {
    // Paso 1: Obtener referencias a los elementos select del formulario
    const tipoSelect = document.getElementById('tipoEquipo_id');  // Select de tipo de equipo
    const marcaSelect = document.getElementById('marcaEquipo_id');  // Select de marca
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelo
    const tipoId = parseInt(tipoSelect.value);  // ID del tipo seleccionado (convertido a número)
    
    console.log('Filtrando marcas para tipo:', tipoId);
    console.log('Total modelos disponibles:', todosLosModelos.length);
    
    // Paso 2: Resetear los selects dependientes cuando cambia el tipo
    // Limpiar las opciones de marca y modelo, y deshabilitar el select de modelo
    marcaSelect.innerHTML = '<option value="">Seleccione marca...</option>';
    modeloSelect.innerHTML = '<option value="">Primero seleccione marca...</option>';
    modeloSelect.disabled = true;  // Deshabilitar hasta que se seleccione una marca
    document.getElementById('nombrePreview').value = '-';  // Resetear preview del nombre
    
    // Paso 3: Si no hay tipo seleccionado, deshabilitar marca y salir
    if (!tipoId) {
        marcaSelect.disabled = true;
        return;
    }
    
    // Paso 4: Filtrar modelos que pertenecen al tipo seleccionado
    // De estos modelos, extraer las marcas únicas disponibles
    const marcasUnicas = new Set();  // Usar Set para evitar marcas duplicadas
    const modelosFiltrados = todosLosModelos.filter(m => m.tipo_id === tipoId);
    console.log('Modelos filtrados por tipo:', modelosFiltrados.length);
    
    // Paso 5: Extraer marcas únicas de los modelos filtrados
    // Se usa JSON.stringify/parse para comparar objetos completos en el Set
    modelosFiltrados.forEach(m => {
        marcasUnicas.add(JSON.stringify({id: m.marca_id, nombre: m.marca_nombre}));
    });
    
    // Paso 6: Convertir Set a Array y ordenar alfabéticamente
    const marcasArray = Array.from(marcasUnicas).map(m => JSON.parse(m));
    marcasArray.sort((a, b) => a.nombre.localeCompare(b.nombre));  // Ordenar por nombre
    
    console.log('Marcas únicas encontradas:', marcasArray.length);
    
    // Paso 7: Poblar el select de marcas con las opciones filtradas
    if (marcasArray.length > 0) {
        marcasArray.forEach(marca => {
            const option = document.createElement('option');  // Crear elemento option
            option.value = marca.id;  // Valor del option (ID de la marca)
            option.textContent = marca.nombre;  // Texto visible (nombre de la marca)
            marcaSelect.appendChild(option);  // Agregar al select
        });
        marcaSelect.disabled = false;  // Habilitar el select de marcas
        console.log('Marcas cargadas, select habilitado');
    } else {
        // Si no hay marcas disponibles, mostrar mensaje y deshabilitar
        marcaSelect.innerHTML = '<option value="">No hay marcas disponibles para este tipo</option>';
        marcaSelect.disabled = true;
        console.log('No hay marcas disponibles');
    }
}

// Función para filtrar los modelos disponibles según el tipo y marca seleccionados
// Implementa el segundo nivel del filtro en cascada: Tipo -> Marca -> Modelo
// Esta función se ejecuta cuando el usuario selecciona una marca después de haber seleccionado un tipo
function filtrarModelosPorTipoYMarca() {
    // Paso 1: Obtener referencias a los elementos select y sus valores seleccionados
    const tipoId = parseInt(document.getElementById('tipoEquipo_id').value);  // ID del tipo seleccionado
    const marcaId = parseInt(document.getElementById('marcaEquipo_id').value);  // ID de la marca seleccionada
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelo
    
    // Paso 2: Resetear el select de modelo y el preview del nombre
    // Limpiar las opciones y deshabilitar hasta que se seleccione un modelo válido
    modeloSelect.innerHTML = '<option value="">Seleccione modelo...</option>';
    document.getElementById('nombrePreview').value = '-';  // Resetear preview del nombre
    
    // Paso 3: Validar que tanto tipo como marca estén seleccionados
    // Si falta alguno, deshabilitar el select de modelo y salir
    if (!tipoId || !marcaId) {
        modeloSelect.disabled = true;
        return;  // Salir de la función si faltan datos
    }
    
    // Paso 4: Filtrar modelos que pertenecen tanto al tipo como a la marca seleccionados
    // Se usa filter() para obtener solo los modelos que cumplen ambas condiciones
    const modelosFiltrados = todosLosModelos.filter(m => 
        m.tipo_id === tipoId && m.marca_id === marcaId  // Debe coincidir tipo Y marca
    );
    
    // Paso 5: Ordenar los modelos filtrados alfabéticamente por nombre
    // Esto facilita encontrar el modelo deseado en la lista
    modelosFiltrados.sort((a, b) => a.nombre.localeCompare(b.nombre));
    
    // Paso 6: Poblar el select de modelos con las opciones filtradas
    if (modelosFiltrados.length > 0) {
        modelosFiltrados.forEach(modelo => {
            const option = document.createElement('option');  // Crear elemento option
            option.value = modelo.id;  // Valor del option (ID del modelo)
            option.textContent = modelo.nombre;  // Texto visible (nombre del modelo)
            option.setAttribute('data-sigla', modelo.tipo_sigla);  // Guardar sigla para generar nombre del equipo
            modeloSelect.appendChild(option);  // Agregar al select
        });
        modeloSelect.disabled = false;  // Habilitar el select de modelos
    } else {
        // Si no hay modelos disponibles, mostrar mensaje y deshabilitar
        modeloSelect.innerHTML = '<option value="">No hay modelos disponibles para esta combinación</option>';
        modeloSelect.disabled = true;
    }
}

// Función para actualizar la vista previa del nombre del equipo
// El nombre del equipo se genera automáticamente basado en: sigla del tipo + código interno + patente (opcional)
// Esta función se ejecuta cuando cambian el modelo, código interno o patente
function actualizarNombrePreview() {
    // Paso 1: Obtener referencias a los elementos del formulario
    const modeloSelect = document.getElementById('modeloEquipo_id');  // Select de modelo
    const codigo = document.getElementById('codigoInterno').value;  // Campo de código interno
    const patente = document.getElementById('patente').value;  // Campo de patente (opcional)
    
    // Paso 2: Validar que hay modelo y código interno seleccionados
    // El código interno es obligatorio para generar el nombre
    if (!modeloSelect.value || !codigo) {
        document.getElementById('nombrePreview').value = '-';  // Mostrar guión si faltan datos
        return;  // Salir de la función
    }
    
    // Paso 3: Buscar el modelo seleccionado en la lista global de modelos
    // Se busca por ID para obtener la sigla del tipo de equipo
    const modelo = todosLosModelos.find(m => m.id === parseInt(modeloSelect.value));
    if (!modelo) {
        // Si no se encuentra el modelo, mostrar guión
        document.getElementById('nombrePreview').value = '-';
        return;  // Salir de la función
    }
    
    // Paso 4: Construir el nombre del equipo
    // Formato: SIGLA + CODIGO_INTERNO (ej: GT001, EX123)
    const sigla = modelo.tipo_sigla;  // Sigla del tipo de equipo (ej: GT, EX)
    let nombrePreview = sigla + codigo;  // Concatenar sigla y código interno
    
    // Paso 5: Agregar patente al nombre si existe (opcional)
    // Si hay patente, se agrega separada por guión (ej: GT001 - ABC123)
    if (patente && patente.trim()) {
        nombrePreview += ' - ' + patente.trim().toUpperCase();  // Patente en mayúsculas
    }
    
    // Paso 6: Actualizar el campo de preview con el nombre generado
    // Este campo es de solo lectura y muestra cómo quedará el nombre del equipo
    document.getElementById('nombrePreview').value = nombrePreview;
}

// Función principal para guardar un equipo (crear nuevo o actualizar existente)
// Esta función se ejecuta cuando el usuario envía el formulario de equipo
// Realiza validaciones en el frontend y luego envía los datos al servidor mediante AJAX
// Parámetros:
//   event: Objeto Event del submit del formulario
function guardarEquipo(event) {
    // Paso 1: Prevenir el comportamiento por defecto del formulario
    // Esto evita que la página se recargue y permite manejar el envío con AJAX
    event.preventDefault();
    
    // Paso 2: Obtener valores de los campos del formulario
    // Estos valores se validarán y enviarán al servidor
    const equipoId = document.getElementById('equipo_id').value;  // ID del equipo (null si es creación)
    const empresaSelect = document.getElementById('empresa_id');  // Select de empresa
    const empresaId = empresaSelect ? empresaSelect.value : '';  // ID de empresa seleccionada
    const modeloId = document.getElementById('modeloEquipo_id').value;  // ID del modelo seleccionado
    const codigo = document.getElementById('codigoInterno').value;  // Código interno del equipo
    const horometro = document.getElementById('horometro').value;  // Horas de uso (opcional)
    const odometro = document.getElementById('odometro').value;  // Kilómetros recorridos (opcional)
    const horometroSE = document.getElementById('horometroSuperEstructural').value;  // Horas superestructura (opcional)
    
    // Paso 3: Validaciones básicas en el frontend antes de enviar al servidor
    // Estas validaciones mejoran la experiencia del usuario mostrando errores inmediatamente
    
    // Validación 1: Empresa es obligatoria
    if (!empresaId || empresaId === '' || empresaId === 'Seleccione empresa...') {
        mostrarError('Debe seleccionar una empresa');
        return;  // Detener el proceso si falta la empresa
    }
    
    // Validación 2: Modelo es obligatorio
    if (!modeloId) {
        mostrarError('Debe seleccionar un modelo de equipo');
        return;  // Detener el proceso si falta el modelo
    }
    
    // Validación 3: Código interno es obligatorio
    if (!codigo) {
        mostrarError('Debe ingresar un código interno');
        return;  // Detener el proceso si falta el código interno
    }
    
    // Paso 4: Validar que los valores numéricos no sean negativos
    // Convertir strings a números enteros, o null si están vacíos
    const horometroVal = horometro ? parseInt(horometro) : null;
    const odometroVal = odometro ? parseInt(odometro) : null;
    const horometroSEVal = horometroSE ? parseInt(horometroSE) : null;
    
    // Validar horómetro (no puede ser negativo)
    if (horometroVal !== null && horometroVal < 0) {
        mostrarError('El horómetro no puede ser negativo');
        return;  // Detener el proceso si el valor es inválido
    }
    
    // Validar odómetro (no puede ser negativo)
    if (odometroVal !== null && odometroVal < 0) {
        mostrarError('El odómetro no puede ser negativo');
        return;  // Detener el proceso si el valor es inválido
    }
    
    // Validar horómetro superestructural (no puede ser negativo)
    if (horometroSEVal !== null && horometroSEVal < 0) {
        mostrarError('El horómetro superestructural no puede ser negativo');
        return;  // Detener el proceso si el valor es inválido
    }
    
    // Paso 5: Preparar los datos para enviar al servidor
    // Se construye un objeto con todos los datos del formulario
    const data = {
        equipo_id: equipoId || null,  // ID del equipo (null si es creación, número si es edición)
        empresa_id: parseInt(empresaId),  // ID de la empresa (convertido a número)
        modeloEquipo_id: parseInt(modeloId),  // ID del modelo (convertido a número)
        codigoInterno: codigo.trim().toUpperCase(),  // Código interno en mayúsculas y sin espacios
        patente: document.getElementById('patente').value.trim().toUpperCase(),  // Patente en mayúsculas (opcional)
        horometro: horometroVal,  // Horas de uso (null si está vacío)
        odometro: odometroVal,  // Kilómetros recorridos (null si está vacío)
        horometroSuperEstructural: horometroSEVal  // Horas de superestructura (null si está vacío)
    };
    
    // Paso 6: Deshabilitar el botón de envío para evitar múltiples envíos
    // Se muestra un spinner para indicar que se está procesando
    const submitBtn = event.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;  // Deshabilitar botón
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando...';  // Mostrar spinner
    
    // Paso 7: Enviar datos al servidor mediante petición POST
    // Se usa fetch API para realizar la petición AJAX
    fetch('/maquinarias/api/equipos/guardar/', {
        method: 'POST',  // Método HTTP POST para crear/actualizar datos
        headers: {
            'Content-Type': 'application/json',  // Indicar que se envía JSON
        },
        body: JSON.stringify(data)  // Convertir objeto JavaScript a JSON
    })
    .then(response => response.json())  // Convertir respuesta a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: El equipo se guardó correctamente
            // Paso 8.1: Mostrar mensaje de éxito al usuario
            mostrarExito(data.message);
            
            // Paso 8.2: Redirigir a la lista de equipos después de 1 segundo
            // Esto permite que el usuario vea el mensaje de éxito antes de redirigir
            setTimeout(() => {
                window.location.href = '/maquinarias/equipos/';
            }, 1000);
        } else {
            // CASO ERROR: El servidor retornó un error
            // Paso 9.1: Mostrar mensaje de error al usuario
            mostrarError(data.error);
            
            // Paso 9.2: Re-habilitar el botón para que el usuario pueda intentar nuevamente
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>' + (equipoId ? 'Actualizar' : 'Crear') + ' Equipo';
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        // Paso 10.1: Registrar error en consola para debugging
        console.error('Error:', error);
        
        // Paso 10.2: Mostrar mensaje genérico de error al usuario
        mostrarError('Error de conexión al guardar el equipo');
        
        // Paso 10.3: Re-habilitar el botón para que el usuario pueda intentar nuevamente
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>' + (equipoId ? 'Actualizar' : 'Crear') + ' Equipo';
    });
}

// Sistema de notificaciones para mostrar mensajes al usuario
// Crea notificaciones temporales en la esquina superior derecha de la pantalla
// Parámetros:
//   message: Texto del mensaje a mostrar
//   type: Tipo de notificación ('success' para éxito, cualquier otro valor para error)
function showNotification(message, type = 'success') {
    // Paso 1: Obtener o crear el contenedor de mensajes
    // El contenedor se crea una sola vez y se reutiliza para todas las notificaciones
    let container = document.querySelector('.messages-container');
    if (!container) {
        // Si no existe, crear el contenedor con estilos apropiados
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);  // Agregar al body del documento
    }
    
    // Paso 2: Determinar clases CSS e icono según el tipo de notificación
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';  // Clase de Bootstrap para el color
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';  // Icono de Bootstrap Icons
    
    // Paso 3: Crear el elemento de alerta con el mensaje
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-permanent`;  // Clases de Bootstrap
    alertDiv.setAttribute('role', 'alert');  // Atributo de accesibilidad
    alertDiv.style.marginBottom = '10px';  // Espaciado entre notificaciones
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Paso 4: Agregar la notificación al contenedor
    container.appendChild(alertDiv);
    
    // Paso 5: Configurar eliminación automática después de 3 segundos
    // La notificación desaparece automáticamente para no saturar la interfaz
    setTimeout(() => {
        alertDiv.classList.remove('show');  // Iniciar animación de desvanecimiento
        setTimeout(() => {
            alertDiv.remove();  // Eliminar el elemento del DOM después de la animación
        }, 150);  // Esperar a que termine la animación CSS (150ms)
    }, 3000);  // Mostrar durante 3 segundos
}

// Función auxiliar para mostrar mensajes de éxito
// Es un wrapper de showNotification que simplifica su uso para casos de éxito
// Parámetros:
//   mensaje: Texto del mensaje de éxito a mostrar
function mostrarExito(mensaje) {
    showNotification(mensaje, 'success');  // Llamar a showNotification con tipo 'success'
}

// Función auxiliar para mostrar mensajes de error
// Es un wrapper de showNotification que simplifica su uso para casos de error
// Parámetros:
//   mensaje: Texto del mensaje de error a mostrar
function mostrarError(mensaje) {
    showNotification(mensaje, 'error');  // Llamar a showNotification con tipo 'error'
}

