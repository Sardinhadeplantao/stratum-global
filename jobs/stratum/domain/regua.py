"""Régua única das séries (decisão 0011): percentil contra o próprio histórico, os mesmos parâmetros para todas.

Regra pura: recebe os pontos de uma série (data, valor), já com só o que o sistema sabia no momento da leitura, e
devolve a leitura do último ponto. Sem banco, rede ou IA. Mudar um parâmetro pede decisão nova e versão nova.
"""
from bisect import bisect_left, bisect_right, insort
from dataclasses import dataclass, field
from datetime import date
from statistics import median

REGUA = "regua-1.2"  # 1.1: o dia da troca de contrato futuro fica fora da régua (decisão 0014)
                     # 1.2: contagens (navios por dia) medidas pela média de 7 dias (decisão 0018)
JANELA_ANOS = 5
MINIMO = {"diaria": 250, "mensal": 24}   # medidas no histórico; abaixo disso, "histórico curto"
EXTREMO = 5                              # fora do normal: percentil até 5 ou a partir de 95
PERSISTENCIA = 2                         # extremo que persiste: períodos seguidos fora do normal, do mesmo lado
RITMO_PONTOS = 20                        # agitação = DAM das últimas 20 medidas
RITMO_EXTREMO = 95                       # quebra de ritmo: agitação no percentil 95 ou mais
ESCALA_DAM = 1.4826                      # DAM vezes isto = um desvio-padrão numa curva normal
MEDIA_DIAS = 7                           # contagens: o nível da semana, não a variação de um dia para o outro


def parametros() -> dict:
    """Os parâmetros em vigor, para a tela Método (regra 6)."""
    return {"versao": REGUA, "janela_anos": JANELA_ANOS, "minimo": dict(MINIMO), "extremo": EXTREMO,
            "persistencia": PERSISTENCIA, "ritmo_pontos": RITMO_PONTOS, "ritmo_extremo": RITMO_EXTREMO,
            "media_dias": MEDIA_DIAS}


