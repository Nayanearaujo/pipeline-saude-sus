# Entrega do Desafio Final · Pipeline de Internações do SUS

**Autora:** Nayane Araujo
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
| Três camadas (bronze, prata, ouro) | `ingestao.py` (bronze), `transformacao.py` (prata), `marts.py` + 8 SQL (ouro) |
| Pelo menos 2 tabelas com JOIN | `internacoes` × `cid10` (nome da doença) e × `ufs` (sigla e região) |
| Testes com cobertura mínima de 70% | 44 testes, cobertura de 95% |
| Repositório com todo o código e README | Sim, com README de instalação e execução |
| Histórico de commits passo a passo | Commits pequenos e temáticos, em português (Conventional Commits) |
| Dashboard (opcional) | Streamlit interativo por estado, com deploy no Streamlit Cloud |

## Além do pedido

- **Qualidade de dados que trava o build** (`pipeline/qualidade.py`): 17 regras
  que falham o pipeline se um número não fechar (as partes somam o todo, o grão é
  real, valores dentro do domínio).
- **CI no GitHub Actions**: roda testes e lint (ruff) a cada push.
- **Relatório HTML estático** publicado no GitHub Pages, por ano.
- **Comando único** (`executar.py`) roda tudo: bronze, prata, ouro e qualidade.

## Achados (o que o dado revelou ao ser conferido contra a fonte)

1. **Metade das internações "de abril" entrou em outro mês.** O arquivo é por
   competência (mês de pagamento), não por data de entrada. Por isso a série
   diária não soma o KPI de internações: são perguntas diferentes, e o painel
   deixa isso explícito.
2. **Um em cada vinte bebês estava na faixa etária errada.** A idade no SIH vem
   com uma unidade (`COD_IDADE`: dias, meses, anos) que, ignorada, jogava recém
   nascidos para faixas de adulto. Corrigido, a faixa "< 1 ano" foi de 1,4% para
   4,9%.
3. **Os nomes das doenças sumiam em silêncio** quando o dicionário era gerado sem
   internet. O JOIN funcionava, mas juntava com rótulo vazio. Com a fonte oficial,
   o Top 10 mostra "Parto espontâneo cefálico", não "CID O800".
4. **O grão foi protegido contra colapso silencioso**: dedup por AIH, travada por
   regra de qualidade.

## Papel da IA

A IA escreveu o encanamento a partir de especificações; o trabalho foi conferir.
Os três primeiros achados acima são erros que não lançam exceção, só aparecem
como número errado, e por isso a conferência foi codificada em `qualidade.py`.
