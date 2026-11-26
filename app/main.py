"""API do Estudaí."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.resposta import responder

app = FastAPI(title="Estudaí")

class Pergunta(BaseModel):
    texto: str = Field(min_length = 3, max_length = 500)


@app.get("/saude")

def saude():
    return {"status": "ok"}


@app.post("/perguntar")

def perguntar(pergunta: Pergunta):
    texto = pergunta.texto.strip()
    if len(texto) < 3:
        raise HTTPException(status_code=422, detail="Escreva uma pergunta.")
    try:
        return responder(texto)
    except Exception as erro:
        print(f"Falha ao responder: {type(erro).__name__}")
        raise HTTPException(status_code=503,detail="Serviço indisponível no momento.")
    