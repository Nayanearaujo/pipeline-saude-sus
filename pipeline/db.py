"""
Conexao com o DuckDB do projeto e utilitarios de schema e carga.

Unico lugar que sabe o nome do arquivo do banco. As etapas (ingestao,
transformacao, marts) pedem a conexao aqui e nunca abrem o arquivo por conta
propria. O banco mora na raiz do projeto, ao lado de pipeline/, sql/ e data/.
"""
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "sih.duckdb"
PASTA_RAW = RAIZ / "data" / "raw"


def conectar():
    """Abre o sih.duckdb na raiz do projeto, criando o arquivo se faltar."""
    return duckdb.connect(str(BANCO))


def criar_schema(con, nome):
    """CREATE SCHEMA IF NOT EXISTS <nome>."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")


def gravar(con, df, schema: str, tabela: str) -> int:
    """Grava o DataFrame em <schema>.<tabela> com CREATE OR REPLACE TABLE.

    Devolve o total de linhas gravadas lido direto do banco com SELECT count(*).
    """
    criar_schema(con, schema)
    con.register("_df_carga", df)
    try:
        con.execute(f"CREATE OR REPLACE TABLE {schema}.{tabela} AS SELECT * FROM _df_carga")
    finally:
        con.unregister("_df_carga")
    return con.execute(f"SELECT count(*) FROM {schema}.{tabela}").fetchone()[0]
