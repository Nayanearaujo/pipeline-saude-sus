-- Grao do resultado: um dia de internacao por UF.
-- Pergunta: como as internacoes se distribuem ao longo do mes, em cada estado?
-- Alimenta a linha temporal do painel. Usa a data de internacao (quando o
-- paciente entrou), nao a de saida. Dias sem internacao simplesmente nao
-- aparecem (o grafico liga os pontos existentes).

-- Eixo = data de ENTRADA do paciente. O arquivo RD e por competencia (mes de
-- processamento/pagamento da AIH): boa parte das AIH pagas em abril/2026 teve
-- entrada em meses anteriores. Por isso esta serie (so entradas de abril) NAO
-- soma o total de internacoes dos KPIs (que e por competencia): a diferenca e
-- grande e proposital. O filtro recorta abril para o grafico ler o mes atual.
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
