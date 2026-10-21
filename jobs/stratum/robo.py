"""Robô: uma rodada lê cada fonte, grava só o que é novo e registra tudo. Uma fonte falhar não para as outras.
Fonte de dados (séries, decisão 0011) é lida no ritmo dela: entre uma leitura boa e a próxima, espera `a_cada_horas`.

Uso:  python -m stratum.robo [--exportar CAMINHO/status.json]
"""
import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import timedelta

import requests
from sqlalchemy import exc as erros_sql, select

from stratum import VERSAO, agendador, avisos, config, copia, db, export, historias, mercados, resumo, traducao
from stratum import fontes as catalogo
from stratum.connectors import eventos as conectores_eventos, rss, series as conectores_series
from stratum.domain.documento import hash_documento

CONECTORES = {"rss": rss.ler}
CONECTORES_SERIES = conectores_series.CONECTORES
CONECTORES_EVENTOS = conectores_eventos.CONECTORES


@dataclass
class Resultado:
    rodada_id: int
    situacao: str                       # ok | parcial | falhou
    novos: int = 0
    falhas: list[str] = field(default_factory=list)


def rodar(engine, fontes: list[dict], session, cfg: config.Config, agora=db.agora, conectores=CONECTORES,
          series: list[dict] | None = None, conectores_series=CONECTORES_SERIES,
          conectores_eventos=CONECTORES_EVENTOS) -> Resultado:
    banco = "permanente" if cfg.banco_permanente else "temporario"
    ids = {f["id"] for f in fontes}
    series = [s for s in (catalogo.SERIES if series is None else series) if s["fonte"] in ids]
    with engine.begin() as c:
        db.gravar_fontes(c, fontes)
        db.gravar_series(c, series)
        rid = c.execute(db.rodada.insert().values(iniciada_em=agora(), situacao="rodando", banco=banco, versao=VERSAO)
                        ).inserted_primary_key[0]

    resultado = Resultado(rodada_id=rid, situacao="rodando")
    ativas = [f for f in catalogo.ativas(fontes) if not _cedo_demais(engine, f, agora())]
    for f in ativas:
        inicio = agora()
        try:
            if f["conector"] in conectores_series:
                da_fonte = [s for s in series if s["fonte"] == f["id"] and s.get("ativa", True)]
                with engine.connect() as c:
                    primeira = mercados.desde(c, da_fonte)
                itens = conectores_series[f["conector"]](f, da_fonte, session, cfg.user_agent, primeira)
                novos = mercados.gravar(engine, da_fonte, itens, rid, agora())
            elif f["conector"] in conectores_eventos:
                itens = conectores_eventos[f["conector"]](f, session, cfg.user_agent)
                novos = _gravar_eventos(engine, f["id"], itens, rid, agora())
            else:
                itens = conectores[f["conector"]](f, session, cfg.user_agent)
                novos = _gravar(engine, f["id"], itens, rid, agora())
            linha = dict(situacao="ok", itens_lidos=len(itens), itens_novos=novos, erro=None)
            resultado.novos += novos
        except Exception as exc:  # isola a falha: as outras fontes seguem
            resultado.falhas.append(f["id"])
            linha = dict(situacao="falhou", itens_lidos=0, itens_novos=0, erro=erro_legivel(exc))
        with engine.begin() as c:
            c.execute(db.coleta.insert().values(rodada_id=rid, fonte_id=f["id"], iniciada_em=inicio, terminada_em=agora(), **linha))
        print(f"{f['id']}: {linha['situacao']}, {linha['itens_lidos']} lidos, {linha['itens_novos']} novos"
              + (f" ({linha['erro']})" if linha["erro"] else ""), flush=True)

    if not resultado.falhas:
        resultado.situacao = "ok"
    else:
        resultado.situacao = "falhou" if len(resultado.falhas) == len(ativas) else "parcial"
    with engine.begin() as c:
        c.execute(db.rodada.update().where(db.rodada.c.id == rid).values(terminada_em=agora(), situacao=resultado.situacao))
    return resultado


def _cedo_demais(engine, f: dict, agora) -> bool:
    """Fonte com ritmo próprio (a_cada_horas) lida com sucesso há pouco tempo: fica para uma rodada seguinte."""
    if not f.get("a_cada_horas"):
        return False
    with engine.connect() as c:
        ultima = c.execute(select(db.coleta.c.iniciada_em).where(db.coleta.c.fonte_id == f["id"], db.coleta.c.situacao == "ok")
                           .order_by(db.coleta.c.id.desc()).limit(1)).scalar()
    if ultima is not None and agora - ultima < timedelta(hours=f["a_cada_horas"]):
        print(f"{f['id']}: lida às {ultima:%H:%M} UTC; a próxima leitura é depois de {f['a_cada_horas']}h", flush=True)
        return True
    return False


def erro_legivel(exc: Exception) -> str:
    """Mensagem curta para a tela Método. O nome técnico fica entre parênteses para quem for consertar."""
    nome = type(exc).__name__
    if isinstance(exc, erros_sql.SQLAlchemyError):  # a mensagem do banco pode conter dados da conexão (regra 12)
        return f"Falha ao gravar no banco ({nome})."
    if isinstance(exc, requests.Timeout):
        return f"O site demorou demais para responder ({nome})."
    if isinstance(exc, (requests.ConnectionError, ConnectionError)):
        return f"Não foi possível conectar ao site ({nome})."
    texto = str(exc)
    if texto.startswith("HTTP "):
        return f"O site recusou o pedido ({texto})."
    if isinstance(exc, ValueError) and texto.startswith(("formato inesperado", "valor ilegível")):
        return f"O arquivo da fonte mudou de formato ({texto[:160]})."
    if isinstance(exc, ValueError) and "feed" in texto:
        return f"O endereço não devolveu um feed válido ({texto})."
    return f"{nome}: {texto[:160]}"


