# Validação da entrega

## Escopo

A validação reúne os dez CSVs publicados, o código do repositório e os resultados
de duas execuções locais do commit `4510595`. Os arquivos brutos e o banco
não são versionados. As execuções reutilizaram os arquivos locais, sem novo
download de microdados.

## Resultados da execução local

| Item | Resultado |
|---|---:|
| Internações na Bronze | 1.238.763 |
| AIHs na Prata | 1.238.234 |
| Duplicatas excluídas | 529 |
| Exclusões por ausência de valor | 0 |
| Códigos únicos no dicionário CID | 14.240 |
| Códigos únicos de municípios | 5.571 |
| Marts | 10 |
| Linhas nos marts | 16.400 |
| Regras de qualidade aprovadas | 37 |

Todas as linhas da Bronze têm `ANO_CMPT = 2026` e `MES_CMPT = 04`.
O histograma da Prata contém 216 meses e soma as 1.238.234 AIHs.

| Mês de entrada | Internações |
|---|---:|
| Abril de 2026 | 703.067 |
| Março de 2026 | 343.386 |
| Fevereiro de 2026 | 100.989 |
| Janeiro de 2026 | 76.254 |
| Antes de 2026 | 14.538 |

As quatro últimas linhas somam 535.167. A diferença para a série de abril é
explicada pelas datas registradas, não por exclusão desses registros da Prata.
A exatidão das datas originais não foi comprovada. As 617 entradas de 01/01/2008
foram identificadas como AIHs tipo 5, de continuidade.

A conferência final imprimiu o valor exato de R$ 2.258.865.118,36.
Os dez marts coincidiram com os CSVs publicados em todos os campos comparados,
sem linhas exclusivas em nenhum dos lados. Os hashes dos dez CSVs também passaram.

## Descrições de diagnósticos

A inclusão das categorias do CID completou 1.048 descrições nacionais.
As internações sem nome passaram de 36.736 para 76, em sete códigos ausentes
no espelho versionado. Esses sete foram depois completados com fontes oficiais
registradas em `docs/cid-complementar.csv`, deixando zero ausências nos CSVs. A atualização dos CSVs alterou apenas `doenca`.
Códigos, posições, contagens, valores e demais campos foram preservados.
As três regras de descrição passaram nos CSVs e na execução local registrada.

## Testes e verificações

- 156 testes automatizados aprovados, com cobertura de 97,06%.
- Ruff aprovado e cobertura mínima de 95% preservada.
- Download, dicionários e orquestração incluídos na cobertura.
- Duplicata recente sem valor não elimina a linha válida da mesma AIH.
- Unidade de idade ignorada ou não reconhecida passa a ser preservada como nula.
  Os marts demográficos já incluem a categoria técnica `nao informado`.
- Código, credenciais e microdados são verificados separadamente na conferência local.

A correção final de idade foi executada sobre o Parquet local e não alterou
os dez marts, inclusive os perfis. As unidades na Bronze são 2 (35.843 linhas),
3 (24.997), 4 (1.177.041) e 5 (882). A soma é 1.238.763. Não há unidade ignorada
ou desconhecida neste conjunto, e a Prata permaneceu sem idade nula.

A consulta de datas anteriores a fevereiro de 2008 encontrou uma única data,
2008-01-01, com 617 registros. A consulta posterior confirmou `IDENT = 5` em todas essas linhas.
O relatório foi gerado com nove figuras e mapa SVG. Os arquivos originais foram preservados.

Referência para a unidade ignorada: [Ministério da Saúde, Orientações básicas
para utilização de sistemas informatizados em auditoria no SUS](https://bvsms.saude.gov.br/bvs/publicacoes/auditoria_sus.pdf).
O dicionário identifica `COD_IDADE = 0` como idade ignorada.

## Apresentação e publicação

O relatório mantém nove figuras e o mapa SVG completo, com dimensões compactas.
A curva municipal usa SVG para funcionar sem WebGL. A tabela expansível do
perfil oferece filtros de sexo e faixa etária. Dois testes de regressão verificam
a renderização da curva completa e o escape dos textos da tabela. A execução
local anterior permaneceu registrada com seus 145 testes e cobertura de 97,01%.
O Streamlit mantém os filtros de estado e métrica, o detalhamento do perfil e as
análises nacionais de mortalidade por CID e concentração municipal.
A conferência visual do painel e do relatório inclui os nove gráficos, os
seletores, o perfil expansível e a curva municipal. O funcionamento público
deve ser conferido novamente após alterações na publicação.

## Limites preservados

O recorte mensal agora usa a competência explícita, sem `mode()`.
A Bronze deve conter uma única competência por execução, inclusive antes da
deduplicação. Os testes incluem um conjunto com mais entradas em outro mês.
O resultado segue o mês de processamento, independentemente dessa frequência.
A execução com os microdados locais foi confirmada no commit `4510595`.
As duas execuções aprovaram 156 testes, cobertura de 97,06%, as 37 regras e a
comparação integral dos dez marts. A Prata preservou a competência `2026-04-01`
nas 1.238.234 linhas. A auditoria encontrou zero grupos de CID sem descrição,
6.336 grupos de datas e permanências para investigação e 216 grupos mensais.
O número de grupos não informa, sozinho, quantas internações estão envolvidas.

A auditoria de datas produz arquivos agregados locais, sem alterar a Prata.
A regra de dez anos é uma triagem para investigação, sem diagnóstico de causa.
As 617 entradas de 01/01/2008 foram identificadas como AIHs tipo 5, com
permanência coerente com o período cobrado na competência. Isso não comprova
a exatidão da data original nem classifica os outros alertas da auditoria.

AIHs não representam pessoas únicas. Valores registrados não medem o custo
integral da assistência. A mortalidade hospitalar não é uma taxa populacional
nem uma comparação ajustada por gravidade. A geografia é a residência registrada.

## Arquivos de evidência

- [Manifesto de extração e hashes dos CSVs](docs/proveniencia-extracao.json)
- [Resultado atual da execução local](docs/validacao-competencia-local.json)
- [Registro histórico da execução de 24e781e](docs/validacao-local-corrigida.json)
- [Procedimento de conferência final](CONFERENCIA_LOCAL.md)

Os resultados históricos permanecem associados aos respectivos commits.
O registro de `4510595` contém a validação da competência explícita e dos
diagnósticos completados com fontes oficiais.

## Confirmação das AIHs de continuidade

A consulta agregada na Bronze confirmou que as 617 linhas com entrada em
01/01/2008 têm `IDENT = 5`, de continuidade. Há uma linha com saída em 20/04/2026
e 20 dias registrados, uma com saída em 26/04/2026 e 26 dias, e 615 com saída
em 30/04/2026 e 30 dias. O padrão corresponde à regra documentada para AIH tipo 5:
a data original de entrada é mantida e a permanência pode refletir o período
cobrado na competência. Isso explica a diferença para o intervalo de calendário,
mas não comprova a exatidão da data original nem explica os demais alertas.

Fontes: [SIH, AIH de continuidade](https://wiki.saude.gov.br/sih/index.php/P%C3%A1gina_principal)
e [SES-SP, dias de permanência por tipo de AIH](https://www.saude.sp.gov.br/resources/ses/perfil/gestor/informacoes-de-saude/tabnet/comunicado_1_tabnet.pdf).
