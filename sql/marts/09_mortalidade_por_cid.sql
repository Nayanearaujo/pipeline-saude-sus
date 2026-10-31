-- Grao do resultado: um diagnostico (CID) com pelo menos 100 internacoes.
-- Pergunta: quais as doencas de maior letalidade hospitalar, entre as que
-- internam o suficiente para o numero significar algo?
-- Degrau 4 da aula: CTE para montar o grao, HAVING para cortar o volume baixo
-- (sem isso, um CID com 2 internacoes e 1 obito viraria "50% de letalidade" e
-- lideraria o ranking por acaso) e RANK para ordenar da maior letalidade.
WITH por_cid AS (
    -- Grao: um CID principal, so os que tem 100+ internacoes.
    SELECT
        i.cid_principal                                           AS cid,
        COALESCE(c.doenca, 'nao classificado')                    AS doenca,
        COUNT(*)                                                  AS internacoes,
        COUNT(*) FILTER (WHERE i.morte)                           AS obitos,
        ROUND(100.0 * COUNT(*) FILTER (WHERE i.morte) / COUNT(*), 2) AS taxa_mortalidade_pct
    FROM prata.internacoes AS i
    LEFT JOIN prata.cid10  AS c ON c.cid = i.cid_principal
    GROUP BY i.cid_principal, COALESCE(c.doenca, 'nao classificado')
    HAVING COUNT(*) >= 100
)
SELECT
    cid,
    doenca,
    internacoes,
    obitos,
    taxa_mortalidade_pct,
    RANK() OVER (ORDER BY taxa_mortalidade_pct DESC, cid) AS posicao
FROM por_cid
ORDER BY posicao;
