-- Grao do resultado: um dia de internacao por UF.
-- Pergunta: como as internacoes se distribuem ao longo do mes, em cada estado?
-- Alimenta a linha temporal do painel. Usa a data de internacao (quando o
-- paciente entrou), nao a de saida. Dias sem internacao simplesmente nao
-- aparecem (o grafico liga os pontos existentes).

-- Filtro de competencia: o recorte e abril/2026. O SIH guarda a data de
-- entrada do paciente, e internacoes longas (ou erro de digitacao) trazem datas
-- de anos anteriores, que esticariam o grafico. Mantemos so o mes de referencia.
SELECT
    uf,
    data_internacao                 AS dia,
    COUNT(*)                        AS internacoes,
    ROUND(SUM(valor_total), 2)      AS valor_total
FROM prata.internacoes
WHERE uf IS NOT NULL
  AND data_internacao >= DATE '2026-04-01'
  AND data_internacao <  DATE '2026-05-01'
GROUP BY uf, data_internacao
ORDER BY uf, dia;
