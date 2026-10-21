"""Séries de dados (decisões 0011, 0012 e 0013): BCE, FRED, Yahoo Finance e os juros oficiais (Tesouro dos EUA,
Bundesbank, Banco da Inglaterra, Ministério das Finanças do Japão), todos sem chave. Devolvem observações; quem grava é
o robô. Cada formato foi conferido com a resposta real na sonda (scripts/sondar_series.py).

O formato é conferido na entrada: coluna que falta ou valor ilegível é erro, nunca um número inventado.
Valor vazio (feriado no FRED) é só ausência de dado.
"""
import csv
import io
import json
import math
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TEMPO_LIMITE = 60  # segundos: a primeira leitura traz 10 anos


@dataclass(frozen=True)
class Observacao:
    codigo: str        # o código da série na fonte (USD no BCE, DEXBZUS no FRED)
    data: date         # quando aconteceu (o dia da cotação)
    valor: float


def _baixar(session, url: str, user_agent: str, codificacao: str = "utf-8-sig") -> str:
    r = session.get(url, headers={"User-Agent": user_agent, "Accept": "text/csv, application/json, */*;q=0.5"},
                    timeout=TEMPO_LIMITE)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.content.decode(codificacao, errors="replace" if codificacao != "utf-8-sig" else "strict")


def _linhas(texto: str, exigidas: set[str]) -> list[dict]:
    leitor = csv.DictReader(io.StringIO(texto))
    faltam = exigidas - set(leitor.fieldnames or [])
    if faltam:
        raise ValueError(f"formato inesperado: faltam as colunas {', '.join(sorted(faltam))}")
    return list(leitor)


def _numero(texto: str, onde: str) -> float | None:
    texto = (texto or "").strip()
    if texto in ("", ".", "NaN", "N/A", "-"):
        return None
    try:
        return float(texto)
    except ValueError:
        raise ValueError(f"valor ilegível em {onde}: {texto[:20]!r}") from None


# BCE: taxas de referência do euro (dataset EXR), quantas unidades de cada moeda valem 1 euro
def url_bce(fonte: dict, codigos: list[str], desde: date) -> str:
    return (f"{fonte['url']}D.{'+'.join(codigos)}.EUR.SP00.A"
            f"?startPeriod={desde.isoformat()}&format=csvdata&detail=dataonly")


def interpretar_bce(texto: str) -> list[Observacao]:
    saida = []
    for linha in _linhas(texto, {"CURRENCY", "CURRENCY_DENOM", "TIME_PERIOD", "OBS_VALUE"}):
        if linha["CURRENCY_DENOM"] != "EUR":
            raise ValueError(f"formato inesperado: cotação contra {linha['CURRENCY_DENOM']}, não contra o euro")
        valor = _numero(linha["OBS_VALUE"], f"{linha['CURRENCY']} {linha['TIME_PERIOD']}")
        if valor is not None:
            saida.append(Observacao(linha["CURRENCY"], date.fromisoformat(linha["TIME_PERIOD"]), valor))
    return saida


