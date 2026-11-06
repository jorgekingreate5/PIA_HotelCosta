"""Ejecuta los 120 casos y las 20 transiciones del PIA y guarda los resultados en CSV."""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.infrastructure.datos_pia import DatosPIA, ejecutar_casos_de_prueba  # noqa: E402
from src.infrastructure.ejecucion_pia import ejecutar_transiciones  # noqa: E402


def guardar(ruta, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


if __name__ == "__main__":
    salida = RAIZ / "docs" / "evidencias"
    salida.mkdir(parents=True, exist_ok=True)
    casos = ejecutar_casos_de_prueba(DatosPIA(RAIZ / "datos"))
    transiciones = ejecutar_transiciones(RAIZ / "datos")
    guardar(salida / "resultados_casos_prueba.csv", casos)
    guardar(salida / "resultados_transiciones.csv", transiciones)
    print(f"{len(casos)} casos y {len(transiciones)} transiciones guardados en {salida}")
