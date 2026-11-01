"""
Etapa 1: ingestao (arquivos de data/raw/ -> schema bronze).

Le os arquivos brutos do SIH/SUS e grava cada um como uma tabela no schema
bronze do sih.duckdb. Regra da camada bronze: tudo entra como veio, todas as
colunas como texto (VARCHAR), campo vazio virando NULL. Nada de tipo nem de
limpeza aqui, isso e trabalho da transformacao.

Fontes esperadas em data/raw/ (veja README para como gerar com baixar_dados.py
e gerar_dicionarios.py):
    internacoes.parquet   microdados do SIH-RD (uma linha por internacao/AIH)
    cid10.csv             dicionario CID-10: codigo -> nome da doenca
    municipios.csv        dicionario IBGE: codigo -> municipio, UF

Os microdados vem do DATASUS convertidos de .dbc para parquet (pyreaddbc +
dbfread). Os dois dicionarios sao CSVs pequenos e estaveis (API do IBGE e
tabela CID-10 do DATASUS). O DuckDB le parquet e csv direto.

Idempotente: CREATE OR REPLACE TABLE, entao rodar de novo da o mesmo resultado.
Rodar com:
    uv run python -m pipeline.ingestao
"""
import sys
from pathlib import Path

from pipeline.db import conectar, criar_schema

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"

# arquivo em data/raw/ -> (tabela bronze, leitor duckdb)
# all_varchar=true garante a camada bronze para CSV; para o parquet, que carrega
# o proprio tipo, o CAST(COLUMNS(*) AS VARCHAR) forca toda coluna a texto. Sem
# ele, VAL_TOT entraria DOUBLE e IDADE BIGINT, quebrando a regra da bronze.
ARQUIVOS = {
    "internacoes.parquet": (
        "internacoes",
        "SELECT CAST(COLUMNS(*) AS VARCHAR) FROM read_parquet('{caminho}')",
    ),
    "cid10.csv": (
        "cid10",
        "SELECT * FROM read_csv_auto('{caminho}', all_varchar=true, encoding='utf-8')",
    ),
    "municipios.csv": (
        "municipios",
        "SELECT * FROM read_csv_auto('{caminho}', all_varchar=true, encoding='utf-8')",
    ),
}


def main():
    """Lê os arquivos de data/raw/ e grava cada um como tabela na bronze (texto)."""
    # Pre-requisito ANTES de conectar: os tres arquivos tem que existir. Se
    # faltar algum, o script nao pode nem criar um sih.duckdb vazio no disco
    # (ingestao parcial produz dashboard errado). Por isso a checagem vem antes
    # de conectar() e criar_schema().
    faltando = [arq for arq in ARQUIVOS if not (RAW / arq).exists()]
    if faltando:
        print("ERRO: faltam arquivos em data/raw/:")
        for arq in faltando:
            print(f"  - {arq}")
        print("Veja o README (secao 'Como baixar os dados') para gerar os arquivos.")
        sys.exit(1)

    con = conectar()
    criar_schema(con, "bronze")

    total = 0
    for arquivo, (tabela, leitor) in ARQUIVOS.items():
        caminho = (RAW / arquivo).as_posix()
        # os microdados entram como texto: o leitor de parquet ja aplica
        # CAST(COLUMNS(*) AS VARCHAR), o de CSV usa all_varchar=true.
        sql_fonte = leitor.format(caminho=caminho)
        con.execute(f"""
            CREATE OR REPLACE TABLE bronze.{tabela} AS
            SELECT * FROM ({sql_fonte})
        """)
        n = con.execute(f"SELECT count(*) FROM bronze.{tabela}").fetchone()[0]
        total += n
        print(f"  bronze.{tabela:<14} {n:>9,} registros".replace(",", "."))

    print(f"  {'total':<14} {total:>9,} registros".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