def _gravar(engine, fonte_id: str, itens, rodada_id: int, conhecido_em) -> int:
    """Grava os itens que o banco ainda não tem. Devolve quantos eram novos."""
    por_hash = {}
    for it in itens:
        h = hash_documento(it.url, fonte_id, it.titulo)
        por_hash.setdefault(h, it)  # repetido dentro do mesmo feed: fica o primeiro
    if not por_hash:
        return 0
    with engine.begin() as c:
        existentes = set()
        hashes = list(por_hash)
        for i in range(0, len(hashes), 500):
            existentes |= set(c.execute(select(db.documento.c.hash).where(db.documento.c.hash.in_(hashes[i:i + 500]))).scalars())
        linhas = [dict(hash=h, fonte_id=fonte_id, rodada_id=rodada_id, url=it.url, titulo=it.titulo, resumo=it.resumo or None,
                       publicado_em=it.publicado_em, conhecido_em=conhecido_em)
                  for h, it in por_hash.items() if h not in existentes]
        db.inserir_ignorando_repetidos(c, db.documento, linhas, "hash")
    return len(linhas)


def _gravar_eventos(engine, fonte_id: str, eventos, rodada_id: int, conhecido_em) -> int:
    """Cada versão de cada evento entra uma vez (regra 2: revisão da fonte vira registro novo). Devolve as novas."""
    unicos = {(e.ext_id, e.versao): e for e in eventos}
    if not unicos:
        return 0
    with engine.begin() as c:
        t = db.evento_local.c
        existentes = set(c.execute(select(t.ext_id, t.versao).where(
            t.fonte_id == fonte_id, t.ext_id.in_([k[0] for k in unicos]))).all())
        linhas = [dict(fonte_id=fonte_id, ext_id=e.ext_id, versao=e.versao, titulo=e.titulo, url=e.url,
                       magnitude=e.magnitude, lat=e.lat, lon=e.lon, ocorreu_em=e.ocorreu_em, conhecido_em=conhecido_em,
                       rodada_id=rodada_id) for k, e in unicos.items() if k not in existentes]
        db.inserir_ignorando_repetidos(c, db.evento_local, linhas, ["fonte_id", "ext_id", "versao"])
    return len(linhas)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Uma rodada do robô do Stratum Global.")
    p.add_argument("--exportar", help="grava o status para o site neste caminho (JSON)")
    args = p.parse_args(argv)
    cfg = config.ler()
    print(f"Stratum Global {VERSAO}. Banco: {'permanente' if cfg.banco_permanente else 'temporário (segredo SUPABASE_SENHA não configurado)'}.")

    try:
        engine = db.conectar(cfg.database_url)
        db.preparar(engine)
    except Exception as exc:  # nunca imprime a mensagem crua: ela pode conter dados da conexão
        print(f"Banco indisponível ({type(exc).__name__}). Confira a senha (SUPABASE_SENHA) nos Secrets do repositório.")
        if args.exportar:
            export.escrever_falha_banco(args.exportar, type(exc).__name__)
        return 1

    try:
        resultado = rodar(engine, catalogo.FONTES, rss.nova_sessao(), cfg)
        print(f"Rodada {resultado.rodada_id}: {resultado.situacao}, {resultado.novos} documentos novos.")
        try:
            h = historias.atualizar(engine, db.agora())
            print(f"Histórias: {h['documentos']} notícias ligadas, {h['historias_novas']} histórias novas.")
        except erros_sql.SQLAlchemyError:
            raise
        except Exception as exc:  # um defeito na regra não derruba a rodada: as notícias já estão gravadas
            print(f"Histórias: não foi possível ligar as notícias ({type(exc).__name__}).")
        if os.environ.get("STRATUM_TRADUCAO"):  # ligado só no workflow; nos testes, o modelo não é baixado
            try:
                t = traducao.atualizar(engine, db.agora())
                print(f"Tradução: {t['traduzidos']} títulos traduzidos.")
                for original, traduzido in t["exemplos"]:
                    print(f"  {original}  →  {traduzido}")
            except erros_sql.SQLAlchemyError:
                raise
            except Exception as exc:  # sem tradução, o site mostra o título original
                print(f"Tradução: não foi possível traduzir ({type(exc).__name__}).")
        estado = agendador.cuidar(engine, cfg.banco_permanente, cfg.repositorio, db.agora())
        print(f"Agendador: {estado.situacao}" + (f" ({estado.erro})" if estado.erro else ""))
        estado_copia = copia.situacao(cfg.ultima_copia, db.agora())
        print(f"Cópia do banco: {estado_copia['situacao']}")
        envio = resumo.talvez_enviar(
            engine, db.agora(), None if estado.situacao in ("ok", "aguardando", "sem_banco") else estado.texto(),
            cfg.repositorio, cfg.telegram_configurado, lambda t: avisos.enviar(t, cfg), cfg.banco_permanente,
            copia=estado_copia)
        print(f"Resumo do Telegram: {envio}")
        if args.exportar:
            export.escrever(engine, args.exportar, agendador=estado.para_status(), copia=estado_copia)
    except erros_sql.SQLAlchemyError as exc:  # o banco caiu no meio da rodada: o site diz isso, sem a mensagem crua
        print(f"O banco falhou no meio da rodada ({type(exc).__name__}).")
        if args.exportar:
            export.escrever_falha_banco(args.exportar, type(exc).__name__)
        return 1
    return 1 if resultado.situacao == "falhou" else 0


if __name__ == "__main__":
    sys.exit(main())
