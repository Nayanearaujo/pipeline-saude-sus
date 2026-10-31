-- Grao do resultado: um dia de internacao por UF.
-- Pergunta: como as internacoes se distribuem ao longo do mes, em cada estado?
-- Alimenta a linha temporal do painel. Usa a data de internacao (quando o
-- paciente entrou), nao a de saida. Dias sem internacao simplesmente nao
-- aparecem (o grafico liga os pontos existentes).

-- Eixo = data de ENTRADA do paciente. O arquivo RD e por competencia (mes de
-- processamento/pagamento da AIH): boa parte das AIH pagas no mes de referencia
-- teve entrada em meses anteriores. Por isso esta serie (so as entradas do mes)
-- NAO soma o total de internacoes dos KPIs (que e por competencia): a diferenca
-- e grande e proposital.
-- O mes de referencia e derivado dos dados (o mes com mais entradas), nao
-- fixado no SQL: trocar o arquivo baixado nao exige editar o mart.
WITH ref AS (
    SELECT date_trunc('month', mode(data_internacao)) AS mes
    FROM prata.internacoes
)
SELECT
    uf,
    data_internacao                 AS dia,
    COUNT(*)                        AS internacoes,
    ROUND(SUM(valor_total), 2)      AS valor_total
FROM prata.internacoes, ref
WHERE uf IS NOT NULL
  AND data_internacao >= ref.mes
  AND data_internacao <  ref.mes + INTERVAL 1 MONTH
GROUP BY uf, data_internacao
ORDER BY uf, dia;
