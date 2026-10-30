"""
Testes de pipeline/ingestao.py.

Escreve um parquet e dois CSVs pequenos em tmp_path, aponta o pipeline para la e
confere que viram tabelas bronze como texto. Nunca le data/raw/ nem o banco real.
"""
import duckdb
import pandas as pd
import pytest

from pipeline import db, ingestao


def _montar_raw(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    # internacoes.parquet com 2 linhas. VAL_TOT e IDADE entram como numericos
    # de proposito: a bronze tem que forcar tudo a texto mesmo assim (o parquet
    # carrega o tipo; o CAST(COLUMNS(*) AS VARCHAR) da ingestao desfaz isso).
    pd.DataFrame({
        "N_AIH": ["a1", "a2"],
        "MUNIC_RES": ["330455", "355030"],
        "VAL_TOT": [1000.00, 500.00],
        "IDADE": [40, 30],
    }).to_parquet(raw / "internacoes.parquet")
    (raw / "cid10.csv").write_text("codigo,descricao\nA001,Colera\n", encoding="utf-8")
    (raw / "municipios.csv").write_text("codigo,municipio,uf\n330455,Rio,RJ\n", encoding="utf-8")
    monkeypatch.setattr(ingestao, "RAW", raw)
    monkeypatch.setattr(db, "BANCO", tmp_path / "sih.duckdb")


def test_arquivos_viram_tabelas_bronze(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    ingestao.main()
    con = duckdb.connect(str(tmp_path / "sih.duckdb"))
    n = con.execute("SELECT count(*) FROM bronze.internacoes").fetchone()[0]
    m = con.execute("SELECT count(*) FROM bronze.cid10").fetchone()[0]
    con.close()
    assert n == 2
    assert m == 1


def test_bronze_e_tudo_texto(tmp_path, monkeypatch):
    """Regra da bronze: toda coluna como VARCHAR, inclusive vinda do parquet.

    VAL_TOT e IDADE sao numericos no parquet de origem; na bronze tem que
    virar VARCHAR. Este teste falha se o CAST(COLUMNS(*) AS VARCHAR) sumir."""
    _montar_raw(tmp_path, monkeypatch)
    ingestao.main()
    con = duckdb.connect(str(tmp_path / "sih.duckdb"))
    tipos = {r[0]: r[1] for r in con.execute("DESCRIBE bronze.internacoes").fetchall()}
    con.close()
    assert tipos["VAL_TOT"] == "VARCHAR"
    assert tipos["IDADE"] == "VARCHAR"
    assert set(tipos.values()) == {"VARCHAR"}


def test_arquivo_faltando_encerra(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    (tmp_path / "raw" / "cid10.csv").unlink()
    with pytest.raises(SystemExit):
        ingestao.main()
