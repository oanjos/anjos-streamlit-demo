import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit import column_config 

# ===================== CONFIG PÁGINA =====================
st.set_page_config(
    page_title="Anjos do BI - Receita x Custos x Margem",
    page_icon="🪽",
    layout="wide"
)

# ===================== CSS PARA LEMBRAR O POWER BI =====================
css = """
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Remove o cursor em formato de cruz nos gráficos Plotly */
.js-plotly-plot .plotly .cursor-crosshair {
    cursor: default !important;
}

/* Títulos de seção centralizados (linha B) */
.anjos-section-title-center {
    font-size: 0.8rem;
    font-weight: 600;
    color: #6B7280;
    margin-bottom: 1.2rem;   /* mais espaço para b1/b2 */
    text-transform: uppercase;
    letter-spacing: 0.12em;
    text-align: center;
}


/* Header das tabelas (inclui a B3) */
[data-testid="stDataFrame"] thead tr th {
    background-color: #0F172A !important;  /* azul bem escuro */
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Fundo geral */
.main {
    background-color: #E5E7EB;
}

/* Top bar escura */
.anjos-top-bar {
    background: linear-gradient(90deg, #020617, #0F172A);
    color: #E5E7EB;
    padding: 1.2rem 2.2rem 1.4rem 2.2rem;
    border-radius: 0 0 1.5rem 1.5rem;
}

/* Título */
.anjos-top-title {
    font-size: 1.1rem;
    letter-spacing: 0.28em;
}

/* Linha de KPIs principais */
.anjos-kpi-row {
    margin-top: 1.5rem;
    display: flex;
    gap: 1.2rem;
}

.anjos-kpi-card {
    flex: 1;
    border-radius: 1.4rem;
    padding: 1rem 1.4rem 1.3rem 1.4rem;
    color: #F9FAFB;
    box-shadow: 0 18px 40px rgba(15,23,42,0.40);
}

.anjos-kpi-card.receita {
    background: linear-gradient(135deg, #1D4ED8, #0B3B9A);
}
.anjos-kpi-card.margem {
    background: linear-gradient(135deg, #059669, #047857);
}
.anjos-kpi-card.margem-pct {
    background: linear-gradient(135deg, #BE185D, #9D174D);
}

.anjos-kpi-label {
    font-size: 0.75rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #E5E7EB;
}

.anjos-kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin-top: 0.4rem;
}

.anjos-kpi-footer {
    font-size: 0.75rem;
    color: #D1D5DB;
    margin-top: 0.25rem;
}

/* Container “branco” principal */
.anjos-main-panel {
    margin-top: 1.2rem;
    background-color: #F9FAFB;
    border-radius: 1.4rem;
    padding: 1.2rem 1.4rem 1.5rem 1.4rem;
    box-shadow: 0 12px 30px rgba(148,163,184,0.35);
}

/* Títulos de seção (dentro do card) */
.anjos-section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #6B7280;
    margin-bottom: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* Caixas internas */
.anjos-inner-card {
    background-color: #FFFFFF;
    border-radius: 1.1rem;
    padding: 0.9rem 1rem 1rem 1rem;
    border: 1px solid #E5E7EB;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ===================== CARGA DOS DADOS =====================
@st.cache_data
def load_data(path: str = "Receita.xlsx"):
    # Fato de receita
    f = pd.read_excel(path, sheet_name="Receita", engine="openpyxl")
    # Dim de produtos
    d = pd.read_excel(path, sheet_name="Cadastro de Produtos", engine="openpyxl")

    # Ajusta tipos de data
    f["DataEmissao"] = pd.to_datetime(f["DataEmissao"])
    f["Ano"] = f["DataEmissao"].dt.year
    f["Mes"] = f["DataEmissao"].dt.month
    f["AnoMes"] = f["DataEmissao"].dt.to_period("M").dt.to_timestamp()

    # Cria cdProduto numérico na dim (Cod Produto = "Prod 2096")
    d["cdProduto"] = (
        d["Cod Produto"]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)           # permite NaN
        .astype("Int64")         # inteiro que aceita nulos
    )

    # Merge como RELATED do DAX
    df = f.merge(
        d[["cdProduto", "Grupo Produto", "Linha Produto", "Fornecedor", "CustoUnitario"]],
        on="cdProduto",
        how="left"
    )

    # Custos = QtdItens * CustoUnitario
    df["Custos"] = df["QtdItens"] * df["CustoUnitario"]

    # Receita = ValorBruto
    df["Receita"] = df["ValorBruto"]

    # Margem Bruta = Receita - Custos
    df["MargemBruta"] = df["Receita"] - df["Custos"]

    # % MC = Margem Bruta / Receita
    df["MargemPct"] = np.where(
        df["Receita"] != 0,
        df["MargemBruta"] / df["Receita"],
        np.nan
    )

    return df

df = load_data()

# ===================== SIDEBAR (FILTROS) =====================
st.sidebar.header("Filtros")

anos = ["Todos"] + sorted(df["Ano"].unique().tolist())
ano_sel = st.sidebar.selectbox("Ano", anos, index=0)

equipes = ["Todas"] + sorted(df["Equipe Vendas"].dropna().unique().tolist())
equipe_sel = st.sidebar.selectbox("Equipe de Vendas", equipes, index=0)

supers = ["Todos"] + sorted(df["Supervisor"].dropna().unique().tolist())
super_sel = st.sidebar.selectbox("Supervisor", supers, index=0)

vendedores = ["Todos"] + sorted(df["Vendedor"].dropna().unique().tolist())
vend_sel = st.sidebar.selectbox("Vendedor", vendedores, index=0)

df_filt = df.copy()
if ano_sel != "Todos":
    df_filt = df_filt[df_filt["Ano"] == ano_sel]
if equipe_sel != "Todas":
    df_filt = df_filt[df_filt["Equipe Vendas"] == equipe_sel]
if super_sel != "Todos":
    df_filt = df_filt[df_filt["Supervisor"] == super_sel]
if vend_sel != "Todos":
    df_filt = df_filt[df_filt["Vendedor"] == vend_sel]

# ===================== AGREGAÇÕES =====================
# Totais
receita_total = df_filt["Receita"].sum()
custos_total = df_filt["Custos"].sum()
margem_total = df_filt["MargemBruta"].sum()
margem_pct_total = margem_total / receita_total if receita_total != 0 else 0

# Por mês
df_mes = (
    df_filt
    .groupby("AnoMes")[["Receita", "MargemBruta"]]
    .sum()
    .reset_index()
    .sort_values("AnoMes")
)
df_mes["MargemPct"] = np.where(
    df_mes["Receita"] != 0,
    df_mes["MargemBruta"] / df_mes["Receita"],
    np.nan
)

# Por linha de produto
df_linha = (
    df_filt
    .groupby("Linha Produto")[["Receita"]]
    .sum()
    .reset_index()
    .sort_values("Receita", ascending=False)
)

# Por fornecedor
df_forn = (
    df_filt
    .groupby("Fornecedor")[["MargemBruta"]]
    .sum()
    .reset_index()
    .sort_values("MargemBruta", ascending=False)
)

# Por equipe / vendedor
df_equipe = (
    df_filt
    .groupby(["Equipe Vendas", "Vendedor"])
    .agg(
        Receita=("Receita", "sum"),
        MargemBruta=("MargemBruta", "sum")
    )
    .reset_index()
)
df_equipe["MargemPct"] = np.where(
    df_equipe["Receita"] != 0,
    df_equipe["MargemBruta"] / df_equipe["Receita"],
    np.nan
)

# ===================== TOPO: TÍTULO + CARDS =====================
top_container = st.container()
with top_container:
    st.markdown(
        """
        <div class="anjos-top-bar">
            <div class="anjos-top-title">RECEITA × CUSTOS × MARGEM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="anjos-kpi-row">
            <div class="anjos-kpi-card receita">
                <div class="anjos-kpi-label">RECEITA</div>
                <div class="anjos-kpi-value">R$ {receita_total:,.2f}</div>
                <div class="anjos-kpi-footer">Total do período filtrado</div>
            </div>
            <div class="anjos-kpi-card margem">
                <div class="anjos-kpi-label">MARGEM BRUTA</div>
                <div class="anjos-kpi-value">R$ {margem_total:,.2f}</div>
                <div class="anjos-kpi-footer">Receita - Custos</div>
            </div>
            <div class="anjos-kpi-card margem-pct">
                <div class="anjos-kpi-label">MARGEM BRUTA %</div>
                <div class="anjos-kpi-value">{margem_pct_total:,.0%}</div>
                <div class="anjos-kpi-footer">% MC (Margem sobre Receita)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===================== PAINEL PRINCIPAL =====================
