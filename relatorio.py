"""
Gera um relatorio estatico em HTML (relatorio.html) a partir da camada ouro.

Le os marts pelo painel.py, monta os cartoes executivos e os mesmos graficos do
dashboard Streamlit, e grava uma pagina unica estatica (sem servidor Python).
Util para publicar no GitHub Pages e abrir direto no navegador. Zero calculo
novo: todo numero sai de um mart; os graficos sao os mesmos do painel.

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


def _mapa_svg(fig, div_id: str, incluir_js: bool) -> str:
    """Mapa vetorial do relatório: enquadra toda a geometria sem câmera/WebGL."""
    from html import escape
    from math import log, pi, radians, tan

    from plotly.colors import sample_colorscale
    from plotly.offline import get_plotlyjs_version

    trace = fig.data[0]
    valores = dict(zip(trace.locations, trace.z, strict=True))
    escala = [list(par) for par in fig.layout.coloraxis.colorscale]
    minimo, maximo = min(valores.values()), max(valores.values())
    altura = fig.layout.height or 694

    def projetar(ponto):
        longitude, latitude = ponto[:2]
        return radians(longitude), -log(tan(pi / 4 + radians(latitude) / 2))

    formas = []
    pontos = []
    for feature in trace.geojson["features"]:
        geometria = feature["geometry"]
        poligonos = geometria["coordinates"]
        if geometria["type"] == "Polygon":
            poligonos = [poligonos]
        aneis = [[projetar(p) for p in anel] for poligono in poligonos for anel in poligono]
        formas.append((feature["properties"]["sigla"], aneis))
        pontos.extend(p for anel in aneis for p in anel)
    xs, ys = zip(*pontos, strict=True)
    oeste, leste, norte, sul = min(xs), max(xs), min(ys), max(ys)
    largura_util, altura_util = 370, altura - 145
    escala_xy = min(largura_util / (leste - oeste), altura_util / (sul - norte))
    desloc_x = 18 + (largura_util - (leste - oeste) * escala_xy) / 2
    desloc_y = 95 + (altura_util - (sul - norte) * escala_xy) / 2
    paths = []
    for uf, aneis in formas:
        valor = valores.get(uf)
        cor = "#edf2f0"
        detalhe = "sem dados"
        if valor is not None:
            fracao = (valor - minimo) / (maximo - minimo) if maximo != minimo else 0.5
            cor = sample_colorscale(escala, [fracao])[0]
            detalhe = painel.numero(valor) + " internações"
        d = " ".join(
            "M" + " L".join(f"{desloc_x + (x - oeste) * escala_xy:.2f},"
                            f"{desloc_y + (y - norte) * escala_xy:.2f}" for x, y in anel) + " Z"
            for anel in aneis
        )
        paths.append(f'<path d="{d}" fill="{cor}" stroke="white" stroke-width="0.7" '
                     f'fill-rule="evenodd"><title>{escape(uf)}: {detalhe}</title></path>')
    stops = "".join(f'<stop offset="{p * 100}%" stop-color="{cor}"/>' for p, cor in escala)
    topo, base = 180, altura - 115
    ticks = "".join(
        f'<text x="440" y="{base - (base - topo) * i / 4:.1f}" dominant-baseline="middle">'
        f'{painel.numero(minimo + (maximo - minimo) * i / 4)}</text>' for i in range(5)
    )
    titulo, _, subtitulo = fig.layout.title.text.partition("<br>")
    subtitulo = subtitulo.replace("<sub>", "").replace("</sub>", "")
    script = (f'<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" '
              'charset="utf-8"></script>') if incluir_js else ""
    return (
        f'<div class="grafico">{script}<svg id="{div_id}" class="mapa-relatorio" '
        f'viewBox="0 0 520 {altura}" role="img" aria-labelledby="{div_id}-titulo" '
        f'style="display:block;width:100%;height:{altura}px" preserveAspectRatio="xMidYMid meet">'
        f'<title id="{div_id}-titulo">Mapa completo das 27 UFs: internações por estado de residência</title>'
        f'<defs><linearGradient id="{div_id}-escala" x1="0" y1="1" x2="0" y2="0">{stops}'
        '</linearGradient></defs><g font-family="Arial,sans-serif" fill="#39474a" font-size="12">'
        f'<text x="12" y="26" font-size="16" fill="#10171a">{escape(titulo)}</text>'
        f'<text x="12" y="48" font-size="11">{escape(subtitulo)}</text>'
        + "".join(paths)
        + f'<text x="418" y="{topo - 15}" font-size="13">Internações</text>'
        f'<rect x="420" y="{topo}" width="12" height="{base - topo}" fill="url(#{div_id}-escala)"/>'
        + ticks + '</g></svg></div>'
    )


def _grafico(fig, incluir_js: bool, div_id: str, largo: bool = False) -> str:
    """Converte uma figura Plotly em um bloco HTML (card branco).

    largo=True ocupa a linha inteira da grade (bom para serie e perfil); por
    padrao cada grafico ocupa metade (grade de 2 colunas). div_id fixo deixa o
    HTML deterministico: sem ele o Plotly sorteia um id a cada execucao e o
    arquivo muda mesmo com o dado igual."""
    if fig.data and fig.data[0].type == "choroplethmap":
        return _mapa_svg(fig, div_id, incluir_js)
    # Uma única altura em pixels: o cartão cresce com o conteúdo, sem regras
    # percentuais que deixavam o canvas ultrapassar o padding e a borda.
    altura = max(380, fig.layout.height or 380)
    fig.update_layout(autosize=True, width=None, height=altura)
    html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if incluir_js else False,
        config={"displayModeBar": False, "displaylogo": False, "responsive": True},
        default_height=altura,
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
        _card("Internações (competência)", painel.numero(k["internacoes"])),
        _card("Gasto total", painel.reais_curto(k["valor_total"])),
        _card("Custo médio", painel.reais(k["custo_medio"], 0), "por internação"),
        _card("Permanência média", painel.numero(k["dias_medio"], 1) + " dias"),
        _card("Mortalidade hospitalar", painel.pct(k["taxa_mortalidade_pct"], 2)),
    ])

    # o mapa centralizado e sem margem lateral sobrando (o Brasil e estreito e
    # alto; sem isso sobra muito branco dos lados no relatorio).
    mapa = painel.fig_mapa(por_estado, METRICA)
    limites = mapa.layout.map.bounds
    mapa.update_layout(
        margin=dict(l=15, r=105, t=64, b=20),
        map_bounds=dict(west=limites.west - 2, east=limites.east + 2,
                        south=limites.south - 2, north=limites.north + 2),
    )

    # grade de 2 colunas: mapa + ranking no topo; rosca + custo; top diagnosticos
    # emparelhado; serie e perfil ocupam a linha inteira (sao series temporais).
    blocos = [
        (mapa, False),
        (painel.fig_ranking_estados(por_estado, METRICA), False),
        (painel.fig_rosca_regiao(por_estado, METRICA), False),
        (painel.fig_custo_medio_uf(por_estado), False),
        (painel.fig_top_diagnosticos(diag, "Brasil"), True),
        (painel.fig_perfil(perfil, "Brasil"), True),
        (painel.fig_serie_diaria(serie, "Brasil"), True),
    ]
    # Os pares compartilham a altura, evitando vazios abaixo do mapa e da rosca.
    for esquerda, direita in ((0, 1), (2, 3)):
        altura = max(blocos[esquerda][0].layout.height or 380,
                     blocos[direita][0].layout.height or 380)
        blocos[esquerda][0].update_layout(height=altura)
        blocos[direita][0].update_layout(height=altura)
    if "mortalidade_por_cid" in dados and "municipios_pareto" in dados:
        blocos.extend([
            (painel.fig_mortalidade_por_cid(dados["mortalidade_por_cid"]), True),
            (painel.fig_municipios_pareto(dados["municipios_pareto"]), True),
        ])
    graficos = "".join(
        _grafico(f, incluir_js=(i == 0), div_id=f"g{i:02d}", largo=largo)
        + (
            '<p class="leitura">CID: Classificação Internacional de Doenças. '
            'AIH: Autorização de Internação Hospitalar. Taxa: proporção de internações com óbito '
            'no diagnóstico, entre grupos com pelo menos 100 AIHs; não é mortalidade populacional '
            'nem comparação ajustada por gravidade.</p>' if i == 7 else
            '<p class="leitura">Municípios de residência ordenados do maior para o menor valor. '
            'O eixo horizontal indica a posição; o vertical, o percentual do valor total acumulado '
            'até aquela posição. A linha de 80% é uma referência de concentração, não uma meta '
            'de qualidade. Os botões mostram todos os municípios ou os primeiros 30.</p>' if i == 8 else ''
        )
        for i, (f, largo) in enumerate(blocos)
    )

    gerado = datetime.now().strftime("%d/%m/%Y às %H:%M")
    return _PAGINA.format(
        cards=cards, graficos=graficos, gerado=gerado,
        periodo_serie=painel.periodo_serie(serie),
    )


def main():
    """Lê os marts, monta o HTML e grava relatorio.html na raiz e em docs/."""
    dados = painel.ler(marts=[*painel.MARTS, "mortalidade_por_cid", "municipios_pareto"])
    html = construir_html(dados)

    destinos = [RAIZ / "relatorio.html", RAIZ / "docs" / "relatorio.html"]
    for destino in destinos:
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(html, encoding="utf-8")
        tamanho_kb = destino.stat().st_size / 1024
        kb_fmt = f"{tamanho_kb:.1f}".replace(".", ",")
        print(f"  ok: {destino.relative_to(RAIZ)} ({kb_fmt} KB)")
    print("\nPronto. Abra relatorio.html no navegador ou publique docs/ no GitHub Pages.")


# Template da pagina. Paleta e cara alinhadas ao docs/index.html (verde-agua).
_PAGINA = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório · Internações do SUS</title>
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
  .secao{{margin:30px 0 15px;}}
  .secao h2{{font-size:21px;letter-spacing:-.02em;margin:0 0 6px;}}
  .secao p{{margin:0;color:#526364;font-size:14px;}}
  .notas{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:18px;}}
  .nota-card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;}}
  .nota-card h3{{font-size:15px;margin:0 0 8px;}}
  .nota-card p{{font-size:13px;color:#46575a;margin:0;}}
  .grade{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;}}
  .grafico{{background:var(--surface);border:1px solid var(--line);
    border-radius:14px;padding:8px;box-shadow:var(--shadow);
    min-width:0;overflow:hidden;}}
  .grafico .plotly-graph-div{{width:100%;}}
  .grafico.largo{{grid-column:1 / -1;}}
  .leitura{{grid-column:1 / -1;margin:0;color:#46575a;font-size:13px;}}
  @media (max-width:900px){{.grade,.notas{{grid-template-columns:1fr;}}}}
  footer{{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);
    font-size:13px;color:var(--ink-3);text-align:center;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner">
    <h1>🏥 Internações hospitalares do SUS · por competência</h1>
    <p>Relatório executivo gerado da camada ouro · uma linha = uma internação (AIH)</p>
    <p>Série diária: {periodo_serie}</p>
    <p>Fonte: SIH/SUS (DATASUS) ·
       <a href="https://github.com/Nayanearaujo/pipeline-saude-sus">repositório</a> ·
       <a href="https://pipeline-saude-sus.streamlit.app/">dashboard interativo</a></p>
  </div>
  <div class="kpis">{cards}</div>
  <section class="secao" aria-labelledby="leitura">
    <h2 id="leitura">O retrato das internações</h2>
    <p>
Distribuição territorial, perfil das AIHs, diagnósticos e evolução das admissões. Explore os
gráficos para investigar padrões, sem confundir associação com causalidade.</p>

  </section>
  <div class="grade">{graficos}</div>
  <section class="secao" aria-labelledby="metodologia">
    <h2 id="metodologia">Como interpretar os resultados</h2>
    <p>
Transparência metodológica é parte do resultado. Estes indicadores têm denominadores, períodos e
unidades de análise específicos.</p>

  </section>
  <div class="notas">
    <article class="nota-card">
<h3>
Competência não é data de entrada</h3>
<p>
Os indicadores consolidados seguem a competência dos arquivos de origem. A série diária
exibe {periodo_serie}, conforme o recorte do mart. Esse mês não comprova a competência de
processamento, e os totais da série não precisam coincidir com os indicadores consolidados.</p>
</article>

    <article class="nota-card">
<h3>
AIH não representa paciente único</h3>
<p>
Uma autorização de internação hospitalar (AIH) é o registro analisado. Não interprete a contagem
como número de pessoas distintas ou prevalência populacional.</p>
</article>

    <article class="nota-card">
<h3>
Valores pagos, não custos assistenciais</h3>
<p>
O valor total representa o valor registrado na AIH. O indicador monetário não mede o custo econômico
integral da assistência.</p>
</article>

    <article class="nota-card">
<h3>
Óbitos hospitalares, não mortalidade populacional</h3>
<p>
A taxa hospitalar usa óbitos registrados nas AIHs como numerador e internações como denominador. Não
mede o risco de morte na população geral.</p>
</article>

    <article class="nota-card">
<h3>
Geografia de residência</h3>
<p>
A distribuição por UF e município se refere à residência registrada, não necessariamente ao local de
atendimento. Comparações entre regiões não são taxas ajustadas por população.</p>
</article>

    <article class="nota-card">
<h3>
Limites e reprodutibilidade</h3>
<p>
Os números são lidos dos marts da camada ouro, sem reconciliação artificial. Consulte o código SQL e
as verificações de qualidade no repositório para rastrear as regras de cálculo.</p>
</article>

  </div>
  <footer>
    Nayane Araújo · Desafio Final — Engenharia de Dados · dados públicos do SIH/SUS.<br>
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
