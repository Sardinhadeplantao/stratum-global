"""Séries de mercado (decisão 0011): grava as observações novas e monta a leitura de cada série para o site.

A régua está em domain/regua.py. Aqui só entra o banco: o que gravar, desde quando pedir à fonte e o que o sistema
sabia em cada momento (a leitura de um momento nunca usa o que o sistema soube depois).

Saída do banco: o Supabase gratuito tem 5 GB por mês, e ler todas as cotações a cada rodada gastaria uns 17 GB. O
robô guarda uma cópia local das cotações (cache do GitHub) e pede ao banco só as linhas novas (`carregar`).
"""
import gzip
import json
import os
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


def gravar(engine, series: list[dict], observacoes, rodada_id: int, conhecido_em: datetime,
           ate_dia: date | None = None) -> int:
    """Grava o que é novo: data que o banco não tem, ou valor diferente do último conhecido (revisão da fonte).
    Com `ate_dia`, o dia em andamento (essa data ou depois) fica de fora: só o dia que fechou vai para o banco
    (decisão 0016). Devolve quantas observações entraram."""
    por_codigo = {s["codigo"]: s["id"] for s in series}
    # A mesma data duas vezes na mesma leitura (dois arquivos da fonte que se sobrepõem): vale a última
    todas = list({(o.codigo, o.data): o for o in observacoes if o.codigo in por_codigo}.values())
    obs = [o for o in todas if ate_dia is None or o.data < ate_dia]
    if not todas:
        return 0
    with engine.begin() as c:
        atuais = {}
        for sid, d, v in c.execute(select(db.observacao.c.serie_id, db.observacao.c.data, db.observacao.c.valor)
                                   .where(db.observacao.c.serie_id.in_(list(por_codigo.values())),
                                          db.observacao.c.data >= min(o.data for o in todas))
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
        # Contrato futuro do dia (decisão 0014): entra quando é novo para a data; o mesmo de novo é ignorado. O do dia
        # em andamento também entra: o contrato vigente é fato, não preço provisório (decisão 0016)
        contratos = [dict(serie_id=por_codigo[o.codigo], data=o.data, contrato=o.contrato, conhecido_em=conhecido_em)
                     for o in todas if o.contrato]
        db.inserir_ignorando_repetidos(c, db.contrato_futuro, contratos, ["serie_id", "data", "contrato"])
    return len(linhas)


def parciais(series: list[dict], observacoes, ate_dia: date | None, lido_em: datetime) -> list[dict]:
    """O dia em andamento de cada série, como lido nesta rodada (decisão 0016): não vai para o banco, vai para o
    status.json com a data do dia e a hora da leitura."""
    if ate_dia is None:
        return []
    por_codigo = {s["codigo"]: s["id"] for s in series}
    ultimo = {}
    for o in observacoes:
        if o.codigo in por_codigo and o.data >= ate_dia and (o.codigo not in ultimo or o.data >= ultimo[o.codigo].data):
            ultimo[o.codigo] = o
    return [dict(serie_id=por_codigo[c], data=o.data, valor=o.valor, contrato=o.contrato, conhecido_em=lido_em)
            for c, o in ultimo.items()]


def trocas_de_contrato(c, ate: datetime) -> dict[str, set[date]]:
    """Por série, os dias em que o contrato futuro mudou em relação ao dia anterior com contrato conhecido, com o que
    o sistema sabia em `ate`. Dia sem contrato conhecido não marca troca (não dá para saber).

    A conta é feita no banco e só os dias da troca voltam (uns 100 por ano): ler a tabela inteira a cada rodada
    cresceria sem parar e gastaria a cota de tráfego do Supabase gratuito (revisão de 21/10)."""
    t = db.contrato_futuro.c
    ultimo = select(t.serie_id, t.data, t.contrato, func.row_number().over(  # o último registro de cada dia vale
        partition_by=(t.serie_id, t.data), order_by=t.conhecido_em.desc()).label("n")).where(t.conhecido_em <= ate).subquery()
    dia = select(ultimo.c.serie_id, ultimo.c.data, ultimo.c.contrato, func.lag(ultimo.c.contrato).over(
        partition_by=ultimo.c.serie_id, order_by=ultimo.c.data).label("antes")).where(ultimo.c.n == 1).subquery()
    trocas: dict[str, set[date]] = {}
    for sid, d in c.execute(select(dia.c.serie_id, dia.c.data).where(dia.c.antes.is_not(None), dia.c.antes != dia.c.contrato)):
        trocas.setdefault(sid, set()).add(d)
    return trocas


def pontos(c, serie_id: str, ate: datetime) -> list[tuple[date, float]]:
    """A série como o sistema a conhecia em `ate`: para cada data, o último valor que ele já sabia."""
    por_data: dict[date, float] = {}
    for d, v in c.execute(select(db.observacao.c.data, db.observacao.c.valor)
                          .where(db.observacao.c.serie_id == serie_id, db.observacao.c.conhecido_em <= ate)
                          .order_by(db.observacao.c.id)):
        por_data[d] = v
    return sorted(por_data.items())


Linha = tuple[int, str, date, float, datetime]  # id, série, data, valor, conhecido_em


def _consulta():
    o = db.observacao.c
    return select(o.id, o.serie_id, o.data, o.valor, o.conhecido_em).order_by(o.id)


def _ler_copia(caminho: str) -> list[Linha]:
    try:
        with gzip.open(caminho, "rt", encoding="utf-8") as f:
            return [(i, s, date.fromisoformat(d), v, datetime.fromisoformat(k)) for i, s, d, v, k in json.load(f)]
    except (OSError, ValueError, TypeError):  # sem cópia, ou cópia estragada: lê tudo do banco
        return []


def _gravar_copia(caminho: str, linhas: list[Linha]) -> None:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = caminho + ".novo"
    with gzip.open(temporario, "wt", encoding="utf-8") as f:
        json.dump([(i, s, d.isoformat(), v, k.isoformat()) for i, s, d, v, k in linhas], f)
    os.replace(temporario, caminho)


def carregar(c, caminho: str | None = None) -> tuple[dict[str, list[Linha]], dict]:
    """Todas as observações, por série, na ordem em que entraram. Devolve também quantas vieram da cópia e do banco.

    Com `caminho`, usa a cópia local da rodada anterior e pede ao banco só as linhas com id maior. Como `observacao` só
    recebe inserções (regra 2), as linhas já copiadas nunca mudam. Se o banco foi recriado (o último id copiado não
    existe mais, ou a contagem não bate), a cópia é descartada e tudo é lido de novo."""
    copia = _ler_copia(os.path.expanduser(caminho)) if caminho else []
    if copia:
        ultimo = copia[-1]
        o = db.observacao.c
        no_banco = c.execute(_consulta().where(o.id == ultimo[0])).first()
        quantas = c.execute(select(func.count()).select_from(db.observacao).where(o.id <= ultimo[0])).scalar()
        if no_banco is None or tuple(no_banco) != ultimo or quantas != len(copia):
            copia = []
    novas = [tuple(r) for r in c.execute(_consulta().where(db.observacao.c.id > copia[-1][0]) if copia else _consulta())]
    linhas = copia + novas
    if caminho:
        _gravar_copia(os.path.expanduser(caminho), linhas)
    por_serie: dict[str, list[Linha]] = {}
    for linha in linhas:
        por_serie.setdefault(linha[1], []).append(linha)
    return por_serie, {"da_copia": len(copia), "do_banco": len(novas)}


def _pontos(linhas: list[Linha], ate: datetime) -> list[tuple[date, float]]:
    """Como `pontos`, a partir das linhas em memória."""
    por_data: dict[date, float] = {}
    for _, _, d, v, conhecido in linhas:
        if conhecido <= ate:
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
         dia_em_andamento: bool = False, conferida: dict | None = None, trocas: set[date] = frozenset()) -> dict:
    """Situação: ok | nao_confere | troca_de_contrato | parada | historico_curto | sem_dado. Só "ok" tem cor."""
    lido = regua.ler(pts, s["medida"], s["frequencia"], trocas)
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


