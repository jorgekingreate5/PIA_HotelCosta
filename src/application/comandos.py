"""Comandos: peticiones que MODIFICAN información (uno por caso de uso)."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from ..domain.valor import Garantia


@dataclass(frozen=True)
class SolicitarReservacion:
    huesped_id: str
    lineas: list = field(default_factory=list)  # [(categoria_id, cantidad)]
    reservacion_id: Optional[str] = None
    referencia: str = ""
    fecha_solicitud: Optional[date] = None
    autorizada: bool = False
    promocion_activa: bool = False


@dataclass(frozen=True)
class RealizarCheckIn:
    reservacion_id: str
    habitacion_id: str
    identidad_verificada: bool
    garantia: Optional[Garantia] = None


@dataclass(frozen=True)
class RegistrarCargo:
    reservacion_id: str
    concepto: str
    monto: Decimal
    empleado_id: str
    autorizacion_administracion: bool = False  # CAMBIO PIA: excede el tope de crédito


@dataclass(frozen=True)
class CambiarHabitacion:
    reservacion_id: str
    nueva_habitacion_id: str
    motivo: str
    responsable: str


@dataclass(frozen=True)
class RealizarCheckOut:
    reservacion_id: str
    monto_pagado: Decimal = Decimal("0")
