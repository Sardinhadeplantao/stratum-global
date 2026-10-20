"""Histórias no banco: liga cada notícia nova à sua história e lista as histórias recentes (decisão 0009).

A regra fica em `domain/historias.py`. Aqui só se lê e se grava: cada notícia ganha uma ligação, uma vez só, que nunca
muda (regra 2). A história recebe o id da primeira notícia dela. Rede social não entra (regra 4).
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select

from stratum import db
from stratum.domain import historias as regra
from stratum.domain import paises

JANELA_SITE = timedelta(hours=24)
MAX_HISTORIAS = 20
NAO_ENTRA = {"social"}


def atualizar(engine, agora: datetime) -> dict:
    """Liga as notícias ainda sem história. Repassa antes as notícias das 48 horas anteriores, já ligadas, para a
    regra ver a mesma janela da rodada em que elas chegaram. Devolve quantas notícias e histórias novas."""
    d, h, f = db.documento, db.historia_documento, db.fonte
    with engine.begin() as c:
        sem = (select(func.min(d.c.conhecido_em)).select_from(d.join(f, f.c.id == d.c.fonte_id)
                                                               .outerjoin(h, h.c.documento_id == d.c.id))
               .where(h.c.documento_id.is_(None), f.c.tipo.not_in(NAO_ENTRA)))
        primeira = c.execute(sem).scalar()
        if primeira is None:
            return {"documentos": 0, "historias_novas": 0}
        linhas = c.execute(
            select(d.c.id, d.c.titulo, d.c.resumo, d.c.conhecido_em, h.c.historia_id)
            .select_from(d.join(f, f.c.id == d.c.fonte_id).outerjoin(h, h.c.documento_id == d.c.id))
            .where(d.c.conhecido_em >= primeira - regra.Agrupador().janela, f.c.tipo.not_in(NAO_ENTRA))
            .order_by(d.c.conhecido_em, d.c.id)).mappings().all()
        ag = regra.Agrupador()
        novas, ligacoes = 0, []
        for linha in linhas:
            doc = dict(linha)
            hist = ag.adicionar(doc, doc["historia_id"])
            if doc["historia_id"] is None:
                if hist is None:
                    hist, novas = doc["id"], novas + 1
                ligacoes.append(dict(documento_id=doc["id"], historia_id=hist, conhecido_em=agora, regra=regra.REGRA))
            ag.fixar(doc["id"], hist)
        db.inserir_ignorando_repetidos(c, h, ligacoes, "documento_id")
    return {"documentos": len(ligacoes), "historias_novas": novas}


def recentes(engine, agora: datetime, inicio: datetime | None = None) -> list[dict]:
    """Histórias com 2 ou mais notícias e alguma notícia desde `inicio` (padrão: últimas 24 horas).

    Vozes = donos diferentes (decisão 0008): dois veículos do mesmo Estado ou grupo contam como uma voz. É cobertura,
    não confirmação. Ordem: mais vozes, mais notícias, mais recente."""
    from stratum import export  # quando() mora lá; import aqui evita ciclo

    inicio = inicio or agora - JANELA_SITE
    d, h, f = db.documento, db.historia_documento, db.fonte
    with engine.connect() as c:
        ativas = (select(h.c.historia_id).join(d, d.c.id == h.c.documento_id)
                  .where(d.c.conhecido_em >= inicio).distinct())
        linhas = c.execute(
            select(h.c.historia_id, d.c.id, d.c.titulo, d.c.url, d.c.publicado_em, d.c.conhecido_em,
                   f.c.id.label("fonte"), f.c.nome.label("fonte_nome"), f.c.controlador)
            .join(d, d.c.id == h.c.documento_id).join(f, f.c.id == d.c.fonte_id)
            .where(h.c.historia_id.in_(ativas))).mappings().all()
    dic = paises.carregar()
    por_historia: dict = {}
    for l in linhas:
        por_historia.setdefault(l["historia_id"], []).append(dict(l, quando=export.quando(l)))
    saida = []
    for hid, docs in por_historia.items():
        if len(docs) < 2:
            continue
        docs.sort(key=lambda x: (x["quando"], x["id"]), reverse=True)
        primeira = min(docs, key=lambda x: x["id"])
        isos = sorted({iso for x in docs for iso in paises.citados(x["titulo"], dic)})
        saida.append({
            "id": hid,
            "titulo": primeira["titulo"],
            "noticias": len(docs),
            "fontes": len({x["fonte"] for x in docs}),
            "vozes": len({x["controlador"] or x["fonte"] for x in docs}),
            "ultima": export._iso(docs[0]["quando"]),
            "paises": [{"iso": i, "nome": dic.nome(i) or i} for i in isos],
            "documentos": [{"titulo": x["titulo"], "url": x["url"], "fonte": x["fonte"], "fonte_nome": x["fonte_nome"],
                            "publicado_em": export._iso(x["publicado_em"]), "conhecido_em": export._iso(x["conhecido_em"])}
                           for x in docs],
        })
    saida.sort(key=lambda x: (x["vozes"], x["noticias"], x["ultima"] or ""), reverse=True)
    return saida[:MAX_HISTORIAS]
