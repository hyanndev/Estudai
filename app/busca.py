import json
import numpy as np
from app.documentos import RAIZ, carregar_materiais
from app.embeddings import gerar_embeddings
from app.indice import IndiceDeMateriais

CACHE = RAIZ / "cache" / "embeddings.json"

_exemplos = None


def carregar_exemplos():
    global _exemplos
    if _exemplos is not None:
        return _exemplos
    indice = IndiceDeMateriais(gerar_embeddings)
    if CACHE.exists():
        dados = json.loads(CACHE.read_text(encoding="utf-8"))
        indice.carregar(dados["registros"], np.array(dados["vetores"]))
    else:
        indice.adicionar_trechos(carregar_materiais())
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(
            json.dumps({"registros": indice.registros, "vetores": indice.vetores.tolist()}),
            encoding="utf-8",
        )
    for registro in indice.registros:
        registro["exemplo"] = True
    _exemplos = indice
    return _exemplos


def buscar(pergunta, k=3):
    return carregar_exemplos().buscar(pergunta, k)


if __name__ == "__main__":
    import sys
    pergunta = " ".join(sys.argv[1:]) or "Qual a diferença entre TCP e UDP?"
    for r in buscar(pergunta):
        print(f"[{r['nota']}] {r['fonte']} (trecho {r['trecho']})")
        print(r["texto"][:200], "...\n")