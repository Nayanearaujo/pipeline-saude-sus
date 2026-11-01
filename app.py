"""Dashboard executivo do SIH/SUS. Indicadores lidos dos marts, sem novas agregacoes."""
import logging
from html import escape

import streamlit as st

import painel

st.set_page_config(page_title="SUS · Painel executivo", layout="wide", page_icon="◈")
PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False}

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      :root {
        --sus-ink: #142337; --sus-muted: #617084; --sus-line: #e2e8ef;
        --sus-accent: #117d76; --sus-paper: #f4f6f9;
      }
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: var(--sus-paper);
      }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 1440px; padding: 2.5rem 2.4rem 2rem; }
      html, body, [data-testid="stAppViewContainer"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--sus-ink);
      }
      .sus-header {
        display: flex; justify-content: space-between; align-items: center; gap: 28px;
        background: linear-gradient(110deg, #112338, #173a48);
        border-radius: 18px; padding: 30px 34px; margin-bottom: 12px;
        color: #fff; position: relative; overflow: hidden;
      }
      .sus-header::after {
        content: ""; position: absolute; right: -70px; top: -130px;
        width: 330px; height: 330px; border: 1px solid #ffffff10;
        border-radius: 50%; pointer-events: none;
      }
      .sus-eyebrow { color: #a4d8d2; font-size: 11px; letter-spacing: .17em; font-weight: 700; }
      .sus-header h1 {
        color: #fff; font-family: Inter, sans-serif; font-size: clamp(25px, 2.6vw, 37px);
        font-weight: 700; letter-spacing: -.045em; line-height: 1.2;
        padding: 10px 0 8px; margin: 0;
      }
      .sus-header p { color: #c2d0da; font-size: 13px; margin: 0; line-height: 1.6; }
      .sus-header a { color: #d2eae6; text-underline-offset: 3px; }
      .sus-periodo {
        flex-shrink: 0; text-align: right; padding-left: 26px; border-left: 1px solid #ffffff26;
        position: relative; z-index: 1;
      }
      .sus-periodo span { display: block; font-size: 11px; color: #b5c9d2; margin-bottom: 6px; }
      .sus-periodo strong { font-size: 17px; color: #fff; font-weight: 600; }
      [data-testid="stSelectbox"] label p { font-size: 12px; color: var(--sus-muted); font-weight: 600; }
      div[data-baseweb="select"] > div {
        background: #fff; border: 1px solid #dce3eb; border-radius: 9px; min-height: 44px;
      }
      div[data-baseweb="select"] > div:focus-within { border-color: var(--sus-accent); }
      .sus-context { display: flex; align-items: baseline; gap: 12px; margin: 16px 0 13px; flex-wrap: wrap; }
      .sus-context h2 { margin: 0; padding: 0; font-size: 18px; font-weight: 650; letter-spacing: -.025em; }
      .sus-context span { color: var(--sus-muted); font-size: 12px; }
      .sus-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }
      .sus-card {
        background: #fff; border: 1px solid var(--sus-line); border-radius: 12px;
        padding: 20px 18px 17px; min-width: 0; position: relative;
        box-shadow: 0 3px 10px #14233704;
      }
      .sus-card:first-child { border-top: 3px solid var(--sus-accent); padding-top: 18px; }
      .sus-card-number { position: absolute; right: 16px; top: 14px; color: #a2aebb; font-size: 10px; }
      .sus-card-rot {
        color: #52647a; font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
      }
      .sus-card-val {
        color: var(--sus-ink); font-size: clamp(22px, 2.15vw, 30px); font-weight: 700;
        font-variant-numeric: tabular-nums; letter-spacing: -.055em; line-height: 1.3;
        margin: 12px 0 8px; white-space: nowrap;
      }
      .sus-card:first-child .sus-card-val { color: #106c65; }
      .sus-card-sub { color: var(--sus-muted); font-size: 11px; line-height: 1.5; }
      [data-baseweb="tab-list"] { gap: 25px; border-bottom: 1px solid var(--sus-line); margin-bottom: 14px; }
      button[data-baseweb="tab"] { color: var(--sus-muted); padding: 10px 0 15px; }
      button[data-baseweb="tab"] p { font-size: 13px; font-weight: 600; }
      button[data-baseweb="tab"][aria-selected="true"] { color: #106c65; }
      [data-baseweb="tab-highlight"] { background: var(--sus-accent); height: 3px; }
      [data-testid="stPlotlyChart"] {
        background: #fff; border: 1px solid var(--sus-line); border-radius: 12px;
        padding: 7px 9px; overflow: hidden;
      }
      .sus-section { padding: 5px 0 12px; }
      .sus-section h3 {
        color: var(--sus-ink); font-size: 17px; font-weight: 650;
        letter-spacing: -.025em; margin: 0 0 5px; padding: 0;
      }
      .sus-section p { color: var(--sus-muted); font-size: 12px; margin: 0; line-height: 1.6; }
      [data-testid="stExpander"] { background: #fff; border-radius: 10px; margin-top: 20px; }
      .stCaption, [data-testid="stCaptionContainer"] { color: var(--sus-muted); }
      hr { border-color: var(--sus-line); margin: 18px 0; }
      @media (max-width: 1050px) {
        .sus-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .sus-card:last-child { grid-column: 1 / -1; }
        .sus-card-val { font-size: 28px; }
      }
      @media (max-width: 640px) {
        .block-container { padding: 2rem 1rem 1rem; }
        .sus-header { flex-direction: column; align-items: flex-start; padding: 24px; gap: 18px; }
        .sus-periodo { text-align: left; border-left: 0; padding: 0; }
        .sus-header h1 { font-size: 27px; }
        .sus-kpis { grid-template-columns: 1fr; }
        .sus-card:last-child { grid-column: auto; }
        .sus-card { padding: 18px 20px; }
        .sus-card-val { margin: 8px 0; }
        [data-baseweb="tab-list"] { gap: 17px; }
        button[data-baseweb="tab"] p { font-size: 12px; }
      }
      @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def carregar():
    return painel.ler()


def _card_html(rotulo: str, valor: str, nota: str = "", indice: str = "") -> str:
    """Cartao apenas de apresentacao; valores ja calculados nos marts."""
    return (
        "<div class='sus-card'>"
        f"<span class='sus-card-number' aria-hidden='true'>{escape(indice)}</span>"
        f"<div class='sus-card-rot'>{escape(rotulo)}</div>"
        f"<div class='sus-card-val'>{escape(valor)}</div>"
        f"<div class='sus-card-sub'>{escape(nota)}</div></div>"
    )


def _secao(titulo: str, descricao: str):
    st.markdown(
        f'<div class="sus-section"><h3>{escape(titulo)}</h3><p>{escape(descricao)}</p></div>',
        unsafe_allow_html=True,
    )


def _plotar(fig, altura: int = 420):
    """Tema executivo aplicado somente na tela; nao modifica os dados da figura."""
    fig.update_layout(
        template="plotly_white", height=altura,
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#52647a"),
        title_font=dict(family="Inter, Arial, sans-serif", size=15, color="#142337"),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        hoverlabel=dict(bgcolor="#142337", font_color="#ffffff", font_size=12),
        legend=dict(font=dict(size=11)),
    )
    fig.update_xaxes(tickfont=dict(size=11), gridcolor="#eef2f6", zeroline=False)
    fig.update_yaxes(tickfont=dict(size=11), gridcolor="#eef2f6", zeroline=False)
    regioes = {
        "Sudeste": "#153e50", "Nordeste": "#1a8078", "Sul": "#6baa9f",
        "Norte": "#b4ccc7", "Centro-Oeste": "#94a5b8",
    }
    for trace in fig.data:
        cor = getattr(getattr(trace, "marker", None), "color", None)
        if isinstance(cor, str) and cor == painel.COR:
            trace.marker.color = "#18877d"
        if trace.type == "pie":
            trace.marker.colors = [regioes.get(str(label), "#94a5b8") for label in trace.labels]
            trace.insidetextfont.color = [
                "#ffffff" if str(label) in {"Sudeste", "Nordeste"} else "#142337"
                for label in trace.labels
            ]
        if trace.type == "choropleth":
            fig.update_coloraxes(colorscale=[
                [0, "#edf5f4"], [.2, "#c8e5df"], [.5, "#68b6a6"], [1, "#11645f"],
            ])
        if hasattr(trace, "line") and trace.line.color == painel.COR:
            trace.line.color = "#18877d"
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def main():
    try:
        dados = carregar()
    except Exception:  # noqa: BLE001
        logging.exception("Falha ao ler os marts")
        st.error("Não foi possível carregar os indicadores. Tente atualizar os dados ou consultar a fonte.")
        st.stop()

    faltando = [m for m in painel.MARTS if m not in dados or dados[m].empty]
    if faltando:
        st.error("Alguns indicadores estão indisponíveis: " + ", ".join(faltando))
        st.stop()

    periodo = painel.periodo_serie(dados["internacoes_diarias_brasil"])
    st.markdown(
        f"""
        <header class="sus-header">
          <div>
            <div class="sus-eyebrow">SIH / SUS · PAINEL EXECUTIVO</div>
            <h1>Internações hospitalares</h1>
            <p>Volume, valores registrados e perfil assistencial por residência.<br>
            Fonte: <a href="https://datasus.saude.gov.br/transferencia-de-arquivos/"
            target="_blank" rel="noopener noreferrer">SIH/SUS · DATASUS</a></p>
          </div>
          <div class="sus-periodo"><span>Série de entradas</span><strong>{escape(periodo)}</strong></div>
        </header>
        """,
        unsafe_allow_html=True,
    )

    por_estado = dados["por_estado"]
    ufs = sorted(por_estado["uf"].dropna().unique())
    col_estado, col_metrica = st.columns([1, 1])
    with col_estado:
        escolha = st.selectbox("Estado", ["Brasil"] + ufs)
    with col_metrica:
        metrica = st.selectbox(
            "Métrica do mapa e ranking",
            ["internacoes", "valor_total", "custo_medio", "dias_medio", "taxa_mortalidade_pct"],
            format_func=painel.rotulo,
        )
    uf = None if escolha == "Brasil" else escolha
    rotulo = uf or "Brasil"
    k = dados["kpis_gerais"].iloc[0] if uf is None else por_estado.loc[por_estado["uf"] == uf].iloc[0]
    st.markdown(
        f'<div class="sus-context"><h2>Resumo · {escape(rotulo)}</h2>'
        '<span>Consolidado por competência · uma linha representa uma AIH</span></div>',
        unsafe_allow_html=True,
    )
    cartoes = "".join([
        _card_html("Internações", painel.numero(k["internacoes"]), "AIHs no recorte selecionado", "01"),
        _card_html("Valor total", painel.reais_curto(k["valor_total"]), painel.reais(k["valor_total"]), "02"),
        _card_html("Valor médio / AIH", painel.reais(k["custo_medio"], 0), "Valor médio registrado", "03"),
        _card_html("Permanência média", painel.numero(k["dias_medio"], 1) + " dias", "Por internação", "04"),
        _card_html("Mortalidade", painel.pct(k["taxa_mortalidade_pct"], 2), "Óbitos durante a internação", "05"),
    ])
    st.markdown(f"<div class='sus-kpis'>{cartoes}</div>", unsafe_allow_html=True)

    territorio, perfil_tab, complementares_tab = st.tabs([
        "Visão territorial", "Perfil assistencial", "Análises complementares",
    ])
    with territorio:
        _secao("Distribuição territorial", "Visão nacional para comparar as UFs de residência, em qualquer seleção.")
        mapa, ranking = st.columns([1.1, 1])
        with mapa:
            _plotar(painel.fig_mapa(por_estado, metrica), 620)
        with ranking:
            _plotar(painel.fig_ranking_estados(por_estado, metrica), 620)
        regioes, custos = st.columns(2)
        with regioes:
            _plotar(painel.fig_rosca_regiao(por_estado, metrica), 480)
        with custos:
            _plotar(painel.fig_custo_medio_uf(por_estado), 620)

    with perfil_tab:
        _secao(
            f"Perfil assistencial · {rotulo}",
            "Diagnósticos, entradas diárias e perfil demográfico do recorte selecionado.",
        )
        if uf is None:
            diag = dados["top_diagnosticos_brasil"]
            serie = dados["internacoes_diarias_brasil"]
            perfil = dados["perfil_demografico_brasil"]
        else:
            diag = dados["top_diagnosticos"].loc[dados["top_diagnosticos"]["uf"] == uf]
            serie = dados["internacoes_diarias"].loc[dados["internacoes_diarias"]["uf"] == uf]
            perfil = dados["perfil_demografico"].loc[dados["perfil_demografico"]["uf"] == uf]
        diagnosticos, entradas = st.columns(2)
        with diagnosticos:
            _plotar(painel.fig_top_diagnosticos(diag, rotulo), 480)
        with entradas:
            _plotar(painel.fig_serie_diaria(serie, rotulo), 480)
        _plotar(painel.fig_perfil(perfil, rotulo), 420)
        st.caption("A série diária usa a data de entrada; seu total pode diferir do consolidado por competência.")

    with complementares_tab:
        _secao(
            "Mortalidade e concentração · Brasil",
            "Escopo nacional. Estes dois gráficos não acompanham o filtro de estado.",
        )
        try:
            complementares = painel.ler(marts=["mortalidade_por_cid", "municipios_pareto"])
        except (FileNotFoundError, OSError) as erro:
            logging.info("Marts complementares indisponiveis: %s", erro)
            st.info("Análises complementares temporariamente indisponíveis.")
        else:
            mortalidade, concentracao = st.columns(2)
            with mortalidade:
                _plotar(painel.fig_mortalidade_por_cid(complementares["mortalidade_por_cid"]), 480)
            with concentracao:
                _plotar(painel.fig_municipios_pareto(complementares["municipios_pareto"]), 480)
            st.caption(
                "Mortalidade por CID considera grupos com pelo menos 100 AIHs; "
                "a concentração mostra os 30 primeiros municípios."
            )

    with st.expander("Notas de leitura e fonte"):
        st.markdown(
            "- Uma AIH é um registro de internação, não uma pessoa única.\n"
            "- Valores registrados não representam o custo econômico integral da assistência.\n"
            "- Mortalidade hospitalar não é mortalidade populacional nem comparação ajustada por risco.\n"
            "- UF e município correspondem à residência, não necessariamente ao local de atendimento.\n"
            "- O período da série diária não substitui a competência dos arquivos de origem."
        )
    st.divider()
    fonte, atualizar = st.columns([4, 1])
    with fonte:
        st.caption("SIH/SUS · DATASUS | Dados públicos · Indicadores agregados por AIH")
    with atualizar:
        if st.button("Atualizar dados", icon=":material/refresh:", width="stretch"):
            st.cache_data.clear()
            st.rerun()


if __name__ == "__main__":
    main()
