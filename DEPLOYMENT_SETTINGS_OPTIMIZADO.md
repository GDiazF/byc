# 🚀 Deployment: Settings.py Optimizado para Producción

## ✅ Cambios realizados

He optimizado tu `settings.py` para producción manteniendo todas las optimizaciones pero con mejor configuración de archivos estáticos.

### 🔧 Optimizaciones incluidas:

1. ✅ **PostgreSQL RDS** con conexiones persistentes (`CONN_MAX_AGE=600`)
2. ✅ **Caché en base de datos** (compartido entre workers de Gunicorn)
3. ✅ **Sesiones optimizadas** (`cached_db`)
4. ✅ **S3 configurado** con el bucket correcto
5. ✅ **DEBUG = False** para producción
6. ✅ **STATIC_ROOT correcto** (`/home/ec2-user/proyecto/byc/staticfiles/`)
7. ✅ **PASSWORD_HASHERS seguros** (PBKDF2)
8. ✅ **WSGI apuntando a settings.py**

---

## 🚀 PASO A PASO para deployment

### PASO 1: Commit y push

```bash
# En tu máquina local (Windows):
git add bycCore/settings.py bycCore/wsgi.py
git commit -m "perf: settings.py optimizado para producción AWS"
git push origin main
```

---

### PASO 2: Pull y activar entorno en EC2

```bash
# Conectar a EC2
ssh ec2-user@98.94.227.236

cd /home/ec2-user/proyecto/byc
git pull origin main

# Activar entorno virtual
source venv/bin/activate
```

---

### PASO 3: Instalar/verificar dependencias

```bash
# Si tienes requirements.txt:
pip install -r requirements.txt

# Si NO tienes requirements.txt, instalar manualmente:
pip install django psycopg2-binary django-storages boto3 gunicorn pillow
```

---

### PASO 4: Crear tabla de caché (IMPORTANTE)

```bash
python manage.py createcachetable
```

Este comando crea la tabla `django_cache_table` que usa el sistema de caché.

**Output esperado:**
```
Cache table 'django_cache_table' created.
```

---

### PASO 5: Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

Este comando copia todos los archivos estáticos (CSS, JS) a `/home/ec2-user/proyecto/byc/staticfiles/`

**Output esperado:**
```
120 static files copied to '/home/ec2-user/proyecto/byc/staticfiles/'.
```

---

### PASO 6: Verificar migraciones

```bash
python manage.py migrate
```

---

### PASO 7: Reiniciar Gunicorn

```bash
sudo systemctl restart gunicorn.service
sudo systemctl status gunicorn.service
```

Deberías ver `active (running)` en verde.

---

## 🧪 VERIFICAR QUE TODO FUNCIONA

### 1️⃣ Verificar admin con estilos:

Ve a: http://webapp.gruasbyc.cl/admin/

✅ **Debería verse con estilos correctos** (colores azules, formato bonito)
❌ Si se ve sin estilos (texto plano), revisar PASO 5

---

### 2️⃣ Verificar caché funcionando:

```bash
python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test', 'funciona', 60)
>>> cache.get('test')
'funciona'
>>> exit()
```

✅ Si devuelve `'funciona'`, el caché está OK

---

### 3️⃣ Verificar notificaciones optimizadas:

1. Abrir Network tab
2. Navegar por la app
3. Verificar:
   - ✅ Solo 1 llamada a `/notificaciones/api/contar/` por página
   - ✅ Tiempo < 50ms (gracias al caché)
   - ✅ No hay conexiones SSE

---

### 4️⃣ Verificar velocidad general:

Personal → Crear → Volver → Inicio

✅ **Debería cargar en 2-5 segundos** (vs 10-15 antes)

---

## 🔍 Troubleshooting

### ❌ Admin sin estilos

**Causa:** Archivos estáticos no recolectados o ruta incorrecta

**Solución:**
```bash
cd /home/ec2-user/proyecto/byc
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn.service
```

---

### ❌ Error: No module named 'django'

