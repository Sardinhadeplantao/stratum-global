"""Séries de mercado (decisão 0011): grava as observações novas e monta a leitura de cada série para o site.

A régua está em domain/regua.py. Aqui só entra o banco: o que gravar, desde quando pedir à fonte e o que o sistema
sabia em cada momento (a leitura de um momento nunca usa o que o sistema soube depois).
"""
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from stratum import db
from stratum.domain import regua

HISTORICO_DESDE = date(2015, 1, 1)   # 5 anos de janela e mais 5 para a taxa-base
REVISAO_DIAS = 31                    # a cada leitura, pede de novo o último mês, para pegar revisões
LOTE = 1000
CONFERE_ATE_PCT = 2.0                # cotação de mercado × conta pelo BCE no mesmo dia (decisão 0012)


def desde(c, series: list[dict]) -> date:
    """Primeira data a pedir à fonte: o histórico inteiro se falta alguma série; senão, o último mês."""
    ultimas = dict(c.execute(select(db.observacao.c.serie_id, func.max(db.observacao.c.data))
                             .where(db.observacao.c.serie_id.in_([s["id"] for s in series]))
                             .group_by(db.observacao.c.serie_id)).all())
    if any(s["id"] not in ultimas for s in series):
        return HISTORICO_DESDE
    return max(HISTORICO_DESDE, min(ultimas.values()) - timedelta(days=REVISAO_DIAS))


def gravar(engine, series: list[dict], observacoes, rodada_id: int, conhecido_em: datetime) -> int:
    """Grava o que é novo: data que o banco não tem, ou valor diferente do último conhecido (revisão da fonte).
    Devolve quantas observações entraram."""
    por_codigo = {s["codigo"]: s["id"] for s in series}
    obs = [o for o in observacoes if o.codigo in por_codigo]
    if not obs:
        return 0
    with engine.begin() as c:
        atuais = {}
        for sid, d, v in c.execute(select(db.observacao.c.serie_id, db.observacao.c.data, db.observacao.c.valor)
                                   .where(db.observacao.c.serie_id.in_(list(por_codigo.values())),
                                          db.observacao.c.data >= min(o.data for o in obs))
                                   .order_by(db.observacao.c.id)):
            atuais[(sid, d)] = v  # o último registro de cada data é o valor mais recente
        linhas = []
        for o in obs:
            chave = (por_codigo[o.codigo], o.data)
            if atuais.get(chave) == o.valor:
                continue
            atuais[chave] = o.valor
            linhas.append(dict(serie_id=chave[0], data=o.data, valor=o.valor, rodada_id=rodada_id, conhecido_em=conhecido_em))
        for i in range(0, len(linhas), LOTE):
            c.execute(db.observacao.insert(), linhas[i:i + LOTE])
    return len(linhas)


def pontos(c, serie_id: str, ate: datetime) -> list[tuple[date, float]]:
    """A série como o sistema a conhecia em `ate`: para cada data, o último valor que ele já sabia."""
    por_data: dict[date, float] = {}
    for d, v in c.execute(select(db.observacao.c.data, db.observacao.c.valor)
                          .where(db.observacao.c.serie_id == serie_id, db.observacao.c.conhecido_em <= ate)
                          .order_by(db.observacao.c.id)):
        por_data[d] = v
    return sorted(por_data.items())


def _r(x: float | None, casas: int) -> float | None:
    return None if x is None else round(x, casas)


def conferencia(serie: list[tuple[date, float]], numerador: list[tuple[date, float]],
                denominador: list[tuple[date, float]], antes_de: date | None) -> dict | None:
    """Compara a série com a mesma cotação feita pela conta do BCE (numerador ÷ denominador), no último dia completo
    que os três têm. `antes_de`: o dia em andamento, que ainda não fechou, fica de fora."""
    num, den = dict(numerador), dict(denominador)
    for d, v in reversed(serie):
        if (antes_de is None or d < antes_de) and d in num and d in den and den[d] > 0:
            oficial = num[d] / den[d]
            diferenca = (v / oficial - 1) * 100
            return {"data": d.isoformat(), "oficial": round(oficial, 6), "diferenca": round(diferenca, 2),
                    "confere": abs(diferenca) <= CONFERE_ATE_PCT}
    return None


def leitura(c, s: dict, validade_dias: int | None, momento: datetime) -> dict:
    """A leitura de uma série para o status.json (ver _ler)."""
    return _ler(pontos(c, s["id"], momento), s, validade_dias, momento)


