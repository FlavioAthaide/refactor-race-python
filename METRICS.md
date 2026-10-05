# METRICS

Medições feitas com as ferramentas do enunciado (`pytest`, `pytest-cov`, `radon`, `ruff`).
**Antes** = baseline do código legado (commit `83f6327`, antes de qualquer refatoração).
**Depois** = estado final do repositório.

| Indicador                         | Antes                         | Depois                           |
|------------------------------------|--------------------------------|-----------------------------------|
| Testes passando                   | 4 / 4                          | 67 / 67                           |
| Quantidade de testes               | 4                              | 67                                |
| Cobertura de testes                | 83% (72 stmts, 12 sem cobertura) | 100% (106 stmts, 0 sem cobertura) |
| Complexidade da função principal   | E (34) — `process_order`       | A (1) — `process_order`; maior função do módulo: B (6) |
| Complexidade média                 | E (34.0) — 1 bloco              | A (2.5) — 14 blocos               |
| Índice de manutenibilidade         | A (51.69)                      | A (42.01)                         |
| Problemas identificados pelo Ruff  | 4 (3x SIM102, 1x PLR1730)      | 0                                  |

## Análise

- **Melhorou muito:** complexidade ciclomática (34 → 1 na função principal, média 2,5),
  cobertura (83% → 100%), quantidade de testes (4 → 67) e Ruff (4 → 0).
- **Piorou numericamente:** o índice de manutenibilidade do Radon caiu (51,69 → 42,01),
  embora continue na faixa A (> 20). O MI é calculado a partir de linhas de código,
  volume de Halstead e complexidade; o módulo ganhou constantes, docstrings e mais
  funções (mais linhas), o que penaliza o índice mesmo com a complexidade por função
  muito menor. Interpretamos esse número junto com os demais, sem ignorá-lo: ele não
  indica perda de qualidade estrutural, mas mostra que "mais linhas" tem custo nessa
  métrica.
- **Preservação de comportamento:** os 4 testes originais continuam intactos; foram
  adicionados testes de caracterização (validados contra o código legado *antes* de
  refatorar) e uma comparação aleatória legado × refatorado (20.000 pedidos, mesmo
  resultado e mesma saída impressa).

## Como reproduzir

```bash
pip install -r requirements-dev.txt
pytest -v
python tools/compare_with_legacy.py   # legado x refatorado, 20.000 pedidos
pytest --cov=legacy_checkout --cov-report=term-missing
radon cc src/legacy_checkout.py -s -a
radon mi src/legacy_checkout.py -s
ruff check src/legacy_checkout.py --statistics
```

> Observação: o Ruff aplica as regras configuradas no ambiente. Se o resultado no seu
> Colab for diferente (principalmente o "Antes"), atualize a tabela com os valores
> reais medidos pela equipe.
