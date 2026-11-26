import io
import pytest
from pypdf import PdfWriter
from app.materiais import MaterialInvalido, nome_seguro, preparar_trechos, TAMANHO_MAXIMO_ARQUIVO, TRECHOS_MAXIMOS_POR_ARQUIVO


def pdf_em_branco():
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    saida = io.BytesIO()
    escritor.write(saida)
    return saida.getvalue()


def test_txt_com_secoes_vira_um_trecho_por_secao():
    texto = "Resumo\n1. Um\nprimeira parte\n2. Dois\nsegunda parte\n".encode()
    nome, trechos = preparar_trechos("resumo.txt", texto)
    assert nome == "resumo.txt"
    assert len(trechos) == 2
    assert trechos[0]["fonte"] == "resumo.txt" and trechos[0]["trecho"] == 1


def test_txt_sem_secoes_usa_corte_por_tamanho():
    _, trechos = preparar_trechos("livre.txt", ("palavra " * 300).encode())
    assert len(trechos) >= 2


def test_txt_latin1_nao_quebra():
    _, trechos = preparar_trechos("antigo.txt", "ação e reação".encode("latin-1"))
    assert "ação" in trechos[0]["texto"]


def test_extensao_invalida():
    with pytest.raises(MaterialInvalido) as erro:
        preparar_trechos("virus.exe", b"conteudo")
    assert erro.value.codigo == 400


def test_arquivo_grande_demais():
    with pytest.raises(MaterialInvalido) as erro:
        preparar_trechos("grande.txt", b"a" * (TAMANHO_MAXIMO_ARQUIVO + 1))
    assert erro.value.codigo == 413


def test_arquivo_vazio():
    with pytest.raises(MaterialInvalido):
        preparar_trechos("vazio.txt", b"")


def test_texto_so_com_espacos():
    with pytest.raises(MaterialInvalido) as erro:
        preparar_trechos("branco.txt", b"   \n  \n ")
    assert erro.value.codigo == 422


def test_pdf_falso():
    with pytest.raises(MaterialInvalido):
        preparar_trechos("falso.pdf", b"isto nao e um pdf")


def test_pdf_sem_texto_e_recusado():
    with pytest.raises(MaterialInvalido) as erro:
        preparar_trechos("escaneado.pdf", pdf_em_branco())
    assert erro.value.codigo == 422


def test_arquivo_longo_demais():
    texto = "\n".join(f"{n}. Secao\ntexto da secao {n}" for n in range(1, TRECHOS_MAXIMOS_POR_ARQUIVO + 5))
    with pytest.raises(MaterialInvalido) as erro:
        preparar_trechos("enorme.txt", texto.encode())
    assert erro.value.codigo == 413


def test_nome_seguro_remove_caminho_e_caracteres_estranhos():
    assert nome_seguro("../../etc/passwd") == "passwd"
    assert nome_seguro("C:\\Users\\a\\aula 1.pdf") == "aula 1.pdf"
    assert nome_seguro("<script>.txt") == "_script_.txt"
    assert len(nome_seguro("a" * 200 + ".pdf")) <= 80
    assert nome_seguro("a" * 200 + ".pdf").endswith(".pdf")