def _ler(pts: list[tuple[date, float]], s: dict, validade_dias: int | None, momento: datetime,
         dia_em_andamento: bool = False, conferida: dict | None = None) -> dict:
    """Situação: ok | nao_confere | parada | historico_curto | sem_dado. Só "ok" tem cor de leitura."""
    lido = regua.ler(pts, s["medida"], s["frequencia"])
    situacao = lido.situacao
    if lido.data and validade_dias is not None and (momento.date() - lido.data).days > validade_dias:
        situacao = "parada"  # o dado ficou velho: cinza, mesmo com leitura
    elif situacao == "ok" and conferida and not conferida["confere"]:
        situacao = "nao_confere"  # é verdade? a fonte de mercado não bate com o BCE: sem cor até bater
    return {
        "situacao": situacao, "data": lido.data.isoformat() if lido.data else None, "valor": lido.valor,
        "parcial": bool(dia_em_andamento and lido.data and lido.data >= momento.date()),  # o dia ainda não fechou
        "conferencia": conferida,
        "variacao": _r(lido.medida, 2), "percentil": _r(lido.percentil, 1),
        "extremo": lido.extremo if situacao == "ok" else None, "pontuacao": _r(lido.pontuacao, 2),
        "faixa": [_r(x, 2) for x in lido.faixa] if lido.faixa else None, "historico": lido.historico,
        "mudancas": [m | {"desde": m["desde"].isoformat()} for m in lido.mudancas] if situacao == "ok" else [],
    }


def montar(c, fontes: dict[str, dict], momento: datetime, catalogo_fontes: list[dict], catalogo_series: list[dict]) -> dict:
    """Todas as séries ativas, ordenadas só pela pontuação (decisão 0011); sem leitura, no fim, pelo nome.
    Do catálogo (código) vêm a validade e o dia em andamento de cada fonte e a conferência de cada série."""
    validade = {f["id"]: f["validade_dias"] for f in catalogo_fontes if f.get("validade_dias") and f.get("ativa", True)}
    em_andamento = {f["id"] for f in catalogo_fontes if f.get("dia_em_andamento")}
    conferir = {s["id"]: s["conferir"] for s in catalogo_series if s.get("conferir")}
    series = c.execute(select(db.serie).where(db.serie.c.ativa).order_by(db.serie.c.nome)).mappings().all()
    ultima_coleta = dict(c.execute(select(db.observacao.c.serie_id, func.max(db.observacao.c.conhecido_em))
                                   .group_by(db.observacao.c.serie_id)).all())
    pts = {s["id"]: pontos(c, s["id"], momento) for s in series}
    for par in conferir.values():
        for sid in par:
            if sid not in pts:
                pts[sid] = pontos(c, sid, momento)
    lista = []
    for s in series:
        f = fontes.get(s["fonte_id"]) or {}
        andamento = s["fonte_id"] in em_andamento
        conferida = None
        if s["id"] in conferir and pts[s["id"]]:
            ultimo = pts[s["id"]][-1][0]
            conferida = conferencia(pts[s["id"]], *(pts[x] for x in conferir[s["id"]]),
                                    antes_de=ultimo if andamento and ultimo >= momento.date() else None)
            if conferida:
                conferida["com"] = "BCE"
        lista.append({"id": s["id"], "nome": s["nome"], "unidade": s["unidade"], "pais": s["pais"], "codigo": s["codigo"],
                      "medida": s["medida"],  # variacao_pct (em %) ou diferenca (em pontos percentuais)
                      "grupo": s["grupo"],
                      "fonte": s["fonte_id"], "fonte_nome": f.get("nome", s["fonte_id"]),
                      "conhecido_em": ultima_coleta[s["id"]].isoformat(timespec="seconds") + "Z"
                      if s["id"] in ultima_coleta else None,
                      "conferir": s["id"] in conferir}
                     | _ler(pts[s["id"]], dict(s), validade.get(s["fonte_id"]), momento, andamento, conferida))
    lista.sort(key=lambda x: (x["situacao"] != "ok" or x["pontuacao"] is None, -abs(x["pontuacao"] or 0)))
    return {"regua": regua.parametros(), "validade_dias": validade, "confere_ate_pct": CONFERE_ATE_PCT, "series": lista,
            "fora_do_normal": sum(1 for x in lista if x["extremo"]),
            "nao_conferem": sum(1 for x in lista if x["situacao"] == "nao_confere")}
