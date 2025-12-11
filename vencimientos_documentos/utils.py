"""
============================================================================
UTILIDADES PARA CALCULAR ESTADOS DE VENCIMIENTO DE DOCUMENTOS
============================================================================
Este módulo contiene funciones helper para calcular y determinar el estado
de vencimiento de documentos basándose en la fecha de vencimiento y la fecha
actual. Incluye funciones para obtener colores, badges y clases CSS según
el estado de vencimiento.
============================================================================
"""

from datetime import date, timedelta
from typing import Dict, Optional, Tuple


def calcular_estado_vencimiento(fecha_vencimiento: Optional[date]) -> Dict[str, any]:
    """
    Calcula el estado de vencimiento de un documento basado en la fecha.
    
    Determina el estado de vencimiento según los días restantes hasta la fecha
    de vencimiento. Los estados son:
    - Vencido: días < 0
    - Crítico: 0-14 días (rojo)
    - Naranja: 15-29 días (warning)
    - Amarillo: 30-44 días (warning)
    - Verde: 45+ días (success)
    
    Args:
        fecha_vencimiento (Optional[date]): Fecha de vencimiento del documento.
                                          None si no tiene fecha de vencimiento.
    
    Returns:
        Dict[str, any]: Diccionario con información del estado:
            - 'dias_restantes' (int|None): Días restantes hasta el vencimiento
            - 'estado' (str): Estado del documento ('vencido', 'critico', 'naranja',
                            'amarillo', 'verde', 'sin_fecha')
            - 'color' (str): Color de Bootstrap ('danger', 'warning', 'success', 'secondary')
            - 'badge_class' (str): Clase CSS para badge de Bootstrap
            - 'icono' (str): Emoji o icono representativo del estado
            - 'texto' (str): Texto descriptivo del estado
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
    elif dias_restantes <= 14:
        # Crítico (rojo) - 14 días hacia abajo
        return {
            'dias_restantes': dias_restantes,
            'estado': 'critico',
            'color': 'danger',
            'badge_class': 'bg-danger',
            'icono': '⚠️',
            'texto': f'{dias_restantes} día(s)'
        }
    elif dias_restantes <= 29:
        # Naranja (29-15 días)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'naranja',
            'color': 'warning',
            'badge_class': 'bg-warning',
            'icono': '⚠️',
            'texto': f'{dias_restantes} día(s)'
        }
    elif dias_restantes <= 44:
        # Amarillo (44-30 días)
        return {
            'dias_restantes': dias_restantes,
            'estado': 'amarillo',
            'color': 'warning',
            'badge_class': 'bg-warning',
            'icono': '⚠️',
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
    Retorna la clase CSS para el color de fondo de la fila según los días restantes.
    
    Determina el color de fondo de una fila de tabla según el estado de vencimiento:
    - Rojo (table-danger): Vencido o crítico (< 15 días)
    - Amarillo/Naranja (table-warning): Por vencer (15-44 días)
    - Sin color: Más de 45 días o sin fecha
    
    Args:
        dias_restantes (Optional[int]): Días restantes hasta el vencimiento.
                                       None si no hay fecha de vencimiento.
    
    Returns:
        str: Clase CSS de Bootstrap para el color de fondo de la fila.
             Valores posibles: 'table-danger', 'table-warning', '' (sin color).
    """
    if dias_restantes is None:
        return ''
    
    if dias_restantes < 0:
        return 'table-danger'  # Rojo para vencidos
    elif dias_restantes < 15:
        return 'table-danger'  # Rojo para críticos
    elif dias_restantes < 30:
        return 'table-warning'  # Naranja/Amarillo
    elif dias_restantes <= 44:
        return 'table-warning'  # Amarillo
    else:
        return ''  # Sin color (más de 45 días, no se muestran)

