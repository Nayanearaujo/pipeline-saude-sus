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
| Testes com cobertura mínima de 70% | 138 testes, cobertura de 97,01% |
| Repositório com todo o código e README | Sim, com README de instalação e execução |
| Histórico de commits passo a passo | Commits pequenos e temáticos, em português (Conventional Commits) |
| Dashboard (opcional) | Streamlit interativo por estado, com deploy no Streamlit Cloud |

## Além do pedido

- **Qualidade de dados que trava o build** (`pipeline/qualidade.py`): 37 regras
  que falham o pipeline se um número não fechar (as partes somam o todo, o grão é
  real, valores dentro do domínio, consistência por UF x nacional).
- **CI e Keep-Alive no GitHub Actions**: roda testes e lint (ruff) a cada push e mantém o app do Streamlit Cloud acordado via Chromium headless.
- **Relatório HTML estático** publicado no GitHub Pages.
- **Comando único** (`executar.py`) roda tudo: bronze, prata, ouro e qualidade.
- **CAST estrito** na transformação, **API oficial do IBGE** com fallback e **DuckDB UI** (`ui.py`).

## Evidências e limites da entrega

A auditoria de 01/11/2026 está em [AUDITORIA_FINAL.md](AUDITORIA_FINAL.md).
## Validação da entrega

Os dez CSVs reconciliam 1.238.234 internações e R$ 2.258.865.118,36.
A revisão das descrições CID preservou todos os campos numéricos e reduziu
os registros sem nome de 36.736 para 76. A fonte não contém os sete códigos restantes.

São 138 testes aprovados e cobertura de 97,01%, incluindo scripts auxiliares.
O CI exige 95%. Há 37 regras de qualidade; a execução real anterior passou
nas 34 regras existentes naquela versão. As três regras novas e a deduplicação
corrigida aguardam reprocessamento com os microdados locais.

O Streamlit mantém o visual aprovado; o mapa do HTML usa SVG centralizado.
A série mensal continua com o recorte publicado. Sua substituição exige conferir
as colunas de competência e as datas de entrada no Parquet, sem simular resultados.

---

## Autora

**Nayane Araújo** Pós-Graduanda em Engenharia de Dados

[![GitHub Nayanearaujo](https://img.shields.io/badge/GitHub-Nayanearaujo-181717?style=flat&logo=github)](https://github.com/Nayanearaujo)
[![LinkedIn Conectar](https://img.shields.io/badge/LinkedIn-Conectar-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/nayane-araujo-548063195/)
