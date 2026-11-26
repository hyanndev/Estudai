"""Mede a qualidade da busca usando as perguntas de teste."""
import json  
import time 
from app.busca import buscar  
from app.documentos import RAIZ  

ARQUIVO = RAIZ / "tests" / "perguntas.json" 


def avaliar():
    """Roda todas as perguntas e imprime as métricas."""
    casos = json.loads(ARQUIVO.read_text(encoding="utf-8")) 
    notas_dentro = [] 
    notas_fora = []  
    acertos_trecho = 0  
    acertos_fonte = 0 
    total_dentro = 0 

    for caso in casos: 
        trechos = buscar(caso["pergunta"], k=3) 
        melhor = trechos[0]["nota"]  
        time.sleep(0.5)  
        if caso["fonte"] is None:  
            notas_fora.append(melhor) 
            print(f"[fora]   {melhor}  {caso['pergunta']}") 
            continue
        total_dentro += 1  
        notas_dentro.append(melhor)  
        if trechos[0]["fonte"] == caso["fonte"]:  
            acertos_fonte += 1  
        achou = any(caso["palavra"].lower() in t["texto"].lower() for t in trechos) 
        if achou:  
            acertos_trecho += 1  
        print(f"[{'ok' if achou else 'FALHOU'}]  {melhor}  {caso['pergunta']}")  

    print("\n--- Resultado ---") 
    print(f"Arquivo certo em 1º lugar: {acertos_fonte}/{total_dentro}") 
    print(f"Trecho com a resposta entre os 3 melhores: {acertos_trecho}/{total_dentro}")  
    print(f"Menor nota entre as perguntas dentro dos materiais: {min(notas_dentro)}")  
    print(f"Maior nota entre as perguntas fora dos materiais: {max(notas_fora)}")  


if __name__ == "__main__": 
    avaliar()  