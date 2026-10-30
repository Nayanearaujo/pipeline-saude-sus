"""
Gera os dois dicionarios de apoio em data/raw/: cid10.csv e municipios.csv.
Roda na SUA maquina, depois do baixar_dados.py:

    uv run python gerar_dicionarios.py

Estrategia: baixa as tabelas OFICIAIS (IBGE para municipios, DATASUS para
CID-10) e salva no formato que a ingestao espera (codigo -> nome). Se nao houver
internet, cai num modo neutro (nomes rotulados pelo codigo) para nao travar o
pipeline. A camada ouro usa LEFT JOIN e nunca perde linha por falta de nome.

Fontes (dados publicos):
  municipios  IBGE via kelvins/municipios-brasileiros (CSV, 5.570 municipios)
  cid10       DATASUS via cleytonferrari/CidDataSus (CSV, subcategorias)
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "data" / "raw"
PARQUET = RAW / "internacoes.parquet"

URL_MUNICIPIOS = (
    "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/"
    "main/csv/municipios.csv"
)
URL_CID = (
    "https://raw.githubusercontent.com/cleytonferrari/CidDataSus/"
    "master/CIDImport/Repositorio/Resources/CID-10-SUBCATEGORIAS.CSV"
)

UF_POR_COD = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}


def _coluna(df, *nomes):
    for n in nomes:
        if n in df.columns:
            return n
    raise KeyError(f"nenhuma destas colunas: {nomes}")


# ---------------------------------------------------------------------------
# Municipios: baixa a tabela do IBGE; fallback para nomes neutros.
# ---------------------------------------------------------------------------
def gerar_municipios(codigos_usados: set[str]):
    try:
        ibge = pd.read_csv(URL_MUNICIPIOS, dtype=str)
        # a tabela tem codigo_ibge (7 digitos), nome, codigo_uf
        col_cod = _coluna(ibge, "codigo_ibge", "codigo", "cod_ibge")
        col_nome = _coluna(ibge, "nome", "municipio", "name")
        ibge["codigo6"] = ibge[col_cod].str[:6]
        ibge["uf"] = ibge["codigo6"].str[:2].map(UF_POR_COD).fillna("NA")
        munic = ibge[["codigo6", col_nome, "uf"]].rename(
            columns={"codigo6": "codigo", col_nome: "municipio"}
        )
        munic = munic.drop_duplicates("codigo")
        munic.to_csv(RAW / "municipios.csv", index=False, encoding="utf-8")
        print(f"  ok: municipios.csv ({len(munic):,} do IBGE)".replace(",", "."))
        return
    except Exception as e:  # noqa: BLE001
        print(f"  aviso: nao baixei o IBGE ({e}); usando nomes neutros.")

    munic = pd.DataFrame({"codigo": sorted(c for c in codigos_usados if len(c) == 6)})
    munic["uf"] = munic["codigo"].str[:2].map(UF_POR_COD).fillna("NA")
    munic["municipio"] = "Municipio " + munic["codigo"]
    munic[["codigo", "municipio", "uf"]].to_csv(
        RAW / "municipios.csv", index=False, encoding="utf-8"
    )
    print(f"  ok: municipios.csv ({len(munic):,} neutros)".replace(",", "."))


# ---------------------------------------------------------------------------
# CID-10: baixa a tabela do DATASUS; fallback para nomes neutros.
# ---------------------------------------------------------------------------
def gerar_cid(codigos_usados: set[str]):
    try:
        # a tabela do DATASUS vem em latin-1, separada por ';', com colunas
        # SUBCAT (codigo) e DESCRICAO.
        cid = pd.read_csv(URL_CID, sep=";", dtype=str, encoding="latin-1")
        col_cod = _coluna(cid, "SUBCAT", "CODIGO", "CAT")
        col_desc = _coluna(cid, "DESCRICAO", "DESCRABREV", "descricao")
        out = cid[[col_cod, col_desc]].rename(
            columns={col_cod: "codigo", col_desc: "descricao"}
        )
        out["codigo"] = out["codigo"].str.strip().str.replace(".", "", regex=False)
        out = out.drop_duplicates("codigo")
        out.to_csv(RAW / "cid10.csv", index=False, encoding="utf-8")
        print(f"  ok: cid10.csv ({len(out):,} do DATASUS)".replace(",", "."))
        return
    except Exception as e:  # noqa: BLE001
        print(f"  aviso: nao baixei o CID-10 ({e}); usando nomes neutros.")

    cid = pd.DataFrame({"codigo": sorted(c for c in codigos_usados if c and c != "nan")})
    cid["descricao"] = "CID " + cid["codigo"]
    cid.to_csv(RAW / "cid10.csv", index=False, encoding="utf-8")
    print(f"  ok: cid10.csv ({len(cid):,} neutros)".replace(",", "."))


def main():
    if not PARQUET.exists():
        print(f"ERRO: {PARQUET} nao existe. Rode antes: uv run python baixar_dados.py")
        sys.exit(1)

    df = pd.read_parquet(PARQUET)
    col_munic = _coluna(df, "MUNIC_RES", "munic_res")
    col_cid = _coluna(df, "DIAG_PRINC", "diag_princ")
    cods_munic = set(df[col_munic].astype(str).str.strip().str[:6].dropna().unique())
    cods_cid = set(df[col_cid].astype(str).str.strip().dropna().unique())

    gerar_municipios(cods_munic)
    gerar_cid(cods_cid)

    print("\nPronto. Agora rode o pipeline:")
    print("  uv run python -m pipeline.ingestao")
    print("  uv run python -m pipeline.transformacao")
    print("  uv run python -m pipeline.marts")


if __name__ == "__main__":
    main()
