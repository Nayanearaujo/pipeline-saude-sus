# Auditoria final · pipeline-saude-sus

Data: 01/11/2026. Base revisada: `8659318041ea985a8f997dd9e1dd2309f225bb4c`.
Este documento acompanha uma proposta de conclusão; não autoriza seu merge.

## Resultado

O código passou em 108 testes, com cobertura de 97,31% no escopo configurado
em `pyproject.toml` e Ruff aprovado. Os oito CSVs já publicados são internamente
coerentes nas 14 verificações registradas em
[docs/auditoria-publicacao.json](docs/auditoria-publicacao.json).

A entrega **ainda não equivale a uma revalidação completa da fonte DATASUS**.
Não estão disponíveis neste ambiente `sih.duckdb` nem o Parquet bruto. Não foram
baixados microdados nesta auditoria, alterados os oito CSVs existentes ou
fabricados os dois CSVs complementares ausentes.

## Evidências dos dados publicados

| Verificação | Resultado |
|---|---|
| KPI, 27 UFs e diagnósticos nacionais: quantidade | 1.238.234 AIHs em cada caminho |
| KPI, UFs e diagnósticos nacionais: valor total | R$ 2.258.889.119,23 em cada caminho, comparado com Decimal |
| Perfil nacional e por UF | 1.238.234 AIHs; grupos de faixa etária/sexo conferem |
| Série nacional e por UF | 703.067 entradas; contagens e valores conferem por dia |
| Valor total da série | R$ 964.527.475,26 nos dois caminhos |
| Período da série publicada | 01/04/2026 a 30/04/2026 |
| Custo médio nacional | R$ 1.824,28, compatível com valor total / AIHs |
| Chaves auditadas | Sem duplicação em UF, CID nacional, perfil por UF e série por UF |
| Perfil menor de um ano | 60.839 AIHs no CSV nacional |
| Marts complementares | SQL e testes existentes; CSVs reais ausentes |

Os hashes SHA-256 e as quantidades de linhas dos oito arquivos constam da
evidência JSON. A concordância entre agregados não comprova a proveniência,
a integridade dos microdados, os óbitos individuais ou as exclusões históricas.
Os 1.238.763 registros brutos e as 529 exclusões citados na documentação são
registros históricos, não uma execução reproduzida nesta auditoria.

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

Os arquivos em `sql/marts/` e os oito CSVs publicados não foram alterados.
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

A proposta final também foi testada localmente com AppTest: Brasil, SP e AC,
cinco cartões, período vindo da série e aviso de CSVs complementares ausentes.
Isso verifica a execução Python da interface; não substitui uma inspeção visual
do deploy depois que esta proposta for aprovada e publicada.

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

## Pendências antes do encerramento integral

1. Reexecutar o pipeline com os arquivos reais e verificar as 34 regras,
   incluindo as exclusões da Bronze e os resultados do desempate corrigido.
2. Exportar os CSVs reais `mortalidade_por_cid` e `municipios_pareto`.
3. Registrar competência/proveniência da extração e confirmar o recorte diário;
   o mês da série não substitui esse registro.
4. Após aprovação e merge final, conferir novamente o deploy e o relatório
   publicados. A revisão desta proposta e o merge final permanecem com o usuário.
