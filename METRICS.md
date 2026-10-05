# METRICS

Medições feitas com as ferramentas do enunciado (`pytest`, `pytest-cov`, `radon`, `ruff`).
Coluna **Antes** = baseline do código legado, medida ANTES de qualquer refatoração.

| Indicador                        | Antes                | Depois |
|-----------------------------------|-----------------------|--------|
| Testes passando                  | 4 / 4                | |
| Quantidade de testes              | 4                     | |
| Cobertura de testes               | 83% (12 linhas sem cobertura) | |
| Complexidade da função principal  | E (34) — `process_order` | |
| Complexidade média                | E (34.0)              | |
| Índice de manutenibilidade        | A (51.69)             | |
| Problemas identificados pelo Ruff | 4 (3x SIM102, 1x PLR1730) | |

## Como reproduzir

```bash
pip install -r requirements-dev.txt
pytest -v
python tools/compare_with_legacy.py
pytest --cov=legacy_checkout --cov-report=term-missing
radon cc src/legacy_checkout.py -s -a
radon mi src/legacy_checkout.py -s
ruff check src/legacy_checkout.py --statistics
```
