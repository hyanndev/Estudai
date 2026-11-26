import numpy as np
from app.indice import IndiceDeMateriais


def gerar_falso(textos, tipo):
    vetores = []
    for texto in textos:
        v = np.zeros(32)
        for palavra in texto.lower().split():
            v[hash(palavra) % 32] += 1
        vetores.append(v / (np.linalg.norm(v) or 1))
    return np.array(vetores)


def registros(fonte, textos, exemplo=False):
    return [{"fonte": fonte, "trecho": i, "texto": t, "exemplo": exemplo} for i, t in enumerate(textos, start=1)]


def criar():
    indice = IndiceDeMateriais(gerar_falso)
    indice.adicionar_trechos(registros("redes.txt", ["tcp confirma recebimento dos dados", "dns traduz nomes em enderecos ip"]))
    indice.adicionar_trechos(registros("agil.txt", ["scrum usa sprints curtas", "kanban limita o trabalho em andamento"], exemplo=True))
    return indice


def test_busca_devolve_o_trecho_mais_parecido():
    resultado = criar().buscar("dns traduz nomes", k=1)
    assert resultado[0]["fonte"] == "redes.txt"
    assert resultado[0]["trecho"] == 2


def test_indice_vazio_nao_devolve_nada():
    assert IndiceDeMateriais(gerar_falso).buscar("qualquer coisa") == []


def test_fontes_conta_trechos_e_marca_exemplo():
    fontes = {f["nome"]: f for f in criar().fontes()}
    assert fontes["redes.txt"]["trechos"] == 2
    assert fontes["redes.txt"]["exemplo"] is False
    assert fontes["agil.txt"]["exemplo"] is True


def test_remover_fonte():
    indice = criar()
    assert indice.remover_fonte("redes.txt") is True
    assert indice.total_trechos() == 2
    assert all(r["fonte"] == "agil.txt" for r in indice.buscar("dns", k=5))
    assert indice.remover_fonte("nao_existe.txt") is False


def test_remover_tudo_deixa_indice_vazio():
    indice = criar()
    indice.remover_fonte("redes.txt")
    indice.remover_fonte("agil.txt")
    assert indice.buscar("dns") == []


def test_copia_e_independente():
    original = criar()
    copia = original.copiar()
    copia.adicionar_trechos(registros("novo.txt", ["algo novo"]))
    copia.remover_fonte("redes.txt")
    assert original.total_trechos() == 4
    assert copia.total_trechos() == 3