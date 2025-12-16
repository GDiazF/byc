#!/usr/bin/env python
"""
Script para extraer todos los datos de SQLite3 y generar un script SQL para PostgreSQL.

Este script:
1. Se conecta a la base de datos SQLite3 (db.sqlite3)
2. Extrae todos los datos de todas las tablas
3. Genera un script SQL compatible con PostgreSQL
4. Maneja las diferencias de sintaxis entre SQLite y PostgreSQL
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Configuración
SQLITE_DB = 'db.sqlite3'
OUTPUT_FILE = 'datos_completos_postgresql.sql'
BASE_DIR = Path(__file__).resolve().parent

def escapar_valor(valor):
    """
    Escapa valores para SQL PostgreSQL.
    Maneja None, strings, números, fechas, etc.
    """
    if valor is None:
        return 'NULL'
    elif isinstance(valor, str):
        # Escapar comillas simples duplicándolas y envolver en comillas
        valor_escapado = valor.replace("'", "''")
        return f"'{valor_escapado}'"
    elif isinstance(valor, (int, float)):
        return str(valor)
    elif isinstance(valor, bool):
        return 'TRUE' if valor else 'FALSE'
    elif isinstance(valor, bytes):
        # Para campos BLOB, convertir a formato hexadecimal de PostgreSQL
        return f"E'\\\\x{valor.hex()}'"
    else:
        # Para otros tipos (datetime, date, etc.), convertir a string
        return f"'{str(valor)}'"

def obtener_nombre_tabla_postgresql(tabla_sqlite):
    """
    Convierte el nombre de tabla de SQLite a PostgreSQL.
    Django usa nombres específicos según db_table o genera automáticamente.
    """
    # Mapeo de nombres de tablas conocidos (tablas con db_table específico)
    mapeo_tablas = {
        # Tablas con db_table específico de rrhh_personal
        'sexo': 'sexo',
        'estadocivil': 'estadocivil',
        'Personal': 'Personal',
        'tipo_licencia_interna': 'tipo_licencia_interna',
        'licencia_interna_por_personal': 'licencia_interna_por_personal',
        'licencia_medica_por_personal': 'licencia_medica_por_personal',
        'rrhh_personal_historialpersonal': 'rrhh_personal_historialpersonal',
        'rrhh_personal_historialdocumentopersonal': 'rrhh_personal_historialdocumentopersonal',
        
        # Tablas de maquinarias con db_table específico
        'maquinarias_seccion': 'maquinarias_seccion',
        'maquinarias_estadoot': 'maquinarias_estadoot',
        'maquinarias_tiporeparacion': 'maquinarias_tiporeparacion',
        'maquinarias_pautamantenimientopreventivo': 'maquinarias_pautamantenimientopreventivo',
        'maquinarias_itempauta': 'maquinarias_itempauta',
        'maquinarias_tipodocumento': 'maquinarias_tipodocumento',
        'maquinarias_documento': 'maquinarias_documento',
        'maquinarias_historialdocumento': 'maquinarias_historialdocumento',
        'maquinarias_tipomantenimiento': 'maquinarias_tipomantenimiento',
        'maquinarias_estadoequipo': 'maquinarias_estadoequipo',
        'maquinarias_estadocalendarioequipo': 'maquinarias_estadocalendarioequipo',
        'maquinarias_estadofuenteequipo': 'maquinarias_estadofuenteequipo',
        'maquinarias_estadomanualequipo': 'maquinarias_estadomanualequipo',
        'maquinarias_ordentrabajo': 'maquinarias_ordentrabajo',
        'maquinarias_itemseccionot': 'maquinarias_itemseccionot',
        'maquinarias_historialobservacionesot': 'maquinarias_historialobservacionesot',
        'maquinarias_historialot': 'maquinarias_historialot',
        'maquinarias_historialequipo': 'maquinarias_historialequipo',
    }
    
    # Si está en el mapeo, usar ese nombre
    if tabla_sqlite in mapeo_tablas:
        return mapeo_tablas[tabla_sqlite]
    
    # Si no, mantener el nombre original
    # Django genera nombres automáticamente como: app_label_nombremodelo
    # En SQLite y PostgreSQL deberían ser iguales si se usan las mismas migraciones
    return tabla_sqlite

def obtener_columnas_tabla(cursor, tabla):
    """Obtiene la lista de columnas de una tabla."""
    cursor.execute(f"PRAGMA table_info({tabla})")
    return [row[1] for row in cursor.fetchall()]

def obtener_todas_las_tablas(cursor):
    """Obtiene la lista de todas las tablas en la base de datos, excluyendo tablas del sistema."""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%' 
        AND name NOT LIKE 'django_%'
        ORDER BY name
    """)
    tablas = [row[0] for row in cursor.fetchall()]
    
    # Ordenar tablas para respetar dependencias básicas
    # Tablas sin FK generalmente van primero
    tablas_ordenadas = []
    tablas_restantes = tablas.copy()
    
    # Tablas que generalmente no tienen dependencias (ir primero)
    tablas_sin_deps = [
        'sexo', 'estadocivil', 
        'gen_settings_region', 'gen_settings_comuna', 'gen_settings_unidadmedida',
        'rrhh_personal_deptoempresa', 'rrhh_personal_tipoausentismo',
        'rrhh_personal_tipoexamen', 'rrhh_personal_resultadoexamen',
        'rrhh_personal_tipocertificacion', 'rrhh_personal_tipolicencia',
        'rrhh_personal_tipolicenciamedica', 'tipo_licencia_interna',
        'rrhh_personal_tipoclasificacion',
        'maquinarias_tipoequipo', 'maquinarias_marcaequipo',
        'maquinarias_estadoequipo', 'maquinarias_estadoot',
        'maquinarias_tipomantenimiento', 'maquinarias_seccion',
        'maquinarias_estadocalendarioequipo', 'maquinarias_tipodocumento',
        'maquinarias_estadofuenteequipo', 'maquinarias_estadomanualequipo',
        'maquinarias_tiporeparacion',
        'ope_calendario_estado', 'gen_permissions_rol'
    ]
    
    # Agregar tablas sin dependencias primero
    for tabla in tablas_sin_deps:
        if tabla in tablas_restantes:
            tablas_ordenadas.append(tabla)
            tablas_restantes.remove(tabla)
    
    # Agregar el resto en orden alfabético
    tablas_ordenadas.extend(sorted(tablas_restantes))
    
    return tablas_ordenadas

