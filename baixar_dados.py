"""
Baixa os dados brutos do SIH/SUS e grava em data/raw/ no formato que a ingestao
espera. Roda na SUA maquina (precisa de internet e do PySUS).

    uv run python baixar_dados.py

O que faz:
1. Baixa os microdados do SIH-RD (internacoes) do mes/ano configurados, para
   todas as 27 UFs, converte de .dbc para um unico parquet em
   data/raw/internacoes.parquet.
2. Gera data/raw/cid10.csv e data/raw/municipios.csv a partir das tabelas de
   apoio do proprio PySUS (ou de um CSV do IBGE, ver observacao).

Ajuste ANO e MES abaixo. Se o mes ainda nao estiver publicado no DATASUS (o SIH
costuma ter 2-4 meses de atraso), o download avisa e voce usa um mes fechado.
"""
import sys
from pathlib import Path

ANO = 2026
MES = 7  # julho

RAW = Path(__file__).resolve().parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def baixar_internacoes():
    import pandas as pd
    from pysus.online_data.SIH import download

    print(f"Baixando SIH-RD {MES:02d}/{ANO} (todas as UFs)... pode demorar.")
    # grupo 'RD' = AIH reduzida (uma linha por internacao)
    arquivos = download(group="RD", states=None, years=ANO, months=MES)
    # PySUS devolve objeto(s) ParquetSet; to_dataframe() concatena
    if not isinstance(arquivos, list):
        arquivos = [arquivos]
    dfs = [a.to_dataframe() for a in arquivos]
    df = pd.concat(dfs, ignore_index=True)
    destino = RAW / "internacoes.parquet"
    df.to_parquet(destino, index=False)
    print(f"  ok: {destino} ({len(df):,} linhas)".replace(",", "."))


def gerar_dicionarios():
    """
    cid10.csv e municipios.csv sao tabelas de apoio estaveis.

    CID-10: o PySUS expoe via pysus.online_data.CID10, mas o jeito mais simples
    e robusto e baixar uma vez o CSV oficial do DATASUS/CID e salvar aqui. Se
    voce ja tem os arquivos, pule esta funcao.

    Municipios: a lista do IBGE (codigo de 6 ou 7 digitos, municipio, UF).
    """
    print(
        "Dicionarios: salve manualmente data/raw/cid10.csv (colunas: codigo,descricao)\n"
        "e data/raw/municipios.csv (colunas: codigo,municipio,uf).\n"
        "Veja o README, secao 'Como baixar os dados', para as fontes."
    )


if __name__ == "__main__":
    try:
        baixar_internacoes()
    except Exception as e:  # noqa: BLE001
        print(f"ERRO ao baixar internacoes: {e}")
        print("Se for mes nao publicado, ajuste ANO/MES no topo deste arquivo.")
        sys.exit(1)
    gerar_dicionarios()
