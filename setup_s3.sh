#!/bin/bash

# Script para configurar variables de entorno para AWS S3
# Específico para Django + Gunicorn + Nginx en EC2

echo "=== Configuración de AWS S3 para Django + Gunicorn + Nginx ==="
echo

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "Error: No se encontró manage.py. Asegúrate de ejecutar este script desde el directorio del proyecto Django."
    exit 1
fi

# Verificar si AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "AWS CLI no está instalado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y awscli
fi

echo "Por favor, ingresa los siguientes valores:"
echo

# Solicitar información del bucket
read -p "Nombre del bucket S3 (ej: byc-documentos-bucket): " BUCKET_NAME
read -p "Región de AWS (ej: us-east-1): " AWS_REGION
read -p "AWS Access Key ID: " ACCESS_KEY_ID
read -s -p "AWS Secret Access Key: " SECRET_ACCESS_KEY
echo
echo

# Preguntar el método de configuración preferido
echo "¿Cómo quieres configurar las variables de entorno?"
echo "1) En el archivo de servicio de systemd (Recomendado)"
echo "2) Usando archivo .env con script de inicio"
read -p "Selecciona una opción (1 o 2): " CONFIG_METHOD

if [ "$CONFIG_METHOD" = "1" ]; then
    echo "=== Configurando variables en systemd ==="
    
    # Verificar si existe el archivo de servicio
    if [ ! -f "/etc/systemd/system/gunicorn.service" ]; then
        echo "No se encontró /etc/systemd/system/gunicorn.service"
        echo "¿Quieres que cree un archivo de servicio básico? (y/n)"
        read CREATE_SERVICE
        
        if [[ $CREATE_SERVICE == "y" || $CREATE_SERVICE == "Y" ]]; then
            # Detectar ruta del entorno virtual
            VENV_PATH=""
            if [ -d "venv" ]; then
                VENV_PATH="/home/ubuntu/byc/venv/bin/gunicorn"
            elif [ -d "env" ]; then
                VENV_PATH="/home/ubuntu/byc/env/bin/gunicorn"
            else
                VENV_PATH="$(which gunicorn)"
            fi
            
            sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/byc
Environment="AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID"
Environment="AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY"
Environment="AWS_STORAGE_BUCKET_NAME=$BUCKET_NAME"
Environment="AWS_S3_REGION_NAME=$AWS_REGION"
ExecStart=$VENV_PATH --access-logfile - --workers 3 --bind unix:/home/ubuntu/byc/byc.sock bycCore.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
            echo "✓ Archivo de servicio creado"
        else
            echo "Por favor, configura manualmente el archivo de servicio."
            exit 1
        fi
    else
        echo "Actualizando archivo de servicio existente..."
        # Hacer backup del archivo actual
        sudo cp /etc/systemd/system/gunicorn.service /etc/systemd/system/gunicorn.service.backup
        
        # Agregar variables de entorno al archivo existente
        sudo sed -i '/\[Service\]/a Environment="AWS_ACCESS_KEY_ID='$ACCESS_KEY_ID'"' /etc/systemd/system/gunicorn.service
        sudo sed -i '/AWS_ACCESS_KEY_ID/a Environment="AWS_SECRET_ACCESS_KEY='$SECRET_ACCESS_KEY'"' /etc/systemd/system/gunicorn.service
        sudo sed -i '/AWS_SECRET_ACCESS_KEY/a Environment="AWS_STORAGE_BUCKET_NAME='$BUCKET_NAME'"' /etc/systemd/system/gunicorn.service
        sudo sed -i '/AWS_STORAGE_BUCKET_NAME/a Environment="AWS_S3_REGION_NAME='$AWS_REGION'"' /etc/systemd/system/gunicorn.service
        
        echo "✓ Variables agregadas al archivo de servicio"
    fi
    
