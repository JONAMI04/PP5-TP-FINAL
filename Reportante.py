from dataclasses import dataclass, field

from dominio.excepciones import DatoInvalido


@dataclass(frozen=True)
class Reportante:
    """Entidad: dos reportantes son el mismo si comparten identificador."""

    identificador: str
    nombre: str = field(compare=False)

    def __post_init__(self):
        if not str(self.identificador).strip() or not str(self.nombre).strip():
            raise DatoInvalido("El reportante necesita identificador y nombre")