def variacao_pct(pontos: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Medida de preço: variação em % desde a observação anterior (fim de semana e feriado não contam)."""
    return [(d, (v / anterior - 1) * 100) for (_, anterior), (d, v) in zip(pontos, pontos[1:]) if anterior > 0]


def diferenca(pontos: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Medida de taxa (juros): a diferença em pontos percentuais desde a observação anterior."""
    return [(d, v - anterior) for (_, anterior), (d, v) in zip(pontos, pontos[1:])]


def media_7d(pontos: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Medida de contagem (navios por dia, decisão 0018): a média das últimas 7 observações. De 0 para 4 navios não é
    "+400%": o que se compara com o histórico é o nível da semana."""
    return [(pontos[i][0], sum(v for _, v in pontos[i + 1 - MEDIA_DIAS:i + 1]) / MEDIA_DIAS)
            for i in range(MEDIA_DIAS - 1, len(pontos))]


MEDIDAS = {"variacao_pct": variacao_pct, "diferenca": diferenca, "media_7d": media_7d}


def anos_antes(d: date, anos: int) -> date:
    try:
        return d.replace(year=d.year - anos)
    except ValueError:  # 29 de fevereiro
        return d.replace(year=d.year - anos, day=28)


def percentil(x: float, ordenados: list[float]) -> float:
    """Posição de x no histórico, de 0 a 100; empates contam metade."""
    abaixo, ate = bisect_left(ordenados, x), bisect_right(ordenados, x)
    return (abaixo + (ate - abaixo) / 2) / len(ordenados) * 100


def quantil(ordenados: list[float], q: float) -> float:
    pos = q * (len(ordenados) - 1)
    i = int(pos)
    j = min(i + 1, len(ordenados) - 1)
    return ordenados[i] + (ordenados[j] - ordenados[i]) * (pos - i)


def dam(valores: list[float]) -> float:
    """Desvio absoluto mediano."""
    m = median(valores)
    return median(abs(v - m) for v in valores)


def percentis(medidas: list[tuple[date, float]], minimo: int) -> list[float | None]:
    """Percentil de cada medida contra as dos 5 anos anteriores, sem ela e sem nada depois dela."""
    janela: list[float] = []
    saida: list[float | None] = []
    inicio = 0
    for d, x in medidas:
        limite = anos_antes(d, JANELA_ANOS)
        while inicio < len(saida) and medidas[inicio][0] < limite:
            janela.pop(bisect_left(janela, medidas[inicio][1]))
            inicio += 1
        saida.append(percentil(x, janela) if len(janela) >= minimo else None)
        insort(janela, x)
    return saida


def _lado(p: float | None) -> str | None:
    if p is None:
        return None
    return "alta" if p >= 100 - EXTREMO else "baixa" if p <= EXTREMO else None


def _episodio(condicao: list[bool], datas: list[date], validos: list[bool], recuo: int = 0) -> dict | None:
    """Se a condição vale no último ponto: quando o episódio atual começou e quantos começaram nos 5 anos antes.
    `recuo`: quantos pontos antes do primeiro dia da condição o episódio começou (o 1º dos dias seguidos)."""
    if not condicao or not condicao[-1]:
        return None
    comeco = len(condicao) - 1
    while comeco > 0 and condicao[comeco - 1]:
        comeco -= 1
    primeiro_valido = next((i for i, v in enumerate(validos) if v), comeco)
    limite = max(anos_antes(datas[-1], JANELA_ANOS), datas[primeiro_valido])
    vezes = sum(1 for i in range(1, comeco) if condicao[i] and not condicao[i - 1] and datas[i] >= limite)
    return {"desde": datas[max(comeco - recuo, 0)], "taxa_base": {"vezes": vezes, "anos": round((datas[-1] - limite).days / 365.25, 1)}}


@dataclass
class Leitura:
    situacao: str                        # ok | historico_curto | sem_dado | troca_de_contrato
    data: date | None = None             # data do último ponto (quando aconteceu)
    valor: float | None = None
    medida: float | None = None          # a variação do último ponto
    percentil: float | None = None
    extremo: str | None = None           # alta | baixa | None
    pontuacao: float | None = None       # distância até a mediana, em DAM (só para ordenar)
    faixa: tuple[float, float] | None = None
    historico: int = 0                   # quantas medidas no histórico de referência
    mudancas: list[dict] = field(default_factory=list)


def ler(pontos: list[tuple[date, float]], medida: str = "variacao_pct", frequencia: str = "diaria",
        trocas: frozenset[date] | set[date] = frozenset(), mudancas: bool = True) -> Leitura:
    """A leitura do último ponto da série. `pontos` em ordem de data, um por data.
    `trocas`: dias em que o contrato futuro mudou; a variação deles não mede o mercado e fica fora da régua.
    `mudancas=False`: só a leitura do dia, sem procurar extremo que persiste nem quebra de ritmo (mais rápido)."""
    if pontos and pontos[-1][0] in trocas:
        return Leitura("troca_de_contrato", data=pontos[-1][0], valor=pontos[-1][1])
    medidas = [m for m in MEDIDAS[medida](pontos) if m[0] not in trocas]
    if not medidas:
        return Leitura("sem_dado" if not pontos else "historico_curto",
                       data=pontos[-1][0] if pontos else None, valor=pontos[-1][1] if pontos else None)
    minimo = MINIMO[frequencia]
    d, x = medidas[-1]
    limite = anos_antes(d, JANELA_ANOS)
    referencia = sorted(v for dd, v in medidas[:-1] if dd >= limite)
    base = Leitura("historico_curto", data=d, valor=pontos[-1][1], medida=x, historico=len(referencia))
    if len(referencia) < minimo:
        return base
    p = percentil(x, referencia)
    escala = dam(referencia) * ESCALA_DAM
    base.situacao, base.percentil, base.extremo = "ok", p, _lado(p)
    base.pontuacao = (x - median(referencia)) / escala if escala > 0 else None
    base.faixa = (quantil(referencia, EXTREMO / 100), quantil(referencia, 1 - EXTREMO / 100))
    if not mudancas:
        return base

    datas = [dd for dd, _ in medidas]
    ps = percentis(medidas, minimo)
    lados, validos = [_lado(q) for q in ps], [q is not None for q in ps]
    if base.extremo:
        persiste = [i + 1 >= PERSISTENCIA and all(lados[j] == base.extremo for j in range(i + 1 - PERSISTENCIA, i + 1))
                    for i in range(len(lados))]
        if ep := _episodio(persiste, datas, validos, recuo=PERSISTENCIA - 1):
            base.mudancas.append({"tipo": "extremo_persiste", "sentido": base.extremo} | ep)

    agitacao = [(datas[i], dam([v for _, v in medidas[i + 1 - RITMO_PONTOS:i + 1]]))
                for i in range(RITMO_PONTOS - 1, len(medidas))]
    p_agitacao = percentis(agitacao, minimo)
    quebra = [False] * (RITMO_PONTOS - 1) + [q is not None and q >= RITMO_EXTREMO for q in p_agitacao]
    validos_ritmo = [False] * (RITMO_PONTOS - 1) + [q is not None for q in p_agitacao]
    if ep := _episodio(quebra, datas, validos_ritmo):
        base.mudancas.append({"tipo": "quebra_de_ritmo", "sentido": "agitacao"} | ep)
    return base
