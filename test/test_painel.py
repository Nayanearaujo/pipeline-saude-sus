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


def test_lidera_descreve_o_maior_e_a_participacao():
    """lidera() le a 1a linha e a % pronta (pct_col), sem calcular."""
    # o mart ja vem ordenado e com a participacao pronta na coluna
    df = pd.DataFrame({
        "uf": ["SP", "MG", "RJ"],
        "internacoes": [50, 30, 20],
        "pct": [50.0, 30.0, 20.0],
    })
    frase = painel.lidera(df, "uf", "internacoes", "pct")
    assert frase == "SP lidera: 50 (50,0% do total)"


def test_lidera_sem_pct_mostra_so_o_valor():
    """Sem coluna de % pronta, lidera() nao inventa a conta: so o valor."""
    df = pd.DataFrame({"uf": ["SP", "MG"], "custo_medio": [2000.0, 1500.0]})
    assert painel.lidera(df, "uf", "custo_medio") == "SP lidera: 2.000"


def test_lidera_df_vazio_volta_string_vazia():
    df = pd.DataFrame({"uf": [], "internacoes": []})
    assert painel.lidera(df, "uf", "internacoes", "pct") == ""


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


def _diag_df(n):
    """DataFrame de diagnosticos no formato que o mart 03/06 entrega hoje:
    ja ordenado, com posicao e pct_do_total prontos."""
    return pd.DataFrame({
        "cid": [f"C{i:03d}" for i in range(n)],
        "doenca": [f"d{i}" for i in range(n)],
        "internacoes": list(range(n, 0, -1)),
        "valor_total": [i * 100.0 for i in range(n)],
        "pct_do_total": [100.0 / n] * n,
        "posicao": list(range(1, n + 1)),
    })


def test_top_diagnosticos_corta_em_dez():
    fig = painel.fig_top_diagnosticos(_diag_df(15), "Brasil")
    assert len(fig.data[0].y) == 10


def test_top_diagnosticos_nome_longo_cortado_no_eixo():
    """Nome longo e truncado no eixo (com reticencias), mas inteiro no hover."""
    nome_longo = "Doença com nome realmente muito comprido para o eixo caber"
    df = pd.DataFrame({
        "cid": ["X999"],
        "doenca": [nome_longo],
        "internacoes": [10],
        "valor_total": [1234.56],
        "pct_do_total": [100.0],
        "posicao": [1],
    })
    fig = painel.fig_top_diagnosticos(df, "Brasil")
    assert fig.data[0].y[0].endswith("…")                  # eixo truncado
    assert fig.data[0].customdata[0][0] == nome_longo      # hover completo


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


def test_periodo_serie_respeita_dados_e_nao_fixa_abril():
    serie = pd.DataFrame({"dia": ["2027-07-02", "2027-07-01"]})
    assert painel.periodo_serie(serie) == "julho/2027"


def test_periodo_serie_com_multiplos_meses_e_vazio():
    serie = pd.DataFrame({"dia": ["2027-02-01", "2026-12-31", None]})
    assert painel.periodo_serie(serie) == "dezembro/2026, fevereiro/2027"
    assert painel.periodo_serie(pd.DataFrame({"dia": []})) == "não informado"
