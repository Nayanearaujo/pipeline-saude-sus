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

## Pendente de execução local

Os microdados e o banco não estão disponíveis nesta revisão remota.
É necessário gerar o dicionário completo e reexecutar a nova deduplicação,
os marts e as 37 regras antes de afirmar que os totais da nova execução real
permanecem iguais. Não houve novo download de microdados nem alteração de `data/raw/`.

A série diária permanece com 703.067 internações; a diferença para o consolidado
é de 535.167 (43,22%). O SQL usa o mês da data mais frequente, não o mês de maior
volume. A distribuição dessas entradas e as colunas `ANO_CMPT` e `MES_CMPT`
precisam ser conferidas no Parquet local antes de alterar o recorte.

## Publicação e apresentação

A versão anterior já estava incorporada à main, com CI e publicação aprovados.
O Streamlit e seu visual permanecem preservados nesta revisão. O HTML foi
regenerado com os nomes CID preenchidos e mantém o mapa SVG completo e centralizado.
O workflow de keep-alive permanece como estava; nenhuma automação foi removida.
