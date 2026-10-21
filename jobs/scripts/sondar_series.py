"""Sonda as fontes de séries (decisão 0011) do jeito que o robô lê, e mostra o começo do arquivo bruto.

Roda no GitHub Actions (workflow sondar.yml), porque a máquina do Claude não alcança o BCE nem o FRED. O trecho
bruto impresso vira a amostra real guardada em tests/fixtures (regra de fonte nova). Nada é gravado.

Também sonda candidatas a série nova (fase 2: juros, bolsas, commodities e cripto): se respondem, quantos anos de
histórico têm e o formato bruto. Nada entra em fontes.py sem passar por aqui.

Uso:  python scripts/sondar_series.py
"""
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stratum import config, fontes  # noqa: E402
from stratum.connectors import rss, series as conectores  # noqa: E402


# Candidatas no Yahoo (decisão 0012): índice principal da bolsa de cada membro do G20, commodities e cripto
YAHOO = {
    "bolsas": ["^GSPC", "^BVSP", "000001.SS", "^N225", "^NSEI", "^FTSE", "^GDAXI", "^FCHI", "FTSEMIB.MI", "^GSPTSE",
               "^AXJO", "^KS11", "^MXX", "^JKSE", "XU100.IS", "^J203.JO", "^TASI.SR", "^MERV", "IMOEX.ME", "^STOXX50E"],
    "commodities": ["BZ=F", "CL=F", "NG=F", "TTF=F", "GC=F", "SI=F", "HG=F", "ALI=F", "ZW=F", "ZC=F", "ZS=F"],
    "cripto": ["BTC-USD", "ETH-USD"],
    "juros": ["^TNX"],
}
# Candidatas oficiais de juros de 10 anos (plano da fase 2: Tesouro dos EUA, BCE, Bundesbank, Banco da Inglaterra, Japão)
OFICIAIS = {
    "tesouro_eua": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
                   "{ano}/all?type=daily_treasury_yield_curve&field_tdr_date_value={ano}&page&_format=csv",
    "bce_curva_aaa": "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
                     "?startPeriod={inicio}&format=csvdata&detail=dataonly",
    "bce_curva_todos": "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y"
                       "?startPeriod={inicio}&format=csvdata&detail=dataonly",
    "bundesbank": "https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZAR.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A"
                  "?format=csv&lang=en&startPeriod={inicio}",
    "boe": "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom={inicio_boe}"
           "&Dateto=now&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N",
    "japao_mes": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv",
    "japao_historico": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv",
}


