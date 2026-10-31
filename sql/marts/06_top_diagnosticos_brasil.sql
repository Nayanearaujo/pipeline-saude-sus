-- Grao do resultado: um diagnostico (CID principal) no Brasil inteiro.
-- Pergunta: quais as doencas que mais internam no pais?
-- Mart separado do 03 (que e por UF) de proposito: consolidar o Brasil e uma
-- agregacao, e agregacao e trabalho do mart, nunca da tela. A coluna posicao
-- (rank com desempate por cid) deixa o ranking deterministico; o painel le as
-- 10 primeiras sem precisar ordenar nem calcular nada.
WITH nacional AS (
    -- Grao: um diagnostico (CID principal) no pais.
    SELECT
        i.cid_principal                         AS cid,
        COALESCE(c.doenca, 'nao classificado')  AS doenca,
        COUNT(*)                                AS internacoes,
        ROUND(SUM(i.valor_total), 2)            AS valor_total,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_do_total
    FROM prata.internacoes AS i
    LEFT JOIN prata.cid10   AS c ON c.cid = i.cid_principal
    GROUP BY i.cid_principal, COALESCE(c.doenca, 'nao classificado')
)
SELECT
    cid,
    doenca,
    internacoes,
    valor_total,
    pct_do_total,
    ROW_NUMBER() OVER (ORDER BY internacoes DESC, cid) AS posicao
FROM nacional
ORDER BY posicao;
