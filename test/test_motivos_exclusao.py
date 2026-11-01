"""Testa a classificacao exclusiva das exclusoes entre bronze e prata."""

import duckdb

from pipeline import transformacao
from test_transformacao import _preparar


def test_motivos_exclusao_sem_sobreposicao(tmp_path, monkeypatch, capsys):
    """Duplicata sem valor conta apenas como duplicata se nao for a AIH escolhida."""
    banco = _preparar(tmp_path, monkeypatch)
    con = duckdb.connect(str(banco))
    # a3 ja nao tem valor. A copia de a1 com valor vazio perde no desempate.
    con.execute("""
        INSERT INTO bronze.internacoes
        SELECT N_AIH, MUNIC_RES, DIAG_PRINC, PROC_REA, NULL, DIAS_PERM,
               IDADE, COD_IDADE, SEXO, MORTE, DT_INTER, '20260101'
        FROM bronze.internacoes WHERE N_AIH = 'a1'
    """)
    assert transformacao._motivos_exclusao_internacoes(con) == (1, 1)
    con.close()

    transformacao.main()
    saida = capsys.readouterr().out
    assert "exclusoes: 1 sem valor, 1 AIH duplicadas" in saida

    con = duckdb.connect(str(banco))
    assert con.execute("SELECT count(*) FROM prata.internacoes").fetchone()[0] == 4
    con.close()


def test_aih_com_todos_valores_vazios(tmp_path, monkeypatch):
    """Uma AIH com duas linhas sem valor gera uma duplicata e uma exclusao por valor."""
    banco = _preparar(tmp_path, monkeypatch)
    con = duckdb.connect(str(banco))
    con.execute("INSERT INTO bronze.internacoes SELECT * FROM bronze.internacoes WHERE N_AIH = 'a3'")
    assert transformacao._motivos_exclusao_internacoes(con) == (1, 1)
    con.close()
