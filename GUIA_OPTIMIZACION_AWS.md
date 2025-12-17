# 🚀 GUÍA DE OPTIMIZACIÓN PARA AWS (Solución a lentitud en recargas)

## 📋 Problema identificado

Tu aplicación se vuelve lenta en las recargas porque:

1. ❌ **Sin conexiones persistentes** - Cada request abre una nueva conexión a RDS (latencia alta)
2. ❌ **Sesiones en base de datos** - Cada request guarda la sesión en RDS (queries extra)
3. ❌ **Caché local en memoria** - Se llena y se vuelve lento en producción
4. ❌ **Sin optimización S3** - Verifica archivos innecesariamente

## ✅ Solución implementada

He creado `settings_aws_optimized.py` con las siguientes mejoras:

### 1. **Conexiones persistentes a RDS** ⚡
```python
"CONN_MAX_AGE": 600  # Mantiene conexiones abiertas 10 minutos
"CONN_HEALTH_CHECKS": True  # Verifica que la conexión esté viva
```
**Beneficio:** Elimina la latencia de conectar a RDS en cada request (~100-200ms)

### 2. **Sesiones en caché** 💾
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_SAVE_EVERY_REQUEST = False
```
**Beneficio:** Reduce queries a la BD en cada request

### 3. **Caché en base de datos** 🗄️
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}
```
**Beneficio:** Más confiable que memoria local, funciona con múltiples instancias

### 4. **Optimizaciones S3** 📦
```python
AWS_QUERYSTRING_AUTH = False  # No genera URLs firmadas
AWS_S3_FILE_OVERWRITE = False  # No verifica archivos cada vez
```
**Beneficio:** Reduce latencia al acceder a archivos en S3

---

## 🔧 PASOS PARA IMPLEMENTAR

### Paso 1: Conectarse a tu servidor AWS EC2

```bash
ssh -i tu-llave.pem ec2-user@98.94.227.236
cd /ruta/a/tu/proyecto/byc
```

### Paso 2: Crear la tabla de caché

```bash
python manage.py createcachetable --settings=bycCore.settings_aws_optimized
```

Este comando crea la tabla `django_cache_table` en PostgreSQL para el sistema de caché.

### Paso 3: Configurar variables de entorno (IMPORTANTE)

Edita el archivo de configuración de tu servidor web (Gunicorn/uWSGI):

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

O si usas supervisor:

```bash
sudo nano /etc/supervisor/conf.d/byc.conf
```

Agrega las variables de entorno de AWS:

```ini
[Service]
Environment="AWS_ACCESS_KEY_ID=tu_access_key_aqui"
Environment="AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui"
Environment="DJANGO_SETTINGS_MODULE=bycCore.settings_aws_optimized"
```

### Paso 4: Actualizar el wsgi.py

Edita `bycCore/wsgi.py` para usar el nuevo settings:

```python
import os
from django.core.wsgi import get_wsgi_application

# Usar settings optimizado para AWS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bycCore.settings_aws_optimized')

application = get_wsgi_application()
```

### Paso 5: Crear directorio de logs

```bash
sudo mkdir -p /home/ec2-user/byc/logs
sudo chown -R ec2-user:ec2-user /home/ec2-user/byc/logs
```

### Paso 6: Reiniciar los servicios

```bash
# Si usas Gunicorn con systemd
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Si usas supervisor
sudo supervisorctl restart byc

# Verificar que todo está corriendo
sudo systemctl status gunicorn
# o
sudo supervisorctl status
```

### Paso 7: Verificar que funciona

1. Abre tu navegador y ve a: https://webapp.gruasbyc.cl
2. Inicia sesión
3. Navega a diferentes páginas
4. **Recarga varias veces** - Debería ser RÁPIDO ahora

---

## 📊 Mejoras esperadas

| Métrica | Antes | Después |
|---------|-------|---------|
| **Primera carga** | ~2-3s | ~1-2s |
| **Recargas** | ~5-10s ❌ | ~0.5-1s ✅ |
| **Conexiones a RDS** | 1 por request | Reutilizadas |
| **Queries por request** | 15-20 | 8-12 |

