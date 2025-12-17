# 🚀 DEPLOYMENT: Tests de Velocidad

## Archivos modificados:
- ✅ `main_home/views.py` - Agregadas 3 vistas de diagnóstico
- ✅ `bycCore/urls.py` - Agregadas rutas de test

---

## 📤 PASO 1: Subir cambios a GitHub

Desde tu máquina local (Windows):

```bash
git add main_home/views.py bycCore/urls.py
git commit -m "feat: agregar vistas de diagnóstico de rendimiento"
git push origin main
```

*(Cambia `main` por tu rama si es diferente)*

---

## 📥 PASO 2: Actualizar en la EC2

Conéctate a tu EC2 y ejecuta:

```bash
cd /home/ec2-user/proyecto/byc
git pull origin main
source venv/bin/activate

# Recargar Gunicorn (elige UNA opción):

# Opción A: Recarga rápida sin interrupciones (RECOMENDADA)
pkill -HUP gunicorn

# O Opción B: Reinicio completo del servicio (si tienes systemd)
# sudo systemctl restart byccore.service
```

Verifica que Gunicorn esté corriendo:

```bash
ps aux | grep gunicorn
```

Deberías ver varios procesos de Gunicorn activos.

---

## 🧪 PASO 3: Probar las URLs

Abre tu navegador y prueba estas 3 URLs:

### 1️⃣ Test de Django puro (sin BD ni S3)
```
http://webapp.gruasbyc.cl/test-speed/
```
**Esperado:** < 50ms  
**Si es lento:** Problema de infraestructura AWS (red, CPU, instancia EC2)

---

### 2️⃣ Test de conexión a PostgreSQL RDS
```
http://webapp.gruasbyc.cl/test-database/
```
**Esperado:** 50-200ms  
**Si es lento:** Problema de configuración RDS o red entre EC2 y RDS

---

### 3️⃣ Test de acceso a S3
```
http://webapp.gruasbyc.cl/test-s3/
```
**Esperado:** 200-500ms  
**Si es lento:** Problema de latencia S3 o credenciales

---

## 📊 INTERPRETACIÓN DE RESULTADOS

| Resultado | Causa probable | Solución |
|-----------|---------------|----------|
| `test-speed` > 1 segundo | Problema de red/EC2 | Revisar configuración EC2, Security Groups, VPC |
| `test-database` > 500ms | Latencia RDS | Verificar que RDS esté en la misma VPC/subnet que EC2 |
| `test-s3` > 2 segundos | Problema S3 | Revisar credenciales, verificar región, usar IAM Role |
| Todos lentos intermitentemente | Throttling o cuotas AWS | Revisar límites de la cuenta AWS Academy |

---

## 🔍 SI HAY ERRORES

Ver logs del servidor:

```bash
sudo journalctl -u byccore.service -n 50
```

O logs de Django:

```bash
tail -f /home/ec2-user/proyecto/byc/logs/django.log
```

---

## 🗑️ LIMPIEZA DESPUÉS DEL DIAGNÓSTICO

Una vez identificado el problema, eliminar:

1. En `main_home/views.py` - Las funciones `test_speed`, `test_database`, `test_s3`
2. En `bycCore/urls.py` - El import y las 3 rutas de test

```bash
git add main_home/views.py bycCore/urls.py
git commit -m "chore: eliminar vistas de diagnóstico"
git push origin main
```

Y en la EC2:

```bash
cd /home/ec2-user/proyecto/byc
git pull origin main
pkill -HUP gunicorn
```

---

## 🔧 SOLUCIONES SEGÚN DIAGNÓSTICO

### Si el error es `InvalidAccessKeyId` en S3:

**CAUSA:** Credenciales de AWS Academy expiradas (común en cuentas de estudiante).

**SOLUCIÓN 1: Actualizar credenciales AWS Academy**

1. Ve a AWS Academy → Learner Lab
2. Click en "AWS Details"
3. Click en "Show" en AWS CLI credentials
4. Copia las 3 variables:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`

5. En la EC2, edita el archivo de environment:

```bash
sudo nano /etc/systemd/system/byccore.service
```

Busca la sección `[Service]` y actualiza/agrega:

```ini
Environment="AWS_ACCESS_KEY_ID=tu_nuevo_access_key"
Environment="AWS_SECRET_ACCESS_KEY=tu_nuevo_secret_key"
Environment="AWS_SESSION_TOKEN=tu_nuevo_session_token"
```

Guarda (`Ctrl+O`, Enter, `Ctrl+X`) y reinicia:

```bash
sudo systemctl daemon-reload
sudo systemctl restart byccore.service
```

**SOLUCIÓN 2: Usar IAM Role en lugar de credenciales** (MEJOR, pero requiere configuración)

Si puedes configurar un IAM Role en tu cuenta AWS Academy:
1. Crear rol con permisos S3
2. Asignarlo a la instancia EC2
3. Eliminar las variables de entorno de credenciales

**SOLUCIÓN 3: Deshabilitar verificación S3 temporalmente**

En `settings_aws_optimized.py`:

```python
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_VERIFY = False  # Ya está así
```

Y agregar:

```python
# Desactivar verificación de existencia de archivos
AWS_S3_USE_THREADS = False
```

---

## 📊 RESULTADOS ESPERADOS DESPUÉS DE LA CORRECCIÓN

| Test | Esperado |
|------|----------|
| test-speed | < 50ms |
| test-database | < 200ms |
| test-s3 | < 500ms (sin error) |

---

## 📝 REPORTAR RESULTADOS

Copia los tiempos de las 3 URLs para analizar:
- test-speed: `___ms`
- test-database: `___ms`
- test-s3: `___ms`

Y describe el comportamiento: ¿Siempre lento? ¿Intermitente? ¿Rápido al principio y luego lento?

