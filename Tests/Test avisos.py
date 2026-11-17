from datetime import datetime, timedelta
import pytest
from dominio.Aviso import Aviso
from dominio.Catalogos import Gravedad, TipoSituacion
from dominio.Excepciones import AvisoNoPendiente, DatoInvalido, ValorFueraDeCatalogo
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


def test_esquema_desde_dominio_copia_los_datos_como_valores_planos(aviso, reportante):
    aviso.agregar_nota(reportante, "Novedad", hace(5))

    esquema = AvisoEsquema.desde_dominio(aviso)

    assert esquema.identificador == "av-1"
    assert esquema.reportante_id == "rep-1"
    assert esquema.ubicacion == "Costanera 1200, Rosario"
    assert esquema.tipo == "inundacion"
    assert esquema.gravedad_estimada == "media"
    assert esquema.estado == "pendiente"
    assert esquema.notas[0]["texto"] == "Novedad"
    assert esquema.descarte is None


def test_ida_y_vuelta_conserva_aviso_pendiente_con_sus_notas_en_orden(aviso, reportante):
    aviso.agregar_nota(reportante, "Primera", hace(5))
    aviso.agregar_nota(reportante, "Segunda", hace(10))

    restaurado = AvisoEsquema.desde_dominio(aviso).a_dominio()

    assert restaurado.estado.nombre == "Pendiente"
    assert restaurado.notas == aviso.notas
    assert [n.texto for n in restaurado.notas] == ["Primera", "Segunda"]
    assert restaurado.ubicacion == aviso.ubicacion
    assert restaurado.tipo is aviso.tipo
    assert restaurado.gravedad_estimada is aviso.gravedad_estimada


def test_ida_y_vuelta_conserva_aviso_descartado_con_justificacion_y_fecha(aviso):
    aviso.descartar("Aviso duplicado", hace(30))

    restaurado = AvisoEsquema.desde_dominio(aviso).a_dominio()

    assert restaurado.estado.nombre == "Descartado"
    assert restaurado.descarte == aviso.descarte
    assert restaurado.descarte.justificacion == "Aviso duplicado"


def test_el_aviso_restaurado_sigue_aplicando_las_reglas_del_dominio(aviso, reportante):
    aviso.descartar("Aviso duplicado", hace(30))
    restaurado = AvisoEsquema.desde_dominio(aviso).a_dominio()

    with pytest.raises(AvisoNoPendiente):
        restaurado.agregar_nota(reportante, "Nota tardía", hace(60))
    with pytest.raises(AvisoNoPendiente):
        restaurado.descartar("Otra", hace(60))
    assert restaurado.descarte.justificacion == "Aviso duplicado"


def test_esquema_arma_un_aviso_aceptado_sin_implementar_aceptar():
    aviso = AvisoEsquema(**datos_basicos(estado="aceptado")).a_dominio()

    assert aviso.estado.nombre == "Aceptado"
    assert aviso.descarte is None


def test_esquema_con_estado_desconocido_se_rechaza():
    with pytest.raises(DatoInvalido):
        AvisoEsquema(**datos_basicos(estado="archivado")).a_dominio()


def test_esquema_descartado_sin_descarte_se_rechaza():
    with pytest.raises(DatoInvalido):
        AvisoEsquema(**datos_basicos(estado="descartado", descarte=None)).a_dominio()


@pytest.mark.parametrize("estado", ["pendiente", "aceptado"])
def test_esquema_no_descartado_con_descarte_se_rechaza(estado):
    descarte = {"justificacion": "Motivo", "fecha_hora": AHORA}
    with pytest.raises(DatoInvalido):
        AvisoEsquema(**datos_basicos(estado=estado, descarte=descarte)).a_dominio()


def test_esquema_con_tipo_fuera_de_catalogo_se_rechaza_al_convertir():
    with pytest.raises(ValorFueraDeCatalogo):
        AvisoEsquema(**datos_basicos(tipo="terremoto")).a_dominio()


def test_el_esquema_es_inmutable():
    esquema = AvisoEsquema(**datos_basicos())
    with pytest.raises(AttributeError):
        esquema.estado = "aceptado"