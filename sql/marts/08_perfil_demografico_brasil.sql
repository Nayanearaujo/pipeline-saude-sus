-- Grao do resultado: uma faixa etaria por sexo no Brasil inteiro.
-- Pergunta: quem interna mais, por idade e sexo, no pais?
-- Consolida o perfil nacional. Mart separado do 04 (por UF) pelo mesmo motivo:
-- somar os estados e agregacao, feita aqui e nao na tela.

SELECT
    CASE
        WHEN idade IS NULL           THEN 'nao informado'
        WHEN idade < 1               THEN '< 1 ano'
        WHEN idade BETWEEN 1 AND 14  THEN '1-14'
        WHEN idade BETWEEN 15 AND 29 THEN '15-29'
        WHEN idade BETWEEN 30 AND 49 THEN '30-49'
        WHEN idade BETWEEN 50 AND 64 THEN '50-64'
        ELSE '65+'
    END                              AS faixa_etaria,
    COALESCE(sexo, 'nao informado')  AS sexo,
    COUNT(*)                         AS internacoes,
    ROUND(AVG(dias_permanencia), 1)  AS dias_medio
FROM prata.internacoes
GROUP BY faixa_etaria, COALESCE(sexo, 'nao informado')
ORDER BY internacoes DESC;
