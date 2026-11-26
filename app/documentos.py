"""Leitura dos materiais e divisão em trechos."""
from pathlib import Path  
from pypdf import PdfReader  

RAIZ = Path(__file__).resolve().parent.parent  
PASTA_MATERIAIS = RAIZ / "materiais"  
TAMANHO_TRECHO = 800  
SOBREPOSICAO = 100  


def ler_arquivo(caminho: Path) -> str:
    """Devolve o texto de um arquivo .txt ou .pdf."""
    if caminho.suffix.lower() == ".pdf": 
        leitor = PdfReader(caminho)  
        paginas = [p.extract_text() or "" for p in leitor.pages]  
        return "\n".join(paginas)  
    return caminho.read_text(encoding="utf-8") 


def dividir_em_trechos(texto: str, tamanho: int = TAMANHO_TRECHO, sobreposicao: int = SOBREPOSICAO) -> list[str]:
    """Quebra o texto em trechos de tamanho fixo, com sobreposição."""
    if sobreposicao >= tamanho:  
        raise ValueError("sobreposicao deve ser menor que tamanho")
    texto = " ".join(texto.split())  
    trechos = []  
    inicio = 0  
    while inicio < len(texto): 
        fim = inicio + tamanho  
        trecho = texto[inicio:fim].strip() 
        if trecho:  
            trechos.append(trecho)  
        if fim >= len(texto):  
            break
        inicio += tamanho - sobreposicao  
    return trechos 


def carregar_materiais(pasta: Path = PASTA_MATERIAIS) -> list[dict]:
    """Lê todos os .txt e .pdf da pasta e devolve os trechos com a fonte."""
    registros = []  
    for caminho in sorted(pasta.iterdir()):  
        if caminho.suffix.lower() not in (".txt", ".pdf"):  
            continue
        texto = ler_arquivo(caminho)  # lê o texto do arquivo
        for numero, trecho in enumerate(dividir_em_trechos(texto), start=1):  
            registros.append({"fonte": caminho.name, "trecho": numero, "texto": trecho})  
    return registros  


if __name__ == "__main__":  
    registros = carregar_materiais()  
    print(f"{len(registros)} trechos carregados")  
    if registros:  
        print(registros[0])  
