"""Testes dos graficos complementares com valores sinteticos."""

import pandas as pd

import painel


def test_mortalidade_usa_taxas_do_mart_sem_recalcular():
    df = pd.DataFrame({
        "cid": ["A00", "B00"], "doenca": ["Doença A", "Doença B"],
        "internacoes": [200, 150], "obitos": [25, 12],
        "taxa_mortalidade_pct": [12.5, 8.0],
        "posicao": [1, 2],
    })
    fig = painel.fig_mortalidade_por_cid(df)
    assert list(fig.data[0].x) == [12.5, 8.0]
    assert list(fig.data[0].y) == ["A00", "B00"]


def test_pareto_usa_percentuais_prontos_do_mart():
    df = pd.DataFrame({
        "cod_municipio": [2, 1], "municipio": ["B", "A"],
        "uf": ["RJ", "SP"], "internacoes": [30, 20],
        "valor_total": [1500.0, 1000.0],
        "posicao": [2, 1], "pct_acumulado": [55.0, 40.0],
    })
    fig = painel.fig_municipios_pareto(df)
    assert list(fig.data[0].x) == [1, 2]
    assert list(fig.data[0].y) == [40.0, 55.0]
