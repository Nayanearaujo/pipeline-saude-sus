"""
Gera os dois dicionarios de apoio em data/raw/: cid10.csv e municipios.csv.
Roda na SUA maquina, depois do baixar_dados.py:

    uv run python gerar_dicionarios.py

Estrategia: baixa as tabelas OFICIAIS (IBGE para municipios, DATASUS para
CID-10) e salva no formato que a ingestao espera (codigo -> nome). Se nao houver
internet, cai num modo neutro (nomes rotulados pelo codigo) para nao travar o
pipeline. A camada ouro usa LEFT JOIN e nunca perde linha por falta de nome.

Fontes (dados publicos):
  municipios  API oficial do IBGE (localidades); espelho CSV como fallback
  cid10       DATASUS via cleytonferrari/CidDataSus (CSV, categorias e subcategorias)
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "data" / "raw"
PARQUET = RAW / "internacoes.parquet"

# Fonte primaria: API oficial do IBGE (JSON). Cada item tem id (codigo de 7
# digitos) e nome do municipio. E a fonte que o README cita.
URL_IBGE_API = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
# Fonte secundaria (espelho em CSV), usada so se a API oficial falhar.
URL_MUNICIPIOS = (
    "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/"
    "main/csv/municipios.csv"
)
URL_CID = (
    "https://raw.githubusercontent.com/cleytonferrari/CidDataSus/"
    "b6eb7d0fe8be752307741d156d67eacf539a186c/CIDImport/Repositorio/Resources/CID-10-SUBCATEGORIAS.CSV"
)

URL_CID_CATEGORIAS = URL_CID.replace("SUBCATEGORIAS", "CATEGORIAS")

UF_POR_COD = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}


def _coluna(df, *nomes):
    """Devolve o primeiro nome de coluna presente no DataFrame."""
    for n in nomes:
        if n in df.columns:
            return n
    raise KeyError(f"nenhuma destas colunas: {nomes}")


def _municipios_da_api_ibge() -> pd.DataFrame:
    """Le os municipios da API oficial do IBGE (JSON) com timeout e validacao.

    Devolve um DataFrame com as colunas codigo (6 digitos), municipio e uf.
    Levanta excecao se a rede falhar ou o formato nao bater (quem chama trata)."""
    import gzip
    import json
    import urllib.request

    # alguns endpoints do IBGE respondem com gzip; pede texto e descomprime se vier.
    req = urllib.request.Request(URL_IBGE_API, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as resposta:
        bruto = resposta.read()
        if resposta.headers.get("Content-Encoding") == "gzip" or bruto[:2] == b"\x1f\x8b":
            bruto = gzip.decompress(bruto)
    dados = json.loads(bruto.decode("utf-8"))
    if not isinstance(dados, list) or not dados:
        raise ValueError("resposta da API do IBGE vazia ou em formato inesperado")

    linhas = []
    for item in dados:
        codigo7 = str(item["id"])              # id = codigo IBGE de 7 digitos
        codigo6 = codigo7[:6]
        uf = UF_POR_COD.get(codigo6[:2], "NA")
        linhas.append({"codigo": codigo6, "municipio": item["nome"], "uf": uf})
    return pd.DataFrame(linhas).drop_duplicates("codigo")


# ---------------------------------------------------------------------------
# Municipios: 1) API oficial do IBGE; 2) espelho em CSV; 3) nomes neutros.
# ---------------------------------------------------------------------------
def gerar_municipios(codigos_usados: set[str]):
    """Gera municipios.csv, tentando a API oficial do IBGE antes dos fallbacks."""
    # 1) fonte primaria: API oficial do IBGE (o que o README promete)
    try:
        munic = _municipios_da_api_ibge()
        munic.to_csv(RAW / "municipios.csv", index=False, encoding="utf-8")
        print(f"  ok: municipios.csv ({len(munic):,} da API do IBGE)".replace(",", "."))
        return
    except (OSError, ValueError, KeyError) as e:
        print(f"  aviso: API do IBGE indisponivel ({e}); tentando o espelho CSV.")

    # 2) fonte secundaria: espelho em CSV (GitHub)
    try:
        ibge = pd.read_csv(URL_MUNICIPIOS, dtype=str)
        col_cod = _coluna(ibge, "codigo_ibge", "codigo", "cod_ibge")
        col_nome = _coluna(ibge, "nome", "municipio", "name")
        ibge["codigo6"] = ibge[col_cod].str[:6]
        ibge["uf"] = ibge["codigo6"].str[:2].map(UF_POR_COD).fillna("NA")
        munic = ibge[["codigo6", col_nome, "uf"]].rename(
            columns={"codigo6": "codigo", col_nome: "municipio"}
        )
        munic = munic.drop_duplicates("codigo")
        munic.to_csv(RAW / "municipios.csv", index=False, encoding="utf-8")
        print(f"  ok: municipios.csv ({len(munic):,} do espelho CSV)".replace(",", "."))
        return
    except (OSError, ValueError, KeyError) as e:
        print(f"  aviso: espelho CSV indisponivel ({e}); usando nomes neutros.")

    # 3) ultimo recurso: nomes neutros (nao trava o pipeline sem internet)
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
        tabelas = []
        for url in (URL_CID_CATEGORIAS, URL_CID):
            cid = pd.read_csv(url, sep=";", dtype=str, encoding="latin-1")
            col_cod = _coluna(cid, "SUBCAT", "CODIGO", "CAT")
            col_desc = _coluna(cid, "DESCRICAO", "DESCRABREV", "descricao")
            tabelas.append(cid[[col_cod, col_desc]].rename(
                columns={col_cod: "codigo", col_desc: "descricao"}
            ))
        out = pd.concat(tabelas, ignore_index=True)
        out["codigo"] = out["codigo"].str.strip().str.replace(".", "", regex=False)
        out = out.dropna(subset=["codigo", "descricao"]).drop_duplicates("codigo")
        out.to_csv(RAW / "cid10.csv", index=False, encoding="utf-8")
        print(f"  ok: cid10.csv ({len(out):,} do espelho CID-10)".replace(",", "."))
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
