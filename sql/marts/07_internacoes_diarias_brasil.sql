-- Grao do resultado: um dia de internacao no Brasil inteiro.
-- Pergunta: como as internacoes se distribuem ao longo do mes no pais?
-- Consolida a serie diaria nacional. Mart separado do 05 (por UF) porque somar
-- os estados num unico dia e agregacao, trabalho do mart e nao da tela.

-- Eixo = data de ENTRADA (ver nota no mart 05). Serie so das entradas de
-- abril/2026, que NAO soma o total dos KPIs (esse e por competencia).
SELECT
    data_internacao             AS dia,
    COUNT(*)                    AS internacoes,
    ROUND(SUM(valor_total), 2)  AS valor_total
FROM prata.internacoes
WHERE data_internacao >= DATE '2026-04-01'
  AND data_internacao <  DATE '2026-05-01'
GROUP BY data_internacao
ORDER BY dia;
