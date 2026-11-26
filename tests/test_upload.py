import numpy as np
import pytest
from app.indice import IndiceDeMateriais
from app.materiais import MaterialInvalido, adicionar_material, MAXIMO_ARQUIVOS_ENVIADOS, MAXIMO_TRECHOS_POR_SESSAO


def gerar_falso(textos, tipo):
    vetores = []
    for texto in textos:
        v = np.zeros(32)
        for palavra in texto.lower().split():
            v[hash(palavra) % 32] += 1
        vetores.append(v / (np.linalg.norm(v) or 1))
    return np.array(vetores)


TEXTO = "Resumo\n1. Um\nprimeira parte\n2. Dois\nsegunda parte\n".encode()


def test_adicionar_material_entra_no_indice():
    indice = IndiceDeMateriais(gerar_falso)
    nome = adicionar_material(indice, "aula.txt", TEXTO)
    assert nome == "aula.txt"
    fontes = indice.fontes()
    assert fontes == [{"nome": "aula.txt", "trechos": 2, "exemplo": False}]


def test_nome_repetido_e_recusado():
    indice = IndiceDeMateriais(gerar_falso)
    adicionar_material(indice, "aula.txt", TEXTO)
    with pytest.raises(MaterialInvalido) as erro:
        adicionar_material(indice, "aula.txt", TEXTO)
    assert erro.value.codigo == 409


def test_limite_de_arquivos_enviados():
    indice = IndiceDeMateriais(gerar_falso)
    for n in range(MAXIMO_ARQUIVOS_ENVIADOS):
        adicionar_material(indice, f"aula{n}.txt", TEXTO)
    with pytest.raises(MaterialInvalido) as erro:
        adicionar_material(indice, "extra.txt", TEXTO)
    assert erro.value.codigo == 429


def test_arquivos_de_exemplo_nao_contam_no_limite_de_arquivos():
    indice = IndiceDeMateriais(gerar_falso)
    indice.adicionar_trechos([{"fonte": "exemplo.pdf", "trecho": 1, "texto": "algo", "exemplo": True}])
    for n in range(MAXIMO_ARQUIVOS_ENVIADOS):
        adicionar_material(indice, f"aula{n}.txt", TEXTO)
    assert len(indice.fontes()) == MAXIMO_ARQUIVOS_ENVIADOS + 1


def test_limite_de_trechos_da_sessao():
    indice = IndiceDeMateriais(gerar_falso)
    indice.adicionar_trechos([{"fonte": "grande.pdf", "trecho": n, "texto": f"t{n}", "exemplo": True} for n in range(MAXIMO_TRECHOS_POR_SESSAO - 1)])
    with pytest.raises(MaterialInvalido) as erro:
        adicionar_material(indice, "aula.txt", TEXTO)
    assert erro.value.codigo == 413


def test_falha_ao_gerar_embeddings_nao_deixa_arquivo_pela_metade():
    def gerar_com_falha(textos, tipo):
        raise RuntimeError("API fora do ar")
    indice = IndiceDeMateriais(gerar_com_falha)
    with pytest.raises(RuntimeError):
        adicionar_material(indice, "aula.txt", TEXTO)
    assert indice.fontes() == []