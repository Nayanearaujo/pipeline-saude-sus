# Auditoria final · pipeline-saude-sus

Data: 01/11/2026. Base revisada: `8659318041ea985a8f997dd9e1dd2309f225bb4c`.
Este documento acompanha uma proposta de conclusão; não autoriza seu merge.

## Resultado

O código passou em 108 testes, com cobertura de 97,31% no escopo configurado
em `pyproject.toml` e Ruff aprovado. Os dez CSVs recebidos no PR são internamente
coerentes nas 27 verificações registradas em
[docs/auditoria-publicacao-atual.json](docs/auditoria-publicacao-atual.json).
Os dez hashes SHA-256 conferem com o manifesto
[docs/proveniencia-extracao.json](docs/proveniencia-extracao.json).
A auditoria dos oito CSVs anteriores foi preservada como registro histórico em
[docs/auditoria-publicacao.json](docs/auditoria-publicacao.json).

A execução real local foi confirmada pela saída de terminal fornecida pelo
usuário em 01/11/2026, sobre o commit `99d5eb9`: as quatro etapas terminaram,
as 34 regras passaram e os dez marts foram exportados. O banco e os arquivos
brutos permanecem no computador do usuário, sem transferência para o agente.
Isso não comprova um novo download da fonte DATASUS. A comparação posterior
identificou três totais financeiros distintos e confirmou a reprodução do
resultado novo nos dois bancos com a regra atual. Os dez CSVs e o HTML foram
recebidos no commit `2dfed29` e verificados diretamente pelo agente.
O merge final e a atualização do deploy de produção não foram realizados.

## Evidências dos agregados recebidos no PR final

| Verificação | Resultado |
|---|---|
| KPI, 27 UFs e diagnósticos nacionais: quantidade | 1.238.234 AIHs em cada caminho |
| KPI, UFs e diagnósticos nacionais: valor total | R$ 2.258.865.118,36 em cada caminho, comparado com Decimal |
| Perfil nacional e por UF | 1.238.234 AIHs; grupos de faixa etária/sexo conferem |
| Série nacional e por UF | 703.067 entradas; contagens e valores conferem por dia |
| Valor total da série | R$ 964.527.475,26 nos dois caminhos |
| Período da série publicada | 01/04/2026 a 30/04/2026 |
| Custo médio nacional | R$ 1.824,26, compatível com valor total / AIHs |
| Chaves auditadas | Sem duplicação em UF, CID nacional, perfil por UF e série por UF |
| Perfil menor de um ano | 60.839 AIHs no CSV nacional |
| Marts complementares | Recebidos: 1.429 linhas de mortalidade por CID e 5.569 de Pareto |

Os hashes SHA-256 e as quantidades de linhas dos dez arquivos constam da
nova evidência JSON. O Pareto soma a mesma quantidade e o mesmo valor do KPI,
tem posições sequenciais e acumulado válido terminando em 100%. Os CIDs de
mortalidade respeitam o mínimo de 100 AIHs, o domínio de óbitos/taxa e as
quantidades dos diagnósticos nacionais.
A concordância entre agregados não comprova a proveniência,
a integridade dos microdados, os óbitos individuais ou as exclusões históricas.
O reprocessamento local confirmou 1.238.763 linhas na Bronze e 1.238.234 na
Prata. As 529 exclusões foram classificadas como AIHs duplicadas; nenhuma
exclusão ocorreu por ausência de valor. Não foram mantidos nulos em sexo,
idade ou UF. O novo KPI informado soma R$ 2.258.865.118,36, com custo médio
de R$ 1.824,26. Os valores da publicação antiga foram preservados na seção
histórica e na evidência JSON anterior.

## Evidência de execução real local

Fonte: saída de terminal fornecida pelo usuário, não execução remota pelo agente.
Registro estruturado: [docs/evidencia-execucao-local.json](docs/evidencia-execucao-local.json).

- Commit executado: `99d5eb9`; macOS, Python 3.11.4.
- Bronze: 1.238.763 internações, 12.451 CIDs e 5.571 municípios.
- Prata: 1.238.234 internações; 0 sem valor e 529 AIHs duplicadas excluídas.
- Ouro: dez marts, com 16.400 linhas no conjunto.
- Mortalidade por CID: 1.429 linhas; Pareto municipal: 5.569 linhas.
- Qualidade: 34 regras aprovadas, incluindo reconciliações Bronze/Prata/KPI.
- Dez CSVs exportados e os dois HTMLs gerados, com 69,0 KB cada.

