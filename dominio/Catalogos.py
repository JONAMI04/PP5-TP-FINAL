from enum import Enum
from Excepciones import ValorFueraDeCatalogo

class _Catalogo(Enum):
    """Catálogo cerrado: un valor que no es miembro nunca llega al dominio."""

    @classmethod
    def desde(cls, valor):
        """Acepta un miembro o su valor; cualquier otra cosa se rechaza."""
        try:
            return cls(valor)
        except ValueError:
            raise ValorFueraDeCatalogo(
                f"{valor!r} no pertenece al catálogo {cls.__name__}"
            ) from None


class TipoSituacion(_Catalogo):
    INUNDACION = "inundacion"
    INCENDIO = "incendio"
    ACCIDENTE_VIAL = "accidente_vial"


class Gravedad(_Catalogo):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"