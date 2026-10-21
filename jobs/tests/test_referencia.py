"""Casos de referência: definem o caráter do sistema. Nunca mude um destes para um teste passar;
se a regra mudar de verdade, registre a decisão em docs/decisoes/ antes."""
import json
from datetime import timedelta

from sqlalchemy import func, select

from stratum import db, export, robo
from conftest import Relogio, SessaoFalsa, fonte

URL_A, URL_B = "https://a.example/feed", "https://b.example/feed"


def _contar(engine, tabela):
    with engine.connect() as c:
        return c.execute(select(func.count()).select_from(tabela)).scalar()


def test_documento_coletado_duas_vezes_vira_um_registro(engine, cfg, feed_rss):
    fontes = [fonte("a", URL_A)]
    sessao = SessaoFalsa({URL_A: feed_rss})
    primeira = robo.rodar(engine, fontes, sessao, cfg, agora=Relogio())
    segunda = robo.rodar(engine, fontes, sessao, cfg, agora=Relogio())
    # 3 itens com título no feed; 2 são o mesmo artigo (só muda a âncora) -> 2 documentos
    assert primeira.novos == 2 and segunda.novos == 0
    assert _contar(engine, db.documento) == 2


def test_rastreio_na_url_nao_cria_documento_novo(engine, cfg, feed_rss):
    outra_versao = feed_rss.replace(b"utm_source=rss&amp;utm_medium=feed", b"utm_campaign=outra")
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=Relogio())
    r = robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: outra_versao}), cfg, agora=Relogio())
    assert r.novos == 0


def test_nada_e_reescrito_quando_a_fonte_muda_o_titulo(engine, cfg, feed_rss):
    relogio = Relogio()
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=relogio)
    with engine.connect() as c:
        antes = c.execute(select(db.documento).order_by(db.documento.c.id)).mappings().all()
    alterado = feed_rss.replace(b"Conselho aprova", b"Conselho REJEITA")
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: alterado}), cfg, agora=relogio)
    with engine.connect() as c:
        depois = c.execute(select(db.documento).order_by(db.documento.c.id)).mappings().all()
    assert depois == antes  # título e data de conhecimento originais preservados


def test_data_de_conhecimento_e_a_da_primeira_coleta(engine, cfg, feed_rss):
    relogio = Relogio()
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=relogio)
    primeira = relogio.t
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=relogio)
    with engine.connect() as c:
        datas = set(c.execute(select(db.documento.c.conhecido_em)).scalars())
    assert max(datas) <= primeira


def test_uma_fonte_que_falha_nao_derruba_as_outras(engine, cfg, feed_rss):
    r = robo.rodar(engine, [fonte("a", URL_A), fonte("b", URL_B)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=Relogio())
    assert r.situacao == "parcial" and r.falhas == ["b"] and r.novos == 2
    with engine.connect() as c:
        coletas = {x["fonte_id"]: x for x in c.execute(select(db.coleta)).mappings()}
    assert coletas["a"]["situacao"] == "ok"
    assert coletas["b"]["situacao"] == "falhou"
    assert coletas["b"]["erro"] == "Não foi possível conectar ao site (ConnectionError)."


def test_erro_http_conta_como_falha_da_fonte(engine, cfg):
    r = robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: 503}), cfg, agora=Relogio())
    assert r.situacao == "falhou"
    with engine.connect() as c:
        assert c.execute(select(db.coleta.c.erro)).scalar() == "O site recusou o pedido (HTTP 503)."


def test_pagina_que_nao_e_feed_tem_erro_claro(engine, cfg):
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: b"<html>erro</html>"}), cfg, agora=Relogio())
    with engine.connect() as c:
        assert c.execute(select(db.coleta.c.erro)).scalar().startswith("O endereço não devolveu um feed válido")


def test_fonte_inativa_nao_e_lida(engine, cfg, feed_rss):
    sessao = SessaoFalsa({URL_A: feed_rss, URL_B: feed_rss})
    robo.rodar(engine, [fonte("a", URL_A), fonte("b", URL_B, ativa=False)], sessao, cfg, agora=Relogio())
    assert sessao.chamadas == [URL_A]


