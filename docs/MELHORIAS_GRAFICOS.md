# Gráficos · manutenção da identidade visual da saúde

O PR nº 16 foi revisto após a avaliação do usuário. O cabeçalho, o fundo
verde-bebê, os cartões e a disposição anterior foram restaurados. A proposta
azul com abas não faz parte desta revisão.

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

Não foram alterados SQLs ou os dez CSVs auditados. Não foram criadas médias,
taxas ou percentuais novos na interface. A mediana e a permanência por grupo
já existem nos marts; os percentuais do Pareto são lidos prontos.

O mapa usa MapLibre com fundo sem tiles. O arquivo e sua atribuição/licença
estão em `assets/`. A geometria foi simplificada para uso visual e não serve
para análises geoespaciais. JavaScript e WebGL continuam necessários.
A dependência Plotly foi alinhada à API de mapas usada, mantendo a versão 7.1.0
já presente no lockfile e no deploy.

Validação: 120 testes aprovados, cobertura de 97,54%, Ruff aprovado. AppTest
com Brasil/SP/AC e as cinco métricas, nove gráficos e tabela demográfica.
A verificação visual do mapa na prévia do usuário permanece necessária;
a remoção das dependências remotas não equivale a testar seu navegador.
O relatório estático foi regenerado com os mesmos CSVs para acompanhar as
mudanças dos gráficos compartilhados, preservando os valores da auditoria.

Revisão de entrega: o HTML inclui os nove gráficos nacionais e as explicações dos dois complementares. A prévia local das mudanças visuais foi aprovada pelo usuário; a versão do Streamlit público ainda precisa ser confirmada.
