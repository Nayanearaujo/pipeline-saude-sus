# Internações do SUS · pipeline e dashboard por estado

Pipeline de dados de ponta a ponta sobre as **internações hospitalares do SUS**
(SIH/SUS, DATASUS), em **Python + DuckDB**, com um **dashboard interativo por
estado** em Streamlit. Parte dos microdados oficiais e chega a um painel que
compara os 27 estados em volume, gasto, permanência e mortalidade.

> Recorte: internações de **abril de 2026**, Brasil inteiro, com o **Rio de
> Janeiro** como foco da análise. Dados públicos do Ministério da Saúde.

## Links

- 📊 **Dashboard ao vivo (Streamlit):** https://pipeline-saude-sus.streamlit.app/
- 📖 **Guia do projeto (GitHub Pages):** https://nayanearaujo.github.io/pipeline-saude-sus/
- 💻 **Repositório:** https://github.com/Nayanearaujo/pipeline-saude-sus

## As quatro etapas do pipeline

Este projeto refaz, do zero e com um dataset novo (SUS), o caminho das quatro
aulas do curso: da ingestão ao dashboard.

| Etapa | O que faz | Arquivo |
|---|---|---|
| **1 · Ingestão** | lê os `.dbc` do SIH para a camada bronze, tudo texto | `pipeline/ingestao.py` |
| **2 · Transformação** | tipa e decodifica os códigos do SIH (camada prata) | `pipeline/transformacao.py` |
| **3 · SQL / Marts** | 8 indicadores em **SQL puro** (camada ouro) | `pipeline/marts.py` + `sql/marts/*.sql` |
| **4 · Dashboard + testes** | painel interativo por estado e 27 testes (89%) | `app.py`, `painel.py`, `test/` |

---

## Arquitetura: três camadas

```
data/raw/ (.parquet + .csv)  ──ingestao.py──▶  bronze.*   espelho do arquivo, tudo texto
                                                 │
                                          transformacao.py
                                                 ▼
                                              prata.*     tipado, códigos do SIH decodificados
                                                 │
                                          marts.py + sql/marts/*.sql
                                                 ▼
                                              ouro.*      indicadores por estado
                                                 │
                                          painel.py ──▶ app.py (Streamlit)
```

| Camada | O que é | Quem constrói |
|---|---|---|
| **bronze** | os 3 arquivos como vieram, todas as colunas texto | `pipeline/ingestao.py` |
| **prata** | tipado (valor→`DECIMAL`, data→`DATE`), códigos do SIH decodificados (sexo, UF, óbito), nomes legíveis. 1 linha = 1 internação | `pipeline/transformacao.py` |
| **ouro** | uma tabela por pergunta: KPIs, por estado, diagnósticos, perfil, série diária | `pipeline/marts.py` + `sql/marts/*.sql` |
| **dashboard** | a tela. Nunca calcula: todo número sai de um mart | `painel.py`, `app.py` |

---

## Como baixar os dados

