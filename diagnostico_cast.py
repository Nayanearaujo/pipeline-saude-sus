"""
Diagnostico (so leitura): existe valor sujo na bronze que quebraria o CAST estrito?

NAO altera nada. Le bronze.internacoes e conta, por coluna que hoje usa
TRY_CAST, quantos valores sao "sujos": nao nulos, nao vazios, mas que falham na
conversao (TRY_CAST devolve NULL). Se tudo der 0, trocar TRY_CAST por CAST e
seguro. Se der > 0, mostra exemplos para decidirmos o que fazer.

    uv run python diagnostico_cast.py
"""
import sys

from pipeline.db import conectar

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# coluna da bronze -> expressao de conversao que a transformacao usa hoje
CONVERSOES = {
    "VAL_TOT": "TRY_CAST(VAL_TOT AS DECIMAL(12,2))",
    "DIAS_PERM": "TRY_CAST(DIAS_PERM AS INTEGER)",
    "IDADE": "TRY_CAST(IDADE AS INTEGER)",
    "DT_INTER": "TRY_CAST(strptime(CAST(DT_INTER AS VARCHAR), '%Y%m%d') AS DATE)",
    "DT_SAIDA": "TRY_CAST(strptime(CAST(DT_SAIDA AS VARCHAR), '%Y%m%d') AS DATE)",
}


def main():
    con = conectar()
    print("Coluna     | nao-nulos | sujos (falham no CAST) | exemplos")
    print("-" * 72)
    total_sujo = 0
    for col, conv in CONVERSOES.items():
        # 'sujo' = tem texto (apos TRIM) mas a conversao devolve NULL
        sujos = con.execute(f"""
            SELECT count(*) FROM bronze.internacoes
            WHERE NULLIF(TRIM(CAST({col} AS VARCHAR)), '') IS NOT NULL
              AND {conv} IS NULL
        """).fetchone()[0]
        nao_nulos = con.execute(f"""
            SELECT count(*) FROM bronze.internacoes
            WHERE NULLIF(TRIM(CAST({col} AS VARCHAR)), '') IS NOT NULL
        """).fetchone()[0]
        exemplos = ""
        if sujos:
            linhas = con.execute(f"""
                SELECT DISTINCT CAST({col} AS VARCHAR) FROM bronze.internacoes
                WHERE NULLIF(TRIM(CAST({col} AS VARCHAR)), '') IS NOT NULL
                  AND {conv} IS NULL
                LIMIT 5
            """).fetchall()
            exemplos = ", ".join(repr(r[0]) for r in linhas)
        total_sujo += sujos
        print(f"{col:<10} | {nao_nulos:>9,} | {sujos:>22,} | {exemplos}".replace(",", "."))
    con.close()

    print("-" * 72)
    if total_sujo == 0:
        print("RESULTADO: nenhum valor sujo. Trocar TRY_CAST por CAST e seguro.")
    else:
        print(f"RESULTADO: {total_sujo} valores sujos. Decidir o tratamento antes de trocar.")


if __name__ == "__main__":
    main()
