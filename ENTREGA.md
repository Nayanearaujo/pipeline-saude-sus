# Entrega do Desafio Final · Pipeline de Internações do SUS

**Autora:** Nayane Araújo
**Dataset:** Internações hospitalares do SUS (SIH/SUS, DATASUS), abril de 2026, Brasil inteiro, 1.238.763 registros brutos.

## Links

- Repositório: https://github.com/Nayanearaujo/pipeline-saude-sus
- Dashboard ao vivo (Streamlit): https://pipeline-saude-sus.streamlit.app/
- Relatório executivo (GitHub Pages): https://nayanearaujo.github.io/pipeline-saude-sus/relatorio.html
- Guia do projeto (GitHub Pages): https://nayanearaujo.github.io/pipeline-saude-sus/

## O que é

Um pipeline de dados de ponta a ponta sobre as internações do SUS, partindo dos
arquivos `.dbc` do DATASUS e chegando a um dashboard interativo por estado e a um
relatório estático. O mesmo caminho das aulas (Olist), com um dataset novo: dado
de saúde brasileiro, cru e sem documentação amigável.

## Como cumpre cada requisito da aula 4

| Requisito | Como foi atendido |
|---|---|
| Dataset diferente do das aulas | SIH/SUS (DATASUS), 1,2 milhão de internações |
| Três camadas (bronze, prata, ouro) | `ingestao.py` (bronze), `transformacao.py` (prata), `marts.py` + 10 SQL (ouro) |
| Pelo menos 2 tabelas com JOIN | `internacoes` × `cid10` (nome da doença), × `ufs` (sigla e região) e × `municipios` (nome da cidade) |
| Testes com cobertura mínima de 70% | 120 testes, cobertura de 97,54% |
| Repositório com todo o código e README | Sim, com README de instalação e execução |
| Histórico de commits passo a passo | Commits pequenos e temáticos, em português (Conventional Commits) |
| Dashboard (opcional) | Streamlit interativo por estado, com deploy no Streamlit Cloud |

## Além do pedido

- **Qualidade de dados que trava o build** (`pipeline/qualidade.py`): 34 regras
  que falham o pipeline se um número não fechar (as partes somam o todo, o grão é
  real, valores dentro do domínio, consistência por UF x nacional).
- **CI e Keep-Alive no GitHub Actions**: roda testes e lint (ruff) a cada push e mantém o app do Streamlit Cloud acordado via Chromium headless.
- **Relatório HTML estático** publicado no GitHub Pages.
- **Comando único** (`executar.py`) roda tudo: bronze, prata, ouro e qualidade.
- **CAST estrito** na transformação, **API oficial do IBGE** com fallback e **DuckDB UI** (`ui.py`).

## Evidências e limites da entrega

A auditoria de 01/11/2026 está em [AUDITORIA_FINAL.md](AUDITORIA_FINAL.md).
Os CSVs recebidos no PR final reconciliam 1.238.234 AIHs e R$ 2.258.865.118,36 entre
estados, diagnósticos nacionais e KPI; os perfis e a série diária também
conferem por grupo. A série de abril soma 703.067 entradas, um recorte distinto.

A saída de terminal fornecida pelo usuário confirmou o reprocessamento local
do PR final: 1.238.763 linhas brutas, 1.238.234 na Prata, 529 AIHs duplicadas
excluídas e 0 sem valor. As 34 regras passaram e os dez marts foram exportados,
incluindo os dois complementares. Os dez CSVs e o HTML foram recebidos no PR;
os hashes dos CSVs foram conferidos e a competência 2026/04 consta no manifesto.
A recomputação nos dois bancos confirmou R$ 2.258.865.118,36. Não houve
transferência de microdados nem novo download DATASUS confirmado pelo agente.

A correção final trata o valor numericamente no desempate de AIHs e estabiliza
empates completos. A comparação das regras antiga e nova não mostrou efeito financeiro nesses
dados. A Prata antiga e o CSV antigo não correspondem à recomputação atual;
a auditoria registra os três totais e a limitação de proveniência histórica.
O mês exibido na série vem dos dados, sem ser apresentado como prova da
competência de processamento. Os SQLs dos dez marts foram preservados.

---

## Autora

**Nayane Araújo** Pós-Graduanda em Engenharia de Dados

[![GitHub Nayanearaujo](https://img.shields.io/badge/GitHub-Nayanearaujo-181717?style=flat&logo=github)](https://github.com/Nayanearaujo)
[![LinkedIn Conectar](https://img.shields.io/badge/LinkedIn-Conectar-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/nayane-araujo-548063195/)
