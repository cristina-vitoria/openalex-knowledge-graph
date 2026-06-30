"""
dashboard.py
Dashboard interativo com Streamlit para exploração do Knowledge Graph.

Executar com:
    streamlit run app/dashboard.py
"""

import json
from collections import Counter
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

_OA_PALETTE = ["#01696f", "#4f98a3", "#a3cdd1", "#e07b54", "#f2c57c", "#c0c0c0"]

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OpenAlex Knowledge Graph",
    page_icon="🔬",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://openalex.org/img/openalex-logo.png",
        use_container_width=True,
    )
    st.header("⚙️ Configurações")
    tipo_grafo = st.radio("Tipo de grafo", ["Co-autoria", "Co-conceito"])
    min_degree = st.slider("Grau mínimo do nó", 1, 10, 2)
    apenas_maior_componente = st.checkbox("Apenas maior componente", value=True)
    top_n = st.slider("Top N por centralidade", 5, 50, 20)
    st.divider()

    # Glossário na sidebar
    with st.expander("📖 Glossário de Métricas"):
        st.markdown("""
**Grau (Degree)**
Número de colaboradores diretos. Alto grau = autor prolífico.

**Betweenness**
Frequência com que o autor aparece no caminho mais curto entre dois outros. Alto betweenness = **ponte** entre grupos.

**Eigenvector**
Peso das conexões pelos vizinhos: colaborar com autores importantes eleva este valor. Lógica similar ao PageRank.

**Clustering**
O quanto os colaboradores de um autor também colaboram entre si. Alto = grupo coeso e fechado.

**Comunidade (Louvain)**
Grupo de autores que publicam mais entre si do que com o restante da rede. Tende a corresponder a grupos de pesquisa ou linhas temáticas.
        """)
    st.caption(
        "Dados coletados via [OpenAlex API](https://openalex.org). "
        "Licença CC0."
    )

# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados():
    candidatos = [
        Path("data/raw/works_ufms_cs.json"),
        Path("../data/raw/works_ufms_cs.json"),
        Path(__file__).parent.parent / "data" / "raw" / "works_ufms_cs.json",
    ]
    for p in candidatos:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    return []

works = carregar_dados()

if not works:
    st.warning(
        "⚠️ Arquivo `data/raw/works_ufms_cs.json` não encontrado. "
        "Execute `notebooks/01_coleta.ipynb` primeiro e recarregue a página."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Construção do grafo (cacheado)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Construindo grafo...")
def construir(_works, tipo, min_deg, maior_comp):
    G = (
        construir_grafo_coautoria(_works)
        if tipo == "Co-autoria"
        else construir_grafo_conceito(_works)
    )
    G = filtrar_grafo(G, min_degree=min_deg)
    if maior_comp and G.number_of_nodes() > 0:
        G = maior_componente(G)
    return G

G = construir(works, tipo_grafo, min_degree, apenas_maior_componente)

# ---------------------------------------------------------------------------
# Header + KPIs globais
# ---------------------------------------------------------------------------
st.title("🔬 OpenAlex Knowledge Graph")
st.caption(
    f"**{len(works):,} papers** coletados · "
    "Instituições brasileiras (2018–2026) · Área: Computer Science"
)

resumo = resumo_rede(G)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("👤 Nós", f"{resumo['nodes']:,}",
          help="Total de autores no componente selecionado")
c2.metric("🔗 Arestas", f"{resumo['edges']:,}",
          help="Total de pares de autores que co-assinaram ao menos 1 paper")
c3.metric("🌐 Densidade", resumo["density"],
          help="Fração de arestas existentes vs possíveis. Próximo de 0 = rede esparsa")
c4.metric("📊 Grau Médio", resumo["avg_degree"],
          help="Número médio de colaboradores diretos por autor")
c5.metric("🧩 Componentes", resumo["components"],
          help="Subgrafos desconectados. 1 = toda a rede está conectada")

st.divider()

# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
tab_grafo, tab_centralidade, tab_eda, tab_papers = st.tabs([
    "🕸️ Grafo",
    "🏆 Centralidade",
    "📈 EDA",
    "📚 Top Papers",
])

# ===== ABA 1: GRAFO =========================================================
with tab_grafo:
    try:
        comunidades = detectar_comunidades(G)
        nx.set_node_attributes(G, comunidades, "community")
        n_com = len(set(comunidades.values()))
    except Exception:
        comunidades = {n: 0 for n in G.nodes()}
        n_com = 1

    # Interpretação das comunidades
    st.info(
        f"🧩 **{n_com} comunidades detectadas** pelo algoritmo de Louvain — "
        "cada cor representa um grupo de autores que colaboram mais intensamente "
        "entre si do que com o restante da rede. No contexto de co-autoria, "
        "comunidades tendem a corresponder a **grupos de pesquisa** ou **linhas temáticas** "
        "de uma mesma instituição. Nós maiores têm maior grau (mais colaboradores diretos)."
    )

    busca = st.text_input("🔍 Destacar autor", placeholder="Digite parte do nome...")

    pos = nx.spring_layout(G, seed=42, k=0.5)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_names = list(G.nodes())
    node_x = [pos[n][0] for n in node_names]
    node_y = [pos[n][1] for n in node_names]
    node_color = [comunidades.get(n, 0) for n in node_names]
    node_size = [6 + G.degree(n) * 3 for n in node_names]

    if busca:
        node_color = [
            999 if busca.lower() in n.lower() else comunidades.get(n, 0)
            for n in node_names
        ]
        node_size = [
            20 if busca.lower() in n.lower() else 6 + G.degree(n) * 3
            for n in node_names
        ]

    hover_text = [
        f"<b>{n}</b><br>Grau: {G.degree(n)}<br>Comunidade: {comunidades.get(n, '?')}"
        for n in node_names
    ]

    fig_grafo = go.Figure()
    fig_grafo.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.4, color="#cccccc"),
        hoverinfo="none",
    ))
    fig_grafo.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text" if G.number_of_nodes() < 60 else "markers",
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Comunidade", thickness=12),
            line=dict(width=0.5, color="white"),
        ),
        text=node_names,
        textposition="top center",
        textfont=dict(size=7),
        hovertext=hover_text,
        hoverinfo="text",
    ))
    fig_grafo.update_layout(
        height=620,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(t=10, b=10, l=10, r=10),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
    )
    st.plotly_chart(fig_grafo, use_container_width=True)

    if n_com > 1:
        with st.expander("🧩 Tamanho das comunidades"):
            tamanhos = pd.Series(comunidades.values()).value_counts().sort_index()
            fig_com = px.bar(
                x=tamanhos.index.astype(str),
                y=tamanhos.values,
                labels={"x": "Comunidade", "y": "Número de autores"},
                color_discrete_sequence=["#01696f"],
            )
            fig_com.update_layout(margin=dict(t=10))
            st.plotly_chart(fig_com, use_container_width=True)
            st.caption(
                "Comunidades grandes geralmente representam grupos de pesquisa consolidados. "
                "Comunidades pequenas (2–3 nós) podem ser colaborações pontuais entre instituições."
            )

