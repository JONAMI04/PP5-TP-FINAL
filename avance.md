# Avance 1 — Avisos y notas (CRCE)

## 1. Alcance e interpretación

La rebanada cubre tres operaciones del aviso: **registrarlo**, **agregarle notas** y **descartarlo**
(§2.1, §2.2, §7.1). Aceptar el aviso y crear la emergencia quedan fuera, pero el estado
*Aceptado* existe en el modelo.

Interpretaciones tomadas:

- Un aviso está en **un solo estado a la vez** (Pendiente, Aceptado o Descartado), modelado con el
  patrón State. No hay booleanos sueltos que puedan contradecirse.
- Las **notas** y el **descarte** son valores inmutables. Una nota sin autor o un descarte sin
  justificación no pueden existir.
- La **fecha y hora** siempre entran como parámetro: el dominio nunca llama a `datetime.now()`.
- **Tipo de situación y gravedad** son catálogos cerrados (enumeraciones). Un valor fuera del
  catálogo se rechaza con `ValorFueraDeCatalogo` antes de llegar al aviso.
- **Toda operación valida antes de modificar** (R6): ante un rechazo, el aviso queda como estaba.
- La **ubicación** se modela como valor (`Ubicacion`) con texto obligatorio; la consigna no pide
  más estructura que eso.

## 2. Diagrama de clases

```mermaid
classDiagram
    class Aviso {
        -identificador
        -reportante : Reportante
        -ubicacion : Ubicacion
        -tipo : TipoSituacion
        -gravedad_estimada : Gravedad
        -descripcion : str
        -fecha_hora_registro : datetime
        -estado : EstadoAviso
        -notas : Nota[0..*]
        +registrar(...) Aviso
        +agregar_nota(autor, texto, fecha_hora)
        +descartar(justificacion, fecha_hora)
        +descarte() Descarte
    }
    class Reportante {
        +identificador
        +nombre
    }
    class Ubicacion {
        +texto
    }
    class Nota {
        +autor : Reportante
        +texto : str
        +fecha_hora : datetime
    }
    class Descarte {
        +justificacion : str
        +fecha_hora : datetime
    }
    class EstadoAviso {
        <<abstract>>
        +nombre
        +descarte()
        +agregar_nota(aviso, nota)
        +descartar(aviso, descarte)
    }
    class EstadoPendiente
    class EstadoAceptado
    class EstadoDescartado {
        -descarte : Descarte
    }
    class TipoSituacion {
        <<enumeration>>
        INUNDACION
        INCENDIO
        ACCIDENTE_VIAL
    }
    class Gravedad {
        <<enumeration>>
        BAJA
        MEDIA
        ALTA
    }

    Aviso "1" --> "1" Reportante : reportante
    Aviso "1" --> "1" Ubicacion
    Aviso "1" --> "1" TipoSituacion
    Aviso "1" --> "1" Gravedad
    Aviso "1" *-- "0..*" Nota : notas ordenadas
    Aviso "1" --> "1" EstadoAviso : estado actual
    Nota "0..*" --> "1" Reportante : autor
    EstadoAviso <|-- EstadoPendiente
    EstadoAviso <|-- EstadoAceptado
    EstadoAviso <|-- EstadoDescartado
    EstadoDescartado "1" *-- "1" Descarte
```

**Identidad:** `Aviso` y `Reportante` son entidades (se distinguen por su identificador).
`Nota`, `Descarte` y `Ubicacion` son valores inmutables. Los estados son objetos sin identidad.

## 3. Diagrama de estados del aviso

```mermaid
stateDiagram-v2
    [*] --> Pendiente : registrar
    Pendiente --> Pendiente : agregar_nota
    Pendiente --> Descartado : descartar(justificacion no vacía)
    Pendiente --> Aceptado : aceptar (avance 2)
    Descartado --> [*]
    Aceptado --> [*]
```

Operaciones por estado:

| Operación | Pendiente | Descartado | Aceptado |
|---|---|---|---|
| `agregar_nota` | admite (sigue Pendiente) | **rechaza** `AvisoNoPendiente` | **rechaza** `AvisoNoPendiente` |
| `descartar` | admite → Descartado | **rechaza** `AvisoNoPendiente` | **rechaza** `AvisoNoPendiente` |
| `aceptar` *(avance 2)* | admite → Aceptado | rechazará | rechazará |

Descartado y Aceptado son estados finales: no hay transición de salida.

