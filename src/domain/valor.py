"""Value Objects y enumeraciones del dominio."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .errores import DatoInvalidoError


class EstadoReservacion(str, Enum):
    SOLICITADA = "SOLICITADA"
    CONFIRMADA = "CONFIRMADA"
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"
    CANCELADA = "CANCELADA"
    NO_SHOW = "NO_SHOW"


class EstadoHabitacion(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    OCUPADA = "OCUPADA"
    PENDIENTE_DE_LIMPIEZA = "PENDIENTE_DE_LIMPIEZA"
    FUERA_DE_SERVICIO = "FUERA_DE_SERVICIO"


class Rol(str, Enum):
    RESERVACIONES = "RESERVACIONES"
    RECEPCION = "RECEPCION"
    LIMPIEZA = "LIMPIEZA"
    ADMINISTRACION = "ADMINISTRACION"


@dataclass(frozen=True)
class LineaReservacion:
    """Renglón de la reservación: categoría de habitación, cantidad y tarifa acordada."""

    categoria_id: str
    cantidad: int
    tarifa: Decimal

    def __post_init__(self):
        if self.cantidad <= 0:
            raise DatoInvalidoError("La cantidad debe ser mayor a cero")
        if self.tarifa < 0:
            raise DatoInvalidoError("La tarifa no puede ser negativa")

    @property
    def subtotal(self):
        return self.tarifa * self.cantidad


@dataclass(frozen=True)
class Garantia:
    """Respaldo del huésped (tarjeta o depósito) que se verifica en el check-in."""

    tipo: str
    referencia: str

    def __post_init__(self):
        if not self.tipo.strip() or not self.referencia.strip():
            raise DatoInvalidoError("La garantía necesita tipo y referencia")