# ===== ABA 2: CENTRALIDADE ==================================================
with tab_centralidade:
    st.caption(
        "💡 **Como ler esta aba:** Betweenness alto = autor-ponte entre grupos. "
        "Eigenvector alto = colabora com autores influentes. "
        "Clustering alto = grupo coeso e fechado. "
        "Veja o glossário completo na barra lateral."
    )

    col_esq, col_dir = st.columns([1, 1])
    df_metrics = calcular_centralidades(G)

    with col_esq:
        st.subheader(f"🏆 Top {top_n} — Betweenness")
        st.dataframe(
            df_metrics.head(top_n)[
                ["node", "degree_raw", "betweenness", "eigenvector", "clustering"]
            ].rename(columns={
                "node": "Autor", "degree_raw": "Grau",
                "betweenness": "Betweenness", "eigenvector": "Eigenvector",
                "clustering": "Clustering",
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Betweenness": st.column_config.ProgressColumn(
                    "Betweenness",
                    help="Frequência nos caminhos mais curtos. Alto = ponte entre grupos.",
                    format="%.4f",
                    min_value=0,
                    max_value=float(df_metrics["betweenness"].max()),
                ),
                "Eigenvector": st.column_config.ProgressColumn(
                    "Eigenvector",
                    help="Influência ponderada pelos vizinhos. Alto = conectado a autores importantes.",
                    format="%.4f",
                    min_value=0,
                    max_value=float(df_metrics["eigenvector"].max()),
                ),
                "Clustering": st.column_config.ProgressColumn(
                    "Clustering",
                    help="Coesão do grupo. Alto = colaboradores também se colaboram entre si.",
                    format="%.3f",
                    min_value=0,
                    max_value=1.0,
                ),
            },
        )

    with col_dir:
        st.subheader("📊 Distribuição de Grau")
        graus = [d for _, d in G.degree()]
        fig_grau = px.histogram(
            x=graus, nbins=30,
            labels={"x": "Grau (nº de colaboradores)", "y": "Número de autores"},
            color_discrete_sequence=["#01696f"],
        )
        fig_grau.update_layout(showlegend=False, margin=dict(t=10))
        st.plotly_chart(fig_grau, use_container_width=True)
        st.caption(
            "Redes de co-autoria tipicamente seguem uma distribuição de lei de potência — "
            "poucos autores com muitos colaboradores, muitos com poucos."
        )

    st.divider()
    st.subheader("🔍 Betweenness vs Eigenvector")
    st.caption(
        "Autores no **canto superior direito** são os mais estratégicos: "
        "servem de ponte entre grupos *e* estão conectados a pesquisadores influentes. "
        "O tamanho do círculo representa o grau (nº de colaboradores)."
    )
    fig_scatter = px.scatter(
        df_metrics.head(100),
        x="eigenvector",
        y="betweenness",
        size="degree_raw",
        hover_name="node",
        size_max=30,
        color="betweenness",
        color_continuous_scale="Teal",
        labels={
            "eigenvector": "Eigenvector (influência dos vizinhos)",
            "betweenness": "Betweenness (ponte entre grupos)",
        },
    )
    fig_scatter.update_layout(margin=dict(t=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ===== ABA 3: EDA ===========================================================
with tab_eda:
    col1, col2 = st.columns(2)

    anos = [w.get("publication_year") for w in works if w.get("publication_year")]
    with col1:
        st.subheader("📅 Publicações por Ano")
        fig_ano = px.bar(
            x=sorted(set(anos)),
            y=[anos.count(a) for a in sorted(set(anos))],
            labels={"x": "Ano", "y": "Papers"},
            color_discrete_sequence=["#01696f"],
        )
        fig_ano.update_layout(margin=dict(t=10))
        st.plotly_chart(fig_ano, use_container_width=True)

    oa = [w.get("open_access", {}).get("oa_status", "unknown") for w in works]
    with col2:
        st.subheader("🔓 Status Open Access")
        oa_counts = pd.Series(Counter(oa)).sort_values(ascending=False)
        fig_oa = px.pie(
            names=oa_counts.index,
            values=oa_counts.values,
            color_discrete_sequence=px.colors.sequential.Teal,
            hole=0.4,
        )
        fig_oa.update_layout(margin=dict(t=10))
        st.plotly_chart(fig_oa, use_container_width=True)

    col3, col4 = st.columns(2)
    conceitos_todos = [
        c["display_name"]
        for w in works
        for c in w.get("concepts", [])[:3]
        if c.get("display_name")
    ]
    top_conceitos = pd.Series(Counter(conceitos_todos)).nlargest(20)

    with col3:
        st.subheader("🧠 Top 20 Conceitos")
        fig_conc = px.bar(
            x=top_conceitos.values,
            y=top_conceitos.index,
            orientation="h",
            labels={"x": "Ocorrências", "y": ""},
            color_discrete_sequence=["#4f98a3"],
        )
        fig_conc.update_layout(margin=dict(t=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_conc, use_container_width=True)

    autores_todos = [
        a["author"]["display_name"]
        for w in works
        for a in w.get("authorships", [])
        if a.get("author") and a["author"].get("display_name")
    ]
    top_autores = pd.Series(Counter(autores_todos)).nlargest(20)

    with col4:
        st.subheader("👤 Top 20 Autores")
        fig_aut = px.bar(
            x=top_autores.values,
            y=top_autores.index,
            orientation="h",
            labels={"x": "Papers", "y": ""},
            color_discrete_sequence=["#01696f"],
        )
        fig_aut.update_layout(margin=dict(t=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_aut, use_container_width=True)

# ===== ABA 4: TOP PAPERS ====================================================
with tab_papers:
    st.subheader("📚 Papers Mais Citados")

    df_papers = pd.DataFrame([{
        "Título": (w.get("title") or "N/A")[:90],
        "Ano": w.get("publication_year"),
        "Citações": w.get("cited_by_count", 0),
        "OA": w.get("open_access", {}).get("oa_status", "?"),
        "URL": (w.get("primary_location") or {}).get("landing_page_url") or "",
    } for w in works])

    col_f1, col_f2 = st.columns(2)
    ano_min, ano_max = int(df_papers["Ano"].min()), int(df_papers["Ano"].max())
    with col_f1:
        intervalo = st.slider("Intervalo de anos", ano_min, ano_max, (ano_min, ano_max))
    with col_f2:
        status_oa = st.multiselect(
            "Status Open Access",
            options=df_papers["OA"].unique().tolist(),
            default=df_papers["OA"].unique().tolist(),
        )

    df_filtrado = df_papers[
        df_papers["Ano"].between(*intervalo) &
        df_papers["OA"].isin(status_oa)
    ].sort_values("Citações", ascending=False)

    st.caption(f"{len(df_filtrado):,} papers no filtro atual")
    st.dataframe(
        df_filtrado.drop(columns=["URL"]).head(50),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("📈 Citações ao Longo do Tempo")
    fig_cit = px.scatter(
        df_filtrado,
        x="Ano",
        y="Citações",
        hover_name="Título",
        color="OA",
        size="Citações",
        size_max=40,
        color_discrete_sequence=_OA_PALETTE,
        labels={"Ano": "Ano de Publicação"},
    )
    fig_cit.update_layout(margin=dict(t=10))
    st.plotly_chart(fig_cit, use_container_width=True)
