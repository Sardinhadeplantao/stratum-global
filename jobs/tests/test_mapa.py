"""A página inicial em torno do mapa (decisão 0014): pontos críticos, terremotos e a faixa de baixo."""
from datetime import datetime, timedelta

import pytest

from conftest import Relogio, fonte
from stratum import db, export, robo
from stratum import fontes as catalogo
from stratum.connectors import eventos as conectores
from stratum.connectors.eventos import Evento

AGORA = datetime(2026, 10, 21, 12)
USGS = next(f for f in catalogo.FONTES if f["id"] == "usgs_terremotos")


def _noticias(engine, itens):
    """itens: (fonte_id, controlador, título)."""
    with engine.begin() as c:
        db.gravar_fontes(c, [fonte(f, f"https://{f}/feed", controlador=ctl) for f, ctl in {(f, ctl) for f, ctl, _ in itens}])
        rid = c.execute(db.rodada.insert().values(iniciada_em=AGORA, situacao="ok", banco="temporario", versao="t")
                        ).inserted_primary_key[0]
        c.execute(db.documento.insert(), [
            dict(hash=f"h{i}", fonte_id=f, rodada_id=rid, url=f"https://{f}/{i}", titulo=t, resumo=None,
                 publicado_em=AGORA - timedelta(hours=1), conhecido_em=AGORA - timedelta(minutes=50))
            for i, (f, _, t) in enumerate(itens)])


def test_status_traz_o_ponto_critico_com_contexto(engine):
    _noticias(engine, [("aljazeera", "estado:QAT", "Oil tanker on fire after hitting mine in Hormuz: Iran's Guards"),
                       ("bbc", "estado:GBR", "Shipping insurers weigh Strait of Hormuz risk"),
                       ("folha", "grupo:folha", "Canal do Panamá amplia calado")])
    p = export.montar(engine, agora=lambda: AGORA)["pontos"]
    ormuz, panama = p["lista"][0], next(x for x in p["lista"] if x["id"] == "panama")
    assert ormuz["id"] == "ormuz" and ormuz["estado"] == "critico" and (ormuz["noticias"], ormuz["vozes"]) == (2, 2)
    assert [d["acao"] for d in ormuz["documentos"]].count(True) == 1
    assert {m["iso"] for m in ormuz["margens"]} == {"IRN", "OMN", "ARE"} and ormuz["fatos"][0]["url"].startswith("https://")
    assert panama["estado"] == "em_pauta" and (p["criticos"], p["em_pauta"]) == (1, 1)


def test_rede_social_nao_acende_ponto(engine):
    with engine.begin() as c:
        db.gravar_fontes(c, [fonte("s", "https://s/feed", tipo="social", controlador="grupo:s")])
        rid = c.execute(db.rodada.insert().values(iniciada_em=AGORA, situacao="ok", banco="temporario", versao="t")
                        ).inserted_primary_key[0]
        c.execute(db.documento.insert().values(hash="s1", fonte_id="s", rodada_id=rid, url="https://s/1",
                                               titulo="Missile attack in the Strait of Hormuz", resumo=None,
                                               publicado_em=AGORA, conhecido_em=AGORA))
    ormuz = next(x for x in export.montar(engine, agora=lambda: AGORA)["pontos"]["lista"] if x["id"] == "ormuz")
    assert ormuz["estado"] == "sem_pauta"  # rede social é pista, nunca entra em conta (regra 4)


def _evento(ext_id, versao, mag, horas_atras=2):
    return Evento(ext_id, versao, f"M {mag} - south of the Fiji Islands", f"https://earthquake.usgs.gov/{ext_id}",
                  mag, -23.5, 179.1, AGORA - timedelta(hours=horas_atras))


def test_terremoto_revisado_vira_registro_novo_e_o_site_mostra_o_mais_recente(engine, cfg):
    relogio = Relogio(AGORA - timedelta(minutes=30))
    primeira = [_evento("us1", "100", 6.1), _evento("us2", "100", 4.6, horas_atras=30)]  # us2: fora das 24 h
    r1 = robo.rodar(engine, [USGS], None, cfg, agora=relogio, conectores_eventos={"usgs": lambda *_: primeira})
    r2 = robo.rodar(engine, [USGS], None, cfg, agora=relogio, conectores_eventos={"usgs": lambda *_: primeira})
    # O USGS muda a data de atualização sem mudar nada que se vê (revisão de 21/10): não é registro novo
    so_data = robo.rodar(engine, [USGS], None, cfg, agora=relogio,
                         conectores_eventos={"usgs": lambda *_: [_evento("us1", "150", 6.1)]})
    r3 = robo.rodar(engine, [USGS], None, cfg, agora=relogio,
                    conectores_eventos={"usgs": lambda *_: [_evento("us1", "200", 6.3)]})
    assert (r1.novos, r2.novos, so_data.novos, r3.novos) == (2, 0, 0, 1)
    with engine.connect() as c:
        assert len(c.execute(db.evento_local.select()).all()) == 3  # a versão antiga fica (regra 2)
    s = export.montar(engine, agora=lambda: AGORA)
    assert [(e["id"], e["magnitude"]) for e in s["terremotos"]] == [("us1", 6.3)]
    assert any(i["tipo"] == "terremoto" for i in s["faixa"])  # 6 ou mais vai para a faixa de baixo


