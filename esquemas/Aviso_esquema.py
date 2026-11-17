from dataclasses import dataclass
from datetime import datetime
from dominio.Aviso import Aviso
from dominio.Estados import EstadoAceptado, EstadoDescartado, EstadoPendiente
from dominio.Excepciones import DatoInvalido
from dominio.Reportante import Reportante
from dominio.Valores import Descarte, Nota, Ubicacion


def _sin_descarte(descarte):
    if descarte is not None:
        raise DatoInvalido("Un aviso que no está descartado no puede tener descarte")


def _pendiente(descarte):
    _sin_descarte(descarte)
    return EstadoPendiente()


def _aceptado(descarte):
    _sin_descarte(descarte)
    return EstadoAceptado()


def _descartado(descarte):
    if descarte is None:
        raise DatoInvalido("Un aviso descartado necesita su descarte")
    return EstadoDescartado(Descarte(descarte["justificacion"], descarte["fecha_hora"]))


# etiqueta de persistencia -> cómo se arma el estado de dominio
_ESTADOS = {
    "pendiente": _pendiente,
    "aceptado": _aceptado,
    "descartado": _descartado,
}


@dataclass(frozen=True)
class AvisoEsquema:
    identificador: str
    reportante_id: str
    reportante_nombre: str
    ubicacion: str
    tipo: str
    gravedad_estimada: str
    descripcion: str
    fecha_hora_registro: datetime
    estado: str
    notas: tuple = ()
    descarte: dict | None = None

    @staticmethod
    def desde_dominio(aviso):
        """Dominio -> esquema (como `from_domain` de la clase 9)."""
        descarte = aviso.descarte
        return AvisoEsquema(
            identificador=aviso.identificador,
            reportante_id=aviso.reportante.identificador,
            reportante_nombre=aviso.reportante.nombre,
            ubicacion=aviso.ubicacion.texto,
            tipo=aviso.tipo.value,
            gravedad_estimada=aviso.gravedad_estimada.value,
            descripcion=aviso.descripcion,
            fecha_hora_registro=aviso.fecha_hora_registro,
            estado=aviso.estado.nombre.lower(),
            notas=tuple(
                {"autor_id": n.autor.identificador, "autor_nombre": n.autor.nombre,
                 "texto": n.texto, "fecha_hora": n.fecha_hora}
                for n in aviso.notas),
            descarte=None if descarte is None else
            {"justificacion": descarte.justificacion, "fecha_hora": descarte.fecha_hora},
        )

    def a_dominio(self):
        """Esquema -> dominio: reconstruye el aviso tal como estaba, sin repetir sus operaciones."""
        try:
            armar_estado = _ESTADOS[self.estado]
        except KeyError:
            raise DatoInvalido(f"Estado desconocido: {self.estado!r}") from None
        return Aviso(
            self.identificador,
            Reportante(self.reportante_id, self.reportante_nombre),
            Ubicacion(self.ubicacion), self.tipo, self.gravedad_estimada, self.descripcion, self.fecha_hora_registro,
            estado=armar_estado(self.descarte),
            notas=tuple(Nota(Reportante(n["autor_id"], n["autor_nombre"]), n["texto"], n["fecha_hora"]) for n in self.notas),
        )