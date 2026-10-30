"""
Painel do SIH/SUS: leitura dos marts, formatacao e graficos.

Spec (fonte da verdade; o codigo e consequencia dela):

1. LEITURA
   ler() devolve um dict nome -> DataFrame, rodando apenas SELECT * FROM
   ouro.<nome>. Nenhuma outra SQL. Conexao read_only=True, aberta e fechada
   dentro de ler(). Motivo: conexao aberta segura o arquivo e trava o pipeline.

2. NENHUM CALCULO
   Este modulo nao agrega (sem groupby/sum/mean/merge). So ordena, filtra linha,
   head(n) e formata. Numero novo na tela exige mart novo.

3. FORMATO
   reais/numero/pct sao funcoes puras (sem streamlit, sem banco): milhar com
   ponto, decimal com virgula, sempre, sem depender do locale da maquina.
   Uma funcao por grafico, recebendo DataFrame e devolvendo figura plotly.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# duckdb so e importado dentro de ler(), quando ha banco local. No deploy
# (Streamlit Cloud) o painel le CSVs e nao precisa do duckdb instalado.

BANCO = "sih.duckdb"

# GeoJSON dos estados do Brasil (sigla da UF em properties.sigla), usado no mapa.
GEOJSON_UF = (
    "https://raw.githubusercontent.com/codeforgermany/click_that_hood/"
    "main/public/data/brazil-states.geojson"
)

MARTS = [
    "kpis_gerais",
    "por_estado",
    "top_diagnosticos",
    "perfil_demografico",
    "internacoes_diarias",
    "top_diagnosticos_brasil",
    "internacoes_diarias_brasil",
    "perfil_demografico_brasil",
]

# Nome bonito (com acento) de cada metrica, para a tela e os titulos.
ROTULO_METRICA = {
    "internacoes": "Internações",
    "valor_total": "Gasto total",
    "custo_medio": "Custo médio",
    "dias_medio": "Permanência média",
    "taxa_mortalidade_pct": "Taxa de mortalidade",
}


def rotulo(metrica: str) -> str:
    """Devolve o nome legivel de uma metrica (ou ela mesma, se nao mapeada)."""
    return ROTULO_METRICA.get(metrica, metrica)

# Paleta suave: verde-agua claro como cor base, escala continua leve para o
# mapa (nao cansa a vista). Tons pastel, puxando do verde ao azul.
COR = "#5bb6a6"           # verde-agua medio, suave
ESCALA = "Teal"           # escala continua verde->azul suave para o mapa
# Paleta qualitativa (rosca, varias categorias): tons claros e harmonicos.
PALETA = ["#7fcbbd", "#9fd6c6", "#5bb6a6", "#cbe8df", "#f0c674", "#b7c4c0"]

# Cor por regiao na rosca: Sudeste no azul-bebe (o tom pedido), as demais em
# tons suaves que contrastam bem entre si.
COR_REGIAO = {
    "Sudeste": "#8fcfe0",         # azul-bebe
    "Nordeste": "#8fd4b8",        # verde claro
    "Sul": "#b6e0a8",             # verde-limao suave
    "Norte": "#f0c674",           # amarelo suave
    "Centro-Oeste": "#d9a8e0",    # lilas suave
}

# Cor por sexo: feminino em verde-bebe puxando ao azul; masculino em verde
# claro, menos escuro. Pedido para nao cansar a vista.
COR_SEXO = {
    "Feminino": "#8fcfe0",        # verde-agua/azul bebe
    "Masculino": "#8fd4b8",       # verde claro suave
    "nao informado": "#c9d3cf",
}


def _layout(fig, titulo: str):
    """Aplica um visual consistente a qualquer figura: titulo, fonte, margens.

    separators=',.' deixa todo numero no padrao BR (ponto de milhar, virgula
    decimal) tanto nos rotulos quanto no hover, sem depender do locale."""
    # o <sub> do subtitulo-resposta herda a fonte do titulo; css inline no texto
    # deixa ele menor e mais suave que o titulo principal.
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16, family="Arial", color="#10171a")),
        font=dict(family="Arial", size=13, color="#39474a"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=64, b=10),
        title_x=0.02,
        separators=",.",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef1ee", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef1ee", zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# 1. LEITURA
# ---------------------------------------------------------------------------
def ler(marts: list[str] | None = None, banco: str = BANCO) -> dict[str, pd.DataFrame]:
    """Le cada mart como DataFrame.

    Duas fontes, nesta ordem:
    1. o sih.duckdb (uso local, apos rodar o pipeline) -> le do schema ouro;
    2. a pasta dados_painel/ com os CSVs exportados (uso no deploy, onde nao ha
       banco) -> le de dados_painel/<mart>.csv.
    Assim o mesmo painel roda na maquina (banco completo) e no Streamlit Cloud
    (so a camada ouro, leve)."""
    from pathlib import Path

    nomes = marts if marts is not None else MARTS

    if Path(banco).exists():
        import duckdb  # importado so aqui: no deploy nao ha banco nem duckdb
        con = duckdb.connect(banco, read_only=True)
        try:
            return {nome: con.execute(f"SELECT * FROM ouro.{nome}").df() for nome in nomes}
        finally:
            con.close()

    # Fallback: CSVs da camada ouro (deploy).
    pasta = Path(__file__).resolve().parent / "dados_painel"
    if not (pasta / f"{nomes[0]}.csv").exists():
        raise FileNotFoundError(
            "Nem o sih.duckdb nem a pasta dados_painel/ foram encontrados. "
            "Rode o pipeline e depois 'uv run python exportar_painel.py'."
        )
    return {nome: pd.read_csv(pasta / f"{nome}.csv") for nome in nomes}


# ---------------------------------------------------------------------------
# 3. FORMATO (funcoes puras)
# ---------------------------------------------------------------------------
def _br(texto: str) -> str:
    """Troca os separadores para o padrao brasileiro sem depender do locale."""
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def reais(valor: float, casas: int = 2) -> str:
    """1003862.14 -> 'R$ 1.003.862,14'"""
    return "R$ " + _br(f"{valor:,.{casas}f}")


def reais_curto(valor: float) -> str:
    """Formato compacto para caber no cartao: 2259000000 -> 'R$ 2,26 bi'."""
    v = float(valor)
    if abs(v) >= 1_000_000_000:
        return "R$ " + _br(f"{v / 1_000_000_000:.2f}") + " bi"
    if abs(v) >= 1_000_000:
        return "R$ " + _br(f"{v / 1_000_000:.2f}") + " mi"
    if abs(v) >= 1_000:
        return "R$ " + _br(f"{v / 1_000:.1f}") + " mil"
    return "R$ " + _br(f"{v:.2f}")


def numero(valor: float, casas: int = 0) -> str:
    """96470 -> '96.470'"""
    return _br(f"{valor:,.{casas}f}")


def pct(valor: float, casas: int = 1) -> str:
    """4.3 -> '4,3%'"""
    return _br(f"{valor:,.{casas}f}") + "%"


def lidera(df: pd.DataFrame, rotulo_col: str, valor_col: str) -> str:
    """Frase-resposta do tipo 'SP lidera: 249.866 (20,2% do total)'.

    Nao agrega: le a maior linha de um DataFrame que ja veio somado do mart e
    descreve quem lidera e sua participacao. E apresentacao, nao calculo de
    negocio (a regra 'o painel nao agrega' continua valendo)."""
    if df.empty:
        return ""
    total = df[valor_col].sum()
    topo = df.loc[df[valor_col].idxmax()]
    parte = 100.0 * topo[valor_col] / total if total else 0.0
    return f"{topo[rotulo_col]} lidera: {numero(topo[valor_col])} ({pct(parte)} do total)"


# ---------------------------------------------------------------------------
# Graficos: uma funcao por grafico. Nenhuma agrega; o dado ja vem do mart.
# ---------------------------------------------------------------------------
def _barh(df: pd.DataFrame, x: str, y: str, titulo: str,
          hovertemplate: str | None = None) -> go.Figure:
    """Barras horizontais, maior em cima, com visual consistente.

    Numeros no padrao BR (ponto de milhar) via separators=',.'; hover opcional
    para um rotulo mais rico do que o padrao do plotly."""
    fig = px.bar(df, x=x, y=y, orientation="h", text=x)
    fig.update_traces(
        marker_color=COR,
        textposition="outside",
        texttemplate="%{text:,.0f}",
        textfont=dict(size=11, color="#39474a"),
        cliponaxis=False,
    )
    if hovertemplate is not None:
        fig.update_traces(hovertemplate=hovertemplate)
    fig = _layout(fig, titulo)
    # margem direita extra para o maior rotulo nao cortar; eixo x limpo.
    # separators=',.' faz o plotly usar '.' para milhar e ',' para decimal (BR).
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=70, t=52, b=10),
        separators=",.",
    )
    fig.update_xaxes(showticklabels=False, showgrid=False, title=None)
    fig.update_yaxes(title=None)
    return fig


def fig_mapa(por_estado: pd.DataFrame, metrica: str = "internacoes") -> go.Figure:
    """Mapa coropletico do Brasil por UF. O 'salta aos olhos' do painel.

    Hover em portugues (UF, regiao e a metrica formatada); a escala de cor e o
    titulo acompanham a metrica escolhida."""
    fig = px.choropleth(
        por_estado,
        geojson=GEOJSON_UF,
        locations="uf",
        featureidkey="properties.sigla",
        color=metrica,
        color_continuous_scale=ESCALA,
        scope="south america",
        custom_data=["uf", "regiao", metrica],
    )
    fig.update_geos(fitbounds="locations", visible=False)
    # hover: "SP · Sudeste" em negrito, e a metrica formatada em padrao BR
    fig.update_traces(
        marker_line_color="white", marker_line_width=0.6,
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
            f"{rotulo(metrica)}: " + "%{customdata[2]:,.0f}<extra></extra>"
        ),
    )
    # titulo que responde: quem lidera na metrica e com que participacao
    resposta = lidera(por_estado, "uf", metrica)
    titulo = f"{rotulo(metrica)} por estado<br><sub>{resposta}</sub>"
    fig = _layout(fig, titulo)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    fig.update_layout(
        coloraxis_colorbar_title_text=rotulo(metrica),
        separators=",.",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def fig_rosca_regiao(por_estado: pd.DataFrame, metrica: str = "internacoes") -> go.Figure:
    """Grafico de rosca (donut) com a participacao de cada regiao na metrica.
    O 'circulo classico': mostra como o total se divide entre as 5 regioes.
    Sudeste no azul-bebe (COR_REGIAO)."""
    fig = px.pie(
        por_estado, names="regiao", values=metrica, hole=0.55,
        color="regiao", color_discrete_map=COR_REGIAO,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      marker=dict(line=dict(color="white", width=2)))
    fig = _layout(fig, f"Participação por região · {rotulo(metrica).lower()}")
    fig.update_layout(showlegend=True)
    return fig


def fig_ranking_estados(por_estado: pd.DataFrame, metrica: str = "internacoes") -> go.Figure:
    """Ranking das UFs pela metrica escolhida, maior em cima."""
    df = por_estado.sort_values(metrica, ascending=False)
    resposta = lidera(por_estado, "uf", metrica)
    return _barh(df, x=metrica, y="uf",
                 titulo=f"Ranking de estados · {rotulo(metrica).lower()}<br><sub>{resposta}</sub>")


def fig_custo_medio_uf(por_estado: pd.DataFrame) -> go.Figure:
    """Custo medio por internacao em cada UF: mostra a desigualdade regional."""
    df = por_estado.sort_values("custo_medio", ascending=False)
    # resposta: o contraste entre o maior e o menor custo medio (desigualdade)
    resposta = ""
    if not df.empty:
        alto, baixo = df.iloc[0], df.iloc[-1]
        resposta = (f"{alto['uf']} ({reais(alto['custo_medio'], 0)}) custa "
                    f"{alto['custo_medio'] / baixo['custo_medio']:.1f}× o de "
                    f"{baixo['uf']} ({reais(baixo['custo_medio'], 0)})")
    return _barh(df, x="custo_medio", y="uf",
                 titulo=f"Custo médio por internação · por UF<br><sub>{resposta}</sub>")


# As tres funcoes de detalhe recebem o DataFrame ja no escopo certo: o app
# passa o mart nacional (para "Brasil") ou o mart por UF ja filtrado por linha
# (para um estado). Assim o painel nunca decide escopo nem agrega.
def fig_top_diagnosticos(df: pd.DataFrame, rotulo: str) -> go.Figure:
    """Top 10 diagnosticos do escopo recebido, maior em cima.

    Eixo mostra o nome da doenca; o codigo CID e o valor pago vao para o hover,
    para o rotulo ficar limpo mas a informacao tecnica continuar a um passe de mouse."""
    top = df.sort_values("internacoes", ascending=False).head(10).copy()
    # corta nomes muito longos no eixo, sem perder o nome inteiro (fica no hover)
    top["rotulo"] = top["doenca"].str.slice(0, 32).where(
        top["doenca"].str.len() <= 32, top["doenca"].str.slice(0, 32) + "…"
    )
    # titulo que responde: a doenca que mais interna no escopo e sua participacao
    resposta = lidera(df, "doenca", "internacoes")
    fig = _barh(
        top, x="internacoes", y="rotulo",
        titulo=f"Top 10 diagnósticos · {rotulo}<br><sub>{resposta}</sub>",
    )
    # hover rico: nome completo (codigo CID), internacoes e valor pago.
    fig.update_traces(
        customdata=top[["doenca", "cid", "valor_total"]].to_numpy(),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "%{x:,.0f} internações<br>"
            "R$ %{customdata[2]:,.2f}<extra></extra>"
        ),
    )
    return fig


def fig_serie_diaria(df: pd.DataFrame, rotulo: str) -> go.Figure:
    """Internacoes por dia (por data de ENTRADA) ao longo do mes, no escopo recebido.

    O total desta serie nao bate com o KPI de internacoes: o KPI e por
    competencia (AIH processadas no mes) e a serie e por data de entrada."""
    serie = df.sort_values("dia")
    fig = px.line(serie, x="dia", y="internacoes", markers=True)
    fig.update_traces(
        line_color=COR, marker_color=COR, line_width=2,
        fill="tozeroy", fillcolor="rgba(91,182,166,0.12)",
        hovertemplate="%{x|%d/%m}<br>%{y:,.0f} internações<extra></extra>",
    )
    # resposta: o dia de pico de entradas no mes
    resposta = ""
    if not serie.empty:
        pico = serie.loc[serie["internacoes"].idxmax()]
        dia_br = str(pico["dia"])[8:10] + "/" + str(pico["dia"])[5:7]
        resposta = f"pico em {dia_br}: {numero(pico['internacoes'])} entradas"
    fig.update_layout(xaxis_title="dia (data de entrada)", yaxis_title="internações")
    return _layout(fig, f"Internações por dia de entrada · {rotulo}<br><sub>{resposta}</sub>")


def fig_perfil(df: pd.DataFrame, rotulo: str) -> go.Figure:
    """Internacoes por faixa etaria e sexo (barras agrupadas), no escopo recebido."""
    ordem = ["< 1 ano", "1-14", "15-29", "30-49", "50-64", "65+", "nao informado"]
    fig = px.bar(
        df, x="faixa_etaria", y="internacoes", color="sexo", barmode="group",
        category_orders={"faixa_etaria": ordem},
        color_discrete_map=COR_SEXO,
    )
    fig.update_layout(xaxis_title="faixa etária", yaxis_title="internações")
    return _layout(fig, f"Perfil por faixa etária e sexo · {rotulo}")
