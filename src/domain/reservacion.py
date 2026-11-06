from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .base import RaizDeAgregado
from .errores import (ConflictoError, DatoInvalidoError, PrecondicionNoCumplidaError,
                      SinCupoError)
from .especificaciones import (CategoriasHabilitadas, ContextoDeReservacion, CupoSuficiente,
                               beneficio_preferente, explicar_incumplimiento, puede_procesarse)
from .eventos import (BeneficioPreferenteOtorgado, CheckInRealizado, CheckOutRealizado,
                      HabitacionCambiada, NoShowRegistrado, ReservacionAutorizada,
                      ReservacionCancelada, ReservacionConfirmada, ReservacionSolicitada)
from .maquina_estados import MAQUINA_RESERVACION
from .valor import EstadoReservacion


# CAMBIO PIA (regla del BRD y de la Actividad 5): cancelación gratuita con >= 48 h.
HORAS_CANCELACION_GRATUITA = 48


@dataclass(frozen=True)
class CambioDeHabitacion:
    fecha: datetime
    origen_id: str
    destino_id: str
    motivo: str
    responsable: str


class Reservacion(RaizDeAgregado):
    """Compromiso del hotel con un huésped; su estado lo gobierna la máquina de estados."""

    def __init__(self, id, huesped_id, lineas, referencia="", fecha_solicitud=None,
                 autorizada=False, promocion_activa=False, estado=EstadoReservacion.SOLICITADA):
        super().__init__()
        self.id = id
        self.huesped_id = huesped_id
        self.lineas = tuple(lineas)
        self.referencia = referencia
        self.fecha_solicitud = fecha_solicitud
        self.autorizada = autorizada
        self.promocion_activa = promocion_activa
        self.estado = estado
        self.garantia = None
        self.habitacion_id = None
        self.beneficio_preferente = False
        self.cambios = []
        self.penalidad_cancelacion = Decimal("0")  # CAMBIO PIA (no se persiste)

    @classmethod
    def solicitar(cls, *args, **kwargs):
        reservacion = cls(*args, **kwargs)
        reservacion._registrar(ReservacionSolicitada(reservacion.id))
        return reservacion

    @property
    def total(self):
        return sum((linea.subtotal for linea in self.lineas), Decimal("0"))

    def cantidades_por_categoria(self):
        cantidades = {}
        for linea in self.lineas:
            cantidades[linea.categoria_id] = cantidades.get(linea.categoria_id, 0) + linea.cantidad
        return cantidades

    def autorizar(self):
        if self.estado != EstadoReservacion.SOLICITADA:
            raise ConflictoError("Solo se autoriza una reservación solicitada")
        if not self.autorizada:
            self.autorizada = True
            self._registrar(ReservacionAutorizada(self.id))

    def confirmar(self, huesped, categorias, umbral_beneficio):
        siguiente = MAQUINA_RESERVACION.siguiente(self.estado, "confirmar")
        contexto = ContextoDeReservacion(self, huesped, categorias)
        basica = puede_procesarse() & CategoriasHabilitadas()
        if not basica.es_satisfecha_por(contexto):
            raise PrecondicionNoCumplidaError(
                "No cumple las condiciones para confirmarse: " + explicar_incumplimiento(contexto)
            )
        if not CupoSuficiente().es_satisfecha_por(contexto):
            raise SinCupoError("No hay cupo suficiente para las categorías solicitadas")
        for categoria_id, cantidad in self.cantidades_por_categoria().items():
            categorias[categoria_id].reservar_cupo(cantidad)
        self.estado = siguiente
        self._registrar(ReservacionConfirmada(self.id))
        if beneficio_preferente(umbral_beneficio).es_satisfecha_por(contexto):
            self.beneficio_preferente = True
            self._registrar(BeneficioPreferenteOtorgado(self.id))

    def _liberar_cupo(self, categorias):
        for categoria_id, cantidad in self.cantidades_por_categoria().items():
            categorias[categoria_id].liberar_cupo(cantidad)

    def cancelar(self, categorias, ahora=None, fecha_llegada=None, autorizacion_jefe=False):
        """Cancela y devuelve la penalidad (CAMBIO PIA).

        Regla del BRD: sin costo con >= 48 h de anticipación; si no, cargo de 1 noche
        (tarifa de la primera línea). Solo aplica a reservaciones CONFIRMADAS (con garantía);
        el Jefe de Reservaciones/Administración puede exentarla (autorizacion_jefe=True).
        """
        estaba_confirmada = self.estado == EstadoReservacion.CONFIRMADA
        self.estado = MAQUINA_RESERVACION.siguiente(self.estado, "cancelar")
        penalidad = Decimal("0")
        if estaba_confirmada:
            self._liberar_cupo(categorias)
            tardia = (ahora is not None and fecha_llegada is not None
                      and fecha_llegada - ahora < timedelta(hours=HORAS_CANCELACION_GRATUITA))
            if tardia and not autorizacion_jefe and self.lineas:
                penalidad = self.lineas[0].tarifa
        self.penalidad_cancelacion = penalidad
        self._registrar(ReservacionCancelada(self.id, penalidad))
        return penalidad

    def registrar_no_show(self, categorias):
        self.estado = MAQUINA_RESERVACION.siguiente(self.estado, "no_show")
        self._liberar_cupo(categorias)
        self._registrar(NoShowRegistrado(self.id))

    def registrar_check_in(self, habitacion, identidad_verificada, garantia):
        siguiente = MAQUINA_RESERVACION.siguiente(self.estado, "check_in")
        if not identidad_verificada:
            raise PrecondicionNoCumplidaError("Falta verificar la identidad del huésped")
        if garantia is None:
            raise PrecondicionNoCumplidaError("Falta registrar la garantía")
        if habitacion.categoria_id not in self.cantidades_por_categoria():
            raise ConflictoError("La habitación no corresponde a una categoría reservada")
        habitacion.entregar()
        self.garantia = garantia
        self.habitacion_id = habitacion.id
        self.estado = siguiente
        self._registrar(CheckInRealizado(self.id, habitacion.id))

    def cambiar_habitacion(self, actual, nueva, motivo, responsable, fecha):
        siguiente = MAQUINA_RESERVACION.siguiente(self.estado, "cambiar_habitacion")
        if actual.id != self.habitacion_id:
            raise ConflictoError("La habitación actual no es la asignada a la reservación")
        if nueva.id == actual.id:
            raise DatoInvalidoError("La nueva habitación debe ser distinta a la actual")
        nueva.entregar()
        actual.enviar_a_limpieza()
        self.cambios.append(CambioDeHabitacion(fecha, actual.id, nueva.id, motivo, responsable))
        self.habitacion_id = nueva.id
        self.estado = siguiente
        self._registrar(HabitacionCambiada(self.id, actual.id, nueva.id))

    def registrar_check_out(self, habitacion):
        siguiente = MAQUINA_RESERVACION.siguiente(self.estado, "check_out")
        if habitacion.id != self.habitacion_id:
            raise ConflictoError("La habitación no es la asignada a la reservación")
        habitacion.enviar_a_limpieza()
        self.estado = siguiente
        self._registrar(CheckOutRealizado(self.id))
