# Gráficos · manutenção da identidade visual da saúde

O dashboard mantém o cabeçalho, o fundo verde-bebê, os cartões e o fluxo contínuo aprovados.

| Gráfico | Melhoria |
|---|---|
| Mapa | Geometria das 27 UFs embutida, limites enquadrados, fundo sem tiles e unidades corretas no detalhe. Não busca o GeoJSON externo ao abrir. |
| Ranking de UFs | Altura para leitura das 27 linhas e rótulos próprios para dinheiro, dias e percentuais. |
| Regiões | Detalhe com volume/valor e participação; não soma médias ou taxas para formar uma rosca. |
| Valor médio por UF | Média e mediana já existentes no mart, com símbolos distintos e valores completos no detalhe. |
| Diagnósticos | CID no eixo para distinguir nomes truncados; nome completo, volume, valor e participação no detalhe. |
| Série diária | Datas legíveis, detalhe unificado e anotação do pico já presente nos dados. |
| Sexo e faixa etária | Números nas barras quando couberem, permanência média no detalhe e tabela expansível com os dados do mart. |
| Mortalidade por CID | Nome do diagnóstico e CID visíveis; volume e óbitos no detalhe; explicação de CID, AIH e taxa abaixo. |
| Pareto municipal | Curva completa, referência de 80% dentro da área visível, explicação dos eixos e botões para todos ou os primeiros 30. |

Os SQLs dos marts e as métricas visuais permanecem iguais. A atualização de
CID alterou somente descrições em três CSVs; não criou taxas, médias ou
percentuais na interface. A mediana, a permanência por grupo e o percentual
acumulado são lidos prontos dos marts.

O Streamlit usa MapLibre com geometria local em `assets/`, cuja licença e
atribuição estão preservadas. Precisa de JavaScript e WebGL. No relatório HTML,
o mapa é SVG completo e centralizado, sem câmera nem dependência de WebGL.
A geometria é simplificada para apresentação, não para análise geoespacial.

Validação: 138 testes, cobertura de 97,01% incluindo scripts auxiliares e Ruff aprovado.
O visual do Streamlit e o enquadramento do mapa SVG foram aprovados na revisão
anterior. Esta atualização preserva as figuras e altera somente os nomes CID.
O HTML foi regenerado a partir dos CSVs atuais.
