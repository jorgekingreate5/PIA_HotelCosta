"""Contratos que la aplicación necesita del exterior (los implementa infraestructura)."""
from abc import ABC, abstractmethod

from ..domain.repositorios import (RepositorioDeCategorias, RepositorioDeCuentas,
                                   RepositorioDeHabitaciones, RepositorioDeHuespedes,
                                   RepositorioDeReservaciones)


class UnidadDeTrabajo(ABC):
    """Agrupa los cambios de un caso de uso: se guardan todos o ninguno."""

    huespedes: RepositorioDeHuespedes
    categorias: RepositorioDeCategorias
    habitaciones: RepositorioDeHabitaciones
    reservaciones: RepositorioDeReservaciones
    cuentas: RepositorioDeCuentas

    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, tipo, valor, traza): ...

    @abstractmethod
    def guardar_cambios(self): ...


class PublicadorDeEventos(ABC):
    @abstractmethod
    def publicar(self, evento): ...


class PasarelaDeGarantia(ABC):
    """Servicio externo que valida la garantía (tarjeta o depósito) del huésped."""

    @abstractmethod
    def validar(self, garantia):
        """Devuelve True si se aprueba. Puede lanzar TimeoutError si no responde."""
