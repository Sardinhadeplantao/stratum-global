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
