import threading
import numpy as np


class IndiceDeMateriais:
    def __init__(self, gerar):
        self.gerar = gerar
        self.registros = []
        self.vetores = None
        self._trava = threading.Lock()

    def carregar(self, registros, vetores):
        with self._trava:
            self.registros = list(registros)
            self.vetores = np.array(vetores, dtype=float)

    def adicionar_trechos(self, registros):
        if not registros:
            return
        novos = self.gerar([r["texto"] for r in registros], "RETRIEVAL_DOCUMENT")
        with self._trava:
            if self.vetores is None or not self.registros:
                self.vetores = novos
            else:
                self.vetores = np.vstack([self.vetores, novos])
            self.registros = self.registros + list(registros)

    def remover_fonte(self, fonte):
        with self._trava:
            manter = [i for i, r in enumerate(self.registros) if r["fonte"] != fonte]
            if len(manter) == len(self.registros):
                return False
            self.vetores = self.vetores[manter] if manter else None
            self.registros = [self.registros[i] for i in manter]
            return True

    def fontes(self):
        with self._trava:
            registros = self.registros
        contagem = {}
        for r in registros:
            item = contagem.setdefault(r["fonte"], {"nome": r["fonte"], "trechos": 0, "exemplo": bool(r.get("exemplo"))})
            item["trechos"] += 1
        return list(contagem.values())

    def total_trechos(self):
        return len(self.registros)

    def copiar(self):
        novo = IndiceDeMateriais(self.gerar)
        with self._trava:
            novo.registros = list(self.registros)
            novo.vetores = None if self.vetores is None else self.vetores.copy()
        return novo

    def buscar(self, pergunta, k=3):
        with self._trava:
            registros = self.registros
            vetores = self.vetores
        if not registros or vetores is None:
            return []
        consulta = self.gerar([pergunta], "RETRIEVAL_QUERY")[0]
        notas = vetores @ consulta
        melhores = np.argsort(notas)[::-1][:k]
        return [{**registros[i], "nota": round(float(notas[i]), 3)} for i in melhores]