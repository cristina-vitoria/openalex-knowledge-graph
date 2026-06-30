"""
fetch.py
Funções para coleta de dados da API OpenAlex via PyAlex.
"""

import json
from pathlib import Path
from tqdm import tqdm
import pyalex
from pyalex import Works

pyalex.config.email = "seu@email.com"  # polite pool -> prioridade na fila

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ROR IDs de grandes universidades brasileiras
INSTITUICAO_ROR = {
    "UFMS":    "https://ror.org/00mj4fy29",
    "USP":     "https://ror.org/036rp1748",
    "UNICAMP": "https://ror.org/04wffgt70",
    "UFRJ":    "https://ror.org/03490as77",
}


def buscar_works(
    instituicao_ror: str,
    ano_inicio: int = 2018,
    ano_fim: int = 2026,
    conceito: str = "Computer Science",
    limite: int = 1000,
) -> list:
    """
    Busca publicações de uma instituição filtradas por conceito e período.

    Returns:
        Lista de dicts com os campos selecionados.
    """
    query = (
        Works()
        .filter(
            institutions={"ror": instituicao_ror},
            publication_year=f"{ano_inicio}-{ano_fim}",
        )
        .search_filter(concepts={"display_name": conceito})
        .select([
            "id", "title", "publication_year",
            "authorships", "concepts",
            "cited_by_count", "primary_location",
            "open_access",
        ])
    )

    resultados = []
    for pagina in tqdm(query.paginate(per_page=200, n_max=limite), desc="Coletando papers"):
        resultados.extend(pagina)

    return resultados


def salvar_raw(dados: list, nome_arquivo: str) -> Path:
    """Salva dados brutos em JSON."""
    caminho = RAW_DIR / f"{nome_arquivo}.json"
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(dados)} records -> {caminho}")
    return caminho


def carregar_raw(nome_arquivo: str) -> list:
    """Carrega dados brutos do JSON."""
    caminho = RAW_DIR / f"{nome_arquivo}.json"
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    works = buscar_works(
        instituicao_ror=INSTITUICAO_ROR["UFMS"],
        ano_inicio=2018,
        limite=500,
    )
    salvar_raw(works, "works_ufms_cs")
