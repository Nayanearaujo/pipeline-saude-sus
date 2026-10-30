"""
Testes unitarios das funcoes puras de formato e dos graficos de painel.py.

Dado inventado, sem banco. O valor esperado sai da conta sobre a entrada, nunca
de um numero real do SIH.
"""
import duckdb
import pandas as pd
import pytest

import painel


# --- ler(): as duas fontes (duckdb local e CSV no deploy) ------------------
def test_ler_do_duckdb_quando_ha_banco(tmp_path):
    """Havendo sih.duckdb, ler() busca no schema ouro."""
    banco = tmp_path / "sih.duckdb"
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA ouro")
    con.execute("CREATE TABLE ouro.kpis_gerais AS SELECT 7 AS internacoes")
    con.close()
    dados = painel.ler(marts=["kpis_gerais"], banco=str(banco))
    assert int(dados["kpis_gerais"].iloc[0]["internacoes"]) == 7


def test_ler_do_csv_quando_nao_ha_banco(tmp_path, monkeypatch):
    """Sem banco, ler() cai no fallback: dados_painel/<mart>.csv (caso do deploy)."""
    pasta = tmp_path / "dados_painel"
    pasta.mkdir()
    (pasta / "kpis_gerais.csv").write_text("internacoes\n9\n", encoding="utf-8")
    # painel.ler() monta o caminho a partir da pasta do proprio modulo
    monkeypatch.setattr(painel, "__file__", str(tmp_path / "painel.py"))
    dados = painel.ler(marts=["kpis_gerais"], banco=str(tmp_path / "nao_existe.duckdb"))
    assert int(dados["kpis_gerais"].iloc[0]["internacoes"]) == 9


def test_ler_sem_banco_nem_csv_erro(tmp_path, monkeypatch):
    """Sem banco e sem CSV, ler() explica com FileNotFoundError."""
    monkeypatch.setattr(painel, "__file__", str(tmp_path / "painel.py"))
    with pytest.raises(FileNotFoundError):
        painel.ler(marts=["kpis_gerais"], banco=str(tmp_path / "nao_existe.duckdb"))


def test_reais_milhar_e_centavos():
    assert painel.reais(1003862.14) == "R$ 1.003.862,14"


def test_reais_valor_pequeno():
    assert painel.reais(137.42) == "R$ 137,42"


def test_numero_tem_separador_de_milhar():
    assert painel.numero(96470) == "96.470"


def test_numero_uma_casa():
    assert painel.numero(12.5, 1) == "12,5"


def test_pct_duas_casas():
    assert painel.pct(4.27, 2) == "4,27%"


def test_reais_curto_bilhoes_milhoes_mil():
    assert painel.reais_curto(2_259_000_000) == "R$ 2,26 bi"
    assert painel.reais_curto(5_400_000) == "R$ 5,40 mi"
    assert painel.reais_curto(3_200) == "R$ 3,2 mil"


def test_rotulo_traduz_metrica():
    assert painel.rotulo("internacoes") == "Internações"
    assert painel.rotulo("custo_medio") == "Custo médio"
    # metrica desconhecida volta ela mesma
    assert painel.rotulo("xyz") == "xyz"


def test_formato_nao_depende_de_locale():
    # milhar e decimal juntos, sem trocar um pelo outro
    assert painel.numero(1234.5, 1) == "1.234,5"


def test_ranking_estados_ordena_do_maior():
    df = pd.DataFrame({"uf": ["RJ", "SP", "MG"], "internacoes": [10, 30, 20]})
    fig = painel.fig_ranking_estados(df, "internacoes")
    # barra horizontal com y invertido: o maior (SP) fica em cima
    assert list(fig.data[0].x) == [30, 20, 10]


def test_top_diagnosticos_corta_em_dez():
    df = pd.DataFrame({
        "doenca": [f"d{i}" for i in range(15)],
        "internacoes": list(range(15, 0, -1)),
    })
    fig = painel.fig_top_diagnosticos(df, "Brasil")
    assert len(fig.data[0].y) == 10


def test_serie_diaria_um_ponto_por_dia():
    df = pd.DataFrame({"dia": ["2026-07-01", "2026-07-02"], "internacoes": [5, 8]})
    fig = painel.fig_serie_diaria(df, "RJ")
    assert len(fig.data[0].x) == 2


def test_rosca_regiao_uma_fatia_por_regiao():
    df = pd.DataFrame({
        "regiao": ["Sudeste", "Sul", "Nordeste"],
        "internacoes": [100, 50, 30],
    })
    fig = painel.fig_rosca_regiao(df, "internacoes")
    # uma fatia por regiao
    assert len(fig.data[0].labels) == 3
    # e um donut (tem buraco no meio)
    assert fig.data[0].hole > 0


def test_custo_medio_uf_ordena_do_maior():
    df = pd.DataFrame({
        "uf": ["RJ", "SP", "MG"],
        "custo_medio": [1000.0, 2000.0, 1500.0],
    })
    fig = painel.fig_custo_medio_uf(df)
    assert list(fig.data[0].x) == [2000.0, 1500.0, 1000.0]


def test_mapa_usa_a_coluna_da_metrica():
    df = pd.DataFrame({
        "uf": ["RJ", "SP"], "regiao": ["Sudeste", "Sudeste"],
        "internacoes": [10, 20],
    })
    fig = painel.fig_mapa(df, "internacoes")
    # o choropleth recebeu as 2 UFs
    assert len(fig.data[0].locations) == 2


def test_perfil_tem_duas_series_de_sexo():
    df = pd.DataFrame({
        "faixa_etaria": ["30-49", "30-49"],
        "sexo": ["Feminino", "Masculino"],
        "internacoes": [100, 80],
    })
    fig = painel.fig_perfil(df, "Brasil")
    # barras agrupadas: uma trace por sexo
    assert len(fig.data) == 2