def generar_insert_sql(tabla_postgresql, columnas, fila, cursor_sqlite):
    """
    Genera una sentencia INSERT SQL para PostgreSQL.
    Maneja nombres de columnas que pueden tener espacios o caracteres especiales.
    """
    valores = []
    columnas_escritas = []
    
    for columna in columnas:
        valor = fila[columna]
        # Solo incluir columnas con valores no NULL o que sean necesarias
        # Escapar nombres de columnas que puedan tener caracteres especiales
        columna_escrita = f'"{columna}"' if not columna.islower() or ' ' in columna or '-' in columna else columna
        columnas_escritas.append(columna_escrita)
        valores.append(escapar_valor(valor))
    
    columnas_str = ', '.join(columnas_escritas)
    valores_str = ', '.join(valores)
    
    return f"INSERT INTO {tabla_postgresql} ({columnas_str}) VALUES ({valores_str}) ON CONFLICT DO NOTHING;"

def main():
    """Función principal que extrae los datos y genera el script SQL."""
    
    sqlite_path = BASE_DIR / SQLITE_DB
    
    if not sqlite_path.exists():
        print(f"ERROR: No se encontró el archivo {SQLITE_DB}")
        return
    
    print(f"Conectando a {SQLITE_DB}...")
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    tablas = obtener_todas_las_tablas(cursor)
    print(f"Encontradas {len(tablas)} tablas")
    
    # Generar script SQL
    output_path = BASE_DIR / OUTPUT_FILE
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Escribir encabezado
        f.write(f"""-- ============================================================================
-- SCRIPT DE EXPORTACIÓN DE DATOS DE SQLITE3 A POSTGRESQL
-- ============================================================================
-- Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 
-- Este script contiene TODOS los datos de la base de datos SQLite3
-- exportados para cargar en PostgreSQL RDS.
-- 
-- IMPORTANTE: 
-- 1. Ejecutar este script DESPUÉS de crear las tablas (migraciones de Django)
-- 2. Verificar que las tablas existan antes de ejecutar
-- 3. Los datos se insertan respetando el orden de dependencias
-- ============================================================================

-- Desactivar temporalmente las restricciones de claves foráneas (opcional)
-- BEGIN;
-- SET session_replication_role = 'replica';

""")
        
        # Procesar cada tabla
        total_registros = 0
        for tabla_sqlite in sorted(tablas):
            tabla_postgresql = obtener_nombre_tabla_postgresql(tabla_sqlite)
            
            try:
                # Obtener columnas
                columnas = obtener_columnas_tabla(cursor, tabla_sqlite)
                
                if not columnas:
                    print(f"  [AVISO] Tabla {tabla_sqlite}: Sin columnas, saltando...")
                    continue
                
                # Obtener todos los registros
                cursor.execute(f"SELECT * FROM {tabla_sqlite}")
                filas = cursor.fetchall()
                
                if not filas:
                    print(f"  [VACIA] Tabla {tabla_sqlite}: Sin registros")
                    continue
                
                # Escribir comentario de tabla
                f.write(f"\n-- ============================================================================\n")
                f.write(f"-- TABLA: {tabla_postgresql} (SQLite: {tabla_sqlite})\n")
                f.write(f"-- Registros: {len(filas)}\n")
                f.write(f"-- ============================================================================\n\n")
                
                # Escribir INSERTs
                registros_escritos = 0
                for idx, fila in enumerate(filas):
                    # Convertir Row a dict para facilitar el acceso
                    fila_dict = {col: fila[col] for col in columnas}
                    
                    try:
                        insert_sql = generar_insert_sql(tabla_postgresql, columnas, fila_dict, cursor)
                        f.write(insert_sql + "\n")
                        registros_escritos += 1
                    except Exception as e:
                        print(f"  [ERROR] Error al escribir registro {idx+1} de {tabla_sqlite}: {e}")
                        f.write(f"-- ERROR al insertar registro {idx+1}: {e}\n")
                        # Intentar escribir al menos los valores básicos para debugging
                        try:
                            valores_debug = ', '.join([f"{col}={repr(fila_dict.get(col))}" for col in columnas[:5]])
                            f.write(f"-- Datos del registro: {valores_debug}...\n")
                        except:
                            pass
                
                total_registros += registros_escritos
                print(f"  [OK] Tabla {tabla_sqlite} ({tabla_postgresql}): {registros_escritos} registros")
                
            except Exception as e:
                print(f"  [ERROR] Error procesando tabla {tabla_sqlite}: {e}")
                f.write(f"\n-- ERROR al procesar tabla {tabla_sqlite}: {e}\n\n")
        
        # Escribir pie
        f.write(f"""
-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
-- Total de registros insertados: {total_registros}
-- 
-- Para reactivar las restricciones de claves foráneas:
-- COMMIT;
-- 
-- Verificación de datos insertados:
-- SELECT 
--     schemaname,
--     tablename,
--     n_tup_ins as registros_insertados
-- FROM pg_stat_user_tables
-- WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
-- ORDER BY tablename;
-- ============================================================================
""")
    
    conn.close()
    
    print(f"\n[EXITO] Script generado exitosamente: {OUTPUT_FILE}")
    print(f"   Total de registros: {total_registros}")
    print(f"\n[PASOS] Proximos pasos:")
    print(f"   1. Verificar que las tablas existan en PostgreSQL (ejecutar migraciones)")
    print(f"   2. Ejecutar: psql -U usuario -d base_datos -f {OUTPUT_FILE}")
    print(f"   3. Verificar que los datos se insertaron correctamente")

if __name__ == '__main__':
    main()

