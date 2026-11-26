import threading
import time
from collections import deque


class LimitadorDeUso:
    def __init__(self, maximo, janela_segundos, relogio=time.monotonic):
        self.maximo = maximo
        self.janela = janela_segundos
        self.relogio = relogio
        self.registros = {}
        self.trava = threading.Lock()

    def tentar(self, chave):
        agora = self.relogio()
        with self.trava:
            if len(self.registros) > 5000:
                self._limpar(agora)
            fila = self.registros.setdefault(chave, deque())
            while fila and agora - fila[0] >= self.janela:
                fila.popleft()
            if len(fila) >= self.maximo:
                return False, self.janela - (agora - fila[0])
            fila.append(agora)
            return True, 0.0

    def _limpar(self, agora):
        vazias = [c for c, fila in self.registros.items() if not fila or agora - fila[-1] >= self.janela]
        for chave in vazias:
            del self.registros[chave]