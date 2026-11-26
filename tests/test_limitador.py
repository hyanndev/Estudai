from app.limitador import LimitadorDeUso


class Relogio:
    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora


def test_permite_ate_o_maximo_e_bloqueia_depois():
    limitador = LimitadorDeUso(2, 60, Relogio())
    assert limitador.tentar("a")[0] is True
    assert limitador.tentar("a")[0] is True
    liberado, espera = limitador.tentar("a")
    assert liberado is False
    assert 0 < espera <= 60


def test_janela_desliza_e_libera_de_novo():
    relogio = Relogio()
    limitador = LimitadorDeUso(1, 60, relogio)
    assert limitador.tentar("a")[0] is True
    relogio.agora = 30
    assert limitador.tentar("a")[0] is False
    relogio.agora = 61
    assert limitador.tentar("a")[0] is True


def test_cada_chave_tem_o_seu_limite():
    limitador = LimitadorDeUso(1, 60, Relogio())
    assert limitador.tentar("a")[0] is True
    assert limitador.tentar("b")[0] is True
    assert limitador.tentar("a")[0] is False


def test_tempo_de_espera_diminui_com_o_relogio():
    relogio = Relogio()
    limitador = LimitadorDeUso(1, 60, relogio)
    limitador.tentar("a")
    relogio.agora = 20
    _, espera = limitador.tentar("a")
    assert round(espera) == 40


def test_bloqueio_nao_consome_o_limite():
    relogio = Relogio()
    limitador = LimitadorDeUso(1, 60, relogio)
    limitador.tentar("a")
    for _ in range(10):
        limitador.tentar("a")
    relogio.agora = 61
    assert limitador.tentar("a")[0] is True


def test_limpeza_remove_visitantes_antigos():
    relogio = Relogio()
    limitador = LimitadorDeUso(1, 60, relogio)
    for n in range(5100):
        limitador.tentar(f"visitante{n}")
    relogio.agora = 120
    limitador.tentar("novo")
    assert len(limitador.registros) < 5100