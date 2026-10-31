-- Grao do resultado: uma UF.
-- Pergunta: como cada estado se compara em volume, gasto e desfecho?
-- E o mart central do painel: alimenta o mapa, os rankings e a comparacao.
-- Internacoes sem UF (codigo de municipio que nao casou com o dicionario de
-- UFs) ficam de fora deste recorte, porque o indicador e "por estado".

-- pct_internacoes e pct_valor: participacao da UF no total do pais, com window
-- function (SUM OVER). custo_mediana e dias_mediana completam a media: a media
-- e puxada por internacoes de altissimo custo; a mediana mostra o caso tipico.
-- Tudo pronto no mart para o painel nao calcular. Desempate por uf no ORDER BY.
SELECT
    uf,
    regiao,
    COUNT(*)                                                   AS internacoes,
    ROUND(SUM(valor_total), 2)                                 AS valor_total,
    ROUND(AVG(valor_total), 2)                                 AS custo_medio,
    ROUND(MEDIAN(valor_total), 2)                              AS custo_mediana,
    ROUND(AVG(dias_permanencia), 1)                            AS dias_medio,
    MEDIAN(dias_permanencia)                                   AS dias_mediana,
    ROUND(100.0 * COUNT(*) FILTER (WHERE morte) / COUNT(*), 2) AS taxa_mortalidade_pct,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)         AS pct_internacoes,
    ROUND(100.0 * SUM(valor_total) / SUM(SUM(valor_total)) OVER (), 2) AS pct_valor
FROM prata.internacoes
WHERE uf IS NOT NULL
GROUP BY uf, regiao
ORDER BY internacoes DESC, uf;
