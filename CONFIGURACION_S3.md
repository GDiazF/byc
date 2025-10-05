# Configuración de AWS S3 para almacenamiento de archivos

## Resumen de cambios realizados

1. **Dependencias agregadas** (`requirements.txt`):
   - `boto3==1.34.*` - SDK de AWS para Python
   - `django-storages==1.14.*` - Backend de almacenamiento para Django

2. **Configuración en `settings.py`**:
   - Agregada app `storages` a `INSTALLED_APPS`
   - Configuración de AWS S3 con variables de entorno
   - `DEFAULT_FILE_STORAGE` configurado para usar S3

3. **Storage personalizado** (`rrhh_personal/storage.py`):
   - `OverwriteS3Storage` - Clase base para S3 con sobrescritura
   - `MediaS3Storage` - Storage específico para archivos de media

4. **Actualización de modelos** (`rrhh_personal/models.py`):
   - `OverwriteStorage` ahora hereda de `MediaS3Storage`
   - Mantiene la funcionalidad de sobrescribir archivos

## Pasos para configurar en AWS EC2 (Linux + Gunicorn + Nginx)

### 1. Instalar dependencias

**IMPORTANTE**: Asegúrate de activar tu entorno virtual si usas uno:

```bash
# Navegar al directorio del proyecto
cd /home/ubuntu/byc

# Si usas entorno virtual, activarlo primero
source venv/bin/activate  # o el nombre de tu entorno virtual

# Instalar las nuevas dependencias
pip install -r requirements.txt
```

### 2. Configurar AWS S3

#### Opción A: Usar el script automático
```bash
chmod +x setup_s3.sh
./setup_s3.sh
```

#### Opción B: Configuración manual

1. **Crear bucket S3** (si no existe):
```bash
aws s3 mb s3://byc-documentos-bucket --region us-east-1
```

2. **Configurar variables de entorno**:
```bash
# Crear archivo .env
nano /home/ubuntu/byc/.env
```

Agregar las siguientes líneas:
```bash
export AWS_ACCESS_KEY_ID="tu_access_key_aqui"
export AWS_SECRET_ACCESS_KEY="tu_secret_key_aqui"
export AWS_STORAGE_BUCKET_NAME="byc-documentos-bucket"
export AWS_S3_REGION_NAME="us-east-1"
```

3. **Cargar variables de entorno**:
```bash
source /home/ubuntu/byc/.env
echo "source /home/ubuntu/byc/.env" >> ~/.bashrc
```

### 3. Configurar variables de entorno para Gunicorn

**IMPORTANTE**: Gunicorn necesita acceso a las variables de entorno. Hay varias formas de hacerlo:

#### Opción A: Variables en el archivo de servicio de systemd

```bash
# Editar el archivo de servicio de Gunicorn
sudo nano /etc/systemd/system/gunicorn.service
```

Agregar las variables de entorno en la sección `[Service]`:

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/byc
Environment="AWS_ACCESS_KEY_ID=tu_access_key_aqui"
Environment="AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui"
Environment="AWS_STORAGE_BUCKET_NAME=byc-documentos-bucket"
Environment="AWS_S3_REGION_NAME=us-east-1"
ExecStart=/home/ubuntu/byc/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/ubuntu/byc/byc.sock bycCore.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Opción B: Archivo .env con script de inicio

```bash
# Crear archivo de variables de entorno
nano /home/ubuntu/byc/.env
```

Contenido del archivo `.env`:
```bash
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_STORAGE_BUCKET_NAME=byc-documentos-bucket
AWS_S3_REGION_NAME=us-east-1
```

Luego crear un script de inicio:
```bash
# Crear script de inicio
nano /home/ubuntu/byc/start_gunicorn.sh
```

Contenido del script:
```bash
#!/bin/bash
cd /home/ubuntu/byc
source venv/bin/activate
source .env
exec gunicorn --access-logfile - --workers 3 --bind unix:/home/ubuntu/byc/byc.sock bycCore.wsgi:application
```

```bash
# Hacer ejecutable el script
chmod +x /home/ubuntu/byc/start_gunicorn.sh
```

Y actualizar el servicio de systemd:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/byc
ExecStart=/home/ubuntu/byc/start_gunicorn.sh

[Install]
WantedBy=multi-user.target
```

### 4. Configurar permisos IAM

Crear una política IAM con los siguientes permisos mínimos:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::byc-documentos-bucket",
                "arn:aws:s3:::byc-documentos-bucket/*"
            ]
        }
    ]
}
```

### 5. Recargar y reiniciar servicios

**IMPORTANTE**: Después de hacer cambios en la configuración:

```bash
# Recargar configuración de systemd
sudo systemctl daemon-reload

# Reiniciar Gunicorn
sudo systemctl restart gunicorn

# Verificar que Gunicorn esté funcionando
sudo systemctl status gunicorn

# Reiniciar Nginx (si es necesario)
sudo systemctl restart nginx

# Verificar que Nginx esté funcionando
sudo systemctl status nginx
```

### 6. Verificar logs

```bash
# Ver logs de Gunicorn
sudo journalctl -u gunicorn -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Ver logs de Django (si tienes configurado logging)
tail -f /home/ubuntu/byc/logs/django.log  # ajusta la ruta según tu configuración
```

## Estructura de archivos en S3

Los archivos se almacenarán con la siguiente estructura:
```
byc-documentos-bucket/
└── media/
    └── Documentacion_Personal/
        └── [RUT]/
            ├── Documentos_Personales/
            ├── Licencias/
            ├── Licencias_Medicas/
            ├── Certificaciones/
            └── Examenes/
```

## Verificación

Para verificar que todo funciona correctamente:

1. **Probar subida de archivos** en la aplicación
2. **Verificar en AWS Console** que los archivos aparecen en el bucket
3. **Revisar logs** de Django para errores relacionados con S3

```bash
# Ver logs de la aplicación
sudo journalctl -u gunicorn -f
```

## Migración de archivos existentes

Si tienes archivos existentes en el servidor local, puedes migrarlos a S3:

```bash
# Sincronizar archivos locales con S3
aws s3 sync /home/ubuntu/byc/Documentacion_Personal/ s3://byc-documentos-bucket/media/Documentacion_Personal/ --recursive
```

## Notas importantes

- Los archivos se almacenan como **privados** por defecto
- Django generará URLs firmadas para acceder a los archivos
- Los archivos estáticos (CSS, JS) siguen en el servidor local
- Las credenciales de AWS nunca deben incluirse en el código fuente

## Troubleshooting

### Error de permisos
- Verificar que las credenciales de AWS son correctas
- Confirmar que el usuario IAM tiene los permisos necesarios

### Error de bucket no encontrado
- Verificar que el nombre del bucket es correcto
- Confirmar que el bucket existe en la región especificada

### Error de variables de entorno
- Verificar que las variables están cargadas: `echo $AWS_ACCESS_KEY_ID`
- Reiniciar el servicio después de cambiar variables de entorno
