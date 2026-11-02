# Definições dos indicadores

## Planejamento

Foram avaliadas dez perguntas de negócio. Nove são viáveis com a base pública
usada e foram implementadas em dez marts. A reinternação por pessoa ficou fora
do escopo por falta de identificador pessoal adequado ao acompanhamento.

| Pergunta | Origem na Bronze | Implementação na Ouro |
|---|---|---|
| Quantas AIHs há no recorte? | `N_AIH` | `kpis_gerais`, `por_estado` |
| Qual é o valor total registrado? | `VAL_TOT` | `kpis_gerais`, `por_estado` |
| Qual é o valor médio e a mediana por AIH? | `VAL_TOT`, `MUNIC_RES` | `kpis_gerais`, `por_estado` |
| Qual é a permanência média? | `DIAS_PERM` | `kpis_gerais`, `por_estado` |
| Qual é a proporção de internações com óbito? | `MORTE`, `DIAG_PRINC` | KPIs, estados e `mortalidade_por_cid` |
| Quais diagnósticos são mais frequentes? | `DIAG_PRINC`, dicionário CID | `top_diagnosticos`, `top_diagnosticos_brasil` |
| Como se distribuem idade e sexo? | `IDADE`, `COD_IDADE`, `SEXO` | `perfil_demografico`, `perfil_demografico_brasil` |
| Como se distribuem as entradas no mês? | `DT_INTER` | `internacoes_diarias`, `internacoes_diarias_brasil` |
| Como se concentra o valor por município de residência? | `MUNIC_RES`, `VAL_TOT`, municípios | `municipios_pareto` |
| Qual é a reinternação em 30 dias por pessoa? | Identificador pessoal indisponível | Não implementada |

## Classificação das perguntas

- **Diretas após tipagem:** volume, valor total, média, mediana e permanência.
- **Exigem cuidado:** mortalidade, descrições CID, idade, série diária e municípios.
- **Não sustentada pela base:** reinternação por pessoa.

## Grão e deduplicação

Uma linha de `prata.internacoes` representa uma AIH com valor financeiro preenchido.
A seleção prioriza valor preenchido, alta mais recente e maior valor numérico.
Campos adicionais estabilizam os empates. Após a seleção, linhas sem valor são
excluídas. Valores não numéricos interrompem a conversão estrita.
A contagem de exclusões e a reconciliação usam a mesma prioridade financeira.

`VAL_TOT` é convertido para `DECIMAL(12,2)`. Datas usam o formato de origem
`AAAAMMDD`. Os dicionários mantêm uma linha por chave para evitar multiplicação
no `JOIN`.

## Idade e sexo

A idade em anos considera `IDADE` e `COD_IDADE`. Dias e meses são apresentados
na faixa de menos de um ano. O código 4 usa anos e o código 5 soma 100 ao valor.
Unidades ignoradas ou não reconhecidas ficam nulas. Não são classificadas como
bebês. Os marts preservam idade ou sexo ausentes na categoria técnica `nao informado`.

O sexo registrado usa 1 para masculino e 3 para feminino. Outros códigos
permanecem nulos. As contagens representam internações, não pessoas únicas.

## Mortalidade hospitalar

A taxa é `100.0 * COUNT(*) FILTER (WHERE morte) / COUNT(*)`.
O indicador `morte` corresponde a `MORTE = '1'`.
O mart por diagnóstico inclui apenas grupos com pelo menos 100 AIHs.
A taxa não é ajustada por gravidade e não mede mortalidade populacional.

## Diagnósticos

Os códigos são ligados ao dicionário completo de categorias e subcategorias.
O código é preservado sem ponto. Sem correspondência exata, a expressão SQL
`COALESCE(c.doenca, 'nao classificado')` mantém a internação no resultado.

A qualidade tolera até 0,1% das internações sem descrição e exige nomes nos
20 primeiros diagnósticos nacionais e de mortalidade. A versão publicada
completou os sete códigos restantes, associados a 76 internações, com fontes
oficiais complementares registradas em `docs/cid-complementar.csv`.

## Série diária e competência

A competência registra processamento. A data de entrada é outra variável.
Neste conjunto, todas as 1.238.763 linhas da Bronze têm competência abril de 2026.
A série de entradas de abril soma 703.067 AIHs. As 535.167 restantes têm datas
anteriores e permanecem nos indicadores consolidados.

Os marts 05 e 07 selecionam as entradas no mês da coluna `competencia`,
preservada de `ANO_CMPT` e `MES_CMPT`. O pipeline rejeita competências misturadas
antes da deduplicação e da construção dos marts. A generalização para vários meses
exige execuções separadas. A série não inclui entradas anteriores, mas elas
continuam nos indicadores consolidados da competência.

## Municípios, geografia e concentração

O código municipal do SIH usa os seis primeiros dígitos do código do IBGE.
A UF deriva de `MUNIC_RES`, a residência registrada. A UF do arquivo de origem
não deve ser confundida automaticamente com essa referência geográfica.

O mart municipal contém a curva completa, ordenada do maior para o menor valor.
O percentual acumulado vem do SQL. A linha de 80% é uma referência de
concentração, não uma meta de qualidade nem uma comprovação da regra 80/20.
Média, mediana, taxas, participações e posições são calculadas nos marts.
