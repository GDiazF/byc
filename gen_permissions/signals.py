# ============================================================================
# SIGNALS PARA AUTOMATIZAR LA CREACION Y ACTUALIZACION DE PERFILES DE USUARIO
# ============================================================================
# Este modulo define signals que se ejecutan automaticamente cuando:
# - Se crea un nuevo User: Crea automaticamente un UserProfile
# - Se modifica un UserProfile: Actualiza los permisos del usuario
#
# Los signals estan definidos en models.py, pero se importan aqui para
# asegurar que se registren correctamente cuando Django carga la app.
# ============================================================================

# Los signals estan definidos en models.py para mantener todo junto
# Este archivo existe para documentacion y para asegurar que los signals
# se registren correctamente cuando Django carga la app

# Importar los signals desde models.py para que se registren
from .models import (
    crear_user_profile,
    actualizar_permisos_usuario
)

# Los signals se registran automaticamente cuando Django importa este modulo
# No es necesario hacer nada mas aqui


