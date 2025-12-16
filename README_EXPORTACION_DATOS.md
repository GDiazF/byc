# Exportación de Datos de SQLite3 a PostgreSQL RDS

Este documento explica cómo exportar todos los datos de la base de datos SQLite3 local a PostgreSQL en AWS RDS.

## Archivos Generados

- **`extraer_datos_sqlite_a_postgresql.py`**: Script Python que extrae los datos de SQLite3
- **`datos_completos_postgresql.sql`**: Script SQL generado con todos los datos (1.1 MB, ~4,724 registros)

## Proceso de Exportación

### Paso 1: Ejecutar el Script de Extracción

El script ya se ejecutó y generó el archivo `datos_completos_postgresql.sql`. Si necesitas regenerarlo:

```bash
python extraer_datos_sqlite_a_postgresql.py
```

El script:
- Se conecta a `db.sqlite3`
- Extrae todos los datos de todas las tablas (excepto tablas del sistema Django)
- Genera un script SQL compatible con PostgreSQL
- Maneja automáticamente la conversión de tipos de datos
- Ordena las tablas para respetar dependencias de claves foráneas

### Paso 2: Preparar PostgreSQL RDS

Antes de cargar los datos, asegúrate de que:

1. **Las tablas existan**: Ejecuta las migraciones de Django en PostgreSQL RDS
   ```bash
   python manage.py migrate --database=default
   ```

2. **Verificar conexión**: Asegúrate de que `settings.py` esté configurado para conectarse a RDS

### Paso 3: Cargar los Datos en PostgreSQL RDS

#### Opción A: Usando psql (Recomendado)

```bash
# Conectarse a RDS usando psql
psql -h tu-instancia-rds.xxxxx.us-east-1.rds.amazonaws.com \
     -U tu_usuario \
     -d nombre_base_datos \
     -f datos_completos_postgresql.sql
```

#### Opción B: Desde Python/Django

```python
# En un script Python o shell de Django
from django.db import connection
from pathlib import Path

sql_file = Path('datos_completos_postgresql.sql')
with connection.cursor() as cursor:
    cursor.execute(sql_file.read_text())
```

#### Opción C: Usando pgAdmin o DBeaver

1. Abre pgAdmin o DBeaver
2. Conéctate a tu instancia RDS
3. Abre el archivo `datos_completos_postgresql.sql`
4. Ejecuta el script completo

### Paso 4: Verificar la Carga

Ejecuta esta consulta en PostgreSQL para verificar cuántos registros se insertaron:

```sql
-- Verificar registros por tabla
SELECT 
    schemaname,
    tablename,
    n_tup_ins as registros_insertados
FROM pg_stat_user_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY tablename;
```

O verifica manualmente algunas tablas clave:

```sql
-- Verificar algunas tablas importantes
SELECT COUNT(*) FROM "Personal";
SELECT COUNT(*) FROM maquinarias_equipo;
SELECT COUNT(*) FROM rrhh_personal_infolaboral;
SELECT COUNT(*) FROM auth_user;
```

## Características del Script Generado

- **Total de registros**: ~4,724 registros
- **Total de tablas**: 79 tablas
- **Manejo de conflictos**: Usa `ON CONFLICT DO NOTHING` para evitar errores por duplicados
- **Orden de inserción**: Respeta dependencias de claves foráneas
- **Compatibilidad**: Compatible con PostgreSQL 12+

## Tablas Principales Exportadas

- **Personal**: 308 registros
- **Equipos de Maquinarias**: 25 registros
- **Órdenes de Trabajo**: 8 registros
- **Usuarios**: 9 registros
- **Permisos y Roles**: ~1,200 registros
- **Notificaciones**: 401 registros
- **Y muchas más...**

## Solución de Problemas

### Error: "relation does not exist"

**Problema**: Las tablas no existen en PostgreSQL.

**Solución**: Ejecuta las migraciones de Django primero:
```bash
python manage.py migrate
```

### Error: "duplicate key value violates unique constraint"

**Problema**: Ya existen algunos registros en PostgreSQL.

**Solución**: El script usa `ON CONFLICT DO NOTHING`, así que los duplicados se ignoran automáticamente. Si quieres sobrescribir, elimina los datos existentes primero o modifica el script.

### Error: "foreign key constraint violation"

**Problema**: El orden de inserción no respeta las dependencias.

**Solución**: El script ya ordena las tablas para respetar dependencias. Si aún hay problemas, puedes desactivar temporalmente las restricciones:

```sql
BEGIN;
SET session_replication_role = 'replica';
-- Ejecutar el script aquí
COMMIT;
```

### Error: "encoding" o caracteres especiales

**Problema**: Problemas con caracteres especiales (tildes, ñ, etc.).

**Solución**: El script maneja UTF-8 correctamente. Asegúrate de que PostgreSQL esté configurado con encoding UTF-8:

```sql
-- Verificar encoding
SHOW server_encoding;
-- Debe ser UTF8 o similar
```

## Notas Importantes

1. **Backup**: Siempre haz un backup de tu base de datos RDS antes de cargar datos masivos.

2. **Tiempo de ejecución**: La carga puede tardar varios minutos dependiendo del tamaño de los datos y la conexión a RDS.

3. **Archivos**: Los archivos referenciados en campos FileField (como documentos PDF) NO se migran automáticamente. Debes migrarlos manualmente a S3 o al sistema de archivos del servidor.

4. **Passwords**: Las contraseñas de usuarios (`auth_user`) se mantienen con el mismo hash, así que funcionarán igual.

5. **IDs**: Los IDs se mantienen iguales si no hay conflictos. Si hay conflictos, PostgreSQL generará nuevos IDs automáticamente.

## Regenerar el Script

Si necesitas regenerar el script después de hacer cambios en SQLite3:

```bash
python extraer_datos_sqlite_a_postgresql.py
```

Esto sobrescribirá el archivo `datos_completos_postgresql.sql` con los datos más recientes.

## Estructura del Script SQL Generado

El script generado tiene esta estructura:

```sql
-- Encabezado con información
-- Tabla 1: INSERT statements
-- Tabla 2: INSERT statements
-- ...
-- Pie con estadísticas
```

Cada tabla tiene:
- Comentario con nombre de tabla y cantidad de registros
- INSERT statements con `ON CONFLICT DO NOTHING`
- Manejo de errores (comentarios si hay problemas)

## Contacto y Soporte

Si encuentras problemas al cargar los datos, verifica:
1. Que las migraciones estén ejecutadas
2. Que la conexión a RDS funcione
3. Que los permisos del usuario de PostgreSQL sean correctos
4. Los logs de PostgreSQL para errores específicos

