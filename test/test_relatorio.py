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
        "mortalidade_por_cid": pd.DataFrame({
            "cid": ["A00"], "doenca": ["Diagnóstico de teste"], "internacoes": [200],
            "obitos": [20], "taxa_mortalidade_pct": [10.0], "posicao": [1],
        }),
        "municipios_pareto": pd.DataFrame({
            "municipio": ["Município de teste"], "uf": ["SP"], "internacoes": [100],
            "valor_total": [1000.0], "posicao": [1], "pct_acumulado": [100.0],
        }),
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
    assert 'id="g08"' in html
    assert "referência de concentração" in html
    assert 'height:820px' in html


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


def test_main_grava_os_dois_arquivos(tmp_path, monkeypatch):
    """main() le os marts, monta o HTML e grava relatorio.html na raiz e em docs/."""
    monkeypatch.setattr(relatorio.painel, "ler", lambda **kwargs: _dados_inventados())
    monkeypatch.setattr(relatorio, "RAIZ", tmp_path)
    relatorio.main()
    raiz_html = tmp_path / "relatorio.html"
    docs_html = tmp_path / "docs" / "relatorio.html"
    assert raiz_html.exists()
    assert docs_html.exists()
    assert "Internações" in raiz_html.read_text(encoding="utf-8")


def test_relatorio_explicita_limites_metodologicos():
    """A leitura responsável dos indicadores deve estar no HTML publicado."""
    html = relatorio.construir_html(_dados_inventados())
    assert "Como interpretar os resultados" in html
    assert "Competência não é data de entrada" in html
    assert "AIH não representa paciente único" in html
    assert "Óbitos hospitalares, não mortalidade populacional" in html
    assert "Valores pagos, não custos assistenciais" in html
    assert "Geografia de residência" in html
    assert "Limites e reprodutibilidade" in html


def test_relatorio_deriva_periodo_da_serie_sem_inferir_competencia():
    dados = _dados_inventados()
    dados["internacoes_diarias_brasil"]["dia"] = ["2027-07-01", "2027-07-02"]
    html = relatorio.construir_html(dados)
    assert "Série diária: julho/2027" in html
    assert "abril/2026" not in html
    assert "não comprova a competência" in html
