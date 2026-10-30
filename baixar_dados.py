"""
Baixa os dados brutos do SIH/SUS e grava data/raw/internacoes.parquet.
Roda na SUA maquina (precisa de internet e do PySUS 2.x).

    uv run python baixar_dados.py

API do PySUS 2.x: `from pysus import SIH`, depois get_files(grupo, uf, year,
month) para listar os arquivos do FTP e download(files) para baixar e converter
de .dbc para parquet. O grupo 'RD' e a AIH reduzida (uma linha por internacao).

Ajuste ANO, MES e UFS abaixo. Se o mes ainda nao estiver publicado (o SIH tem
2-4 meses de atraso), o download devolve lista vazia e o script avisa.
"""
import sys
from pathlib import Path

ANO = 2026
MES = 4            # abril
# Para "todos os estados", deixe UFS = None. Para um recorte leve de teste,
# use por exemplo UFS = ["RJ", "SP", "MG"].
UFS = None

RAW = Path(__file__).resolve().parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

TODAS_UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]


def _to_df(baixados):
    """Converte o retorno do download (ParquetSet ou lista) em um DataFrame."""
    import pandas as pd

    if baixados is None:
        return pd.DataFrame()
    if not isinstance(baixados, list):
        baixados = [baixados]
    dfs = []
    for item in baixados:
        # ParquetSet tem to_dataframe(); alguns retornos ja sao DataFrame
        if hasattr(item, "to_dataframe"):
            dfs.append(item.to_dataframe())
        elif isinstance(item, pd.DataFrame):
            dfs.append(item)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def main():
    import pandas as pd  # noqa: F401  (garante erro claro se faltar)

    try:
        from pysus import SIH
    except Exception as e:  # noqa: BLE001
        print(f"ERRO ao importar PySUS: {e}")
        print("Instale/atualize com: uv add pysus")
        sys.exit(1)

    ufs = UFS if UFS is not None else TODAS_UFS
    sih = SIH().load()  # .load() prepara o indice de arquivos do FTP

    print(f"Procurando SIH-RD {MES:02d}/{ANO} para {len(ufs)} UF(s)...")
    arquivos = sih.get_files("RD", uf=ufs, year=ANO, month=MES)

    if not arquivos:
        print(f"Nenhum arquivo encontrado para {MES:02d}/{ANO}.")
        print("Provavel que o mes ainda nao foi publicado (SIH atrasa 2-4 meses).")
        print("Edite ANO/MES no topo deste arquivo para um mes fechado e rode de novo.")
        sys.exit(1)

    print(f"Encontrados {len(arquivos)} arquivo(s). Baixando e convertendo...")
    baixados = sih.download(arquivos)
    df = _to_df(baixados)

    if df.empty:
        print("ERRO: o download nao retornou linhas.")
        sys.exit(1)

    destino = RAW / "internacoes.parquet"
    df.to_parquet(destino, index=False)
    print(f"  ok: {destino} ({len(df):,} linhas)".replace(",", "."))
    print("\nAgora gere os dicionarios:")
    print("  uv run python gerar_dicionarios.py")


if __name__ == "__main__":
    main()
