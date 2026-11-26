import os
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.busca import carregar_exemplos
from app.materiais import (
    MAXIMO_ARQUIVOS_ENVIADOS,
    MaterialInvalido,
    TAMANHO_MAXIMO_ARQUIVO,
    adicionar_material,
)
from app.limitador import LimitadorDeUso
from app.resposta import responder
from app.sessoes import GerenciadorDeSessoes

PASTA_ESTATICA = Path(__file__).resolve().parent / "static"
NOME_COOKIE = "sessao"
VALIDADE_SESSAO = 3600

sessoes = GerenciadorDeSessoes(
    criar_indice=lambda: carregar_exemplos().copiar(),
    validade_segundos=VALIDADE_SESSAO,
)



def inteiro_do_ambiente(nome, padrao):
    try:
        valor = int(os.getenv(nome, ""))
        return valor if valor > 0 else padrao
    except ValueError:
        return padrao


LIMITE_PERGUNTAS_POR_MINUTO = inteiro_do_ambiente("LIMITE_PERGUNTAS_POR_MINUTO", 6)
LIMITE_ENVIOS_POR_HORA = inteiro_do_ambiente("LIMITE_ENVIOS_POR_HORA", 10)
LIMITE_GERAL_POR_HORA = inteiro_do_ambiente("LIMITE_GERAL_POR_HORA", 300)

limite_perguntas = LimitadorDeUso(LIMITE_PERGUNTAS_POR_MINUTO, 60)
limite_envios = LimitadorDeUso(LIMITE_ENVIOS_POR_HORA, 3600)
limite_geral = LimitadorDeUso(LIMITE_GERAL_POR_HORA, 3600)

app = FastAPI(title="Estudaí")
app.mount("/static", StaticFiles(directory=PASTA_ESTATICA), name="static")


class Pergunta(BaseModel):
    texto: str = Field(min_length=3, max_length=500)


def sessao_atual(requisicao: Request, resposta: Response):
    try:
        sid, indice, nova = sessoes.obter_ou_criar(requisicao.cookies.get(NOME_COOKIE))
    except Exception as erro:
        print(f"Falha ao criar sessão: {type(erro).__name__}")
        raise HTTPException(status_code=503, detail="Serviço indisponível no momento.")
    if nova:
        https = requisicao.url.scheme == "https" or requisicao.headers.get("x-forwarded-proto") == "https"
        resposta.set_cookie(
            NOME_COOKIE,
            sid,
            max_age=VALIDADE_SESSAO,
            httponly=True,
            samesite="lax",
            secure=https,
        )
    return indice


def identificar_visitante(requisicao: Request):
    encaminhado = requisicao.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return requisicao.client.host if requisicao.client else "desconhecido"


def aplicar_limite(limitador, requisicao: Request):
    liberado, espera = limite_geral.tentar("geral")
    if liberado:
        liberado, espera = limitador.tentar(identificar_visitante(requisicao))
    if not liberado:
        segundos = max(1, int(espera) + 1)
        raise HTTPException(
            status_code=429,
            detail=f"Muitas requisições. Tente de novo em {segundos} segundos.",
            headers={"Retry-After": str(segundos)},
        )


def resumo(indice):
    return {
        "materiais": indice.fontes(),
        "limites": {
            "arquivos": MAXIMO_ARQUIVOS_ENVIADOS,
            "tamanho_mb": TAMANHO_MAXIMO_ARQUIVO // (1024 * 1024),
        },
    }


@app.get("/")
def pagina_inicial():
    return FileResponse(PASTA_ESTATICA / "index.html")


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.get("/materiais")
def listar_materiais(indice=Depends(sessao_atual)):
    return resumo(indice)


@app.post("/materiais", status_code=201)
def enviar_material(requisicao: Request, arquivo: UploadFile, indice=Depends(sessao_atual)):
    aplicar_limite(limite_envios, requisicao)
    tamanho = requisicao.headers.get("content-length", "")
    if tamanho.isdigit() and int(tamanho) > TAMANHO_MAXIMO_ARQUIVO + 200_000:
        raise HTTPException(status_code=413, detail="O arquivo passa de 2 MB.")
    dados = arquivo.file.read(TAMANHO_MAXIMO_ARQUIVO + 1)
    try:
        adicionar_material(indice, arquivo.filename or "", dados)
    except MaterialInvalido as erro:
        raise HTTPException(status_code=erro.codigo, detail=erro.mensagem)
    except Exception as erro:
        print(f"Falha ao processar material: {type(erro).__name__}")
        raise HTTPException(status_code=503, detail="Não foi possível processar o arquivo agora.")
    return resumo(indice)


@app.delete("/materiais/{nome}")
def remover_material(nome: str, indice=Depends(sessao_atual)):
    if not indice.remover_fonte(nome):
        raise HTTPException(status_code=404, detail="Material não encontrado.")
    return resumo(indice)


@app.post("/perguntar")
def perguntar(requisicao: Request, pergunta: Pergunta, indice=Depends(sessao_atual)):
    aplicar_limite(limite_perguntas, requisicao)
    texto = pergunta.texto.strip()
    if len(texto) < 3:
        raise HTTPException(status_code=422, detail="Escreva uma pergunta.")
    try:
        return responder(texto, indice)
    except Exception as erro:
        print(f"Falha ao responder: {type(erro).__name__}")
        raise HTTPException(status_code=503, detail="Serviço indisponível no momento.")