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
import streamlit as st

import painel

st.set_page_config(page_title="SUS · internações por estado", layout="wide", page_icon="🏥")


@st.cache_data
def carregar():
    return painel.ler()


def main():
    st.title("🏥 Internações hospitalares do SUS · por estado")
    st.caption("Fonte: SIH/SUS (DATASUS). Uma linha = uma internação (AIH).")

    try:
        dados = carregar()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Não consegui ler os marts do sih.duckdb.\n\n"
            f"Detalhe: {e}\n\n"
            "Rode antes: `uv run python -m pipeline.marts`"
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
        escolha = st.selectbox("Estado", ["Brasil"] + ufs, index=0)
    with col_met:
        metrica = st.selectbox(
            "Métrica do mapa e ranking",
            ["internacoes", "valor_total", "custo_medio", "dias_medio", "taxa_mortalidade_pct"],
            index=0,
        )

    uf = None if escolha == "Brasil" else escolha

    # ---- Cartoes: Brasil le kpis_gerais; UF le a linha do mart por_estado ----
    if uf is None:
        k = dados["kpis_gerais"].iloc[0]
        internacoes, valor, custo = k["internacoes"], k["valor_total"], k["custo_medio"]
        dias, mort, n_ufs = k["dias_medio"], k["taxa_mortalidade_pct"], k["ufs"]
    else:
        linha = por_estado[por_estado["uf"] == uf].iloc[0]
        internacoes, valor, custo = linha["internacoes"], linha["valor_total"], linha["custo_medio"]
        dias, mort, n_ufs = linha["dias_medio"], linha["taxa_mortalidade_pct"], 1

    c = st.columns(5)
    c[0].metric("Internações", painel.numero(internacoes))
    c[1].metric("Gasto total", painel.reais(valor))
    c[2].metric("Custo médio", painel.reais(custo))
    c[3].metric("Permanência média", painel.numero(dias, 1) + " dias")
    c[4].metric("Mortalidade", painel.pct(mort, 2))

    st.divider()

    # ---- Faixa nacional: mapa + ranking (sempre Brasil, para comparar) -------
    st.subheader("Visão nacional")
    f1 = st.columns([3, 2])
    with f1[0]:
        st.plotly_chart(painel.fig_mapa(por_estado, metrica), width="stretch")
    with f1[1]:
        st.plotly_chart(painel.fig_ranking_estados(por_estado, metrica), width="stretch")

    st.plotly_chart(painel.fig_custo_medio_uf(por_estado), width="stretch")

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

    st.subheader(f"Detalhe · {rotulo}")
    f2 = st.columns(2)
    with f2[0]:
        st.plotly_chart(painel.fig_top_diagnosticos(diag, rotulo), width="stretch")
    with f2[1]:
        st.plotly_chart(painel.fig_serie_diaria(serie, rotulo), width="stretch")

    st.plotly_chart(painel.fig_perfil(perfil, rotulo), width="stretch")


if __name__ == "__main__":
    main()
