from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .base import RaizDeAgregado
from .errores import CreditoExcedidoError, CuentaError, DatoInvalidoError
from .eventos import CargoRegistrado


# CAMBIO PIA (regla del BRD y de la Actividad 5): tope de crédito de consumos por habitación.
TOPE_CREDITO = Decimal("3000")
CONCEPTO_HOSPEDAJE = "Hospedaje"


@dataclass(frozen=True)
class Cargo:
    fecha: datetime
    concepto: str
    monto: Decimal
    empleado_id: str


class CuentaEstancia(RaizDeAgregado):
    """Lo que el huésped debe y ha pagado durante su estancia."""

    def __init__(self, id, reservacion_id):
        super().__init__()
        self.id = id
        self.reservacion_id = reservacion_id
        self.cargos = []
        self.pagado = Decimal("0")
        self.abierta = True

    @classmethod
    def abrir(cls, id, reservacion_id, monto_hospedaje, fecha):
        cuenta = cls(id, reservacion_id)
        cuenta.registrar_cargo(CONCEPTO_HOSPEDAJE, monto_hospedaje, "sistema", fecha)
        return cuenta

    @property
    def total(self):
        return sum((c.monto for c in self.cargos), Decimal("0"))

    @property
    def saldo(self):
        return self.total - self.pagado

    @property
    def credito_usado(self):
        """Consumos (sin hospedaje) menos lo ya pagado: lo que el hotel tiene 'fiado'."""
        consumos = sum((c.monto for c in self.cargos if c.concepto != CONCEPTO_HOSPEDAJE),
                       Decimal("0"))
        return max(consumos - self.pagado, Decimal("0"))

    def registrar_cargo(self, concepto, monto, empleado_id, fecha,
                        autorizacion_administracion=False):
        # R5: solo se agregan cargos a una cuenta abierta y con monto mayor a cero
        if not self.abierta:
            raise CuentaError("La cuenta ya está cerrada")
        if monto <= 0:
            raise DatoInvalidoError("El cargo debe ser mayor a cero")
        # R7 (CAMBIO PIA): tope de crédito $3,000 MXN; se supera con pago parcial previo
        # (reduce credito_usado) o con autorización de Administración.
        if (concepto != CONCEPTO_HOSPEDAJE and not autorizacion_administracion
                and self.credito_usado + monto > TOPE_CREDITO):
            raise CreditoExcedidoError(
                f"El consumo supera el tope de crédito de {TOPE_CREDITO} MXN; "
                "requiere pago parcial o autorización de Administración")
        self.cargos.append(Cargo(fecha, concepto, monto, empleado_id))
        self._registrar(CargoRegistrado(self.reservacion_id, concepto, monto))

    def registrar_pago(self, monto):
        if not self.abierta:
            raise CuentaError("La cuenta ya está cerrada")
        if monto < 0:
            raise DatoInvalidoError("El pago no puede ser negativo")
        self.pagado += monto

    def cerrar(self):
        # R6: no se cierra una cuenta con saldo pendiente
        if not self.abierta:
            raise CuentaError("La cuenta ya está cerrada")
        if self.saldo > 0:
            raise CuentaError(f"Hay un saldo pendiente de {self.saldo}")
        self.abierta = False
