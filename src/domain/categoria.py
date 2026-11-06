from .base import RaizDeAgregado
from .errores import DatoInvalidoError, SinCupoError


class CategoriaHabitacion(RaizDeAgregado):
    """Tipo de habitación del catálogo (Estándar, Doble, Suite...) con su cupo."""

    def __init__(self, id, descripcion, tarifa, cupo_disponible, habilitada=True):
        super().__init__()
        self.id = id
        self.descripcion = descripcion
        self.tarifa = tarifa
        self.cupo_disponible = cupo_disponible
        self.habilitada = habilitada

    def reservar_cupo(self, cantidad):
        if cantidad <= 0:
            raise DatoInvalidoError("La cantidad debe ser mayor a cero")
        if cantidad > self.cupo_disponible:
            raise SinCupoError(
                f"Sin cupo en {self.descripcion}: hay {self.cupo_disponible}, "
                f"se pidieron {cantidad}"
            )
        self.cupo_disponible -= cantidad

    def liberar_cupo(self, cantidad):
        if cantidad <= 0:
            raise DatoInvalidoError("La cantidad debe ser mayor a cero")
        self.cupo_disponible += cantidad
