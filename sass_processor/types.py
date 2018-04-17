from decimal import Decimal
from sass import SassNumber as _SassNumber, SassColor, SassList, SassMap

__all__ = ['SassNumber', 'SassColor', 'SassList', 'SassMap']


def SassNumber(value):
    if isinstance(value, (int, float, Decimal)):
        return str(_SassNumber(value, type(value).__name__.encode()).value)
    return value
