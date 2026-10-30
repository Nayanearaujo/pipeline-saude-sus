"""Testes de pipeline/db.py. Banco novo em tmp_path, nunca o sih.duckdb real."""
import duckdb

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
