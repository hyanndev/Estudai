import secrets
import threading
import time


class GerenciadorDeSessoes:
    def __init__(self, criar_indice, validade_segundos=3600, maximo_sessoes=50, relogio=time.monotonic):
        self.criar_indice = criar_indice
        self.validade = validade_segundos
        self.maximo = maximo_sessoes
        self.relogio = relogio
        self.sessoes = {}
        self.trava = threading.Lock()

    def _limpar_vencidas(self):
        agora = self.relogio()
        vencidas = [sid for sid, (_, ultimo_uso) in self.sessoes.items() if agora - ultimo_uso > self.validade]
        for sid in vencidas:
            del self.sessoes[sid]

    def obter_ou_criar(self, sid):
        with self.trava:
            self._limpar_vencidas()
            if sid and sid in self.sessoes:
                self.sessoes[sid][1] = self.relogio()
                return sid, self.sessoes[sid][0], False
            if len(self.sessoes) >= self.maximo:
                mais_antiga = min(self.sessoes, key=lambda s: self.sessoes[s][1])
                del self.sessoes[mais_antiga]
            novo_sid = secrets.token_urlsafe(24)
            self.sessoes[novo_sid] = [self.criar_indice(), self.relogio()]
            return novo_sid, self.sessoes[novo_sid][0], True

    def existe(self, sid):
        with self.trava:
            self._limpar_vencidas()
            return bool(sid) and sid in self.sessoes

    def total(self):
        with self.trava:
            return len(self.sessoes)