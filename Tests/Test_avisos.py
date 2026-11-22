from datetime import datetime, timedelta
import pytest
from dominio.Aviso import Aviso
from dominio.Catalogos import Gravedad, TipoSituacion
from dominio.Excepciones import (
    AutorNoAutorizado,
    AvisoNoPendiente,
    DatoInvalido,
    JustificacionVacia,
    NotaInvalida,
    ValorFueraDeCatalogo,
)
from dominio.Reportante import Reportante
from dominio.Valores import Ubicacion
from esquemas.Aviso_esquema import AvisoEsquema

AHORA = datetime(2026, 11, 20, 10, 0)


def hace(minutos):
    return AHORA + timedelta(minutes=minutos)


@pytest.fixture
def reportante():
    return Reportante("rep-1", "Ana Gómez")


@pytest.fixture
def aviso(reportante):
    return Aviso.registrar("av-1", reportante, Ubicacion("Costanera 1200, Rosario"),
                           TipoSituacion.INUNDACION, Gravedad.MEDIA,
                           "Agua en la calle", AHORA)


def datos_basicos(**cambios):
    datos = dict(identificador="av-9", reportante_id="rep-1", reportante_nombre="Ana Gómez",
                 ubicacion="Centro", tipo="incendio", gravedad_estimada="alta",
                 descripcion="Humo", fecha_hora_registro=AHORA, estado="pendiente")
    datos.update(cambios)
    return datos


def estado_del_aviso(aviso):
    return (
        aviso.identificador,
        aviso.reportante,
        aviso.ubicacion,
        aviso.tipo,
        aviso.gravedad_estimada,
        aviso.descripcion,
        aviso.fecha_hora_registro,
        aviso.estado,
        aviso.notas,
        aviso.descarte,
    )


def test_r1_aviso_registrado_queda_pendiente_sin_notas_ni_descarte(aviso, reportante):
    assert aviso.estado.nombre == "Pendiente"
    assert aviso.notas == ()
    assert aviso.descarte is None
    assert aviso.identificador == "av-1"
    assert aviso.reportante == reportante
    assert aviso.ubicacion == Ubicacion("Costanera 1200, Rosario")
    assert aviso.tipo is TipoSituacion.INUNDACION
    assert aviso.gravedad_estimada is Gravedad.MEDIA
    assert aviso.descripcion == "Agua en la calle"
    assert aviso.fecha_hora_registro == AHORA


@pytest.mark.parametrize("ubicacion", [None, "Costanera 1200, Rosario"])
def test_r1_registrar_rechaza_ubicacion_ausente_o_invalida(reportante, ubicacion):
    with pytest.raises(DatoInvalido):
        Aviso.registrar(
            "av-1", reportante, ubicacion, TipoSituacion.INUNDACION,
            Gravedad.MEDIA, "Agua en la calle", AHORA,
        )


@pytest.mark.parametrize(
    ("tipo", "gravedad"),
    [("terremoto", Gravedad.MEDIA), (TipoSituacion.INUNDACION, "extrema")],
)
def test_r1_registrar_rechaza_valores_fuera_de_catalogo(reportante, tipo, gravedad):
    with pytest.raises(ValorFueraDeCatalogo):
        Aviso.registrar(
            "av-1", reportante, Ubicacion("Centro"), tipo,
            gravedad, "Agua en la calle", AHORA,
        )


@pytest.mark.parametrize(
    ("reportante", "descripcion", "fecha_hora"),
    [
        (None, "Agua en la calle", AHORA),
        (Reportante("rep-1", "Ana Gómez"), "   ", AHORA),
        (Reportante("rep-1", "Ana Gómez"), "Agua en la calle", None),
    ],
)
def test_r1_registrar_rechaza_datos_obligatorios_ausentes(reportante, descripcion, fecha_hora):
    with pytest.raises(DatoInvalido):
        Aviso.registrar(
            "av-1", reportante, Ubicacion("Centro"), TipoSituacion.INUNDACION,
            Gravedad.MEDIA, descripcion, fecha_hora,
        )


