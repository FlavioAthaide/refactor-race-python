# REFactor Race Python

## EQUIPE
- Flavio Gabriel Athaide de Oliveira
R.A: 325144298

## DESCRIÇÃO
Refatoração de um sistema legado de processamento de pedidos (`process_order`),
preservando o comportamento existente e comprovando a melhoria com testes e métricas
(pytest, pytest-cov, radon e ruff).

```bash
pip install -r requirements-dev.txt
pytest -v
```

## DIAGNÓSTICO INICIAL
1. `process_order` concentrava cálculo, validação de regras, formatação, armazenamento
   (`ORDERS_PROCESSED`) e impressão em uma só função: complexidade ciclomática **E (34)**.
2. O subtotal era calculado duas vezes (`total1` nunca usado + `subtotal`): código duplicado e morto.
3. Condicionais aninhadas em `if/else/if/else` para o desconto por tipo de cliente.
4. Números mágicos (`0.15`, `1000`, `1.8`, `0.4`, `25%`...) e strings mágicas espalhados.
5. Cadeia de `if/elif` para taxas por estado e `state == "MG" or ...` repetido.
6. Busca de produtos duplicados com dois `for` aninhados: O(n²) comparações.
7. Nomes pouco claros (`x`, `total1`, `taxa`, `frete`) e mistura de português/inglês.
8. Baixa testabilidade: não era possível testar frete ou imposto sem executar tudo
   (e sem imprimir na tela).
9. Estado global mutável (`ORDERS_PROCESSED`) alterado dentro da regra de negócio.

## CODE SMELLS ENCONTRADOS
| Smell | Onde | Por quê é problema |
|---|---|---|
| Long Function / God Function | `process_order` | Muitas responsabilidades, difícil de entender e testar |
| Código duplicado / morto | `total1` | Custo de manutenção sem benefício |
| Condicionais complexas/aninhadas | desconto, frete, imposto | Difíceis de ler; propensas a erro |
| Magic numbers / magic strings | ao longo da função | Regra de negócio sem nome e repetida |
| Estrutura inadequada | duplicados O(n²) | Ineficiente e verboso |
| Estado global | `ORDERS_PROCESSED` | Efeito colateral escondido |
| Comentários explicando código confuso | "procura ... de forma bem pouco elegante" | Sintoma de código que precisava de uma função com nome |

## REFATORAÇÕES REALIZADAS

### 1. Remover cálculo duplicado e extrair subtotal/peso
- **Problema:** dois loops idênticos para o subtotal (um sem uso).
- **Alteração:** removido `total1`; criadas `calculate_subtotal` e `calculate_total_weight`.
- **Justificativa:** elimina duplicação e código morto; cada regra passa a ter um nome e ser testável.

### 2. Extract Function + constantes + mapeamento (descontos, cupons, frete, impostos, pontos)
- **Problema:** regras de negócio misturadas, números/strings mágicos, `if/elif` para taxas.
- **Alteração:** `calculate_customer_discount`, `calculate_coupon_discount`, `calculate_discount`
  (com `min` para o teto de 25%), `calculate_shipping`, `calculate_tax` (`TAX_RATES.get`),
  `calculate_points`; constantes como `EXPRESS_SHIPPING_MULTIPLIER`; `state in SOUTHEAST_STATES`.
- **Justificativa:** reduz a complexidade (E 34 → maior função B 6), remove aninhamento e
  centraliza cada regra em um só lugar.

### 3. Separar responsabilidades e otimizar duplicados
- **Problema:** cálculo, formatação, armazenamento e impressão na mesma função; duplicados em O(n²).
- **Alteração:** `calculate_order` (função pura, retorna `OrderCalculation`), `build_order_result`,
  `print_order_summary`; `process_order` só orquestra. `find_duplicate_products` usa `Counter` (O(n)),
  mantendo a ordem de primeira aparição.
- **Justificativa:** o cálculo passa a ser testável sem I/O; menos comparações com o mesmo resultado
  (refactor **e** otimização).

