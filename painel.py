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

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# duckdb so e importado dentro de ler(), quando ha banco local. No deploy
# (Streamlit Cloud) o painel le CSVs e nao precisa do duckdb instalado.

# Caminho absoluto a partir deste arquivo: o painel acha o banco mesmo quando
# o Streamlit e iniciado de outra pasta (nao depende do diretorio atual).
BANCO = str(Path(__file__).resolve().parent / "sih.duckdb")

# Geometria local: evita buscar limites estaduais na rede ao abrir o mapa.
GEOJSON_UF = Path(__file__).resolve().parent / "assets" / "brasil-ufs.geojson"


@lru_cache(maxsize=1)
def _geometria_ufs() -> dict:
    return json.loads(GEOJSON_UF.read_text(encoding="utf-8"))


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
# mapa. Tons pastel, puxando do verde ao azul.
COR = "#5bb6a6"           # verde-agua medio, suave
ESCALA = "Teal"           # escala continua verde->azul suave para o mapa
# Paleta qualitativa (rosca, varias categorias): tons claros e harmonicos.
PALETA = ["#7fcbbd", "#9fd6c6", "#5bb6a6", "#cbe8df", "#f0c674", "#b7c4c0"]

# Cor por regiao na rosca: tons suaves que contrastam bem entre si.
COR_REGIAO = {
    "Sudeste": "#8fcfe0",         # azul suave
    "Nordeste": "#8fd4b8",        # verde claro
    "Sul": "#b6e0a8",             # verde-limao suave
    "Norte": "#f0c674",           # amarelo suave
    "Centro-Oeste": "#d9a8e0",    # lilas suave
}

# Cor por sexo no grafico demografico.
COR_SEXO = {
    "Feminino": "#8fcfe0",        # azul-esverdeado claro
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
    nomes = marts if marts is not None else MARTS
    if not nomes:
        return {}

    permitidos = set(MARTS) | {"mortalidade_por_cid", "municipios_pareto"}
    invalidos = set(nomes) - permitidos
    if invalidos:
        raise ValueError(f"Marts não reconhecidos: {', '.join(sorted(invalidos))}")

    if Path(banco).exists():
        import duckdb  # importado so aqui: no deploy nao ha banco nem duckdb
        con = duckdb.connect(banco, read_only=True)
        try:
            return {nome: con.execute(f"SELECT * FROM ouro.{nome}").df() for nome in nomes}
        finally:
            con.close()

    # Fallback: CSVs da camada ouro (deploy).
    pasta = Path(__file__).resolve().parent / "dados_painel"
    ausentes = [nome for nome in nomes if not (pasta / f"{nome}.csv").is_file()]
    if ausentes:
        raise FileNotFoundError(
            "Marts sem CSV exportado: " + ", ".join(ausentes)
            + ". Rode o pipeline e depois 'uv run python exportar_painel.py'."
        )
    return {nome: pd.read_csv(pasta / f"{nome}.csv") for nome in nomes}


# ---------------------------------------------------------------------------
# 3. FORMATO (funcoes puras)
# ---------------------------------------------------------------------------
def periodo_serie(serie: pd.DataFrame) -> str:
    """Formata os meses presentes na serie; nao infere a competencia das AIHs."""
    datas = pd.to_datetime(serie["dia"], errors="raise").dropna()
    meses = sorted(set(datas.dt.strftime("%Y-%m")))
    nomes = ("janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    return ", ".join(f"{nomes[int(mes[5:7]) - 1]}/{mes[:4]}" for mes in meses) or "não informado"


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


def lidera(df: pd.DataFrame, rotulo_col: str, valor_col: str,
           pct_col: str | None = None) -> str:
    """Frase-resposta do tipo 'SP lidera: 249.866 (20,2% do total)'.

    Nao calcula nada: le a primeira linha (os marts ja vem ordenados do maior
    para o menor). Quando pct_col e dado, a participacao ja vem pronta na coluna
    (somada por window function no proprio mart); sem ela, mostra so o valor."""
    if df.empty:
        return ""
    topo = df.iloc[0]
    if pct_col is not None and pct_col in df.columns:
        return (f"{topo[rotulo_col]} lidera: {numero(topo[valor_col])} "
                f"({pct(topo[pct_col])} do total)")
    return f"{topo[rotulo_col]} lidera: {numero(topo[valor_col])}"


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
    """Mapa com limites embutidos e fundo sem tiles externos ou token."""
    geojson = _geometria_ufs()
    fig = px.choropleth_map(
        por_estado, geojson=geojson, locations="uf", featureidkey="properties.sigla",
        color=metrica, color_continuous_scale=ESCALA, map_style="white-bg",
        custom_data=["uf", "regiao", metrica],
    )
    dinheiro = metrica in {"valor_total", "custo_medio"}
    casas = 0 if metrica == "internacoes" else (1 if metrica == "dias_medio" else 2)
    prefixo = "R$ " if dinheiro else ""
    sufixo = "%" if metrica == "taxa_mortalidade_pct" else (" dias" if metrica == "dias_medio" else "")
    fig.update_traces(
        marker_line_color="white", marker_line_width=0.8,
        hovertemplate=("<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                       + rotulo(metrica) + ": " + prefixo
                       + "%{customdata[2]:,." + str(casas) + "f}" + sufixo + "<extra></extra>"),
    )
    ordenado = por_estado.sort_values(metrica, ascending=False)
    resposta = lidera(ordenado, "uf", metrica, "pct_internacoes" if metrica == "internacoes" else None)
    fig = _layout(fig, f"{rotulo(metrica)} por estado<br><sub>{resposta}</sub>")
    oeste, sul, leste, norte = geojson["bbox"]
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=64, b=10),
        map=dict(bounds=dict(west=oeste, east=leste, south=sul, north=norte)),
        coloraxis_colorbar=dict(title=rotulo(metrica), thickness=12, len=0.7,
                               tickprefix=prefixo, ticksuffix=sufixo, tickformat=f",.{casas}f"),
    )
    return fig


