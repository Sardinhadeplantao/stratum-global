"""O que a página inicial mostra em volta do mapa (decisão 0014): pontos críticos com contexto, terremotos e a faixa
de baixo. Tudo sai pronto daqui: o site não calcula (regra 9)."""
from datetime import timedelta

from sqlalchemy import func, select

from stratum import db
from stratum.domain import pontos as regra_pontos

JANELA_TERREMOTOS = timedelta(hours=24)
NOTICIAS_POR_PONTO = 5
FAIXA_NOTICIAS = 8
FAIXA_MAGNITUDE = 6.0   # na faixa de baixo, só terremotos fortes; no mapa, todos de 4,5 ou mais


def _iso(d):
    return d.isoformat(timespec="seconds") + "Z" if d else None


def terremotos(c, momento) -> list[dict]:
    """Os das últimas 24 horas, a versão mais recente de cada um, do mais forte para o mais fraco."""
    t = db.evento_local.c
    ultima = (select(func.max(t.id).label("id")).where(t.ocorreu_em >= momento - JANELA_TERREMOTOS)
              .group_by(t.fonte_id, t.ext_id).subquery())
    linhas = c.execute(select(db.evento_local).join(ultima, t.id == ultima.c.id)).mappings().all()
    saida = [{"id": e["ext_id"], "titulo": e["titulo"], "url": e["url"], "magnitude": e["magnitude"],
              "lat": round(e["lat"], 3), "lon": round(e["lon"], 3), "ocorreu_em": _iso(e["ocorreu_em"]),
              "conhecido_em": _iso(e["conhecido_em"]), "fonte": e["fonte_id"]} for e in linhas]
    return sorted(saida, key=lambda e: (-(e["magnitude"] or 0), e["ocorreu_em"] or ""))


def pontos(contaveis: list[dict], por_fonte: dict, resumo_documento, series: dict[str, dict], dicionario) -> dict:
    """Estado de cada ponto (regra em domain/pontos.py), com o contexto: fatos com fonte, margens, mercados ligados e
    as notícias que o citam (das mais recentes). `contaveis`: notícias da janela, sem rede social."""
    noticias = [{"titulo": d["titulo"], "resumo": d["resumo"],
                 "controlador": (por_fonte.get(d["fonte_id"]) or {}).get("controlador") or d["fonte_id"]}
                for d in contaveis]
    estados = regra_pontos.estados(noticias)
    lista = []
    for p in regra_pontos.PONTOS:
        citam = [d for d in contaveis if p["id"] in regra_pontos.citados(f"{d['titulo']}\n{d['resumo'] or ''}")]
        lista.append({
            "id": p["id"], "nome": p["nome"], "lon": p["lon"], "lat": p["lat"]} | estados[p["id"]] | {
            "margens": [{"iso": iso, "nome": dicionario.nome(iso) or iso} for iso in p["margens"]],
            "fatos": p["fatos"],
            "mercados": [_mercado(series[sid]) for sid in p["mercados"] if sid in series],
            "documentos": [resumo_documento(d) | {"acao": regra_pontos.tem_acao(f"{d['titulo']}\n{d['resumo'] or ''}")}
                           for d in citam[:NOTICIAS_POR_PONTO]],
        })
    ordem = {"critico": 0, "em_pauta": 1, "sem_pauta": 2}
    lista.sort(key=lambda x: (ordem[x["estado"]], -x["vozes"], -x["noticias"]))
    return {"regra": regra_pontos.REGRA, "lista": lista,
            "criticos": sum(1 for x in lista if x["estado"] == "critico"),
            "em_pauta": sum(1 for x in lista if x["estado"] == "em_pauta")}


def _mercado(s: dict) -> dict:
    """O resumo de uma série para os painéis (a leitura completa fica em mercados.series)."""
    return {k: s.get(k) for k in ("id", "nome", "unidade", "medida", "data", "valor", "variacao", "percentil", "extremo",
                                  "situacao", "parcial", "conhecido_em")}


def faixa(ultimos: list[dict], estado_pontos: dict, series: list[dict], eventos: list[dict]) -> list[dict]:
    """A faixa que passa embaixo da página: pontos críticos, mercados fora do normal, terremotos fortes e as últimas
    notícias. Cada item já traz o texto; a ordem é esta, e o site só mostra."""
    itens = []
    for p in estado_pontos["lista"]:
        if p["estado"] == "critico":
            itens.append({"tipo": "ponto", "id": p["id"], "texto": f"{p['nome']}: crítico",
                          "detalhe": f"{p['noticias']} notícias, {p['vozes']} vozes independentes"})
    for s in series:
        if s.get("extremo"):
            itens.append({"tipo": "mercado", "id": s["id"], "texto": s["nome"], "variacao": s["variacao"],
                          "medida": s["medida"], "extremo": s["extremo"], "parcial": s["parcial"]})
    for e in eventos:
        if (e["magnitude"] or 0) >= FAIXA_MAGNITUDE:
            itens.append({"tipo": "terremoto", "texto": e["titulo"], "url": e["url"], "quando": e["ocorreu_em"]})
    for d in ultimos[:FAIXA_NOTICIAS]:
        itens.append({"tipo": "noticia", "texto": d["titulo"], "url": d["url"], "fonte": d["fonte_nome"],
                      "quando": d["publicado_em"] or d["conhecido_em"]})
    return itens
