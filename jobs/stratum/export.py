"""Gera o status.json que o site mostra. O site não calcula nada: só lê este arquivo."""
import json
import os
import unicodedata
from datetime import timedelta

from sqlalchemy import func, or_, select

from stratum import VERSAO, db, fontes as catalogo, historias, mapa, mercados, traducao
from stratum.domain import historias as regra_historias
from stratum.domain import paises

VERSAO_FORMATO = 2
ULTIMOS_DOCUMENTOS = 100  # a aba Notícias busca e filtra nestas (decisão 0014)
RODADAS_RECENTES = 24

# Citações de países: quantas notícias publicadas na janela citam cada país (regra em domain/paises.py)
JANELA_HORAS = 24
TOLERANCIA_FUTURO = timedelta(hours=1)  # data da fonte mais de 1h depois da coleta: relógio errado, vale a da coleta
NIVEIS = (1, 3, 10, 30)                  # 1-2 citações = nível 1; 3-9 = 2; 10-29 = 3; 30 ou mais = 4
DOCUMENTOS_POR_PAIS = 5
MAIS_CITADOS = 8
NAO_CONTA = {"social"}  # rede social é pista, nunca entra em conta (regra 4)

# O site é refeito a cada rodada. Se passar disto sem rodada nova, ele avisa que os dados estão parados
AVISAR_ATRASO_APOS = timedelta(hours=2)
HISTORIAS_POR_PAIS = 5                 # no painel do país (decisão 0009)


def _iso(d):
    return d.isoformat(timespec="seconds") + "Z" if d else None


def nivel(citacoes: int) -> int:
    return sum(1 for limite in NIVEIS if citacoes >= limite)


def quando(d):
    """Quando a notícia saiu: a data da fonte; sem ela, ou adiantada demais em relação à coleta, a hora da coleta.
    Calculado aqui, e não no SQL, para dar o mesmo resultado no PostgreSQL e no SQLite."""
    publicado, conhecido = d["publicado_em"], d["conhecido_em"]
    return conhecido if publicado is None or publicado > conhecido + TOLERANCIA_FUTURO else publicado


def documentos_desde(c, inicio) -> list[dict]:
    """Documentos cuja data (regra de quando()) é a partir de inicio, do mais recente para o mais antigo."""
    candidatos = c.execute(select(db.documento).where(
        or_(db.documento.c.publicado_em >= inicio, db.documento.c.conhecido_em >= inicio))).mappings().all()
    docs = [dict(d, quando=quando(d)) for d in candidatos]
    return sorted((d for d in docs if d["quando"] >= inicio), key=lambda d: (d["quando"], d["id"]), reverse=True)


def ordem_alfabetica(nome: str) -> str:
    """Índia antes de Zâmbia: ordena sem acento."""
    return unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode().casefold()