def fig_rosca_regiao(por_estado: pd.DataFrame, metrica: str = "internacoes") -> go.Figure:
    """Grafico de rosca (donut) com a participacao de cada regiao na metrica."""
    if metrica not in {"internacoes", "valor_total"}:
        raise ValueError("Composicao regional exige uma metrica aditiva: internacoes ou valor_total")
    fig = px.pie(
        por_estado, names="regiao", values=metrica, hole=0.6,
        color="regiao", color_discrete_map=COR_REGIAO,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      marker=dict(line=dict(color="white", width=2)))
    fig = _layout(fig, f"Participação por região · {rotulo(metrica).lower()}")
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>" + ("R$ " if metrica == "valor_total" else "")
                      + "%{value:,." + ("2" if metrica == "valor_total" else "0")
                      + "f}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(height=470, showlegend=True,
                      legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08))
    return fig


def fig_ranking_estados(por_estado: pd.DataFrame, metrica: str = "internacoes") -> go.Figure:
    """Ranking das UFs pela metrica escolhida, maior em cima."""
    df = por_estado.sort_values(metrica, ascending=False)
    pct_col = "pct_internacoes" if metrica == "internacoes" else None
    resposta = lidera(df, "uf", metrica, pct_col)
    fig = _barh(df, x=metrica, y="uf",
                titulo=f"Ranking de estados · {rotulo(metrica).lower()}<br><sub>{resposta}</sub>")
    fig.update_layout(height=max(430, 22 * len(df) + 100))
    if metrica in {"valor_total", "custo_medio"}:
        fig.update_traces(text=[reais_curto(v) for v in df[metrica]], texttemplate="%{text}",
                          hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
    elif metrica == "taxa_mortalidade_pct":
        fig.update_traces(texttemplate="%{x:,.2f}%", hovertemplate="%{y}: %{x:,.2f}%<extra></extra>")
    elif metrica == "dias_medio":
        fig.update_traces(texttemplate="%{x:,.1f} dias", hovertemplate="%{y}: %{x:,.1f} dias<extra></extra>")
    return fig


def fig_custo_medio_uf(por_estado: pd.DataFrame) -> go.Figure:
    """Custo medio por internacao em cada UF: mostra a desigualdade regional."""
    df = por_estado.sort_values("custo_medio", ascending=False)
    # resposta: o contraste entre o maior e o menor custo medio (desigualdade).
    # So leitura das pontas do ranking ja ordenado, sem conta.
    resposta = ""
    if not df.empty:
        alto, baixo = df.iloc[0], df.iloc[-1]
        resposta = (f"{alto['uf']} ({reais(alto['custo_medio'], 0)}) no topo, "
                    f"{baixo['uf']} ({reais(baixo['custo_medio'], 0)}) na base")
    fig = _barh(df, x="custo_medio", y="uf",
                titulo=f"Valor médio registrado por AIH · por UF<br><sub>{resposta}</sub>")
    fig.update_traces(name="Média", showlegend=True, texttemplate="R$ %{x:,.0f}",
                      hovertemplate="<b>%{y}</b><br>Média: R$ %{x:,.2f}<extra></extra>")
    if "custo_mediana" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["custo_mediana"], y=df["uf"], mode="markers", name="Mediana",
            marker=dict(symbol="diamond", size=8, color="#245f68"),
            hovertemplate="<b>%{y}</b><br>Mediana: R$ %{x:,.2f}<extra></extra>",
        ))
    fig.update_layout(height=max(430, 22 * len(df) + 100),
                      legend=dict(orientation="h", y=-0.08, x=0))
    return fig


