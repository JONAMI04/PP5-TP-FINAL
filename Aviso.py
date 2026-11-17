from dominio.catalogos import Gravedad, TipoSituacion
from dominio.estados import EstadoPendiente
from dominio.excepciones import AutorNoAutorizado, DatoInvalido
from dominio.valores import Descarte, Nota


class Aviso:
    """Entidad. Conoce su estado y, por lo tanto, decide qué operaciones admite."""

    def __init__(self, identificador, reportante, ubicacion, tipo,
                 gravedad_estimada, descripcion, fecha_hora_registro,
                 estado, notas=()):
        """Constructor de reconstitución (tests, persistencia).
        Para crear un aviso nuevo se usa `Aviso.registrar`."""
        if reportante is None:
            raise DatoInvalido("El aviso necesita un reportante")
        if descripcion is None or not str(descripcion).strip():
            raise DatoInvalido("La descripción no puede estar vacía")
        if fecha_hora_registro is None:
            raise DatoInvalido("El aviso necesita fecha y hora de registro")
        self._identificador = identificador
        self._reportante = reportante
        self._ubicacion = ubicacion
        self._tipo = TipoSituacion.desde(tipo)
        self._gravedad_estimada = Gravedad.desde(gravedad_estimada)
        self._descripcion = descripcion
        self._fecha_hora_registro = fecha_hora_registro
        self._estado = estado
        self._notas = list(notas)

    @classmethod
    def registrar(cls, identificador, reportante, ubicacion, tipo,
                  gravedad_estimada, descripcion, fecha_hora):
        return cls(identificador, reportante, ubicacion, tipo,
                   gravedad_estimada, descripcion, fecha_hora,
                   estado=EstadoPendiente())

    # --- consultas (solo lectura)
    @property
    def identificador(self):
        return self._identificador

    @property
    def reportante(self):
        return self._reportante

    @property
    def ubicacion(self):
        return self._ubicacion

    @property
    def tipo(self):
        return self._tipo

    @property
    def gravedad_estimada(self):
        return self._gravedad_estimada

    @property
    def descripcion(self):
        return self._descripcion

    @property
    def fecha_hora_registro(self):
        return self._fecha_hora_registro

    @property
    def estado(self):
        return self._estado

    @property
    def notas(self):
        return tuple(self._notas)

    @property
    def descarte(self):
        return self._estado.descarte

    # --- operaciones: validan todo antes de modificar (R6)
    def agregar_nota(self, autor, texto, fecha_hora):
        if autor != self._reportante:
            raise AutorNoAutorizado("Solo el reportante del aviso puede agregarle notas")
        nota = Nota(autor, texto, fecha_hora)
        self._estado.agregar_nota(self, nota)

    def descartar(self, justificacion, fecha_hora):
        descarte = Descarte(justificacion, fecha_hora)
        self._estado.descartar(self, descarte)

    # --- ganchos que usan los estados (no son parte de la API pública)
    def _guardar_nota(self, nota):
        self._notas.append(nota)

    def _cambiar_estado(self, nuevo_estado):
        self._estado = nuevo_estado