def test_usgs_le_a_resposta_real():
    # Trecho real do feed (sonda de 21/10/2026, os 2 primeiros terremotos da resposta)
    from conftest import FIXTURES
    fiji, paquistao = conectores.interpretar_usgs((FIXTURES / "usgs_4.5_day.geojson").read_text(encoding="utf-8"))
    assert (fiji.ext_id, fiji.versao, fiji.magnitude) == ("us6000u3r3", "1792542098040", 4.9)
    assert fiji.titulo == "M 4.9 - south of the Fiji Islands" and (fiji.lat, fiji.lon) == (-25.502, 179.592)
    assert fiji.url == "https://earthquake.usgs.gov/earthquakes/eventpage/us6000u3r3"
    assert paquistao.ocorreu_em == datetime(2026, 10, 20, 23, 16, 43, 934000)  # "time" em milissegundos, UTC


@pytest.mark.parametrize("texto, motivo", [
    ("<html>erro</html>", "não é JSON"),
    ('{"type": "Feature"}', "não é uma coleção"),
    ('{"type": "FeatureCollection", "features": [{"id": "x", "properties": {}}]}', "sem os campos"),
    ('{"type": "FeatureCollection", "features": [{"id": "x", "properties": {"title": "M 5", "mag": 5, "time": 0, '
     '"updated": 0}, "geometry": {"coordinates": [200, 10, 5]}}]}', "fora do mapa"),
])
def test_usgs_formato_inesperado_e_erro(texto, motivo):
    with pytest.raises(ValueError, match=motivo):
        conectores.interpretar_usgs(texto)


def test_faixa_mostra_ponto_critico_e_ultimas_noticias(engine):
    _noticias(engine, [("aljazeera", "estado:QAT", "Missile strike on tanker in the Red Sea"),
                       ("bbc", "estado:GBR", "Houthis claim attack near Bab el-Mandeb")])
    faixa = export.montar(engine, agora=lambda: AGORA)["faixa"]
    assert faixa[0]["tipo"] == "ponto" and faixa[0]["id"] == "bab_el_mandeb"
    assert [i["tipo"] for i in faixa].count("noticia") == 2


def test_ponto_mostra_os_navios_por_dia_fora_do_mercado(engine):
    # Decisão 0018: navios por dia de Ormuz (PortWatch), pela média de 7 dias; não entram no painel de mercados
    import random
    from datetime import date
    from stratum import mercados
    from stratum.connectors.series import Observacao
    navios = [s for s in catalogo.SERIES if s["id"] in ("navios_ormuz", "petroleiros_ormuz")]
    with engine.begin() as c:
        db.gravar_fontes(c, [f for f in catalogo.FONTES if f["id"] == "portwatch"])
        db.gravar_series(c, navios)
    rnd, d, obs = random.Random(5), date(2019, 1, 1), []
    while d <= date(2026, 10, 11):
        obs += [Observacao("chokepoint6:n_total", d, float(round(rnd.gauss(100, 12)))),
                Observacao("chokepoint6:n_tanker", d, float(round(rnd.gauss(40, 6))))]
        d += timedelta(days=1)
    for i, v in enumerate([4, 0, 7, 2, 3, 7, 3]):  # 12 a 18/10/2026, como a sonda de 21/10 trouxe
        obs.append(Observacao("chokepoint6:n_total", date(2026, 10, 12) + timedelta(days=i), float(v)))
    mercados.gravar(engine, navios, obs, None, datetime(2026, 10, 21, 6))
    s = export.montar(engine, agora=lambda: AGORA)
    ormuz = next(p for p in s["pontos"]["lista"] if p["id"] == "ormuz")
    total = ormuz["navios"][0]
    assert (total["id"], total["data"], total["media_7d"], total["extremo"]) == ("navios_ormuz", "2026-10-18", 3.7, "baixa")
    assert 90 < total["um_ano_antes"] < 110 and total["contra_um_ano"] < -90 and len(total["ano"]) == 53
    assert ormuz["navios"][1]["id"] == "petroleiros_ormuz"
    assert not any(x["grupo"] == "navios" for x in s["mercados"]["series"])  # navio não é mercado
    assert any(i["tipo"] == "navios" and i["id"] == "ormuz" for i in s["faixa"])