Os totais financeiros e as diferenças principais foram registrados abaixo.
O manifesto recebido registra competência `2026/04`, hashes dos três arquivos
brutos e dos dez CSVs, além do commit do processamento. O agente recalculou e
confirmou os hashes dos dez CSVs recebidos; os hashes dos brutos são evidências
informadas na origem, pois os microdados não foram transferidos.
A publicação em produção e o merge final não foram realizados.

### Reconciliação da diferença financeira

| Referência | Valor total |
|---|---:|
| CSV antigo do projeto original | R$ 2.258.889.119,23 |
| Prata e KPI gravados no banco original | R$ 2.258.865.695,19 |
| Prata e KPI gravados no banco da revisão | R$ 2.258.865.118,36 |
| Banco original recalculado com a regra atual, em memória | R$ 2.258.865.118,36 |
| Banco da revisão recalculado com a regra atual, em memória | R$ 2.258.865.118,36 |

A quantidade permanece em 1.238.234 AIHs em todas as recomputações. O CSV
antigo difere do novo em R$ 24.000,87; o banco original gravado difere do novo
em R$ 576,83. Nenhum registro financeiro exclusivo foi encontrado entre as
Bronzes comparadas nos campos N_AIH, DT_SAIDA e VAL_TOT normalizados. Isso não
é uma comparação integral de todas as colunas dos arquivos de origem.

A transformação antiga (commit `1322714`), aplicada à Bronze da revisão,
também produziu o mesmo total novo: a comparação por AIH informou zero
diferenças em valor, permanência e desfecho. Portanto, a mudança financeira
observada frente aos artefatos antigos **não foi reproduzida como efeito da
correção do PR nº 15 nesses dados**. A Prata antiga gravada não corresponde à
recomputação atual da própria Bronze; o CSV antigo também não corresponde ao
KPI gravado no banco original. Sem histórico de execução/proveniência,
não é possível afirmar qual versão, seleção ou extração gerou cada artefato.

Na comparação dos CSVs por chave foram informadas quatro linhas de perfil
por UF com permanência média diferente, 17 linhas de UFs com algum campo
diferente e 92 diagnósticos nacionais com valor diferente, sem chaves
adicionadas/removidas nessas tabelas. As séries diárias, o perfil nacional e
o top de diagnósticos por UF permaneceram idênticos byte a byte.

O resultado de referência proposto é o novo, reproduzível nas duas Bronzes
financeiramente comparadas e aprovado nas 34 regras. Não houve ajuste manual
para forçar igualdade aos totais antigos.

## Correções preparadas para revisão

1. **Período na interface e no relatório.** Removido o rótulo fixo abril/2026
   da interface executável. O mês é formatado a partir do mart diário e
   identificado como período da série; não é usado para inferir a competência.
   Testes incluem julho/2027, vários meses e série vazia. O HTML em
   `docs/relatorio.html` foi regenerado dos mesmos CSVs publicados.
2. **Desempate de AIHs.** `VAL_TOT` entra na Bronze como texto. A ordenação
   anterior colocava `900.00` antes de `1000.00` em ordem decrescente. Agora
   compara DECIMAL e usa os demais campos preservados para estabilizar empates
   de data e valor. Reconciliação e contagem de exclusões usam o valor numérico.
   Os testes cobrem valores de magnitudes distintas e inversão da ordem de
   entrada. **Essa correção pode mudar a linha escolhida no reprocessamento**;
   não foi aplicado um ajuste artificial aos CSVs históricos.
3. **Dependências do deploy.** As três dependências diretas de
   `requirements.txt` foram alinhadas às versões do `uv.lock`: Streamlit
   1.66.1, Plotly 7.1.0 e pandas 2.3.3. O ambiente de desenvolvimento usa o
   lockfile; o arquivo do deploy fixa as diretas, não todo o grafo transitivo.
4. **Documentação.** README, guia e entrega atualizados para o resultado
   observado: 108 testes, cobertura de 97,31%, 34 regras de qualidade e
   limitações verificáveis. Removidas afirmações de revalidação da fonte ou
   de comparação histórica que não puderam ser repetidas.

Os arquivos em `sql/marts/` não foram alterados. Os CSVs do PR foram
substituídos/adicionados pelos resultados exportados do reprocessamento local.
As diferenças foram comparadas e documentadas; os artefatos da `main`
permanecem intactos até o merge final.
O critério de desempate completo é uma convenção técnica para reprodutibilidade;
não identifica qual registro empatado é clinicamente mais correto.

## SQL e interpretação

Os dez marts mantêm agregações na camada Ouro, JOINs com dicionários
padronizados, dinheiro em DECIMAL e separação entre recortes nacionais e por UF.
Os denominadores de mortalidade são AIHs, não pessoas nem população residente.
O ranking de mortalidade por CID exige ao menos 100 AIHs; isso não é ajuste de
risco nem medida de significância estatística.

