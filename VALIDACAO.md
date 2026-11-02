# Validação da entrega

## Escopo

A revisão usa os dez CSVs publicados, o código do repositório e a saída agregada
da conferência local final do commit `24e781e`. Os arquivos brutos e o banco permanecem
fora do GitHub. Não houve confirmação de novo download de microdados.

## Evidência local recebida

| Item | Resultado |
|---|---:|
| Internações na Bronze | 1.238.763 |
| AIHs na Prata | 1.238.234 |
| Duplicatas excluídas | 529 |
| Exclusões por ausência de valor | 0 |
| Códigos únicos no dicionário CID | 14.233 |
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
A origem das datas antigas não foi comprovada. A data 2008-01-01 contém 617 entradas.

A conferência final imprimiu o valor exato de R$ 2.258.865.118,36.
Os dez marts coincidiram com os CSVs publicados em todos os campos comparados,
sem linhas exclusivas em nenhum dos lados. Os hashes dos dez CSVs também passaram.

## Descrições de diagnósticos

A inclusão das categorias do CID completou 1.048 descrições nacionais.
As internações sem nome passaram de 36.736 para 76, em sete códigos ausentes
na fonte versionada. A atualização dos CSVs alterou apenas `doenca`.
Códigos, posições, contagens, valores e demais campos foram preservados.
As três regras de descrição passaram nos CSVs e na execução local registrada.

## Revisão final do código

- 145 testes automatizados aprovados, com cobertura de 97,01%.
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
2008-01-01, com 617 registros. Isso confirma a concentração, mas não sua causa.
O relatório foi gerado com nove figuras e mapa SVG. Os arquivos originais foram preservados.

Referência para a unidade ignorada: [Ministério da Saúde, Orientações básicas
para utilização de sistemas informatizados em auditoria no SUS](https://bvsms.saude.gov.br/bvs/publicacoes/auditoria_sus.pdf).
O dicionário identifica `COD_IDADE = 0` como idade ignorada.

## Apresentação e publicação

O relatório mantém nove figuras e o mapa SVG completo, com dimensões compactas.
O Streamlit mantém os filtros de estado e métrica, o detalhamento do perfil e as
análises nacionais de mortalidade por CID e concentração municipal.
O código atual contém esses recursos, mas a instância pública observada ainda
apresentou uma interface anterior. A verificação após o reinício do aplicativo
é necessária antes de considerar o deploy confirmado.

## Limites preservados

O recorte mensal continua usando o mês da data de entrada mais frequente,
por meio de `mode()`. Ele coincide com abril de 2026 neste conjunto.
A generalização para outras competências exige uma alteração específica.

AIHs não representam pessoas únicas. Valores registrados não medem o custo
integral da assistência. A mortalidade hospitalar não é uma taxa populacional
nem uma comparação ajustada por gravidade. A geografia é a residência registrada.

## Arquivos de evidência

- [Manifesto de extração e hashes dos CSVs](docs/proveniencia-extracao.json)
- [Evidência agregada da execução local](docs/validacao-local-corrigida.json)
- [Procedimento de conferência final](CONFERENCIA_LOCAL.md)

As auditorias intermediárias e as capturas antigas foram retiradas da entrega
para evitar números concorrentes. O histórico Git preserva as versões anteriores.
