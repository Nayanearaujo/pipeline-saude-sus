# Validação da entrega

## Escopo

A revisão usa os dez CSVs publicados, o código do repositório e a saída agregada
da execução local do commit `2eab12c`. Os arquivos brutos e o banco permanecem
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
A origem das datas antigas não foi comprovada. Janeiro de 2008 contém 617 entradas.

A saída financeira recebida foi abreviada em notação científica. Ela não permite
verificar centavos. Separadamente, os CSVs publicados reconciliam o valor exato
de R$ 2.258.865.118,36 entre KPIs e estados.

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

A correção final de idade ainda precisa ser executada sobre o Parquet local.
Os CSVs publicados não foram alterados com base em uma suposição. A conferência
compara os dez marts e sinaliza qualquer diferença, inclusive nos perfis.

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
