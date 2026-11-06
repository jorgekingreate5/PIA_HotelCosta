"""Máquina de estados: tabla (estado, acción) -> siguiente estado."""
from .errores import TransicionInvalidaError
from .valor import EstadoHabitacion as H
from .valor import EstadoReservacion as R


class MaquinaDeEstados:
    def __init__(self, transiciones):
        self._transiciones = dict(transiciones)

    def siguiente(self, estado, accion):
        try:
            return self._transiciones[(estado, accion)]
        except KeyError:
            raise TransicionInvalidaError(
                f"No se puede '{accion}' desde el estado {estado.value}"
            ) from None

    def acciones_permitidas(self, estado):
        return sorted(a for (e, a) in self._transiciones if e == estado)


MAQUINA_RESERVACION = MaquinaDeEstados({
    (R.SOLICITADA, "confirmar"): R.CONFIRMADA,
    (R.SOLICITADA, "cancelar"): R.CANCELADA,
    (R.CONFIRMADA, "cancelar"): R.CANCELADA,
    (R.CONFIRMADA, "no_show"): R.NO_SHOW,
    (R.CONFIRMADA, "check_in"): R.CHECK_IN,
    (R.CHECK_IN, "cambiar_habitacion"): R.CHECK_IN,
    (R.CHECK_IN, "check_out"): R.CHECK_OUT,
})

MAQUINA_HABITACION = MaquinaDeEstados({
    (H.DISPONIBLE, "entregar"): H.OCUPADA,
    (H.OCUPADA, "enviar_a_limpieza"): H.PENDIENTE_DE_LIMPIEZA,
    (H.PENDIENTE_DE_LIMPIEZA, "marcar_disponible"): H.DISPONIBLE,
    (H.DISPONIBLE, "fuera_de_servicio"): H.FUERA_DE_SERVICIO,
    (H.PENDIENTE_DE_LIMPIEZA, "fuera_de_servicio"): H.FUERA_DE_SERVICIO,
    (H.FUERA_DE_SERVICIO, "reactivar"): H.PENDIENTE_DE_LIMPIEZA,
})