## TESTES ADICIONADOS
- `tests/test_checkout_characterization.py` (40 testes): descontos por tipo de cliente e limites
  (799/800, 999/1000), cupons (PROMO10, PROMO20 com limite de 500, VIP50, inválido, sensível a
  maiúsculas), teto de 25%, quantidade zero, frete (grátis, região, peso, expresso, sem peso),
  impostos por estado (parametrizado), total, pontos, duplicados (0, 3 repetições, ordem),
  histórico e saída impressa. Escritos e validados contra o código **legado** antes de refatorar.
- `tests/test_checkout_units.py` (23 testes): funções extraídas isoladamente.

Nenhum teste original foi removido ou alterado.

## MÉTRICAS ANTES E DEPOIS
Ver [METRICS.md](METRICS.md). Resumo: testes 4 → 67, cobertura 83% → 100%,
complexidade da função principal E (34) → A (1), média E (34.0) → A (2.5), Ruff 4 → 0.
O índice de manutenibilidade do Radon caiu de 51,69 para 42,01 (ambos A); explicação em METRICS.md.

## DECISÕES TÉCNICAS
- Mantivemos o nome `legacy_checkout.py` e a assinatura de `process_order` porque os testes
  (inclusive possíveis testes ocultos) e os comandos de medição dependem deles.
- Mantivemos `ORDERS_PROCESSED` e os `print`, pois fazem parte do comportamento atual.
- **Não** implementamos os Tickets 1 (qty <= 0 → ValueError), 2 (cupom sem diferenciar
  maiúsculas) e 3 (pontos de fidelidade): são novos requisitos e o enunciado só manda
  implementá-los quando liberados pelo professor. Até o momento da entrega, nenhum ticket
  havia sido liberado em aula. Há um teste documentando o comportamento atual dos cupons
  (`test_coupons_are_case_sensitive_in_current_behavior`).
- Preservamos comportamentos estranhos existentes, pois refatorar não é corrigir (ver débitos).
- Adicionamos `pytest.ini` (`pythonpath = src`) para os testes importarem o módulo.

## USO DE INTELIGÊNCIA ARTIFICIAL

- **Ferramenta utilizada:** Claude (Anthropic).
- **Finalidade:** apoiar a equipe na identificação de code smells, na extração de funções,
  na escrita de testes de caracterização e na elaboração da documentação (README e METRICS).
- **Comandos/pedidos feitos à IA:**
  - "Leia o código legado e identifique os principais problemas de qualidade."
  - "Escreva testes de caracterização que comprovem o comportamento atual antes de refatorar."
  - "Extraia as regras de desconto, frete, imposto e pontos em funções separadas, substituindo
    números e strings mágicas por constantes nomeadas."
  - "Otimize a busca de produtos duplicados, que hoje é O(n²)."
  - "Gere um script que compare o código antigo e o novo em milhares de pedidos aleatórios."
- **As sugestões foram aceitas, modificadas ou rejeitadas?** A maior parte das sugestões foi
  aceita após leitura e teste pela equipe. Nenhuma sugestão foi aplicada sem antes rodar os
  testes e conferir se o comportamento permanecia o mesmo.
- **Como a equipe validou a solução?** Testes de caracterização escritos e confirmados contra
  o código legado antes de qualquer alteração; execução do `pytest` após cada etapa de
  refatoração; comparação automática entre o código antigo e o novo em 20.000 pedidos
  aleatórios (`tools/compare_with_legacy.py`); e leitura em grupo de cada função final.

## MELHORIAS FUTURAS (débitos técnicos)
1. Quantidade negativa é ignorada no subtotal, mas **reduz o peso** do frete (comportamento
   preservado; provavelmente bug — candidato ao Ticket 1).
2. Cupons e tipos de cliente ainda são strings (`"vip"`, `"PROMO10"`): usar `Enum`/tabela de cupons.
3. Valores monetários em `float`: avaliar `Decimal`.
4. `process_order` ainda imprime e grava em lista global: injetar repositório/logger.
5. Sem validação de entrada (chaves ausentes geram `KeyError`).
6. Renomear o módulo `legacy_checkout` e dividir em módulos (descontos, frete, impostos).
7. Tickets 1, 2 e 3 aguardam liberação do professor.
