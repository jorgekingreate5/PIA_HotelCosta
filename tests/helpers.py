from datetime import datetime
from decimal import Decimal

from src.domain.categoria import CategoriaHabitacion
from src.domain.habitacion import Habitacion
from src.domain.huesped import Huesped
from src.infrastructure.composicion import crear_contenedor
from src.infrastructure.configuracion import Configuracion

RELOJ = lambda: datetime(2026, 10, 20, 12, 0)  # noqa: E731


def contenedor_basico(reloj=RELOJ, pasarela=None):
    """Hotel pequeño: 2 huéspedes (uno preferente), 2 categorías y 3 habitaciones."""
    c = crear_contenedor(Configuracion(), reloj=reloj, pasarela=pasarela)
    with c.nueva_uow() as uow:
        uow.huespedes.guardar(Huesped("H1", "Ana", es_preferente=False, activo=True))
        uow.huespedes.guardar(Huesped("H2", "Beto", es_preferente=True, activo=True))
        uow.huespedes.guardar(Huesped("H3", "Carla", es_preferente=False, activo=False))
        uow.categorias.guardar(CategoriaHabitacion("C1", "Estándar", Decimal("1000"), 5))
        uow.categorias.guardar(CategoriaHabitacion("C2", "Suite", Decimal("2000"), 1))
        uow.categorias.guardar(CategoriaHabitacion("C3", "Cerrada", Decimal("500"), 9, False))
        uow.habitaciones.guardar(Habitacion("HAB-101", "101", "C1"))
        uow.habitaciones.guardar(Habitacion("HAB-102", "102", "C1"))
        uow.habitaciones.guardar(Habitacion("HAB-201", "201", "C2"))
        uow.guardar_cambios()
    return c