def sondar_candidatas(sessao, ua) -> None:
    f = {"url": "https://query1.finance.yahoo.com/v8/finance/chart/"}
    ate = int(time.time()) + 86400
    for grupo, codigos in ({} if "--so-contratos" in sys.argv else YAHOO).items():
        print(f"== Candidatas no Yahoo: {grupo}")
        for codigo in codigos:
            url = conectores.url_yahoo(f, codigo, date(2015, 1, 1), ate)
            try:
                bruto = conectores._baixar(sessao, url, ua)
                meta = json.loads(bruto)["chart"]["result"][0]["meta"]
                obs = conectores.interpretar_yahoo(bruto.replace(f'"symbol":"{meta["symbol"]}"', f'"symbol":"{codigo}"'),
                                                   codigo)
                print(f"OK {codigo}: volta como {meta['symbol']}, {meta.get('longName') or meta.get('shortName')}, "
                      f"{meta.get('currency')}, {meta.get('exchangeTimezoneName')}; {len(obs)} dias de "
                      f"{obs[0].data if obs else '-'} a {obs[-1].data if obs else '-'} = {obs[-1].valor if obs else '-'}")
            except Exception as exc:  # noqa: BLE001 - a sonda só relata
                print(f"FALHOU {codigo}: {type(exc).__name__}: {str(exc)[:120]}")
    print("== Terremotos (USGS, decisão 0014): resposta bruta e o que o leitor entende")
    from stratum.connectors import eventos
    usgs = next(x for x in fontes.FONTES if x["id"] == "usgs_terremotos")
    try:
        bruto = conectores._baixar(sessao, usgs["url"], ua)
        dados = json.loads(bruto)
        print(f"::group::Bruto do USGS [{usgs['url']}]\n" + json.dumps({**dados, "features": dados["features"][:2]})[:5000]
              + "\n::endgroup::")
        lidos = eventos.interpretar_usgs(bruto)
        print(f"OK usgs_terremotos: {len(lidos)} terremotos; mais forte: "
              f"{max(lidos, key=lambda e: e.magnitude or 0) if lidos else '-'}")
    except Exception as exc:  # noqa: BLE001
        print(f"FALHOU usgs_terremotos: {type(exc).__name__}: {str(exc)[:160]}")
    print("== Contratos futuros: o Yahoo diz qual contrato vale? (troca de contrato, decisão 0013)")
    for codigo in ["CL=F", "BZ=F", "NG=F", "TTF=F", "GC=F", "ZW=F", "CLX26.NYM", "CLZ26.NYM", "BZZ26.NYM", "BZF27.NYM"]:
        url = conectores.url_yahoo(f, codigo, date.today() - timedelta(days=8), ate)
        try:
            r = json.loads(conectores._baixar(sessao, url, ua))["chart"]["result"][0]
            meta, q = r["meta"], r["indicators"]["quote"][0]["close"]
            dias = [str(datetime.fromtimestamp(t, timezone.utc).date()) for t in r.get("timestamp") or []]
            print(f"{codigo}: chaves={sorted(meta)}")
            print(f"  nomes: short={meta.get('shortName')!r} long={meta.get('longName')!r} "
                  f"expira={meta.get('expireDate')} contrato={meta.get('underlyingSymbol')}")
            print(f"  preço {meta.get('regularMarketPrice')} em {meta.get('regularMarketTime')}; "
                  f"anterior {meta.get('chartPreviousClose')}/{meta.get('previousClose')}; "
                  f"fechamentos {list(zip(dias, q))[-4:]}")
        except Exception as exc:  # noqa: BLE001
            print(f"FALHOU {codigo}: {type(exc).__name__}: {str(exc)[:120]}")
    hoje = date.today()
    inicio = hoje - timedelta(days=12)
    print("== Candidatas oficiais de juros de 10 anos")
    for nome, modelo in OFICIAIS.items():
        url = modelo.format(ano=hoje.year, inicio=inicio.isoformat(), inicio_boe=inicio.strftime("%d/%b/%Y"))
        try:
            r = sessao.get(url, headers={"User-Agent": ua}, timeout=60)
            linhas = r.content.decode("utf-8-sig", errors="replace").splitlines()
            print(f"::group::{nome}: HTTP {r.status_code}, {len(linhas)} linhas [{url}]")
            print("\n".join(l[:400] for l in linhas[:6]))
            if len(linhas) > 9:
                print("...\n" + "\n".join(l[:400] for l in linhas[-3:]))
            print("::endgroup::")
        except Exception as exc:  # noqa: BLE001
            print(f"FALHOU {nome}: {type(exc).__name__}: {str(exc)[:120]}  [{url}]")


def main() -> None:
    sessao, ua = rss.nova_sessao(), config.ler().user_agent
    desde = date.today() - timedelta(days=10)
    for f in fontes.ativas():
        if f["conector"] not in conectores.CONECTORES:
            continue
        da_fonte = [s for s in fontes.SERIES if s["fonte"] == f["id"] and s.get("ativa", True)]
        amostra = da_fonte[:2] if f["conector"] == "bce" else da_fonte[:1]
        url = {"bce": lambda: conectores.url_bce(f, [s["codigo"] for s in amostra], desde),
               "fred": lambda: conectores.url_fred(f, amostra[0]["codigo"], desde),
               "yahoo": lambda: conectores.url_yahoo(f, amostra[0]["codigo"], desde, int(time.time()) + 86400),
               }.get(f["conector"], lambda: None)()  # os juros têm o bruto na sonda das candidatas
        try:
            if url:
                bruto = conectores._baixar(sessao, url, ua)
                print(f"::group::Bruto de {f['id']} [{url}]\n" + "\n".join(bruto.splitlines()[:12])[:6000] + "\n::endgroup::")
            obs = conectores.CONECTORES[f["conector"]](f, da_fonte, sessao, ua, desde)
        except Exception as exc:  # noqa: BLE001 - a sonda só relata
            print(f"FALHOU {f['id']}: {type(exc).__name__}: {str(exc)[:160]}  [{url}]")
            if f["conector"] == "yahoo":  # diagnóstico: a recusa é pelo nome do robô (User-Agent)?
                r = sessao.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                print(f"  com User-Agent de navegador: HTTP {r.status_code}, {len(r.content)} bytes")
            continue
        por_codigo: dict[str, list] = {}
        for o in obs:
            por_codigo.setdefault(o.codigo, []).append(o)
        faltam = [s["codigo"] for s in da_fonte if s["codigo"] not in por_codigo]
        print(f"OK {f['id']}: {len(obs)} observações de {len(por_codigo)} séries"
              + (f"; sem dado: {', '.join(faltam)}" if faltam else ""))
        for codigo, lista in sorted(por_codigo.items()):
            print(f"  {codigo}: {lista[-1].data} = {lista[-1].valor}")


if __name__ == "__main__":
    main()
    sondar_candidatas(rss.nova_sessao(), config.ler().user_agent)
