"""Domain Events: hechos del negocio que ya ocurrieron."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EventoDeDominio:
    pass


@dataclass(frozen=True)
class ReservacionSolicitada(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class ReservacionAutorizada(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class ReservacionConfirmada(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class BeneficioPreferenteOtorgado(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class ReservacionCancelada(EventoDeDominio):
    reservacion_id: str
    penalidad: Decimal = Decimal("0")  # CAMBIO PIA: cargo por cancelación tardía


@dataclass(frozen=True)
class NoShowRegistrado(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class CheckInRealizado(EventoDeDominio):
    reservacion_id: str
    habitacion_id: str


@dataclass(frozen=True)
class CargoRegistrado(EventoDeDominio):
    reservacion_id: str
    concepto: str
    monto: Decimal


@dataclass(frozen=True)
class HabitacionCambiada(EventoDeDominio):
    reservacion_id: str
    origen_id: str
    destino_id: str


@dataclass(frozen=True)
class CheckOutRealizado(EventoDeDominio):
    reservacion_id: str


@dataclass(frozen=True)
class HabitacionPendienteDeLimpieza(EventoDeDominio):
    habitacion_id: str


@dataclass(frozen=True)
class HabitacionDisponible(EventoDeDominio):
    habitacion_id: str


@dataclass(frozen=True)
class HabitacionFueraDeServicio(EventoDeDominio):
    habitacion_id: str
