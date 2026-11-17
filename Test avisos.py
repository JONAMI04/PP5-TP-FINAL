from datetime import datetime, timedelta

import pytest

from dominio.aviso import Aviso
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.estados import EstadoAceptado
from dominio.excepciones import (AutorNoAutorizado, AvisoNoPendiente, DatoInvalido,
                                 JustificacionVacia, NotaInvalida, ValorFueraDeCatalogo)
from dominio.reportante import Reportante
from dominio.valores import Descarte, Nota, Ubicacion

AHORA = datetime(2026, 11, 20, 10, 0)


def hace(minutos):
    return AHORA + timedelta(minutes=minutos)


@pytest.fixture
def reportante():
    return Reportante("rep-1", "Ana Gómez")


@pytest.fixture
def otro_reportante():
    return Reportante("rep-2", "Luis Pérez")


@pytest.fixture
def aviso(reportante):
    return Aviso.registrar(
        "av-1", reportante, Ubicacion("Costanera 1200, Rosario"),
        TipoSituacion.INUNDACION, Gravedad.MEDIA,
        "Agua en la calle, hay personas aisladas", AHORA)


@pytest.fixture
def aviso_descartado(aviso):
    aviso.descartar("Aviso duplicado", hace(5))
    return aviso


@pytest.fixture
def aviso_aceptado(reportante):
    # No existe `aceptar` todavía: se reconstruye el objeto ya en estado Aceptado.
    return Aviso("av-2", reportante, Ubicacion("Ruta 9 km 300"),
                 TipoSituacion.ACCIDENTE_VIAL, Gravedad.ALTA,
                 "Choque entre dos vehículos", AHORA, estado=EstadoAceptado())


def datos_originales(aviso):
    return (aviso.identificador, aviso.reportante, aviso.ubicacion, aviso.tipo,
            aviso.gravedad_estimada, aviso.descripcion, aviso.fecha_hora_registro)


# ---------------------------------------------------------------- R1
def test_r1_aviso_recien_registrado_esta_pendiente_sin_notas_ni_descarte(aviso):
    assert aviso.estado.nombre == "Pendiente"
    assert aviso.notas == ()
    assert aviso.descarte is None


def test_r1_aviso_conserva_los_datos_con_los_que_fue_registrado(aviso, reportante):
    assert aviso.reportante == reportante
    assert aviso.ubicacion == Ubicacion("Costanera 1200, Rosario")
    assert aviso.tipo is TipoSituacion.INUNDACION
    assert aviso.gravedad_estimada is Gravedad.MEDIA
    assert aviso.descripcion == "Agua en la calle, hay personas aisladas"
    assert aviso.fecha_hora_registro == AHORA


@pytest.mark.parametrize("tipo", ["terremoto", "INUNDACION", "", None, 42])
def test_r1_tipo_de_situacion_fuera_del_catalogo_no_llega_al_aviso(reportante, tipo):
    with pytest.raises(ValorFueraDeCatalogo):
        Aviso.registrar("av-9", reportante, Ubicacion("Centro"), tipo,
                        Gravedad.BAJA, "Descripción", AHORA)


@pytest.mark.parametrize("gravedad", ["critica", "ALTA", "", None, 3])
def test_r1_gravedad_fuera_del_catalogo_no_llega_al_aviso(reportante, gravedad):
    with pytest.raises(ValorFueraDeCatalogo):
        Aviso.registrar("av-9", reportante, Ubicacion("Centro"),
                        TipoSituacion.INCENDIO, gravedad, "Descripción", AHORA)


def test_r1_los_catalogos_aceptan_tambien_el_valor_textual(reportante):
    aviso = Aviso.registrar("av-9", reportante, Ubicacion("Centro"),
                            "incendio", "alta", "Humo en un edificio", AHORA)
    assert aviso.tipo is TipoSituacion.INCENDIO
    assert aviso.gravedad_estimada is Gravedad.ALTA


@pytest.mark.parametrize("descripcion", ["", "   ", None])
def test_r1_aviso_sin_descripcion_es_rechazado(reportante, descripcion):
    with pytest.raises(DatoInvalido):
        Aviso.registrar("av-9", reportante, Ubicacion("Centro"),
                        TipoSituacion.INCENDIO, Gravedad.BAJA, descripcion, AHORA)


def test_r1_aviso_sin_reportante_es_rechazado():
    with pytest.raises(DatoInvalido):
        Aviso.registrar("av-9", None, Ubicacion("Centro"),
                        TipoSituacion.INCENDIO, Gravedad.BAJA, "Descripción", AHORA)


@pytest.mark.parametrize("texto", ["", "  ", None])
def test_r1_ubicacion_vacia_es_rechazada(texto):
    with pytest.raises(DatoInvalido):
        Ubicacion(texto)


# ---------------------------------------------------------------- R2
def test_r2_agregar_nota_a_aviso_pendiente_conserva_autor_fecha_y_hora(aviso, reportante):
    aviso.agregar_nota(reportante, "Ya son tres las personas aisladas", hace(10))

    assert aviso.notas == (Nota(reportante, "Ya son tres las personas aisladas", hace(10)),)
    nota = aviso.notas[0]
    assert nota.autor == reportante
    assert nota.fecha_hora == hace(10)
    assert aviso.estado.nombre == "Pendiente"


def test_r2_dos_notas_se_conservan_en_el_orden_en_que_llegaron(aviso, reportante):
    aviso.agregar_nota(reportante, "Primera novedad", hace(10))
    aviso.agregar_nota(reportante, "Segunda novedad", hace(20))

    assert [nota.texto for nota in aviso.notas] == ["Primera novedad", "Segunda novedad"]
    assert [nota.fecha_hora for nota in aviso.notas] == [hace(10), hace(20)]


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_r2_nota_sin_texto_es_rechazada_y_no_se_agrega(aviso, reportante, texto):
    with pytest.raises(NotaInvalida):
        aviso.agregar_nota(reportante, texto, hace(1))
    assert aviso.notas == ()


