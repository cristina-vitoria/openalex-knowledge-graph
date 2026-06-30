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
    "UFMS":    "https://ror.org/0366d2847",
    "USP":     "https://ror.org/036rp1748",
    "UNICAMP": "https://ror.org/04wffgt70",
    "UFRJ":    "https://ror.org/03490as77",
}

# IDs de "field" do OpenAlex (segundo nível da hierarquia domain/field/subfield/topic).
# 17 = Computer Science. Para confirmar ou achar outros, consulte:
# https://api.openalex.org/topics?search=computer science&select=id,display_name,field
FIELD_ID = {
    "Computer Science": 17,
}


def buscar_works(
    instituicao_ror: str,
    ano_inicio: int = 2018,
    ano_fim: int = 2026,
    field_id: int = FIELD_ID["Computer Science"],
    apenas_topico_primario: bool = False,
    limite: int = 1000,
) -> list:
    """
    Busca publicações de uma instituição filtradas por field (área) e período.

    Args:
        instituicao_ror: URL ROR da instituição.
        ano_inicio: Ano mínimo de publicação.
        ano_fim: Ano máximo de publicação.
        field_id: ID numérico do field do OpenAlex (default 17 = Computer Science).
        apenas_topico_primario: Se True, filtra por `primary_topic.field.id`
            (mais restrito: só considera o tópico principal do work). Se False,
            filtra por `topics.field.id` (mais abrangente: basta o field aparecer
            entre os tópicos secundários do work também).
        limite: Número máximo de resultados.

    Returns:
        Lista de dicts com os campos selecionados.
    """
    campo_filtro = "primary_topic" if apenas_topico_primario else "topics"

    q = (
        Works()
        .filter(
            authorships={"institutions": {"ror": instituicao_ror}},
            publication_year=f"{ano_inicio}-{ano_fim}",
        )
        .filter(**{campo_filtro: {"field": {"id": field_id}}})
        .select([
            "id", "title", "publication_year",
            "authorships", "concepts", "topics",
            "cited_by_count", "primary_location",
            "open_access",
        ])
    )

    resultados = []
    for pagina in tqdm(
        q.paginate(per_page=200, n_max=limite),
        desc=f"Coletando papers (field {field_id})",
    ):
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
        field_id=FIELD_ID["Computer Science"],
        limite=500,
    )
    salvar_raw(works, "works_ufms_cs")