# Quadros de destaque do painel de mercados (decisão 0014): um número por grande mercado, para quem lê do Brasil.
# Bolsa e juro dos EUA, dólar no mundo, ouro, petróleo, cripto, e o dólar e a bolsa do Brasil. Escolha fixa, não muda
# com o dia: o que se mexeu fora do normal aparece pela régua, não por estar aqui.
DESTAQUES = {"bolsa_gspc": "S&P 500", "juros_usa_10a": "US10Y", "yahoo_dxynyb": "DXY", "commodity_gc": "Ouro",
             "commodity_bz": "Brent", "cripto_btc": "BTC/USD", "yahoo_brl": "USD/BRL", "bolsa_bvsp": "Ibovespa"}
DIAS_DO_MES = 30  # o minigráfico: as cotações dos últimos 30 dias corridos, como o sistema as conhecia


def _amplitude(lista: list[dict]) -> dict:
    """Quantas séries sobem, caem ou ficam iguais no último dia. Só conta leitura "ok": parada, troca de contrato e
    cotação que não confere com a fonte oficial ficam de fora (a variação delas não é confiável)."""
    def contar(xs):
        ok = [x["variacao"] for x in xs if x["situacao"] == "ok" and x["variacao"] is not None]
        return {"sobem": sum(v > 0 for v in ok), "caem": sum(v < 0 for v in ok), "estaveis": sum(v == 0 for v in ok)}
    total = contar(lista)
    medidas = total["sobem"] + total["caem"] + total["estaveis"]
    grupos = sorted({x["grupo"] for x in lista})
    return total | {"proporcao_sobem": round(total["sobem"] / medidas, 3) if medidas else None,
                    "por_grupo": {g: contar([x for x in lista if x["grupo"] == g]) for g in grupos}}


