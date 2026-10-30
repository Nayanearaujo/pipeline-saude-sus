"""
Conexao com o DuckDB do projeto e utilitarios de schema.

Unico lugar que sabe o nome do arquivo do banco. As etapas (ingestao,
transformacao, marts) pedem a conexao aqui e nunca abrem o arquivo por conta
propria. O banco mora na raiz do projeto, ao lado de pipeline/, sql/ e data/.
"""
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "sih.duckdb"


def conectar():
    """Abre o sih.duckdb na raiz do projeto, criando o arquivo se faltar."""
    return duckdb.connect(str(BANCO))


def criar_schema(con, nome):
    """CREATE SCHEMA IF NOT EXISTS <nome>."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")
