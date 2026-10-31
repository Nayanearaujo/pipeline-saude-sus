"""
Gera um relatorio estatico em HTML (relatorio.html) a partir da camada ouro.

Lê os marts pelo painel.py, monta os cartoes executivos e os mesmos graficos do
dashboard Streamlit, e grava uma pagina unica e offline. Util para publicar no
GitHub Pages e para quem nao quer rodar o Streamlit. Zero calculo novo: todo
numero sai de um mart; os graficos sao os mesmos do painel.

    uv run python relatorio.py

Gera relatorio.html na raiz e uma copia em docs/ (para o GitHub Pages servir ao
lado do index.html). Rode depois do pipeline (pipeline.marts) ou com os CSVs de
dados_painel/ ja presentes.
"""
import sys
from datetime import datetime
from pathlib import Path

import painel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent

# Metrica padrao do mapa/ranking/rosca na visao nacional do relatorio.
METRICA = "internacoes"


def _card(rotulo: str, valor: str, nota: str = "") -> str:
    """Monta o HTML de um cartao executivo (rotulo, valor grande, nota)."""
    sub = f'<div class="nota">{nota}</div>' if nota else ""
    return (
        f'<div class="kpi"><div class="rot">{rotulo}</div>'
        f'<div class="val">{valor}</div>{sub}</div>'
    )


def _grafico(fig, incluir_js: bool, div_id: str, largo: bool = False) -> str:
    """Converte uma figura Plotly em um bloco HTML (card branco).

    largo=True ocupa a linha inteira da grade (bom para serie e perfil); por
    padrao cada grafico ocupa metade (grade de 2 colunas). div_id fixo deixa o
    HTML deterministico: sem ele o Plotly sorteia um id a cada execucao e o
    arquivo muda mesmo com o dado igual."""
    # a altura vem do CSS (.grafico height:380px); o grafico preenche o card.
    # autosize + responsive deixam o Plotly acompanhar a largura da coluna da grade.
    fig.update_layout(autosize=True)
    html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if incluir_js else False,
        config={"displayModeBar": False, "displaylogo": False, "responsive": True},
        default_height="100%",
        default_width="100%",
        div_id=div_id,
    )
    classe = "grafico largo" if largo else "grafico"
    return f'<div class="{classe}">{html}</div>'


def construir_html(dados: dict) -> str:
    """Monta a pagina inteira: cabecalho, cartoes, graficos e rodape."""
    k = dados["kpis_gerais"].iloc[0]
    por_estado = dados["por_estado"]
    diag = dados["top_diagnosticos_brasil"]
    serie = dados["internacoes_diarias_brasil"]
    perfil = dados["perfil_demografico_brasil"]

    cards = "".join([
        _card("Internações (abril/2026)", painel.numero(k["internacoes"])),
        _card("Gasto total", painel.reais_curto(k["valor_total"])),
        _card("Custo médio", painel.reais(k["custo_medio"], 0), "por internação"),
        _card("Permanência média", painel.numero(k["dias_medio"], 1) + " dias"),
        _card("Mortalidade hospitalar", painel.pct(k["taxa_mortalidade_pct"], 2)),
    ])

    # o mapa centralizado e sem margem lateral sobrando (o Brasil e estreito e
    # alto; sem isso sobra muito branco dos lados no relatorio).
    mapa = painel.fig_mapa(por_estado, METRICA)
    mapa.update_geos(fitbounds="locations", visible=False)
    mapa.update_layout(margin=dict(l=0, r=0, t=56, b=0))

    # grade de 2 colunas: mapa + ranking no topo; rosca + custo; top diagnosticos
    # emparelhado; serie e perfil ocupam a linha inteira (sao series temporais).
    blocos = [
        (mapa, False),
        (painel.fig_ranking_estados(por_estado, METRICA), False),
        (painel.fig_rosca_regiao(por_estado, METRICA), False),
        (painel.fig_custo_medio_uf(por_estado), False),
        (painel.fig_top_diagnosticos(diag, "Brasil"), False),
        (painel.fig_perfil(perfil, "Brasil"), False),
        (painel.fig_serie_diaria(serie, "Brasil"), True),
    ]
    graficos = "".join(
        _grafico(f, incluir_js=(i == 0), div_id=f"g{i:02d}", largo=largo)
        for i, (f, largo) in enumerate(blocos)
    )

    gerado = datetime.now().strftime("%d/%m/%Y às %H:%M")
    return _PAGINA.format(cards=cards, graficos=graficos, gerado=gerado)