def montar(c, fontes: dict[str, dict], momento: datetime, catalogo_fontes: list[dict], catalogo_series: list[dict],
           copia: str | None = None, parciais: list[dict] | None = None) -> dict:
    """Todas as séries ativas, ordenadas só pela pontuação (decisão 0011); sem leitura, no fim, pelo nome.
    Do catálogo (código) vêm a validade e o dia em andamento de cada fonte, a conferência e o símbolo de cada série.
    `copia`: caminho da cópia local das cotações (ver `carregar`). `parciais`: o dia em andamento lido nesta rodada,
    que não vai para o banco (decisão 0016)."""
    validade = {f["id"]: f["validade_dias"] for f in catalogo_fontes if f.get("validade_dias") and f.get("ativa", True)}
    em_andamento = {f["id"] for f in catalogo_fontes if f.get("dia_em_andamento")}
    conferir = {s["id"]: s["conferir"] for s in catalogo_series if s.get("conferir")}
    regiao = {s["id"]: s["regiao"] for s in catalogo_series if s.get("regiao")}
    simbolo = {s["id"]: s["simbolo"] for s in catalogo_series if s.get("simbolo")}
    inicio_mes = momento.date() - timedelta(days=DIAS_DO_MES)
    series = c.execute(select(db.serie).where(db.serie.c.ativa).order_by(db.serie.c.nome)).mappings().all()
    todas, origem = carregar(c, copia)
    trocas = trocas_de_contrato(c, momento)
    print(f"Cotações: {origem['da_copia']} da cópia local, {origem['do_banco']} lidas do banco.", flush=True)
    ultima_coleta = {sid: max(l[4] for l in linhas) for sid, linhas in todas.items()}
    pts = {sid: _pontos(todas.get(sid, []), momento)
           for sid in {s["id"] for s in series} | {x for par in conferir.values() for x in par}}
    for p in parciais or []:  # o dia em andamento desta rodada (decisão 0016): não está no banco
        if p["serie_id"] in pts and p["conhecido_em"] <= momento:
            pts[p["serie_id"]] = sorted({**dict(pts[p["serie_id"]]), p["data"]: p["valor"]}.items())
            ultima_coleta[p["serie_id"]] = max(ultima_coleta.get(p["serie_id"], p["conhecido_em"]), p["conhecido_em"])
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
        lista.append({"id": s["id"], "simbolo": simbolo.get(s["id"], s["nome"]), "nome": s["nome"], "unidade": s["unidade"],
                      "pais": s["pais"], "codigo": s["codigo"],
                      "medida": s["medida"],  # variacao_pct (em %) ou diferenca (em pontos percentuais)
                      "grupo": s["grupo"], "regiao": regiao.get(s["id"]),
                      "mes": [v for d, v in pts[s["id"]] if d > inicio_mes],
                      "fonte": s["fonte_id"], "fonte_nome": f.get("nome", s["fonte_id"]),
                      "conhecido_em": ultima_coleta[s["id"]].isoformat(timespec="seconds") + "Z"
                      if s["id"] in ultima_coleta else None,
                      "conferir": s["id"] in conferir}
                     | _ler(pts[s["id"]], dict(s), validade.get(s["fonte_id"]), momento, andamento, conferida,
                            trocas.get(s["id"], set())))
    lista.sort(key=lambda x: (x["situacao"] != "ok" or x["pontuacao"] is None, -abs(x["pontuacao"] or 0)))
    por_pais: dict[str, list[str]] = {}
    for x in lista:  # moeda, juros e bolsa de cada país, para o painel do país (decisão 0014)
        if x["pais"]:
            por_pais.setdefault(x["pais"], []).append(x["id"])
    return {"regua": regua.parametros(), "validade_dias": validade, "confere_ate_pct": CONFERE_ATE_PCT, "series": lista,
            "por_pais": por_pais,
            "destaques": [{"id": i, "rotulo": r} for i, r in DESTAQUES.items() if any(x["id"] == i for x in lista)],
            "amplitude": _amplitude(lista),
            "fora_do_normal": sum(1 for x in lista if x["extremo"]),
            "nao_conferem": sum(1 for x in lista if x["situacao"] == "nao_confere")}
