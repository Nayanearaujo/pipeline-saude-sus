"""
Testes de exportar_painel.py: a exportacao da camada ouro para CSVs.

Monta um sih.duckdb com um schema ouro minimo (dado inventado), aponta o script
para la e confere que cada mart vira um CSV em dados_painel/. Nunca toca no
banco real nem baixa nada.
"""
import errno
from pathlib import Path

import duckdb
import pandas as pd
import pytest

import exportar_painel


def _ouro_minimo(banco):
    """Cria um schema ouro com uma linha em cada mart esperado."""
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA ouro")
    for nome in exportar_painel.MARTS:
        con.execute(f"CREATE TABLE ouro.{nome} AS SELECT 1 AS a, 2 AS b")
    con.close()


def _preparar(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    destino = tmp_path / "dados_painel"
    _ouro_minimo(banco)
    monkeypatch.setattr(exportar_painel, "BANCO", banco)
    monkeypatch.setattr(exportar_painel, "DESTINO", destino)
    return banco, destino


def test_exporta_um_csv_por_mart(tmp_path, monkeypatch):
    _banco, destino = _preparar(tmp_path, monkeypatch)
    exportar_painel.main()
    for nome in exportar_painel.MARTS:
        arquivo = destino / f"{nome}.csv"
        assert arquivo.exists()
        # cabecalho + 1 linha de dado
        assert len(arquivo.read_text().strip().splitlines()) == 2


def test_sem_banco_encerra(tmp_path, monkeypatch):
    """Sem sih.duckdb, o script explica e encerra (nao escreve CSV vazio)."""
    monkeypatch.setattr(exportar_painel, "BANCO", tmp_path / "nao_existe.duckdb")
    monkeypatch.setattr(exportar_painel, "DESTINO", tmp_path / "dados_painel")
    with pytest.raises(SystemExit):
        exportar_painel.main()
    assert not (tmp_path / "dados_painel").exists()


def test_mart_ausente_nao_sobrescreve_csvs(tmp_path, monkeypatch):
    banco, destino = _preparar(tmp_path, monkeypatch)
    destino.mkdir()
    anterior = destino / "kpis_gerais.csv"
    anterior.write_text("versao,anterior\\n1,2\\n", encoding="utf-8")
    con = duckdb.connect(str(banco))
    con.execute("DROP TABLE ouro.municipios_pareto")
    con.close()
    with pytest.raises(duckdb.Error):
        exportar_painel.main()
    assert anterior.read_text(encoding="utf-8") == "versao,anterior\\n1,2\\n"
    assert not (destino / "por_estado.csv").exists()


def test_mart_vazio_nao_publica_csvs(tmp_path, monkeypatch):
    banco, destino = _preparar(tmp_path, monkeypatch)
    con = duckdb.connect(str(banco))
    con.execute("DELETE FROM ouro.municipios_pareto")
    con.close()
    with pytest.raises(ValueError, match="Mart vazio"):
        exportar_painel.main()
    assert not destino.exists()


@pytest.mark.parametrize("exportacao_anterior", [False, True])
def test_falta_de_espaco_preserva_csvs_e_limpa_temporarios(tmp_path, monkeypatch, exportacao_anterior):
    _banco, destino = _preparar(tmp_path, monkeypatch)
    if exportacao_anterior:
        exportar_painel.main()
    anteriores = {p.name: p.read_bytes() for p in destino.glob("*.csv")}
    original = pd.DataFrame.to_csv

    def falha_no_ultimo_csv(df, caminho, *args, **kwargs):
        caminho = Path(caminho)
        assert caminho.parent.parent == destino.parent
        if caminho.name == "municipios_pareto.csv":
            caminho.write_text("parcial", encoding="utf-8")
            raise OSError(errno.ENOSPC, "Sem espaco em disco")
        return original(df, caminho, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", falha_no_ultimo_csv)
    with pytest.raises(OSError) as erro:
        exportar_painel.main()
    assert erro.value.errno == errno.ENOSPC
    assert {p.name: p.read_bytes() for p in destino.glob("*.csv")} == anteriores
    assert not list(destino.parent.glob("marts-export-*"))


@pytest.mark.parametrize("anterior", [False, True])
def test_falha_no_replace_reverte_todos_os_csvs(tmp_path, monkeypatch, anterior):
    _banco, destino = _preparar(tmp_path, monkeypatch)
    if anterior:
        exportar_painel.main()
    anteriores = {p.name: p.read_bytes() for p in destino.glob("*.csv")}
    original = Path.replace
    chamadas = 0

    def falha_na_publicacao(self, target):
        nonlocal chamadas
        if Path(target).parent == destino:
            chamadas += 1
            if chamadas == 5:
                raise OSError(errno.EIO, "Falha simulada ao publicar")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", falha_na_publicacao)
    with pytest.raises(OSError, match="Falha simulada"):
        exportar_painel.main()
    assert {p.name: p.read_bytes() for p in destino.glob("*.csv")} == anteriores
    assert not list(destino.parent.glob("marts-export-*"))
