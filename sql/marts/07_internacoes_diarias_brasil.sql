-- Grao do resultado: um dia de internacao no Brasil inteiro.
-- Pergunta: como as internacoes se distribuem ao longo do mes no pais?
-- Consolida a serie diaria nacional. Mart separado do 05 (por UF) porque somar
-- os estados num unico dia e agregacao, trabalho do mart e nao da tela.

-- Eixo = data de ENTRADA (ver nota no mart 05). Serie so das entradas do mes
-- de referencia, que NAO soma o total dos KPIs (esse e por competencia).
-- O mes de referencia e derivado dos dados (o mes com mais entradas), nao
-- fixado no SQL: trocar o arquivo baixado nao exige editar o mart.
WITH ref AS (
    SELECT date_trunc('month', mode(data_internacao)) AS mes
    FROM prata.internacoes
)
SELECT
    data_internacao             AS dia,
    COUNT(*)                    AS internacoes,
    ROUND(SUM(valor_total), 2)  AS valor_total
FROM prata.internacoes, ref
WHERE data_internacao >= ref.mes
  AND data_internacao <  ref.mes + INTERVAL 1 MONTH
GROUP BY data_internacao
ORDER BY dia;
