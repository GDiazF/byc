"""
Utilidades para calcular estados de vencimiento de documentos.
"""

from datetime import date, timedelta
from typing import Dict, Optional, Tuple


def calcular_estado_vencimiento(fecha_vencimiento: Optional[date]) -> Dict[str, any]:
    """
    Calcula el estado de vencimiento de un documento basado en la fecha.
    
    Args:
        fecha_vencimiento: Fecha de vencimiento del documento (None si no tiene)
    
    Returns:
        Diccionario con:
        - 'dias_restantes': int o None
        - 'estado': str ('vencido', 'critico', 'naranja', 'amarillo', 'verde')
        - 'color': str ('danger', 'warning', 'info', 'success')
        - 'badge_class': str (clase CSS para badge)
        - 'icono': str (emoji o icono)
    """
    if fecha_vencimiento is None:
        return {
            'dias_restantes': None,
            'estado': 'sin_fecha',
            'color': 'secondary',
            'badge_class': 'bg-secondary',
            'icono': '❓',
            'texto': 'Sin fecha'
        }
    
    hoy = date.today()
    dias_restantes = (fecha_vencimiento - hoy).days
    
    if dias_restantes < 0:
        # Vencido
        return {
            'dias_restantes': dias_restantes,
            'estado': 'vencido',
            'color': 'danger',
            'badge_class': 'bg-danger',
            'icono': '✗',
            'texto': f'Vencido hace {abs(dias_restantes)} día(s)'
        }
    elif dias_restantes < 15:
        # Crítico (rojo)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'critico',
            'color': 'danger',
            'badge_class': 'bg-danger',
            'icono': '⚠️',
            'texto': f'{dias_restantes} día(s)'
        }
    elif dias_restantes < 30:
        # Naranja (29-15 días)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'naranja',
            'color': 'warning',
            'badge_class': 'bg-warning',
            'icono': '⚠️',
            'texto': f'{dias_restantes} día(s)'
        }
    elif dias_restantes < 45:
        # Amarillo (44-30 días)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'amarillo',
            'color': 'info',
            'badge_class': 'bg-info',
            'icono': '✓',
            'texto': f'{dias_restantes} día(s)'
        }
    else:
        # Verde (45+ días)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'verde',
            'color': 'success',
            'badge_class': 'bg-success',
            'icono': '✓',
            'texto': f'{dias_restantes} día(s)'
        }


def obtener_color_fila(dias_restantes: Optional[int]) -> str:
    """
    Retorna la clase CSS para el color de fondo de la fila.
    
    Args:
        dias_restantes: Días restantes hasta el vencimiento
    
    Returns:
        Clase CSS de Bootstrap para el color de fondo
    """
    if dias_restantes is None:
        return ''
    
    if dias_restantes < 0:
        return 'table-danger'  # Rojo para vencidos
    elif dias_restantes < 15:
        return 'table-danger'  # Rojo para críticos
    elif dias_restantes < 30:
        return 'table-warning'  # Naranja/Amarillo
    elif dias_restantes < 45:
        return 'table-info'  # Amarillo claro
    else:
        return ''  # Sin color (verde implícito)