def montar(engine, agora=db.agora, agendador: dict | None = None, copia: dict | None = None,
           parciais: list[dict] | None = None) -> dict:
    momento = agora()
    limite_24h = momento - timedelta(hours=24)
    inicio_janela = momento - timedelta(hours=JANELA_HORAS)
    with engine.connect() as c:
        ultima = c.execute(select(db.rodada).order_by(db.rodada.c.id.desc()).limit(1)).mappings().first()
        recentes = c.execute(select(db.rodada.c.iniciada_em, db.rodada.c.situacao)
                             .order_by(db.rodada.c.id.desc()).limit(RODADAS_RECENTES)).mappings().all()

        ultima_coleta_id = (select(db.coleta.c.fonte_id, func.max(db.coleta.c.id).label("id"))
                            .group_by(db.coleta.c.fonte_id).subquery())
        coletas = {r["fonte_id"]: r for r in c.execute(
            select(db.coleta).join(ultima_coleta_id, db.coleta.c.id == ultima_coleta_id.c.id)).mappings()}
        total_por_fonte = dict(c.execute(select(db.documento.c.fonte_id, func.count())
                                         .group_by(db.documento.c.fonte_id)).all())
        # Arquivo conferido (decisão 0015): as notícias que saíram do banco continuam nas contagens
        arquivados = c.execute(select(db.arquivo).where(db.arquivo.c.tabela == "documento")
                               .order_by(db.arquivo.c.id)).mappings().all()
        for a in arquivados:
            for f, n in json.loads(a["detalhe"] or "{}").get("por_fonte", {}).items():
                total_por_fonte[f] = total_por_fonte.get(f, 0) + n
        dia_por_fonte = dict(c.execute(select(db.documento.c.fonte_id, func.count())
                                       .where(db.documento.c.conhecido_em >= limite_24h)
                                       .group_by(db.documento.c.fonte_id)).all())
        fontes = c.execute(select(db.fonte).order_by(db.fonte.c.tipo, db.fonte.c.nome)).mappings().all()
        janela = documentos_desde(c, inicio_janela)
        if len(janela) < ULTIMOS_DOCUMENTOS:  # janela curta (fontes paradas): mostra os mais recentes mesmo assim
            recentes_coletados = c.execute(select(db.documento).order_by(db.documento.c.id.desc())
                                           .limit(ULTIMOS_DOCUMENTOS * 5)).mappings().all()
            ultimos = sorted((dict(d, quando=quando(d)) for d in recentes_coletados),
                             key=lambda d: (d["quando"], d["id"]), reverse=True)[:ULTIMOS_DOCUMENTOS]
        else:
            ultimos = janela[:ULTIMOS_DOCUMENTOS]
        em_portugues = traducao.titulos(c, {d["id"] for d in janela} | {d["id"] for d in ultimos})
        estado_traducao = traducao.situacao(c)
        obs_por_fonte = dict(c.execute(select(db.serie.c.fonte_id, func.count()).select_from(
            db.observacao.join(db.serie)).group_by(db.serie.c.fonte_id)).all())
        estado_mercados = mercados.montar(c, {f["id"]: f for f in fontes}, momento, catalogo.FONTES, catalogo.SERIES,
                                          copia=os.environ.get("STRATUM_CACHE_OBSERVACOES"), parciais=parciais)
        eventos = mapa.terremotos(c, momento)
        eventos_por_fonte = dict(c.execute(select(db.evento_local.c.fonte_id, func.count(func.distinct(db.evento_local.c.ext_id)))
                                           .group_by(db.evento_local.c.fonte_id)).all())

    dicionario = paises.carregar()
    por_fonte = {f["id"]: f for f in fontes}

    def citados(d) -> list[str]:
        return sorted(paises.citados(f"{d['titulo']}\n{d['resumo'] or ''}", dicionario))

    def resumo_documento(d) -> dict:
        f = por_fonte.get(d["fonte_id"]) or {}
        pt = em_portugues.get(d["id"])
        return {
            "titulo": pt or d["titulo"], "titulo_original": d["titulo"] if pt else None,  # decisão 0010
            "url": d["url"], "fonte": d["fonte_id"], "fonte_nome": f.get("nome", d["fonte_id"]),
            "fonte_tipo": f.get("tipo"), "fonte_pais": f.get("pais"), "fonte_pais_nome": dicionario.nome(f.get("pais")),
            "fonte_controle": f.get("controle"),  # estatal | publico | privado | multilateral: quem é dono da fonte
            "publicado_em": _iso(d["publicado_em"]), "conhecido_em": _iso(d["conhecido_em"]),
            "paises": [{"iso": iso, "nome": dicionario.nome(iso) or iso} for iso in citados(d)],
        }

    contagem: dict[str, int] = {}
    documentos_do_pais: dict[str, list] = {}
    origem: dict[str | None, int] = {}
    com_pais = oficiais = 0
    contaveis = [d for d in janela if (por_fonte.get(d["fonte_id"]) or {}).get("tipo") not in NAO_CONTA]
    for d in contaveis:  # do mais recente para o mais antigo
        isos = citados(d)
        com_pais += bool(isos)
        f = por_fonte.get(d["fonte_id"]) or {}
        oficiais += f.get("tipo") == "oficial"
        origem[f.get("pais")] = origem.get(f.get("pais"), 0) + 1
        for iso in isos:
            contagem[iso] = contagem.get(iso, 0) + 1
            lista = documentos_do_pais.setdefault(iso, [])
            if len(lista) < DOCUMENTOS_POR_PAIS:
                lista.append(resumo_documento(d))
    maximo = max(contagem.values(), default=0)
    ranking = sorted(contagem.items(), key=lambda kv: (-kv[1], ordem_alfabetica(dicionario.nome(kv[0]) or kv[0]), kv[0]))

    lista_fontes = []
    for f in fontes:
        col = coletas.get(f["id"])
        lista_fontes.append({
            "id": f["id"], "nome": f["nome"], "tipo": f["tipo"], "pais": f["pais"], "pais_nome": dicionario.nome(f["pais"]),
            "idioma": f["idioma"], "url": f["url"], "criterio": f["criterio"], "ativa": f["ativa"],
            "nivel": f["nivel"], "controle": f["controle"], "controlador_nome": f["controlador_nome"],
            "controlador_fontes": [u.strip() for u in (f["controlador_fonte"] or "").split(";") if u.strip()],
            "ultima_coleta": None if col is None else {
                "em": _iso(col["iniciada_em"]), "situacao": col["situacao"], "itens_lidos": col["itens_lidos"],
                "itens_novos": col["itens_novos"], "erro": col["erro"]},
            "documentos": total_por_fonte.get(f["id"], 0),
            "documentos_24h": dia_por_fonte.get(f["id"], 0),
            "observacoes": obs_por_fonte.get(f["id"], 0),  # fonte de dados (decisão 0011)
            "eventos": eventos_por_fonte.get(f["id"], 0),  # terremotos (decisão 0014)
        })

    series_por_id = {s["id"]: s for s in estado_mercados["series"]}
    estado_pontos = mapa.pontos(contaveis, por_fonte, resumo_documento, series_por_id, dicionario)
    ultimos_resumidos = [resumo_documento(d) for d in ultimos]

    todas_historias = historias.recentes(engine, momento, limite=None)
    lista_historias = todas_historias[:historias.MAX_HISTORIAS]
    historias_do_pais: dict[str, list] = {}
    for h in todas_historias:  # já vêm na ordem: mais vozes primeiro
        for p in h["paises"]:
            historias_do_pais.setdefault(p["iso"], []).append(
                {"id": h["id"], "titulo": h["titulo"], "titulo_original": h["titulo_original"], "noticias": h["noticias"],
                 "vozes": h["vozes"]})
    return {
        "versao_formato": VERSAO_FORMATO,
        "versao_robo": VERSAO,
        "gerado_em": _iso(momento),
        "avisar_atraso_apos": _iso(momento + AVISAR_ATRASO_APOS),
        "banco": ultima["banco"] if ultima else None,
        "erro_banco": None,
        "ultima_rodada": None if ultima is None else {
            "id": ultima["id"], "iniciada_em": _iso(ultima["iniciada_em"]), "terminada_em": _iso(ultima["terminada_em"]),
            "situacao": ultima["situacao"]},
        "agendador": agendador,
        "copia": copia,
        "arquivo": {"documentos": sum(a["linhas"] for a in arquivados),
                    "ultimo": {"etiqueta": arquivados[-1]["etiqueta"], "url": arquivados[-1]["url"],
                               "corte": _iso(arquivados[-1]["corte"]), "feito_em": _iso(arquivados[-1]["feito_em"])}
                    if arquivados else None},
        "historias": lista_historias,
        "traducao": estado_traducao,
        "mercados": estado_mercados,
        "pontos": estado_pontos,          # pontos críticos e o contexto de cada um (decisão 0014)
        "terremotos": eventos,
        "faixa": mapa.faixa(ultimos_resumidos, estado_pontos, estado_mercados["series"], eventos),
        "contagem_historias": {"total": len(todas_historias),
                               "varias_vozes": sum(1 for h in todas_historias if h["vozes"] >= 2)},
        "regra_historias": {"versao": regra_historias.REGRA, "limiar": regra_historias.CONFIG["limiar"],
                            "janela_horas": regra_historias.CONFIG["janela_horas"]},
        "rodadas_recentes": [{"iniciada_em": _iso(r["iniciada_em"]), "situacao": r["situacao"]} for r in recentes],
        "totais": {
            "documentos": sum(total_por_fonte.values()),
            "documentos_24h": sum(dia_por_fonte.values()),
            "fontes": len([f for f in fontes if f["ativa"]]),
            "fontes_ok": len([f for f in lista_fontes if f["ativa"] and f["ultima_coleta"] and f["ultima_coleta"]["situacao"] == "ok"]),
        },
        "fontes": lista_fontes,
        "ultimos_documentos": ultimos_resumidos,
        "atencao": {
            "regra": dicionario.versao,
            "janela_horas": JANELA_HORAS,
            "inicio": _iso(inicio_janela),
            "fim": _iso(momento),
            "niveis": list(NIVEIS),
            "documentos": len(contaveis),
            "documentos_com_pais": com_pais,
            "oficiais": oficiais,
            "paises_citados": len(contagem),
            "ignorados": list(dicionario.ignorados),
        },
        "paises": {iso: {"nome": dicionario.nome(iso) or iso, "citacoes": n, "nivel": nivel(n),
                         "documentos": documentos_do_pais[iso],
                         "historias": historias_do_pais.get(iso, [])[:HISTORIAS_POR_PAIS]} for iso, n in ranking},
        "mais_citados": [{"iso": iso, "nome": dicionario.nome(iso) or iso, "citacoes": n,
                          "proporcao": round(n / maximo, 4)} for iso, n in ranking[:MAIS_CITADOS]],
        "origem_fontes": [{"pais": p, "nome": dicionario.nome(p) or "Internacional", "documentos": n,
                           "proporcao": round(n / max(origem.values()), 4)}
                          for p, n in sorted(origem.items(), key=lambda kv: (-kv[1], kv[0] or ""))],
    }


