from .base import RaizDeAgregado
from .errores import HabitacionNoDisponibleError
from .eventos import (HabitacionDisponible, HabitacionFueraDeServicio,
                      HabitacionPendienteDeLimpieza)
from .maquina_estados import MAQUINA_HABITACION
from .valor import EstadoHabitacion


class Habitacion(RaizDeAgregado):
    """Cuarto físico del hotel. Solo cambia de estado por operaciones del negocio."""

    def __init__(self, id, numero, categoria_id, estado=EstadoHabitacion.DISPONIBLE):
        super().__init__()
        self.id = id
        self.numero = numero
        self.categoria_id = categoria_id
        self.estado = estado

    def _transitar(self, accion):
        self.estado = MAQUINA_HABITACION.siguiente(self.estado, accion)

    def entregar(self):
        # R1: solo se entrega una habitación disponible (limpia y lista)
        if self.estado != EstadoHabitacion.DISPONIBLE:
            raise HabitacionNoDisponibleError(
                f"La habitación {self.numero} no está disponible ({self.estado.value})"
            )
        self._transitar("entregar")

    def enviar_a_limpieza(self):
        self._transitar("enviar_a_limpieza")
        self._registrar(HabitacionPendienteDeLimpieza(self.id))

    def marcar_disponible(self):
        # R8: solo una habitación pendiente de limpieza vuelve a estar disponible
        self._transitar("marcar_disponible")
        self._registrar(HabitacionDisponible(self.id))

    def marcar_fuera_de_servicio(self):
        self._transitar("fuera_de_servicio")
        self._registrar(HabitacionFueraDeServicio(self.id))

    def reactivar(self):
        self._transitar("reactivar")
        self._registrar(HabitacionPendienteDeLimpieza(self.id))
