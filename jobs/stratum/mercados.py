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


def leitura(c, s: dict, validade_dias: int | None, momento: datetime) -> dict:
    """A leitura de uma série para o status.json. Situação: ok | parada | historico_curto | sem_dado."""
    lido = regua.ler(pontos(c, s["id"], momento), s["medida"], s["frequencia"])
    situacao = lido.situacao
    if lido.data and validade_dias is not None and (momento.date() - lido.data).days > validade_dias:
        situacao = "parada"  # o dado ficou velho: cinza, mesmo com leitura
    return {
        "situacao": situacao, "data": lido.data.isoformat() if lido.data else None, "valor": lido.valor,
        "variacao": _r(lido.medida, 2), "percentil": _r(lido.percentil, 1),
        "extremo": lido.extremo if situacao == "ok" else None, "pontuacao": _r(lido.pontuacao, 2),
        "faixa": [_r(x, 2) for x in lido.faixa] if lido.faixa else None, "historico": lido.historico,
        "mudancas": [m | {"desde": m["desde"].isoformat()} for m in lido.mudancas] if situacao == "ok" else [],
    }


def montar(c, fontes: dict[str, dict], momento: datetime, validade: dict[str, int]) -> dict:
    """Todas as séries ativas, ordenadas só pela pontuação (decisão 0011); sem leitura, no fim, pelo nome."""
    series = c.execute(select(db.serie).where(db.serie.c.ativa).order_by(db.serie.c.nome)).mappings().all()
    conhecidas = c.execute(select(db.observacao.c.serie_id, func.max(db.observacao.c.conhecido_em))
                           .group_by(db.observacao.c.serie_id)).all()
    ultima_coleta = dict(conhecidas)
    lista = []
    for s in series:
        f = fontes.get(s["fonte_id"]) or {}
        lista.append({"id": s["id"], "nome": s["nome"], "unidade": s["unidade"], "pais": s["pais"], "codigo": s["codigo"],
                      "fonte": s["fonte_id"], "fonte_nome": f.get("nome", s["fonte_id"]),
                      "conhecido_em": ultima_coleta[s["id"]].isoformat(timespec="seconds") + "Z"
                      if s["id"] in ultima_coleta else None}
                     | leitura(c, dict(s), validade.get(s["fonte_id"]), momento))
    lista.sort(key=lambda x: (x["situacao"] != "ok" or x["pontuacao"] is None, -abs(x["pontuacao"] or 0)))
    return {"regua": regua.parametros(), "validade_dias": validade, "series": lista,
            "fora_do_normal": sum(1 for x in lista if x["extremo"])}
