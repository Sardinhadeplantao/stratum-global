"""Séries de dados (decisão 0011): BCE e FRED, arquivos públicos sem chave. Devolvem observações; quem grava é o robô.

O formato é conferido na entrada: coluna que falta ou valor ilegível é erro, nunca um número inventado.
Valor vazio (feriado no FRED) é só ausência de dado.
"""
import csv
import io
from dataclasses import dataclass
from datetime import date

TEMPO_LIMITE = 60  # segundos: a primeira leitura traz 10 anos


@dataclass(frozen=True)
class Observacao:
    codigo: str        # o código da série na fonte (USD no BCE, DEXBZUS no FRED)
    data: date         # quando aconteceu (o dia da cotação)
    valor: float


def _baixar(session, url: str, user_agent: str) -> str:
    r = session.get(url, headers={"User-Agent": user_agent, "Accept": "text/csv, */*;q=0.5"}, timeout=TEMPO_LIMITE)
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


CONECTORES = {"bce": ler_bce, "fred": ler_fred}
