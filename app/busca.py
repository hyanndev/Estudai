"""Embeddings e busca por significado."""
import json  
import os  
import numpy as np  
from dotenv import load_dotenv  
from google import genai  
from google.genai import types  
from app.documentos import RAIZ, carregar_materiais  

load_dotenv()  

MODELO_EMBEDDING = "gemini-embedding-001" 
DIMENSOES = 768 
CACHE = RAIZ / "cache" / "embeddings.json"  


def criar_cliente():
    """Cria o cliente do Gemini com a chave do .env."""
    chave = os.getenv("GEMINI_API_KEY")  
    if not chave:  
        raise RuntimeError("Defina GEMINI_API_KEY no arquivo .env")  
    return genai.Client(api_key=chave)  


def normalizar(matriz):
    """Deixa cada vetor com tamanho 1, para o produto virar similaridade."""
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)  
    return matriz / normas 


def gerar_embeddings(textos, tipo):
    """Transforma uma lista de textos em vetores."""
    cliente = criar_cliente()  
    vetores = []  
    for i in range(0, len(textos), 50):  
        lote = textos[i:i + 50]  
        resposta = cliente.models.embed_content(  
            model=MODELO_EMBEDDING,  
            contents=lote,
            config=types.EmbedContentConfig(task_type=tipo, output_dimensionality=DIMENSOES),  
        )
        vetores.extend(e.values for e in resposta.embeddings)  
    return normalizar(np.array(vetores, dtype=float))  


def construir_indice():
    """Lê os materiais, calcula os vetores e salva no cache."""
    registros = carregar_materiais() 
    textos = [r["texto"] for r in registros]  
    vetores = gerar_embeddings(textos, "RETRIEVAL_DOCUMENT")  
    CACHE.parent.mkdir(exist_ok=True)  
    CACHE.write_text(json.dumps({"registros": registros, "vetores": vetores.tolist()}), encoding="utf-8")  # salva tudo
    return registros, vetores  


def carregar_indice():
    """Usa o cache se existir; senão, constrói o índice."""
    if CACHE.exists():  
        dados = json.loads(CACHE.read_text(encoding="utf-8"))  # lê o arquivo
        return dados["registros"], np.array(dados["vetores"])  # devolve trechos e vetores
    return construir_indice()  


def buscar(pergunta, k=3):
    """Devolve os k trechos mais parecidos com a pergunta."""
    registros, vetores = carregar_indice()  
    consulta = gerar_embeddings([pergunta], "RETRIEVAL_QUERY")[0]  
    notas = vetores @ consulta  
    melhores = np.argsort(notas)[::-1][:k]  
    return [{**registros[i], "nota": round(float(notas[i]), 3)} for i in melhores]  


if __name__ == "__main__":  
    import sys  
    pergunta = " ".join(sys.argv[1:]) or "Qual a diferença entre TCP e UDP?"  
    for r in buscar(pergunta): 
        print(f"[{r['nota']}] {r['fonte']} (trecho {r['trecho']})")  
        print(r["texto"][:200], "...\n") 