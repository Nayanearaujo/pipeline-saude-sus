"""Testes de pipeline/db.py. Banco novo em tmp_path, nunca o sih.duckdb real."""
import duckdb
import pandas as pd

from pipeline import db


def test_conectar_cria_arquivo_que_faltava(tmp_path, monkeypatch):
    alvo = tmp_path / "sih.duckdb"
    monkeypatch.setattr(db, "BANCO", alvo)
    assert not alvo.exists()
    con = db.conectar()
    con.close()
    assert alvo.exists()


def test_criar_schema_e_idempotente(tmp_path):
    con = duckdb.connect(str(tmp_path / "s.duckdb"))
    db.criar_schema(con, "prata")
    db.criar_schema(con, "prata")  # duas vezes sem erro
    achou = con.execute(
        "SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'prata'"
    ).fetchone()[0]
    con.close()
    assert achou == 1


def test_gravar_substitui_tabela_e_devolve_contagem(tmp_path):
    con = duckdb.connect(str(tmp_path / "s.duckdb"))
    df1 = pd.DataFrame({"codigo": ["1", "2", "3"]})
    df2 = pd.DataFrame({"codigo": ["10", "20"]})
    n1 = db.gravar(con, df1, "bronze", "amostra")
    n2 = db.gravar(con, df2, "bronze", "amostra")
    con.close()
    assert n1 == 3
    assert n2 == 2  # CREATE OR REPLACE substitui em vez de duplicar
