import io
import re
from pypdf import PdfReader
from app.documentos import dividir_por_secoes

TAMANHO_MAXIMO_ARQUIVO = 2 * 1024 * 1024
PAGINAS_MAXIMAS = 40
TRECHOS_MAXIMOS_POR_ARQUIVO = 120
EXTENSOES = (".txt", ".pdf")


class MaterialInvalido(Exception):
    def __init__(self, mensagem, codigo=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo


def nome_seguro(nome):
    base = re.split(r"[\\/]", nome or "")[-1]
    base = re.sub(r"[^\w.\- ]", "_", base).strip(" .")
    if len(base) > 80:
        ponto = base.rfind(".")
        extensao = base[ponto:] if ponto != -1 else ""
        base = base[:80 - len(extensao)] + extensao
    return base


def extrair_texto(nome, dados):
    if nome.lower().endswith(".pdf"):
        if not dados.startswith(b"%PDF-"):
            raise MaterialInvalido("Este arquivo não é um PDF válido.")
        try:
            leitor = PdfReader(io.BytesIO(dados))
            if leitor.is_encrypted:
                raise MaterialInvalido("PDFs protegidos por senha não são aceitos.")
            if len(leitor.pages) > PAGINAS_MAXIMAS:
                raise MaterialInvalido(f"O PDF tem mais de {PAGINAS_MAXIMAS} páginas.", 413)
            return "\n".join((p.extract_text() or "") for p in leitor.pages)
        except MaterialInvalido:
            raise
        except Exception:
            raise MaterialInvalido("Não foi possível ler este PDF.")
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        return dados.decode("latin-1")


def preparar_trechos(nome, dados):
    nome = nome_seguro(nome)
    if not nome.lower().endswith(EXTENSOES):
        raise MaterialInvalido("Envie um arquivo .txt ou .pdf.")
    if len(dados) > TAMANHO_MAXIMO_ARQUIVO:
        raise MaterialInvalido("O arquivo passa de 2 MB.", 413)
    if len(dados) == 0:
        raise MaterialInvalido("O arquivo está vazio.")
    texto = extrair_texto(nome, dados)
    if not " ".join(texto.split()):
        raise MaterialInvalido("Não encontrei texto neste arquivo. PDFs escaneados (só imagem) não funcionam.", 422)
    trechos = dividir_por_secoes(texto)
    if len(trechos) > TRECHOS_MAXIMOS_POR_ARQUIVO:
        raise MaterialInvalido("O arquivo é muito longo. Envie um material menor.", 413)
    return nome, [{"fonte": nome, "trecho": n, "texto": t} for n, t in enumerate(trechos, start=1)]


MAXIMO_ARQUIVOS_ENVIADOS = 6
MAXIMO_TRECHOS_POR_SESSAO = 300


def adicionar_material(indice, nome, dados):
    nome, registros = preparar_trechos(nome, dados)
    existentes = {f["nome"]: f for f in indice.fontes()}
    if nome in existentes:
        raise MaterialInvalido("Já existe um material com este nome. Remova-o antes de enviar de novo.", 409)
    enviados = [f for f in existentes.values() if not f["exemplo"]]
    if len(enviados) >= MAXIMO_ARQUIVOS_ENVIADOS:
        raise MaterialInvalido(f"Você já enviou {MAXIMO_ARQUIVOS_ENVIADOS} arquivos. Remova algum para enviar outro.", 429)
    if indice.total_trechos() + len(registros) > MAXIMO_TRECHOS_POR_SESSAO:
        raise MaterialInvalido("Seus materiais já estão no limite. Remova algum para enviar outro.", 413)
    indice.adicionar_trechos(registros)
    return nome