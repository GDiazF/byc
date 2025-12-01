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
     * 
     * El formato de Django es: "App | Modelo | Can add modelo"
     * Ejemplo: "Rrhh_Personal | sexo | Can add sexo" -> "sexo"
     * Ejemplo: "Rrhh_Personal | estado civil | Can add estado civil" -> "estadocivil" (normalizado)
     * También puede ser: "Can add sexo" -> "sexo"
     */
    function extraerNombreModelo(textoPermiso) {
        const textoLower = textoPermiso.toLowerCase().trim();
        
        // Remover "(Maestra)" si ya existe
        let texto = textoLower.replace(' (maestra)', '').replace('(maestra)', '').trim();
        
        // Formato 1: "App | Modelo | Can add modelo" (formato estándar de Django)
        // Extraer la parte del medio (el nombre del modelo)
        if (texto.includes(' | ')) {
            const partes = texto.split(' | ');
            if (partes.length >= 2) {
                // La segunda parte es el nombre del modelo (puede tener espacios)
                let modelName = partes[1].trim();
                // Normalizar: quitar espacios y convertir a minúsculas
                // Ejemplo: "estado civil" -> "estadocivil", "tipo equipo" -> "tipoequipo"
                modelName = modelName.replace(/\s+/g, ''); // Quitar todos los espacios
                return modelName;
            }
        }
        
        // Formato 2: "Can add sexo" (formato simple, sin app)
        const acciones = ['can add ', 'can change ', 'can delete ', 'can view '];
        
        for (const accion of acciones) {
            if (texto.startsWith(accion)) {
                let modelName = texto.substring(accion.length).trim();
                // Remover espacios adicionales o texto después del nombre
                const espacioIndex = modelName.indexOf(' ');
                if (espacioIndex > 0) {
                    modelName = modelName.substring(0, espacioIndex);
                }
                // Normalizar: quitar espacios
                modelName = modelName.replace(/\s+/g, '');
                return modelName;
            }
        }
        
        return null;
    }
    
    /**
     * Verifica si un permiso es de tabla maestra.
     * NO marca permisos de navegación o dashboards como maestras.
     */
    function esTablaMaestra(textoPermiso) {
        // Excluir permisos de navegación y dashboards
        // Estos permisos tienen texto como "Puede navegar a..." o "Puede ver Dashboard..."
        const textoLower = textoPermiso.toLowerCase();
        if (textoLower.includes('navegar') || textoLower.includes('dashboard')) {
            return false;
        }
        
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
        
        // Buscar los selects VISIBLES del widget filter_horizontal
        // Estos son los que el usuario ve en pantalla
        // Priorizar los selects visibles sobre los ocultos
        const selectores = [
            'select#id_permisos_from',      // Select visible de disponibles
            'select#id_permisos_to',        // Select visible de seleccionados
            'select[name="permisos_from"]', // Por nombre
            'select[name="permisos_to"]',   // Por nombre
            '.selector-available select',    // Selector de disponibles
            '.selector-chosen select',      // Selector de seleccionados
            '.selector select',             // Selector genérico
            'select.filtered',              // Selects con clase filtered
            'select[name="permisos"]',      // Select oculto (backup)
            'select[name="permisos_old"]',  // Select oculto (backup)
            'select#id_permisos'            // Select oculto (backup)
        ];
        
        let totalProcesados = 0;
        let totalMarcados = 0;
        let selectsEncontrados = 0;
        
        selectores.forEach(function(selector) {
            const $selects = $(selector);
            if ($selects.length > 0) {
                selectsEncontrados += $selects.length;
                console.log(`[Permisos] Encontrados ${$selects.length} select(s) con selector: ${selector}`);
            }
            
            $selects.each(function() {
                const $select = $(this);
                
                $select.find('option').each(function() {
                    const $option = $(this);
                    let text = $option.text().trim();
                    const value = $option.val();
                    
                    // Saltar opciones sin valor
                    if (!value || value === '' || value === '---------') return;
                    
                    totalProcesados++;
                    
                    // Remover etiqueta "(Maestra)" si ya existe para trabajar con el texto original
                    let textoOriginal = text;
                    if (text.includes('(Maestra)') || text.includes('(maestra)')) {
                        textoOriginal = text.replace(/ \(Maestra\)/gi, '').replace(/\(Maestra\)/gi, '').trim();
                    }
                    
                    // Extraer nombre del modelo para debugging
                    const modelName = extraerNombreModelo(textoOriginal);
                    
                    // Verificar si es tabla maestra usando el texto original (sin etiqueta)
                    if (esTablaMaestra(textoOriginal)) {
                        // Es tabla maestra - agregar etiqueta y estilo si no la tiene
                        if (!text.includes('(Maestra)')) {
                            const nuevoTexto = textoOriginal + ' (Maestra)';
                            $option.text(nuevoTexto);
                            totalMarcados++;
                            console.log(`[Permisos] ✓ Marcado como maestra: "${textoOriginal}" -> modelo: "${modelName}"`);
                        }
                        // Asegurar estilo siempre (incluso si ya tenía la etiqueta)
                        $option.css({
                            'color': '#856404',
                            'font-weight': 'bold'
                        });
                        $option.attr('data-maestra', 'true');
                    } else {
                        // NO es tabla maestra - asegurar que NO tenga la etiqueta ni el estilo
                        if (text.includes('(Maestra)') || text.includes('(maestra)')) {
                            // Remover etiqueta si existe incorrectamente
                            $option.text(textoOriginal);
                        }
                        // Remover estilos si existen
                        $option.css({
                            'color': '',
                            'font-weight': ''
                        });
                        $option.removeAttr('data-maestra');
                    }
                });
            });
        });
        
        console.log(`[Permisos] Resumen: ${selectsEncontrados} select(s) encontrado(s), ${totalProcesados} opción(es) procesada(s), ${totalMarcados} marcada(s) como maestra`);
        
        if (selectsEncontrados === 0) {
            console.warn('[Permisos] ⚠ No se encontraron selects de permisos. Verifica los selectores.');
        }
        
        // NOTA: No reordenamos las opciones porque rompe la funcionalidad del widget filter_horizontal de Django
        // Los permisos de tablas maestras se muestran marcados con "(Maestra)" y en color amarillo,
        // pero mantienen su posición original para no interferir con el scroll y las flechas del widget.
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
