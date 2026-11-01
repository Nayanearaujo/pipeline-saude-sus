"""Testes dos graficos complementares com valores sinteticos."""

import pandas as pd
import pytest

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


def test_ler_lista_vazia_nao_abre_banco(tmp_path):
    assert painel.ler(marts=[], banco=str(tmp_path / "inexistente.duckdb")) == {}


def test_ler_rejeita_nome_de_mart_invalido(tmp_path):
    with pytest.raises(ValueError, match="Marts não reconhecidos"):
        painel.ler(
            marts=["kpis_gerais; DROP TABLE ouro.kpis_gerais"],
            banco=str(tmp_path / "inexistente.duckdb"),
        )


def test_ler_informa_csv_complementar_ausente(tmp_path, monkeypatch):
    # Força o caminho CSV e usa o diretório padrão do painel, sem modificar arquivos.
    monkeypatch.setattr(painel, "__file__", str(tmp_path / "painel.py"))
    with pytest.raises(FileNotFoundError, match="mortalidade_por_cid"):
        painel.ler(
            marts=["mortalidade_por_cid", "municipios_pareto"],
            banco=str(tmp_path / "inexistente.duckdb"),
        )
