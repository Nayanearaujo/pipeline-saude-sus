-- Grao do resultado: a operacao inteira, uma linha so.
-- Pergunta: os numeros de topo do painel (cartoes), no mes inteiro, Brasil.
-- Fonte unica: prata.internacoes (uma linha = uma internacao/AIH).
-- custo_medio e o valor total dividido pelo numero de internacoes, no grao de
-- internacao (nao a media de item de nada). taxa_mortalidade e a fracao de
-- internacoes com obito.

SELECT
    COUNT(*)                                                  AS internacoes,
    COUNT(DISTINCT uf)                                        AS ufs,
    ROUND(SUM(valor_total), 2)                                AS valor_total,
    ROUND(AVG(valor_total), 2)                                AS custo_medio,
    ROUND(AVG(dias_permanencia), 1)                           AS dias_medio,
    ROUND(100.0 * COUNT(*) FILTER (WHERE morte) / COUNT(*), 2) AS taxa_mortalidade_pct
FROM prata.internacoes;
