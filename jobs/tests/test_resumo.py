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
    corpo = "".join(f"<item><title>{t}</title><link>https://n.example/{i}</link>"
                    f"<pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S')} GMT</pubDate></item>" for i, (t, d) in enumerate(itens))
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{corpo}</channel></rss>'.encode()


def _coletar(engine, cfg, itens, agora, tipo="imprensa", url="https://a/feed"):
    f = fonte(f"f_{tipo}", url, tipo=tipo, nome=f"Fonte {tipo}")
    robo.rodar(engine, [f], SessaoFalsa({url: _rss(itens)}), cfg, agora=lambda: agora)


def test_so_manda_no_horario_e_nunca_em_dobro(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=4)
    _coletar(engine, cfg, [("France protests: Macron rejects resignation", agora - timedelta(hours=1))], agora)
    enviados = []
    assert resumo.talvez_enviar(engine, agora, [], None, "Dono/stratum-global", True, lambda t: enviados.append(t) or True) == "enviado"
    assert resumo.talvez_enviar(engine, agora + timedelta(minutes=15), [], None, None, True,
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
    assert resumo.talvez_enviar(engine, agora, [], None, None, True, lambda t: False) == "falhou"
    assert resumo.talvez_enviar(engine, agora + timedelta(minutes=15), [], None, None, True, lambda t: True) == "enviado"


def test_sem_telegram_registra_e_nao_insiste(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=2)
    assert resumo.talvez_enviar(engine, agora, [], None, None, False, lambda t: True) == "sem_telegram"
    assert resumo.pendente(engine, agora + timedelta(minutes=15)) is None


def test_conteudo_compara_com_o_periodo_anterior_e_lista_problemas(engine, cfg):
    agora = SETE_E_MEIA + timedelta(minutes=3)
    _coletar(engine, cfg, [
        ("Russia strikes Kyiv", agora - timedelta(hours=2)),
        ("Kremlin comments on talks", agora - timedelta(hours=3)),
        ("Russia old story", agora - timedelta(hours=14)),      # período anterior (12 a 24 horas antes)
    ], agora)
    _coletar(engine, cfg, [("Russia Russia Russia", agora - timedelta(hours=1))], agora, tipo="social", url="https://s/feed")
    texto = resumo.montar(engine, agora, SETE_E_MEIA, ["TASS (O site demorou demais para responder)"],
                          "o GitHub recusou o token", None)
    assert "Desde 18/10 19:33: 2 notícias de 1 fonte, 2 países citados." in texto  # rede social não conta
    assert "1. Rússia: 2 (1)" in texto and "2. Ucrânia: 1 (0)" in texto
    assert "• Rússia: Russia strikes Kyiv" in texto
    assert "Fontes com problema: TASS (O site demorou demais para responder)." in texto
    assert "Agendador: o GitHub recusou o token." in texto


def test_sem_noticias_diz_isso(engine, cfg):
    texto = resumo.montar(engine, SETE_E_MEIA, SETE_E_MEIA, [], None, None)
    assert "Nenhuma notícia nova desde 18/10 19:30." in texto
