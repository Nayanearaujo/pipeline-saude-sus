-- Grao do resultado: um diagnostico (CID principal) por UF.
-- Pergunta: quais as doencas que mais internam, em cada estado?
-- Traz o nome legivel da doenca com LEFT JOIN no dicionario CID-10, para nao
-- perder a internacao quando o codigo nao tem traducao (vira 'nao classificado').
-- O painel filtra por UF; por isso o grao inclui a UF, e o ranking e dentro dela.

SELECT
    i.uf,
    i.cid_principal                                  AS cid,
    COALESCE(c.doenca, 'nao classificado')           AS doenca,
    COUNT(*)                                          AS internacoes,
    ROUND(SUM(i.valor_total), 2)                      AS valor_total
FROM prata.internacoes AS i
LEFT JOIN prata.cid10   AS c ON c.cid = i.cid_principal
WHERE i.uf IS NOT NULL
GROUP BY i.uf, i.cid_principal, COALESCE(c.doenca, 'nao classificado')
ORDER BY i.uf, internacoes DESC;
