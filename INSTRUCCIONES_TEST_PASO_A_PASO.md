# 🚀 INSTRUCCIONES PARA IMPLEMENTAR TEST DE VELOCIDAD

## PASO 1: Subir archivos a EC2

Desde tu máquina Windows, ejecuta:

```powershell
scp test_speed_view.py ec2-user@98.94.227.236:/home/ec2-user/proyecto/byc/main_home/views_test.py
scp bycCore_urls_completo.py ec2-user@98.94.227.236:/home/ec2-user/proyecto/byc/bycCore/urls_nuevo.py
```

**O alternativamente**, copia el contenido de cada archivo manualmente en el servidor.

---

## PASO 2: En la EC2, conecta por SSH

```bash
ssh ec2-user@98.94.227.236
cd /home/ec2-user/proyecto/byc
source venv/bin/activate
```

---

## PASO 3: Agregar las vistas de test a main_home/views.py

```bash
nano main_home/views.py
```

Al **FINAL** del archivo, pega este código:

```python
# ============================================================================
# VISTAS DE DIAGNÓSTICO (TEMPORAL)
# ============================================================================
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import time

@csrf_exempt
def test_speed(request):
    """Test básico de velocidad sin base de datos"""
    start = time.time()
    elapsed = time.time() - start
    return JsonResponse({
        'test': 'speed',
        'tiempo': f'{elapsed*1000:.2f}ms',
        'mensaje': 'OK - Sin procesamiento'
    })

@csrf_exempt
def test_database(request):
    """Test de velocidad con consulta a base de datos"""
    start = time.time()
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    
    elapsed = time.time() - start
    return JsonResponse({
        'test': 'database',
        'tiempo': f'{elapsed*1000:.2f}ms',
        'mensaje': 'OK - Consulta básica a PostgreSQL RDS'
    })

@csrf_exempt
def test_s3(request):
    """Test de velocidad de listado S3"""
    start = time.time()
    
    try:
        from storages.backends.s3boto3 import S3Boto3Storage
        storage = S3Boto3Storage()
        
        # Listar máximo 10 archivos
        files = list(storage.listdir('')[1][:10])
        
        elapsed = time.time() - start
        return JsonResponse({
            'test': 's3',
            'tiempo': f'{elapsed*1000:.2f}ms',
            'archivos_encontrados': len(files),
            'mensaje': 'OK - Listado S3'
        })
    except Exception as e:
        elapsed = time.time() - start
        return JsonResponse({
            'test': 's3',
            'tiempo': f'{elapsed*1000:.2f}ms',
            'error': str(e),
            'mensaje': 'ERROR - Revisar configuración S3'
        })
```

Guarda con `Ctrl + O`, Enter, `Ctrl + X`

---

## PASO 4: Modificar bycCore/urls.py

```bash
nano bycCore/urls.py
```

**A) Al inicio del archivo**, después de los demás imports, agrega:

```python
from main_home.views import test_speed, test_database, test_s3
```

**B) Dentro de `urlpatterns`**, antes del corchete final `]`, agrega:

```python
    # === RUTAS DE DIAGNÓSTICO ===
    path('test-speed/', test_speed, name='test_speed'),
    path('test-database/', test_database, name='test_database'),
    path('test-s3/', test_s3, name='test_s3'),
```

Guarda con `Ctrl + O`, Enter, `Ctrl + X`

---

## PASO 5: Reiniciar Gunicorn

```bash
sudo systemctl restart byccore.service
sudo systemctl status byccore.service
```

Si ves `active (running)` en verde, está OK.

---

## PASO 6: Probar las URLs

Desde tu navegador, ve a:

1. **http://webapp.gruasbyc.cl/test-speed/**
   - Debería cargar instantáneo (< 50ms)
   
2. **http://webapp.gruasbyc.cl/test-database/**
   - Debería cargar rápido (< 200ms)
   
3. **http://webapp.gruasbyc.cl/test-s3/**
   - Puede ser más lento (depende de S3)

---

## 🔍 INTERPRETAR RESULTADOS

| Test | Tiempo esperado | Qué significa si es lento |
|------|----------------|---------------------------|
| `test-speed` | < 50ms | Problema en infraestructura AWS (red, CPU, etc) |
| `test-database` | < 200ms | Problema de conexión con RDS o configuración DB |
| `test-s3` | < 500ms | Problema de latencia S3 o credenciales |

---

## ⚠️ SI ALGO FALLA

Ver logs del servidor:

```bash
sudo journalctl -u byccore.service -n 50
```

O logs de Django:

```bash
tail -f /home/ec2-user/proyecto/byc/logs/django.log
```

---

## 🗑️ LIMPIAR DESPUÉS DE LAS PRUEBAS

Cuando termines el diagnóstico, elimina estas rutas del archivo `urls.py` y las vistas del archivo `views.py`.

