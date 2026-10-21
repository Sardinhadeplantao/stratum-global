"""Séries de dados (decisões 0011 e 0012): BCE, FRED e Yahoo Finance, sem chave. Devolvem observações; quem grava é
o robô.

O formato é conferido na entrada: coluna que falta ou valor ilegível é erro, nunca um número inventado.
Valor vazio (feriado no FRED) é só ausência de dado.
"""
import csv
import io
import json
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


def _baixar(session, url: str, user_agent: str) -> str:
    r = session.get(url, headers={"User-Agent": user_agent, "Accept": "text/csv, application/json, */*;q=0.5"},
                    timeout=TEMPO_LIMITE)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.content.decode("utf-8-sig")


def _linhas(texto: str, exigidas: set[str]) -> list[dict]:
    leitor = csv.DictReader(io.StringIO(texto))
    faltam = exigidas - set(leitor.fieldnames or [])
    if faltam:
        raise ValueError(f"formato inesperado: faltam as colunas {', '.join(sorted(faltam))}")
    return list(leitor)


def _numero(texto: str, onde: str) -> float | None:
    texto = (texto or "").strip()
    if texto in ("", ".", "NaN"):
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
    if meta.get("symbol") != codigo:
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
        if not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(f"valor ilegível em {codigo}: {str(v)[:20]!r}")
        por_dia[datetime.fromtimestamp(t, fuso).date()] = _significativos(v)  # o último valor do dia vale
    return [Observacao(codigo, d, v) for d, v in sorted(por_dia.items())]


def ler_yahoo(fonte: dict, series: list[dict], session, user_agent: str, desde: date) -> list[Observacao]:
    ate = int(time.time()) + 86400
    saida = []
    for s in series:
        saida += interpretar_yahoo(_baixar(session, url_yahoo(fonte, s["codigo"], desde, ate), user_agent), s["codigo"])
    return saida


CONECTORES = {"bce": ler_bce, "fred": ler_fred, "yahoo": ler_yahoo}
