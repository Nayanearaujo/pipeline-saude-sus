"""Auditoria agregada de descrições e datas, sem modificar o banco."""
from pathlib import Path

from pipeline.db import conectar

DESTINO = Path(__file__).resolve().parents[1] / "data" / "auditoria"
SEM_DESCRICAO = "nao classificado"


def tabelas(con):
    """Gera achados por código, competência e datas, sem identificadores de AIH."""
    cids = con.execute("""
        SELECT i.cid_principal AS cid, count(*) AS internacoes,
               round(100.0 * count(*) / (SELECT count(*) FROM prata.internacoes), 6) AS pct_do_total,
               round(sum(i.valor_total), 2) AS valor_total,
               'nao classificado' AS situacao
        FROM prata.internacoes i LEFT JOIN prata.cid10 c ON c.cid = i.cid_principal
        WHERE c.doenca IS NULL OR trim(c.doenca) = '' OR c.doenca = 'CID ' || i.cid_principal
        GROUP BY i.cid_principal ORDER BY internacoes DESC, cid
    """).df()
    datas = con.execute("""
        SELECT competencia, uf, data_internacao, data_saida, dias_permanencia,
               date_diff('day', data_internacao, data_saida) AS intervalo_calendario_dias,
               count(*) AS internacoes,
               data_internacao < competencia - INTERVAL 10 YEAR AS entrada_antiga,
               data_saida < data_internacao AS saida_anterior_entrada,
               data_internacao IS NULL OR data_saida IS NULL AS data_ausente,
               data_internacao >= competencia + INTERVAL 1 MONTH AS entrada_posterior_competencia,
               dias_permanencia != date_diff('day', data_internacao, data_saida) AS permanencia_divergente
        FROM prata.internacoes
        WHERE data_internacao < competencia - INTERVAL 10 YEAR
           OR data_saida < data_internacao
           OR data_internacao IS NULL OR data_saida IS NULL
           OR data_internacao >= competencia + INTERVAL 1 MONTH
           OR dias_permanencia != date_diff('day', data_internacao, data_saida)
        GROUP BY ALL ORDER BY competencia, data_internacao, uf, data_saida, dias_permanencia
    """).df()
    meses = con.execute("""
        SELECT competencia, date_trunc('month', data_internacao)::DATE AS mes_entrada,
               count(*) AS internacoes
        FROM prata.internacoes GROUP BY ALL ORDER BY competencia, mes_entrada
    """).df()
    return {"cid_sem_descricao": cids, "datas_para_investigar": datas, "entradas_por_mes": meses}


def main():
    """Exporta os achados locais. Alertas não alteram nem excluem internações."""
    con = conectar()
    try:
        achados = tabelas(con)
    finally:
        con.close()
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome, dados in achados.items():
        dados.to_csv(DESTINO / f"{nome}.csv", index=False)
        print(f"  Auditoria: {nome}, {len(dados)} grupos")
    print("  Datas antigas e permanências divergentes são alertas para investigação, não causas comprovadas.")


if __name__ == "__main__":
    main()
