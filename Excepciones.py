class ErrorDeDominio(Exception):
    """Base de todas las violaciones de reglas de negocio."""


class DatoInvalido(ErrorDeDominio):
    """Un dato obligatorio falta o está vacío."""


class ValorFueraDeCatalogo(DatoInvalido):
    """El valor no pertenece a un catálogo cerrado (tipo de situación, gravedad)."""


class JustificacionVacia(DatoInvalido):
    """Descartar exige una justificación que no esté vacía."""


class NotaInvalida(DatoInvalido):
    """Una nota necesita autor y texto."""


class AvisoNoPendiente(ErrorDeDominio):
    """El aviso ya fue evaluado: no admite nuevas notas ni nuevas evaluaciones."""


class AutorNoAutorizado(ErrorDeDominio):
    """Solo el reportante del aviso puede agregarle notas."""