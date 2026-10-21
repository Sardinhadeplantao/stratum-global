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


def test_bce_pede_uma_moeda_por_vez():
    # Na produção, as 13 moedas de 11 anos num pedido só passaram de 60 segundos (21/10)
    f = next(f for f in catalogo.FONTES if f["id"] == "bce_cambio")
    sessao = SessaoCsv((FIXTURES / "bce_exr.csv").read_bytes())
    conectores.ler_bce(f, [{"codigo": "USD"}, {"codigo": "JPY"}], sessao, "teste", date(2015, 1, 1))
    assert sessao.chamadas == [
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2015-01-01&format=csvdata&detail=dataonly",
        "https://data-api.ecb.europa.eu/service/data/EXR/D.JPY.EUR.SP00.A?startPeriod=2015-01-01&format=csvdata&detail=dataonly"]


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


def test_status_traz_o_ultimo_mes_quem_sobe_e_quem_cai_e_os_destaques(engine, cfg):
    # Decisão 0014: o minigráfico, a contagem de altas e quedas e os quadros de destaque saem prontos do robô
    from stratum import mercados
    yahoo = next(f for f in catalogo.FONTES if f["id"] == "yahoo_cambio")
    series = [s for s in catalogo.SERIES if s["id"] in ("bce_brl", "bce_usd", "yahoo_brl")]
    dias = _dias_uteis(1300, date(2021, 6, 1))
    reais = {d: 6 + ((i * 7) % 11) / 1000 for i, d in enumerate(dias)}
    dolares = {d: 1.1 + ((i * 5) % 7) / 1000 for i, d in enumerate(dias)}
    reais[dias[-1]] = reais[dias[-2]] + 0.004      # o real sobe no último dia
    dolares[dias[-1]] = dolares[dias[-2]] - 0.004  # o dólar cai

    def bce(f, ss, *_):
        return [Observacao("BRL", d, v) for d, v in reais.items()] + [Observacao("USD", d, v) for d, v in dolares.items()]

    def mercado(f, ss, *_):
        return [Observacao("BRL=X", d, round(reais[d] / dolares[d], 4)) for d in dias]

    relogio = Relogio(datetime.combine(dias[-1], datetime.min.time()) + timedelta(hours=18))
    robo.rodar(engine, [BCE, yahoo], None, cfg, agora=relogio, series=series,
               conectores_series={"bce": bce, "yahoo": mercado})
    m = export.montar(engine, agora=relogio)["mercados"]
    por_id = {x["id"]: x for x in m["series"]}
    assert por_id["bce_brl"]["mes"] == [v for d, v in sorted(reais.items()) if (dias[-1] - d).days < 30]
    assert len(por_id["bce_usd"]["mes"]) in (21, 22, 23)  # um mês de dias úteis
    assert m["amplitude"] == {"sobem": 2, "caem": 1, "estaveis": 0, "proporcao_sobem": 0.667,
                              "por_grupo": {"moedas": {"sobem": 2, "caem": 1, "estaveis": 0}}}
    assert m["destaques"] == [{"id": "yahoo_brl", "rotulo": mercados.DESTAQUES["yahoo_brl"]}]  # só os da lista que existem


def test_trocas_de_contrato_so_os_dias_da_troca(engine):
    # O banco devolve só os dias da troca (revisão de 21/10: ler a tabela inteira a cada rodada cresceria sem parar)
    from stratum import mercados
    commodities = next(f for f in catalogo.FONTES if f["id"] == "yahoo_commodities")
    wti = next(s for s in catalogo.SERIES if s["id"] == "commodity_cl")
    t0 = datetime(2026, 10, 20, 12)
    with engine.begin() as c:
        db.gravar_fontes(c, [commodities])
        db.gravar_series(c, [wti])
        c.execute(db.contrato_futuro.insert(), [
            dict(serie_id="commodity_cl", data=d, contrato=k, conhecido_em=t) for d, k, t in [
                (date(2026, 10, 15), "Nov 26", t0), (date(2026, 10, 16), "Nov 26", t0),
                (date(2026, 10, 19), "Dec 26", t0),                                        # troca
                (date(2026, 10, 20), "Dec 26", t0), (date(2026, 10, 20), "Jan 27", t0 + timedelta(hours=1))]])
    with engine.connect() as c:
        # no mesmo dia vale o último contrato conhecido; antes dele, o sistema não sabia da segunda troca
        assert mercados.trocas_de_contrato(c, t0 + timedelta(hours=2)) == {
            "commodity_cl": {date(2026, 10, 19), date(2026, 10, 20)}}
        assert mercados.trocas_de_contrato(c, t0 + timedelta(minutes=30)) == {"commodity_cl": {date(2026, 10, 19)}}
        assert mercados.trocas_de_contrato(c, t0 - timedelta(minutes=1)) == {}