Os marts diários usam `date_trunc('month', mode(data_internacao))`. Isso seleciona
o mês da **data individual mais frequente**, não o mês com a maior soma de
entradas. Um exemplo sintético com 10 entradas em um dia de janeiro e 18 em
dois dias de fevereiro ainda seleciona janeiro. Também não comprova a
competência de processamento do arquivo. A regra foi preservada; uma evolução
deve introduzir metadados explícitos de competência e discutir esse recorte
antes de alterar SQL ou números publicados.

A publicação dos CSVs prepara todos os arquivos antes das substituições e tenta
restaurar os anteriores em caso de erro. Não oferece visibilidade simultaneamente
atômica para leitores de vários arquivos, nem recuperação garantida após queda
do processo ou falha também durante a restauração. Não é apresentada como uma
transação de filesystem completa.

## Segurança e dependências

- A consulta `pip-audit` sobre as 40 dependências de produção selecionadas do
  `uv.lock` não encontrou vulnerabilidades conhecidas em 01/11/2026. Resultado:
  [docs/auditoria-dependencias.json](docs/auditoria-dependencias.json).
- A consulta não cobre automaticamente variantes de plataforma/Python,
  dependências de desenvolvimento ou o Playwright do workflow, e não certifica
  ausência de vulnerabilidades ainda desconhecidas.
- A busca heurística por formatos de tokens e chaves privadas no código
  rastreado não encontrou credenciais. Isso não é uma varredura completa do
  histórico Git nem substitui rotação caso uma chave já tenha sido exposta.
- Não foram usadas credenciais de API. O IBGE é uma API pública; o CID-10 é
  consultado em espelho público, sem garantia de disponibilidade ou imutabilidade.
- `.gitignore` exclui banco, dados brutos, `.env`, chaves privadas e secrets do
  Streamlit. Workflows usam permissões de leitura de conteúdo.

## Interface e automação

O dashboard publicado foi observado com cinco cartões e os gráficos principais.
O keepalive corrigido no PR nº 14 passou no runner e registrou cinco cartões
renderizados. O CI nº 46 e a publicação Pages passaram após esse merge.

A proposta final foi testada com os dez CSVs recebidos usando AppTest: Brasil,
SP e AC, cinco cartões, nove gráficos e os dois marts complementares carregados,
sem aviso de exportação ausente. O HTML recebido confere com sua reconstrução
a partir dos CSVs, após normalizar apenas o horário do rodapé e a representação
das datas da série (DATE do banco versus string CSV, ambas no mesmo dia).
Isso verifica a execução Python e o conteúdo do relatório; não substitui a
inspeção visual do deploy após aprovação e publicação.

## Reprodução

```bash
uv sync --frozen
uv run ruff check .
uv run pytest --cov
# Com os CSVs publicados, sem gerar microdados:
uv run streamlit run app.py
uv run python relatorio.py
```

Para a fonte real, em ambiente com acesso ao DATASUS, configure `ANO`/`MES` e
mantenha `UFS = None` em `baixar_dados.py`. Depois execute:

```bash
uv run python baixar_dados.py
uv run python gerar_dicionarios.py
uv run python executar.py
uv run python exportar_painel.py
uv run python relatorio.py
```

Não contorne o bloqueio de completude para publicar uma amostra como Brasil.
`PERMITIR_PARCIAL=1` é exclusivo de uma execução conscientemente parcial.
Publique apenas os agregados após qualidade aprovada; não versione microdados,
banco ou credenciais. Registre a competência, a versão dos dicionários e os
hashes da extração ao reprocessar.

Para repetir a consulta de dependências:

```bash
uv export --frozen --no-dev --no-hashes --format requirements-txt --output-file /tmp/sus-requirements.txt
uvx pip-audit -r /tmp/sus-requirements.txt --no-deps --disable-pip --format json
```

## Situação para aprovação final

Concluídos: testes e lint, reprocessamento local com 34 regras aprovadas,
reconciliações financeiras, dez marts recebidos, hashes dos dez CSVs conferidos,
competência 2026/04 registrada, interface com complementares e relatório conferidos.
As evidências dos microdados foram fornecidas pelo usuário; não houve novo
download DATASUS nem auditoria independente desses arquivos pelo agente.

Aguardam a revisão/autorização do usuário para o merge final e, depois,
a conferência do CI da `main`, do GitHub Pages e do dashboard em produção.
Permanecem como limitações conhecidas: proveniência histórica incompleta dos
artefatos antigos, seleção heurística do mês da série nos SQLs preservados e
ausência de publicação simultaneamente atômica do conjunto de CSVs.
Nenhuma dessas limitações é apresentada como resolvida.
