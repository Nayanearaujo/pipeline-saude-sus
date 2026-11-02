# Conferência final no computador

Execute no Terminal do macOS. O bloco abaixo cria uma cópia isolada do código
que será entregue. Ele não altera a pasta original nem publica dados no GitHub.

## Preparação

Se a revisão ainda estiver em um pedido de alteração, use a referência indicada
na resposta de entrega. Após a aprovação e incorporação, use `main`.

```bash
cd /Users/nayane/pipeline-saude-sus
git fetch origin main
CONFERENCIA="$(mktemp -d /Users/nayane/pipeline-sus-final.XXXXXX)"
git worktree add --detach "$CONFERENCIA" FETCH_HEAD
cd "$CONFERENCIA"
bash scripts/conferir_entrega.sh /Users/nayane/pipeline-saude-sus
```

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
- 156 testes aprovados e cobertura de 97,06% no ambiente usado nesta revisão.
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

## Auditoria nova

A execução cria três CSVs em `data/auditoria/`. Confira os códigos ainda sem
nome, o histograma mensal e os grupos com datas ou permanências sinalizadas.
A competência deve aparecer como `2026-04-01` na Prata. A série de entradas
deve continuar com 703.067 internações, sem incorporar as entradas anteriores.
As fontes oficiais complementares devem completar os sete códigos que antes
somavam 76 internações sem descrição. Preserve os arquivos de auditoria e a
saída do Terminal para confirmar o resultado sobre os microdados.

## Resultado já obtido

A conferência do commit `24e781e` foi aprovada no macOS com Python 3.11.4.
Passaram 145 testes, cobertura de 97,01% e as 37 regras. O valor exato foi
R$ 2.258.865.118,36. Os dez marts coincidiram com os CSVs publicados.
A correção de idade ignorada não alterou este conjunto. O procedimento acima
permanece disponível para repetir a verificação.
