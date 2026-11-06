"""La matriz de trazabilidad no puede apuntar a pruebas, historias o endpoints que no existen."""
import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
ESTE = "test_trazabilidad.py"


def filas():
    with open(RAIZ / "docs" / "matriz_trazabilidad.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pruebas_definidas():
    nombres = set()
    for archivo in (RAIZ / "tests").rglob("test_*.py"):
        if archivo.name != ESTE:
            nombres |= set(re.findall(r"^def (test_\w+)\(", archivo.read_text(encoding="utf-8"), re.M))
    return nombres


def test_cada_prueba_citada_existe():
    definidas = pruebas_definidas()
    faltantes = [(f["historia"], p) for f in filas() for p in f["pruebas"].split(";")
                 if p not in definidas]
    assert faltantes == []


def test_cada_historia_citada_esta_documentada():
    texto = (RAIZ / "docs" / "historias_usuario.md").read_text(encoding="utf-8")
    assert [f["historia"] for f in filas() if f"## {f['historia']} " not in texto] == []


def test_cada_endpoint_citado_existe_en_la_api():
    codigo = (RAIZ / "src" / "api" / "app.py").read_text(encoding="utf-8")
    faltantes = []
    for fila in filas():
        for endpoint in fila["endpoint"].split("|"):
            ruta = endpoint.split(" ", 1)[1]
            if f'"{ruta}"' not in codigo:
                faltantes.append(endpoint)
    assert faltantes == []


def test_se_cubren_las_19_historias_implementadas():
    historias = {f["historia"] for f in filas()}
    assert historias == {f"US-{n:02d}" for n in range(1, 20)}


def test_hay_al_menos_15_historias_con_gherkin():
    texto = (RAIZ / "docs" / "historias_usuario.md").read_text(encoding="utf-8")
    assert texto.count("Scenario:") >= 30
    assert len(re.findall(r"^## US-\d+", texto, re.M)) >= 15
