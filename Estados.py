from abc import ABC, abstractmethod

from dominio.excepciones import AvisoNoPendiente


class EstadoAviso(ABC):
    """State: cada estado decide qué operaciones admite y a qué estado pasa."""

    nombre: str

    @property
    def descarte(self):
        return None

    @abstractmethod
    def agregar_nota(self, aviso, nota):
        """Admite o rechaza la nota."""

    @abstractmethod
    def descartar(self, aviso, descarte):
        """Admite o rechaza el descarte."""

    def _rechazar(self, operacion):
        raise AvisoNoPendiente(
            f"No se puede {operacion}: el aviso está {self.nombre.lower()}"
        )


class EstadoPendiente(EstadoAviso):
    nombre = "Pendiente"

    def agregar_nota(self, aviso, nota):
        aviso._guardar_nota(nota)

    def descartar(self, aviso, descarte):
        aviso._cambiar_estado(EstadoDescartado(descarte))


class _EstadoEvaluado(EstadoAviso):
    """Un aviso evaluado rechaza todo lo que exige estar pendiente."""

    def agregar_nota(self, aviso, nota):
        self._rechazar("agregar una nota")

    def descartar(self, aviso, descarte):
        self._rechazar("descartar")


class EstadoAceptado(_EstadoEvaluado):
    nombre = "Aceptado"


class EstadoDescartado(_EstadoEvaluado):
    nombre = "Descartado"

    def __init__(self, descarte):
        self._descarte = descarte

    @property
    def descarte(self):
        return self._descarte