**Causa:** Entorno virtual no activado o Django no instalado

**Solución:**
```bash
cd /home/ec2-user/proyecto/byc
source venv/bin/activate
pip install django psycopg2-binary django-storages boto3
```

---

### ❌ Error: table "django_cache_table" does not exist

**Causa:** No creaste la tabla de caché

**Solución:**
```bash
python manage.py createcachetable
sudo systemctl restart gunicorn.service
```

---

### ❌ Archivos de media (fotos, documentos) no se ven

**Causa:** Credenciales de AWS expiradas

**Solución:**
1. Obtener nuevas credenciales de AWS Academy
2. Editar `/etc/systemd/system/gunicorn.service`
3. Actualizar las 3 variables de entorno:
   ```ini
   Environment="AWS_ACCESS_KEY_ID=..."
   Environment="AWS_SECRET_ACCESS_KEY=..."
   Environment="AWS_SESSION_TOKEN=..."
   ```
4. Reiniciar:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart gunicorn.service
   ```

---

### ❌ Error 500 al hacer login

**Causa:** Varias posibles (ver logs)

**Ver logs:**
```bash
sudo journalctl -u gunicorn.service -n 50
```

**Soluciones comunes:**
- Verificar que PostgreSQL esté accesible
- Verificar credenciales de base de datos
- Verificar que las migraciones estén aplicadas

---

## 📊 Comparación: settings_aws_optimized.py vs settings.py

| Característica | settings_aws_optimized.py | settings.py (optimizado) |
|----------------|--------------------------|--------------------------|
| PostgreSQL RDS | ✅ | ✅ |
| Conexiones persistentes | ✅ | ✅ |
| Caché optimizado | ✅ | ✅ |
| Sesiones optimizadas | ✅ | ✅ |
| S3 configurado | ✅ | ✅ |
| DEBUG = False | ✅ | ✅ |
| STATIC_ROOT correcto | ✅ | ✅ |
| Admin con estilos | ❌ Problema | ✅ Funciona |
| Más fácil de mantener | ❌ | ✅ |

---

## 💡 Ventajas del settings.py optimizado

1. **Un solo archivo de configuración** → Más fácil de mantener
2. **Comentarios claros** → Fácil cambiar entre desarrollo/producción
3. **Admin funciona perfectamente** → STATIC_ROOT correcto
4. **Todas las optimizaciones** → Mismo rendimiento
5. **Más estándar** → Sigue las convenciones de Django

---

## 🎯 Próximos pasos opcionales

### Si quieres servir archivos estáticos con Nginx (más eficiente):

```nginx
# En tu configuración de Nginx:
location /static/ {
    alias /home/ec2-user/proyecto/byc/staticfiles/;
}
```

Esto hace que Nginx sirva los archivos estáticos directamente, sin pasar por Gunicorn.

### Si quieres usar Redis para caché (aún más rápido):

```bash
# Instalar Redis
sudo yum install redis -y
sudo systemctl start redis
sudo systemctl enable redis

# Instalar cliente Python
pip install redis

# En settings.py:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## ✅ Checklist final

- [ ] Commit y push de settings.py y wsgi.py
- [ ] Pull en EC2
- [ ] Activar venv
- [ ] Instalar dependencias (si faltan)
- [ ] Crear tabla de caché (`createcachetable`)
- [ ] Collectstatic
- [ ] Migrar
- [ ] Reiniciar Gunicorn
- [ ] Verificar admin tiene estilos
- [ ] Verificar caché funciona
- [ ] Verificar notificaciones optimizadas funcionan
- [ ] Verificar navegación es rápida

---

## 🎉 Resultado esperado

Después de seguir estos pasos:

✅ Admin con estilos bonitos  
✅ Navegación rápida (2-5 segundos)  
✅ Notificaciones funcionando sin causar lentitud  
✅ Archivos en S3 accesibles  
✅ Caché funcionando  
✅ Un solo archivo de configuración fácil de mantener  

---

¿Listo para hacer el deployment? 🚀

