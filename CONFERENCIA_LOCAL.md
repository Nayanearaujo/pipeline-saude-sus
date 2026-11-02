# Conferência final no computador

Execute no Terminal do macOS. O bloco abaixo cria uma cópia isolada do código
que será entregue. Ele não altera a pasta original nem publica dados no GitHub.

## Preparação

Use a pasta que contém a cópia original do projeto, com os arquivos em
`data/raw/`. A partir da pasta imediatamente acima dela, execute:

```bash
cd pipeline-saude-sus
ORIGEM_DADOS="$(pwd -P)"
git fetch origin main
CONFERENCIA="$(mktemp -d "${TMPDIR:-/tmp}/pipeline-sus-final.XXXXXX")"
git worktree add --detach "$CONFERENCIA" FETCH_HEAD
cd "$CONFERENCIA"
bash scripts/conferir_entrega.sh "$ORIGEM_DADOS"
```

A variável `ORIGEM_DADOS` guarda o caminho da pasta original antes da mudança
para a cópia isolada. O procedimento funciona sem um nome de conta específico.

O script instala as dependências versionadas e executa Ruff e pytest com cobertura.
Ele confere os hashes publicados, reutiliza o Parquet original apenas para leitura,
copia o dicionário de municípios e gera o dicionário CID na pasta isolada.

Em seguida, executa as cinco etapas do pipeline e as 37 regras de qualidade.
O valor total é impresso sem abreviação e comparado com R$ 2.258.865.118,36.
Os dez marts são comparados com os CSVs publicados, por conteúdo e quantidade,
sem depender da ordem das linhas. Campos numéricos usam precisão de seis casas
na comparação, suficiente para detectar diferença de centavos.

## O que conferir na saída

- Ruff sem erros e cobertura de pelo menos 95%.
- 156 testes aprovados e cobertura de 97,06% no ambiente registrado na validação atual.
- 37 regras de qualidade aprovadas.
- 1.238.234 AIHs na Prata e valor exato de R$ 2.258.865.118,36.
- Dez marts com resultado `OK`.
- Distribuição de `COD_IDADE` na origem.
- Datas mais frequentes entre os registros anteriores a fevereiro de 2008.
- Competência 2026/04 nas 1.238.763 linhas da Bronze.
- Nove figuras no HTML, incluindo o mapa SVG.

Uma diferença nos perfis pode revelar o efeito da correção de idade ignorada.
Não ajuste o resultado para fazê-lo coincidir. Preserve a saída e revise os
agregados antes da publicação final. O arquivo `conferencia-final.json` resume
as comparações e não é versionado.

## Conferência visual

```bash
uv run streamlit run app.py --server.port 8502
```

Abra `http://localhost:8502` e confira os dois seletores no topo, cinco cartões,
nove gráficos e o painel expansível de detalhes por sexo e faixa etária.
Escolha Brasil e uma UF. Mortalidade por CID e concentração municipal devem
continuar identificadas como análises do Brasil.

Abra também o `docs/relatorio.html` gerado. Confira o mapa completo, os nove
gráficos, as legendas, a curva municipal e a leitura em uma janela menor.
Abra a tabela de perfil e teste os filtros de sexo e faixa etária.

## Instância pública do Streamlit

Confira os nove gráficos, o detalhamento do perfil e os valores atuais na
instância pública. Se uma versão anterior persistir, use `Manage app` e
`Reboot app` na conta proprietária. Nunca compartilhe credenciais no repositório.

## Auditoria de descrições e datas

A execução cria três CSVs em `data/auditoria/`. Confira os códigos ainda sem
nome, o histograma mensal e os grupos com datas ou permanências sinalizadas.
A competência deve aparecer como `2026-04-01` na Prata. A série de entradas
deve continuar com 703.067 internações, sem incorporar as entradas anteriores.
As fontes oficiais complementares devem completar os sete códigos que antes
somavam 76 internações sem descrição. Preserve os arquivos de auditoria e a
saída do Terminal para confirmar o resultado sobre os microdados.

## Resultado histórico

A conferência do commit `24e781e` foi aprovada no macOS com Python 3.11.4.
Passaram 145 testes, cobertura de 97,01% e as 37 regras. O valor exato foi
R$ 2.258.865.118,36. Os dez marts coincidiram com os CSVs publicados.
A correção de idade ignorada não alterou este conjunto. O procedimento acima
permanece disponível para repetir a verificação.

## Conferência da atualização de competência

Executei duas conferências completas do commit `4510595` no macOS,
com Python 3.11.4. Passaram 156 testes, cobertura de 97,06%, as 37 regras e a
comparação dos dez marts, sem linhas exclusivas. O valor exato permaneceu em
R$ 2.258.865.118,36. O dicionário passou a 14.240 códigos, sem CID sem descrição.
A Prata preservou a competência abril de 2026. O HTML foi gerado com nove figuras.
A auditoria listou 6.336 grupos para investigação. A consulta ao campo `IDENT`
confirmou tipo 5 nas 617 entradas de 01/01/2008. Uma tem saída em 20/04/2026
e 20 dias registrados, uma tem saída em 26/04/2026 e 26 dias, e 615 têm saída
em 30/04/2026 e 30 dias. Esse padrão é compatível com a permanência por
competência das AIHs de continuidade. Os demais alertas continuam sujeitos
a investigação. Os arquivos originais foram preservados.
