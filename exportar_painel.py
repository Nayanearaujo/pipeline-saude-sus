"""
Exporta a camada ouro (os marts) para CSVs leves em dados_painel/.

Esses CSVs sao a fonte de leitura do dashboard quando ele roda num servidor
(Streamlit Cloud), onde nao da para processar 1,2 milhao de linhas brutas. A
camada ouro tem poucas dezenas de milhares de linhas no total, cabe no Git e
sobe leve. Rode depois do pipeline, na sua maquina:

    uv run python exportar_painel.py

Resultado: dados_painel/<mart>.csv para cada mart. O painel.py le desses CSVs
se o sih.duckdb nao existir (caso do deploy).
"""
import sys
import tempfile
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent
BANCO = RAIZ / "sih.duckdb"
DESTINO = RAIZ / "dados_painel"

MARTS = [
    "kpis_gerais",
    "por_estado",
    "top_diagnosticos",
    "perfil_demografico",
    "internacoes_diarias",
    "top_diagnosticos_brasil",
    "internacoes_diarias_brasil",
    "perfil_demografico_brasil",
    "mortalidade_por_cid",
    "municipios_pareto",
]


def main():
    if not BANCO.exists():
        print(f"ERRO: {BANCO} nao existe. Rode o pipeline antes (pipeline.marts).")
        sys.exit(1)

    # Valida todos os marts antes de alterar qualquer CSV publicado.
    # Se uma consulta falhar, o diretorio de destino permanece intacto.
    con = duckdb.connect(str(BANCO), read_only=True)
    try:
        # Temporarios ao lado do destino: replace exige o mesmo filesystem.
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        con.execute("BEGIN")
        with tempfile.TemporaryDirectory(prefix="marts-export-", dir=DESTINO.parent) as pasta:
            temporario = Path(pasta)
            total = 0
            for nome in MARTS:
                df = con.execute(f"SELECT * FROM ouro.{nome}").df()
                if df.empty:
                    raise ValueError(f"Mart vazio: ouro.{nome}")
                df.to_csv(temporario / f"{nome}.csv", index=False, encoding="utf-8")
                total += len(df)

            con.execute("COMMIT")
            DESTINO.mkdir(parents=True, exist_ok=True)
            for nome in MARTS:
                (temporario / f"{nome}.csv").replace(DESTINO / f"{nome}.csv")
                print(f"  dados_painel/{nome}.csv  publicado")
            print(f"  total {total:,} linhas exportadas".replace(",", "."))
    finally:
        con.close()

    print("\nPronto. Esses CSVs alimentam o dashboard no deploy (Streamlit Cloud).")


if __name__ == "__main__":
    main()
