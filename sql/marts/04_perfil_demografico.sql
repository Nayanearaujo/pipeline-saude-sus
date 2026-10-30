-- Grao do resultado: uma faixa etaria por sexo por UF.
-- Pergunta: quem interna mais, por idade e sexo, em cada estado?
-- A faixa etaria e derivada da idade em anos, com CASE WHEN. Internacoes sem
-- sexo ou sem idade ficam em 'nao informado' em vez de sumir, para o total do
-- perfil bater com o total de internacoes do estado.

SELECT
    uf,
    CASE
        WHEN idade IS NULL           THEN 'nao informado'
        WHEN idade < 1               THEN '< 1 ano'
        WHEN idade BETWEEN 1 AND 14  THEN '1-14'
        WHEN idade BETWEEN 15 AND 29 THEN '15-29'
        WHEN idade BETWEEN 30 AND 49 THEN '30-49'
        WHEN idade BETWEEN 50 AND 64 THEN '50-64'
        ELSE '65+'
    END                                          AS faixa_etaria,
    COALESCE(sexo, 'nao informado')              AS sexo,
    COUNT(*)                                     AS internacoes,
    ROUND(AVG(dias_permanencia), 1)              AS dias_medio
FROM prata.internacoes
WHERE uf IS NOT NULL
GROUP BY uf, faixa_etaria, COALESCE(sexo, 'nao informado')
ORDER BY uf, internacoes DESC;
