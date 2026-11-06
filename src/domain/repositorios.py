"""Contratos de persistencia que necesita el dominio (sin tecnología concreta)."""
from abc import ABC, abstractmethod


class RepositorioDeHuespedes(ABC):
    @abstractmethod
    def obtener(self, huesped_id): ...

    @abstractmethod
    def guardar(self, huesped): ...


class RepositorioDeCategorias(ABC):
    @abstractmethod
    def obtener(self, categoria_id): ...

    @abstractmethod
    def guardar(self, categoria): ...

    @abstractmethod
    def listar(self): ...


class RepositorioDeHabitaciones(ABC):
    @abstractmethod
    def obtener(self, habitacion_id): ...

    @abstractmethod
    def guardar(self, habitacion): ...

    @abstractmethod
    def listar(self): ...


class RepositorioDeReservaciones(ABC):
    @abstractmethod
    def obtener(self, reservacion_id): ...

    @abstractmethod
    def guardar(self, reservacion): ...

    @abstractmethod
    def listar(self): ...


class RepositorioDeCuentas(ABC):
    @abstractmethod
    def obtener_por_reservacion(self, reservacion_id): ...

    @abstractmethod
    def guardar(self, cuenta): ...
