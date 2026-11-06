from dataclasses import dataclass


@dataclass
class Huesped:
    id: str
    nombre: str
    es_preferente: bool = False
    activo: bool = True
    ciudad: str = ""