def test_toda_bolsa_tem_regiao():
    bolsas = [s for s in catalogo.SERIES if s["grupo"] == "bolsas"]
    assert all(s.get("regiao") in catalogo.REGIOES for s in bolsas)
    assert {s["regiao"] for s in bolsas} == set(catalogo.REGIOES)


def test_juros_medem_a_diferenca_em_pontos():
    # Decisão 0011: taxa se mede em pontos percentuais; 4,00% -> 4,10% é +0,10 ponto, não +2,5%
    assert regua.diferenca([(date(2026, 10, 19), 4.0), (date(2026, 10, 20), 4.1)])[0][1] == pytest.approx(0.1)
    normais = [((i * 7) % 11 - 5) / 100 for i in range(1300)]       # de -0,05 a +0,05 ponto por dia
    dias = _dias_uteis(1302)
    taxa, pontos = 4.0, []
    for d, m in zip(dias, [0.0] + normais + [0.25]):
        taxa += m
        pontos.append((d, taxa))
    lido = regua.ler(pontos, medida="diferenca")
    assert lido.medida == pytest.approx(0.25) and lido.extremo == "alta"


# Juros oficiais (decisão 0013): amostras reais da sonda de 21/10/2026

def test_tesouro_le_a_coluna_de_10_anos():
    obs = conectores.interpretar_tesouro((FIXTURES / "tesouro_2026.csv").read_text(), "10 Yr")
    assert obs[-1] == Observacao("10 Yr", date(2026, 10, 20), 5.12) and obs[0].data == date(2026, 10, 14)
    assert len(obs) == 5


def test_tesouro_pede_um_arquivo_por_ano():
    f = next(f for f in catalogo.FONTES if f["id"] == "tesouro_eua")
    assert conectores.url_tesouro(f, 2015).endswith("/2015/all?type=daily_treasury_yield_curve"
                                                    "&field_tdr_date_value=2015&page&_format=csv")


def test_bundesbank_pula_a_descricao_e_o_dia_sem_valor():
    codigo = "BBSIS.D.I.ZAR.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A"
    obs = conectores.interpretar_bundesbank((FIXTURES / "bundesbank_10a.csv").read_text(), codigo)
    assert obs == [Observacao(codigo, date(2026, 10, 19), 3.46), Observacao(codigo, date(2026, 10, 20), 3.45)]
    f = next(f for f in catalogo.FONTES if f["id"] == "bundesbank")
    assert conectores.url_bundesbank(f, codigo, date(2026, 10, 9)) == (
        "https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZAR.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A"
        "?format=csv&lang=en&startPeriod=2026-10-09")
    with pytest.raises(ValueError, match="não traz a série"):
        conectores.interpretar_bundesbank((FIXTURES / "bundesbank_10a.csv").read_text(), "BBSIS.OUTRA")


def test_banco_da_inglaterra_le_a_data_em_ingles():
    obs = conectores.interpretar_boe((FIXTURES / "boe_iudmnpy.csv").read_text(), "IUDMNPY")
    assert obs[0] == Observacao("IUDMNPY", date(2026, 10, 9), 5.3993) and obs[-1].valor == 5.3092
    f = next(f for f in catalogo.FONTES if f["id"] == "boe")
    assert "Datefrom=09/Oct/2026&Dateto=now&SeriesCodes=IUDMNPY" in conectores.url_boe(f, "IUDMNPY", date(2026, 10, 9))


def test_japao_le_o_mes_e_o_historico():
    mes = conectores.interpretar_japao((FIXTURES / "japao_mes.csv").read_text(), "10Y")
    assert mes[-1] == Observacao("10Y", date(2026, 10, 19), 2.935) and len(mes) == 5  # as notas do fim não entram
    historico = conectores.interpretar_japao((FIXTURES / "japao_historico.csv").read_text(), "10Y")
    assert [o.data for o in historico] == [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30)]  # 1974 não tinha 10Y


def test_japao_so_le_o_historico_quando_precisa():
    f = next(f for f in catalogo.FONTES if f["id"] == "japao_mof")
    mes, historico = (FIXTURES / "japao_mes.csv").read_bytes(), (FIXTURES / "japao_historico.csv").read_bytes()

    class Sessao:
        chamadas = []

        def get(self, url, headers=None, timeout=None):
            self.chamadas.append(url.rsplit("/", 1)[1])
            return Resposta(historico if "historical" in url else mes)

    s = Sessao()
    conectores.ler_japao(f, [{"codigo": "10Y"}], s, "teste", date.today().replace(day=1))
    assert s.chamadas == ["jgbcme.csv"]
    obs = conectores.ler_japao(f, [{"codigo": "10Y"}], s, "teste", date(2026, 9, 29))
    assert s.chamadas[1:] == ["jgbcme.csv", "jgbcme_all.csv"] and obs[0].data == date(2026, 9, 29)


