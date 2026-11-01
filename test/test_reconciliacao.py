"""Testes de regressao da reconciliacao entre bronze e prata."""

import duckdb

from pipeline import transformacao
from test.test_transformacao import _preparar


def test_exclusoes_por_valor_e_aih_duplicada(tmp_path, monkeypatch):
    """Uma AIH duplicada e uma linha sem valor nao podem inflar a prata."""
    banco = _preparar(tmp_path, monkeypatch)
    con = duckdb.connect(str(banco))
    con.execute("INSERT INTO bronze.internacoes SELECT * FROM bronze.internacoes WHERE N_AIH = 'a1'")
    origem = con.execute("SELECT count(*) FROM bronze.internacoes").fetchone()[0]
    con.close()

    transformacao.main()

    con = duckdb.connect(str(banco))
    destino, chaves = con.execute(
        "SELECT count(*), count(DISTINCT aih) FROM prata.internacoes"
    ).fetchone()
    con.close()

    assert origem == 6
    assert destino == chaves == 4
    assert origem - destino == 2