def test_r2_solo_el_reportante_del_aviso_puede_agregar_notas(aviso, otro_reportante):
    with pytest.raises(AutorNoAutorizado):
        aviso.agregar_nota(otro_reportante, "Nota ajena", hace(1))
    assert aviso.notas == ()
    assert aviso.estado.nombre == "Pendiente"


def test_r2_una_nota_no_puede_existir_sin_autor():
    with pytest.raises(NotaInvalida):
        Nota(None, "Texto", AHORA)


# ---------------------------------------------------------------- R3
def test_r3_agregar_nota_no_modifica_los_datos_originales(aviso, reportante):
    antes = datos_originales(aviso)

    aviso.agregar_nota(reportante, "Novedad", hace(10))

    assert datos_originales(aviso) == antes
    assert aviso.ubicacion == Ubicacion("Costanera 1200, Rosario")
    assert aviso.tipo is TipoSituacion.INUNDACION
    assert aviso.gravedad_estimada is Gravedad.MEDIA
    assert aviso.descripcion == "Agua en la calle, hay personas aisladas"


# ---------------------------------------------------------------- R4
def test_r4_descartar_aviso_pendiente_conserva_justificacion_y_fecha(aviso):
    aviso.descartar("Falsa alarma confirmada por bomberos", hace(30))

    assert aviso.estado.nombre == "Descartado"
    assert aviso.descarte == Descarte("Falsa alarma confirmada por bomberos", hace(30))
    assert aviso.descarte.justificacion == "Falsa alarma confirmada por bomberos"
    assert aviso.descarte.fecha_hora == hace(30)


@pytest.mark.parametrize("justificacion", ["", "   ", "\n\t ", None])
def test_r4_r6_descartar_con_justificacion_vacia_se_rechaza_y_el_aviso_sigue_pendiente(
        aviso, justificacion):
    antes = datos_originales(aviso)

    with pytest.raises(JustificacionVacia):
        aviso.descartar(justificacion, hace(5))

    assert aviso.estado.nombre == "Pendiente"
    assert aviso.descarte is None
    assert aviso.notas == ()
    assert datos_originales(aviso) == antes


# ---------------------------------------------------------------- R5
def test_r5_r6_aviso_descartado_rechaza_nuevas_notas(aviso_descartado, reportante):
    with pytest.raises(AvisoNoPendiente):
        aviso_descartado.agregar_nota(reportante, "Nota tardía", hace(60))

    assert aviso_descartado.notas == ()
    assert aviso_descartado.estado.nombre == "Descartado"


def test_r5_r6_aviso_descartado_rechaza_un_segundo_descarte_y_conserva_la_justificacion_original(
        aviso_descartado):
    original = aviso_descartado.descarte

    with pytest.raises(AvisoNoPendiente):
        aviso_descartado.descartar("Otra justificación", hace(90))

    assert aviso_descartado.descarte == original
    assert aviso_descartado.descarte.justificacion == "Aviso duplicado"
    assert aviso_descartado.estado.nombre == "Descartado"


def test_r5_aviso_aceptado_rechaza_nuevas_notas(aviso_aceptado, reportante):
    with pytest.raises(AvisoNoPendiente):
        aviso_aceptado.agregar_nota(reportante, "Nota tardía", hace(60))

    assert aviso_aceptado.notas == ()
    assert aviso_aceptado.estado.nombre == "Aceptado"


def test_r5_aviso_aceptado_rechaza_ser_descartado(aviso_aceptado):
    with pytest.raises(AvisoNoPendiente):
        aviso_aceptado.descartar("Ya no hace falta", hace(60))

    assert aviso_aceptado.estado.nombre == "Aceptado"
    assert aviso_aceptado.descarte is None


# ---------------------------------------------------------------- R6 / encapsulamiento
def test_r6_nota_rechazada_en_aviso_evaluado_no_deja_cambios_en_los_datos(
        aviso_descartado, reportante):
    antes = datos_originales(aviso_descartado)
    with pytest.raises(AvisoNoPendiente):
        aviso_descartado.agregar_nota(reportante, "Nota tardía", hace(60))
    assert datos_originales(aviso_descartado) == antes


def test_las_notas_expuestas_no_se_pueden_modificar_desde_afuera(aviso, reportante):
    aviso.agregar_nota(reportante, "Novedad", hace(1))
    with pytest.raises(AttributeError):
        aviso.notas.append(Nota(reportante, "Colada", hace(2)))
    assert len(aviso.notas) == 1


def test_el_estado_no_se_puede_reemplazar_desde_afuera(aviso):
    with pytest.raises(AttributeError):
        aviso.estado = EstadoAceptado()
    assert aviso.estado.nombre == "Pendiente"


def test_notas_y_descartes_son_valores_inmutables(reportante):
    nota = Nota(reportante, "Texto", AHORA)
    descarte = Descarte("Motivo", AHORA)
    with pytest.raises(AttributeError):
        nota.texto = "Otro"
    with pytest.raises(AttributeError):
        descarte.justificacion = "Otro"


def test_dos_reportantes_con_el_mismo_identificador_son_el_mismo():
    assert Reportante("rep-1", "Ana Gómez") == Reportante("rep-1", "Ana G.")
    assert Reportante("rep-1", "Ana Gómez") != Reportante("rep-2", "Ana Gómez")