def main():
    """Lê os marts, monta o HTML e grava relatorio.html na raiz e em docs/."""
    dados = painel.ler()
    html = construir_html(dados)

    destinos = [RAIZ / "relatorio.html", RAIZ / "docs" / "relatorio.html"]
    for destino in destinos:
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(html, encoding="utf-8")
        print(f"  ok: {destino.relative_to(RAIZ)}")
    print("\nPronto. Abra relatorio.html no navegador ou publique docs/ no GitHub Pages.")


# Template da pagina. Paleta e cara alinhadas ao docs/index.html (verde-agua).
_PAGINA = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório · Internações do SUS (abril/2026)</title>
<style>
  :root{{--paper:#eef3f1;--surface:#fff;--ink:#10171a;--ink-3:#6b7b7c;
    --line:#d6e0db;--accent:#1a6b52;
    --shadow:0 1px 2px rgba(16,23,26,.05),0 10px 30px -20px rgba(16,23,26,.4);}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--paper);color:var(--ink);
    font-family:"Segoe UI",system-ui,-apple-system,sans-serif;line-height:1.6;}}
  .wrap{{max-width:1100px;margin:0 auto;padding:28px 18px 56px;}}
  .banner{{background:linear-gradient(135deg,#1a6b52,#2e9e74);color:#fff;
    border-radius:16px;padding:28px 26px;box-shadow:var(--shadow);margin-bottom:22px;}}
  .banner h1{{margin:0 0 6px;font-size:clamp(22px,4vw,30px);}}
  .banner p{{margin:3px 0;opacity:.95;font-size:14.5px;}}
  .banner a{{color:#dff3ea;}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
    gap:12px;margin:0 0 20px;}}
  .kpi{{background:var(--surface);border:1px solid var(--line);border-radius:14px;
    padding:16px;box-shadow:var(--shadow);}}
  .kpi .rot{{font-size:12px;color:var(--ink-3);}}
  .kpi .val{{font-size:23px;font-weight:700;margin-top:4px;}}
  .kpi .nota{{font-size:11.5px;color:var(--ink-3);margin-top:2px;}}
  .grade{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;}}
  .grafico{{background:var(--surface);border:1px solid var(--line);
    border-radius:14px;padding:8px;box-shadow:var(--shadow);
    min-width:0;height:380px;}}
  .grafico .plotly-graph-div{{width:100%!important;height:100%!important;}}
  .grafico.largo{{grid-column:1 / -1;}}
  @media (max-width:900px){{.grade{{grid-template-columns:1fr;}}}}
  footer{{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);
    font-size:13px;color:var(--ink-3);text-align:center;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner">
    <h1>🏥 Internações hospitalares do SUS · abril/2026</h1>
    <p>Relatório executivo gerado da camada ouro · uma linha = uma internação (AIH)</p>
    <p>Fonte: SIH/SUS (DATASUS) ·
       <a href="https://github.com/Nayanearaujo/pipeline-saude-sus">repositório</a> ·
       <a href="https://pipeline-saude-sus.streamlit.app/">dashboard interativo</a></p>
  </div>
  <div class="kpis">{cards}</div>
  <div class="grade">{graficos}</div>
  <footer>
    Nayane Araujo · Desafio Final — Engenharia de Dados · dados públicos do SIH/SUS.<br>
    A série diária é por data de entrada e não soma o total (que é por competência).
    Números lidos direto dos marts, sem cálculo na página.<br>
    Relatório gerado em {gerado}.
  </footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
