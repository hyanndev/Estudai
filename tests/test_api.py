import numpy as np
import pytest
from fastapi.testclient import TestClient
from app import main
from app.indice import IndiceDeMateriais
from app.sessoes import GerenciadorDeSessoes

TEXTO = "Resumo\n1. Um\nprimeira parte\n2. Dois\nsegunda parte\n".encode()


def gerar_falso(textos, tipo):
    vetores = []
    for texto in textos:
        v = np.zeros(32)
        for palavra in texto.lower().split():
            v[hash(palavra) % 32] += 1
        vetores.append(v / (np.linalg.norm(v) or 1))
    return np.array(vetores)


@pytest.fixture(autouse=True)
def sessoes_falsas(monkeypatch):
    def criar():
        indice = IndiceDeMateriais(gerar_falso)
        indice.adicionar_trechos([{"fonte": "exemplo.txt", "trecho": 1, "texto": "texto de exemplo", "exemplo": True}])
        return indice
    monkeypatch.setattr(main, "sessoes", GerenciadorDeSessoes(criar_indice=criar))


def enviar(cliente, nome="aula.txt", conteudo=TEXTO):
    return cliente.post("/materiais", files={"arquivo": (nome, conteudo, "text/plain")})


def test_saude():
    r = TestClient(main.app).get("/saude")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_perguntar_valida(monkeypatch):
    monkeypatch.setattr(main, "responder", lambda texto, indice: {"resposta": "ok", "fontes": []})
    r = TestClient(main.app).post("/perguntar", json={"texto": "O que é TCP?"})
    assert r.status_code == 200
    assert r.json()["resposta"] == "ok"


def test_pergunta_curta_demais():
    r = TestClient(main.app).post("/perguntar", json={"texto": "a"})
    assert r.status_code == 422


def test_pergunta_em_branco():
    r = TestClient(main.app).post("/perguntar", json={"texto": "     "})
    assert r.status_code == 422


def test_falha_interna_vira_503(monkeypatch):
    def quebra(texto, indice):
        raise RuntimeError("falhou")
    monkeypatch.setattr(main, "responder", quebra)
    r = TestClient(main.app).post("/perguntar", json={"texto": "O que é TCP?"})
    assert r.status_code == 503
    assert "falhou" not in r.text


def test_primeira_visita_recebe_cookie_seguro():
    r = TestClient(main.app).get("/materiais")
    cabecalho = r.headers["set-cookie"].lower()
    assert "sessao=" in cabecalho
    assert "httponly" in cabecalho
    assert "samesite=lax" in cabecalho


def test_lista_comeca_com_os_exemplos():
    r = TestClient(main.app).get("/materiais")
    nomes = [m["nome"] for m in r.json()["materiais"]]
    assert nomes == ["exemplo.txt"]


def test_enviar_material():
    cliente = TestClient(main.app)
    r = enviar(cliente)
    assert r.status_code == 201
    nomes = [m["nome"] for m in r.json()["materiais"]]
    assert "aula.txt" in nomes
    assert [m["nome"] for m in cliente.get("/materiais").json()["materiais"]] == nomes


def test_tipo_invalido():
    r = enviar(TestClient(main.app), nome="virus.exe", conteudo=b"abc")
    assert r.status_code == 400


def test_nome_repetido():
    cliente = TestClient(main.app)
    enviar(cliente)
    assert enviar(cliente).status_code == 409


def test_arquivo_muito_grande():
    r = enviar(TestClient(main.app), conteudo=b"a" * (3 * 1024 * 1024))
    assert r.status_code == 413


def test_remover_material():
    cliente = TestClient(main.app)
    enviar(cliente)
    r = cliente.delete("/materiais/aula.txt")
    assert r.status_code == 200
    assert [m["nome"] for m in r.json()["materiais"]] == ["exemplo.txt"]
    assert cliente.delete("/materiais/aula.txt").status_code == 404


def test_cada_visitante_ve_so_os_seus_materiais():
    ana = TestClient(main.app)
    beto = TestClient(main.app)
    enviar(ana, nome="da_ana.txt")
    nomes_beto = [m["nome"] for m in beto.get("/materiais").json()["materiais"]]
    assert "da_ana.txt" not in nomes_beto


def test_pergunta_usa_os_materiais_da_sessao(monkeypatch):
    recebidos = {}

    def falso(texto, indice):
        recebidos["nomes"] = [f["nome"] for f in indice.fontes()]
        return {"resposta": "ok", "fontes": []}

    monkeypatch.setattr(main, "responder", falso)
    cliente = TestClient(main.app)
    enviar(cliente, nome="minha_aula.txt")
    cliente.post("/perguntar", json={"texto": "O que é TCP?"})
    assert "minha_aula.txt" in recebidos["nomes"]


def test_cookie_falso_nao_da_acesso_a_sessao_alheia():
    ana = TestClient(main.app)
    enviar(ana, nome="da_ana.txt")
    invasor = TestClient(main.app)
    invasor.cookies.set("sessao", "tentativa-de-adivinhar")
    nomes = [m["nome"] for m in invasor.get("/materiais").json()["materiais"]]
    assert "da_ana.txt" not in nomes