## 4. Tarjetas CRC

| **Aviso** | |
|---|---|
| **Sabe** | identificador, reportante, ubicación, tipo, gravedad estimada, descripción, fecha y hora de registro, notas, estado actual |
| **Hace** | se registra siempre Pendiente; agrega notas; se descarta; informa su descarte; valida antes de modificar |
| **Colabora con** | Reportante, Nota, Descarte, EstadoAviso, catálogos |

| **EstadoAviso** (Pendiente, Aceptado, Descartado) | |
|---|---|
| **Sabe** | su nombre; el Descartado conoce su Descarte |
| **Hace** | decide si admite o rechaza `agregar_nota` y `descartar`; indica al aviso a qué estado pasar |
| **Colabora con** | Aviso, Nota, Descarte |

| **Nota** (valor) | |
|---|---|
| **Sabe** | autor, texto, fecha y hora |
| **Hace** | se valida al crearse: sin autor o sin texto no existe |
| **Colabora con** | Reportante |

| **Descarte** (valor) | |
|---|---|
| **Sabe** | justificación, fecha y hora |
| **Hace** | se valida al crearse: no existe sin justificación |
| **Colabora con** | — |

| **Reportante** (entidad) | |
|---|---|
| **Sabe** | identificador, nombre |
| **Hace** | se compara con otro por su identificador |
| **Colabora con** | Aviso, Nota |

| **Ubicacion** (valor) | |
|---|---|
| **Sabe** | texto |
| **Hace** | se valida al crearse: no puede ser vacía |
| **Colabora con** | Aviso |

| **TipoSituacion / Gravedad** (catálogos) | |
|---|---|
| **Sabe** | sus valores cerrados |
| **Hace** | `desde(valor)` devuelve el miembro o rechaza con `ValorFueraDeCatalogo` |
| **Colabora con** | Aviso |

## 5. Decisión de diseño: ¿quién verifica que solo el reportante agrega notas?

**Respuesta: el aviso.** La capa que recibe al usuario autenticado solo identifica quién es y
verifica su perfil; la relación "este usuario es el reportante de este aviso" la hace cumplir el dominio.

Justificación:

1. Es una **regla de negocio**, no un detalle de transporte. La consigna (§9) separa los permisos
   del perfil de las relaciones específicas con el recurso.
2. El aviso es quien **conoce a su reportante**: tiene el dato y la decisión.
3. Si la regla viviera solo en la capa de la API, cualquier otro punto de entrada (otra API, un script,
   la interfaz gráfica) podría saltársela. En el dominio, ningún camino la evita.
4. Se puede probar sin HTTP (`test_r2_solo_el_reportante_del_aviso_puede_agregar_notas`).

División de responsabilidades: la API autentica, construye el `Reportante` desde el token y
verifica que el perfil sea Reportante (si no, 403). El aviso compara ese reportante con el suyo y
lanza `AutorNoAutorizado`, que la API traduce también a 403.

El costo es que el aviso conoce el concepto de reportante, pero ya lo tiene como dato propio.

## 6. Reglas y tests

| Regla | Tests (`tests/test_avisos.py`) |
|---|---|
| R1 | `test_r1_aviso_recien_registrado_esta_pendiente_sin_notas_ni_descarte` (escenario 1), `..._conserva_los_datos...`, catálogos fuera de rango, descripción/reportante/ubicación vacíos |
| R2 | `test_r2_agregar_nota_..._conserva_autor_fecha_y_hora` (2), `test_r2_dos_notas_..._en_el_orden...` (3), nota sin texto, autor ajeno |
| R3 | `test_r3_agregar_nota_no_modifica_los_datos_originales` (4) |
| R4 | `test_r4_descartar_aviso_pendiente_conserva_justificacion_y_fecha` (5), `test_r4_r6_descartar_con_justificacion_vacia...` (6) |
| R5 | `test_r5_r6_aviso_descartado_rechaza_nuevas_notas` (7), `..._un_segundo_descarte...` (8), `test_r5_aviso_aceptado_rechaza_nuevas_notas` (9), aceptado rechaza descartar |
| R6 | cada test de rechazo verifica estado, notas y datos después del `pytest.raises`; además `test_r6_nota_rechazada...` |

Escenario 9: no existe `aceptar` todavía, así que el aviso aceptado se arma con el constructor de
reconstitución: `Aviso(..., estado=EstadoAceptado())`. Es el mismo camino que usará la persistencia.