Os microdados do SIH vêm em `.dbc` (formato legado do DATASUS). O
[PySUS](https://github.com/AlertaDengue/PySUS) baixa e converte para parquet.

```bash
uv sync
uv run python baixar_dados.py   # gera data/raw/internacoes.parquet
```

Ainda faltam dois dicionários pequenos em `data/raw/` (salve manualmente):

- **`cid10.csv`** — colunas `codigo,descricao` (código CID-10 → nome da doença).
  Fonte: tabela CID-10 do DATASUS.
- **`municipios.csv`** — colunas `codigo,municipio,uf` (código IBGE → município,
  UF). Fonte: IBGE (lista de municípios).

> Se julho/2026 ainda não estiver publicado (o SIH tem 2 a 4 meses de atraso),
> ajuste `ANO`/`MES` no topo de `baixar_dados.py` para o último mês fechado.

---

## Como rodar

```bash
# baixar os dados (gera data/raw/, não vai para o Git)
uv run python baixar_dados.py             # baixa o SIH-RD de abril/2026 (27 UFs)
uv run python gerar_dicionarios.py        # gera cid10.csv e municipios.csv

# pipeline, do arquivo ao indicador
uv run python -m pipeline.ingestao        # data/raw -> bronze
uv run python -m pipeline.transformacao   # bronze   -> prata
uv run python -m pipeline.marts           # prata    -> ouro

# dashboard interativo
uv run streamlit run app.py               # abre em localhost:8501

# testes
uv run pytest --cov                        # unitários, dado inventado, cobertura >= 70%
```

### Resultado de uma execução (abril/2026, Brasil)

Números reais de uma execução completa do pipeline, para conferência:

```
ingestao      bronze.internacoes  1.238.763 · cid10 7.928 · municipios 5.569
transformacao prata.internacoes   1.238.763 linhas (0 removidas)
marts         8 marts, 88.174 linhas na camada ouro
```

As 1.238.763 internações se distribuem pelas 27 UFs: **SP** lidera com 251.270,
seguido de **MG** (135.007), **PR** (85.532), **BA** (83.766) e **RJ** (78.575).
*(Os dados brutos não ficam no repositório; rode `baixar_dados.py` para gerá-los.)*

---

## O que uma linha representa (grão)

| Tabela prata | Uma linha é… |
|---|---|
| `internacoes` | uma internação (AIH): município, UF, diagnóstico, procedimento, valor, dias, idade, sexo, óbito, datas |
| `cid10` | um código CID-10 e o nome da doença |
| `municipios` | um município do IBGE |
| `ufs` | uma unidade federativa (código, sigla, região) |

A camada prata decodifica os códigos crípticos do SIH: `SEXO` 1/3 → Masculino/
Feminino, `MORTE` → booleano, `DT_INTER` (AAAAMMDD) → data, `VAL_TOT` →
`DECIMAL`, e deriva a UF/região a partir do código IBGE do município.

---

## Indicadores (camada ouro)

Cada mart tem o grão declarado na primeira linha do `.sql`.

| Mart | Pergunta |
|---|---|
| `kpis_gerais` | os números de topo do painel (Brasil) |
| `por_estado` | volume, gasto, custo médio, permanência e mortalidade por UF |
| `top_diagnosticos` / `_brasil` | doenças que mais internam, por UF e nacional |
| `perfil_demografico` / `_brasil` | internações por faixa etária e sexo |
| `internacoes_diarias` / `_brasil` | série diária ao longo do mês |

---

## O dashboard

Abre com a **visão Brasil** e tem um **seletor de estado** que recorta tudo:

- **5 cartões:** internações, gasto total, custo médio, permanência média,
  mortalidade. No "Brasil" vêm do `kpis_gerais`; numa UF, da linha do `por_estado`.
- **Mapa do Brasil** (coroplético por UF) e **ranking de estados**, com métrica
  escolhível (volume, gasto, custo médio, permanência, mortalidade).
- **Custo médio por UF** (desigualdade regional).
- **Top 10 diagnósticos**, **série diária** e **perfil por idade/sexo**,
  recortados pelo estado selecionado.

---

## Estrutura do projeto

```
pipeline-saude-sus/
├── pipeline/            db.py, ingestao.py, transformacao.py, marts.py
├── sql/marts/           8 marts .sql, grão no topo de cada um
├── painel.py            lê os marts, formata e desenha (sem cálculo)
├── app.py               dashboard Streamlit interativo por estado
├── baixar_dados.py      baixa o SIH com PySUS para data/raw/
├── test/                testes pytest com dado inventado
├── data/raw/            os arquivos baixados (não versionados)
└── pyproject.toml
```

---

## Decisões de dado e o papel da IA

As decisões de transformação (o que é descartado, como cada código é
decodificado, por que o valor é `DECIMAL` e o CEP/município é texto) estão nos
comentários de `transformacao.py` e no topo de cada `.sql`. A IA foi usada para
escrever o encanamento a partir das specs; o erro típico dela em SQL não estoura
(acerta a sintaxe, erra o grão), então cada mart declara o grão e foi conferido
contando linhas antes e depois.

## Fonte

Microdados do **SIH/SUS**, DATASUS/Ministério da Saúde (dados públicos). CID-10
e municípios: DATASUS e IBGE. Uso não comercial, para fins de estudo.
