import ast
from pathlib import Path
import pytest

DOMINIO = Path(__file__).resolve().parent.parent / "dominio"
ARCHIVOS = sorted(DOMINIO.glob("*.py"))
PERMITIDOS = {"dominio", "abc", "dataclasses", "datetime", "enum", "__future__", "typing"}


def arbol(archivo):
    return ast.parse(archivo.read_text(encoding="utf-8"))


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_el_dominio_no_pregunta_por_la_clase_de_los_objetos(archivo):
    llamadas = {n.func.id for n in ast.walk(arbol(archivo))
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not llamadas & {"isinstance", "type", "issubclass"}


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_el_dominio_solo_importa_biblioteca_estandar_y_a_si_mismo(archivo):
    importados = set()
    for nodo in ast.walk(arbol(archivo)):
        if isinstance(nodo, ast.Import):
            importados |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module.split(".")[0])
    assert importados <= PERMITIDOS, importados - PERMITIDOS


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_el_dominio_no_toma_la_hora_del_sistema(archivo):
    llamados = {n.attr for n in ast.walk(arbol(archivo)) if isinstance(n, ast.Attribute)}
    assert not llamados & {"now", "utcnow", "today"}