def test_yahoo_aceita_preco_negativo_que_aconteceu():
    # O WTI fechou a -37,63 dólares em 20/04/2020 (sonda de 21/10: a recusa derrubava a série inteira)
    real = (FIXTURES / "yahoo_brl.json").read_text().replace("4.985899925231934", "-37.630001068115234", 1)
    assert conectores.interpretar_yahoo(real, "BRL=X")[0].valor == -37.63
    nan = (FIXTURES / "yahoo_brl.json").read_text().replace("4.985899925231934", "NaN", 1)
    with pytest.raises(ValueError, match="ilegível"):
        conectores.interpretar_yahoo(nan, "BRL=X")


# Cópia local das cotações (revisão de 21/10: ler tudo a cada rodada gastaria uns 17 GB/mês do Supabase gratuito)

def _encher_cotacoes(engine, dias, inicio=date(2021, 6, 1), conhecido=datetime(2026, 10, 20, 12)):
    from stratum import mercados
    with engine.begin() as c:
        db.gravar_fontes(c, [BCE])
        db.gravar_series(c, [BRL])
    obs = [Observacao("BRL", d, 6 + ((i * 7) % 11) / 1000) for i, d in enumerate(_dias_uteis(dias, inicio))]
    mercados.gravar(engine, [BRL], obs, None, conhecido)


def test_copia_local_so_pede_ao_banco_o_que_e_novo(engine, tmp_path):
    from stratum import mercados
    caminho = str(tmp_path / "cache" / "observacoes.json.gz")
    _encher_cotacoes(engine, 300)
    with engine.connect() as c:
        _, origem = mercados.carregar(c, caminho)
    assert origem == {"da_copia": 0, "do_banco": 300}
    mercados.gravar(engine, [BRL], [Observacao("BRL", date(2026, 10, 21), 6.5)], None, datetime(2026, 10, 21, 15))
    with engine.connect() as c:
        com_copia, origem = mercados.carregar(c, caminho)
        sem_copia, _ = mercados.carregar(c)
    assert origem == {"da_copia": 300, "do_banco": 1}
    assert com_copia == sem_copia  # o mesmo resultado, lendo só a linha nova


def test_copia_local_e_descartada_se_o_banco_mudou(engine, tmp_path):
    # Banco recriado (restauração, projeto novo): o último id da cópia não bate e tudo é lido de novo
    from stratum import mercados
    caminho = str(tmp_path / "observacoes.json.gz")
    _encher_cotacoes(engine, 300)
    with engine.connect() as c:
        mercados.carregar(c, caminho)
    outro = db.conectar(f"sqlite:///{tmp_path / 'outro.db'}")
    db.preparar(outro)
    _encher_cotacoes(outro, 200, inicio=date(2022, 1, 3))
    with outro.connect() as c:
        dados, origem = mercados.carregar(c, caminho)
        sem_copia, _ = mercados.carregar(c)
    assert origem == {"da_copia": 0, "do_banco": 200} and dados == sem_copia
    (tmp_path / "observacoes.json.gz").write_bytes(b"estragada")
    with outro.connect() as c:
        assert mercados.carregar(c, caminho)[1] == {"da_copia": 0, "do_banco": 200}


def test_status_igual_com_e_sem_copia_local(engine, cfg, tmp_path, monkeypatch):
    _encher_cotacoes(engine, 1300)
    momento = datetime(2026, 10, 21, 12)
    sem = export.montar(engine, agora=lambda: momento)["mercados"]
    monkeypatch.setenv("STRATUM_CACHE_OBSERVACOES", str(tmp_path / "observacoes.json.gz"))
    export.montar(engine, agora=lambda: momento)                       # primeira rodada: cria a cópia
    com = export.montar(engine, agora=lambda: momento)["mercados"]     # segunda: usa a cópia
    assert com == sem


def test_mesma_data_duas_vezes_na_mesma_leitura_entra_uma_vez(engine):
    from stratum import mercados
    with engine.begin() as c:
        db.gravar_fontes(c, [BCE])
        db.gravar_series(c, [BRL])
    dupla = [Observacao("BRL", date(2026, 9, 30), 6.1), Observacao("BRL", date(2026, 9, 30), 6.2)]
    assert mercados.gravar(engine, [BRL], dupla, None, datetime(2026, 10, 1)) == 1
    assert mercados.gravar(engine, [BRL], dupla, None, datetime(2026, 10, 1, 1)) == 0  # e não volta a cada leitura