def ler_bce(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    """Uma chamada só para todas as moedas."""
    return interpretar_bce(_baixar(session, url_bce(fonte, [s["codigo"] for s in series], desde), user_agent))


# FRED: um arquivo CSV por série (fredgraph.csv, sem chave)
def url_fred(fonte: dict, codigo: str, desde: date) -> str:
    return f"{fonte['url']}?id={codigo}&cosd={desde.isoformat()}"


def interpretar_fred(texto: str, codigo: str) -> list[Observacao]:
    leitor = csv.reader(io.StringIO(texto))
    cabecalho = next(leitor, None)
    if not cabecalho or len(cabecalho) < 2 or cabecalho[0] not in ("observation_date", "DATE") or cabecalho[1] != codigo:
        raise ValueError(f"formato inesperado: cabeçalho {','.join(cabecalho or [])[:60]!r}, esperado a data e {codigo}")
    saida = []
    for linha in leitor:
        if not linha:
            continue
        valor = _numero(linha[1] if len(linha) > 1 else "", f"{codigo} {linha[0]}")
        if valor is not None:
            saida.append(Observacao(codigo, date.fromisoformat(linha[0]), valor))
    return saida


def ler_fred(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    saida = []
    for s in series:
        saida += interpretar_fred(_baixar(session, url_fred(fonte, s["codigo"], desde), user_agent), s["codigo"])
    return saida


# Yahoo Finance: cotações de mercado, não oficiais (decisão 0012); um arquivo JSON por série, com o dia em andamento
def url_yahoo(fonte: dict, codigo: str, desde: date, ate: int) -> str:
    inicio = int(datetime(desde.year, desde.month, desde.day, tzinfo=timezone.utc).timestamp())
    return f"{fonte['url']}{quote(codigo)}?period1={inicio}&period2={ate}&interval=1d"


def _significativos(v: float) -> float:
    """6 algarismos significativos: a fonte manda 5.432100296020508 para 5,4321."""
    return float(f"{v:.6g}")


def interpretar_yahoo(texto: str, codigo: str) -> list[Observacao]:
    try:
        dados = json.loads(texto)
    except ValueError:
        raise ValueError("formato inesperado: a resposta não é JSON") from None
    chart = dados.get("chart") if isinstance(dados, dict) else None
    if not isinstance(chart, dict) or chart.get("error") or not chart.get("result"):
        motivo = (chart or {}).get("error") if isinstance(chart, dict) else None
        raise ValueError(f"formato inesperado: sem cotações ({str(motivo)[:80] if motivo else 'resposta vazia'})")
    r = chart["result"][0]
    meta = r.get("meta") or {}
    # O Yahoo às vezes devolve o mesmo par com o dólar escrito na frente (CAD=X volta como USDCAD=X); nada além disso
    if meta.get("symbol") not in (codigo, "USD" + codigo if codigo.endswith("=X") else codigo):
        raise ValueError(f"formato inesperado: veio {meta.get('symbol')!r}, esperado {codigo}")
    try:
        fuso = ZoneInfo(meta.get("exchangeTimezoneName") or "UTC")
    except ZoneInfoNotFoundError:
        raise ValueError(f"formato inesperado: fuso {meta.get('exchangeTimezoneName')!r}") from None
    instantes = r.get("timestamp") or []
    try:
        fechamentos = r["indicators"]["quote"][0]["close"] or []
    except (KeyError, IndexError, TypeError):
        raise ValueError("formato inesperado: faltam os fechamentos") from None
    if len(instantes) != len(fechamentos):
        raise ValueError("formato inesperado: datas e valores em número diferente")
    por_dia: dict[date, float] = {}
    for t, v in zip(instantes, fechamentos):
        if v is None:
            continue
        if not isinstance(v, (int, float)) or not math.isfinite(v):  # negativo vale: o WTI fechou a -37,63 em 2020
            raise ValueError(f"valor ilegível em {codigo}: {str(v)[:20]!r}")
        por_dia[datetime.fromtimestamp(t, fuso).date()] = _significativos(v)
    # O último preço negociado vale para o dia dele: a barra do dia demora a ser atualizada (em 20/10, a barra fechava
    # em 5,0370 e o último preço era 5,0238; a conta pelo BCE dava 5,0236). É também a oscilação do dia em andamento.
    preco, quando = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
    if isinstance(preco, (int, float)) and math.isfinite(preco) and isinstance(quando, int):
        por_dia[datetime.fromtimestamp(quando, fuso).date()] = _significativos(preco)
    return [Observacao(codigo, d, v) for d, v in sorted(por_dia.items())]


def ler_yahoo(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    ate = int(time.time()) + 86400
    saida = []
    for s in series:
        saida += interpretar_yahoo(_baixar(session, url_yahoo(fonte, s["codigo"], desde, ate), user_agent), s["codigo"])
    return saida


# Juros oficiais de 10 anos (decisão 0013)
def _desde(obs: list[Observacao], desde: date) -> list[Observacao]:
    return sorted((o for o in obs if o.data >= desde), key=lambda o: (o.codigo, o.data))


def url_tesouro(fonte: dict, ano: int) -> str:
    return f"{fonte['url']}{ano}/all?type=daily_treasury_yield_curve&field_tdr_date_value={ano}&page&_format=csv"


def interpretar_tesouro(texto: str, codigo: str) -> list[Observacao]:
    """Curva diária do Tesouro dos EUA: uma linha por dia (MM/DD/AAAA), uma coluna por prazo ("10 Yr")."""
    saida = []
    for linha in _linhas(texto, {"Date", codigo}):
        valor = _numero(linha[codigo], f"{codigo} {linha['Date']}")
        if valor is not None:
            mes, dia, ano = linha["Date"].split("/")
            saida.append(Observacao(codigo, date(int(ano), int(mes), int(dia)), valor))
    return sorted(saida, key=lambda o: o.data)


def ler_tesouro(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    """Um arquivo por ano: o histórico inteiro na primeira vez; depois, só o ano corrente (e o anterior em janeiro)."""
    saida = []
    for ano in range(desde.year, date.today().year + 1):
        texto = _baixar(session, url_tesouro(fonte, ano), user_agent)
        for s in series:
            saida += interpretar_tesouro(texto, s["codigo"])
    return _desde(saida, desde)


_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def url_bundesbank(fonte: dict, codigo: str, desde: date) -> str:
    conjunto, chave = codigo.split(".", 1)
    return f"{fonte['url']}{conjunto}/{chave}?format=csv&lang=en&startPeriod={desde.isoformat()}"


def interpretar_bundesbank(texto: str, codigo: str) -> list[Observacao]:
    """Bundesbank: linhas de descrição no topo (a primeira traz o código da série), depois data ISO e valor."""
    linhas = list(csv.reader(io.StringIO(texto)))
    if not linhas or len(linhas[0]) < 2 or linhas[0][1] != codigo:
        raise ValueError(f"formato inesperado: a primeira linha não traz a série {codigo}")
    saida = []
    for linha in linhas[1:]:
        if len(linha) >= 2 and _DATA_ISO.match(linha[0]):
            valor = _numero(linha[1], f"{codigo} {linha[0]}")
            if valor is not None:
                saida.append(Observacao(codigo, date.fromisoformat(linha[0]), valor))
    return saida


def ler_bundesbank(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    saida = []
    for s in series:
        saida += interpretar_bundesbank(_baixar(session, url_bundesbank(fonte, s["codigo"], desde), user_agent), s["codigo"])
    return saida


_MESES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def url_boe(fonte: dict, codigo: str, desde: date) -> str:
    inicio = f"{desde.day:02d}/{_MESES[desde.month - 1]}/{desde.year}"
    return (f"{fonte['url']}?csv.x=yes&Datefrom={inicio}&Dateto=now&SeriesCodes={codigo}"
            f"&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")


def interpretar_boe(texto: str, codigo: str) -> list[Observacao]:
    """Banco da Inglaterra: DATE ("09 Oct 2026") e uma coluna com o código da série."""
    saida = []
    for linha in _linhas(texto, {"DATE", codigo}):
        valor = _numero(linha[codigo], f"{codigo} {linha['DATE']}")
        if valor is None:
            continue
        try:
            dia, mes, ano = linha["DATE"].split()
            saida.append(Observacao(codigo, date(int(ano), _MESES.index(mes) + 1, int(dia)), valor))
        except ValueError:
            raise ValueError(f"formato inesperado: data {linha['DATE'][:20]!r}") from None
    return saida


def ler_boe(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    saida = []
    for s in series:
        saida += interpretar_boe(_baixar(session, url_boe(fonte, s["codigo"], desde), user_agent), s["codigo"])
    return saida


_DATA_JAPAO = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$")


def interpretar_japao(texto: str, codigo: str) -> list[Observacao]:
    """Ministério das Finanças do Japão: título, cabeçalho ("Date,1Y,...,10Y,..."), dias (AAAA/M/D) e notas no fim."""
    linhas = list(csv.reader(io.StringIO(texto)))
    cabecalho = next((l for l in linhas if l and l[0] == "Date"), None)
    if not cabecalho or codigo not in cabecalho:
        raise ValueError(f"formato inesperado: falta a coluna {codigo}")
    coluna = cabecalho.index(codigo)
    saida = []
    for linha in linhas:
        if linha and _DATA_JAPAO.match(linha[0]) and len(linha) > coluna:
            valor = _numero(linha[coluna], f"{codigo} {linha[0]}")
            if valor is not None:
                ano, mes, dia = linha[0].split("/")
                saida.append(Observacao(codigo, date(int(ano), int(mes), int(dia)), valor))
    return saida


def ler_japao(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    """O mês corrente num arquivo; os anteriores, no histórico (desde 1974), lido só quando precisa."""
    hoje = date.today()
    arquivos = ["jgbcme.csv"] + (["historical/jgbcme_all.csv"] if desde < hoje.replace(day=1) else [])
    saida = []
    for arquivo in arquivos:
        texto = _baixar(session, fonte["url"] + arquivo, user_agent, codificacao="cp932")  # notas em japonês
        for s in series:
            saida += interpretar_japao(texto, s["codigo"])
    return _desde(saida, desde)


CONECTORES = {"bce": ler_bce, "fred": ler_fred, "yahoo": ler_yahoo, "tesouro": ler_tesouro,
              "bundesbank": ler_bundesbank, "boe": ler_boe, "japao": ler_japao}
