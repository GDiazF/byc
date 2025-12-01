/**
 * JavaScript para agregar etiquetas "(Maestra)" a permisos de tablas maestras.
 * 
 * Este script modifica directamente el texto de las opciones en los selects
 * de permisos para mostrar "(Maestra)" en los permisos de tablas maestras.
 */

(function($) {
    'use strict';
    
    // Lista de modelos que son tablas maestras por app
    // DEBE coincidir con la lista en utils.py
    const tablasMaestras = {
        'rrhh_personal': [
            'sexo', 'estadocivil', 'deptoempresa', 'cargo', 'tipoausentismo',
            'proveedor', 'tipoclasificacion', 'clasificacionproveedor',
            'tipoexamen', 'resultadoexamen', 'tipocertificacion',
            'tipolicencia', 'tipolicenciainterna', 'tipolicenciamedica'
        ],
        'maquinarias': [
            'tipoequipo', 'marcaequipo', 'modeloequipo', 'seccion',
            'tiporeparacion', 'tipodocumentomaquinaria', 'tipomantenimiento',
            'estadoot', 'estadoequipo', 'estadocalendarioequipo',
            'estadofuenteequipo', 'estadomanualequipo'
        ],
        'gen_settings': [
            'region', 'comuna', 'empresa', 'unidadmedida'
        ],
        'ope_calendario': [
            'estado', 'estadofuente', 'turno', 'turnobloque', 'estadomanual'
        ]
    };
    
    /**
     * Extrae el nombre del modelo del texto de un permiso.
     * Ejemplo: "Can add sexo" -> "sexo"
     */
    function extraerNombreModelo(textoPermiso) {
        const textoLower = textoPermiso.toLowerCase().trim();
        
        // Remover "(Maestra)" si ya existe
        let texto = textoLower.replace(' (maestra)', '').replace('(maestra)', '').trim();
        
        // Buscar patrones: "can add ", "can change ", etc.
        const acciones = ['can add ', 'can change ', 'can delete ', 'can view '];
        
        for (const accion of acciones) {
            if (texto.startsWith(accion)) {
                let modelName = texto.substring(accion.length).trim();
                // Remover espacios adicionales o texto después del nombre
                const espacioIndex = modelName.indexOf(' ');
                if (espacioIndex > 0) {
                    modelName = modelName.substring(0, espacioIndex);
                }
                return modelName;
            }
        }
        
        return null;
    }
    
    /**
     * Verifica si un permiso es de tabla maestra.
     */
    function esTablaMaestra(textoPermiso) {
        const modelName = extraerNombreModelo(textoPermiso);
        if (!modelName) return false;
        
        // Buscar en todas las apps
        for (const appLabel in tablasMaestras) {
            const modelos = tablasMaestras[appLabel];
            if (modelos.includes(modelName)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Función principal que marca los permisos de tablas maestras.
     */
    function marcarPermisosMaestros() {
        console.log('[Permisos] Iniciando marcado de permisos maestros...');
        
        // Buscar TODOS los selects posibles (Django filter_horizontal crea varios)
        const selectores = [
            'select[name="permisos_from"]',
            'select[name="permisos_to"]',
            'select[name="permisos"]',
            'select#id_permisos_from',
            'select#id_permisos_to',
            'select#id_permisos',
            '.selector select',
            '.selector-available select',
            '.selector-chosen select'
        ];
        
        let totalProcesados = 0;
        let totalMarcados = 0;
        
        selectores.forEach(function(selector) {
            $(selector).each(function() {
                const $select = $(this);
                
                $select.find('option').each(function() {
                    const $option = $(this);
                    let text = $option.text().trim();
                    const value = $option.val();
                    
                    // Saltar opciones sin valor
                    if (!value || value === '' || value === '---------') return;
                    
                    totalProcesados++;
                    
                    // Si ya tiene la etiqueta "(Maestra)", solo asegurar estilo
                    if (text.includes('(Maestra)') || text.includes('(maestra)')) {
                        if (!text.includes('(Maestra)')) {
                            text = text.replace('(maestra)', '(Maestra)');
                            $option.text(text);
                        }
                        $option.css({
                            'color': '#856404',
                            'font-weight': 'bold'
                        });
                        $option.attr('data-maestra', 'true');
                        return;
                    }
                    
                    // Verificar si es tabla maestra
                    if (esTablaMaestra(text)) {
                        // Es tabla maestra - agregar etiqueta y estilo
                        const nuevoTexto = text + ' (Maestra)';
                        $option.text(nuevoTexto);
                        $option.css({
                            'color': '#856404',
                            'font-weight': 'bold'
                        });
                        $option.attr('data-maestra', 'true');
                        totalMarcados++;
                        console.log('[Permisos] Marcado como maestra:', nuevoTexto);
                    }
                });
            });
        });
        
        console.log(`[Permisos] Procesados: ${totalProcesados}, Marcados como maestra: ${totalMarcados}`);
    }
    
    // Ejecutar cuando el documento esté listo
    $(document).ready(function() {
        console.log('[Permisos] Script cargado, iniciando marcado...');
        
        // Ejecutar inmediatamente
        marcarPermisosMaestros();
        
        // Ejecutar después de varios delays para asegurar que Django haya cargado todo
        setTimeout(function() {
            console.log('[Permisos] Ejecutando después de 300ms...');
            marcarPermisosMaestros();
        }, 300);
        
        setTimeout(function() {
            console.log('[Permisos] Ejecutando después de 800ms...');
            marcarPermisosMaestros();
        }, 800);
        
        setTimeout(function() {
            console.log('[Permisos] Ejecutando después de 1500ms...');
            marcarPermisosMaestros();
        }, 1500);
        
        // Observar cambios en el DOM
        const observer = new MutationObserver(function(mutations) {
            let hayCambios = false;
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    hayCambios = true;
                }
            });
            if (hayCambios) {
                setTimeout(function() {
                    console.log('[Permisos] Cambios detectados en DOM, re-marcando...');
                    marcarPermisosMaestros();
                }, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Observar cuando se mueven elementos entre selects (filter_horizontal)
        $(document).on('change', 'select[name="permisos_from"], select[name="permisos_to"]', function() {
            setTimeout(function() {
                console.log('[Permisos] Cambio en select detectado, re-marcando...');
                marcarPermisosMaestros();
            }, 100);
        });
        
        // Observar clicks en botones de mover (>> y <<)
        $(document).on('click', '.selector-chooseall, .selector-add, .selector-remove, .selector-clearall', function() {
            setTimeout(function() {
                console.log('[Permisos] Click en botón de mover detectado, re-marcando...');
                marcarPermisosMaestros();
            }, 200);
        });
    });
    
})(django.jQuery || jQuery);