with st.container():
   # st.markdown('<div class="anjos-main-panel">', unsafe_allow_html=True)

    # -------- Linha superior: 3 gráficos por mês --------
        # -------- Linha superior: 3 gráficos por mês --------
    c1, c2, c3 = st.columns(3)

    with c1:
      #  st.markdown(
      #      '<div class="anjos-inner-card"><div class="anjos-section-title">RECEITA MENSAL</div>',
      #      unsafe_allow_html=True
      #  )

        if not df_mes.empty:
            fig_receita = px.bar(
                df_mes,
                x="AnoMes",
                y="Receita",
                labels={"AnoMes": "", "Receita": "Receita (R$)"},
                color_discrete_sequence=["#1D4ED8"],  # azul (card de Receita)
            )
            fig_receita.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                bargap=0.05,  # barras mais grossas
                xaxis=dict(showgrid=False, showline=False),
                yaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_receita.update_traces(
                hovertemplate="Mês: %{x|%b %Y}<br>Receita: R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_receita, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem dados para a combinação de filtros atual.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
      #  st.markdown(
      #      '<div class="anjos-inner-card"><div class="anjos-section-title">MARGEM BRUTA MENSAL</div>',
      #      unsafe_allow_html=True
      #  )
        if not df_mes.empty:
            fig_margem = px.bar(
                df_mes,
                x="AnoMes",
                y="MargemBruta",
                labels={"AnoMes": "", "MargemBruta": "Margem Bruta (R$)"},
                color_discrete_sequence=["#059669"],  # verde (card de Margem)
            )
            fig_margem.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                bargap=0.05,
                xaxis=dict(showgrid=False, showline=False),
                yaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_margem.update_traces(
                hovertemplate="Mês: %{x|%b %Y}<br>Margem Bruta: R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_margem, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem dados para a combinação de filtros atual.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
     #   st.markdown(
     #       '<div class="anjos-inner-card"><div class="anjos-section-title">%¨MARGEM BRUTA MENSAL</div>',
     #       unsafe_allow_html=True
     #   )
        if not df_mes.empty:
            df_mes_pct = df_mes.copy()
            df_mes_pct["MargemPct"] = df_mes_pct["MargemPct"].fillna(0)

            fig_margem_pct = px.bar(
                df_mes_pct,
                x="AnoMes",
                y="MargemPct",
                labels={"AnoMes": "", "MargemPct": "% Margem Bruta"},
                color_discrete_sequence=["#BE185D"],  # magenta (card de %MC)
            )
            fig_margem_pct.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                bargap=0.05,
                xaxis=dict(showgrid=False, showline=False),
                yaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickformat=".0%"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_margem_pct.update_traces(
                hovertemplate="Mês: %{x|%b %Y}<br>Margem Bruta: %{y:.1%}<extra></extra>"
            )
            st.plotly_chart(fig_margem_pct, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem dados para a combinação de filtros atual.")
        st.markdown('</div>', unsafe_allow_html=True)


    st.markdown("")

    # -------- Linha inferior: rosca, barras horizontais e tabela --------
    b1, b2, b3 = st.columns([1.1, 1.1, 2])

    # RECEITA POR LINHA DE PRODUTO (ROSCA)
    with b1:
        st.markdown(
            '<div class="anjos-section-title-center">RECEITA POR LINHA DE PRODUTO</div>',
            unsafe_allow_html=True
        )   

        if not df_linha.empty:
            df_linha_plot = df_linha.copy()
            fig_linha = px.pie(
                df_linha_plot,
                names="Linha Produto",
                values="Receita",
                hole=0.65,
                color_discrete_sequence=["#0B62D6", "#77B5F7", "#93C5FD", "#BFDBFE"],
            )
            fig_linha.update_traces(
                textposition="inside",
                texttemplate="%{label}<br>%{percent:.1%}",
                hovertemplate="%{label}: R$ %{value:,.2f} (%{percent:.1%})<extra></extra>",
            )
            fig_linha.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=260,
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_linha, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem dados para a combinação de filtros atual.")

        st.markdown('</div>', unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)


    # MARGEM POR FORNECEDOR (BARRAS HORIZONTAIS)
    with b2:
        st.markdown('<div class="anjos-section-title-center">MARGEM POR FORNECEDOR</div>', unsafe_allow_html=True)
        
        if not df_forn.empty:
            df_forn_plot = df_forn.copy()
            df_forn_plot = df_forn_plot.sort_values("MargemBruta", ascending=True)

            fig_forn = px.bar(
                df_forn_plot,
                x="MargemBruta",
                y="Fornecedor",
                orientation="h",
                labels={"MargemBruta": "Margem Bruta (R$)", "Fornecedor": ""},
                color_discrete_sequence=["#296857"],  # seu verde
            )
            fig_forn.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=0, b=0),
                bargap=0.25,
                xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickformat=",.0f"),
                yaxis=dict(showgrid=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_forn.update_traces(
                hovertemplate="Fornecedor: %{y}<br>Margem Bruta: R$ %{x:,.2f}<extra></extra>"
            )
            st.plotly_chart(
                fig_forn,
                use_container_width=True,
                config={"displayModeBar": False},  # sem staticPlot
            )

        else:
            st.info("Sem dados para a combinação de filtros atual.")

        st.markdown("</div>", unsafe_allow_html=True)

# ANÁLISE POR EQUIPE DE VENDAS (TABELA)

df_equipe_view = df_equipe.copy()
df_equipe_view["Receita"] = df_equipe_view["Receita"].round(2)
df_equipe_view["MargemBruta"] = df_equipe_view["MargemBruta"].round(2)
df_equipe_view["MargemPct"] = df_equipe_view["MargemPct"] * 100  # vira 37, 41 etc.
df_equipe_view["MargemPct"] = df_equipe_view["MargemPct"].round(2)

df_equipe_view = df_equipe_view.rename(columns={
    "Equipe Vendas": "Equipe",
    "Vendedor": "Vendedor",
    "Receita": "Receita",
    "MargemBruta": "Margem Bruta",
    "MargemPct": "% MC"
})

with b3:
    st.markdown('<div class="anjos-section-title">ANÁLISE POR EQUIPE DE VENDAS</div>', unsafe_allow_html=True)

    if not df_equipe_view.empty:
        st.dataframe(
            df_equipe_view,
            use_container_width=True,
            column_config={
                "Equipe": column_config.TextColumn("Equipe"),
                "Vendedor": column_config.TextColumn("Vendedor"),
                "Receita": column_config.NumberColumn(
                    "Receita",
                    format="R$ %.2f",
                ),
                "Margem Bruta": column_config.NumberColumn(
                    "Margem Bruta",
                    format="R$ %.2f",
                ),
                "% MC": column_config.NumberColumn(
                    "% MC",
                    format="%.1f %%",
                ),
            },
            hide_index=True,
        )
    else:
        st.info("Sem dados para a combinação de filtros atual.")
