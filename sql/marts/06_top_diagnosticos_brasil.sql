-- Grao do resultado: um diagnostico (CID principal) no Brasil inteiro.
-- Pergunta: quais as doencas que mais internam no pais?
-- Mart separado do 03 (que e por UF) de proposito: consolidar o Brasil e uma
-- agregacao, e agregacao e trabalho do mart, nunca da tela. Assim o painel so
-- escolhe qual mart ler (nacional ou por UF), sem recalcular nada.

SELECT
    i.cid_principal                         AS cid,
    COALESCE(c.doenca, 'nao classificado')  AS doenca,
    COUNT(*)                                AS internacoes,
    ROUND(SUM(i.valor_total), 2)            AS valor_total
FROM prata.internacoes AS i
LEFT JOIN prata.cid10   AS c ON c.cid = i.cid_principal
GROUP BY i.cid_principal, COALESCE(c.doenca, 'nao classificado')
ORDER BY internacoes DESC;