def _gravar_json(caminho: str, dados: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=1)


def diagnostico(engine, agora=db.agora) -> list[str]:
    """Uma linha por notícia da janela com os países encontrados, para conferir a regra com manchetes reais."""
    momento = agora()
    with engine.connect() as c:
        docs = documentos_desde(c, momento - timedelta(hours=JANELA_HORAS))
    dicionario = paises.carregar()
    linhas = []
    for d in sorted(docs, key=lambda d: (d["fonte_id"], d["id"])):
        fonte_id, titulo, resumo = d["fonte_id"], d["titulo"], d["resumo"]
        achados = paises.encontrados(f"{titulo}\n{resumo or ''}", dicionario)
        termos = sorted({t for t, _ in achados})
        isos = sorted({iso for _, iso in achados if iso})
        linhas.append(f"[{','.join(isos) or '-'}] ({'; '.join(termos)}) {fonte_id}: {titulo} || {(resumo or '')[:160]}")
    return linhas


def escrever(engine, caminho: str, agendador: dict | None = None, copia: dict | None = None,
             parciais: list[dict] | None = None) -> None:
    dados = montar(engine, agendador=agendador, copia=copia, parciais=parciais)
    _gravar_json(caminho, dados)
    if os.environ.get("STRATUM_DIAGNOSTICO"):
        print("::group::Diagnóstico da regra de países (uma linha por notícia)")
        print("\n".join(diagnostico(engine)))
        print("::endgroup::")
    a = dados["atencao"]
    destaque = ", ".join(f"{p['iso']} {p['citacoes']}" for p in dados["mais_citados"][:5]) or "nenhum"
    print(f"Citações ({a['regra']}): {a['documentos']} notícias em {a['janela_horas']}h, "
          f"{a['documentos_com_pais']} citam algum país, {a['paises_citados']} países. Mais citados: {destaque}.")
    print(f"Status gravado em {caminho}")


def escrever_falha_banco(caminho: str, tipo_erro: str) -> None:
    """Quando o banco não abre, o site ainda é publicado e diz isso."""
    _gravar_json(caminho, {
        "versao_formato": VERSAO_FORMATO, "versao_robo": VERSAO, "gerado_em": _iso(db.agora()),
        "avisar_atraso_apos": _iso(db.agora() + AVISAR_ATRASO_APOS), "banco": "erro",
        "erro_banco": f"Não foi possível abrir o banco ({tipo_erro}).", "ultima_rodada": None, "agendador": None, "copia": None, "arquivo": None, "historias": [], "contagem_historias": None, "traducao": None, "mercados": None, "pontos": None, "terremotos": [], "faixa": [],
        "regra_historias": None,
        "rodadas_recentes": [],
        "totais": {"documentos": 0, "documentos_24h": 0, "fontes": 0, "fontes_ok": 0}, "fontes": [], "ultimos_documentos": [],
        "atencao": None, "paises": {}, "mais_citados": [], "origem_fontes": [],
    })
