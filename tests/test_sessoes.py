from app.sessoes import GerenciadorDeSessoes


class Relogio:
    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora


def criar(relogio=None, **opcoes):
    return GerenciadorDeSessoes(criar_indice=lambda: object(), relogio=relogio or Relogio(), **opcoes)


def test_primeira_visita_cria_sessao():
    gerenciador = criar()
    sid, indice, nova = gerenciador.obter_ou_criar(None)
    assert nova is True
    assert len(sid) >= 30
    assert indice is not None


def test_mesmo_sid_devolve_o_mesmo_indice():
    gerenciador = criar()
    sid, indice, _ = gerenciador.obter_ou_criar(None)
    sid2, indice2, nova = gerenciador.obter_ou_criar(sid)
    assert sid2 == sid and indice2 is indice and nova is False


def test_sid_desconhecido_nao_e_aceito():
    gerenciador = criar()
    sid, _, nova = gerenciador.obter_ou_criar("inventado-pelo-cliente")
    assert nova is True
    assert sid != "inventado-pelo-cliente"


def test_visitantes_diferentes_tem_indices_diferentes():
    gerenciador = criar()
    _, a, _ = gerenciador.obter_ou_criar(None)
    _, b, _ = gerenciador.obter_ou_criar(None)
    assert a is not b


def test_sessao_expira_sem_uso():
    relogio = Relogio()
    gerenciador = criar(relogio, validade_segundos=100)
    sid, _, _ = gerenciador.obter_ou_criar(None)
    relogio.agora = 101
    _, _, nova = gerenciador.obter_ou_criar(sid)
    assert nova is True


def test_uso_renova_a_validade():
    relogio = Relogio()
    gerenciador = criar(relogio, validade_segundos=100)
    sid, _, _ = gerenciador.obter_ou_criar(None)
    relogio.agora = 80
    gerenciador.obter_ou_criar(sid)
    relogio.agora = 160
    _, _, nova = gerenciador.obter_ou_criar(sid)
    assert nova is False


def test_limite_de_sessoes_remove_a_mais_antiga():
    relogio = Relogio()
    gerenciador = criar(relogio, maximo_sessoes=2)
    primeira, _, _ = gerenciador.obter_ou_criar(None)
    relogio.agora = 1
    gerenciador.obter_ou_criar(None)
    relogio.agora = 2
    gerenciador.obter_ou_criar(None)
    assert gerenciador.total() == 2
    _, _, nova = gerenciador.obter_ou_criar(primeira)
    assert nova is True


def test_existe_so_para_sessoes_criadas_aqui():
    gerenciador = criar()
    sid, _, _ = gerenciador.obter_ou_criar(None)
    assert gerenciador.existe(sid) is True
    assert gerenciador.existe("inventado") is False
    assert gerenciador.existe(None) is False


def test_existe_considera_a_expiracao():
    relogio = Relogio()
    gerenciador = criar(relogio, validade_segundos=100)
    sid, _, _ = gerenciador.obter_ou_criar(None)
    relogio.agora = 101
    assert gerenciador.existe(sid) is False