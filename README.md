# CRCE — Avance 1: avisos y notas

Dominio en Python (solo biblioteca estándar) con sus tests.

```
uv run pytest        # o: python -m pytest
```

- `dominio/`: Aviso, estados, valores, catálogos y excepciones.
- `esquemas/`: DTO del aviso; convierte entre dominio y datos planos (conoce al dominio, no al revés).
- `tests/test_avisos.py`: pruebas de R1 a R6. `test_esquemas.py`: frontera. `test_diseno.py`: reglas de diseño.
- `docs/avance-1.md`: diagramas de clases y de estados, tarjetas CRC y decisiones de diseño.

Entrega: `git tag avance-1 && git push origin avance-1`.