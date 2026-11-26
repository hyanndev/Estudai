import os
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSOES = 768
TAMANHO_LOTE = 50


def criar_cliente():
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("Defina GEMINI_API_KEY no arquivo .env")
    return genai.Client(api_key=chave)


def normalizar(matriz):
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    return matriz / normas


def gerar_embeddings(textos, tipo):
    cliente = criar_cliente()
    vetores = []
    for i in range(0, len(textos), TAMANHO_LOTE):
        lote = textos[i:i + TAMANHO_LOTE]
        resposta = cliente.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=lote,
            config=types.EmbedContentConfig(task_type=tipo, output_dimensionality=DIMENSOES),
        )
        vetores.extend(e.values for e in resposta.embeddings)
    return normalizar(np.array(vetores, dtype=float))