def test_fonte_que_sai_da_lista_fica_inativa_e_mantem_os_documentos(engine, cfg, feed_rss):
    robo.rodar(engine, [fonte("a", URL_A)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=Relogio())
    robo.rodar(engine, [fonte("b", URL_B)], SessaoFalsa({URL_B: feed_rss.replace(b"exemplo.org", b"outro.org")}), cfg,
               agora=Relogio())
    with engine.connect() as c:
        ativas = dict(c.execute(select(db.fonte.c.id, db.fonte.c.ativa)).all())
    assert ativas == {"a": False, "b": True}
    assert _contar(engine, db.documento) == 4
    assert export.montar(engine)["totais"]["fontes"] == 1


def test_status_para_o_site(engine, cfg, feed_rss):
    relogio = Relogio()
    robo.rodar(engine, [fonte("a", URL_A), fonte("b", URL_B)], SessaoFalsa({URL_A: feed_rss}), cfg, agora=relogio)
    uma_hora_depois = relogio.t + timedelta(hours=1)
    s = export.montar(engine, agora=lambda: uma_hora_depois)
    assert s["banco"] == "temporario" and s["ultima_rodada"]["situacao"] == "parcial"
    assert s["totais"] == {"documentos": 2, "documentos_24h": 2, "fontes": 2, "fontes_ok": 1}
    por_id = {f["id"]: f for f in s["fontes"]}
    assert por_id["a"]["documentos"] == 2 and por_id["b"]["ultima_coleta"]["situacao"] == "falhou"
    assert s["ultimos_documentos"][0]["fonte_nome"] == "a"
    dois_dias_depois = relogio.t + timedelta(days=2)
    assert export.montar(engine, agora=lambda: dois_dias_depois)["totais"]["documentos_24h"] == 0


def test_status_quando_o_banco_nao_abre(tmp_path):
    caminho = tmp_path / "status.json"
    export.escrever_falha_banco(str(caminho), "OperationalError")
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["banco"] == "erro" and "OperationalError" in dados["erro_banco"]
    assert dados["atencao"] is None and dados["avisar_atraso_apos"]  # cinza no site, e aviso se o robô parar


def test_erro_de_banco_nao_mostra_a_mensagem_crua():
    from sqlalchemy.exc import OperationalError
    erro = OperationalError("INSERT", {}, Exception("senha errada para postgres://usuario:segredo@servidor"))
    texto = robo.erro_legivel(erro)
    assert "segredo" not in texto and "servidor" not in texto and "OperationalError" in texto


def test_endereco_do_banco_so_com_a_senha(monkeypatch):
    from stratum import config
    for nome in ("DATABASE_URL", "SUPABASE_SENHA", "SUPABASE_HOST", "SUPABASE_USUARIO"):
        monkeypatch.delenv(nome, raising=False)
    assert config.endereco_do_banco() is None  # sem senha: banco temporário
    monkeypatch.setenv("SUPABASE_HOST", "aws-0-us-east-2.pooler.supabase.com")
    monkeypatch.setenv("SUPABASE_USUARIO", "postgres.abc")
    monkeypatch.setenv("SUPABASE_SENHA", "a@b#c/d")
    assert config.endereco_do_banco() == "postgresql://postgres.abc:a%40b%23c%2Fd@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    assert config.endereco_do_banco() == "postgresql://x"  # o endereço completo, se existir, vence


def test_rodada_completa_grava_o_status_do_site(tmp_path, monkeypatch, feed_rss):
    """A rodada inteira (coleta, agendador, resumo, status.json), como no GitHub Actions, sem rede e sem segredos."""
    from stratum import fontes as catalogo
    from stratum.connectors import rss
    f = fonte("a", "https://a/feed")
    monkeypatch.setattr(catalogo, "FONTES", [f])
    monkeypatch.setattr(rss, "nova_sessao", lambda: SessaoFalsa({"https://a/feed": feed_rss}))
    for nome in ("DATABASE_URL", "SUPABASE_SENHA", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GITHUB_REPOSITORY"):
        monkeypatch.delenv(nome, raising=False)
    caminho = tmp_path / "status.json"
    assert robo.main(["--exportar", str(caminho)]) == 0
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["banco"] == "temporario" and dados["totais"]["documentos"] == 2
    assert dados["agendador"]["situacao"] == "sem_banco"


# Séries de mercado (decisão 0011)

def _serie(n, escala=1.0, semente=1, inicio=None):
    """Cotação sintética de n dias úteis, com variações sorteadas de tamanho `escala` (em %)."""
    import random
    from datetime import date
    rnd, d, v, pontos = random.Random(semente), inicio or date(2020, 1, 1), 100.0, []
    while len(pontos) < n:
        if d.weekday() < 5:
            v *= 1 + rnd.gauss(0, escala) / 100
            pontos.append((d, v))
        d += timedelta(days=1)
    return pontos


def _gravar_serie(engine, pontos, conhecido_em, serie_id="bce_brl", codigo="BRL"):
    from stratum import fontes as catalogo, mercados
    from stratum.connectors.series import Observacao
    with engine.begin() as c:
        db.gravar_fontes(c, [f for f in catalogo.FONTES if f["id"] == "bce_cambio"])
        db.gravar_series(c, [s for s in catalogo.SERIES if s["id"] == serie_id])
    serie = {"id": serie_id, "codigo": codigo}
    return mercados.gravar(engine, [serie], [Observacao(codigo, d, v) for d, v in pontos], None, conhecido_em)


def test_cotacao_repetida_nao_entra_duas_vezes_e_revisao_vira_registro_novo(engine):
    from datetime import date, datetime
    dia = date(2026, 10, 16)
    assert _gravar_serie(engine, [(dia, 6.3345)], datetime(2026, 10, 16, 15)) == 1
    assert _gravar_serie(engine, [(dia, 6.3345)], datetime(2026, 10, 16, 18)) == 0   # a mesma cotação de novo
    assert _gravar_serie(engine, [(dia, 6.3400)], datetime(2026, 10, 17, 9)) == 1    # a fonte revisou o valor
    with engine.connect() as c:
        linhas = c.execute(select(db.observacao.c.valor, db.observacao.c.conhecido_em).order_by(db.observacao.c.id)).all()
    assert [v for v, _ in linhas] == [6.3345, 6.3400]  # o valor antigo fica; o novo entra com a data em que soube


def test_leitura_de_um_momento_so_usa_o_que_o_sistema_sabia(engine):
    from datetime import datetime
    from stratum import mercados
    pontos = _serie(1300, escala=0.5)
    _gravar_serie(engine, pontos, datetime(2026, 1, 1))
    ultimo_dia, ultimo_valor = pontos[-1]
    _gravar_serie(engine, [(ultimo_dia, ultimo_valor * 1.05)], datetime(2026, 2, 1))   # revisão: +5% no último dia
    serie = {"id": "bce_brl", "medida": "variacao_pct", "frequencia": "diaria"}
    with engine.connect() as c:
        antes = mercados.leitura(c, serie, None, datetime(2026, 1, 15))
        depois = mercados.leitura(c, serie, None, datetime(2026, 2, 15))
    assert antes["valor"] == ultimo_valor and antes["extremo"] is None
    assert depois["valor"] == ultimo_valor * 1.05 and depois["extremo"] == "alta"


def test_a_mesma_regua_para_todas_as_series():
    # Fora do normal é contra o próprio histórico: 1% é extremo numa moeda calma e comum numa agitada.
    # Os parâmetros são os mesmos, e a escala do preço não muda nada.
    from stratum.domain import regua
    calma, agitada = _serie(1300, escala=0.2, semente=2), _serie(1300, escala=2.0, semente=3)
    for pontos in (calma, agitada):
        dia, valor = pontos[-1]
        pontos.append((dia + timedelta(days=3 if dia.weekday() == 4 else 1), valor * 1.01))
    assert regua.ler(calma).extremo == "alta"
    assert regua.ler(agitada).extremo is None
    em_mil = [(d, v * 1000) for d, v in calma]
    assert regua.ler(em_mil).percentil == regua.ler(calma).percentil


def test_historico_curto_nao_gera_leitura():
    from stratum.domain import regua
    curto = regua.ler(_serie(200))
    assert curto.situacao == "historico_curto" and curto.percentil is None and curto.extremo is None
    assert regua.ler([]).situacao == "sem_dado"


def test_serie_parada_fica_sem_cor(engine):
    # Passou da validade da fonte, a leitura não pinta nada: cinza, mesmo que o último dado tenha sido extremo
    from datetime import datetime
    from stratum import mercados
    pontos = _serie(1300, escala=0.2)
    dia, valor = pontos[-1]
    pontos.append((dia + timedelta(days=3 if dia.weekday() == 4 else 1), valor * 1.05))
    ultimo = datetime.combine(pontos[-1][0], datetime.min.time())
    _gravar_serie(engine, pontos, ultimo + timedelta(hours=16))
    serie = {"id": "bce_brl", "medida": "variacao_pct", "frequencia": "diaria"}
    with engine.connect() as c:
        em_dia = mercados.leitura(c, serie, 5, ultimo + timedelta(days=2))
        parada = mercados.leitura(c, serie, 5, ultimo + timedelta(days=9))
    assert em_dia["situacao"] == "ok" and em_dia["extremo"] == "alta"
    assert parada["situacao"] == "parada" and parada["extremo"] is None and parada["mudancas"] == []


def test_cotacao_de_mercado_que_nao_bate_com_o_bce_fica_sem_cor():
    # É verdade? O dólar em reais do Yahoo é conferido com a conta pelo BCE no mesmo dia (decisão 0012)
    from datetime import datetime
    from stratum import mercados
    euro_em_reais, euro_em_dolares = _serie(1300, escala=0.2, semente=4), _serie(1300, escala=0.2, semente=5)
    dolar_em_reais = [(d, r / u) for (d, r), (_, u) in zip(euro_em_reais, euro_em_dolares)]
    dia, valor = dolar_em_reais[-1]
    dolar_em_reais[-1] = (dia, valor * 1.04)  # 4% fora da conta do BCE: dado errado ou dia anormal
    momento = datetime.combine(dia, datetime.min.time()) + timedelta(days=1)
    serie = {"id": "yahoo_brl", "medida": "variacao_pct", "frequencia": "diaria"}

    conferida = mercados.conferencia(dolar_em_reais, euro_em_reais, euro_em_dolares, antes_de=None)
    assert conferida["data"] == dia.isoformat() and conferida["diferenca"] == 4.0 and not conferida["confere"]
    lido = mercados._ler(dolar_em_reais, serie, 5, momento, conferida=conferida)
    assert lido["situacao"] == "nao_confere" and lido["extremo"] is None and lido["mudancas"] == []

    certo = dolar_em_reais[:-1] + [(dia, valor)]
    assert mercados.conferencia(certo, euro_em_reais, euro_em_dolares, antes_de=None)["confere"]


def test_dia_em_andamento_aparece_marcado_e_fica_fora_da_conferencia():
    from datetime import datetime
    from stratum import mercados
    euro_em_reais, euro_em_dolares = _serie(1300, escala=0.2, semente=4), _serie(1300, escala=0.2, semente=5)
    dolar_em_reais = [(d, r / u) for (d, r), (_, u) in zip(euro_em_reais, euro_em_dolares)]
    hoje = dolar_em_reais[-1][0] + timedelta(days=3 if dolar_em_reais[-1][0].weekday() == 4 else 1)
    dolar_em_reais.append((hoje, dolar_em_reais[-1][1] * 1.003))  # o dia de hoje, às 14h, ainda sem o BCE
    momento = datetime.combine(hoje, datetime.min.time()) + timedelta(hours=14)
    serie = {"id": "yahoo_brl", "medida": "variacao_pct", "frequencia": "diaria"}
    conferida = mercados.conferencia(dolar_em_reais, euro_em_reais, euro_em_dolares, antes_de=hoje)
    assert conferida["data"] == dolar_em_reais[-2][0].isoformat() and conferida["confere"]  # o último dia fechado
    lido = mercados._ler(dolar_em_reais, serie, 5, momento, dia_em_andamento=True, conferida=conferida)
    assert lido["parcial"] and lido["data"] == hoje.isoformat() and lido["situacao"] == "ok"
    assert not mercados._ler(dolar_em_reais[:-1], serie, 5, momento, dia_em_andamento=True)["parcial"]


# Pontos críticos (decisão 0014): regra de palavras, sem IA; mede atenção das fontes, não gravidade

def _noticia(titulo, controlador, resumo=""):
    return {"titulo": titulo, "resumo": resumo, "controlador": controlador}


def test_ponto_fica_critico_com_acao_e_duas_vozes():
    from stratum.domain import pontos
    manchete = "Oil tanker on fire after hitting mine in Hormuz: Iran's Guards"  # manchete real de 20/10
    uma_voz = pontos.estados([_noticia(manchete, "estado:QAT")])
    assert uma_voz["ormuz"]["estado"] == "em_pauta"            # uma voz só: em pauta, ainda não crítico
    duas_vozes = pontos.estados([_noticia(manchete, "estado:QAT"),
                                 _noticia("Iran warns ships in the Strait of Hormuz", "estado:GBR")])
    assert duas_vozes["ormuz"] == {"estado": "critico", "noticias": 2, "vozes": 2, "com_acao": 1}


def test_ponto_citado_sem_acao_fica_em_pauta():
    from stratum.domain import pontos
    e = pontos.estados([_noticia("Panama Canal traffic returns to normal", "estado:GBR"),
                        _noticia("Canal do Panamá amplia calado", "grupo:folha")])
    assert e["panama"]["estado"] == "em_pauta" and e["panama"]["vozes"] == 2 and e["panama"]["com_acao"] == 0
    assert e["ormuz"]["estado"] == "sem_pauta" and e["ormuz"]["noticias"] == 0


def test_nome_do_ponto_so_conta_como_palavra_inteira():
    from stratum.domain import pontos
    e = pontos.estados([_noticia("Suezmax tanker rates hit record after attack", "estado:QAT")])
    assert e["suez"]["noticias"] == 0  # "Suezmax" é tipo de navio, não o canal


def test_mar_vermelho_conta_para_bab_el_mandeb():
    from stratum.domain import pontos
    e = pontos.estados([_noticia("Houthis claim missile attack on ship in the Red Sea", "estado:QAT"),
                        _noticia("Navio é atacado no Mar Vermelho", "grupo:folha")])
    assert e["bab_el_mandeb"]["estado"] == "critico"


def test_dia_da_troca_de_contrato_nao_entra_na_regua(engine):
    # O WTI de 20/10/2026: a série do Yahoo passou do contrato de novembro (103,66) para o de dezembro (98,47), uma
    # falsa queda de 5%. Com o contrato de cada dia guardado, o dia da troca fica sem cor e fora da régua.
    from datetime import datetime
    from stratum import fontes as catalogo, mercados
    from stratum.connectors.series import Observacao
    wti = next(s for s in catalogo.SERIES if s["id"] == "commodity_cl")
    with engine.begin() as c:
        db.gravar_fontes(c, [f for f in catalogo.FONTES if f["id"] == "yahoo_commodities"])
        db.gravar_series(c, [wti])
    pontos = _serie(1300, escala=1.0, semente=9)
    pontos[-2] = (pontos[-2][0], 103.66)
    pontos[-1] = (pontos[-1][0], 98.47)
    dia_19, dia_20 = pontos[-2][0], pontos[-1][0]
    obs = [Observacao("CL=F", d, v) for d, v in pontos[:-2]]
    noite_19 = datetime.combine(dia_19, datetime.min.time()) + timedelta(hours=22)
    noite_20 = datetime.combine(dia_20, datetime.min.time()) + timedelta(hours=22)
    mercados.gravar(engine, [wti], obs + [Observacao("CL=F", dia_19, 103.66, "Nov 26")], None, noite_19)
    mercados.gravar(engine, [wti], [Observacao("CL=F", dia_20, 98.47, "Dec 26")], None, noite_20)
    serie = {"id": "commodity_cl", "medida": "variacao_pct", "frequencia": "diaria"}
    momento = noite_20 + timedelta(hours=1)
    with engine.connect() as c:
        trocas = mercados.trocas_de_contrato(c, momento)
        lido = mercados._ler(mercados.pontos(c, "commodity_cl", momento), serie, 5, momento, trocas=trocas["commodity_cl"])
    assert trocas["commodity_cl"] == {dia_20}
    assert lido["situacao"] == "troca_de_contrato" and lido["extremo"] is None and lido["valor"] == 98.47
    # Sem saber o contrato, a mesma queda apareceria como fora do normal
    sem_contrato = mercados._ler(pontos, serie, 5, momento)
    assert sem_contrato["extremo"] == "baixa"
