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
    # internacoes.parquet com 2 linhas
    pd.DataFrame({
        "N_AIH": ["a1", "a2"],
        "MUNIC_RES": ["330455", "355030"],
        "VAL_TOT": ["1000.00", "500.00"],
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


def test_arquivo_faltando_encerra(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    (tmp_path / "raw" / "cid10.csv").unlink()
    with pytest.raises(SystemExit):
        ingestao.main()
