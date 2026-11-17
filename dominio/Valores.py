from dataclasses import dataclass
from datetime import datetime
from dominio.Excepciones import DatoInvalido, JustificacionVacia, NotaInvalida


def _vacio(texto):
    return texto is None or not str(texto).strip()

@dataclass(frozen=True)
class Ubicacion:
    texto: str

    def __post_init__(self):
        if _vacio(self.texto):
            raise DatoInvalido("La ubicación no puede estar vacía")


@dataclass(frozen=True)
class Nota:
    """Valor inmutable: autor, texto, fecha y hora nacen juntos."""

    autor: object
    texto: str
    fecha_hora: datetime

    def __post_init__(self):
        if self.autor is None or self.fecha_hora is None:
            raise NotaInvalida("La nota necesita autor, fecha y hora")
        if _vacio(self.texto):
            raise NotaInvalida("La nota no puede estar vacía")


@dataclass(frozen=True)
class Descarte:
    """Valor inmutable: no existe un descarte sin justificación."""

    justificacion: str
    fecha_hora: datetime

    def __post_init__(self):
        if _vacio(self.justificacion):
            raise JustificacionVacia("Descartar exige una justificación")
        if self.fecha_hora is None:
            raise DatoInvalido("El descarte necesita fecha y hora")