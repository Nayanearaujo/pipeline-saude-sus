"""
app.py: dashboard interativo das internacoes do SUS, por estado.

So arruma na tela o que painel.py entrega; nao calcula nada. Rodar com:
    uv run streamlit run app.py

Interacao: um seletor de estado no topo. "Brasil" mostra a visao nacional
(cartoes do mart kpis_gerais, mapa, rankings). Ao escolher uma UF, os cartoes
passam a ler a linha daquela UF no mart por_estado, e os graficos de
diagnostico, serie diaria e perfil recortam para o estado. Os valores por UF
ja vem prontos do mart: a tela so escolhe a linha, nao recalcula.
"""
import logging

import streamlit as st

import painel

st.set_page_config(page_title="SUS · internações por estado", layout="wide", page_icon="🏥")

# Esconde a barra de ferramentas do plotly (camera, zoom, etc.): visual mais
# limpo e profissional. Desliga tambem o menuzinho "produced with plotly".
PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False}

# Visual: cards com borda arredondada e sombra, fundo suave, margens.
st.markdown(
    """
    <style>
      /* fonte elegante para o titulo (Poppins) e corpo (Inter) */
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

      /* fundo verde-bebe na pagina inteira (reforca o config.toml;
         cobre os seletores que mudam entre versoes do Streamlit) */
      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      .main,
      section.main { background: #eaf7f0 !important; }
      [data-testid="stHeader"] { background: transparent !important; }
      .block-container { padding-top: 2.4rem; padding-bottom: 2.4rem; max-width: 1280px; }

      /* corpo em Inter; titulo em Poppins, verde escuro e encorpado */
      html, body, [class*="st-"] { font-family: 'Inter', system-ui, sans-serif; }
      h1 {
        font-family: 'Poppins', sans-serif !important;
        color: #14543f; font-weight: 800; letter-spacing: -0.5px;
        font-size: 2.3rem;
      }
      .stCaption, [data-testid="stCaptionContainer"] { color: #5a6b66; }

      /* cartoes de metrica: brancos, cantos suaves, sombra leve e borda verde */
      div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dbeee4;
        border-top: 3px solid #5bb6a6;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 1px 2px rgba(20,84,63,.04), 0 10px 30px -22px rgba(20,84,63,.45);
        transition: box-shadow .2s ease, transform .2s ease;
      }
      div[data-testid="stMetric"]:hover {
        box-shadow: 0 2px 4px rgba(20,84,63,.06), 0 14px 34px -20px rgba(20,84,63,.5);
        transform: translateY(-1px);
      }
      /* rotulo do cartao em maiusculas discretas: ar executivo */
      div[data-testid="stMetricLabel"] {
        color: #6b7b7c; font-size: 0.74rem; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase;
      }
      div[data-testid="stMetricValue"] { color: #14543f; font-weight: 800; }

      /* graficos num cartao branco, mesma linguagem dos cartoes */
      div[data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #dbeee4;
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 1px 2px rgba(20,84,63,.04), 0 10px 30px -22px rgba(20,84,63,.45);
      }

      /* seletores (selectbox) em destaque: fundo branco, borda verde mais
         marcada e sombra, para a area de escolha "saltar" do fundo verde */
      div[data-baseweb="select"] > div {
        background: #ffffff; border-radius: 12px;
        border: 1.5px solid #5bb6a6 !important;
        box-shadow: 0 6px 18px -12px rgba(20,84,63,.5);
        min-height: 46px;
      }
      div[data-baseweb="select"] > div:hover { border-color: #2e9e74 !important; }
      /* caixa que agrupa cada seletor, com um respiro */
      div[data-testid="stSelectbox"] { margin-bottom: 4px; }
      /* rotulo proprio acima de cada seletor: negrito verde, bolinha verde */
      .sus-label {
        font-weight: 700; color: #14543f; font-size: 1rem;
        margin: 0 0 4px 2px;
      }
      .sus-label::first-letter { color: #5bb6a6; }

      /* rotulos dos seletores (Estado, Metrica...): negrito verde, um pouco
         maiores, com uma bolinha verde antes para chamar a atencao */
      div[data-testid="stWidgetLabel"] label,
      div[data-testid="stWidgetLabel"] p,
      label[data-testid="stWidgetLabel"] {
        font-weight: 700 !important; color: #14543f !important;
        font-size: 0.98rem !important;
      }
      div[data-testid="stWidgetLabel"] p::before {
        content: "● "; color: #5bb6a6;
      }

      /* cabecalho (banner): faixa branca levemente esverdeada, titulo Poppins */
      .sus-header {
        background: linear-gradient(135deg, #ffffff 0%, #f0faf5 100%);
        border: 1px solid #d3ebe0; border-left: 6px solid #2e9e74;
        border-radius: 16px; padding: 22px 26px; margin-bottom: 18px;
        box-shadow: 0 10px 30px -22px rgba(20,84,63,.5);
      }
      .sus-title {
        font-family: 'Poppins', sans-serif; font-weight: 800;
        font-size: 2.15rem; line-height: 1.15; color: #14543f;
        letter-spacing: -0.5px;
      }
      .sus-title span { color: #2e9e74; font-weight: 700; }
      /* linha da fonte: discreta, com o link do DATASUS bem visivel */
      .sus-fonte { color: #5a6b66; font-size: 0.92rem; margin-top: 8px; }
      .sus-fonte a {
        color: #1a6b52 !important; font-weight: 700;
        text-decoration: underline; text-underline-offset: 3px;
      }
      .sus-fonte a:hover { color: #2e9e74 !important; }

      /* subtitulo de secao: etiqueta verde, com um tracinho antes */
      .sus-sub {
        color: #14543f; font-size: 1.1rem; font-weight: 700;
        margin: 10px 0 6px; padding-left: 12px; border-left: 4px solid #5bb6a6;
      }
      /* divisor mais discreto */
      hr { border-color: #cfe6da !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def carregar():
    return painel.ler()


def main():
    # Cabecalho como um bloco HTML proprio: banner verde com o titulo em Poppins
    # e a fonte do dado como link para o DATASUS. Controlado 100% aqui, sem
    # depender dos componentes do Streamlit (que sanitizam parte do CSS).
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@700;800&display=swap" rel="stylesheet">
        <div class="sus-header">
          <div class="sus-title">🏥 Internações hospitalares do SUS <span>· por estado</span></div>
          <div class="sus-fonte">
            Fonte:
            <a href="https://datasus.saude.gov.br/transferencia-de-arquivos/" target="_blank">SIH/SUS · DATASUS</a>
            · abril/2026 · uma linha = uma internação (AIH).
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        dados = carregar()
    except Exception:  # noqa: BLE001
        # Mensagem amigavel na tela; o detalhe tecnico vai para o log do
        # servidor, nao para o usuario (evita vazar caminho/stack na UI).
        logging.exception("Falha ao ler os marts do sih.duckdb")
        st.error(
            "Não consegui carregar os dados do painel. "
            "Se você está rodando localmente, gere os marts antes com "
            "`uv run python -m pipeline.marts`."
        )
        st.stop()

    faltando = [m for m in painel.MARTS if m not in dados or dados[m].empty]
    if faltando:
        st.error("Faltam marts: " + ", ".join(faltando) + "\n\nRode: `uv run python -m pipeline.marts`")
        st.stop()

    por_estado = dados["por_estado"]
    ufs = sorted(por_estado["uf"].dropna().unique())

    col_sel, col_met = st.columns([1, 1])
    with col_sel:
        st.markdown("<div class='sus-label'>● Estado</div>", unsafe_allow_html=True)
        escolha = st.selectbox(
            "Estado", ["Brasil"] + ufs, index=0, label_visibility="collapsed"
        )
    with col_met:
        st.markdown(
            "<div class='sus-label'>● Métrica do mapa e ranking</div>",
            unsafe_allow_html=True,
        )
        opcoes = ["internacoes", "valor_total", "custo_medio", "dias_medio", "taxa_mortalidade_pct"]
        metrica = st.selectbox(
            "Métrica do mapa e ranking",
            opcoes,
            index=0,
            format_func=painel.rotulo,  # mostra "Internações", guarda "internacoes"
            label_visibility="collapsed",
        )

    uf = None if escolha == "Brasil" else escolha

    # ---- Cartoes: Brasil le kpis_gerais; UF le a linha do mart por_estado ----
    if uf is None:
        k = dados["kpis_gerais"].iloc[0]
        internacoes, valor, custo = k["internacoes"], k["valor_total"], k["custo_medio"]
        dias, mort = k["dias_medio"], k["taxa_mortalidade_pct"]
    else:
        linha = por_estado[por_estado["uf"] == uf].iloc[0]
        internacoes, valor, custo = linha["internacoes"], linha["valor_total"], linha["custo_medio"]
        dias, mort = linha["dias_medio"], linha["taxa_mortalidade_pct"]

    c = st.columns(5)
    c[0].metric("Internações", painel.numero(internacoes))
    c[1].metric("Gasto total", painel.reais_curto(valor))      # R$ 2,26 bi, cabe no card
    c[2].metric("Custo médio", painel.reais(custo, 0))          # R$ 1.824, sem centavos
    c[3].metric("Permanência média", painel.numero(dias, 1) + " dias")
    c[4].metric("Mortalidade", painel.pct(mort, 2))

    st.divider()

    # ---- Faixa nacional: mapa + ranking (sempre Brasil, para comparar) -------
    st.markdown('<div class="sus-sub">Visão nacional</div>', unsafe_allow_html=True)
    f1 = st.columns([3, 2])
    with f1[0]:
        st.plotly_chart(painel.fig_mapa(por_estado, metrica), width="stretch", config=PLOTLY_CONFIG)
    with f1[1]:
        st.plotly_chart(painel.fig_ranking_estados(por_estado, metrica), width="stretch", config=PLOTLY_CONFIG)

    # mapa + rosca (o circulo classico) lado a lado com o custo por UF
    f1b = st.columns([2, 3])
    with f1b[0]:
        st.plotly_chart(painel.fig_rosca_regiao(por_estado, metrica), width="stretch", config=PLOTLY_CONFIG)
    with f1b[1]:
        st.plotly_chart(painel.fig_custo_medio_uf(por_estado), width="stretch", config=PLOTLY_CONFIG)

    st.divider()

    # ---- Faixa recortada pelo estado escolhido -------------------------------
    # Brasil le os marts nacionais; uma UF filtra a linha dos marts por estado.
    rotulo = uf if uf else "Brasil"
    if uf is None:
        diag = dados["top_diagnosticos_brasil"]
        serie = dados["internacoes_diarias_brasil"]
        perfil = dados["perfil_demografico_brasil"]
    else:
        diag = dados["top_diagnosticos"][dados["top_diagnosticos"]["uf"] == uf]
        serie = dados["internacoes_diarias"][dados["internacoes_diarias"]["uf"] == uf]
        perfil = dados["perfil_demografico"][dados["perfil_demografico"]["uf"] == uf]

    st.markdown(f'<div class="sus-sub">Detalhe · {rotulo}</div>', unsafe_allow_html=True)
    f2 = st.columns(2)
    with f2[0]:
        st.plotly_chart(painel.fig_top_diagnosticos(diag, rotulo), width="stretch", config=PLOTLY_CONFIG)
    with f2[1]:
        st.plotly_chart(painel.fig_serie_diaria(serie, rotulo), width="stretch", config=PLOTLY_CONFIG)

    st.plotly_chart(painel.fig_perfil(perfil, rotulo), width="stretch", config=PLOTLY_CONFIG)


if __name__ == "__main__":
    main()
