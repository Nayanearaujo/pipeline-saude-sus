"""
Testes de relatorio.py: o gerador do relatorio HTML estatico.

Monta um dict de marts inventado (no formato que painel.ler() devolveria) e
chama construir_html direto, sem banco e sem rede. Confere que os cartoes
aparecem no HTML, que os ids dos graficos sao fixos (deterministico) e que
rodar duas vezes muda so a data do rodape.
"""
import pandas as pd

import relatorio


def _dados_inventados():
    """Os marts que construir_html le, com poucas linhas e numeros conhecidos."""
    return {
        "kpis_gerais": pd.DataFrame([{
            "internacoes": 100, "valor_total": 2_260_000_000.0,
            "custo_medio": 1824.0, "dias_medio": 4.8, "taxa_mortalidade_pct": 4.1,
        }]),
        "por_estado": pd.DataFrame({
            "uf": ["SP", "RJ"], "regiao": ["Sudeste", "Sudeste"],
            "internacoes": [60, 40], "valor_total": [1200.0, 800.0],
            "custo_medio": [20.0, 20.0], "dias_medio": [4.0, 5.0],
            "taxa_mortalidade_pct": [4.0, 5.0],
            "pct_internacoes": [60.0, 40.0], "pct_valor": [60.0, 40.0],
        }),
        "top_diagnosticos_brasil": pd.DataFrame({
            "cid": ["O800"], "doenca": ["Parto espontâneo"],
            "internacoes": [50], "valor_total": [500.0],
            "pct_do_total": [50.0], "posicao": [1],
        }),
        "internacoes_diarias_brasil": pd.DataFrame({
            "dia": ["2026-04-01", "2026-04-02"], "internacoes": [30, 20],
            "valor_total": [300.0, 200.0],
        }),
        "perfil_demografico_brasil": pd.DataFrame({
            "faixa_etaria": ["30-49", "30-49"], "sexo": ["Feminino", "Masculino"],
            "internacoes": [60, 40], "dias_medio": [3.6, 5.6],
        }),
    }


def test_html_tem_os_cartoes():
    """O HTML gerado contem o rotulo e o valor de cada cartao executivo."""
    html = relatorio.construir_html(_dados_inventados())
    assert "Internações" in html
    assert "Gasto total" in html
    assert "Mortalidade hospitalar" in html
    # o valor do KPI de internacoes aparece formatado em padrao BR
    assert "100" in html


def test_ids_de_grafico_sao_fixos():
    """Os graficos usam div_id g00, g01... (HTML deterministico, nao aleatorio)."""
    html = relatorio.construir_html(_dados_inventados())
    assert 'id="g00"' in html
    assert 'id="g01"' in html


def test_rodar_duas_vezes_muda_so_a_data(monkeypatch):
    """Sem contar o rodape de data, duas geracoes dao o mesmo HTML."""
    dados = _dados_inventados()

    # congela a data para a 1a geracao
    class _Fixa:
        @staticmethod
        def now():
            import datetime as _dt
            return _dt.datetime(2026, 1, 1, 10, 0)

    monkeypatch.setattr(relatorio, "datetime", _Fixa)
    um = relatorio.construir_html(dados)
    dois = relatorio.construir_html(dados)
    assert um == dois  # mesma data congelada -> HTML identico