def test_r2_agregar_nota_conserva_autor_texto_y_fecha_hora(aviso, reportante):
    fecha_hora = hace(5)

    aviso.agregar_nota(reportante, "El agua está bajando", fecha_hora)

    assert len(aviso.notas) == 1
    assert aviso.notas[0].autor == reportante
    assert aviso.notas[0].texto == "El agua está bajando"
    assert aviso.notas[0].fecha_hora == fecha_hora
    assert aviso.estado.nombre == "Pendiente"


def test_r2_dos_notas_se_conservan_en_orden(aviso, reportante):
    aviso.agregar_nota(reportante, "Primera actualización", hace(5))
    aviso.agregar_nota(reportante, "Segunda actualización", hace(10))

    assert [nota.texto for nota in aviso.notas] == [
        "Primera actualización",
        "Segunda actualización",
    ]
    assert [nota.fecha_hora for nota in aviso.notas] == [hace(5), hace(10)]


def test_r2_r6_solo_el_reportante_agrega_notas_y_el_rechazo_no_modifica_aviso(aviso):
    antes = estado_del_aviso(aviso)

    with pytest.raises(AutorNoAutorizado):
        aviso.agregar_nota(Reportante("rep-2", "Luis"), "Actualización", hace(5))

    assert estado_del_aviso(aviso) == antes


def test_r3_agregar_nota_no_modifica_los_datos_originales(aviso, reportante):
    originales = (
        aviso.identificador,
        aviso.reportante,
        aviso.ubicacion,
        aviso.tipo,
        aviso.gravedad_estimada,
        aviso.descripcion,
        aviso.fecha_hora_registro,
        aviso.estado,
    )

    aviso.agregar_nota(reportante, "Actualización", hace(5))

    assert (
        aviso.identificador,
        aviso.reportante,
        aviso.ubicacion,
        aviso.tipo,
        aviso.gravedad_estimada,
        aviso.descripcion,
        aviso.fecha_hora_registro,
        aviso.estado,
    ) == originales
    assert len(aviso.notas) == 1


def test_r4_descartar_aviso_pendiente_conserva_justificacion_y_fecha(aviso):
    fecha_hora = hace(30)

    aviso.descartar("Aviso duplicado", fecha_hora)

    assert aviso.estado.nombre == "Descartado"
    assert aviso.descarte.justificacion == "Aviso duplicado"
    assert aviso.descarte.fecha_hora == fecha_hora


def test_r4_r6_justificacion_vacia_rechaza_sin_modificar_aviso(aviso):
    antes = estado_del_aviso(aviso)

    with pytest.raises(JustificacionVacia):
        aviso.descartar("   ", hace(30))

    assert estado_del_aviso(aviso) == antes


def test_r5_r6_aviso_descartado_rechaza_nueva_nota_sin_modificarlo(aviso, reportante):
    aviso.descartar("Aviso duplicado", hace(30))
    antes = estado_del_aviso(aviso)

    with pytest.raises(AvisoNoPendiente):
        aviso.agregar_nota(reportante, "Actualización tardía", hace(60))

    assert estado_del_aviso(aviso) == antes


def test_r5_r6_aviso_descartado_rechaza_segundo_descarte_sin_modificarlo(aviso):
    aviso.descartar("Aviso duplicado", hace(30))
    antes = estado_del_aviso(aviso)

    with pytest.raises(AvisoNoPendiente):
        aviso.descartar("Otro motivo", hace(60))

    assert estado_del_aviso(aviso) == antes


def test_r5_r6_aviso_aceptado_rechaza_nota_y_descarte_sin_modificarlo():
    aviso = AvisoEsquema(**datos_basicos(estado="aceptado")).a_dominio()
    antes = estado_del_aviso(aviso)

    with pytest.raises(AvisoNoPendiente):
        aviso.agregar_nota(aviso.reportante, "Actualización tardía", hace(5))

    assert estado_del_aviso(aviso) == antes

    with pytest.raises(AvisoNoPendiente):
        aviso.descartar("No corresponde", hace(30))

    assert estado_del_aviso(aviso) == antes


def test_r6_nota_vacia_rechaza_sin_modificar_aviso(aviso, reportante):
    antes = estado_del_aviso(aviso)

    with pytest.raises(NotaInvalida):
        aviso.agregar_nota(reportante, "   ", hace(5))

    assert estado_del_aviso(aviso) == antes