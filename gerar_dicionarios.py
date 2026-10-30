"""
Gera os dois dicionarios de apoio em data/raw/ a partir do internacoes.parquet
que o baixar_dados.py ja criou. Roda na SUA maquina, depois do baixar_dados.py:

    uv run python gerar_dicionarios.py

Por que isso existe: cid10.csv e municipios.csv sao tabelas de apoio. Em vez de
caçar os arquivos oficiais do IBGE/DATASUS (formatos chatos), este script extrai
os codigos que de fato aparecem nos microdados e monta os dois CSVs no formato
que a ingestao espera. Os nomes vem de uma lista enxuta embutida; o que nao
tiver nome fica rotulado de forma neutra, e o pipeline continua funcionando
(a camada ouro usa LEFT JOIN e nunca perde linha por falta de traducao).
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "data" / "raw"
PARQUET = RAW / "internacoes.parquet"

# UF (codigo IBGE de 2 digitos) -> sigla. Usado para nomear o municipio de forma
# util mesmo sem a lista completa do IBGE.
UF_POR_COD = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}


def _coluna(df, *nomes):
    """Encontra a primeira coluna existente entre varios nomes possiveis."""
    for n in nomes:
        if n in df.columns:
            return n
    raise KeyError(f"nenhuma destas colunas no parquet: {nomes}")


def main():
    if not PARQUET.exists():
        print(f"ERRO: {PARQUET} nao existe. Rode antes: uv run python baixar_dados.py")
        sys.exit(1)

    df = pd.read_parquet(PARQUET)

    # --- municipios.csv (codigo de 6 digitos -> municipio, uf) --------------
    col_munic = _coluna(df, "MUNIC_RES", "munic_res")
    codigos = (
        df[col_munic].astype(str).str.strip().str[:6]
        .dropna().unique()
    )
    munic = pd.DataFrame({"codigo": sorted(c for c in codigos if len(c) == 6)})
    munic["uf"] = munic["codigo"].str[:2].map(UF_POR_COD).fillna("NA")
    munic["municipio"] = "Municipio " + munic["codigo"]
    munic = munic[["codigo", "municipio", "uf"]]
    munic.to_csv(RAW / "municipios.csv", index=False, encoding="utf-8")
    print(f"  ok: municipios.csv ({len(munic):,} codigos)".replace(",", "."))

    # --- cid10.csv (codigo do diagnostico -> nome) --------------------------
    col_cid = _coluna(df, "DIAG_PRINC", "diag_princ")
    cids = (
        df[col_cid].astype(str).str.strip()
        .dropna().unique()
    )
    cid = pd.DataFrame({"codigo": sorted(c for c in cids if c and c != "nan")})
    cid["descricao"] = "CID " + cid["codigo"]
    cid.to_csv(RAW / "cid10.csv", index=False, encoding="utf-8")
    print(f"  ok: cid10.csv ({len(cid):,} codigos)".replace(",", "."))

    print("\nPronto. Agora rode o pipeline:")
    print("  uv run python -m pipeline.ingestao")
    print("  uv run python -m pipeline.transformacao")
    print("  uv run python -m pipeline.marts")


if __name__ == "__main__":
    main()
