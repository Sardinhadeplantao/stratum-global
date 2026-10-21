"""Reação do mercado a cada evento (decisão 0017), no status.json: histórias e pontos críticos com os ativos ligados."""
import random
from datetime import date, datetime, timedelta

from stratum import db, export, historias, mercados
from stratum import fontes as catalogo
from stratum.connectors.series import Observacao
from test_historias import SOLTAS, T0, _inserir

BOLSA = next(s for s in catalogo.SERIES if s["id"] == "bolsa_bvsp")


def _cotacoes(engine, ultimo: date, salto: float):
    """1300 pregões do Ibovespa até a véspera de `ultimo`, calmos, e o dia `ultimo` com a variação `salto` (em %)."""
    rnd, dias, d = random.Random(7), [], ultimo - timedelta(days=1)
    while len(dias) < 1300:
        if d.weekday() < 5:
            dias.append(d)
        d -= timedelta(days=1)
    v, pontos = 100_000.0, []
    for d in reversed(dias):
        v *= 1 + rnd.gauss(0, 0.5) / 100
        pontos.append((d, v))
    pontos.append((ultimo, v * (1 + salto / 100)))
    with engine.begin() as c:
        db.gravar_fontes(c, [f for f in catalogo.FONTES if f["id"] == BOLSA["fonte"]])
        db.gravar_series(c, [BOLSA])
    mercados.gravar(engine, [BOLSA], [Observacao(BOLSA["codigo"], d, x) for d, x in pontos], None,
                    datetime.combine(ultimo, datetime.min.time()) + timedelta(hours=22))
    return pontos


def test_historia_mostra_a_reacao_sem_mudar_a_ordem(engine):
    pontos = _cotacoes(engine, T0.date(), salto=4.0)
    _inserir(engine, SOLTAS + [
        ("bbc_mundo", "Brazil central bank raises interest rates in surprise move"),
        ("aljazeera", "Brazil central bank raises interest rates in surprise move to fight inflation"),
        ("tass", "Russia and Iran sign gas pipeline agreement in Tehran"),
        ("bbc_mundo", "Russia and Iran sign gas pipeline agreement in Tehran talks"),
        ("dw_mundo", "Russia and Iran sign gas pipeline agreement after Tehran meeting"),
    ])
    momento = T0 + timedelta(days=1, hours=1)
    historias.atualizar(engine, momento)
    s = export.montar(engine, agora=lambda: momento)
    russia, brasil = s["historias"]
    # Preço é contexto (regra 8): a história com mais vozes continua primeiro, mesmo sem ativo ligado
    assert russia["vozes"] > brasil["vozes"]
    assert russia["reacao"]["situacao"] == "sem_ativo"  # Rússia e Irã não têm série acompanhada
    r = brasil["reacao"]
    assert r["situacao"] == "fora_do_normal" and r["fora"] == 1 and r["dia"] == T0.date().isoformat()
    bvsp = r["ativos"][0]
    assert (bvsp["id"], bvsp["simbolo"], bvsp["por"]["id"]) == ("bolsa_bvsp", "Ibovespa", "BRA")
    assert bvsp["base"]["data"] == pontos[-2][0].isoformat() and bvsp["dias"][0]["extremo"] == "alta"
    assert bvsp["desde"] == 4.0 and r["taxa_base"]["pct"] < 20


def test_ponto_em_pauta_mostra_a_reacao_e_sem_pauta_nao(engine):
    from test_mapa import AGORA, _noticias
    _noticias(engine, [("aljazeera", "estado:QAT", "Oil tanker on fire after hitting mine in Hormuz: Iran's Guards")])
    p = {x["id"]: x for x in export.montar(engine, agora=lambda: AGORA)["pontos"]["lista"]}
    assert p["ormuz"]["inicio"] == (AGORA - timedelta(hours=1)).isoformat() + "Z"
    assert p["ormuz"]["reacao"]["situacao"] == "sem_ativo"  # o banco do teste não tem o Brent
    assert p["panama"]["reacao"] is None
