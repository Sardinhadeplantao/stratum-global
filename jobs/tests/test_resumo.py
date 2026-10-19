"""Resumo no Telegram 3 vezes ao dia (decisão 0005): só nos horários, nunca em dobro, conteúdo por regra."""
from datetime import datetime, timedelta

from stratum import resumo, robo
from conftest import SessaoFalsa, fonte

# 19/10/2026: Brasília = UTC-3. 7:30 em Brasília = 10:30 UTC; 12:00 = 15:00 UTC; 19:00 = 22:00 UTC
SETE_E_MEIA = datetime(2026, 10, 19, 10, 30)


def test_horario_devido_e_o_ultimo_que_passou():
    assert resumo.horario_devido(datetime(2026, 10, 19, 10, 35)) == SETE_E_MEIA
    assert resumo.horario_devido(datetime(2026, 10, 19, 14, 59)) == SETE_E_MEIA
    assert resumo.horario_devido(datetime(2026, 10, 19, 15, 0)) == datetime(2026, 10, 19, 15, 0)
    assert resumo.horario_devido(datetime(2026, 10, 19, 9, 0)) == datetime(2026, 10, 18, 22, 0)  # 6h em Brasília: o das 19h de ontem


def _rss(itens):
    corpo = "".join(f"<item><title>{t}</title><link>https://n.example/{t.replace(' ', '-')}</link>"
                    f"<pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S')} GMT</pubDate></item>" for i, (t, d) in enumerate(itens))
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{corpo}</channel></rss>'.encode()


def _coletar(engine, cfg, itens, agora, tipo="imprensa", url="https://a/feed"):
    f = fonte(f"f_{tipo}", url, tipo=tipo, nome=f"Fonte {tipo}")
    robo.rodar(engine, [f], SessaoFalsa({url: _rss(itens)}), cfg, agora=lambda: agora)


def test_so_manda_no_horario_e_nunca_em_dobro(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=4)
    _coletar(engine, cfg, [("France protests: Macron rejects resignation", agora - timedelta(hours=1))], agora)
    enviados = []
    assert resumo.talvez_enviar(engine, agora, None, "Dono/stratum-global", True, lambda t: enviados.append(t) or True) == "enviado"
    assert resumo.talvez_enviar(engine, agora + timedelta(minutes=15), None, None, True,
                                lambda t: enviados.append(t) or True) == "fora_do_horario"  # já saiu
    assert len(enviados) == 1
    texto = enviados[0]
    assert texto.startswith("Stratum Global · resumo das 7:30 (19/10)")
    assert "1. França: 1 (0)" in texto and "https://dono.github.io/stratum-global/" in texto


def test_atrasado_mais_de_3_horas_pula(engine, cfg):
    assert resumo.pendente(engine, SETE_E_MEIA + timedelta(hours=3, minutes=1)) is None
    assert resumo.pendente(engine, SETE_E_MEIA + timedelta(hours=2, minutes=59)) == SETE_E_MEIA


def test_falha_do_telegram_tenta_de_novo(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=2)
    assert resumo.talvez_enviar(engine, agora, None, None, True, lambda t: False) == "falhou"
    assert resumo.talvez_enviar(engine, agora + timedelta(minutes=15), None, None, True, lambda t: True) == "enviado"


def test_sem_telegram_registra_e_nao_insiste(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=2)
    assert resumo.talvez_enviar(engine, agora, None, None, False, lambda t: True) == "sem_telegram"
    assert resumo.pendente(engine, agora + timedelta(minutes=15)) is None


def test_banco_temporario_nunca_manda(engine, cfg):
    # sem banco permanente, o robô não lembra do resumo anterior e mandaria um a cada rodada
    agora = SETE_E_MEIA + timedelta(minutes=2)
    assert resumo.talvez_enviar(engine, agora, None, None, True, lambda t: True, banco_permanente=False) == "sem_banco"


def test_conteudo_compara_com_o_periodo_anterior_e_lista_problemas(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=3)
    # período anterior (de 12 a 24 horas antes): o robô soube desta notícia 14 horas atrás
    _coletar(engine, cfg, [("Russia old story", agora - timedelta(hours=14))], agora - timedelta(hours=14))
    _coletar(engine, cfg, [
        ("Russia strikes Kyiv", agora - timedelta(hours=2)),
        ("Kremlin comments on talks", agora - timedelta(hours=3)),
    ], agora)
    _coletar(engine, cfg, [("Russia Russia Russia", agora - timedelta(hours=1))], agora, tipo="social", url="https://s/feed")
    tass = fonte("tass", "https://tass/feed", nome="TASS")
    robo.rodar(engine, [tass], SessaoFalsa({}), cfg, agora=lambda: agora - timedelta(hours=1))   # caiu no meio do período
    robo.rodar(engine, [tass], SessaoFalsa({"https://tass/feed": _rss([])}), cfg, agora=lambda: agora)  # e voltou
    texto = resumo.montar(engine, agora, SETE_E_MEIA, "o GitHub recusou o token", None)
    assert "Desde 18/10 19:33: 2 notícias de 1 fonte, 2 países citados." in texto  # rede social não conta
    assert "Mais citados (entre parênteses, quantas notícias de 18/10 7:33 a 18/10 19:33):" in texto
    assert "1. Rússia: 2 (1)" in texto and "2. Ucrânia: 1 (0)" in texto
    assert "• Rússia: Russia strikes Kyiv" in texto
    assert "Fontes com problema desde o último resumo:" in texto
    assert "• TASS: falhou em 1 de 2 coletas (Não foi possível conectar ao site (ConnectionError))." in texto
    assert "Agendador: o GitHub recusou o token." in texto


def test_cada_pais_tem_destaque_mesmo_quando_divide_a_noticia(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=3)
    _coletar(engine, cfg, [
        ("Russia and Ukraine trade prisoners", agora - timedelta(hours=1)),
        ("Russia strikes Kyiv", agora - timedelta(hours=2)),
        ("Ukraine grain deal", agora - timedelta(hours=3)),
    ], agora)
    texto = resumo.montar(engine, agora, SETE_E_MEIA, None, None)
    # Ucrânia (3) vem antes da Rússia (2); a notícia mais recente das duas é a mesma, então a Rússia ganha a seguinte
    assert "• Ucrânia: Russia and Ukraine trade prisoners" in texto
    assert "• Rússia: Russia strikes Kyiv" in texto


def test_noticia_que_chega_depois_do_resumo_entra_no_seguinte(engine, cfg):
    sete = SETE_E_MEIA + timedelta(minutes=3)
    resumo.registrar(engine, SETE_E_MEIA, sete, "enviado", "texto")
    # a fonte estava fora do ar às 7:33; volta às 9:00 com uma notícia publicada às 7:00
    _coletar(engine, cfg, [("Iran nuclear talks resume", SETE_E_MEIA - timedelta(minutes=30))],
             SETE_E_MEIA + timedelta(hours=1, minutes=30))
    meio_dia = datetime(2026, 10, 19, 15, 2)
    texto = resumo.montar(engine, meio_dia, datetime(2026, 10, 19, 15, 0), None, None)
    assert "Desde 19/10 7:33: 1 notícia de 1 fonte, 1 país citado." in texto and "1. Irã: 1 (0)" in texto


def test_sem_noticias_diz_isso(engine, cfg):
    texto = resumo.montar(engine, SETE_E_MEIA, SETE_E_MEIA, None, None)
    assert "Nenhuma notícia nova desde 18/10 19:30." in texto