---

## 🔍 DIAGNÓSTICO: Ver queries SQL (opcional)

Si quieres ver qué queries se están ejecutando para diagnóstico:

1. Edita `settings_aws_optimized.py`
2. Cambia el nivel de log de django.db.backends:

```python
'django.db.backends': {
    'handlers': ['console'],
    'level': 'DEBUG',  # Cambiar de WARNING a DEBUG
    'propagate': False,
},
```

3. Reinicia el servidor
4. Revisa los logs: `tail -f /home/ec2-user/byc/logs/django.log`

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Error: "No module named 'argon2'"

Instalar argon2:

```bash
pip install django[argon2]
```

### Error: "cache table doesn't exist"

Ejecutar:

```bash
python manage.py createcachetable --settings=bycCore.settings_aws_optimized
```

### Error: "Too many connections to RDS"

Reducir `CONN_MAX_AGE` en settings:

```python
"CONN_MAX_AGE": 300,  # Reducir a 5 minutos
```

### Sesiones no persisten / usuarios se deslogean

Verificar que `SESSION_COOKIE_SECURE = True` solo si tienes HTTPS configurado.
Si no tienes HTTPS, cambiar a `False`:

```python
SESSION_COOKIE_SECURE = False  # Solo si NO tienes HTTPS
```

---

## 🔄 ROLLBACK (Volver a la configuración anterior)

Si algo sale mal, puedes volver fácilmente:

1. Edita `bycCore/wsgi.py`:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bycCore.settings')
```

2. Reinicia el servidor:
```bash
sudo systemctl restart gunicorn
```

---

## 📈 PRÓXIMOS PASOS (Opcional - para máximo rendimiento)

### 1. Agregar índices en la base de datos

Conectarse a PostgreSQL:

```bash
psql -h byccore-db.cjscic8mi81f.us-east-1.rds.amazonaws.com -U postgres -d bycCore
```

Ejecutar:

```sql
-- Índices para vencimientos de documentos
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_personal_fecha_vencimiento 
    ON "Personal"(fecha_vencimiento_carnet) 
    WHERE activo = true AND fecha_vencimiento_carnet IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_licencia_fecha_vencimiento 
    ON rrhh_personal_licenciaporpersonal(fechaVencimiento) 
    WHERE fechaVencimiento IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_licencia_interna_fecha_vencimiento 
    ON rrhh_personal_licenciainternaporpersonal(fechaVencimiento) 
    WHERE fechaVencimiento IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_certificacion_fecha_vencimiento 
    ON rrhh_personal_certificacion(fechaVencimiento) 
    WHERE fechaVencimiento IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_examen_fecha_vencimiento 
    ON rrhh_personal_examen(fechaVencimiento) 
    WHERE fechaVencimiento IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documento_maquinaria_fecha_vencimiento 
    ON maquinarias_documento(fecha_vencimiento) 
    WHERE fecha_vencimiento IS NOT NULL;
```

**Nota:** `CONCURRENTLY` permite crear índices sin bloquear la tabla.

### 2. Usar Redis para caché (más rápido que BD)

Si tienes presupuesto, considera Amazon ElastiCache Redis:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://tu-redis-endpoint.cache.amazonaws.com:6379/1',
    }
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Conectarse a EC2
- [ ] Crear tabla de caché (`createcachetable`)
- [ ] Configurar variables de entorno AWS
- [ ] Actualizar wsgi.py
- [ ] Crear directorio de logs
- [ ] Reiniciar servicios
- [ ] Probar recargas múltiples
- [ ] Verificar logs
- [ ] (Opcional) Agregar índices en PostgreSQL
- [ ] (Opcional) Configurar Redis

---

## 📞 SOPORTE

Si tienes problemas, revisa:

1. Logs de Django: `tail -f /home/ec2-user/byc/logs/django.log`
2. Logs de Gunicorn: `sudo journalctl -u gunicorn -f`
3. Logs de Nginx: `sudo tail -f /var/log/nginx/error.log`

---

**¡Listo! Con estas optimizaciones, tu aplicación debería ser mucho más rápida en AWS! 🚀**