# As tres funcoes de detalhe recebem o DataFrame ja no escopo certo: o app
# passa o mart nacional (para "Brasil") ou o mart por UF ja filtrado por linha
# (para um estado). Assim o painel nunca decide escopo nem agrega.
def fig_top_diagnosticos(df: pd.DataFrame, rotulo: str) -> go.Figure:
    """Top 10 diagnosticos do escopo recebido, maior em cima.

    Eixo mostra o nome da doenca; o codigo CID e o valor pago vao para o hover,
    para o rotulo ficar limpo mas a informacao tecnica continuar a um passe de mouse."""
    # o mart ja vem ordenado por 'posicao' e com o top 10 (mart 03) ou todos
    # (mart 06); head(10) cobre os dois casos sem reordenar nem calcular.
    top = df.sort_values("posicao").head(10).copy()
    # corta nomes muito longos no eixo, sem perder o nome inteiro (fica no hover)
    top["rotulo"] = top["doenca"].str.slice(0, 32).where(
        top["doenca"].str.len() <= 32, top["doenca"].str.slice(0, 32) + "…"
    )
    top["rotulo"] = top["cid"].fillna("Sem CID").astype(str) + " · " + top["rotulo"]
    # titulo que responde: a doenca que mais interna no escopo e sua participacao
    resposta = lidera(top, "doenca", "internacoes", "pct_do_total")
    fig = _barh(
        top, x="internacoes", y="rotulo",
        titulo=f"Top 10 diagnósticos · {rotulo}<br><sub>{resposta}</sub>",
    )
    # hover rico: nome completo (codigo CID), internacoes e valor pago.
    fig.update_traces(
        customdata=top[["doenca", "cid", "valor_total", "pct_do_total"]].to_numpy(),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "%{x:,.0f} internações<br>"
            "R$ %{customdata[2]:,.2f}<br>%{customdata[3]:,.2f}% do total do recorte<extra></extra>"
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
    # resposta: o dia de pico de entradas no mes (le a maior linha, nao calcula)
    resposta = ""
    if not serie.empty:
        pico = serie.sort_values("internacoes", ascending=False).iloc[0]
        dia_br = str(pico["dia"])[8:10] + "/" + str(pico["dia"])[5:7]
        resposta = f"pico em {dia_br}: {numero(pico['internacoes'])} entradas"
        fig.add_annotation(x=pico["dia"], y=pico["internacoes"], text=f"Pico · {dia_br}",
                           showarrow=True, arrowhead=2, ax=0, ay=-32,
                           bgcolor="white", bordercolor=COR, font=dict(size=11))
        fig.update_yaxes(range=[0, float(pico["internacoes"]) * 1.18 or 1])
    fig.update_layout(xaxis_title="dia (data de entrada)", yaxis_title="internações", hovermode="x unified")
    fig.update_xaxes(tickformat="%d/%m", hoverformat="%d/%m/%Y")
    fig.update_yaxes(rangemode="tozero")
    return _layout(fig, f"Internações por dia de entrada · {rotulo}<br><sub>{resposta}</sub>")


def fig_perfil(df: pd.DataFrame, rotulo: str) -> go.Figure:
    """Internacoes por faixa etaria e sexo (barras agrupadas), no escopo recebido."""
    ordem = ["< 1 ano", "1-14", "15-29", "30-49", "50-64", "65+", "nao informado"]
    fig = px.bar(
        df, x="faixa_etaria", y="internacoes", color="sexo", barmode="group",
        category_orders={"faixa_etaria": ordem, "sexo": ["Feminino", "Masculino", "nao informado"]},
        color_discrete_map=COR_SEXO, text="internacoes",
        custom_data=["dias_medio"] if "dias_medio" in df.columns else None,
    )
    detalhe = "<br>Permanência média: %{customdata[0]:,.1f} dias" if "dias_medio" in df.columns else ""
    fig.update_traces(texttemplate="%{y:,.0f}", textposition="auto", textangle=0, cliponaxis=False,
                      hovertemplate="<b>%{fullData.name}</b> · %{x}<br>%{y:,.0f} internações"
                                    + detalhe + "<extra></extra>")
    fig.update_layout(xaxis_title="faixa etária", yaxis_title="internações",
                      height=470, bargap=0.22, bargroupgap=0.08,
                      legend=dict(title=None, orientation="h", y=-0.18, x=0),
                      uniformtext_minsize=11, uniformtext_mode="hide")
    fig.update_yaxes(rangemode="tozero")
    return _layout(fig, f"Perfil por faixa etária e sexo · {rotulo}")


def fig_mortalidade_por_cid(df: pd.DataFrame) -> go.Figure:
    """Exibe as maiores taxas hospitalares entre CID com 100 ou mais AIHs."""
    top = df.sort_values("posicao").head(10).copy()
    fig = _barh(
        top, x="taxa_mortalidade_pct", y="cid",
        titulo="Mortalidade hospitalar por CID · mínimo de 100 AIHs",
        hovertemplate="%{y}: %{x:,.2f}%<extra></extra>",
    )
    fig.update_traces(
        texttemplate="%{x:,.2f}%", customdata=top[["doenca", "internacoes", "obitos"]].to_numpy(),
        hovertemplate="<b>%{y} · %{customdata[0]}</b><br>%{customdata[1]:,.0f} internações"
                      "<br>%{customdata[2]:,.0f} óbitos<br>Taxa: %{x:,.2f}%<extra></extra>",
    )
    fig.update_xaxes(range=[0, 100])
    return fig


def fig_municipios_pareto(df: pd.DataFrame) -> go.Figure:
    """Mostra o percentual acumulado dos municípios, já calculado no mart."""
    ordem = df.sort_values("posicao")
    fig = px.line(ordem, x="posicao", y="pct_acumulado", markers=False)
    fig.update_traces(
        line_color=COR, marker_color=COR,
        customdata=ordem[["municipio", "uf", "internacoes", "valor_total"]].to_numpy(),
        hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b><br>Posição: %{x}"
                      "<br>%{customdata[2]:,.0f} internações<br>R$ %{customdata[3]:,.2f}"
                      "<br>Acumulado: %{y:,.2f}%<extra></extra>",
    )
    fig.add_hline(y=80, line_dash="dot", line_color="#b08c4f", annotation_text="Referência de 80%")
    fig.update_layout(xaxis_title="Municípios no ranking", yaxis_title="Gasto acumulado (%)")
    fig.update_yaxes(range=[0, 100])
    fig = _layout(
        fig, "Concentração do valor por município de residência<br><sub>Curva completa · referência de 80%</sub>",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=75, b=100),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.22,
                         bgcolor="#f3fbf7", bordercolor="#dbeee4", font=dict(size=11),
                         buttons=[dict(label="Todos os municípios", method="relayout",
                                       args=[{"xaxis.autorange": True}]),
                                  dict(label="Primeiros 30", method="relayout",
                                       args=[{"xaxis.range": [0.5, 30.5], "xaxis.autorange": False}])])],
    )
    return fig
