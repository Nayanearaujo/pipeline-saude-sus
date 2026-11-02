# Indicadores de Negócio · SIH/SUS (abril/2026)

Levantamento dos **10 indicadores** desenhados na Aula 1 a partir da exploração da camada `bronze`, classificados nas três pilhas da Aula 2 (*Dá*, *Dá, mas...* e *Não dá*) e com as **definições fechadas** na Aula 3 antes da escrita dos marts SQL.

---

## 1. Os 10 indicadores e as tabelas de origem

| # | Indicador | Pergunta que responde | Tabela e coluna de origem (`bronze`) | Pilha (Aula 2) | Mart (`ouro`) |
|---|---|---|---|---|---|
| 1 | **Volume de internações aprovadas** | Quantas AIH foram processadas no mês? | `internacoes (N_AIH)` | **Dá** | `01_kpis_gerais` / `02_por_estado` |
| 2 | **Gasto hospitalar total** | Quanto o SUS desembolsou nas AIH aprovadas? | `internacoes (VAL_TOT)` | **Dá** | `01_kpis_gerais` / `02_por_estado` |
| 3 | **Ticket médio e mediana por AIH** | Quanto custa, em média e no meio da fila, uma internação por UF? | `internacoes (VAL_TOT, MUNIC_RES)` | **Dá** | `01_kpis_gerais` / `02_por_estado` |
| 4 | **Permanência média hospitalar** | Quantos dias o paciente permanece internado? | `internacoes (DIAS_PERM)` | **Dá** | `01_kpis_gerais` / `02_por_estado` |
| 5 | **Taxa de mortalidade hospitalar** | Qual a proporção de internações que evoluíram para óbito? | `internacoes (MORTE, N_AIH)` | **Dá, mas...** | `01_kpis_gerais` / `02_por_estado` / `09_mortalidade_por_cid` |
| 6 | **Ranking de diagnósticos (CID-10)** | Quais doenças mais internam no país e em cada UF? | `internacoes (DIAG_PRINC)` + `cid10 (codigo, descricao)` | **Dá, mas...** | `03_top_diagnosticos` / `06_top_diagnosticos_brasil` |
| 7 | **Perfil demográfico (faixa etária e sexo)** | Quem interna no SUS por idade e sexo? | `internacoes (IDADE, COD_IDADE, SEXO)` | **Dá, mas...** | `04_perfil_demografico` / `08_perfil_demografico_brasil` |
| 8 | **Curva diária de entradas** | Como as admissões se distribuem ao longo dos dias do mês? | `internacoes (DT_INTER)` | **Dá, mas...** | `05_internacoes_diarias` / `07_internacoes_diarias_brasil` |
| 9 | **Concentração municipal do gasto (Pareto 80/20)** | Quantos municípios concentram 80% do orçamento do SIH? | `internacoes (MUNIC_RES, VAL_TOT)` + `municipios (codigo, municipio, uf)` | **Dá, mas...** | `10_municipios_pareto` |
| 10 | **Taxa de reinternação em 30 dias por paciente** | Quantos pacientes voltaram a internar em menos de 30 dias? | Não existe CPF/CNS na RD pública do SIH | **Não dá** | Fora do escopo (exige base identificada) |

---

## 2. As três pilhas da Aula 2

### Pilha 1 · "Dá" (direto da tabela-fato após tipagem)
- **Indicadores 1, 2, 3 e 4:** dependem apenas da deduplicação por `N_AIH` e da conversão estrita de `VAL_TOT` para `DECIMAL(12,2)` e `DIAS_PERM` para `INTEGER` em `prata.internacoes`.

### Pilha 2 · "Dá, mas..." (exige decodificação ou recorte explícito)
- **Indicador 5 (Mortalidade por CID):** calcular letalidade bruta sem filtro de volume coloca doenças com 1 caso e 1 óbito (100%) no topo. Exige `HAVING count(*) >= 100` no mart `09_mortalidade_por_cid`.
- **Indicador 6 (Diagnósticos):** `DIAG_PRINC` vem sem ponto (`O800`) e pode trazer subcategorias ausentes na tabela oficial da OMS. Exige `LEFT JOIN prata.cid10` com `COALESCE(c.doenca, 'nao classificado')`.
- **Indicador 7 (Idade em anos):** a coluna `IDADE` não está sempre em anos : `COD_IDADE` define a unidade (`0` a `3` são minutos/horas/dias/meses, `4` é anos e `5` soma 100 anos). Sem combinar `IDADE` + `COD_IDADE` na camada `prata`, recém-nascidos de 5 meses entrariam na faixa `1-14`.
- **Indicador 8 (Série diária):** o arquivo mensal do SIH é fechado por **competência de apresentação**, não por data de entrada. A série de entradas pode ter um recorte diferente do consolidado; a execução local confirmou 703.067 entradas em abril/2026 e 535.167 anteriores, com competência 2026/04 em toda a Bronze. Exige recortar `data_internacao` ao mês de referência nos marts `05` e `07` (o SQL deriva o mês da data mais frequente, via `mode()`; em abril/2026, de 01/04 a 30/04).
- **Indicador 9 (Municípios):** o SIH grava o código IBGE com **6 dígitos** (sem dígito verificador), enquanto a API do IBGE entrega 7 dígitos. Exige padronizar `substr(codigo, 1, 6)` na camada `prata`.

### Pilha 3 · "Não dá" (o dado público não sustenta)
- **Indicador 10 (Reinternação por paciente):** a base pública reduzida do SIH (`RD*.dbc`) é anonimizada por determinação da LGPD e do Ministério da Saúde. Uma linha é uma **AIH (autorização de internação)**, não um indivíduo único. Medir reinternação ou mortalidade pós-alta exigiria relacionamento nominal com o CNS/CPF ou com o SIM (Sistema de Informações sobre Mortalidade).

---

## 3. Definições fechadas antes do SQL (Aula 3)

1. **Grão da tabela-fato (`prata.internacoes`):** 1 linha = 1 AIH aprovada (`aih` único). Após a seleção por AIH, registros sem valor financeiro são excluídos; entradas não numéricas interrompem a conversão estrita. A deduplicação prioriza registros com valor preenchido, depois a alta mais recente e o maior valor normalizado em `DECIMAL(12,2)`, com desempates estáveis definidos em `pipeline/transformacao.py`. Na execução local validada, foram excluídas 529 AIHs duplicadas e zero linhas por ausência de valor.

2. **Custo médio e mediana:** calculados sobre `valor_total` (`DECIMAL(12,2)`) de todas as AIH válidas da UF ou do país (`AVG(valor_total)` e `MEDIAN(valor_total)`).
3. **Taxa de mortalidade hospitalar:** `100.0 * COUNT(*) FILTER (WHERE morte) / COUNT(*)`, onde `morte = TRUE` corresponde exclusivamente a `MORTE = '1'` no SIH (óbito ocorrido durante a internação).
4. **Participação percentual (`pct_internacoes`, `pct_valor`, `pct_do_total`) e Pareto (`pct_acumulado`):** calculados sempre nos marts SQL com *window functions* (`SUM(...) OVER ()`), nunca na camada visual (`painel.py` ou `app.py`).
