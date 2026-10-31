-- Grao do resultado: um dos 10 diagnosticos que mais internam, por UF.
-- Pergunta: quais as 10 doencas que mais internam, em cada estado?
-- Traz o nome legivel da doenca com LEFT JOIN no dicionario CID-10, para nao
-- perder a internacao quando o codigo nao tem traducao (vira 'nao classificado').
-- O "top 10" e feito aqui no mart, com window function, nao na tela: assim o
-- painel so le o mart ja recortado. O desempate por cid deixa o ranking
-- deterministico quando duas doencas tem o mesmo numero de internacoes.
WITH por_uf AS (
    -- Grao: um diagnostico (CID principal) por UF, com a posicao no ranking.
    SELECT
        i.uf,
        i.cid_principal                                  AS cid,
        COALESCE(c.doenca, 'nao classificado')           AS doenca,
        COUNT(*)                                          AS internacoes,
        ROUND(SUM(i.valor_total), 2)                      AS valor_total,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY i.uf), 2) AS pct_do_total,
        ROW_NUMBER() OVER (
            PARTITION BY i.uf
            ORDER BY COUNT(*) DESC, i.cid_principal
        )                                                 AS posicao
    FROM prata.internacoes AS i
    LEFT JOIN prata.cid10   AS c ON c.cid = i.cid_principal
    WHERE i.uf IS NOT NULL
    GROUP BY i.uf, i.cid_principal, COALESCE(c.doenca, 'nao classificado')
)
SELECT uf, cid, doenca, internacoes, valor_total, pct_do_total, posicao
FROM por_uf
WHERE posicao <= 10
ORDER BY uf, posicao;
