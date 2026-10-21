"""Séries de mercado (decisão 0011): régua, leitores do BCE e do FRED e a rodada do robô com dados."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import func, select

from conftest import FIXTURES, Relogio, Resposta, fonte
from stratum import db, export, robo
from stratum import fontes as catalogo
from stratum.connectors import series as conectores
from stratum.connectors.series import Observacao
from stratum.domain import regua


def _dias_uteis(n, inicio=date(2020, 1, 1)):
    d, saida = inicio, []
    while len(saida) < n:
        if d.weekday() < 5:
            saida.append(d)
        d += timedelta(days=1)
    return saida


def _de_medidas(medidas, inicio=date(2020, 1, 1)):
    """Pontos cuja variação diária é exatamente `medidas` (em %)."""
    dias = _dias_uteis(len(medidas) + 1, inicio)
    v, pontos = 100.0, [(dias[0], 100.0)]
    for d, m in zip(dias[1:], medidas):
        v *= 1 + m / 100
        pontos.append((d, v))
    return pontos


# Régua

def test_percentil_conta_empates_pela_metade():
    assert regua.percentil(2, [1, 2, 3, 4]) == 37.5
    assert regua.percentil(0, [1, 2]) == 0 and regua.percentil(9, [1, 2]) == 100


def test_janela_e_de_cinco_anos_sem_o_proprio_ponto():
    medidas = [(date(2015, 1, 1), 50.0)] + [(date(2021, 1, 1) + timedelta(days=i), float(i % 10)) for i in range(300)]
    ps = regua.percentis(medidas, minimo=250)
    # o 50 de 2015 está fora da janela de 5 anos: não conta para o mínimo, e um 9 não fica abaixo dele
    assert ps[0] is None and ps[250] is None and ps[251] is not None
    assert ps[-1] == regua.percentil(9.0, sorted(v for _, v in medidas[1:-1]))


def test_extremo_que_persiste_vem_com_a_taxa_base():
    normais = [((i * 7) % 11 - 5) / 10 for i in range(1300)]          # entre -0,5% e +0,5%
    medidas = normais[:600] + [3.0, 3.0] + normais[600:1200] + [2.0, 2.5]  # um episódio antes; outro agora
    lido = regua.ler(_de_medidas(medidas))
    assert lido.extremo == "alta" and lido.percentil > 95
    [m] = [m for m in lido.mudancas if m["tipo"] == "extremo_persiste"]
    assert m["sentido"] == "alta" and m["taxa_base"]["vezes"] == 1
    assert m["desde"] == _de_medidas(medidas)[-2][0]  # o primeiro dos dois dias fora do normal
    assert 0 < m["taxa_base"]["anos"] <= 5


def test_um_dia_fora_do_normal_nao_e_mudanca():
    normais = [((i * 7) % 11 - 5) / 10 for i in range(1300)]
    lido = regua.ler(_de_medidas(normais + [3.0]))
    assert lido.extremo == "alta" and not [m for m in lido.mudancas if m["tipo"] == "extremo_persiste"]


def test_quebra_de_ritmo_quando_a_agitacao_sai_do_normal():
    calmas = [0.5 if i % 2 else -0.5 for i in range(1300)]          # agitação sempre igual: nunca quebrou
    agitadas = [(-1) ** i * 4.0 for i in range(20)]                 # 20 dias de vai e volta de 4%
    lido = regua.ler(_de_medidas(calmas + agitadas))
    [m] = [m for m in lido.mudancas if m["tipo"] == "quebra_de_ritmo"]
    assert m["taxa_base"]["vezes"] == 0


def test_faixa_normal_e_pontuacao():
    normais = [((i * 7) % 11 - 5) / 10 for i in range(1300)]
    lido = regua.ler(_de_medidas(normais + [3.0]))
    baixo, alto = lido.faixa
    assert baixo < 0 < alto and lido.pontuacao > 3
    assert regua.ler(_de_medidas(normais + [6.0])).pontuacao > lido.pontuacao  # ordena dentro dos extremos


# Leitores

def test_bce_le_as_taxas_de_referencia():
    obs = conectores.interpretar_bce((FIXTURES / "bce_exr.csv").read_text())  # trecho real de 20/10
    assert Observacao("JPY", date(2026, 10, 20), 177.34) in obs and Observacao("USD", date(2026, 10, 15), 1.1208) in obs
    assert len(obs) == 11


def test_bce_endereco_pede_todas_as_moedas_numa_chamada():
    f = next(f for f in catalogo.FONTES if f["id"] == "bce_cambio")
    url = conectores.url_bce(f, ["USD", "BRL"], date(2015, 1, 1))
    assert url == ("https://data-api.ecb.europa.eu/service/data/EXR/D.USD+BRL.EUR.SP00.A"
                   "?startPeriod=2015-01-01&format=csvdata&detail=dataonly")


def test_fred_le_o_csv():
    obs = conectores.interpretar_fred((FIXTURES / "fred_dtwexbgs.csv").read_text(), "DTWEXBGS")  # trecho real de 20/10
    assert obs[-1] == Observacao("DTWEXBGS", date(2026, 10, 16), 121.4048) and len(obs) == 4


def test_fred_feriado_e_ausencia_de_dado_nao_zero():
    # Caso de borda do formato (o FRED deixa o valor vazio no feriado): vira falta de dado, nunca zero
    obs = conectores.interpretar_fred("observation_date,DTWEXBGS\n2026-10-13,121.4433\n2026-10-14,\n", "DTWEXBGS")
    assert [o.data for o in obs] == [date(2026, 10, 13)]


@pytest.mark.parametrize("texto, codigo", [
    ("DATE,DEXJPUS\n2026-10-08,150.1\n", "DEXBZUS"),           # outra série
    ("<html>erro</html>", "DEXBZUS"),
    ("observation_date,DEXBZUS\n2026-10-08,abc\n", "DEXBZUS"),  # valor ilegível
])
def test_fred_formato_inesperado_e_erro(texto, codigo):
    with pytest.raises(ValueError) as e:
        conectores.interpretar_fred(texto, codigo)
    assert robo.erro_legivel(e.value).startswith("O arquivo da fonte mudou de formato")


def test_bce_sem_as_colunas_e_erro():
    with pytest.raises(ValueError, match="faltam as colunas"):
        conectores.interpretar_bce("KEY,TIME_PERIOD\nEXR.D.BRL.EUR.SP00.A,2026-10-16\n")


class SessaoCsv:
    def __init__(self, conteudo: bytes):
        self.conteudo, self.chamadas = conteudo, []

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append(url)
        return Resposta(self.conteudo)


def test_fred_uma_chamada_por_serie():
    f = next(f for f in catalogo.FONTES if f["id"] == "fred_cambio")
    sessao = SessaoCsv((FIXTURES / "fred_dtwexbgs.csv").read_bytes())
    obs = conectores.ler_fred(f, [{"codigo": "DTWEXBGS"}], sessao, "teste", date(2026, 10, 1))
    assert sessao.chamadas == ["https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS&cosd=2026-10-01"]
    assert len(obs) == 4


def test_yahoo_le_a_resposta_real():
    # Resposta real do Yahoo para o dólar em reais (sonda de 21/10/2026, 00:10 UTC)
    obs = conectores.interpretar_yahoo((FIXTURES / "yahoo_brl.json").read_text(), "BRL=X")
    assert [o.data for o in obs] == [date(2026, 10, d) for d in (12, 13, 14, 15, 16, 19, 20)]  # 21/10 sem preço ainda
    assert obs[0] == Observacao("BRL=X", date(2026, 10, 12), 4.9859)  # 4.985899925231934 com 6 algarismos
    assert obs[-1].valor == 5.0238  # o último preço de 20/10, não a barra atrasada (5,0370); o BCE dava 5,0236


def test_yahoo_aceita_o_par_com_o_dolar_na_frente():
    real = (FIXTURES / "yahoo_brl.json").read_text()
    assert conectores.interpretar_yahoo(real.replace('"symbol":"BRL=X"', '"symbol":"USDBRL=X"'), "BRL=X")
    with pytest.raises(ValueError, match="esperado BRL=X"):
        conectores.interpretar_yahoo(real.replace('"symbol":"BRL=X"', '"symbol":"EURBRL=X"'), "BRL=X")


def test_yahoo_endereco_por_serie():
    f = next(f for f in catalogo.FONTES if f["id"] == "yahoo_cambio")
    assert conectores.url_yahoo(f, "BRL=X", date(2015, 1, 1), 1800000000) == (
        "https://query1.finance.yahoo.com/v8/finance/chart/BRL%3DX?period1=1420070400&period2=1800000000&interval=1d")


@pytest.mark.parametrize("texto, motivo", [
    ('{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found"}}}', "sem cotações"),
    ('<html>Too Many Requests</html>', "não é JSON"),
    ('{"chart":{"result":[{"meta":{"symbol":"JPY=X","exchangeTimezoneName":"Europe/London"},"timestamp":[1],'
     '"indicators":{"quote":[{"close":[150.1]}]}}],"error":null}}', "esperado BRL=X"),
])
def test_yahoo_resposta_inesperada_e_erro(texto, motivo):
    # Casos de borda do formato: erro da fonte, página de bloqueio, outra moeda
    with pytest.raises(ValueError, match=motivo):
        conectores.interpretar_yahoo(texto, "BRL=X")


# Robô

BCE = next(f for f in catalogo.FONTES if f["id"] == "bce_cambio")
BRL = next(s for s in catalogo.SERIES if s["id"] == "bce_brl")


def test_rodada_grava_as_cotacoes_no_ritmo_da_fonte(engine, cfg):
    pedidos = []

    def falso(f, series, session, user_agent, desde):
        pedidos.append(desde)
        return [Observacao("BRL", date(2026, 10, 15), 6.31), Observacao("BRL", date(2026, 10, 16), 6.33)]

    relogio = Relogio(datetime(2026, 10, 16, 18))
    kw = dict(series=[BRL], conectores_series={"bce": falso})
    r1 = robo.rodar(engine, [BCE], None, cfg, agora=relogio, **kw)
    r2 = robo.rodar(engine, [BCE], None, cfg, agora=relogio, **kw)               # minutos depois: ainda não
    relogio.t += timedelta(hours=3)
    r3 = robo.rodar(engine, [BCE], None, cfg, agora=relogio, **kw)
    assert (r1.novos, r2.novos, r3.novos) == (2, 0, 0) and r2.situacao == "ok"
    assert pedidos == [date(2015, 1, 1), date(2026, 9, 15)]  # o histórico inteiro; depois, só o último mês
    with engine.connect() as c:
        assert c.execute(select(func.count()).select_from(db.observacao)).scalar() == 2
        assert c.execute(select(func.count()).select_from(db.coleta)).scalar() == 2  # a rodada pulada não coleta


def test_falha_da_fonte_de_dados_nao_derruba_as_noticias(engine, cfg, feed_rss):
    from conftest import SessaoFalsa

    def quebrado(*_):
        raise ValueError("formato inesperado: faltam as colunas OBS_VALUE")

    r = robo.rodar(engine, [fonte("a", "https://a/feed"), BCE], SessaoFalsa({"https://a/feed": feed_rss}), cfg,
                   agora=Relogio(), series=[BRL], conectores_series={"bce": quebrado})
    assert r.situacao == "parcial" and r.falhas == ["bce_cambio"] and r.novos == 2


def test_status_traz_as_series_com_a_regua(engine, cfg):
    dias = _dias_uteis(1300, date(2021, 6, 1))
    obs = [Observacao("BRL", d, 6 + ((i * 7) % 11) / 1000) for i, d in enumerate(dias)]
    relogio = Relogio(datetime.combine(dias[-1], datetime.min.time()) + timedelta(hours=18))
    robo.rodar(engine, [BCE], None, cfg, agora=relogio, series=[BRL], conectores_series={"bce": lambda *_: obs})
    s = export.montar(engine, agora=relogio)
    m = s["mercados"]
    assert m["regua"]["versao"] == regua.REGUA and m["regua"]["janela_anos"] == 5
    [serie] = m["series"]
    assert serie["id"] == "bce_brl" and serie["situacao"] == "ok" and serie["percentil"] is not None
    assert serie["fonte_nome"] == BCE["nome"] and serie["data"] == dias[-1].isoformat()
    assert next(f for f in s["fontes"] if f["id"] == "bce_cambio")["observacoes"] == 1300


def test_status_traz_a_conferencia_com_o_bce_e_o_dia_em_andamento(engine, cfg):
    yahoo = next(f for f in catalogo.FONTES if f["id"] == "yahoo_cambio")
    series = [s for s in catalogo.SERIES if s["id"] in ("bce_brl", "bce_usd", "yahoo_brl")]
    dias = _dias_uteis(1300, date(2021, 6, 1))
    reais = {d: 6 + ((i * 7) % 11) / 1000 for i, d in enumerate(dias)}
    dolares = {d: 1.1 + ((i * 5) % 7) / 1000 for i, d in enumerate(dias)}
    hoje = dias[-1] + timedelta(days=3 if dias[-1].weekday() == 4 else 1)

    def bce(f, ss, *_):
        return [Observacao("BRL", d, v) for d, v in reais.items()] + [Observacao("USD", d, v) for d, v in dolares.items()]

    def mercado(f, ss, *_):  # a conta do BCE em cada dia, mais o dia de hoje em andamento
        return [Observacao("BRL=X", d, round(reais[d] / dolares[d], 4)) for d in dias] + [Observacao("BRL=X", hoje, 5.5)]

    relogio = Relogio(datetime.combine(hoje, datetime.min.time()) + timedelta(hours=14))
    robo.rodar(engine, [BCE, yahoo], None, cfg, agora=relogio, series=series,
               conectores_series={"bce": bce, "yahoo": mercado})
    m = export.montar(engine, agora=relogio)["mercados"]
    por_id = {x["id"]: x for x in m["series"]}
    brl = por_id["yahoo_brl"]
    assert brl["parcial"] and brl["data"] == hoje.isoformat() and brl["conferir"]
    assert brl["conferencia"]["com"] == "BCE" and brl["conferencia"]["data"] == dias[-1].isoformat()
    assert brl["conferencia"]["confere"] and abs(brl["conferencia"]["diferenca"]) < 0.01
    assert not por_id["bce_brl"]["parcial"] and por_id["bce_brl"]["conferencia"] is None
    assert m["confere_ate_pct"] == 2.0 and m["nao_conferem"] == 0
