# Configuración de Bucket S3 Público

## Problema: Error "Access Denied" al ver archivos

Si puedes subir archivos pero recibes "Access Denied" al intentar verlos, significa que el bucket S3 no tiene la política correcta para permitir acceso público de lectura.

## Solución: Configurar Política de Bucket en AWS

### Paso 1: Ir a la Consola de AWS S3

1. Accede a la [Consola de AWS S3](https://s3.console.aws.amazon.com/)
2. Selecciona tu bucket: `byc-core-media-files-2025-12-13` (o el nombre que uses)

### Paso 2: Configurar Permisos del Bucket

1. Ve a la pestaña **"Permissions"** (Permisos)
2. Desplázate hasta la sección **"Bucket policy"** (Política del bucket)
3. Haz clic en **"Edit"** (Editar)

### Paso 3: Agregar Política Pública

Copia y pega la siguiente política (reemplaza `NOMBRE_BUCKET` con el nombre real de tu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::byc-core-media-files-2025-12-13/*"
        }
    ]
}
```

**IMPORTANTE**: Reemplaza `byc-core-media-files-2025-12-13` con el nombre real de tu bucket.

### Paso 4: Desactivar "Block Public Access" (si es necesario)

1. En la misma pestaña **"Permissions"**, ve a **"Block public access (bucket settings)"**
2. Haz clic en **"Edit"**
3. **Desmarca** la opción **"Block all public access"** o al menos desmarca **"Block public access to buckets and objects granted through new access control lists (ACLs)"**
4. Guarda los cambios

**NOTA**: AWS te pedirá confirmación porque estás haciendo el bucket público. Confirma que entiendes las implicaciones.

### Paso 5: Verificar Object Ownership

1. En la pestaña **"Permissions"**, ve a **"Object Ownership"**
2. Debe estar configurado como **"Bucket owner enforced"** (esto es correcto y no permite ACLs)
3. Si no está así, cámbialo y guarda

## Verificación

Después de configurar la política:

1. Intenta acceder a un archivo directamente desde el navegador usando una URL como:
   ```
   https://byc-core-media-files-2025-12-13.s3.us-east-1.amazonaws.com/media/Documentacion_Personal/12345678/Documentos_Personales/curriculum_20250101120000.pdf
   ```

2. Si puedes ver el archivo, la configuración es correcta.

3. Si aún recibes "Access Denied", verifica:
   - Que la política del bucket tenga el nombre correcto del bucket
   - Que "Block public access" esté desactivado
   - Que el ARN en la política sea correcto (debe terminar con `/*`)

## Estructura de URLs Generadas

El código ahora genera URLs en este formato:
```
https://[BUCKET_NAME].s3.[REGION].amazonaws.com/media/[RUTA_ARCHIVO]
```

Ejemplo:
```
https://byc-core-media-files-2025-12-13.s3.us-east-1.amazonaws.com/media/Documentacion_Personal/12345678/Licencias/licencia_20250101120000.pdf
```

## Notas de Seguridad

⚠️ **ADVERTENCIA**: Hacer un bucket público significa que cualquiera con la URL puede acceder a los archivos. Asegúrate de:

1. No almacenar información sensible sin protección adicional
2. Usar nombres de archivo únicos y difíciles de adivinar (el código ya lo hace con timestamps)
3. Considerar usar CloudFront con signed URLs si necesitas más seguridad en el futuro

## Troubleshooting

### Error: "Access Denied" después de configurar la política

1. Espera unos minutos (los cambios pueden tardar en propagarse)
2. Verifica que la política esté guardada correctamente
3. Verifica que el nombre del bucket en la política coincida exactamente
4. Verifica que el ARN termine con `/*` (no solo el nombre del bucket)

### Error: "Block public access" no se puede desactivar

Si AWS no te permite desactivar "Block public access", puede ser porque:
- Tu cuenta tiene restricciones de seguridad
- Necesitas permisos adicionales de IAM
- Contacta al administrador de AWS de tu cuenta

### Los archivos se suben pero no se pueden ver

Esto indica que:
- ✅ La configuración de Django está correcta (puede subir)
- ❌ La política del bucket no está configurada (no puede leer)

Sigue los pasos anteriores para configurar la política del bucket.

