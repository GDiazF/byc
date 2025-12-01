"""
Signals para automatizar la creación y actualización de perfiles de usuario.

Este módulo define signals que se ejecutan automáticamente cuando:
- Se crea un nuevo User: Crea automáticamente un UserProfile
- Se modifica un UserProfile: Actualiza los permisos del usuario

Los signals están definidos en models.py, pero se importan aquí para
asegurar que se registren correctamente cuando Django carga la app.
"""

# Los signals están definidos en models.py para mantener todo junto
# Este archivo existe para documentación y para asegurar que los signals
# se registren correctamente cuando Django carga la app

# Importar los signals desde models.py para que se registren
from .models import (
    crear_user_profile,
    actualizar_permisos_usuario
)

# Los signals se registran automáticamente cuando Django importa este módulo
# No es necesario hacer nada más aquí

