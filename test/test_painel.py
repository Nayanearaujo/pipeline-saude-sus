"""
Testes unitarios das funcoes puras de formato e dos graficos de painel.py.

Dado inventado, sem banco. O valor esperado sai da conta sobre a entrada, nunca
de um numero real do SIH.
"""
import pandas as pd

import painel


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
