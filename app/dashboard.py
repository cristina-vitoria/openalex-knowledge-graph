"""
dashboard.py
Dashboard interativo com Streamlit para exploração do Knowledge Graph.

Executar com:
    streamlit run app/dashboard.py
"""

import json
from pathlib import Path
import sys

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from src.graph import (
    construir_grafo_coautoria,
    construir_grafo_conceito,
    filtrar_grafo,
    maior_componente,
)
from src.metrics import calcular_centralidades, detectar_comunidades, resumo_rede

st.set_page_config(
    page_title="OpenAlex Knowledge Graph",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 OpenAlex Knowledge Graph")
st.caption("Mapeamento do conhecimento científico brasileiro via grafos de co-autoria e co-conceito.")

# -- Sidebar ------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    tipo_grafo = st.radio("Tipo de grafo", ["Co-autoria", "Co-conceito"])
    min_degree = st.slider("Grau mínimo do nó", 1, 10, 2)
    apenas_maior_componente = st.checkbox("Apenas maior componente", value=True)
    top_n = st.slider("Top N nós por centralidade", 5, 50, 20)

# -- Carregamento de dados ----------------------------------------------------
@st.cache_data
def carregar_dados():
    caminho = Path("data/raw/works_ufms_cs.json")
    if not caminho.exists():
        st.warning("Arquivo não encontrado. Execute o notebook 01_coleta.ipynb primeiro.")
        return []
    with open(caminho) as f:
        return json.load(f)

works = carregar_dados()

if not works:
    st.info("Execute `notebooks/01_coleta.ipynb` para coletar os dados e recarregue esta página.")
    st.stop()

# -- Construção do grafo ------------------------------------------------------
@st.cache_resource
def construir(_works, tipo, min_deg, maior_comp):
    G = construir_grafo_coautoria(_works) if tipo == "Co-autoria" else construir_grafo_conceito(_works)
    G = filtrar_grafo(G, min_degree=min_deg)
    if maior_comp:
        G = maior_componente(G)
    return G

G = construir(works, tipo_grafo, min_degree, apenas_maior_componente)

# -- KPIs ---------------------------------------------------------------------
resumo = resumo_rede(G)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Nós", resumo["nodes"])
c2.metric("Arestas", resumo["edges"])
c3.metric("Densidade", resumo["density"])
c4.metric("Grau médio", resumo["avg_degree"])

st.divider()

# -- Tabela + Histograma ------------------------------------------------------
col_esq, col_dir = st.columns([1, 1])

with col_esq:
    st.subheader(f"🏆 Top {top_n} por Betweenness Centrality")
    df_metrics = calcular_centralidades(G)
    st.dataframe(
        df_metrics.head(top_n)[["node", "degree_raw", "betweenness", "eigenvector", "clustering"]]
        .rename(columns={
            "node": "Nó", "degree_raw": "Grau",
            "betweenness": "Betweenness", "eigenvector": "Eigenvector",
            "clustering": "Clustering",
        }),
        use_container_width=True,
    )

with col_dir:
    st.subheader("📊 Distribuição de Grau")
    graus = [d for _, d in G.degree()]
    fig = px.histogram(x=graus, nbins=30, labels={"x": "Grau", "y": "Frequência"},
                       color_discrete_sequence=["#01696f"])
    fig.update_layout(showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -- Visualização do grafo ----------------------------------------------------
st.subheader("🕸️ Visualização do Grafo")

try:
    comunidades = detectar_comunidades(G)
    nx.set_node_attributes(G, comunidades, "community")
except Exception:
    comunidades = {n: 0 for n in G.nodes()}

pos = nx.spring_layout(G, seed=42, k=0.5)

edge_x, edge_y = [], []
for u, v in G.edges():
    x0, y0 = pos[u]; x1, y1 = pos[v]
    edge_x += [x0, x1, None]; edge_y += [y0, y1, None]

node_x = [pos[n][0] for n in G.nodes()]
node_y = [pos[n][1] for n in G.nodes()]
node_color = [comunidades.get(n, 0) for n in G.nodes()]
node_size = [5 + G.degree(n) * 2 for n in G.nodes()]

fig_grafo = go.Figure()
fig_grafo.add_trace(go.Scatter(
    x=edge_x, y=edge_y, mode="lines",
    line=dict(width=0.5, color="#cccccc"), hoverinfo="none"
))
fig_grafo.add_trace(go.Scatter(
    x=node_x, y=node_y,
    mode="markers+text" if G.number_of_nodes() < 80 else "markers",
    marker=dict(size=node_size, color=node_color, colorscale="Viridis", showscale=True),
    text=list(G.nodes()), textposition="top center", textfont=dict(size=8),
    hoverinfo="text",
))
fig_grafo.update_layout(
    height=600, showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig_grafo, use_container_width=True)
