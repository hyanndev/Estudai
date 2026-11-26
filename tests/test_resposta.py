from app import resposta


class IndiceFalso:
    def __init__(self, trechos):
        self.trechos = trechos

    def total_trechos(self):
        return len(self.trechos)

    def buscar(self, pergunta, k=3):
        return self.trechos


class ErroDaApi(Exception):
    def __init__(self, codigo):
        super().__init__("erro")
        self.code = codigo


class ReadTimeout(Exception):
    pass


class RespostaFalsa:
    def __init__(self, texto):
        self.text = texto


class ClienteFalso:
    def __init__(self, passos):
        self.passos = list(passos)
        self.chamadas = 0
        self.models = self

    def generate_content(self, **argumentos):
        self.chamadas += 1
        passo = self.passos.pop(0)
        if isinstance(passo, Exception):
            raise passo
        return RespostaFalsa(passo)


def trechos(nota=0.8):
    return [{"fonte": "a.txt", "trecho": 1, "texto": "O WIP limita o trabalho.", "nota": nota}]


def preparar(monkeypatch, passos):
    cliente = ClienteFalso(passos)
    monkeypatch.setattr(resposta.time, "sleep", lambda segundos: None)
    monkeypatch.setattr(resposta.genai, "Client", lambda **argumentos: cliente)
    return cliente


def test_resposta_normal_traz_texto_e_fontes(monkeypatch):
    cliente = preparar(monkeypatch, ["O WIP é o limite de tarefas."])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == "O WIP é o limite de tarefas."
    assert r["fontes"][0]["texto"] == "O WIP limita o trabalho."
    assert cliente.chamadas == 1


def test_erro_temporario_tenta_de_novo(monkeypatch):
    cliente = preparar(monkeypatch, [ErroDaApi(503), "Funcionou na segunda."])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == "Funcionou na segunda."
    assert cliente.chamadas == 2


def test_timeout_tambem_tenta_de_novo(monkeypatch):
    cliente = preparar(monkeypatch, [ReadTimeout(), "Funcionou."])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == "Funcionou."
    assert cliente.chamadas == 2


def test_duas_falhas_devolvem_mensagem_sem_fontes(monkeypatch):
    cliente = preparar(monkeypatch, [ErroDaApi(503), ErroDaApi(503)])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == resposta.FALHA_NA_GERACAO
    assert r["fontes"] == []
    assert cliente.chamadas == 2


def test_erro_do_pedido_nao_repete(monkeypatch):
    cliente = preparar(monkeypatch, [ErroDaApi(400), "nao deveria chegar aqui"])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == resposta.FALHA_NA_GERACAO
    assert cliente.chamadas == 1


def test_resposta_vazia_conta_como_falha(monkeypatch):
    preparar(monkeypatch, ["", ""])
    r = resposta.responder("O que é WIP?", IndiceFalso(trechos()))
    assert r["resposta"] == resposta.FALHA_NA_GERACAO


def test_nao_encontrei_esconde_as_fontes(monkeypatch):
    preparar(monkeypatch, [resposta.SEM_RESPOSTA])
    r = resposta.responder("O que é NoSQL?", IndiceFalso(trechos()))
    assert r["resposta"] == resposta.SEM_RESPOSTA
    assert r["fontes"] == []


def test_nota_baixa_nem_chama_o_modelo(monkeypatch):
    cliente = preparar(monkeypatch, ["nao deveria ser usado"])
    r = resposta.responder("Capital da França?", IndiceFalso(trechos(nota=0.5)))
    assert r["resposta"] == resposta.SEM_RESPOSTA
    assert cliente.chamadas == 0


def test_sem_materiais(monkeypatch):
    cliente = preparar(monkeypatch, ["nao deveria ser usado"])
    r = resposta.responder("Qualquer coisa?", IndiceFalso([]))
    assert r["resposta"] == resposta.SEM_MATERIAIS
    assert cliente.chamadas == 0