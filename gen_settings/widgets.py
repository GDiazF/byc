"""
============================================================================
WIDGETS PERSONALIZADOS PARA FORMULARIOS DJANGO
============================================================================
Este módulo contiene widgets personalizados para formularios Django,
específicamente DateInputChileno que maneja fechas en formato chileno
(DD-MM-YYYY) y las convierte al formato ISO (YYYY-MM-DD) que Django requiere.
============================================================================
"""
from django import forms
from django.forms.widgets import TextInput
from datetime import datetime


class DateInputChileno(TextInput):
    """
    Widget personalizado para inputs de fecha con formato chileno (DD-MM-YYYY).
    
    Se renderiza como un input de texto que será convertido por JavaScript
    a un date picker. Maneja la conversión entre formato chileno (DD-MM-YYYY)
    y formato ISO (YYYY-MM-DD) que Django requiere internamente.
    """
    input_type = 'text'
    
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            'class': 'form-control fecha-chile-picker',
            'placeholder': 'DD-MM-YYYY',
            'type': 'text'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
        self.format = format or '%d-%m-%Y'
    
    def format_value(self, value):
        """
        Convierte el valor del campo a string en formato ISO (YYYY-MM-DD).
        
        Acepta objetos date, datetime o strings en formato ISO o chileno.
        El JavaScript se encargará de convertirlo a formato chileno para mostrar
        al usuario.
        
        Args:
            value: Valor del campo (date, datetime, str o None).
            
        Returns:
            str: Valor en formato ISO (YYYY-MM-DD) o string vacío si es None.
        """
        if value is None:
            return ''
        
        # Si es un string
        if isinstance(value, str):
            # Si ya está en formato ISO YYYY-MM-DD, devolverlo tal cual
            if len(value) == 10 and value[4] == '-' and value[7] == '-':
                return value
            
            # Si está en formato chileno DD-MM-YYYY, convertirlo a ISO
            if len(value) == 10 and value[2] == '-' and value[5] == '-':
                try:
                    date_obj = datetime.strptime(value, '%d-%m-%Y').date()
                    return date_obj.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    return value
            
            # Intentar parsear como ISO
            try:
                date_obj = datetime.strptime(value, '%Y-%m-%d').date()
                return date_obj.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                return value
        
        # Si es un objeto date o datetime, convertir a ISO
        try:
            if hasattr(value, 'strftime'):
                return value.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        
        return str(value)
    
    def value_from_datadict(self, data, files, name):
        """
        Convierte el valor del formulario de formato chileno a formato ISO.
        
        Cuando el usuario envía el formulario, el valor viene en formato
        chileno (DD-MM-YYYY) y este método lo convierte a formato ISO
        (YYYY-MM-DD) para que Django lo pueda procesar correctamente.
        
        Args:
            data: Diccionario con los datos del formulario.
            files: Diccionario con archivos subidos (no usado).
            name: Nombre del campo.
            
        Returns:
            str|None: Valor en formato ISO (YYYY-MM-DD) o None si está vacío.
        """
        value = data.get(name)
        
        if not value:
            return None
        
        # Si ya está en formato ISO, devolverlo
        if len(value) == 10 and value[4] == '-' and value[7] == '-':
            return value
        
        # Si está en formato chileno DD-MM-YYYY, convertirlo a ISO
        if len(value) == 10 and value[2] == '-' and value[5] == '-':
            try:
                parts = value.split('-')
                if len(parts) == 3:
                    dia, mes, anio = parts
                    return f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
            except (ValueError, IndexError):
                pass
        
        return value

