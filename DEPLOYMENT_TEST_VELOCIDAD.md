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
sudo systemctl restart byccore.service
```

Verifica que el servicio esté corriendo:

```bash
sudo systemctl status byccore.service
```

Deberías ver `active (running)` en verde.

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
sudo systemctl restart byccore.service
```

---

## 📝 REPORTAR RESULTADOS

Copia los tiempos de las 3 URLs para analizar:
- test-speed: `___ms`
- test-database: `___ms`
- test-s3: `___ms`

Y describe el comportamiento: ¿Siempre lento? ¿Intermitente? ¿Rápido al principio y luego lento?

