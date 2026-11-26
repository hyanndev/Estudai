"""Testes da API do Estudaí."""
from fastapi.testclient import TestClient  
from app import main  

cliente = TestClient(main.app)  


def test_saude(): 
    r = cliente.get("/saude")  
    assert r.status_code == 200  
    assert r.json() == {"status": "ok"} 


def test_perguntar_valida(monkeypatch):  
    monkeypatch.setattr(main, "responder", lambda texto: {"resposta": "ok", "fontes": []})  
    r = cliente.post("/perguntar", json={"texto": "O que é TCP?"}) 
    assert r.status_code == 200  
    assert r.json()["resposta"] == "ok" 


def test_pergunta_curta_demais(): 
    r = cliente.post("/perguntar", json={"texto": "a"}) 
    assert r.status_code == 422 

def test_pergunta_em_branco(): 
    r = cliente.post("/perguntar", json={"texto": "     "})  
    assert r.status_code == 422  


def test_falha_interna_vira_503(monkeypatch): 
    def quebra(texto):  
        raise RuntimeError("falhou")  
    monkeypatch.setattr(main, "responder", quebra) 
    r = cliente.post("/perguntar", json={"texto": "O que é TCP?"})  
    assert r.status_code == 503  
    assert "falhou" not in r.text  