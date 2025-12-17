# 🔧 Solución al problema de lentitud por S3

## 🎯 Problema detectado

Tu aplicación está lenta porque Django intenta conectarse a S3 con credenciales inválidas/expiradas, causando timeouts de 3-5 segundos en cada navegación.

---

## ✅ RESPUESTA A TU PREGUNTA: "¿Necesito credenciales si S3 es público?"

### Depende de lo que hagas:

| Operación | ¿Necesita credenciales? | Explicación |
|-----------|------------------------|-------------|
| **Ver archivos desde el navegador** | ❌ NO | Si el bucket es público, las URLs directas funcionan |
| **Subir archivos (crear personal)** | ✅ SÍ | Django necesita permisos de escritura |
| **Listar archivos en carpetas** | ✅ SÍ | Operaciones administrativas requieren auth |
| **Verificar si archivo existe** | ✅ SÍ | Django verifica antes de mostrar |

### 🔍 Tu caso:

Tienes configurado:
```python
DEFAULT_FILE_STORAGE = 'rrhh_personal.storage.MediaS3Storage'
```

Esto hace que Django use S3 como **backend de almacenamiento activo**, no solo para servir archivos. Por eso intenta autenticarse constantemente.

---

## 🚀 SOLUCIONES (elige una):

### **OPCIÓN 1: Actualizar credenciales AWS Academy** ⭐ (RECOMENDADA si subes archivos)

**Úsala si:** Necesitas subir documentos de personal (fotos, certificados, etc.)

1. Ve a AWS Academy → Learner Lab → "AWS Details" → "Show"
2. Copia las 3 credenciales

3. En la EC2:
```bash
cd /home/ec2-user/proyecto/byc
source venv/bin/activate

# Exportar temporalmente (para probar)
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Reiniciar
pkill -HUP gunicorn
```

4. Prueba: http://webapp.gruasbyc.cl/test-s3/
   - Debería responder en < 500ms sin error

5. Si funciona, hazlo permanente (ver `DEPLOYMENT_TEST_VELOCIDAD.md`)

**Desventaja:** Las credenciales de AWS Academy expiran cada 4 horas.

---

### **OPCIÓN 2: Usar almacenamiento local (temporal)** 🔧

**Úsala si:** Solo necesitas hacer la presentación y los archivos ya están en S3 o no vas a subir nada nuevo.

Edita `bycCore/settings_aws_optimized.py`:

```python
# Comentar la línea de S3:
# DEFAULT_FILE_STORAGE = 'rrhh_personal.storage.MediaS3Storage'

# Usar almacenamiento local:
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = '/home/ec2-user/proyecto/byc/media/'
```

Luego:
```bash
git add bycCore/settings_aws_optimized.py
git commit -m "temp: usar almacenamiento local en lugar de S3"
git push origin main

# En la EC2:
cd /home/ec2-user/proyecto/byc
git pull origin main
pkill -HUP gunicorn
```

**Ventaja:** La aplicación será SÚPER rápida  
**Desventaja:** Los archivos que están en S3 no se verán (aparecerán rotos)

---

### **OPCIÓN 3: Bucket completamente público (NO RECOMENDADA)** ⚠️

Hacer el bucket público para escritura es **mala práctica de seguridad** (cualquiera podría subir archivos).

---

### **OPCIÓN 4: Usar IAM Role en la EC2** 🔐 (MEJOR A LARGO PLAZO)

**Si tu AWS Academy lo permite:**

1. Crear un IAM Role con permisos S3
2. Asignar el rol a tu instancia EC2
3. Eliminar las variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`

Django automáticamente usará el rol de la instancia.

**Ventaja:** No expiras credenciales, más seguro  
**Desventaja:** Requiere permisos que quizás AWS Academy no da

---

## 🎓 Para tu presentación:

### Opción rápida (5 minutos):

```bash
# En la EC2:
export AWS_ACCESS_KEY_ID="[copiar de AWS Academy]"
export AWS_SECRET_ACCESS_KEY="[copiar de AWS Academy]"
export AWS_SESSION_TOKEN="[copiar de AWS Academy]"
pkill -HUP gunicorn
```

Esto funcionará por las próximas 4 horas.

### Opción segura para la demo (si no subes archivos):

Cambiar a almacenamiento local (Opción 2) → Aplicación súper rápida, pero archivos de S3 no se ven.

---

## 📊 Verificar que funcionó:

Después de aplicar la solución:

1. **Test S3:**
   - http://webapp.gruasbyc.cl/test-s3/
   - Debería: < 500ms sin error (Opción 1) o error de import (Opción 2, normal)

2. **Navegar en la app:**
   - Personal → Crear personal → Volver
   - Debería: Carga instantánea (< 1 segundo)

---

## 🤔 ¿Cuál elegir?

| Escenario | Mejor opción |
|-----------|--------------|
| Presentación HOY, no vas a subir archivos | **Opción 2** (local) |
| Presentación HOY, vas a demostrar subida de archivos | **Opción 1** (actualizar credenciales) |
| Proyecto en producción real | **Opción 4** (IAM Role) |
| Solo estás probando | **Opción 2** (local) |

---

## 💡 ¿Necesitas ayuda para decidir?

Dime:
1. ¿Cuándo es tu presentación?
2. ¿Vas a demostrar la subida de documentos de personal?
3. ¿Los archivos importantes ya están en S3 o son de prueba?

Y te recomiendo la mejor solución para tu caso.

