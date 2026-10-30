-- Grao do resultado: um dia de internacao por UF.
-- Pergunta: como as internacoes se distribuem ao longo do mes, em cada estado?
-- Alimenta a linha temporal do painel. Usa a data de internacao (quando o
-- paciente entrou), nao a de saida. Dias sem internacao simplesmente nao
-- aparecem (o grafico liga os pontos existentes).

SELECT
    uf,
    data_internacao                 AS dia,
    COUNT(*)                        AS internacoes,
    ROUND(SUM(valor_total), 2)      AS valor_total
FROM prata.internacoes
WHERE uf IS NOT NULL
  AND data_internacao IS NOT NULL
GROUP BY uf, data_internacao
ORDER BY uf, dia;
