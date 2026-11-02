# Revisão técnica da entrega

Base da revisão: `1f221d4d0d8be448b9670d5741c70e290a0052ec`.

## Resultados atuais

- 138 testes aprovados; Ruff aprovado; cobertura de 97,01%, incluindo os scripts auxiliares.
- Dez marts e 16.400 linhas nos CSVs publicados.
- KPI e soma das UFs: 1.238.234 internações e R$ 2.258.865.118,36.
- Dicionário: categorias e subcategorias do espelho CID-10. Foram completadas 1.048 descrições nacionais, de 1.055 ausentes. Restam sete códigos, com 76 internações (aproximadamente 0,0061%).
- As descrições dos 20 primeiros diagnósticos nacionais e de mortalidade estão preenchidas.
- A atualização dos CSVs alterou apenas o campo `doenca`; todos os demais campos foram comparados antes e depois e preservados.
- A deduplicação agora prioriza valor preenchido. O caso sintético com duplicata recente sem valor preserva uma AIH válida; antes perdia essa AIH.
- O código contém 37 regras, incluindo limite ponderado de 0,1% de descrições ausentes e nomes obrigatórios nos dois grupos de 20 diagnósticos.

## Evidência histórica preservada

A execução local anterior registrou 1.238.763 linhas brutas, 1.238.234 na Prata,
529 AIHs duplicadas e zero exclusões por ausência de valor. Passou nas 34 regras
então existentes. Os arquivos de auditoria JSON anteriores registram essa etapa.
Não representam uma nova execução da versão corrigida.

O manifesto `docs/proveniencia-extracao.json` mantém a competência, os hashes
originais dos microdados e os hashes anteriores e atuais dos CSVs com descrições atualizadas.
A origem do dicionário foi fixada no commit `b6eb7d0fe8be752307741d156d67eacf539a186c`
do repositório `cleytonferrari/CidDataSus`, um espelho público, não a API oficial.

## Validação local da versão corrigida

A saída recebida da execução do commit `2eab12c` confirma as quatro etapas e
as 37 regras aprovadas: Bronze com 1.238.763 internações, Prata com 1.238.234,
529 AIHs duplicadas excluídas e zero exclusões por ausência de valor. O dicionário
possui 14.233 códigos únicos; os dez marts continuam com 16.400 linhas.

As colunas `ANO_CMPT` e `MES_CMPT` registram 2026/04 para todas as 1.238.763
linhas da Bronze. O histograma de datas de entrada da Prata contém 216 meses
e soma exatamente 1.238.234 internações:

| Entrada | Internações |
|---|---:|
| Abril/2026 | 703.067 |
| Março/2026 | 343.386 |
| Fevereiro/2026 | 100.989 |
| Janeiro/2026 | 76.254 |
| Antes de 2026 | 14.538 |

As quatro últimas linhas somam 535.167, a diferença entre consolidado e série.
Há datas registradas desde 2008; a contagem não demonstra a causa nem autoriza
interpretá-las como duração comprovada de internação ou erro de origem.

A evidência em `docs/validacao-local-corrigida.json` foi transcrita da saída
recebida, não de acesso remoto ao banco. O total financeiro foi impresso em
notação científica, portanto esta saída não verifica os centavos. Os CSVs
publicados continuam reconciliados separadamente em R$ 2.258.865.118,36.
Não houve confirmação de novo download de microdados.

O recorte mensal permanece igual. O uso de `mode(data_internacao)` continua
como limitação de generalização; substituir a heurística exige uma alteração
própria e revisão dos testes para competências múltiplas ou ausentes.

## Publicação e apresentação

A versão anterior já estava incorporada à main, com CI e publicação aprovados.
O Streamlit e seu visual permanecem preservados nesta revisão. O HTML foi
regenerado com os nomes CID preenchidos e mantém o mapa SVG completo e centralizado.
O workflow de keep-alive permanece como estava; nenhuma automação foi removida.
