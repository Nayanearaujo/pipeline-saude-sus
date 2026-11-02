-- Grao do resultado: um dia de internacao no Brasil inteiro.
-- Pergunta: como as internacoes se distribuem ao longo do mes no pais?
-- Consolida a serie diaria nacional. Mart separado do 05 (por UF) porque somar
-- os estados num unico dia e agregacao, trabalho do mart e nao da tela.

-- Eixo = data de ENTRADA (ver nota no mart 05). Serie so das entradas do mes
-- de referencia, que NAO soma o total dos KPIs (esse e por competencia).
-- O mês vem da competência de processamento, preservada na Prata.
-- A execução exige uma única competência, sem inferência pela data de entrada.
WITH ref AS (
    SELECT CASE WHEN count(DISTINCT competencia) = 1
                     AND count(*) FILTER (WHERE competencia IS NULL) = 0
                THEN min(competencia)
                ELSE error('A série exige uma única competência válida') END AS mes
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
