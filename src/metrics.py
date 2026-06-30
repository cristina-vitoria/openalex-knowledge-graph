"""
metrics.py
Cálculo de métricas de análise de redes complexas.
"""

import pandas as pd
import networkx as nx

try:
    from community import best_partition  # python-louvain
except ImportError:
    best_partition = None


def calcular_centralidades(G: nx.Graph) -> pd.DataFrame:
    """
    Calcula as principais métricas de centralidade para cada nó.

    Returns:
        DataFrame com colunas: node, degree, betweenness, eigenvector, clustering.
    """
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)

    try:
        eigenvector = nx.eigenvector_centrality(G, weight="weight", max_iter=500)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {n: 0.0 for n in G.nodes()}

    clustering = nx.clustering(G, weight="weight")

    df = pd.DataFrame({
        "node": list(G.nodes()),
        "degree": [degree[n] for n in G.nodes()],
        "betweenness": [betweenness[n] for n in G.nodes()],
        "eigenvector": [eigenvector[n] for n in G.nodes()],
        "clustering": [clustering[n] for n in G.nodes()],
        "degree_raw": [G.degree(n) for n in G.nodes()],
    })

    return df.sort_values("betweenness", ascending=False).reset_index(drop=True)


def detectar_comunidades(G: nx.Graph) -> dict:
    """
    Detecta comunidades usando o algoritmo de Louvain.
    Requer: pip install python-louvain
    """
    if best_partition is None:
        raise ImportError("Instale python-louvain: pip install python-louvain")
    return best_partition(G, weight="weight")


def resumo_rede(G: nx.Graph) -> dict:
    """Retorna um resumo estatístico do grafo."""
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "avg_degree": round(sum(d for _, d in G.degree()) / G.number_of_nodes(), 2),
        "components": nx.number_connected_components(G),
        "avg_clustering": round(nx.average_clustering(G, weight="weight"), 4),
        "largest_component_size": len(max(nx.connected_components(G), key=len)),
    }
