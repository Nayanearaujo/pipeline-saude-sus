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
| **4 · Dashboard + testes** | painel interativo por estado e 29 testes (cobertura acima do mínimo de 70%) | `app.py`, `painel.py`, `test/` |

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

Os microdados do SIH vêm em `.dbc` (formato legado do DATASUS). Dois scripts
geram tudo em `data/raw/` (precisam de internet; a pasta não vai para o Git):

```bash
uv sync
uv run python baixar_dados.py        # baixa os .dbc do DATASUS direto (HTTPS,
                                      # converte com pyreaddbc) -> internacoes.parquet
uv run python gerar_dicionarios.py   # baixa IBGE + CID-10 -> cid10.csv, municipios.csv
```

- **`internacoes.parquet`** — microdados do SIH-RD, uma linha por AIH.
  `baixar_dados.py` baixa os `.dbc` por UF e converte com `pyreaddbc` + `dbfread`
  (não usa o PySUS).
- **`cid10.csv`** — `codigo,descricao` (CID-10 → nome da doença). Fonte: DATASUS.
- **`municipios.csv`** — `codigo,municipio,uf` (código IBGE → município, UF).
  Fonte: IBGE.

> `gerar_dicionarios.py` baixa as tabelas oficiais. Sem internet ele cai num
> **modo neutro** (nome = `CID <codigo>` / `Municipio <codigo>`), que mantém o
> pipeline rodando mas deixa os rótulos sem o nome real. Rode-o com internet
> antes de publicar, ou os gráficos mostram o código cru no lugar da doença.

> Se abril/2026 ainda não estiver publicado (o SIH tem 2 a 4 meses de atraso),
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

As 1.238.763 internações se distribuem pelas 27 UFs: **SP** lidera com 249.901,
seguido de **MG** (135.571), **PR** (85.452), **BA** (84.016) e **RJ** (78.571).
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
├── baixar_dados.py      baixa os .dbc do SIH (DATASUS) para data/raw/
├── gerar_dicionarios.py gera cid10.csv e municipios.csv em data/raw/
├── dados_painel/        camada ouro exportada em CSV (lida pelo app na nuvem)
├── exportar_painel.py   exporta a camada ouro para dados_painel/
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

## Limitações e notas de dado

Escolhas e limites conhecidos deste recorte, declarados para leitura honesta dos
indicadores:

- **Série diária não soma o total.** Os marts `internacoes_diarias*` filtram a
  **data de internação** dentro de abril/2026. Como o arquivo é por competência
  (mês de processamento), parte das AIH pagas em abril teve entrada em meses
  anteriores: a série soma ~703 mil internações, não as 1,24 M dos cartões. O
  filtro é proposital (datas antigas esticariam o eixo), mas a diferença é
  grande; o gráfico mostra "entradas de abril", não o faturamento do mês.
- **UF é a de residência do paciente** (`MUNIC_RES`), não a do hospital. "Gasto
  por estado" aqui é por onde o paciente mora. O arquivo também traz a UF de
  internação (`UF_ARQUIVO`); trocar a referência muda o resultado.
- **Valor = valor pago pelo SUS** (`VAL_TOT`), não o custo real do hospital. O
  rótulo "custo médio" significa o valor médio pago por AIH.
- **Idade em anos.** A faixa etária usa `IDADE`; o SIH traz `COD_IDADE` (unidade:
  dias, meses, anos) que este recorte não desdobra. Recém-nascidos contados em
  dias/meses podem cair fora da faixa "< 1 ano".
- **Um único mês (abril/2026).** Não há base para falar de sazonalidade ou
  tendência; a série mostra só a variação dentro do mês.

## Fonte

Microdados do **SIH/SUS**, DATASUS/Ministério da Saúde (dados públicos). CID-10
e municípios: DATASUS e IBGE. Uso não comercial, para fins de estudo.
