"""
graph.py
Construção dos grafos de co-autoria e co-conceito a partir dos dados do OpenAlex.
"""

import networkx as nx


def construir_grafo_coautoria(works: list) -> nx.Graph:
    """
    Constrói grafo não-dirigido de co-autoria.
    Nós = autores; arestas = co-autoria em ao menos 1 paper.
    Peso da aresta = número de papers em comum.
    """
    G = nx.Graph()

    for work in works:
        authorships = work.get("authorships", [])
        autores = [
            a["author"]["display_name"]
            for a in authorships
            if a.get("author") and a["author"].get("display_name")
        ]
        autores_ids = [
            a["author"]["id"]
            for a in authorships
            if a.get("author") and a["author"].get("id")
        ]

        for i, nome in enumerate(autores):
            if not G.has_node(nome):
                opx_id = autores_ids[i] if i < len(autores_ids) else None
                G.add_node(nome, openalex_id=opx_id)

        for i, a1 in enumerate(autores):
            for a2 in autores[i + 1:]:
                if G.has_edge(a1, a2):
                    G[a1][a2]["weight"] += 1
                    G[a1][a2]["papers"].append(work.get("title", ""))
                else:
                    G.add_edge(a1, a2, weight=1, papers=[work.get("title", "")])

    return G


def construir_grafo_conceito(works: list, top_n: int = 5) -> nx.Graph:
    """
    Constrói grafo não-dirigido de co-conceito.
    Nós = conceitos; arestas = aparição conjunta no mesmo paper.
    Peso da aresta = número de co-ocorrências.
    """
    G = nx.Graph()

    for work in works:
        conceitos = [
            c["display_name"]
            for c in work.get("concepts", [])[:top_n]
            if c.get("display_name")
        ]

        for i, c1 in enumerate(conceitos):
            for c2 in conceitos[i + 1:]:
                if G.has_edge(c1, c2):
                    G[c1][c2]["weight"] += 1
                else:
                    G.add_edge(c1, c2, weight=1)

    return G


def filtrar_grafo(G: nx.Graph, min_degree: int = 2) -> nx.Graph:
    """Remove nós com grau menor que min_degree."""
    nos_validos = [n for n, d in G.degree() if d >= min_degree]
    return G.subgraph(nos_validos).copy()


def maior_componente(G: nx.Graph) -> nx.Graph:
    """Retorna o maior componente conexo do grafo."""
    componente = max(nx.connected_components(G), key=len)
    return G.subgraph(componente).copy()
