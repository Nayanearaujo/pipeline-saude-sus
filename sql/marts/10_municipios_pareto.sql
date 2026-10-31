-- Grao do resultado: um municipio de residencia com internacao, do maior gasto
-- para o menor, com o gasto acumulado ate ele.
-- Pergunta: quantos municipios concentram 80% do gasto hospitalar do SUS?
-- Degrau 5 da aula: soma acumulada em window (SUM OVER ORDER BY). Usa a 4a
-- tabela da prata (municipios) para o nome legivel da cidade, com desempate
-- por cod_municipio para o acumulado ser deterministico.
WITH gasto_municipio AS (
    -- Grao: um municipio de residencia. Agrega antes de juntar o nome, para o
    -- JOIN com o dicionario nao multiplicar internacao.
    SELECT
        i.cod_municipio,
        COUNT(*)                     AS internacoes,
        ROUND(SUM(i.valor_total), 2) AS valor_total
    FROM prata.internacoes AS i
    WHERE i.cod_municipio IS NOT NULL
    GROUP BY i.cod_municipio
),
nomeado AS (
    -- Grao: um municipio, com nome e UF do dicionario (1 linha por cod_municipio).
    SELECT
        g.cod_municipio,
        COALESCE(m.municipio, 'nao identificado') AS municipio,
        m.uf,
        g.internacoes,
        g.valor_total
    FROM gasto_municipio AS g
    LEFT JOIN prata.municipios AS m ON m.cod_municipio = g.cod_municipio
)
SELECT
    cod_municipio,
    municipio,
    uf,
    internacoes,
    valor_total,
    ROW_NUMBER() OVER (ORDER BY valor_total DESC, cod_municipio) AS posicao,
    ROUND(
        100.0 * SUM(valor_total) OVER (ORDER BY valor_total DESC, cod_municipio)
        / SUM(valor_total) OVER (),
        2
    ) AS pct_acumulado
FROM nomeado
ORDER BY posicao;