elif [ "$CONFIG_METHOD" = "2" ]; then
    echo "=== Configurando con archivo .env ==="
    
    # Crear el archivo .env
    cat > .env << EOF
AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME=$BUCKET_NAME
AWS_S3_REGION_NAME=$AWS_REGION
EOF
    
    echo "✓ Archivo .env creado"
    
    # Crear script de inicio
    cat > start_gunicorn.sh << EOF
#!/bin/bash
cd /home/ubuntu/byc
source venv/bin/activate 2>/dev/null || source env/bin/activate 2>/dev/null || echo "No se encontró entorno virtual"
source .env
exec gunicorn --access-logfile - --workers 3 --bind unix:/home/ubuntu/byc/byc.sock bycCore.wsgi:application
EOF
    
    chmod +x start_gunicorn.sh
    echo "✓ Script de inicio creado"
    
    # Actualizar servicio de systemd
    if [ -f "/etc/systemd/system/gunicorn.service" ]; then
        sudo cp /etc/systemd/system/gunicorn.service /etc/systemd/system/gunicorn.service.backup
        sudo sed -i 's|ExecStart=.*|ExecStart=/home/ubuntu/byc/start_gunicorn.sh|' /etc/systemd/system/gunicorn.service
        echo "✓ Servicio de systemd actualizado"
    fi
else
    echo "Opción no válida"
    exit 1
fi

echo "=== Verificando configuración ==="
echo "Bucket: $BUCKET_NAME"
echo "Región: $AWS_REGION"
echo

# Verificar que el bucket existe o crear uno nuevo
echo "Verificando bucket S3..."
if aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "✓ El bucket $BUCKET_NAME existe"
else
    echo "El bucket $BUCKET_NAME no existe."
    read -p "¿Deseas crearlo? (y/n): " CREATE_BUCKET
    if [[ $CREATE_BUCKET == "y" || $CREATE_BUCKET == "Y" ]]; then
        if [[ $AWS_REGION == "us-east-1" ]]; then
            aws s3 mb "s3://$BUCKET_NAME"
        else
            aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION"
        fi
        echo "✓ Bucket $BUCKET_NAME creado"
        
        # Configurar políticas del bucket para archivos privados
        cat > bucket_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyPublicRead",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
EOF
        
        aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://bucket_policy.json
        rm bucket_policy.json
        echo "✓ Políticas de seguridad aplicadas al bucket"
    fi
fi

echo
echo "=== Instalando dependencias de Python ==="
# Detectar y activar entorno virtual
if [ -d "venv" ]; then
    echo "Activando entorno virtual 'venv'..."
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "Activando entorno virtual 'env'..."
    source env/bin/activate
else
    echo "No se encontró entorno virtual, usando instalación global..."
fi

pip install -r requirements.txt
echo "✓ Dependencias instaladas"

echo
echo "=== Reiniciando servicios ==="
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
echo "✓ Gunicorn reiniciado"

# Verificar estado de los servicios
echo
echo "=== Verificando estado de servicios ==="
if systemctl is-active --quiet gunicorn; then
    echo "✓ Gunicorn está funcionando correctamente"
else
    echo "❌ Error: Gunicorn no está funcionando"
    echo "Revisa los logs con: sudo journalctl -u gunicorn -f"
fi

if systemctl is-active --quiet nginx; then
    echo "✓ Nginx está funcionando correctamente"
else
    echo "⚠️  Nginx no está activo, es posible que necesites reiniciarlo:"
    echo "sudo systemctl restart nginx"
fi

echo
echo "=== Configuración completada ==="
echo "Tu aplicación Django ahora está configurada para usar AWS S3"
echo
echo "Para verificar que todo funciona:"
echo "1. Sube un archivo desde tu aplicación web"
echo "2. Verifica que aparece en S3: aws s3 ls s3://$BUCKET_NAME/media/ --recursive"
echo "3. Revisa los logs si hay problemas: sudo journalctl -u gunicorn -f"
echo
