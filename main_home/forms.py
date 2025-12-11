# ============================================================================
# FORMULARIOS PARA MAIN_HOME
# ============================================================================
# Este archivo contiene formularios personalizados para la aplicación main_home
# ============================================================================

from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm


class PasswordChangeForm(DjangoPasswordChangeForm):
    """
    Formulario personalizado para cambiar contraseña con mensajes en español.
    
    Extiende el formulario de Django para cambiar contraseña, personalizando
    las etiquetas y mensajes de ayuda en español para mejorar la experiencia
    del usuario.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con etiquetas y mensajes personalizados en español.
        
        Args:
            *args: Argumentos posicionales del formulario.
            **kwargs: Argumentos de palabra clave del formulario.
        """
        super().__init__(*args, **kwargs)
        
        # Personalizar help_text de los campos en español
        self.fields['old_password'].help_text = None
        self.fields['old_password'].label = 'Contraseña Actual'
        
        # Mensajes de ayuda para la nueva contraseña en español
        self.fields['new_password1'].help_text = (
            '<ul class="mb-0 mt-2">'
            '<li>Tu contraseña no puede ser muy similar a tu otra información personal.</li>'
            '<li>Tu contraseña debe contener al menos 13 caracteres.</li>'
            '<li>Tu contraseña no puede ser una contraseña comúnmente utilizada.</li>'
            '<li>Tu contraseña no puede ser completamente numérica.</li>'
            '</ul>'
        )
        self.fields['new_password1'].label = 'Nueva Contraseña'
        
        # Mensaje de ayuda para confirmar contraseña en español
        self.fields['new_password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.'
        self.fields['new_password2'].label = 'Confirmar Nueva Contraseña'

