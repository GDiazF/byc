// Funciones para gestión de pautas en ver_pautas_modelo.html
// Este archivo contiene las funciones JavaScript necesarias para gestionar pautas de mantenimiento
// desde la vista que muestra todas las pautas de un modelo específico

// Variable global para almacenar el ID de la pauta sobre la que se está realizando una acción
// Se usa para mantener el contexto entre la acción inicial y la confirmación
let pautaIdAccion = null;

// Función que se ejecuta cuando el usuario intenta cambiar el estado activo/inactivo de una pauta
// Muestra un modal de confirmación antes de realizar el cambio
// Parámetros:
//   pautaId: ID de la pauta que se está modificando
//   nombre: Nombre de la pauta para mostrar en el modal
//   estadoActual: Estado actual de la pauta (true = activa, false = inactiva)
function toggleActivo(pautaId, nombre, estadoActual) {
    // Paso 1: Guardar el ID de la pauta para usar en la confirmación
    pautaIdAccion = pautaId;
    
    // Paso 2: Mostrar el modal de confirmación apropiado según el estado actual
    if (estadoActual) {
        // Si la pauta está activa, mostrar modal de confirmación para desactivar
        document.getElementById('pautaDesactivarNombre').textContent = nombre;  // Mostrar nombre en el modal
        const modal = new bootstrap.Modal(document.getElementById('confirmDesactivarModal'));
        modal.show();  // Mostrar el modal
    } else {
        // Si la pauta está inactiva, mostrar modal de confirmación para activar
        document.getElementById('pautaActivarNombre').textContent = nombre;  // Mostrar nombre en el modal
        const modal = new bootstrap.Modal(document.getElementById('confirmActivarModal'));
        modal.show();  // Mostrar el modal
    }
}

// Función que se ejecuta cuando el usuario confirma el cambio de estado de una pauta
// Realiza la petición al servidor para cambiar el estado activo/inactivo
function confirmarCambioEstado() {
    // Paso 1: Validar que hay una pauta pendiente de cambio
    if (!pautaIdAccion) return;  // Si no hay ID guardado, salir sin hacer nada
    
    // Paso 2: Realizar petición POST al servidor para cambiar el estado
    // El servidor alterna el estado actual (si está activa la desactiva, y viceversa)
    fetch(`/maquinarias/api/pautas-mantenimiento/${pautaIdAccion}/toggle-activo/`, {
        method: 'POST'  // Método HTTP POST para modificar datos
    })
    .then(response => response.json())  // Convertir respuesta a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: El estado fue cambiado correctamente
            // Paso 3.1: Mostrar notificación de éxito
            showNotification(data.message, 'success');
            
            // Paso 3.2: Cerrar el modal de confirmación
            bootstrap.Modal.getInstance(document.querySelector('.modal.show')).hide();
            
            // Paso 3.3: Recargar la página después de un breve delay
            // Esto actualiza la lista de pautas con el nuevo estado
            setTimeout(() => {
                window.location.reload();
            }, 1000);  // Esperar 1 segundo para que el usuario vea el mensaje de éxito
        } else {
            // CASO ERROR: El servidor retornó un error
            showNotification(data.message, 'error');  // Mostrar mensaje de error
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        showNotification('Error al cambiar estado', 'error');  // Mostrar mensaje genérico de error
    });
}

// Función que se ejecuta cuando el usuario intenta eliminar una pauta
// Muestra un modal de confirmación antes de realizar la eliminación
// Parámetros:
//   pautaId: ID de la pauta que se está eliminando
//   nombre: Nombre de la pauta para mostrar en el modal
function mostrarModalEliminar(pautaId, nombre) {
    // Paso 1: Guardar el ID de la pauta para usar en la confirmación
    pautaIdAccion = pautaId;
    
    // Paso 2: Actualizar el nombre de la pauta en el modal de confirmación
    document.getElementById('pautaEliminarNombre').textContent = nombre;
    
    // Paso 3: Mostrar el modal de confirmación de eliminación
    const modal = new bootstrap.Modal(document.getElementById('confirmEliminarModal'));
    modal.show();
}

// Función que se ejecuta cuando el usuario confirma la eliminación de una pauta
// Realiza la petición al servidor para eliminar la pauta permanentemente
function confirmarEliminar() {
    // Paso 1: Validar que hay una pauta pendiente de eliminación
    if (!pautaIdAccion) return;  // Si no hay ID guardado, salir sin hacer nada
    
    // Paso 2: Realizar petición DELETE al servidor para eliminar la pauta
    // DELETE es el método HTTP apropiado para operaciones de eliminación
    fetch(`/maquinarias/api/pautas-mantenimiento/${pautaIdAccion}/eliminar/`, {
        method: 'DELETE'  // Método HTTP DELETE para eliminar recursos
    })
    .then(response => response.json())  // Convertir respuesta a JSON
    .then(data => {
        if (data.success) {
            // CASO ÉXITO: La pauta fue eliminada correctamente
            // Paso 3.1: Mostrar notificación de éxito
            showNotification(data.message, 'success');
            
            // Paso 3.2: Cerrar el modal de confirmación
            bootstrap.Modal.getInstance(document.getElementById('confirmEliminarModal')).hide();
            
            // Paso 3.3: Recargar la página después de un breve delay
            // Esto actualiza la lista de pautas removiendo la eliminada
            setTimeout(() => {
                window.location.reload();
            }, 1000);  // Esperar 1 segundo para que el usuario vea el mensaje de éxito
        } else {
            // CASO ERROR: El servidor retornó un error
            showNotification(data.message, 'error');  // Mostrar mensaje de error
        }
    })
    .catch(error => {
        // CASO EXCEPCIÓN: Error de red o excepción no manejada
        console.error('Error:', error);  // Registrar error en consola para debugging
        showNotification('Error al eliminar pauta', 'error');  // Mostrar mensaje genérico de error
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

