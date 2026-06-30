# 🔬 OpenAlex Knowledge Graph

> Mapeamento do conhecimento científico brasileiro através de grafos de co-autoria e co-conceito, usando dados abertos do [OpenAlex](https://openalex.org).

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.x-orange)](https://networkx.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow)](#)

---

## 📌 Problema

Como o conhecimento científico de instituições brasileiras está conectado? Quem são os pesquisadores que fazem ponte entre diferentes áreas? Quais comunidades temáticas emergem da literatura nacional?

Este projeto responde essas perguntas construindo e analisando grafos de co-autoria e co-conceito a partir de publicações coletadas via API do OpenAlex — um índice aberto com mais de 250 milhões de obras científicas.

---

## 📊 Dataset

| Atributo | Valor |
|---|---|
| Fonte | [OpenAlex API](https://docs.openalex.org) |
| Escopo | Publicações de instituições brasileiras (CS, 2018–2026) |
| Volume (estimado) | ~1.000 papers · ~1.500 autores · ~3.000 conceitos |
| Licença dos dados | CC0 (domínio público) |
| Custo de acesso | Gratuito, sem autenticação |

---

## 🗂️ Estrutura do Projeto

```
openalex-knowledge-graph/
├── data/
│   ├── raw/            # JSON bruto da API (ignorado pelo git)
│   └── processed/      # CSVs limpos e prontos para análise
├── notebooks/
│   ├── 01_coleta.ipynb       # Coleta via PyAlex
│   ├── 02_eda.ipynb          # Análise exploratória
│   ├── 03_grafo.ipynb        # Construção dos grafos
│   └── 04_analise.ipynb      # Métricas e comunidades
├── src/
│   ├── fetch.py        # Funções de coleta da API
│   ├── graph.py        # Construção e manipulação do grafo
│   └── metrics.py      # Cálculo de métricas de rede
├── app/
│   └── dashboard.py    # Dashboard Streamlit
├── reports/
│   └── figures/        # Visualizações exportadas
├── requirements.txt
└── README.md
```

---

## 🚀 Como Rodar

### 1. Clone o repositório
```bash
git clone https://github.com/cristina-vitoria/openalex-knowledge-graph.git
cd openalex-knowledge-graph
```

### 2. Crie o ambiente virtual e instale as dependências
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

### 3. Execute os notebooks em ordem
```bash
jupyter lab notebooks/
```

### 4. Rode o dashboard
```bash
streamlit run app/dashboard.py
```

---

## 🔍 Análises

- [ ] EDA: distribuição temporal, top autores, top conceitos
- [ ] Grafo de co-autoria (autores como nós, co-autoria como arestas)
- [ ] Grafo de co-conceito (temas como nós, co-ocorrência como arestas)
- [ ] Métricas: degree, betweenness, eigenvector centrality
- [ ] Detecção de comunidades (algoritmo de Louvain)
- [ ] Evolução temporal da rede
- [ ] Dashboard interativo com Streamlit

---

## 💡 Principais Insights

> *Seção a ser preenchida após conclusão das análises.*

---

## 🛠️ Stack

| Ferramenta | Uso |
|---|---|
| `pyalex` | Coleta de dados via API OpenAlex |
| `pandas` | Manipulação de dados tabulares |
| `networkx` | Construção e análise do grafo |
| `python-louvain` | Detecção de comunidades |
| `pyvis` | Visualização interativa do grafo |
| `plotly` | Gráficos EDA |
| `streamlit` | Dashboard web |

---

## 📄 Licença

MIT © [Vitória Cristina](https://github.com/cristina-vitoria)
