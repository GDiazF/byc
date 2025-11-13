"""
Widgets personalizados para formularios Django
"""
from django import forms
from django.forms.widgets import TextInput
from datetime import datetime


class DateInputChileno(TextInput):
    """
    Widget personalizado para inputs de fecha con formato chileno (DD-MM-YYYY)
    Se renderiza como un input de texto que será convertido por JavaScript a date picker
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
        Convierte el valor del campo (datetime.date) a string en formato ISO (YYYY-MM-DD)
        El JavaScript se encargará de convertirlo a formato chileno
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
        Convierte el valor del formulario (DD-MM-YYYY) a formato ISO (YYYY-MM-DD)
        para que Django lo pueda procesar correctamente
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

